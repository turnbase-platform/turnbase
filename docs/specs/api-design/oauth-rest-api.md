# OAuth REST API

The Google OAuth round trip: the browser-navigated consent redirect and callback, and the JSON
endpoints the `/auth/complete-registration` page uses to finish account creation or resolve
`FR-AUTH-016`'s email collision. Closes **`IMP-GATE-37`**: `secrets-and-configuration.md` §5 and
`flows/01-arrival-and-account.md` §E name the two browser-navigated paths (`/auth/callback`,
`/auth/complete-registration`) but no document ever named the endpoint the "Continue with Google"
button hits, the JSON shape of the pending-registration state, or the collision-challenge endpoint
itself.

## Related

| Document | What it supplies |
|---|---|
| [rest-conventions.md](rest-conventions.md) | Status codes, the `turnbase_session` cookie, the `Origin` check on state-changing requests |
| [error-handling.md](error-handling.md) | RFC 9457 Problem Details and the type taxonomy |
| [rate-limiting.md](rate-limiting.md) | Tier 1 (auth failures), Tier 5 (account minting — already names the OAuth callback) |
| [../deployment/secrets-and-configuration.md](../deployment/secrets-and-configuration.md) | §5 — the client secret, the registered redirect URI, the signed `state` |
| [../deployment/local-environment.md](../deployment/local-environment.md) | §7.4 — the new TTL properties this document adds |
| [../platform/data-model-accounts.md](../platform/data-model-accounts.md) | §1 (`app_user`, `email_source`), §2 (`user_auth_method`) |
| [../flows/01-arrival-and-account.md](../flows/01-arrival-and-account.md) | §E — the end-to-end walkthrough this document turns into endpoints |
| [../../requirements/user-accounts.md](../../requirements/user-accounts.md) | FR-AUTH-007…012, FR-AUTH-016 |
| [../../requirements/platform-views.md](../../requirements/platform-views.md) | VW-LOGIN-002, VW-REG-002, VW-OAUTHCOMP-001…002, VW-REDIR-004…006 |

---

## 1. Two kinds of endpoint on one surface

Three routes are **browser-navigated** — Google or the platform issues a `302` to them directly, they
are never called with `fetch`, and they sit outside `/api/` for the same reason `/auth/callback`
already does: the redirect URI is registered with Google as an exact string, and a page navigation is
not a JSON request/response pair. The remaining two are ordinary JSON endpoints the
`/auth/complete-registration` frontend page calls, and they live under `/api/` like everything else.

| Method | Path | Kind | Auth |
|---|---|---|---|
| `GET` | `/api/auth/providers` | JSON | Public |
| `GET` | `/auth/google` | Browser redirect | Public |
| `GET` | `/auth/callback` | Browser redirect | Public |
| `GET` | `/api/auth/oauth/pending` | JSON | Pending cookie |
| `POST` | `/api/auth/oauth/complete-registration` | JSON | Pending cookie |
| `POST` | `/api/auth/oauth/link-challenge` | JSON | Pending cookie |

"Pending cookie" means `turnbase_oauth_pending` (§2) — not the session cookie, and not a header the
frontend can construct itself, since the pending state was minted server-side at `/auth/callback` and
the frontend never sees the raw Google identity.

---

## 2. The pending-registration cookie

A first-time Google login (no `user_auth_method` row for the `sub`) cannot finish in one request: the
platform needs a username (§ VW-OAUTHCOMP-001) or, on collision, a password, and neither is available
at the moment the code exchange completes. The state that bridges `/auth/callback` to whichever JSON
endpoint finishes the job is a Redis-backed token, the same "short-lived, no table" mechanism
`flows/01-arrival-and-account.md` §E step 5b already names:

- **Redis key:** `oauth:pending:{token}`, value `{provider: "GOOGLE", sub, email, collisionUserId}`
  (`collisionUserId` null unless §5 applies), TTL `turnbase.auth.oauth.pending-registration-ttl`
  (default `10m`, §7 below).
