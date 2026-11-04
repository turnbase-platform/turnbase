# Archive — M10 E2E & security audit remediation

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim by `IMP-M20-01`. Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M10-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M10-01 | The version-upload route enforces game ownership | platform | M4-03, M11-08 | DONE |
| IMP-M10-02 | Per-user queues reject a cross-user subscription | platform | M3-07, M11-08 | DONE |
| IMP-M10-03 | An unauthorized room join is denied before it writes Redis | platform | M2-03, M11-08 | DONE |
| IMP-M10-04 | The login-lockout counter is atomic | platform | M1-02, M1-04, M11-08 | DONE |
| IMP-M10-05 | Rate limiting derives the client IP from the trusted hop | platform, frontend | M1-02, M11-08 | DONE |
| IMP-M10-06 | The gRPC registry is unreachable from the public edge | frontend, platform | M3-05, M11-08 | DONE |
| IMP-M10-07 | The body-size limit applies to a chunked request | platform | M1-01, M11-08 | DONE |
| IMP-M10-08 | The Game Host survives its first cold Espresso context | game-host | M3-02, M11-08 | DONE |
| IMP-M10-09 | Catalog search tolerates NUL and control bytes | platform | M4-01, M11-08 | DONE |
| IMP-M10-10 | Login timing does not reveal account existence | platform | M1-04, M11-08 | DONE |
| IMP-M10-11 | Friends, rooms and notifications refresh live | frontend | M8-12, M8-14, M11-08 | DONE |
| IMP-M10-12 | Email change and account deletion re-authenticate | platform, frontend | M1-08, M11-08 | DONE |
| IMP-M10-13 | A send blocked by a privacy setting fails visibly | platform, frontend | M1-09, M11-08 | DONE |
| IMP-M10-14 | The in-memory lock and limiter maps are bounded | platform | M2-03, M1-02, M11-08 | DONE |
| IMP-M10-15 | Search escapes `LIKE` wildcards | platform | M4-01, M11-08 | DONE |
| IMP-M10-16 | Denial copy states the real reason | frontend, platform | M8-06, M11-08 | DONE |
| IMP-M10-17 | An unknown route returns 404, not a soft 200 | frontend | M8-06, M11-08 | DONE |
| IMP-M10-18 | Security headers and strict `Host` matching at the edge | frontend | M8-06, M11-08 | DONE |
| IMP-M10-19 | The session cookie is `Secure` and `__Host-`-prefixed under TLS | platform | M1-06, M11-08 | DONE |
| IMP-M10-20 | The actuator `loggers` endpoint is read-only | platform | M0-10, M11-08 | DONE |
| IMP-M10-21 | The object store uses a scoped service credential | platform | M0-09, M11-08 | DONE |
| IMP-M10-22 | The Espresso sandbox's container dependency is documented | game-host | M3-02, M11-08 | DONE |
| IMP-M10-23 | The SDK game frame does not post to a detached parent | sdk | M3-12, M11-08 | DONE |
| IMP-M10-24 | The anonymous session probe does not log a 401 error | frontend | M7-11, M11-08 | DONE |

---

## M10 — E2E & security audit remediation

Opened 2026-10-10 from the [E2E & security audit](../../reviews/2026-10-10-e2e-security-audit/INDEX.md).
Each item **Closes** an `AUD-*` finding whose evidence and repro live in that round's INDEX; the
finding is the *why*, the clauses below are the *done*. Every finding marked *live* there was
reproduced against the running stack.

**Paused for M11 (2026-10-10).** Every item here depends on `IMP-M11-08`, the Spring Boot 4 migration
([ADR-0016](../../decisions/0016-spring-boot-4-migration.md) §6): building these fixes on Boot 3.5 code
that M11 rewrites would port each of them twice, and nothing can reach a green pipeline until it lands.

### IMP-M10-01 — The version-upload route enforces game ownership

**Repo:** `turnbase-platform` · **Depends on:** IMP-M4-03, IMP-M11-08 · **Closes:** AUD-01

