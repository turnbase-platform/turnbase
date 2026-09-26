# REST API Conventions

## Base Path

All REST endpoints are served under `/api/`. There is no URL version prefix. API evolution is managed through new routes and deprecation headers — see [Versioning and Deprecation](#versioning-and-deprecation).

**Scoped to the public listener.** The admin API ([admin-rest-api.md](admin-rest-api.md)) is a second,
independent listener on the management port (§ *Actuator and the Management Port* below) and uses
`/admin/`, not `/api/` — it shares no namespace with the public API because it shares no port with it.

## URL Structure

- Plural nouns, lowercase: `/api/games`, `/api/rooms`, `/api/users`
- Hyphenated multi-word segments: `/api/game-rooms`
- Nested resources for owned sub-resources, one level deep: `/api/rooms/{roomId}/players`, `/api/games/{gameId}/versions`
- Flat when nesting would exceed two levels

## HTTP Methods

| Method | Semantics | Success Status |
|--------|-----------|---------------|
| GET | Read resource or collection | 200 |
| POST | Create new resource | 201 + `Location` header pointing to the new resource |
| PUT | Replace full editable representation | 200 |
| PATCH | Targeted partial update (flag, single field, or tightly related field group) | 200 |
| DELETE | Remove resource | 204 |

**PUT vs PATCH:** Use PUT when the client submits the complete editable body of a resource (e.g., updating all game metadata fields together). Use PATCH when the client submits only the changed subset — a single field, a flag toggle, or a group of fields that are always changed together (e.g., toggling profile section visibility).

## Status Codes

| Status | Used for |
|--------|----------|
| 200 OK | Successful read or update |
| 201 Created | Successful creation; `Location` header points to the new resource |
| 202 Accepted | Request accepted for asynchronous processing (e.g. bundle validation) |
| 204 No Content | Successful deletion or action with no response body |
| 400 Bad Request | Input validation failure |
| 401 Unauthorized | Missing, expired, or invalid session token |
| 403 Forbidden | Authenticated but insufficient permission |
| 404 Not Found | Resource does not exist (or is intentionally hidden, e.g. private game — `game-catalog.md NFR-SEC-002`) |
| 409 Conflict | Unique constraint violation (duplicate username, email) |
| 410 Gone | Resource existed but has been permanently removed (e.g. expired upload slot) |
| 413 Payload Too Large | Request body exceeds the 64 KB cap — see [input-validation.md](input-validation.md) |
| 422 Unprocessable Entity | Business rule violation (e.g. game version not strictly higher, bundle validation failure) |
| 429 Too Many Requests | Rate limit exceeded — see [rate-limiting.md](rate-limiting.md) |
| 500 Internal Server Error | Unexpected server failure |
| 503 Service Unavailable | Transient upstream failure (e.g. storage unreachable during bundle confirm) |

## Request Format

All request bodies use `Content-Type: application/json`. No XML support.

## Response Format

All response bodies use `Content-Type: application/json`. Successful responses return the resource directly with no wrapper envelope, except list endpoints which include pagination metadata — see [pagination-filtering-sorting.md](pagination-filtering-sorting.md).

Error responses follow RFC 9457 Problem Details — see [error-handling.md](error-handling.md).

## Authentication

All endpoints except those listed as public in `user-accounts.md NFR-SEC-006` require a valid session token delivered as an `httpOnly`, `Secure`, `SameSite=Strict` cookie (`user-accounts.md CON-004`), named **`turnbase_session`**, `Path=/`. The name is a fixed protocol constant, not a `local-environment.md` §7 tunable — every server-side path that reads the cookie back (the STOMP handshake, the SSE endpoint, any authenticated-route filter) must agree on the same literal string, which an operator-configurable name would put at risk for no benefit. Unauthenticated requests to protected endpoints receive a 401 response.

The session lifecycle is four endpoints:

| Endpoint | Effect |
|---|---|
| `POST /api/auth/login` | Revokes any existing session for the account, issues a new one (`FR-SESS-002/003`) |
| `POST /api/auth/guest` | Mints a guest account and a session (`FR-GUEST-001/003`) |
| `POST /api/auth/logout` | Revokes the current session, clears the cookie, returns `204` (`FR-SESS-011`) |
| `GET /api/auth/session` | Returns the current principal, or `401`. The frontend's tier check on load |

**Request bodies (`IMP-GATE-75`).** `login` takes `{ "usernameOrEmail", "password" }` (VW-LOGIN-001); `register` takes
`{ "username", "email", "password", "confirmPassword" }` (VW-REG-001); `guest` and `logout` take none. These are the field
names `turnbase-platform` shipped in `IMP-M1-04` and the springdoc document (`openapi-documentation.md`) is not yet built, so
until it is this is the only place a client can read them.

**The principal representation (`IMP-GATE-75`).** `register`, `login`, `guest` and `session` all respond with the same body, and it is what the shell's tier check reads:

```json
{ "userId": "uuid", "username": "alice", "kind": "REGISTERED" }
```

`kind` is `REGISTERED` or `GUEST` — the literal values of `app_user.kind` (`data-model-accounts.md` §1). It is a field of the principal rather than something the client infers from a `guest-` username prefix (FR-AUTH-013) or from a second request to `GET /api/users/{username}`: the shell must choose between the Guest and Registered tiers on every page load before it renders anything, and a tier decided by string convention is a decision the server cannot change without breaking every client. `login` always answers `REGISTERED` (guests have no login, FR-GUEST-004) and `guest` always `GUEST`.

**Logout is a `POST`, not a `DELETE`.** It is not the removal of an addressable resource — the caller
cannot name the session, and must not be able to, since a session identifier in a URL is a
credential in a URL. `POST` to an action endpoint is the honest shape, and it keeps logout inside the
`Origin` check below, which a `GET` would not be.

**Logout must also close the session's live WebSocket and SSE connections** (`FR-SESS-010`).
Revoking the row does nothing to a socket already open, and for a guest this is irreversible —
`FR-SESS-011` requires a confirmation before the platform destroys the only key to the account.

Four further self-scoped account routes, all under `/api/users/me` so the principal is the resource:

| Endpoint | Effect |
|---|---|
| `PATCH /api/users/me` | Updates username and/or email, either or both in one body. Each field enforces its own rolling 30-day window against `username_changed_at`/`email_changed_at` (`user-accounts.md` FR-ACCT-002/003) independently of the other. `200` with the updated resource; `409` on a duplicate username/email; `422` if the field's window hasn't elapsed; email is rejected outright (`422`) when `email_source = 'OAUTH'` (FR-AUTH-008/012 — an OAuth-derived email is immutable, not merely rate-limited) |
| `POST /api/users/me/password` | Changes the password. Body carries the current password and the new one (`user-accounts.md` FR-ACCT-010). `204` on success, `422` on current-password mismatch |
| `PATCH /api/users/me/privacy` | Profile visibility and the four per-section toggles (`user-accounts.md` FR-PROF-004, FR-PROF-006; `platform-views.md` VW-SET-006, VW-SET-006a). Body is a partial `user_privacy_settings` representation |
| `DELETE /api/users/me` | Permanently deletes the caller's account (`user-accounts.md` FR-ACCT-004…008). `204` on success; clears the session cookie and closes the caller's live connections, same as logout (`FR-SESS-010`). No request body and no confirmation step at this layer — `platform-views.md` VW-SET-007's confirmation is a frontend affordance, not a server-side proof requirement |

**Username and email share one endpoint, not two.** Both are single mutable identity fields on
`app_user` with the identical rolling-window shape (`data-model-accounts.md` §1's "one timestamp, not
a history"), and a client's account-settings form edits them on the same screen. Two endpoints would
let one succeed and the other fail with no shared transaction telling the client which; one `PATCH`
with independent per-field validation reports both outcomes in a single response.

**Password change is a `POST`, not a `PATCH`.** `PATCH` sends a subset of a resource's
representation, and the password is not part of any representation — it cannot be read back, and the
request carries a *proof* (the current password) alongside the new value rather than just the new
value. Modelling it as a field patch invites a client to send it in the same body as a username
change, which would make one field's failure roll back the other.

**Privacy toggles are a `PATCH`, and are the worked example** the *HTTP Methods* section above uses.
One endpoint rather than five: the toggles are edited together on one settings screen, and five
endpoints turn one save into five requests with no transaction across them.

**Account deletion is a `DELETE`, unlike logout.** Logout is a `POST` because the caller cannot name
the session as an addressable resource. Here the resource *is* named — `/api/users/me` is exactly the
account the caller is deleting — so `DELETE` is the honest verb. The idempotent-retry case the general
`DELETE` rule above describes (a second call against an already-deleted resource returning `204`) does
not arise here: deletion revokes the caller's session in the same transaction, so a retry has no
session cookie left to authenticate with and gets `401` before reaching the resource at all.

Both are `404`-free — the principal is always the resource, so there is nothing to fail to find.

**A password change revokes every other session for the account** and closes their live sockets, by
the same mechanism as `FR-SESS-003` displacement. A password change that leaves a stolen session
authenticated is not a password change.

## Authorization and Ownership

Authentication answers *who is calling*; every endpoint below also has to answer *may this caller act
on this object*. Getting the second wrong is an IDOR, and it is the most common serious flaw in an
API shaped like this one — resources are addressed by UUID, and a UUID in a path looks like an
authorization decision without being one.

**The rule: possession of an identifier is never authorization.** Every handler that takes a resource
id resolves the object and evaluates an explicit predicate against the authenticated principal,
inside the same transaction as the mutation.

| Resource | Predicate | Failure |
|---|---|---|
| `/api/users/me/**` | Implicit — the principal *is* the resource. No user id is ever accepted in the path for a self-scoped operation | — |
| `/api/games/{id}` (mutate) | `game.owner_user_id = principal` | `404` if the game is unlisted (`game-catalog.md` NFR-SEC-002), else `403` |
| `/api/games/{id}` (read, unlisted) | `game.owner_user_id = principal` | `404` — never `403`, which would confirm existence |
| `/api/rooms/{id}` (mutate) | `principal` is a participant; host commands additionally `room.host_user_id = principal`, re-checked under the room lock | `403` |
| `/api/notifications/{id}` | `notification.user_id = principal` | `404` |
| `/api/friend-requests/{id}` | `principal ∈ {sender, recipient}`, and the action must match the side | `403` |
| `/api/rooms/{roomId}/invitations` (send) | `room.host_user_id = principal` | `403` |
| `/api/rooms/{roomId}/invitations/me` | Implicit — the invitee is the caller (`room-invitation-rest-api.md` §1) | — |
| `/api/users/{username}` (read) | Public, subject to the profile privacy resolution in `user-accounts.md` FR-PROF-003…007 | — |
| `/admin/**` | Basic auth on the management port; never reachable from the public listener (`admin-tooling.md` FR-ADM-001) | `401` |

**`404` versus `403` is a deliberate choice per resource, not a house style.** A `403` confirms that
the object exists, which for a private game is exactly the enumeration `NFR-SEC-002` forbids. Where
existence is already public — a room, a profile — `403` is the honest answer and hiding it would only
confuse the client.

**Ownership is re-evaluated under the lock for anything mutable at runtime.** Room host is the case
that matters: a channel-level or filter-level check reads state that `TRANSFER_HOST` can invalidate
between the check and the write. The pattern throughout the platform is a cheap guard early and the
authoritative check in the handler, under the lock — see
[room-websocket.md](room-websocket.md)'s authorization model.

**Collections are scoped by the principal, never filtered client-side.** `GET /api/notifications`
returns the caller's notifications because the query is `WHERE user_id = :principal`, not because the
caller asked for their own.

## Idempotency

| Method | Behaviour |
|---|---|
| `GET`, `PUT`, `DELETE` | Idempotent by construction. A `DELETE` of an already-deleted resource returns `204`, not `404` — the caller's desired state holds |
| `PATCH` | Idempotent as specified here: every `PATCH` in the API sets absolute values, never deltas |
| `POST` | **Not** idempotent, with two exceptions below |

Two `POST`s need protection, for different reasons:

- **`POST /api/games/{gameId}/versions`** — a retried upload-slot request must not create a second
  `game_version` row and a second pre-signed URL. `(game_id, version)` is unique, so a retry with the
  same declared version fails on the constraint rather than duplicating; the handler translates that
  into the existing slot when it is still `PENDING`.
- **`POST /api/auth/guest`** — a retry mints a second account, which is exactly what
  `NFR-SEC-007`'s throttle is counting. This is accepted rather than solved: an idempotency key would
  have to be client-supplied, and an unauthenticated caller can supply a fresh one every time.

**No `Idempotency-Key` header is defined.** It would be dead weight on an API whose only unbounded
create is guest minting, where it provides nothing. If a future endpoint needs it, it is additive.

## Actuator and the Management Port

Actuator endpoints are **not** served on the public listener. `management.server.port` is `8081` and
`management.server.address` is `127.0.0.1`
([`../deployment/local-environment.md`](../deployment/local-environment.md) §1).

This is not defence in depth over an endpoint allow-list — it is the control. `admin-tooling.md`
FR-ADM-001 requires the admin API to be bound exclusively to localhost and CON-001 puts it on the
Spring management port, so actuator and the admin API are the **same listener**. Anything reachable
on `8081` is reachable by an operator with a shell and by nobody else.

Consequences worth stating:

- `/actuator/prometheus` (FR-MET-007) is scraped over the cluster-internal network, never through the
  ingress.
- `/actuator/health/liveness` and `/readiness` are probed by the kubelet on the pod IP, which is why
  binding to `127.0.0.1` is correct in compose and must be the pod IP in Kubernetes — a probe cannot
  reach a loopback-only listener from outside the container's network namespace.
- No Ingress rule and no `LoadBalancer` Service ever names port 8081.

## Origin Policy and CSRF

The platform frontend is **same-origin** with the API. There is therefore no legitimate cross-origin caller, and the API is configured accordingly:

- **CORS is default-deny.** No `Access-Control-Allow-Origin` header is emitted on any endpoint. The STOMP WebSocket endpoint is configured with `setAllowedOrigins(<platform origin>)`; the SSE endpoint is same-origin only.
- **State-changing requests are Origin-checked.** Any `POST`, `PUT`, `PATCH` or `DELETE` whose `Origin` header is present and is **not** the platform origin is rejected with 403, before authentication.

The second rule is not redundant with the first. **CORS default-deny does not prevent a cross-origin request from being sent** — it prevents the caller from *reading the response*. A credentialed state-changing request still lands and still takes effect. Blocking CSRF requires the server to refuse it, which is what the `Origin` check does.

This exists because `SameSite=Strict` (`user-accounts.md` CON-004) is nominated as the CSRF defense, and `SameSite` is a **site** check, not an **origin** check: it does not restrict same-site requests. That defense is therefore sound only if untrusted game code never runs same-site with the session cookie. It does not — game frontends are served from a **separate registrable domain** with `connect-src 'self'`, per [game-frontend/game-asset-serving.md](../game-frontend/game-asset-serving.md) §3 and §8. The `Origin` check is the layer that holds even if that assumption is ever weakened.

Neither the games origin nor any other origin is ever added to a CORS allowlist or to `setAllowedOrigins`.

## Versioning and Deprecation

No version prefix is used in URLs. Breaking changes are handled by:

1. Adding a new route with the updated contract
2. Marking the old route deprecated in code (`@Deprecated` on the handler method)
3. Attaching deprecation response headers to all responses from the deprecated handler via a filter:

```
Deprecation: Sat, 01 Jan 2027 00:00:00 GMT
Sunset: Sat, 01 Jul 2027 00:00:00 GMT
Link: </api/new-route>; rel="successor-version"
```

Headers follow RFC 8594. No endpoint is removed without a `Sunset` header and at least one release cycle of advance warning. See [openapi-documentation.md](openapi-documentation.md) for how deprecation is reflected in the Swagger UI.