- **Cookie:** `turnbase_oauth_pending`, carrying `{token}` only — never the email or `sub` directly,
  so a copied cookie value discloses nothing the server does not already hold keyed by it.
  `HttpOnly; Secure; SameSite=Strict; Path=/`, `Max-Age` matching the Redis TTL. Same flag set as
  `turnbase_session` (`user-accounts.md` CON-004) — this cookie is a bearer credential for finishing
  someone's registration, and gets the same treatment as one for logging in as them.
- Cleared (`Max-Age=0`) whenever the pending record is consumed or expires, by every endpoint in this
  document that can be the last step of a flow (§4, §5).

**Why a cookie, not a query parameter carrying the token.** `/auth/callback`'s `302 Location` is a
URL the browser puts in its history and sends as a `Referer` on the next navigation; a token in it
would leak the same way a session ID in a URL would (`rest-conventions.md`'s own reasoning for why
logout is a `POST`). Setting it as a cookie on the `302` response and reading it back implicitly on
the next request keeps the token out of every place a URL gets logged.

**Why the frontend cannot read the email out of the cookie itself.** `HttpOnly` is deliberate — the
one piece of information the complete-registration page needs to render (the provider email,
read-only, per `VW-OAUTHCOMP-001`) is fetched from §3, not decoded from the cookie by JavaScript. An
`HttpOnly` cookie whose payload JavaScript still needs decoded elsewhere is a cookie that should not
have been `HttpOnly` at all.

---

## 3. `GET /auth/google` — initiate

```
GET /auth/google?redirect=/rooms/abcd
```

Unauthenticated, browser-navigated. `redirect` is optional and follows the identical validation
`VW-REDIR-005/006` already applies to the login/guest flow: a valid internal path, or the check fails
closed to `/rooms` — this is the same open-redirect gate, reused rather than re-specified, because
the destination travels through the identical hazard (an attacker-controlled value that returns as a
redirect target).

The validated destination is embedded in a `state` value, **signed with the JWT signing key**
(`secrets-and-configuration.md` §5) and given `turnbase.auth.oauth.state-ttl` (default `5m`, §7). The
response is a `302` to Google's authorization endpoint with the platform's client ID, the fixed
`redirect_uri` (`http://turnbase.localhost:8080/auth/callback` locally), the requested scopes
(`openid email`), and `state`.

No rate limit beyond Tier 4 — this endpoint mints nothing and reads nothing about any account; the
account-creation cost is Tier 5, applied where the account is actually created (§4, §7 note).

**Hidden when the client secret is absent.** Per `secrets-and-configuration.md` §1, a login/register
page with no `TURNBASE_OAUTH_GOOGLE_CLIENT_SECRET` configured never renders the "Continue with
Google" button (`VW-LOGIN-002`, `VW-REG-002`); this endpoint still exists and still 404s cleanly if
hit directly, rather than 500ing on a missing config value.

**How the page knows (`IMP-GATE-76`).** `GET /api/auth/providers` — unauthenticated, Tier 4, no
parameters — answers `200` with

```json
{ "google": true }
```

`google` is `true` exactly when both the client ID and the client secret are configured, and never
discloses either. Nothing else in the corpus told the frontend whether the button would work, and a
browser cannot probe `/auth/google` to find out (a `302` to Google and a `404` are indistinguishable
across a navigation). It is a `GET` that reads only deployment configuration.

---

## 4. `GET /auth/callback` — code exchange

```
GET /auth/callback?code=…&state=…
```

Browser-navigated, sent by Google. In order:

1. Verify `state`'s signature and TTL. Invalid or expired → `302` to `/login` with a generic
   query-string flag the frontend renders as a toast (`login?oauthError=1`); nothing about *why* is
   disclosed, since `state` failing is exactly as attacker-reachable as the redirect destination it
   carries.