**Spec fix (IMP-GATE-96, opened and closed 2026-10-10).** AUD-01 was a specification defect: the
`rest-conventions.md` ownership predicate covered `/api/games/{id}` but not its version sub-resources,
and `file-uploads.md` was silent on authorization — so the upload route shipped with no ownership
check and a non-owner could add a version to the Official game. Fixed in the parent repo:
`file-uploads.md` gained an *Authorization* section and `rest-conventions.md`'s mutate row now names
the three version routes and the ownerless-Official consequence. Build from the corrected spec.

**Read first:**
- `docs/specs/api-design/file-uploads.md` (the *Authorization* section)
- `docs/specs/api-design/rest-conventions.md` (*Authorization and Ownership*)
- `docs/specs/api-design/admin-rest-api.md` §4 (the Official-upload path, the only one for ownerless games)
- `docs/specs/platform/data-model-catalog.md` §2 (`game_official_ownerless_ck`)

**Satisfies:** `game-catalog.md` FR-GAME-006; `game-catalog.md` FR-GAME-008; `game-catalog.md` NFR-SEC-002

**Done when:**
- **Owner-scoped.** All three routes — `POST /api/games/{gameId}/versions`,
  `POST …/{uploadId}/confirm`, `GET …/{uploadId}` — resolve the game from the path and evaluate
  `game.owner_user_id = principal` before any slot is created or read; a non-owner gets `404` for an
  unlisted game, else `403`.
- **Official games refused.** A request against a game with `owner_user_id IS NULL` is refused for
  every caller; the only version path for it remains `admin-rest-api.md` §4.
- **Tests.** Integration tests over real PostgreSQL: owner (allowed), non-owner of a listed game
  (`403`), non-owner of an unlisted game (`404`), and any caller against the Official seed game
  (refused). A regression test asserts the AUD-01 repro now fails closed.

**Closed:** IMP-GATE-97 (opened and closed 2026-10-10, session 166) — FR-CICD-010 fails the build on
CVE-2026-47884/47890 (CRITICAL, `spring-webmvc` 6.2.19), which have no fix on the Boot 3.5 line.
Resolved by [ADR-0016](../../decisions/0016-spring-boot-4-migration.md): upgrade to Spring Boot 4.1, not
waive. The upgrade is milestone M11; this item now depends on `IMP-M11-08`.

**Landed (session 173):** `IMP-M11-08` — `turnbase-platform` `master` (`9a71a57`) pipeline green incl. Trivy gates; ref bumped.

### IMP-M10-02 — Per-user queues reject a cross-user subscription

**Repo:** `turnbase-platform` · **Depends on:** IMP-M3-07, IMP-M11-08 · **Closes:** AUD-02

**Read first:**
- `docs/specs/api-design/websocket.md` (subscription authorization; the `GAME_EVENT` destination model)
- `docs/specs/api-design/room-websocket.md` (the subscription authorizer)

**Satisfies:** `game-contracts.md` NFR-SEC-002

**Done when:**
- **Bound to the principal.** A `SUBSCRIBE` whose destination is a per-user queue
  (`/queue/…-user{sessionId}` and any ancestor/wildcard that `AntPathMatcher` would widen to it) is
  accepted only when the resolved user matches the subscribing principal; any other is refused with an
  `ERROR` frame and no delivery.
- **No wildcard reach.** A subscription to a wildcard or ancestor destination cannot receive a frame
  addressed by `convertAndSendToUser` to a different user.
- **Tests.** An integration test reproduces AUD-02 (user A subscribes a crafted destination, user B is
  sent a `send_to_player` effect) and asserts A receives nothing; a test that the legitimate
  per-user subscription still works.
- **`SEND` guard, same interceptor (SEC-S-03).** While in the subscription authorizer, also reject any
  `SEND` frame whose destination is not under `/app/*` — the equivalent of
  `simpDestMatchers("/topic/**","/queue/**","/user/**").denyAll()`. The 2026-10-10 live probe refuted
  SEC-S-03 as independently exploitable (the per-destination `/app/*` handlers already authorize every
  send), so this is defense-in-depth, not a separate finding; it is folded here because it lives in the
  same `WebSocketChannelInterceptor.preSend` path and costs nothing to add alongside the subscribe fix.
  An integration test asserts a `SEND` straight to `/topic/room.{id}.chat` is refused.

