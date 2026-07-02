# API Design Review — Security, Consistency, Implementability (api-review agent)

Scope: all files under `/home/hmazur/proj/turnbase/docs/specs/api-design/`, cross-referenced against `/home/hmazur/proj/turnbase/docs/requirements/user-accounts.md` and `/home/hmazur/proj/turnbase/docs/requirements/platform-operations.md`. Known-missing items (upload pipeline spec, frontend shell spec, admin tooling, tracked open questions in `docs/requirements-gaps.md`) excluded per instructions.

## BLOCKER

### 1. No rate limiting for WebSocket messages
**Files:** `rate-limiting.md` (all tiers), `room-chat-websocket.md` §SEND_CHAT_MESSAGE, `room-websocket.md` §Command Catalogue
All four rate-limiting tiers are HTTP-only (`HandlerInterceptor`). Once a client holds a WebSocket connection, nothing bounds `SEND_CHAT_MESSAGE`, `REQUEST_ROOM_STATE` (which acquires the room lock and serializes a full snapshot per call), or host commands. On the public internet this is a trivial chat-flood and room-lock-starvation vector, reachable even by guest accounts. Chat has no persistence, so there is no audit trail either.
**Resolution:** Add a Tier 5 to `rate-limiting.md`: per-user inbound STOMP frame budget enforced in the inbound `ChannelInterceptor` (e.g. 10 messages/second sustained, burst 20; chat sub-limit 1 msg/second with burst 5). Over-limit frames get an `ERROR` on `/user/queue/errors` with code `RATE_LIMIT_EXCEEDED`; repeated violation closes the connection.

### 2. Guest account creation is effectively unthrottled
**Files:** `rate-limiting.md` (Tier 1/Tier 4 endpoint lists); cross-ref `user-accounts.md` FR-GUEST-001..005
"Play as Guest" is an unauthenticated POST that creates a DB row and issues a full session token. It is not in Tier 1's list (login, registration, password change, auth methods) — and Tier 1 counts only *failed* attempts anyway, while guest creation always succeeds. Tier 4 lists only read endpoints (catalog, detail, profiles). A single IP can mint thousands of guest accounts and sessions before the hourly cleanup job runs, and each guest can join rooms and chat (compounding gap 1).
**Resolution:** Add guest creation (and credential registration, which is also always-successful and only failure-counted today) to a success-counting IP bucket, e.g. 5 guest accounts per IP per hour, 429 with `Retry-After` beyond that.

### 3. Room affinity model contradicts the platform-operations scaling model
**Files:** `room-websocket.md` §Room Affinity and WebSocket Routing; `platform-operations.md` §WebSocket Horizontal Scaling, NFR-SCALE-001
`room-websocket.md` is built on single-pod room ownership: ingress routing hint (`X-Room-Pod`), JVM-local `ReentrantLock`, in-JVM `AtomicLong` version counters, local broker delivery. `platform-operations.md` states the opposite: "No application-level sticky session requirements (WebSocket cross-instance routing handled via Redis pub/sub)" and describes all instances subscribing to Redis channels so *any* instance can deliver effects. These are two incompatible architectures; an implementer cannot satisfy both, and the choice decides whether distributed locks and Redis counters are needed.
**Resolution:** Pick the room-affinity model (the more detailed and more recent spec) and amend `platform-operations.md`: replace the Redis pub/sub WebSocket-scaling section with a reference to room affinity, and reword NFR-SCALE-001 to "horizontal scaling via per-room pod ownership with ingress affinity; no cross-instance fan-out required."

## IMPORTANT

### 4. No CORS policy and no Origin check on the WebSocket/SSE handshakes
**Files:** `rest-conventions.md` §Authentication, `websocket.md` §Authentication, `sse-notifications.md` §Endpoint
No document states the CORS configuration or that the WebSocket upgrade validates the `Origin` header. `SameSite=Strict` (CON-004) does mitigate cross-site WebSocket hijacking in modern browsers, but a public API should not rely on a single cookie attribute as the only line of defense, and Spring's STOMP `setAllowedOrigins` behavior should be pinned deliberately rather than inherited.
**Resolution:** Add a short cross-cutting section to `rest-conventions.md`: CORS default-deny (no `Access-Control-Allow-Origin` emitted; frontend is same-origin), STOMP endpoint configured with `setAllowedOrigins(<canonical origin>)`, SSE endpoint same-origin only.

