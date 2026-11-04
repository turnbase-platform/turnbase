# Archive — M1 Accounts and sessions

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim by `IMP-M20-01`. Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M1-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M1-01 | Error model, REST conventions, validation harness | platform | M0-03 | DONE |
| IMP-M1-02 | Rate limiter (Tiers 1–5) | platform | M1-01 | DONE |
| IMP-M1-03 | JWT key set, issuance, rotation | platform | M0-09 | DONE |
| IMP-M1-04 | Credential registration and login | platform | M1-01, M1-03 | DONE |
| IMP-M1-05 | Guest minting and purge | platform | M1-04 | DONE |
| IMP-M1-06 | Session lifecycle and displacement | platform | M1-04 | DONE |
| IMP-M1-07 | Profiles and privacy settings | platform | M1-04 | DONE |
| IMP-M1-08 | Account deletion and erasure | platform | M1-07 | DONE |
| IMP-M1-09 | Social graph — friendships and requests | platform | M1-07 | DONE |
| IMP-M1-10 | Google OAuth registration and login | platform | M1-04 | DONE |
| IMP-M1-11 | Account read and auth-method management | platform | M1-10 | DONE |

---

## M1 — Accounts and sessions

### IMP-M1-01 — Error model, REST conventions, validation

**Repo:** `turnbase-platform` · **Depends on:** IMP-M0-03

**Read first:**
- `docs/specs/api-design/rest-conventions.md`
- `docs/specs/api-design/error-handling.md` — especially the **type taxonomy, which is a closed set**
- `docs/specs/api-design/input-validation.md`
- `docs/specs/api-design/pagination-filtering-sorting.md`

**Satisfies:** `user-accounts.md` NFR-SEC-005; `game-rooms.md` NFR-USAB-001; `game-catalog.md`
NFR-USAB-001…002

**Done when:** one `@RestControllerAdvice` produces the single RFC 9457 error shape defined in
`error-handling.md` for every failure class; Bean Validation failures map to it; the pagination
contract is implemented once as a reusable type; an integration test asserts the exact response body
for each error class, including `room-unavailable-retry` and its `retryAfterMs` member.

**This item defines the shape every later endpoint conforms to. Build it before any endpoint.**

**The problem-type taxonomy is closed.** A new failure mode does not get a new `type` URI invented at
the call site — it gets registered in `error-handling.md` first. Every unregistered type is a client
branch nobody wrote.

---

### IMP-M1-02 — Rate limiter, Tiers 1–5

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-01

**Closed:** IMP-GATE-36 (opened and closed 2026-09-08, session 35) — `secrets-and-configuration.md`'s
inventory (§1) and its own "### Redis" section (§4) required `requirepass`, one password shared by
the monolith and the Game Host, and `docker-compose.yml`'s `redis` service already enforced it
(`TURNBASE_REDIS_PASSWORD`) — but no document named the Spring property that carries it into a
running service (unlike the PostgreSQL section two headings above, which names
`TURNBASE_DB_APP_PASSWORD` → `SPRING_DATASOURCE_PASSWORD` explicitly), `local-environment.md` §7.9's
`spring.data.redis.url` row showed a bare `redis://redis:6379` default with no credentials, and the
`platform` service's own environment block in `docker-compose.yml` set no Redis-related variable at
all. Fixed: `secrets-and-configuration.md` § Redis now names `spring.data.redis.password`
(`SPRING_DATA_REDIS_PASSWORD`) as the carrier, kept separate from the URL the same way
`spring.datasource.password` is kept separate from `spring.datasource.url`; `local-environment.md`
§7.9 gained the corresponding row. Wiring `docker-compose.yml`'s `platform` service to actually pass
both is this item's own implementation work, not a further spec fix.

**Read first:**
- `docs/specs/api-design/rate-limiting.md` — Tiers 1–5, *Client identity: deriving the IP*, the 429
  response shape
- `docs/specs/deployment/local-environment.md` §7.6

**Satisfies:** `user-accounts.md` NFR-SEC-003, NFR-SEC-007

**Done when:** each tier's bucket, key, limit and window match the spec; breaches return the
`error-handling.md` shape with `429` and the stated headers; buckets are held in Redis. Tier 6
(WebSocket frames) is IMP-M2-02.

**Tier 5 counts successes, not attempts.** Account minting is limited by how many accounts an IP
actually created; counting attempts lets a failing client exhaust its own budget and lets a
successful one mint freely.

**Done 2026-09-08 (session 35).** One `common.RateLimitInterceptor` covers all five HTTP tiers.
Tiers 2-4 share a plain Bucket4j capacity/window bucket (`Bandwidth.simple`) resolved through a
`ProxyManager<byte[]>` built directly from a raw Lettuce `RedisClient`
(`common.RedisRateLimiterConfig`) — independent of `spring-boot-starter-data-redis`'s own
`LettuceConnectionFactory`, which Bucket4j's proxy manager cannot use directly. Tier 2 alone emits
`X-RateLimit-Limit/Remaining/Reset`. Tier 5 (account minting) pre-consumes a token in `preHandle` and
refunds it in `afterCompletion` when the response is non-2xx, which is what makes it success-only
without a check-then-consume race. Tier 1 (auth failures) is a hand-rolled `StringRedisTemplate`
counter plus a separate lockout key with the doubling duration, entirely independent of Tier 5's
counter even though both apply to `POST /api/auth/register` simultaneously. `common.ClientIpResolver`
implements the two-sided trusted-proxy policy (`X-Forwarded-For` honoured only from a peer inside
`turnbase.security.trusted-proxies`) and IPv6 /64 keying, with a dependency-free CIDR matcher.
Endpoint classification is exact-match against routes that exist today (the same convention
`session.SessionAuthenticationInterceptor` uses) — Tier 3's upload-version-create route
(`IMP-M4-03`), Tier 1's auth-method add/remove and Tier 5's OAuth callback (`IMP-M1-10`) are none of
them built yet, and each item extends the matching set when it lands.

**First Redis consumer in `turnbase-platform`, which is what opened and closed `IMP-GATE-36`** (see
above) before any code could be written. `local-environment.md` §7.9 and `secrets-and-configuration.md`
§ Redis are fixed; `docker-compose.yml`'s `platform` service and the Helm chart's
configmap/secret both now carry `SPRING_DATA_REDIS_URL`/`SPRING_DATA_REDIS_PASSWORD`.
`conventions.md` §7's `concern=application` tag is applied via `common.RateLimitMetrics`, wrapping
every Redis call this item makes (`turnbase_redis_operation_seconds`/`_errors_total`).

**Verified end to end.** `ClientIpResolverTest` (unit) proves the trusted-proxy/XFF policy and the
IPv6 /64 masking directly. `RateLimitInterceptorIT` (Testcontainers Postgres + Redis, real HTTP)
boots its own tiny-limit context per test: Tier 5 rejects over-cap minting with `Retry-After` and
refunds a validation failure rather than counting it; Tier 1 locks out after the configured failure
count and recovers once the lockout elapses; Tier 2 emits the three headers and 429s on the third
request; Tier 4 caps an unauthenticated profile read; disabling the switch under the `test` profile
is honoured. `PostgresIntegrationTest` gained a shared Redis Testcontainer
(`@ServiceConnection(name = "redis")`, no official Testcontainers Redis module exists) so every
full-boot `*IT` can reach one; the four existing classes that drive `/register`/`/guest` repeatedly
(`AuthControllerIT`, `ProfileControllerIT`, `SocialControllerIT`, `AccountDeletionControllerIT`)
needed generous Tier 1/5 overrides to keep passing once real budgets were enforced — the same
per-property escape hatch `local-environment.md` §8 describes for e2e, applied per test class instead
of wholesale. `./mvnw verify -Pintegration` green locally (85 integration tests). **CI green on
`turnbase-platform` `master`** (`build`, 11m10s).