### IMP-M10-03 — An unauthorized room join is denied before it writes Redis

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-03, IMP-M11-08 · **Closes:** AUD-03

**Read first:**
- `docs/specs/api-design/room-rest-api.md` §5 (join; the `reachable()` predicate and the claim order)
- `docs/specs/platform/room-lifecycle.md` §2.1 (lock/claim ordering)

**Satisfies:** `game-rooms.md` FR-JOIN-001; `game-rooms.md` FR-JOIN-005

**Done when:**
- **Deny first.** The join handler evaluates `reachable()` / capacity authorization **before** any
  Redis key (ownership claim, lease, counter) is written; a caller who is ultimately refused leaves no
  residual key behind.
- **Tests.** An integration test asserts that N refused joins write zero new Redis keys, and that a
  legitimate join still claims exactly what §5 requires.

### IMP-M10-04 — The login-lockout counter is atomic

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-02, IMP-M1-04, IMP-M11-08 · **Closes:** AUD-04

**Read first:**
- `docs/specs/api-design/rate-limiting.md` (Tier 1 auth lockout)
- `docs/specs/api-design/error-handling.md` (the `429`/lockout response)

**Satisfies:** `user-accounts.md` NFR-SEC-003

**Done when:**
- **No race.** The failed-attempt counter is incremented and tested atomically (a single Redis
  round-trip / Lua script, or an atomic increment-then-compare), so concurrent failed logins cannot
  each observe a sub-threshold count; no more than NFR-SEC-003's 5 failures are admitted before the
  lockout trips, however many arrive at once.
- **Decay preserved.** The atomic path keeps NFR-SEC-003's doubling and 1-hour idle reset.
- **Tests.** A concurrency test fires parallel bad logins and asserts the 6th-onward is locked out.

### IMP-M10-05 — Rate limiting derives the client IP from the trusted hop

**Repo:** `turnbase-platform`, `turnbase-frontend` · **Depends on:** IMP-M1-02, IMP-M11-08 · **Closes:** AUD-05

**Read first:**
- `docs/specs/api-design/rate-limiting.md` (client-IP derivation)
- `docs/specs/deployment/local-environment.md` §7 (the nginx edge and forwarded headers)

**Satisfies:** `user-accounts.md` NFR-SEC-003; `user-accounts.md` NFR-SEC-007

**Done when:**
- **Trusted source only.** The limiter's client-IP comes from the connection peer or a
  forwarded-header value set by the trusted edge hop, never from a client-supplied `X-Forwarded-For`
  the edge did not overwrite. The trusted-proxy configuration is explicit, not implicit.
- **Edge normalizes.** The frontend nginx config sets/overwrites the forwarded header so a client
  cannot smuggle its own.
- **Tests.** A test that a client-supplied `X-Forwarded-For` neither changes the caller's bucket nor
  poisons another IP's bucket.

### IMP-M10-06 — The gRPC registry is unreachable from the public edge

**Repo:** `turnbase-frontend`, `turnbase-platform` · **Depends on:** IMP-M3-05, IMP-M11-08 · **Closes:** AUD-06

**Read first:**
- `docs/specs/deployment/local-environment.md` §7.8 (the registry servlet shares the HTTP listener)
- `docs/specs/internal-grpc/INDEX.md` (the registry service and its intended reachability boundary)
- `turnbase-frontend/nginx/default.conf.template` (the public proxy)

**Satisfies:** `platform-architecture.md` FR-REG-001; `platform-architecture.md` NFR-SEC-002

**Done when:**
- **Not proxied.** The public edge (nginx) does not forward `/turnbase.gamehost.v1.*` to the platform;
  a request to the registry path from outside gets `404`/`403` at the edge, not `grpc-status: 0`.
- **Boundary documented.** The spec states plainly that the registry's security control is
  unreachability from the public listener, and names where that is enforced, so the assumption is no
  longer implicit.
- **Tests.** A test (or e2e probe) that a `Heartbeat`/`Register` to the registry path via the public
  origin is refused, while the loopback/cluster-internal path still works.

### IMP-M10-07 — The body-size limit applies to a chunked request

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-01, IMP-M11-08 · **Closes:** AUD-07