### 5. The CSRF story depends on where user-uploaded game frontends are served — and that is unstated
**Files:** `rest-conventions.md` §Authentication; cross-ref `user-accounts.md` CON-004; `game-development-experience.md` CON-006
CON-004 declares SameSite=Strict as the complete CSRF defense. That holds only if untrusted game JS never runs *same-site* with the session cookie: SameSite does not restrict same-site requests, so if game iframes are served from the platform's own origin/registrable domain without an opaque origin, any uploaded game can silently fire authenticated REST calls (kick players, delete account, etc.). The gdk-api specs cover postMessage origin validation but no doc pins the serving origin or sandbox attributes. Some of this may land in the planned frontend-shell spec, but the *constraint* belongs with the auth model because CON-004 is unsound without it.
**Resolution:** Add one sentence to `rest-conventions.md` §Authentication (or CON-004): game iframes MUST have an opaque origin — `sandbox="allow-scripts"` without `allow-same-origin` — or be served from a separate registrable domain, so game code can never issue credentialed same-site requests.

### 6. No input-validation/output-encoding conventions document
**Files:** missing from `api-design/`; touches `room-chat-websocket.md` (chat text), `room-websocket.md` §CHANGE_PARAMETERS, `error-handling.md`
NFR-SEC-005 mandates server-side validation, and chat has a 500-char limit, but there is no shared convention for: maximum lengths of common strings (username, room name — nowhere specified), rejection of control characters, Unicode normalization for uniqueness checks (`café` vs `café` usernames), maximum JSON request body size, and who is responsible for XSS-safe rendering of user-generated content (chat text, usernames, game names). Notably, `CHANGE_PARAMETERS` accepts an unbounded `parameters: object` that is broadcast verbatim to every subscriber — an amplification and memory vector.
**Resolution:** Add `input-validation.md` to `api-design/` with concrete defaults: username 3–32 chars restricted charset, strings NFC-normalized with C0/C1 controls rejected, max JSON body 64 KB (uploads excepted via pre-signed flow), `parameters` capped (e.g. 4 KB serialized, validated against the game's declared parameter schema), and a statement that all user-generated strings are plain text — encoded on render (React default escaping; never `dangerouslySetInnerHTML`).

### 7. No stated authorization/ownership model for REST resources (IDOR)
**Files:** `rest-conventions.md`, `file-uploads.md` (all steps)
The WebSocket specs have a solid two-layer authorization model, but REST has none: `rest-conventions.md` only defines the 403 status code. Concretely, `file-uploads.md` never states that `POST /api/games/{gameId}/versions`, confirm, and status polling are restricted to the game's owner — as written, any authenticated user can create version slots or confirm uploads for anyone's game. No convention says whether unauthorized access to an owned resource returns 403 or 404.
**Resolution:** Add an "Authorization" section to `rest-conventions.md`: every non-public resource declares an owner or membership set; mutations require ownership; unauthorized access to resources whose existence is non-public returns 404 (consistent with the existing game-catalog note), otherwise 403. Add one line to `file-uploads.md` Steps 1/3/4: caller must be the game owner.

### 8. Client IP derivation for IP-based rate limiting is unspecified
**Files:** `rate-limiting.md` Tiers 1 and 4
Tiers 1 and 4 key on "IP", but the monolith sits behind a Kubernetes ingress, so the socket peer is the ingress. Without a specified `X-Forwarded-For` trust policy, the implementation either rate-limits the ingress IP (locking out all users platform-wide after 5 failed logins) or blindly trusts XFF (attacker spoofs a fresh header per request and bypasses Tier 1 entirely, or poisons lockouts for victims' IPs).
**Resolution:** One paragraph in `rate-limiting.md`: client IP is the rightmost `X-Forwarded-For` entry appended by the platform's own ingress; XFF from outside the ingress is stripped at the edge; direct connections fall back to the socket address.

### 9. Actuator/management endpoint exposure conflicts with the auth rule
**Files:** `rest-conventions.md` §Authentication; cross-ref `platform-operations.md` FR-MET-007, NFR-SEC-006
NFR-SEC-006 requires a session token on every endpoint except an enumerated public list — `/actuator/prometheus` (mandated by FR-MET-007) and health/liveness probes are on no list. Read literally, Prometheus scrapes and kubelet probes would need session cookies; read loosely, actuator ends up publicly exposed, leaking JVM/DB/heap internals.
**Resolution:** Add to `rest-conventions.md`: actuator runs on a separate management port (`management.server.port`), never routed by the public ingress; only liveness/readiness exposed to the kubelet. Note the NFR-SEC-006 exemption explicitly.

### 10. No logout / session-revocation endpoint anywhere
**Files:** `rest-conventions.md`; cross-ref `user-accounts.md` §Session Management, `platform-views.md` VW-NAV-012
The UI spec has a "Log Out" nav item and the session model covers issuance and displacement, but no requirement or spec defines a logout endpoint. With a 24-hour non-renewable token and no revocation path, a user on a shared machine cannot terminate their session. Since FR-SESS-003 already implies server-side session state, revocation is cheap.
**Resolution:** Specify `POST /api/auth/logout` → 204: invalidates the server-side session and clears the cookie (`Max-Age=0`). One row in an auth-endpoints section of `rest-conventions.md` suffices.

## MINOR

### 11. `GAME_STARTED` topic path contradicts the destination convention
**Files:** `room-websocket.md` §GAME_STARTED (`"gameTopic": "/topic/game/{sessionId}"`) vs `websocket.md` topics table (`/topic/game.{sessionId}`)
Slash vs dot separator; room-websocket's own AntPathMatcher section mandates `.` separators. Fix the payload example to `/topic/game.{sessionId}`.

### 12. STOMP heartbeats unspecified, but disconnect detection depends on them
**Files:** `websocket.md`; cross-ref `room-websocket.md` §PLAYER_DISCONNECTED
`PLAYER_DISCONNECTED` and the grace-period machinery require the server to notice half-open TCP connections; SSE specifies a 30s keepalive but the WebSocket spec sets no heart-beat interval. Default: STOMP `heart-beat 10000,10000`, client considered disconnected after two missed beats.

### 13. Account enumeration is possible by design; state it as accepted
**Files:** `error-handling.md` (409 conflict taxonomy); cross-ref `user-accounts.md` FR-AUTH-003/004
Registration 409s reveal whether a username/email exists. With no password reset flow (CON-003) and Tier 1/Tier 4 throttling this is low-risk for MVP, but the login error should be uniform ("invalid credentials", never "user not found"), and the acceptance should be recorded in one line so it isn't rediscovered as a bug.

### 14. No idempotency convention for retried unsafe requests
**Files:** `rest-conventions.md`
Upload confirm documents 503-retry semantics, but nothing covers a retried `POST /api/rooms` after a network timeout producing duplicate rooms. For MVP a one-line convention suffices: duplicate-sensitive POSTs (room create) accept an optional client-generated `Idempotency-Key` honored for 5 minutes. (Room-state concurrency is already well covered by the room lock + version counter — no ETag machinery needed.)

## Already in good shape

Error shape is genuinely uniform (RFC 9457 everywhere on HTTP including 429s and upload failures; a single documented `ERROR` envelope on WS); the three WebSocket docs interlock cleanly (shared envelope, shared version counter, one reconciliation algorithm, no contradictions among them); the WS authorization two-layer model with in-lock host re-validation and team-chat subscription checks is above MVP bar; chat author identity and team resolution are server-assigned; secrets hygiene is covered (no stack traces in responses, FR-OBS-005 for logs); pagination/sort whitelisting prevents injection via sort params; timestamps are consistently ISO 8601 UTC and IDs are UUIDs.

## Verdict

The API surface is well-specified for its happy paths — unusually so for Phase 0 — but it is **not yet safe to expose on the public internet as-is**. Three things must be resolved before implementation starts: abuse controls that actually cover the real-time surface (gaps 1–2, since WebSocket traffic and guest creation are the cheapest attack paths and are currently unbounded), the room-affinity vs. Redis-pub/sub architecture contradiction (gap 3, which blocks implementation regardless of security), and the small set of one-paragraph security defaults (gaps 4–10: CORS/Origin, game-iframe origin isolation to keep the SameSite-only CSRF model sound, input-validation conventions, REST ownership checks, XFF trust, actuator isolation, logout). None of these require redesign — every one has a cheap, local resolution — so with roughly one focused spec-editing session the surface would be a credible, defensible MVP; without them, the platform ships with unthrottled spam vectors and at least one same-site CSRF hole reachable by any uploaded game.