**No specification defect found beyond IMP-GATE-36.** `rate-limiting.md` settled every tier's
bucket/key/limit/window precisely enough to implement without a further gap; which Redis client
library (Lettuce, matching `spring-data-redis`'s own choice) and which Bucket4j module
(`com.bucket4j:bucket4j_jdk17-lettuce`) are implementation detail no document claims to settle.

---

### IMP-M1-03 — JWT key set, issuance and rotation

**Repo:** `turnbase-platform` · **Depends on:** IMP-M0-09

**Done 2026-09-06 (session 28).** `JwtService` issues HS256 tokens (jjwt) carrying `sub`/`jti`/`kid`
per §3.5, signed with the current active key from `JwtKeySetManager` — the mutable wrapper this item
adds around `IMP-M0-09`'s immutable `JwtKeySet` bean, needed because §3.3's rotation changes the set
while the process keeps running. Verification resolves the signing key by the token's `kid` header
against active-or-retired via a jjwt `Locator`, so a token signed under a just-retired key keeps
validating. `JwtKeyRotationService.promote()`/`retire(kid)` implement §3.3's three steps; `retire`
revokes every `user_session` row still bound to that `kid` (`revoked_reason = 'KEY_ROTATED'`) in the
same transaction the key disappears from the set, via a plain-JDBC `UserSessionRepository`
(`JdbcClient` — no ORM in this repo, `IMP-M0-06`'s own note). `JwtKeySetManagerTest`/`JwtServiceTest`
(unit) and `JwtKeyRotationServiceIT` (Testcontainers Postgres, full application boot) prove the
Done-when clause directly: a token issued under the original key still verifies after that key is
promoted to `retired`, and retiring it revokes exactly the session bound to it while a session on the
new active key is untouched. `./mvnw verify` and `-Pintegration` both green locally; **CI green on
`master`** (build, 5m36s).

**No registration/login endpoint exists yet** (`IMP-M1-04`) to produce a real session through the
ordinary flow, so `JwtKeyRotationServiceIT` inserts a minimal `app_user`/`user_session` fixture
directly — this item owns the key set and the session-revocation mechanics, not the endpoints that
create these rows once `IMP-M1-04` lands.

**No specification defect found.** §3 named the algorithm, claim shape and three-step rotation
precisely enough to implement without a gap; the one judgement call this item made — which JWT
library (`io.jsonwebtoken:jjwt` 0.12.6) and which persistence primitive (`JdbcClient`, matching the
jdbc-not-JPA choice `IMP-M0-06` already recorded) — is implementation detail no document claims to
settle, not an underspecified requirement.

**Read first:**
- `docs/specs/deployment/secrets-and-configuration.md` §3 (JWT signing keys, in full)
- `docs/specs/platform/data-model-accounts.md` §3 (`user_session`)
- `docs/specs/api-design/rest-conventions.md` § *Authentication*

**Satisfies:** `user-accounts.md` FR-SESS-001, FR-SESS-004; `platform-operations.md` FR-CRED-001…004

**Done when:** tokens carry a key id; verification accepts both the current and the previous key;
rotation is exercised by a test that verifies a token issued under the retired key still validates
until its expiry, and that `user_session.revoked_reason` records key-rotation revocation.

**Watch the ID collision:** `FR-SESS-001` and `FR-SESS-003` are each defined in **both**
`user-accounts.md` and `platform-architecture.md` with unrelated meanings. Here, `user-accounts.md`
is the one you want.

---

### IMP-M1-04 — Credential registration and login

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-01, IMP-M1-03

**Done 2026-09-06 (session 29).** `POST /api/auth/register` and `POST /api/auth/login`
(`AuthController`, `account` package). `UsernamePolicy` runs `input-validation.md`'s canonicalization
pipeline plus ICU4J `SpoofChecker` at `MODERATELY_RESTRICTIVE` for FR-AUTH-015's single-script rule,
computes the `getSkeleton(caseFold(NFC(username)))` uniqueness key, and rejects the `guest-` prefix on
that same skeleton (FR-AUTH-013). `CredentialPolicy` validates email (FR-AUTH-002) and password
(FR-AUTH-005) shape. Registration is one transaction (`AccountRepository.insertRegisteredUser`,
`@Transactional`) inserting `app_user`/`user_auth_method`/`user_privacy_settings`; a unique-index
violation is mapped to `ConflictException` by matching the constraint name in Postgres's own error
text (`app_user_email_key` vs `app_user_skeleton_key`) rather than a compile-time dependency on the
driver's exception type, which stays at `runtime` scope. Passwords are Argon2id via
`Argon2PasswordEncoder(16, 32, 1, 19456, 2)` per `input-validation.md`'s explicit cost parameters — the
no-argument constructor input-validation.md itself rejects as too weak.

**New `session.SessionService`** — the public API a principal-resolving flow calls to get a session —
implements `data-model-accounts.md` §3's atomic displace-then-insert (FR-SESS-001/002/003): revoke
whatever session is active for the user, insert the new row, retry (bounded, 5 attempts) on the
partial-unique-index race between two concurrent logins. Both `RegistrationService` and `LoginService`
call it *after* their own transaction commits, never inside it, per this repo's "commit before publish"
rule. `rest-conventions.md`'s newly-named `turnbase_session` cookie (`common.SessionCookie.NAME`,
IMP-GATE-27) is set `HttpOnly; Secure; SameSite=Strict; Path=/` with `maxAge` from the session's actual
`expiresAt`.

**Verified end-to-end, not unit-tested in isolation.** `UsernamePolicyTest`/`CredentialPolicyTest`
(unit) prove the validation/skeleton rules directly, including that case variants of one username
share a skeleton and that a confusable lookalike of `guest-` is still caught. `AuthControllerIT` boots
the real application against Testcontainers Postgres and drives both endpoints over real HTTP: the
three rows land correctly, a duplicate username/email each produce their own 409 message, the reserved
prefix and a mismatched password confirmation both produce 400, login succeeds by username or by
email, a wrong password and an unknown identifier both produce the identical generic 401, and — the
FR-SESS-003 clause itself — a second login revokes the first session's row (`revoked_reason =
'DISPLACED'`) while leaving exactly one active session for the account. `./mvnw verify` and
`-Pintegration` both green locally; **CI green on `master`** (build, 7m59s).

**No specification defect found in the credential-auth path itself.** Two were found and closed
opening the item — see `IMP-GATE-26`/`IMP-GATE-27` below, both opened and closed this session.

**Two runtime dependencies neither `input-validation.md` nor `conventions.md` names, because they are
transitive gaps in libraries the documents *do* name, not choices made here:**
`Argon2PasswordEncoder` delegates to Bouncy Castle's Argon2 implementation
(`org.bouncycastle.crypto.params.Argon2Parameters$Builder`) at runtime — `spring-security-crypto`
keeps `bcprov-jdk18on` optional since not every consumer hashes with Argon2 — so registering a user
threw `NoClassDefFoundError` until it was added explicitly (`runtime` scope, pinned `1.85.2`, not
managed by the Spring Boot BOM). ICU4J itself needed no such fix; only the SpoofChecker API shape
(`failsChecks(String)`, `getSkeleton(CharSequence)`, `Builder.setChecks`/`setRestrictionLevel`) had to
be read from the actual `78.3` jar rather than assumed.

**No OAuth here.** `FR-AUTH-007…012`/`016` and the Google round trip are `IMP-M1-10`, split out by
`IMP-GATE-26` below — this item's own read-list and Done-when never covered them.

**Closed:** IMP-GATE-26 (opened and closed 2026-09-06, session 29) — this item's *Satisfies* claimed the full
`FR-AUTH-001…016` range, which includes six OAuth requirements (`FR-AUTH-007…012`, `FR-AUTH-016`) and
`VW-OAUTHCOMP-001…002`, but the *Done when* clause never mentioned OAuth — no `/auth/callback`, no
`/auth/complete-registration`, no Google client, no `state` handling — and the read-list didn't even
carry `secrets-and-configuration.md` §5, the document naming the OAuth client secret's config key
(`TURNBASE_OAUTH_GOOGLE_CLIENT_SECRET`) an implementation would need. `platform-operations.md`'s own
account of the OAuth client secret states "Google login is unavailable without it... credential login
(FR-AUTH-006) is complete on its own" — i.e. the two are already understood as separable features, so
Google OAuth (a full external round trip: consent screen, code exchange, `state` signing, the
FR-AUTH-016 collision-and-link path) not fitting the same *Done when* as credential auth is not a
surprise, it just was never given its own item. Fixed: this item is retitled *Credential registration
and login* and narrowed to what its *Done when* actually checks — `FR-AUTH-001…006, 011, 013…015`,
dropping the six OAuth-only IDs and `VW-OAUTHCOMP-001…002`. **IMP-M1-10** (new, below) owns Google
OAuth end to end, depending on this item for the `user_auth_method`/session-issuance machinery it
reuses. `VW-LOGIN-001…004`/`VW-REG-001…003` stay split across both — the credential form and page
shell here, the OAuth button and its endpoint in `IMP-M1-10`.

**Closed:** IMP-GATE-27 (opened and closed 2026-09-06, session 29) — building the endpoints that set
the session cookie (`user-accounts.md` CON-004) needs `rest-conventions.md`'s Authentication section,
which was missing from this item's read-list entirely — a registry defect independent of IMP-GATE-26.
Reading it surfaced a second gap: no document anywhere in the corpus names the cookie itself — its
`httpOnly`/`Secure`/`SameSite=Strict` properties are specified, but never its name. Every future item
that reads the cookie back (the STOMP handshake in `IMP-M2-02`, the SSE endpoint in `IMP-M5-03`, any
authenticated-route filter) needs the same string this item picks when setting it, and nothing forced
that agreement. Fixed: `rest-conventions.md`'s Authentication section now names it —
`turnbase_session`, `Path=/` — as a fixed protocol constant, not a `local-environment.md` §7 tunable:
a name two server-side code paths must agree on is not something an operator should be able to change
independently. Read-list corrected to include `rest-conventions.md`.

**Read first:**
- `docs/requirements/user-accounts.md` — FR-AUTH-001…006, FR-AUTH-011, FR-AUTH-013…015, FR-ACCT-001,
  NFR-SEC-001…003, 005…007
- `docs/specs/platform/data-model-accounts.md` §1 (`app_user`), §2 (`user_auth_method`)
- `docs/specs/api-design/input-validation.md` — the field catalogue and canonicalization
- `docs/specs/api-design/rest-conventions.md` — Authentication section (the session cookie's shape
  and name)
- `docs/specs/flows/01-arrival-and-account.md` §A, §D (§E is `IMP-M1-10`'s)

**Satisfies:** `user-accounts.md` FR-AUTH-001…006, FR-AUTH-011, FR-AUTH-013…015, FR-ACCT-001,
NFR-SEC-001…003, NFR-SEC-005…007; `platform-views.md` VW-LOGIN-001, VW-LOGIN-003…004, VW-REG-001,
VW-REG-003

**Done when:** registration and login endpoints exist with the validation rules of
`input-validation.md`; uniqueness is enforced by a database constraint **and** surfaced as a domain
error rather than a constraint-violation 500; passwords are Argon2 (NFR-SEC-001); a user always
retains at least one active auth method (FR-AUTH-011); login displaces the previous session per
`user-accounts.md` FR-SESS-003.

**FR-AUTH-015's homograph rule is a canonicalization problem, not a regex.** Compare usernames on
their canonical form, and store both the display form and the canonical form — a check applied only
at write time is bypassed by every later rename path.

---

### IMP-M1-05 — Guest minting and purge

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-04

**Done 2026-09-08 (session 31).** `POST /api/auth/guest` (`account.AuthController`) mints a
credential-free guest — `account.GuestService.mint` inserts `kind='GUEST'`, a
`guest-<serial>` username drawn from `guest_serial_seq` (`account.AccountRepository.insertGuestUser`),
no `user_auth_method` row and no `user_privacy_settings` row — then issues a session through the same
`SessionService.issueSession` registration and login already use, so the response is a `201` with the
session cookie set, identical in shape to registration's. Exempt from NFR-SEC-006 per `IMP-GATE-29`.

`account.GuestPurgeJob` runs the two-phase purge on `turnbase.jobs.guest-cleanup.interval`, under
`net.javacrumbs.shedlock`'s `@SchedulerLock` over the baseline's `shedlock` table (FR-JOB-005 — the
first scheduled job in this repo, so also the first to need it). Revoke phase:
`session.SessionService.revokeAllForUser` first (the actual inaccessibility mechanism —
`SessionAuthenticationFilter` never consults `app_user`), then `account.GuestPurgeRepository.markExpired`
sets `deleted_at`/`deletion_reason='GUEST_EXPIRED'`/`purgeable_after`. Purge phase
(`purgeUnreferencedGuests`) hard-deletes anything purgeable with no `room_participant` or
`room.host_user_id` reference, in the same run — `purgeable_after` is set to the revoke instant, not a
future deadline, per `data-model-accounts.md` §1's "not on a timer".

**Verified end to end.** `UsernamePolicyTest` covers the guest-skeleton method directly.
`AuthControllerIT` gained two tests: guest mint issues a working, credential-free, immediately
authenticated session with a unique serial. `GuestPurgeJobIT` proves all three `Done when` clauses
against a real Postgres: revoke phase (session revoked, event published, `app_user` marked — checked
against a room-seated guest so the purge phase in the same run doesn't remove the row first), the
unreferenced case (hard-deleted in the same run), and the load-bearing case — a guest seated in a live
room survives the purge phase indefinitely. `./mvnw verify -Pintegration` green locally (73 unit + 45
integration tests); CI green on `turnbase-platform` `master` (`build`, 8m3s — `e2e` stays blocked on
the same un-provisioned `TURNBASE_GAME_HOST_PAT` prior sessions' runs also show).

**Closed:** IMP-GATE-29 (opened and closed 2026-09-08, session 31) — `user-accounts.md` NFR-SEC-006
enumerated the endpoints exempt from session authentication ("the landing page, the login endpoint,
the registration endpoint, user profile pages, the game catalog, game detail pages") and omitted guest
creation, but `docs/specs/api-design/rest-conventions.md`'s Authentication section derives its own
"except" set from that exact list, and its idempotency section separately states `POST /api/auth/guest`
is "an unauthenticated `POST`" outright, matching `rate-limiting.md`'s Tier 5 text. A caller minting a
guest account has by definition no session yet, so the endpoint cannot require one — the omission was
not a defensible narrower reading, since satisfying NFR-SEC-006 literally would make FR-GUEST-001
unreachable. Fixed: NFR-SEC-006 now names the guest-creation endpoint alongside login and
registration, with the reason (no session exists yet to require) inline so the next reader doesn't
re-derive it.

**Closed:** IMP-GATE-30 (opened and closed 2026-09-08, session 31) — this item's *Satisfies* claimed
the full `FR-GUEST-001…010` range, but FR-GUEST-010 ("Guest profile display... only the username")
needs a `GET /api/users/{username}` profile-read endpoint that does not exist yet — that build is
`IMP-M1-07`'s (`FR-PROF-001…008`), which was never a dependency here. `user-accounts.md` FR-PROF-002
("Guest profile display") states the identical duty ("displays only the username... all other
profile fields... are not shown") under a different ID in the same document — a duplicate
`docs/requirements/INDEX.md` doesn't track, since it only lists prefix collisions *across*
documents — not a second requirement to satisfy separately. Same shape as
`IMP-GATE-08`/`IMP-GATE-18`/`IMP-GATE-28`. Fixed: this item's
*Satisfies* narrowed to `FR-GUEST-001…009`; `IMP-M1-07`'s *Satisfies* below gained `FR-GUEST-010`
alongside its existing `FR-PROF-002`, recording that the one endpoint discharges both IDs.

**Read first:**
- `docs/requirements/user-accounts.md` FR-GUEST-001…009, NFR-SEC-006
- `docs/specs/platform/data-model-accounts.md` §1 (the `kind` discriminator)
- `docs/requirements/platform-operations.md` FR-RET-002 (the guest purge window)
- `docs/specs/deployment/local-environment.md` §7.3
- `docs/specs/api-design/rest-conventions.md` § Authentication (`POST /api/auth/guest`'s route,
  status code and response shape — the read-list omitted the one document naming the endpoint itself)

**Satisfies:** `user-accounts.md` FR-GUEST-001…009; `platform-operations.md` FR-RET-002

**Done when:** a guest principal can be minted without registration; guest serials are unique
(FR-GUEST-002); guests have no auth method, no friends, no statistics and no uploads (FR-GUEST-004,
007, 008, 009); the purge is **two-phase** and a guest seated in a live room is never removed — a
literal 24-hour delete fails permanently on `room_participant`'s FK, and the cascade that would
"fix" it removes a seated player from a live game. The real bound is ~8 days.

---

### IMP-M1-06 — Session lifecycle and displacement

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-04

**Done 2026-09-08 (session 30).** `session.SessionAuthenticationFilter` resolves the
`turnbase_session` cookie against `user_session` on every request — JWT verify, then the DB row's
`revoked_at`/`expires_at` — and wraps the request with a `common.AuthenticatedUser` principal on
success, or records why not (`invalid`, `expired`, or the row's own `revoked_reason`) on a request
attribute. It never rejects anything itself; ordered ahead of `CorrelationIdFilter` so the latter's
`userId` MDC value sees a resolved principal rather than running before one exists.
`session.SessionAuthenticationInterceptor` is the actual enforcement — a `HandlerInterceptor`
(the `RequestSizeInterceptor` pattern, so a rejection reaches `GlobalExceptionHandler` through the
same path as every other domain failure): a protected path with no principal throws
`UnauthenticatedException`, with FR-SESS-004's own wording when the reason is `DISPLACED`
("...because you logged in from another device"). NFR-SEC-006's exempt list, `PUBLIC_PATHS`, holds
exactly what has a server-side route today (`register`, `login`); `/test/` is separately exempt for
`IMP-M1-01`'s `GlobalExceptionHandlerIT` harness, which isn't a platform endpoint at all.

`GET /api/auth/session` and `POST /api/auth/logout` complete `rest-conventions.md`'s four-endpoint
session lifecycle table — the third and fourth existing only from this item on. `SessionService`
gained `revoke(sessionId, userId, reason)` for logout, symmetric with `issueSession`'s displacement:
both now publish `session.SessionRevokedEvent(sessionId, userId, reason)` **after** their own
transaction has committed (a plain post-commit call, not a `@TransactionalEventListener` — the
transaction is already committed by the time `issueSession`/`revoke` return, so there was no reason
to reach for the annotation). The event is the mechanism `IMP-M2-02` and `IMP-M5-03` subscribe to
once their connection registries exist (`IMP-GATE-28`).

**Verified end to end.** `SessionAuthenticationFilterTest`/`SessionAuthenticationInterceptorTest`
(unit, Mockito + `spring-test`'s `MockHttpServletRequest`) prove the filter's per-outcome attribute
and the interceptor's per-reason message directly. `AuthControllerIT` gained: a second login
publishing a `DISPLACED` `SessionRevokedEvent` for the first session; `GET /session` returning the
principal when authenticated and the generic 401 with no cookie; `POST /logout` revoking the row
(`revoked_reason = 'LOGOUT'`), clearing the cookie, and publishing the `LOGOUT` event; and a request
bearing the *first* session's cookie after a second login receiving exactly FR-SESS-004's wording.
`./mvnw verify -Pintegration` green locally (71 unit + 40 integration tests, JaCoCo merged gate
met); CI green on `master` (`build`, 9m0s — `e2e` remains blocked on the un-provisioned
`TURNBASE_GAME_HOST_PAT`, the same pre-existing gap `IMP-M1-04`'s run also shows, `conventions.md`
§3).

**Closed:** IMP-GATE-28 (opened and closed 2026-09-08, session 30) — this item's *Satisfies* claimed
`FR-SESS-010` in full, but the requirement's actual duty — closing a session's live WebSocket/SSE
connections on revocation, "after emitting a frame stating the reason" — needs a connection registry
to close, and none exists yet: `IMP-M2-02` (STOMP) and `IMP-M5-03` (SSE) are both still `READY`, and
this item has neither as a dependency. Worse, `IMP-M5-03`'s own *Satisfies* didn't claim `FR-SESS-010`
at all, despite SSE being one of the two connection types the requirement names — so no item's
*Done when* actually required the close-on-revocation behaviour anywhere in the registry. Same shape
as `IMP-GATE-08`/`IMP-GATE-18`: a *Done when* clause reaching past infrastructure that doesn't exist
yet. Fixed: this item's *Satisfies* narrows to `FR-SESS-001…004, FR-SESS-011` — what it actually
builds is the revocation write and a `SessionRevokedEvent` a connection registry can subscribe to, not
the close itself. `IMP-M2-02`'s *Done when* gains the STOMP-side close-on-revocation clause (it already
claimed `FR-SESS-010`). `IMP-M5-03`'s *Satisfies* now also claims `FR-SESS-010`, its *Done when* gains
the SSE-side close-on-revocation clause, and `IMP-M1-06` is added to its *Depends on* — it needs the
event type this item publishes.

**Read first:**
- `docs/requirements/user-accounts.md` FR-SESS-001…004, FR-SESS-010…011
- `docs/specs/platform/data-model-accounts.md` §3 (`user_session`)
- `docs/specs/api-design/rest-conventions.md` § *Authentication*
- `docs/specs/api-design/websocket.md` § *Authentication*; `docs/specs/api-design/sse-notifications.md`
  § *Endpoint*

**Satisfies:** `user-accounts.md` FR-SESS-001…004, FR-SESS-011

**Done when:** at most one active session per account holds as a **database** invariant, not as a
service-layer check (FR-SESS-002); a new login revokes the previous session and writes
`user_session.revoked_reason` (FR-SESS-003); a request bearing an invalidated token receives the
`error-handling.md` 401 shape (FR-SESS-004); logout revokes (FR-SESS-011); every path that revokes a
session (displacement, logout) publishes a `SessionRevokedEvent(sessionId, userId, reason)` after its
own transaction commits — the mechanism `IMP-M2-02`'s STOMP registry and `IMP-M5-03`'s SSE registry
subscribe to once they exist. This item has no live connection to close, so FR-SESS-010's actual duty
is proved there, not here.

**FR-SESS-010 authenticates a WebSocket or SSE connection once, at handshake — and that is the
trap.** A long-lived connection is not re-checked per frame, so revoking a session does nothing to a
socket that is already open unless revocation *pushes* a close to it. Displacement must terminate the
displaced session's live connections; a check-on-next-frame design silently keeps the old device
connected for as long as it stays quiet.

**ID collision:** `FR-SESS-001`/`003` also exist in `platform-architecture.md` meaning something
else. `user-accounts.md` is the one that governs here.

---

### IMP-M1-07 — Profiles and privacy settings

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-04

**Done 2026-09-08 (session 32).** `account.ProfileController` (`/api/users`) adds four endpoints
alongside `AuthController`'s. `GET /{username}` (`ProfileService.view`, exempt from
`SessionAuthenticationInterceptor` via the new `isPublicProfileRead` path match, since the route
carries a variable segment `PUBLIC_PATHS`'s literal set can't match) resolves privacy **server-side**
against `ProfileRepository.findBySkeleton`'s single query: a soft-deleted row returns the FR-ACCT-009
placeholder (`{"username","deleted":true}`, checked before kind so a purged guest gets it too), a
`GUEST` row returns username-only (FR-GUEST-010), the owner (viewer id equals the row's) always gets
every section regardless of settings (FR-PROF-007), a private non-owner view gets none, and otherwise
`visibleSections` names only the sections not `HIDDEN` — `@JsonInclude(NON_NULL)` plus a *named*
(not boolean) section set is what makes "omits hidden sections" literal rather than a client-trust
convention. `PATCH /me` (FR-ACCT-002/003) updates username and/or email in one call, each against its
own `username_changed_at`/`email_changed_at` window (`AccountProperties.renameWindow`, already wired
by `IMP-M0-09`), rejecting an OAuth-sourced email outright. `POST /me/password` (FR-ACCT-010) and
`PATCH /me/privacy` (FR-PROF-004/006/008) round out the surface; all three `/me/**` mutations 403 for
a `GUEST` principal, which has no `user_auth_method` row to change a password against and no
`user_privacy_settings` row to patch (`data-model-accounts.md` §4: "a row exists only for registered
users").

**The friends section's third value, `FRIENDS_ONLY` (`social-friends.md` FR-SOC-017), resolves as
hidden for every non-owner viewer for now** — the confirmed-friendship check it needs is
`IMP-M1-09`'s, which depends on this item and does not exist yet. Recorded as a sentence on
`IMP-M1-09`'s own section below (same pattern as `IMP-M0-10`'s forward obligations) rather than a
gate, since it does not make this item's own Done-when unsatisfiable as written.

**Verified end to end.** `ProfileControllerIT` (13 tests, real Postgres): owner-sees-everything while
private, a private profile showing zero sections to another viewer, a public profile hiding only its
`HIDDEN` sections, an unauthenticated read of a public profile, the guest-only shape, the deleted
placeholder (not a 404), an unknown username *is* a 404, the username-window enforcement (success,
then a same-window rejection as `422`, then a duplicate as `409`), password change (wrong current
password `422`, correct one `204` and the new password logs in), and a guest `403` on the privacy
route. `./mvnw verify -Pintegration` green locally (91 unit + 58 integration tests, full suite); CI
green on `turnbase-platform` `master` (`build`, 6m34s — `e2e` stays blocked on the un-provisioned
`TURNBASE_GAME_HOST_PAT`, the same pre-existing gap every prior session's run also shows).

**Closed:** IMP-GATE-31 (opened and closed 2026-09-08, session 32) — no document in the corpus named a
route for FR-ACCT-002 (username update) or FR-ACCT-003 (email update); `rest-conventions.md`'s
"self-scoped account routes" named `POST /api/users/me/password` and `PATCH /api/users/me/privacy`
but nothing for the two other FR-ACCT mutations this item must satisfy. This item's own read-list
also never named `rest-conventions.md` at all, despite it being the document that supplies the
routes/status codes for every endpoint this item builds (`GET /api/users/{username}`, the password and
privacy routes above). Fixed: `rest-conventions.md` gained `PATCH /api/users/me` — one endpoint for
both username and email, each enforcing its own rolling 30-day window independently, email rejected
outright when OAuth-sourced (FR-AUTH-008/012); read-list corrected to include it.

**Read first:**
- `docs/requirements/user-accounts.md` FR-PROF-001…008, FR-ACCT-002…003, FR-ACCT-009…010
- `docs/specs/platform/data-model-accounts.md` §1, §4 (`user_privacy_settings`)
- `docs/requirements/platform-views.md` VW-PROF-001…008, VW-SET-001…007 — the rendering contract the
  API must be able to satisfy
- `docs/specs/api-design/rest-conventions.md` § Authentication (the self-scoped account routes) and
  § Authorization and Ownership (the `/api/users/**` predicates) — omitted from the original read-list

**Satisfies:** `user-accounts.md` FR-PROF-001…008, FR-ACCT-002…003, FR-ACCT-009…010, FR-GUEST-010
(`IMP-GATE-30`: FR-PROF-002 and FR-GUEST-010 are the same "guest profile shows only the username"
duty under two IDs — the `GET /api/users/{username}` endpoint built here discharges both)

**Done when:** privacy is evaluated **server-side on every read** and the response omits hidden
sections rather than returning them for the client to hide; **the owner is exempt from every one of
their own privacy settings** (FR-PROF-007, and IR-05's five conditions in `platform-views.md`
VW-PROF-002…003 and VW-FREN) — a private profile, a hidden section and a hidden friend list all
render in full to the person who set them; the 30-day username and email change limits are enforced
against a stored timestamp rather than a counter; a soft-deleted user's profile returns the
FR-ACCT-009 placeholder rather than a 404; a guest profile returns the username and nothing else
(FR-GUEST-010).

---

### IMP-M1-08 — Account deletion and erasure

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-07

**Done 2026-09-08 (session 33).** `account.AccountDeletionService`/`AccountErasureRepository` add
`DELETE /api/users/me`. One `@Transactional` JDBC method disposes of every row in
`data-model-accounts.md` §5's table, in the order the spec states — `user_session` revoked
(`ACCOUNT_DELETED`), `user_auth_method` and `user_privacy_settings` deleted, `friendship` and
`friend_request` deleted both directions, `room_invitation` deleted both legs (cascading the
recipient's/inviter's `notification`), the caller's own `notification` rows deleted, any open
`game_review` on an owned game withdrawn (`decided_by = 'system'`), owned `game` rows archived,
`game_history_entry` pseudonymized with a fresh `UUID.randomUUID()` subject token (not derived —
ADR-0004 forbids a reversible construction), `app_user` soft-deleted (`deletion_reason =
'SELF_SERVICE'`, email released, username/skeleton retained per FR-ACCT-006), and
`room_participant` departures last. Room closure/host-transfer is deliberately not attempted here —
`room-lifecycle.md` §5.1 duty 2 on the owning instance discharges it within one sweep interval, since
this REST-triggered transaction holds no room claim. `user_session` is written directly rather than
through `session.SessionService` (which manages its own transaction boundary) precisely so the whole
disposition table is one physical transaction; `SessionRevokedEvent` is published for each revoked
session only after that transaction commits, closing live connections per FR-SESS-010. Guests get
`403`, matching every other `/me/**` mutation this repo builds.

**Verified end to end.** `AccountDeletionControllerIT`: every disposition-table object seeded and
checked after a real `DELETE` call against real Postgres — session revoked and the event published,
auth method and privacy settings gone, friendship/friend-request/room-invitation gone, the deleted
user's own notification gone, the open review withdrawn as `system`, the owned game archived, the
history entry pseudonymized with `user_id` nulled, the room-participant row showing a `LEFT`
departure with `lost_announced_at` still null, username retained and email released on the `app_user`
row. A second `DELETE` call gets `401` (no session left to authenticate with — the idempotent-retry
case `rest-conventions.md`'s general `DELETE` rule describes never arises here). A guest gets `403`.
`./mvnw verify -Pintegration` green locally, run five times to confirm no flakiness. CI green on
`turnbase-platform` `master` (`build`; `e2e` stays blocked on the same un-provisioned
`TURNBASE_GAME_HOST_PAT` every prior session's run also shows) — the first CI push caught a real bug
the local run hadn't: `UUID.compareTo` orders by signed-long comparison of the two halves, while
Postgres's `uuid` type orders by unsigned byte value, so a test fixture ordering a `friendship` pair
by `UUID.compareTo` violates `friendship_order_ck` for roughly half of random UUID pairs — passed
locally by chance, failed in CI on a different random draw. Fixed by comparing the canonical string
form instead, which matches Postgres's byte ordering exactly.

**Closed:** IMP-GATE-32 (opened and closed 2026-09-08, session 33) — this item's *Satisfies* claimed
the full `FR-ACCT-004…010` range, but `FR-ACCT-009` (deleted-profile placeholder) and `FR-ACCT-010`
(password change) are already implemented and claimed by `IMP-M1-07` — `ProfileService.view`'s
deleted-placeholder branch and `POST /me/password`, both verified in `ProfileControllerIT` — and
neither appears in this item's own *Done when* clause, which only ever tested the erasure-transaction
disposition table. Same shape as `IMP-GATE-08`/`18`/`28`/`30`. Fixed: narrowed to `FR-ACCT-004…008`
below, which is what this item actually builds — the deletion endpoint sets `deleted_at`, so
`FR-ACCT-009`'s already-built display renders correctly once this item runs, with no new code owed to
it here.

**Closed:** IMP-GATE-33 (opened and closed 2026-09-08, session 33) — no document in the corpus named a
route, method or status code for FR-ACCT-004 itself (the deletion trigger). `rest-conventions.md`'s
"self-scoped account routes" named `PATCH /api/users/me`, `POST /api/users/me/password` and
`PATCH /api/users/me/privacy` but nothing that triggers deletion, and this item's own read-list never
named `rest-conventions.md` at all despite it being the document that supplies the route for every
other `/api/users/me` mutation. Same shape as `IMP-GATE-31`. Fixed: `rest-conventions.md` gained
`DELETE /api/users/me` as a fourth self-scoped route — `DELETE` is the correct verb here, unlike
logout, because the account *is* the addressable resource named by `/me`. `204` on success, clears the
session cookie and closes live connections per `FR-SESS-010`, same as logout. No confirmation step at
the API layer — `VW-SET-007`'s confirmation is a frontend-only affordance. Read-list corrected to
include it.

**Read first:**
- `docs/specs/api-design/rest-conventions.md` § Authentication — the self-scoped account routes,
  including the deletion trigger added by `IMP-GATE-33`
- `docs/decisions/0004-account-erasure-pseudonymization.md`
- `docs/specs/platform/data-model-accounts.md` §5 in full — *Erasure: what account deletion actually
  writes*. §5 enumerates every object and its disposition; that enumeration is the specification.
- `docs/requirements/user-accounts.md` FR-ACCT-004…008
- `docs/specs/platform/data-model-catalog.md` §5, `data-model-history.md` §4,
  `data-model-notifications.md` §2, `data-model-social.md` §§1–2 — the documents that own the
  non-account objects §5 disposes of
- `docs/specs/platform/room-lifecycle.md` §4, §5.1 duty 2 — how an owed room closure is discharged

**Satisfies:** `user-accounts.md` FR-ACCT-004…008; `platform-operations.md` FR-RET-001, FR-RET-005

**Done when:** erasure is non-reversible — **a random token, not an HMAC**; `HMAC(user_id, pepper)`
is reversible by enumeration over a small id space given the key, which ADR-0004 forbids. Every
object listed in `data-model-accounts.md` §5 has a disposition, including the open `game_review`,
`room_invitation` on both legs, and `room`/`room_participant`. **Nothing happens by cascade on that
path** — a registered deletion is soft.

**The erasure transaction writes participant departures only.** It does not close rooms inline. A
room the deleted user hosted becomes an owed closure carried by the existing deferred tail —
`lost_announced_at IS NULL` — and is discharged by `room-lifecycle.md` §5.1 duty 2 on the owning
instance (IR-11). Closing a room from inside the erasure transaction means closing a room this pod
may not own, which is precisely the write ADR-0008's epoch fence exists to reject.

---

### IMP-M1-09 — Social graph, friendships and requests

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-07

**Done 2026-09-08 (session 34).** `social.SocialController`/`SocialService`/`SocialRepository` add
the seven `social-rest-api.md` endpoints: `POST`/`GET /api/friend-requests`, `POST
/api/friend-requests/{id}/accept`, `DELETE /api/friend-requests/{id}` (cancel or decline,
discriminated by which side the caller is on), `GET /api/users/{username}/friends`, `DELETE
/api/users/me/friends/{userId}`, and `GET /api/users?search=`. Friendship rows insert in
`data-model-social.md` §1's canonical `(user_id_low, user_id_high)` order, using the same
canonical-string-form `UUID` comparison `IMP-M1-08` verified matches Postgres's unsigned-byte `uuid`
ordering (session 33) rather than `UUID#compareTo`. Send/accept/decline/cancel each write or
cascade-delete the matching `FRIEND_REQUEST`/`FRIEND_REQUEST_ACCEPTED`/`FRIEND_REQUEST_DECLINED`/
`FRIEND_ADDED` notification in the same transaction (FR-FREQ-001/003/004/006). The friend cap
(FR-SOC-009) and the block-friend-requests toggle (FR-SOC-021) are enforced without disclosing which
reason applies, both in the direct send response and in search's `canSendRequest` flag. Cross-feature
reads (`app_user`, `user_privacy_settings`, `notification`) go through raw `JdbcClient` SQL rather
than another module's Java API — the same pattern `account.AccountErasureRepository` established —
so `social` and `account` stay a one-way Modulith dependency: `account.ProfileService` calls the new
public `social.RelationshipQueries`; `social` never imports `account`. `account.ProfileResponse`
gained `relationshipState` (`social-rest-api.md` §9, FR-SOC-016), and the `FRIENDS_ONLY` friends-section
check `IMP-M1-07` left conservative now resolves against a real friendship. The confusable-skeleton
algorithm moved from `account.UsernamePolicy` into `common.UsernameSkeleton` so this item's
exact-username resolution can't drift from registration's.

**Verified end to end.** `SocialControllerIT` (17 tests, real Postgres): the notification coupling
on all four terminal actions (send/accept/decline/cancel), the FR-SOC-004 reverse-request auto-accept
with no leftover `friend_request` row, the sender cap and the blocked-recipient rejection (with the
Problem Detail `detail` text checked to never mention "block"), search's `canSendRequest` hiding the
same reason, idempotent delete on an already-resolved request and idempotent/mutual unfriend, a
third party forbidden from resolving someone else's request, `FRIENDS_ONLY` visibility and
`relationshipState` resolved against a real friendship (stranger vs. friend, `NONE`/`FRIENDS`/
`REQUEST_SENT`/`REQUEST_RECEIVED`), guests forbidden on every endpoint, and a ten-random-pair loop
guarding the canonical-ordering fix. `./mvnw verify -Pintegration` green locally, run twice. CI green
on `turnbase-platform` `master` (`build`, 10m17s — `e2e` stays blocked on the same un-provisioned
`TURNBASE_GAME_HOST_PAT` every prior session's run also shows). The first CI attempt on this commit
stalled for 55 minutes on the `Verify` step with no evidence of a code defect (two clean local runs,
no parallel test execution configured, no self-deadlock found in `SocialRepository`'s transactional
methods) and was cancelled and re-run; the re-run completed in the normal 6–10 minute range, pointing
to a one-off runner flake rather than a hang in this item's code.

**Closed:** IMP-GATE-34 (opened and closed 2026-09-08, session 34) — this item's *Satisfies* claimed
`notifications-invitations.md` FR-FREQ-001…006 in full, and `IMP-M5-03` independently claimed the
identical full range in its own *Satisfies*, but neither item's *Done when* clause tested the other's
overlap: this item's never mentioned notifications at all, and `IMP-M5-03`'s tested only the generic
retention/alert mechanics (the partial purge index, the SSE alert/notification class split), none of
it friend-request-specific. `data-model-notifications.md` §3's type table settles which item actually
writes the rows: `FRIEND_REQUEST`/`FRIEND_REQUEST_ACCEPTED`/`FRIEND_REQUEST_DECLINED`/`FRIEND_ADDED`
are all written at the moment a `friend_request` row is created, accepted, or declined — this item's
own transactions, not `IMP-M5-03`'s (which never mutates `friend_request`). Same shape as
`IMP-GATE-28`, in reverse: there the generic infrastructure item over-claimed a requirement the
specific producer had to build; here the generic item (`IMP-M5-03`) over-claimed a requirement the
specific producer (this item) actually builds. Fixed: `IMP-M5-03`'s *Satisfies* narrowed to drop
FR-FREQ-001…006 (its section below); this item keeps the claim, its *Done when* gained the notification
clauses below, and its read-list gained `data-model-notifications.md` §1/§3 — the column names and
type strings the original list never named.

**Closed:** IMP-GATE-35 (opened and closed 2026-09-08, session 34) — no document in the corpus ever
defined this item's REST surface. `rest-conventions.md`'s Authorization table has named the
`/api/friend-requests/{id}` ownership predicate ("`principal ∈ {sender, recipient}`, and the action
must match the side") since it was written, but nothing supplied the endpoints that predicate
governs — the same shape as `IMP-GATE-31`/`33`, except there the route was one missing row in an
existing table and here the entire feature's HTTP surface was unwritten, closer in size to
`room-rest-api.md`'s gap before `IMP-GATE-13`'s era. This item's own read-list never named
`rest-conventions.md` either, so nothing would have surfaced the gap short of writing the controller.
Fixed: new `docs/specs/api-design/social-rest-api.md` (registered in that directory's `INDEX.md`) —
seven endpoints (username search, send, list, accept, cancel/decline, friend list, unfriend) plus a
`relationshipState` extension to `GET /api/users/{username}` for FR-SOC-016, which is also how this
item's `IMP-M1-07` obligation (below) is discharged. Read-list corrected to include it.

**Read first:**
- `docs/requirements/social-friends.md` FR-SOC-001…021
- `docs/specs/platform/data-model-social.md` §§1–3 — `friendship`, `friend_request`, and the
  interaction with `block_friend_requests`
- `docs/requirements/notifications-invitations.md` FR-FREQ-001…006
- `docs/requirements/user-accounts.md` FR-GUEST-007
- `docs/specs/platform/data-model-notifications.md` §1 (`notification` — the subject foreign keys and
  the actionable/informational split), §3 (the four `FRIEND_REQUEST*`/`FRIEND_ADDED` type rows this
  item writes)
- `docs/specs/api-design/social-rest-api.md` **in full** — the seven endpoints, the evaluation orders,
  the error table
- `docs/specs/api-design/rest-conventions.md` § Authorization and Ownership (the
  `/api/friend-requests/{id}` predicate) and § *Four further self-scoped account routes* (the pattern
  §7's `/api/users/me/friends/{userId}` follows)

**Satisfies:** `social-friends.md` FR-SOC-001…021; `notifications-invitations.md`
FR-FREQ-001…006; `user-accounts.md` FR-GUEST-007

**Done when:** guest exclusion is enforced by the foreign key — `friendship` references
`app_user (user_id, kind)` with a local `CHECK kind = 'REGISTERED'` — so `social-friends.md`
FR-SOC-020 cannot be violated from any code path; friendship rows are stored in the canonical
ordering `data-model-social.md` §1 defines, so the pair `(a,b)` and `(b,a)` cannot both exist; a
blocked user's request is rejected without disclosing that a block exists; sending a request inserts a
`FRIEND_REQUEST` notification for the recipient with `friend_request_id` set (FR-FREQ-001), in the same
transaction as the `friend_request` insert; accepting deletes the request, inserts the friendship, and
writes two subject-less notifications in the same transaction — `FRIEND_REQUEST_ACCEPTED` to the
sender and `FRIEND_ADDED` to the accepter (FR-FREQ-003); declining deletes the request and writes one
subject-less `FRIEND_REQUEST_DECLINED` notification to the sender only, none to the decliner
(FR-FREQ-004); cancelling deletes the request and, because the notification carries
`friend_request_id` with `ON DELETE CASCADE`, needs no separate delete statement for the recipient's
notification to disappear (FR-FREQ-006); `friend_request.expires_at` is written absolutely at insert as
`now() + :window`, from the same configuration key `NFR-SOC-SCALE-001` requires, never derived at read
time (the mechanical half of FR-FREQ-005 — the expiry purge job itself is `IMP-M5-04`'s); every
endpoint in `social-rest-api.md` §1 exists with the exact method, path and status codes that document
specifies, including the idempotent `204` on `DELETE /api/friend-requests/{id}` and `DELETE
/api/users/me/friends/{userId}` for an already-resolved id (§5, §7) and the `canSendRequest`/
`relationshipState` fields that carry FR-SOC-021's non-disclosure and FR-SOC-016's button state
respectively (§2, §9).

**Obligation left by `IMP-M1-07`:** `account.ProfileService.visibleSectionsFor` resolves the friends
section's `FRIENDS_ONLY` value (FR-SOC-017) as hidden for every non-owner viewer, since the
confirmed-friendship check it needs is this item's, not `IMP-M1-07`'s. This item's Done-when gains a
fifth clause: replace that conservative resolution with an actual friendship check (a direct query
against `friendship`, canonically ordered, is enough — no new public API is needed since
`ProfileService` and this item's code both live in `turnbase-platform`).

---

### IMP-M1-10 — Google OAuth registration and login

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-04

**Done 2026-09-08 (session 36).** Five endpoints (`OAuthController`, `OAuthRegistrationController`,
`account` package): `GET /auth/google` builds the consent-screen URL with a signed, short-lived
`state` (`session.OAuthStateService`, over the same JWT key set session tokens use) carrying a
validated internal redirect destination; `GET /auth/callback` exchanges the code server-side
(`GoogleOAuthClient`, resolving identity from Google's userinfo endpoint with the freshly-issued
access token rather than verifying the ID token itself) and resolves by
`(method='GOOGLE', provider_subject=sub)`, never by email; a first-time login mints a Redis-backed
pending record (`PendingOAuthRegistration`, `concern=application`) and sets `turnbase_oauth_pending`
rather than a session cookie. `POST /api/auth/oauth/complete-registration` creates the account or
reports `CHALLENGE_REQUIRED` (`200`, not an error — same shape as `social-rest-api.md`'s outcome
pattern) on an FR-AUTH-016 email collision, without creating a duplicate or silently linking;
`POST /api/auth/oauth/link-challenge` verifies the existing account's password and links the Google
identity as an additional `user_auth_method` on success, the same generic 401 on failure whether the
password is wrong or the collision account no longer resolves.

**One platform-wide gap found and fixed while building this item, not gated because the spec was
already correct.** `rest-conventions.md`'s Origin check for state-changing requests had never been
implemented anywhere in the app — six already-`DONE` items (`IMP-M1-04` through `IMP-M1-09`) build
`POST`/`PATCH`/`DELETE` endpoints with no such enforcement. Fixed with a new
`common.OriginCheckInterceptor`, registered ahead of every other interceptor
(`Ordered.HIGHEST_PRECEDENCE`) in `PlatformWebMvcConfig`, covering the whole app at once rather than
just this item's two new `POST` endpoints.

**`rate-limiting.md` changes**: Tier 1 gained `POST /api/auth/oauth/link-challenge` (an
auth-method-addition credential guess); Tier 4 gained the two redirect routes; Tier 5's OAuth
accounting moves to `complete-registration`'s actual success path — the callback never creates the
row, so counting there would charge an aborted registration against the cap.

**Verified end to end.** `GoogleOAuthClientTest`/`OAuthStateServiceTest`/`PendingOAuthRegistrationTest`
(unit) prove the pure mechanics directly, Google stubbed with a plain JDK `HttpServer` — no mock-HTTP
library is a project dependency. `OAuthServiceTest` (unit, Mockito) covers every branch of the
orchestration. `OAuthControllerIT` (Testcontainers Postgres + Redis, real HTTP) drives the full round
trip against a real boot: initiate → callback → complete-registration for a first-time login, a
returning login skipping the pending cookie entirely, and the email-collision challenge-and-link path
including a wrong-password rejection. `./mvnw verify -Pintegration` green locally (211 tests). CI
green on `turnbase-platform` `master` (`build`, 12m27s) — the `e2e` job's "Check out
turnbase-game-host" step fails for an unrelated, pre-existing reason also present in `IMP-M1-02`'s
accepted run.

**Closed:** IMP-GATE-37 (opened and closed 2026-09-08, session 36) — no document in the corpus named
the JSON/redirect REST surface this item builds: `secrets-and-configuration.md` §5 and
`flows/01-arrival-and-account.md` §E name two browser-navigated paths (`/auth/callback`,
`/auth/complete-registration`) but not the endpoint the "Continue with Google" button hits, not the
JSON endpoint the complete-registration page calls to learn the pending email or submit the username,
and not any endpoint for FR-AUTH-016's credential-challenge-and-link step; `rest-conventions.md`'s
Authentication section — the document naming every other auth endpoint — was missing from this item's
own read-list. Same shape as IMP-GATE-31/33/35. Fixed: new `docs/specs/api-design/oauth-rest-api.md` —
five endpoints (initiate, callback, read-pending, complete-registration, link-challenge), the
`turnbase_oauth_pending` cookie, and two new `local-environment.md` §7.4 TTL properties; `rate-limiting.md`
Tier 1's endpoint list gained the link-challenge route and Tier 5's OAuth row now names the exact
success path it counts; read-list corrected.

**Added 2026-09-06 (session 29), closing IMP-GATE-26** — see `IMP-M1-04`'s *Closed* note. Split out
because credential auth (`FR-AUTH-006`) is complete without it (`secrets-and-configuration.md` §1
says so directly — the OAuth client secret is absent by default and the platform starts anyway) and
because the OAuth round trip is a comparable amount of work to `IMP-M1-04` in its own right: consent
redirect, server-side code exchange, signed `state`, a Redis-backed pending-registration token, and
the FR-AUTH-016 email-collision challenge-and-link path — none of which the credential flow touches.

**Closed:** IMP-GATE-38 (opened and closed 2026-09-08, session 36) — `user-accounts.md` NFR-SEC-006
enumerates every endpoint exempt from session authentication and did not name this item's five: the
Google OAuth entry point and callback (never had a session to require) and the three
pending-registration JSON endpoints (gated by `oauth-rest-api.md` §2's pending token instead, a
different mechanism entirely). Same shape as IMP-GATE-29. Fixed: NFR-SEC-006 now names all five;
read-list gained the citation.

**Read first:**
- `docs/requirements/user-accounts.md` FR-AUTH-007…012, FR-AUTH-016, NFR-SEC-006
- `docs/specs/platform/data-model-accounts.md` §1 (`email_source`), §2 (`user_auth_method`)
- `docs/specs/deployment/secrets-and-configuration.md` §1 (the OAuth client secret's absent-by-default
  behaviour), §5 (`TURNBASE_OAUTH_GOOGLE_CLIENT_SECRET`, the redirect URI, the signed `state`)
- `docs/specs/flows/01-arrival-and-account.md` §E
- `docs/requirements/platform-views.md` VW-LOGIN-002, VW-REG-002, VW-OAUTHCOMP-001…002, VW-REDIR-004…006
- `docs/specs/api-design/rest-conventions.md` § Authentication, § Origin Policy and CSRF
- `docs/specs/api-design/oauth-rest-api.md` **in full** — the REST surface this item builds
- `docs/specs/api-design/rate-limiting.md` § Tier 1, § Tier 5
- `docs/specs/api-design/error-handling.md`
- `docs/specs/deployment/local-environment.md` §7.4 (the two new OAuth TTL properties)

**Satisfies:** `user-accounts.md` FR-AUTH-007…009, FR-AUTH-012, FR-AUTH-016; `platform-views.md`
VW-LOGIN-002, VW-REG-002, VW-OAUTHCOMP-001…002 (`FR-AUTH-010`/`011` are `IMP-M1-11`'s — `IMP-GATE-78`)

**Done when:** `GET /auth/google` redirects to Google with a signed, short-lived `state` carrying a
validated internal destination; `GET /auth/callback` verifies `state`, exchanges the code server-side
(client secret never reaches the browser), and resolves the identity by `(method='GOOGLE',
provider_subject=sub)` — never by email; a first-time login mints the `oauth-rest-api.md` §2 pending
record and cookie and redirects to `/auth/complete-registration`; `POST
/api/auth/oauth/complete-registration` creates `app_user` (`email_source='OAUTH'`), `user_auth_method`
and default privacy settings and issues a session, or responds `CHALLENGE_REQUIRED` when the email
collides with an active account (FR-AUTH-016) rather than creating a duplicate or silently linking;
`POST /api/auth/oauth/link-challenge` verifies the existing account's password, links the Google
identity as an additional `user_auth_method` on success, and returns the same generic failure message
on failure that reveals nothing about which account exists; the login/registration pages hide the
Google button when `TURNBASE_OAUTH_GOOGLE_CLIENT_SECRET` is absent rather than offering a button that
fails.

**The redirect URI is `http://turnbase.localhost:8080/auth/callback`, not `localhost`** —
`secrets-and-configuration.md` §5 flags this explicitly: they are different URIs to Google, and the
platform origin is deliberately the non-obvious one.

### IMP-M1-11 — Account read and auth-method management

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-10

**Closed:** IMP-GATE-78 (opened and closed 2026-09-26, session 77) — `IMP-M6-03`'s Account Settings view
(`platform-views.md` VW-SET-001…006a) had nothing to render from and nothing to call. No route
returned the caller's own email, `email_source`, linked auth methods or per-section privacy values
(`GET /api/users/{username}` is the public representation and rightly omits them), and no route added
or removed an auth method: `oauth-rest-api.md` §11 and §12 deferred `FR-AUTH-010`/`011` to "a future
add/remove item" that no registry entry was. Fixed: `rest-conventions.md` gained `GET /api/users/me`
and `/api/users/me/auth-methods` (password add, Google complete, remove); `oauth-rest-api.md` gained
§7a (the three-request Google link flow, shaped by `turnbase_session` being `SameSite=Strict`);
`rate-limiting.md` Tier 1 names the routes; `IMP-M1-10`'s *Satisfies* no longer claims
`FR-AUTH-010`/`011`; this item is new, and `IMP-M6-03` depends on it.

**Read first:**
- `docs/requirements/user-accounts.md` FR-AUTH-008…012, FR-ACCT-002…003, NFR-SEC-003
- `docs/specs/api-design/rest-conventions.md` § Authentication — *The account representation* and
  the `/api/users/me` routes table
- `docs/specs/api-design/oauth-rest-api.md` §2, §3, §4, §7a, §10
- `docs/specs/platform/data-model-accounts.md` §1 (`email_source`, the two `*_changed_at` columns),
  §2 (`user_auth_method`, and FR-AUTH-011's guarded delete), §4 (`user_privacy_settings`)
- `docs/specs/api-design/rate-limiting.md` § Tier 1
- `docs/specs/api-design/error-handling.md`

**Satisfies:** `user-accounts.md` FR-AUTH-010, FR-AUTH-011 (the removal guard; the creation-time half
is `IMP-M1-04`'s)

**Done when:** `GET /api/users/me` answers the representation in `rest-conventions.md` and `403` for a
guest, with no `password_hash` or `provider_subject` anywhere in it; `usernameChangeableAt` and
`emailChangeableAt` are `null` when the field is changeable now and the instant the window elapses
otherwise; `POST .../auth-methods/password` adds a `PASSWORD` row under registration's password policy
and `409`s when one exists; `DELETE .../auth-methods/{method}` is a guarded delete in the same
transaction as its count (two concurrent removals against an account with two methods leave exactly
one — asserted with a real concurrent test, not a mock), refuses the only method with `422`, and
removing `GOOGLE` from an `email_source = 'OAUTH'` account sets `email_source = 'SELF'`; `GET
/auth/google?intent=link` needs a Registered session, and `/auth/callback` on that branch **issues no
session and reads none** — asserted by a callback with no cookie at all — storing only the
`oauth:link:{token}` record; `POST .../auth-methods/google` links only when the record's `userId`
equals the caller's (a record minted for user A, confirmed by user B, is `403` and is not consumed),
`409`s on an already-held `sub`, and never touches `email` or `email_source`; the four Tier 1 routes
count failures only.

---