**Read first:**
- `docs/specs/api-design/input-validation.md` (size limits)
- `docs/specs/api-design/rest-conventions.md` (request handling)

**Satisfies:** `user-accounts.md` NFR-SEC-005

**Done when:**
- **Cap regardless of framing.** A request body exceeding the configured limit is rejected whether the
  size is declared by `Content-Length` or streamed with `Transfer-Encoding: chunked`; the limit is
  enforced on bytes read, not only on the declared length.
- **Tests.** A test POSTing an over-limit chunked body asserts rejection at the documented limit.

### IMP-M10-08 — The Game Host survives its first cold Espresso context

**Repo:** `turnbase-game-host` · **Depends on:** IMP-M3-02, IMP-M11-08 · **Closes:** AUD-08

**Read first:**
- `docs/specs/game-host/game-host-internals.md` (context lifecycle, warm-up)
- `docs/reviews/2026-07-02-mvp-readiness/espresso-spike-results.md` (Espresso boot constraints)

**Satisfies:** `platform-architecture.md` FR-CTX-001; `platform-architecture.md` NFR-AVAIL-001

**Done when:**
- **First game works.** On a cold `make up`, the first `START_GAME` succeeds — no `NO_HOST_AVAILABLE`
  / `GAME_START_FAILED` that a `gamehost` restart would clear. Either the host does not report ready
  until its first Espresso context is live (extending `IMP-M7-09`'s warm-up), or the lease/registration
  race that leaves it registered-but-idle is fixed.
- **Tests.** A clean-boot test (or the e2e harness on a fresh stack) runs a game as the very first
  action after readiness and asserts success. The STATUS gotcha note is removed once it holds.

### IMP-M10-09 — Catalog search tolerates NUL and control bytes

**Repo:** `turnbase-platform` · **Depends on:** IMP-M4-01, IMP-M11-08 · **Closes:** AUD-09

**Read first:**
- `docs/specs/api-design/catalog-rest-api.md` §3 (the listing filters)
- `docs/specs/api-design/input-validation.md` (canonicalization, rejecting control characters)

**Satisfies:** `user-accounts.md` NFR-SEC-005; `game-catalog.md` FR-CAT-005

**Done when:**
- **No 5xx.** `GET /api/games?search=…` with a NUL (`%00`) or other control byte returns `200` (empty
  or filtered) or a `422`/`400` validation error — never `500`. The same canonicalization covers every
  `search`-style filter the listing endpoints accept.
- **Tests.** A test per listing endpoint with a NUL and a control byte in `search`.

### IMP-M10-10 — Login timing does not reveal account existence

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-04, IMP-M11-08 · **Closes:** AUD-10

**Read first:**
- `docs/specs/api-design/input-validation.md` (§ Argon2id cost parameters; credential verification)
- `docs/specs/api-design/error-handling.md` (the generic auth-failure response)

**Satisfies:** `user-accounts.md` FR-AUTH-006; `user-accounts.md` NFR-SEC-001

**Done when:**
- **Constant-ish work.** A login for an unknown username performs the same password-verification work
  (a dummy Argon2 verify against a fixed hash) as one for a known username, so response latency does
  not distinguish present from absent accounts; the response body is already generic.
- **Tests.** A timing-oriented test asserts the present/absent latency distributions overlap within a
  tolerance, and that the response text is identical.

### IMP-M10-11 — Friends, rooms and notifications refresh live

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M8-12, IMP-M8-14, IMP-M11-08 · **Closes:** AUD-11

**Read first:**
- `docs/specs/platform-frontend/shell-architecture.md` (the live-update channels: STOMP, SSE)
- `docs/requirements/platform-views.md` (the Friends, Rooms and notification views)
- `docs/specs/api-design/room-rest-api.md` §3 (why the Rooms list is not a live surface)

**Satisfies:** `social-friends.md` FR-SOC-006

**Done when:**
- **No manual reload.** A friendship/request change and a new notification are reflected in the open
  Friends view and notification panel without a manual reload, over the existing SSE channel (no
  polling). The Friends view re-reads its lists on each pushed `FRIEND_*` notification and on each
  stream (re)connect; the notification panel already does so and keeps doing so.
- **The Rooms list is out of scope, by requirement.** `game-rooms.md` FR-LIST-005 refreshes it only
  on the explicit control and `room-rest-api.md` §3 says it is not a real-time surface; no channel
  carries other users' room changes. AUD-11's room-state staleness is the *room view*, already live
  over `/topic/room.{roomId}`. Do not add a rooms push or timer here.
- **Tests.** Two-context e2e: actor A's friend-request change appears in actor B's open Friends view
  within the push latency.

**Closed:** IMP-GATE-98 (opened and closed 2026-10-10, session 183) — the original clause required the
Rooms list to refresh live, contradicting FR-LIST-005 and `room-rest-api.md` §3 and naming no channel
that could carry it. Rooms dropped from the clause; the audit register's AUD-11 note says so.

### IMP-M10-12 — Email change and account deletion re-authenticate

**Repo:** `turnbase-platform`, `turnbase-frontend` · **Depends on:** IMP-M1-08, IMP-M11-08 · **Closes:** AUD-12

**Closed:** IMP-GATE-99 (opened and closed 2026-10-10, session 185) — `rest-conventions.md` said `DELETE /api/users/me` takes no body and needs no proof, and neither route stated the proof's wire shape. Fixed in `rest-conventions.md` (`PATCH`/`DELETE /api/users/me` carry `currentPassword`; `422` on missing or wrong; OAuth-only exempt) and `user-accounts.md` FR-ACCT-003/004.

**Read first:**
- `docs/requirements/user-accounts.md` (FR-ACCT-004 deletion, FR-ACCT-010's re-auth precedent and its rationale)
- `docs/specs/api-design/rest-conventions.md` (`/api/users/me` self-scoped routes)

**Satisfies:** `user-accounts.md` FR-ACCT-004; `user-accounts.md` FR-ACCT-010

**Done when:**
- **Re-auth on the permanent actions.** Account deletion (`DELETE /api/users/me`) and an email change,
  for a credential account, require the current password server-side, extending FR-ACCT-010's rule
  (a session left open on a shared machine must not permit a permanent, access-ending change). OAuth
  accounts, whose email is immutable (FR-AUTH-008/012) and which have no password, re-auth per their
  own method or are out of scope with that stated.
- **Tests.** A test that deletion/email change without the current password is refused and with it
  succeeds.

### IMP-M10-13 — A send blocked by a privacy setting fails visibly

**Repo:** `turnbase-platform`, `turnbase-frontend` · **Depends on:** IMP-M1-09, IMP-M11-08 · **Closes:** AUD-13

**Read first:**
- `docs/requirements/social-friends.md` FR-SOC-021 (block-incoming-requests; API must reject)
- `docs/specs/api-design/social-rest-api.md` (the send-request endpoint and its `4xx`s)

**Satisfies:** `social-friends.md` FR-SOC-021

**Done when:**
- **Explicit rejection.** A friend request to a user who has enabled FR-SOC-021 is rejected by the API
  with a documented `4xx` (not a silent success), and the sender's UI shows the refusal rather than a
  success state.
- **Tests.** An integration test that the send is rejected, and an e2e that the sender sees the
  refusal.

### IMP-M10-14 — The in-memory lock and limiter maps are bounded

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-03, IMP-M1-02, IMP-M11-08 · **Closes:** AUD-14

**Read first:**
- `docs/specs/api-design/rate-limiting.md` (the pod-local WebSocket limiter buckets)
- `docs/specs/platform/room-lifecycle.md` (per-room lock objects)

**Satisfies:** `platform-operations.md` NFR-SCALE-001

**Done when:**
- **No unbounded growth.** Per-key in-memory structures (room-lock objects, pod-local limiter buckets)
  are evicted when their key goes idle (size- or time-bounded cache), so distinct-key churn does not
  grow heap without limit.
- **Tests.** A test that drives many distinct keys and asserts the map stabilizes (entries are
  reclaimed) rather than growing monotonically.

### IMP-M10-15 — Search escapes `LIKE` wildcards

**Repo:** `turnbase-platform` · **Depends on:** IMP-M4-01, IMP-M11-08 · **Closes:** AUD-15

**Read first:**
- `docs/specs/api-design/catalog-rest-api.md` §3 and `docs/specs/api-design/room-rest-api.md` (the `search` filters)
- `docs/specs/api-design/pagination-filtering-sorting.md` (server-side filtering)

**Satisfies:** `game-catalog.md` FR-CAT-005; `game-rooms.md` FR-LIST-003

**Done when:**
- **Literal search.** `%` and `_` in a `search` value are treated as literals (escaped, with an
  `ESCAPE` clause) so a user cannot craft a match-everything or probe pattern; the substring match is
  over the user's literal text.
- **Tests.** A test that `search=%` matches only rows literally containing `%`, across catalog and
  rooms.

### IMP-M10-16 — Denial copy states the real reason

**Repo:** `turnbase-frontend`, `turnbase-platform` · **Depends on:** IMP-M8-06, IMP-M11-08 · **Closes:** AUD-16

**Not a spec defect.** `error-handling.md` leaves Problem Detail `detail` free-form by design; this is
a copy fix, not a corpus contradiction.

**Read first:**
- `docs/specs/api-design/error-handling.md` (Problem Detail `detail`, the error taxonomy)
- `docs/requirements/platform-views.md` (the view that renders the denial)

**Satisfies:** —  *(copy/UX; `AUD-16`)*

**Done when:**
- **Honest message.** A refused action shows a message naming the real cause (e.g. "the room is full",
  "you do not have permission"), mapped from the Problem Detail `type`/`detail`, not a generic or
  misleading default.
- **Tests.** An e2e asserting the correct copy on at least one refused action per taxonomy class
  exercised by the MVP.

### IMP-M10-17 — An unknown route returns 404, not a soft 200

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M8-06, IMP-M11-08 · **Closes:** AUD-17

**Read first:**
- `docs/specs/platform-frontend/shell-architecture.md` (SPA fallback and the 404 view)
- `turnbase-frontend/nginx/default.conf.template` (the SPA fallback location)

**Satisfies:** `platform-views.md` VW-404-001

**Done when:**
- **Correct status.** A request for a path with no route returns HTTP `404` (the shell still renders
  the 404 view), rather than `200`. Known client routes keep `200`.
- **Tests.** An e2e asserting `GET /nope` → `404` and that the 404 view renders.

### IMP-M10-18 — Security headers and strict `Host` matching at the edge

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M8-06, IMP-M11-08 · **Closes:** AUD-18

**Read first:**
- `turnbase-frontend/nginx/default.conf.template` (the `default_server` and header blocks)
- `docs/specs/api-design/rest-conventions.md` (CORS/Origin, the security posture)

**Satisfies:** `user-accounts.md` NFR-SEC-002

**Done when:**
- **Known hosts only.** The edge serves only the platform host; an unknown `Host` gets a `421`/`444`,
  not the app. The catch-all `default_server` no longer serves arbitrary hosts.
- **Hardening headers.** Standard response headers (`X-Content-Type-Options`, `Referrer-Policy`,
  `X-Frame-Options`/frame-ancestors as the iframe model allows, HSTS under TLS) are present on
  responses, consistent with the existing shell CSP.
- **Tests.** A test that an unknown `Host` is refused and that the headers are present.

### IMP-M10-19 — The session cookie is `Secure` and `__Host-`-prefixed under TLS

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-06, IMP-M11-08 · **Closes:** AUD-19

**Read first:**
- `docs/requirements/user-accounts.md` CON-004 (httpOnly, Secure, SameSite=Strict cookie)
- `docs/specs/api-design/rest-conventions.md` § Authentication (cookie attributes; the former `platform/session-management.md` does not exist)

**Satisfies:** `user-accounts.md` FR-SESS-001

**Done when:**
- **TLS attributes.** Under a TLS/production profile the session cookie carries `Secure` and, where
  compatible, the `__Host-` prefix (path `/`, no `Domain`), satisfying CON-004; the local `http`
  profile keeps a working cookie without `Secure`, selected by config not by code branches in the
  handler.
- **Tests.** A test asserting the attributes per profile.

### IMP-M10-20 — The actuator `loggers` endpoint is read-only

**Repo:** `turnbase-platform` · **Depends on:** IMP-M0-10, IMP-M11-08 · **Closes:** AUD-20

**Read first:**
- `docs/specs/deployment/local-environment.md` §7 (the management port and exposed actuator endpoints)
- `docs/requirements/platform-operations.md` FR-OBS-004 (runtime log-level adjustability)

**Satisfies:** `platform-operations.md` FR-OBS-004

**Done when:**
- **No unauthenticated write.** The actuator `loggers` write operation (POST) is not exposed
  unauthenticated on the management listener; runtime level changes (FR-OBS-004) go through a path that
  is authenticated or disabled in the exposed profile. Read access, if kept, stays read-only.
- **Tests.** A test that a `POST /actuator/loggers/…` is refused on the exposed profile.

### IMP-M10-21 — The object store uses a scoped service credential

**Repo:** `turnbase-platform` · **Depends on:** IMP-M0-09, IMP-M11-08 · **Closes:** AUD-21

**Read first:**
- `docs/specs/deployment/local-environment.md` §1 (MinIO and its credentials)
- `docs/specs/deployment/secrets-and-configuration.md` (credential scoping)

**Satisfies:** `platform-operations.md` FR-CRED-001

**Done when:**
- **Least privilege.** The platform authenticates to the object store with a scoped service
  credential (bucket-limited access key), not the MinIO/S3 root account; the root credential is used
  only for provisioning, if at all.
- **Tests / check.** The compose and Helm config provision the scoped credential; a check (or doc)
  records that the app config no longer references the root account.

### IMP-M10-22 — The Espresso sandbox's container dependency is documented

**Repo:** `turnbase-game-host` · **Depends on:** IMP-M3-02, IMP-M11-08 · **Closes:** AUD-22

**Read first:**
- `docs/requirements/platform-architecture.md` FR-SEC-005, NFR-SEC-001…003 (two-layer isolation)
- `docs/reviews/2026-07-02-mvp-readiness/espresso-spike-results.md` (what the JVM layer does and does not enforce)

**Satisfies:** `platform-architecture.md` NFR-SEC-003

**Done when:**
- **Dependency stated.** The game-host docs record explicitly which isolation guarantees are enforced
  in-JVM by Truffle/Espresso and which are backstopped by the container boundary (the gVisor layer
  being post-MVP, FR-SEC-001), so the defense-in-depth assumption is not silent. No in-JVM behaviour
  change is required; this is the documentation half of FR-SEC-005.
- **Done check.** The note names the container-dependent guarantees and links the spike result.

### IMP-M10-23 — The SDK game frame does not post to a detached parent

**Repo:** `turnbase-sdk` · **Depends on:** IMP-M3-12, IMP-M11-08 · **Closes:** AUD-23 *(same site as CA-10)*

**Read first:**
- `docs/requirements/game-contracts.md` FR-FE-001…006, NFR-SEC-004 (the postMessage surface, origin validation)
- `docs/specs/game-frontend/INDEX.md` (the FE GDK client relay)

**Satisfies:** `game-contracts.md` NFR-SEC-004

**Done when:**
- **Guarded post.** The FE GDK client does not call `postMessage` when `window.parent === window`
  (the frame has been detached, e.g. on *Return to lobby*/remount), eliminating the per-game
  origin-mismatch console warning; legitimate posts to the real parent are unchanged.
- **Tests.** A unit test that a post is suppressed when the frame has no distinct parent, and the
  suite's warning tripwire stays clean across a full game.

### IMP-M10-24 — The anonymous session probe does not log a 401 error

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M7-11, IMP-M11-08 · **Closes:** AUD-24

**Read first:**
- `docs/specs/platform-frontend/shell-architecture.md` (the anonymous session probe)
- `docs/requirements/platform-views.md` (auth-tier gating)

**Satisfies:** `user-accounts.md` NFR-SEC-006

**Done when:**
- **Quiet probe.** The shell's startup session probe treats the expected `401` for an anonymous
  visitor as an ordinary "no session" result, logging no console error; the console stays clean for an
  anonymous first load.
- **Tests.** An e2e asserting no console error on an anonymous landing, keeping the suite tripwire
  meaningful.

---