2. Exchange `code` for tokens server-side, using the client secret (`secrets-and-configuration.md`
   §5) — the secret never reaches the browser at any step in this document.
3. Resolve identity by `(method = 'GOOGLE', provider_subject = sub)` — **never by email**
   (`data-model-accounts.md` §2, `flows/01-arrival-and-account.md` §E's own emphasis).
4. **Found** → issue a session exactly as `IMP-M1-04`'s `SessionService` does for credential login
   (displace-then-insert), set `turnbase_session`, `302` to `state`'s destination or `/rooms`. No
   pending cookie is ever set on this branch.
5. **Not found** → mint the pending record (§2) with `collisionUserId` left unresolved for now (§5
   decides it lazily, at §7, rather than here — see that section's note on why), set
   `turnbase_oauth_pending`, `302` to `/auth/complete-registration`.

No response body on either branch — both are redirects. Tier 4 (unauthenticated, lenient) applies,
the same as §3 — this endpoint mutates nothing itself. It carries no Tier 5 accounting of its own;
`rate-limiting.md`'s "First-time account creation via an OAuth callback" is read as "the
account creation this callback eventually causes", and the counter increments where the row is
actually written (§7's success path), not on a callback that only reaches step 5 and is then
abandoned. Applying it here would let one aborted registration cost real budget from
`rate:mint:register:{ip}` for an account that never came to exist.

---

## 5. `GET /api/auth/oauth/pending` — read pending state

```http
GET /api/auth/oauth/pending
Cookie: turnbase_oauth_pending=…
```

Reads the pending record. This is the only piece of the Google identity the frontend ever sees, and
it exists so `VW-OAUTHCOMP-001`'s form can render the provider email without the cookie needing to
carry it in cleartext JavaScript can read (§2).

```json
{ "email": "alice@example.com" }
```

`404` if the cookie is missing, malformed, or the Redis record has expired — the complete-registration
page has nothing left to show and sends the user back to `/auth/google` to restart.

---

## 6. `POST /api/auth/oauth/complete-registration` — create the account

```http
POST /api/auth/oauth/complete-registration
Content-Type: application/json
Cookie: turnbase_oauth_pending=…

{ "username": "alice" }
```

`Origin`-checked like every other state-changing endpoint (`rest-conventions.md`). Validates
`username` per `input-validation.md`'s full pipeline — the same skeleton uniqueness, `guest-` prefix
rejection (FR-AUTH-013) and script-mixing check (FR-AUTH-015) `IMP-M1-04` runs for credential
registration, since a Google-sourced account is not exempt from any of them.

One transaction:

1. `SELECT` whether `email` (from the pending record) is already held by a live account
   (`app_user_email_key`) — the check `data-model-accounts.md` §2 says the schema "forces" rather than
   leaves to a raw unique-violation.
2. **Not held** → insert `app_user` (`email_source = 'OAUTH'`), `user_auth_method` (`GOOGLE`,
   `provider_subject = sub`), default `user_privacy_settings`. This is the account-creation event
   `rate-limiting.md`'s Tier 5 OAuth line names — increment `rate:mint:register:{ip}` here, on
   success, exactly as `POST /api/auth/register` does. Issue a session, clear the pending cookie,
   `201` with `Location: /api/users/{username}` and the principal representation (`rest-conventions.md` § Authentication — `kind` is `REGISTERED`) as the body.
3. **Held by an active account** → create nothing. Instead, write `collisionUserId` onto the pending
   record (still under its original TTL — this does not extend it) and respond so the frontend can
   switch forms without a second round trip through Google:

   ```json
   { "outcome": "CHALLENGE_REQUIRED" }
   ```

   `200`, not `409` — this is not a failure, the same way `POST /api/friend-requests`'s `FRIENDS`
   outcome (`social-rest-api.md` §3) is a `201` rather than a `409` for the pending request it didn't
   create: the caller asked "finish my registration" and got a valid next step, not a rejected
   request. It does not disclose anything the caller does not already know either way: the email is
   the caller's own (it came from the Google account they just authenticated with), so telling them it
   already has a TurnBase account is not the disclosure FR-AUTH-016 forbids — that disclosure is about
   *other* people's accounts, which is exactly what §7's failure response protects.

**Why the collision is discovered here, not at `/auth/callback`.** Checking at the callback would
mean the pending record's shape depends on a fact the frontend never asked for and cannot act on
before it has even rendered a form; discovering it at the point where an account would otherwise be
created keeps `/auth/callback` a single, uniform "start the pending flow" step (§4) and puts the
branch where FR-AUTH-016 actually bites — the moment the platform would otherwise mint a duplicate.

---

## 7. `POST /api/auth/oauth/link-challenge` — resolve the collision

```http
POST /api/auth/oauth/link-challenge
Content-Type: application/json
Cookie: turnbase_oauth_pending=…

{ "password": "…" }
```

Only reachable after §6 has responded `CHALLENGE_REQUIRED` — the pending record's `collisionUserId`
must be set, or this is `404` (nothing to challenge; also the shape of a replayed or stale request).

Verifies `password` against `collisionUserId`'s `PASSWORD` `user_auth_method` row.

- **Success** → insert a `GOOGLE` `user_auth_method` row on `collisionUserId` (FR-AUTH-009 — an
  additional method, not a replacement), issue a session for that account, clear the pending cookie,
  `200` with `{ "outcome": "LINKED" }`. No Tier 5 accounting — no account was created, an existing one
  gained a login method, which is `IMP-M1-10`'s own linking duty rather than minting.
- **Failure** → `401`, the generic message `flows/01-arrival-and-account.md` §E requires ("a generic
  message that does not confirm which account exists") — identical in shape whether the password is
  wrong or `collisionUserId` itself does not exist, since distinguishing the two would confirm the
  account's existence by a side channel this document exists to close.

**Tier 1 applies.** `NFR-SEC-003` scopes IP-based lockout to "login, registration, password change,
auth method addition/removal", and resolving this challenge is exactly an auth-method addition gated
by a credential guess — the same abuse shape as login, on the same `rate:auth:{ip}` bucket
`rate-limiting.md` §Tier 1 already defines. `rate-limiting.md`'s Tier 1 "applies to" list gains this
endpoint (§8 below).

**No cap on attempts against the pending record itself beyond Tier 1.** The record's own TTL (§2)
already bounds how long a guess campaign against one collision can run; a second layer would only
duplicate Tier 1's job with a different key.

---

## 8. Changes to other documents

- **`rate-limiting.md` § Tier 1** — "Applies to" gains `POST /api/auth/oauth/link-challenge`,
  alongside the credential endpoints it already names. `rate-limiting.md` itself already documents
  that this list grows as the endpoints it covers are built (`STATUS.md` session 35's note on Tier 1's
  auth-method add/remove routes); this is the first one to land.
- **`rate-limiting.md` § Tier 4** — "Applies to" gains `GET /auth/google` and `GET /auth/callback`.
- **`local-environment.md` §7.4** gains five properties (§9 below).

---

## 9. Configuration surface (additions to `local-environment.md` §7.4)

| Property | Default | Env | Source |
|---|---|---|---|
| `turnbase.auth.oauth.state-ttl` | `5m` | `TURNBASE_AUTH_OAUTH_STATE_TTL` | §3 |
| `turnbase.auth.oauth.pending-registration-ttl` | `10m` | `TURNBASE_AUTH_OAUTH_PENDING_REGISTRATION_TTL` | §2 |
| `turnbase.oauth.google.authorization-endpoint` | `https://accounts.google.com/o/oauth2/v2/auth` | `TURNBASE_OAUTH_GOOGLE_AUTHORIZATION_ENDPOINT` | §3 |
| `turnbase.oauth.google.token-endpoint` | `https://oauth2.googleapis.com/token` | `TURNBASE_OAUTH_GOOGLE_TOKEN_ENDPOINT` | §4 |
| `turnbase.oauth.google.userinfo-endpoint` | `https://openidconnect.googleapis.com/v1/userinfo` | `TURNBASE_OAUTH_GOOGLE_USERINFO_ENDPOINT` | §4 |

`state-ttl` bounds only the round trip to Google's consent screen and back; `pending-registration-ttl`
bounds the time a user has to fill in `VW-OAUTHCOMP-001`'s form (or resolve a collision) afterward.
They are separate properties, not one, because the two windows are subject to different pressures — a
slow consent screen versus a user who walks away from the tab — and a future change to one must not
silently move the other.

**The three Google endpoints are fixed URLs, not per-environment configuration** — they are bound
properties purely so a test can point `GoogleOAuthClient` at a local stub instead of the real Google,
the same reason `artifact-store.endpoint` (`local-environment.md` §7.9) can point at a Testcontainers
MinIO instead of a real one.

---

## 10. Errors

| Condition | Status | `type` slug | Requirement |
|---|---|---|---|
| Malformed or missing `code`/`state` on the callback | `302` to `/login?oauthError=1` | — (redirect, no body) | — |
| `state` signature invalid or expired | `302` to `/login?oauthError=1` | — | — |
| Pending cookie missing, malformed, or expired | `404` | `not-found` | — |
| `link-challenge` with no `collisionUserId` on the pending record | `404` | `not-found` | — |
| Malformed body / missing `username` or `password` | `400` | `validation-failed` | — |
| Username fails `input-validation.md`'s pipeline | `400` | `validation-failed` | FR-AUTH-013…015 |
| Username skeleton already taken | `409` | — | FR-AUTH-003 |
| Wrong password, or no such collision account (`link-challenge`) | `401` | `unauthenticated` | FR-AUTH-016 |
| `Origin` present and not the platform origin, on either `POST` | `403` | `forbidden` | `rest-conventions.md` |
| Rate limit (Tier 4 on the two redirects, Tier 1 on `link-challenge`, Tier 5 on `complete-registration`'s success path) | `429` | `rate-limit-exceeded` | `rate-limiting.md` |

---

## 11. What is deliberately absent

- **No `state` refresh / retry endpoint.** An expired `state` restarts at `/auth/google`; there is
  nothing to resume, since nothing has been created yet.
- **No endpoint to abandon a pending registration explicitly.** The TTL (§2, §9) is the only cleanup;
  an abandoned pending record simply expires, and nothing references it in the meantime.
- **No separate "link Google to my existing account" entry point from account settings in this
  document.** `FR-AUTH-010`'s general "add an auth method from settings" is a different, already
  authenticated flow with its own item; the linking this document performs is specifically
  `FR-AUTH-016`'s unauthenticated collision path, reachable only from a pending record.

---

## 12. Requirements traceability

| Requirement | Realized by |
|---|---|
| FR-AUTH-007 | §3, §4, §6 |
| FR-AUTH-008 | §6 — `email_source = 'OAUTH'`; immutability itself is `data-model-accounts.md`'s and `PATCH /api/users/me`'s |
| FR-AUTH-009 | §7 success path |
| FR-AUTH-011 | Not built here — a linked account already has ≥1 method; removal's guard is `IMP-M1-04`'s / a future add/remove item's |
| FR-AUTH-012 | Unaffected by this document — `PATCH /api/users/me`'s existing `email_source` gate covers it |
| FR-AUTH-016 | §6 step 3, §7 |
| VW-LOGIN-002, VW-REG-002 | §3's hidden-when-absent note |
| VW-OAUTHCOMP-001…002 | §5, §6 |
| VW-REDIR-004…006 | §3 — reused, not re-specified |
