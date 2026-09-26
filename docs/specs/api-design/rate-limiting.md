# Rate Limiting

Abuse controls for every inbound surface the platform exposes: HTTP requests, account minting, and
WebSocket frames.

**Realizes:** `user-accounts.md` NFR-SEC-003. **Closes review blockers API-1** (WebSocket messages
unthrottled) and **API-2** (guest creation unthrottled), plus api-design review gap 8 (client-IP
derivation) and GRMP lesson F6 (per-environment configurability).

## Two enforcement domains

| Domain | Tiers | Backing store | Enforcement point |
|---|---|---|---|
| **HTTP** | 1–5 | **Redis** (Bucket4j `RedisBucket`) | `HandlerInterceptor` per endpoint group |
| **WebSocket** | 6 | **Pod-local JVM memory** (Bucket4j `LocalBucket`) | STOMP `ChannelInterceptor` on `clientInboundChannel`, plus two handler-level checks |

HTTP tiers must be distributed: Tiers 1, 4 and 5 are keyed by IP and run **before** authentication, so
any pod can serve the request and every pod must see the same counter.

WebSocket buckets are deliberately **not** distributed. Room affinity (ADR-0002) pins every frame a
user sends about a room to the pod that owns that room, so a pod-local bucket keyed by principal
observes that user's entire frame stream — it is *exact*, not an approximation. Putting a Redis round
trip on the inbound path of every chat message and every game action would add a network hop to the
platform's hottest path to buy nothing. **Rate-limit locality follows the same affinity argument as
effect fan-out** (`websocket.md` § Session affinity and fan-out locality).

The one leak this accepts is stated under [Pod-local budgets](#pod-local-budgets-and-what-they-do-not-cover).

---

## Client identity: deriving the IP

Tiers 1, 4 and 5 key on client IP. The monolith sits behind an ingress, so the socket peer is the
ingress, not the client. Getting this wrong breaks the IP tiers in **both** directions:

- Key on the socket address → every user shares one bucket, and five failed logins lock out the
  entire platform.
- Trust `X-Forwarded-For` blindly → an attacker spoofs a fresh header per request and bypasses Tier 1
  entirely, *and* can poison a victim's IP into lockout by forging their address.

The policy is therefore two-sided, and both sides are required:

1. **At the edge.** The ingress **overwrites** `X-Forwarded-For` with the observed peer address; it
   never appends to a client-supplied value (ingress-nginx: `use-forwarded-headers: "false"`, which is
   the default — it must not be turned on). The header that reaches the application therefore contains
   exactly one entry: the true client.
2. **In the application.** `X-Forwarded-For` is honoured **only** when the socket peer is inside
   `turnbase.security.trusted-proxies` (the ingress CIDR set). Otherwise the socket address is used.
   Direct connections — local `docker compose`, tests — have no proxy and fall back to the socket
   address with no configuration. Spring's `ForwardedHeaderFilter`
   (`server.forward-headers-strategy=FRAMEWORK`) applies the header to `getRemoteAddr()`; the
   trusted-proxy check is what makes trusting it safe.

**IPv6 is keyed by /64 prefix, not by address.** A single residential IPv6 allocation is a /64 or
larger, giving one attacker 2^64 distinct addresses. Keying on the full address would make every
IP-based tier trivially bypassable and is a common, silent failure. IPv4 keys on the full /32.

---

## Tier 1 — Auth failures (IP-based, strict)

Applies to: login, registration, password change, auth-method addition/removal —
including `POST /api/auth/oauth/link-challenge` ([oauth-rest-api.md](oauth-rest-api.md) §7) and the
three `/api/users/me/auth-methods` routes ([rest-conventions.md](rest-conventions.md), `IMP-GATE-78`).

Implements `user-accounts.md` NFR-SEC-003 exactly:

- After 5 failed attempts from the same IP → 30-second lockout
- Each subsequent failed attempt doubles the lockout duration
- **Only failed attempts increment the counter**; successful operations do not affect it

Redis key: `rate:auth:{ip}`

On lockout: 429 with `Retry-After: 30`.

> Tier 1's failure-only counting is exactly why Tier 5 exists. Registration and guest creation
> *always succeed*, so they increment nothing here and Tier 1 does not bound them at all.

## Tier 2 — General API (per-user)

Applies to: all authenticated endpoints not covered by another tier.

- 100 requests per 10-second sliding window
- Redis key: `rate:api:{userId}`

Response headers on every request in this tier:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 73
X-RateLimit-Reset: 1749643200
```

On limit exceeded: 429 with `Retry-After: 4`.

The WebSocket **upgrade** request (`GET /ws`) is an authenticated HTTP request and is covered here.
Only post-`CONNECT` frames need Tier 6.

## Tier 3 — Upload sub-bucket (per-user, per-hour)

Applies to: `POST /api/games/{gameId}/versions` (Step 1 of the pre-signed upload flow — see
[file-uploads.md](file-uploads.md)).

- 10 version uploads per user per rolling hour
- Enforced independently of Tier 2 — a burst of uploads does not exhaust the general API budget
- Redis key: `rate:upload:{userId}`

## Tier 4 — Unauthenticated reads (IP-based, lenient)

Applies to: game catalog, game detail pages, public user profiles, the Google OAuth provider-availability
read (`GET /api/auth/providers`, `IMP-GATE-76`), and the two Google OAuth redirects
(`GET /auth/google`, `GET /auth/callback` — [oauth-rest-api.md](oauth-rest-api.md) §3/§4) — the read
endpoints that require no session token (`user-accounts.md` NFR-SEC-006).

- 200 requests per minute per IP
- Covers normal browsing; blocks scrapers and abusive crawlers
- Redis key: `rate:public:{ip}`

---

## Tier 5 — Account minting (IP-based, success-counting) — closes API-2

Applies to the endpoints that **create an account and issue a session token**:

| Endpoint | Limit | Redis key |
|---|---|---|
| `POST /api/auth/guest` — "Play as Guest" (FR-GUEST-001) | **5 per IP per hour** | `rate:mint:guest:{ip}` |
| `POST /api/auth/register` — credential registration (FR-AUTH-001) | **3 per IP per hour** | `rate:mint:register:{ip}` |
| `POST /api/auth/oauth/complete-registration` success path — first-time Google account creation ([oauth-rest-api.md](oauth-rest-api.md) §6) | counts against the registration bucket | `rate:mint:register:{ip}` |

**This tier counts successes.** That is the whole point, and it is what distinguishes it from Tier 1.
"Play as Guest" is an unauthenticated `POST` that always succeeds, writes a DB row, and hands back a
full session token; the guest can then join rooms, chat, and submit game actions. Under Tiers 1–4 as
they stood, a single IP could mint guest accounts as fast as it could open connections, bounded only
by Tier 4's 200/min — and each minted guest is an independent principal with its own Tier 6 budget.

Registration and guest creation therefore carry **two independent counters**: failures feed Tier 1's
lockout, successes feed Tier 5's bucket. They do not interact.

Over limit: 429 `rate-limit-exceeded` with `Retry-After` set to the seconds until the next token
refills.

**Accepted cost.** A shared egress IP — university, corporate NAT, mobile CGNAT — shares the bucket.
Five guests per hour is generous for a household and tight for a lecture hall. Accepted for the MVP
(which is local-first per ADR-0001, so the population behind any one IP is small); revisit if it
bites, see [OQ-001](#open-questions).

---

## Tier 6 — WebSocket inbound frames (per-user, pod-local) — closes API-1

Every STOMP frame after `CONNECT` passes a `ChannelInterceptor` on `clientInboundChannel`. Frames are
classified **by destination** (available in the STOMP headers, before the payload is deserialized), so
classification costs nothing.

Buckets are keyed by **principal**, not by connection: opening a second tab must not double a user's
budget. `CONNECT` is authenticated (`websocket.md` § Authentication), so every frame has a principal —
**guests included**. Guests are the cheapest identity on the platform to obtain, which is precisely
why no tier may exempt them.

### The budgets

| Bucket | Frames it covers | Sustained | Burst | Why this number |
|---|---|---|---|---|
| `snapshot` | `REQUEST_GAME_SYNC` (`/app/game.*.sync`), `REQUEST_ROOM_STATE` (`/app/room.*.member`) | **1 per 3 s** | 2 | The most expensive frame a client can send. `REQUEST_GAME_SYNC` **re-enters the guest VM** (`onResync`) under the session's single-flight lock; `REQUEST_ROOM_STATE` takes the room lock and serializes a full snapshot. Legitimate use is *once per attach or reconnect*. |
| `action` | `/app/game.*.action` | 5 / s | 10 | Each action is a Redis enqueue plus a guest-VM invocation. Generous enough for click-heavy games, bounded enough that one player cannot monopolise a session's serial executor. |
| `chat` | `/app/room.*.chat` | 1 / s | 5 | Human typing speed. The burst covers pasting a few lines. Chat is **not persisted** (`in-room-chat.md` FR-MSG-005), so a flood leaves no audit trail — bounding it at the source is the only control there is. |
| `command` | `/app/room.*.member`, `/app/room.*.host` | 2 / s | 10 | Room-lock mutations at human UI pace (readiness toggles, team drags). |
| `subscribe` | any `SUBSCRIBE` frame | 1 / s | 20 | Each subscription runs an authorization check. A client subscribes to ~6 destinations on attach; the burst absorbs that and a reconnect storm. |
| `connection` | **every** inbound frame, including all of the above | 10 / s | 30 | Backstop. Also the only thing bounding frames to unknown or malformed destinations, which are rejected but still cost a parse. |

Every frame consumes one token from `connection` **and** one from its class bucket. A frame is
accepted only if both have capacity.

### Two enforcement points, and why

`REQUEST_GAME_SYNC` has its own destination (`/app/game.*.sync`), so the interceptor classifies it
into `snapshot` from the headers alone.

`REQUEST_ROOM_STATE` does **not** — it shares `/app/room.{roomId}.member` with `TOGGLE_READY` and the
other member commands, and the distinguishing `type` field lives in the payload. Rather than
deserialize every member frame in the interceptor just to classify it, the member channel is charged
the (cheap) `command` bucket at the interceptor, and `REQUEST_ROOM_STATE` additionally consumes the
`snapshot` bucket **inside its `@MessageMapping` handler**, before it acquires the room lock — where
the `type` has already been deserialized for free.

This is the same fast-fail/authoritative split the authorization model uses (`room-websocket.md`
§ Authorization Model): the channel check is the cheap one, the handler check is the one that matters.

### The penalty ladder

1. **Over-limit frame → dropped.** Not queued, not delayed. An `ERROR` goes to `/user/queue/errors`:

   ```json
   {
     "type": "ERROR",
     "payload": {
       "code": "RATE_LIMIT_EXCEEDED",
       "message": "You are sending messages too quickly.",
       "bucket": "chat",
       "retryAfterMs": 800
     }
   }
   ```

   Frames dropped at the **interceptor** carry no `correlationId` — the payload was never
   deserialized. Frames dropped at the **handler** (`REQUEST_ROOM_STATE`) echo it.

   **The error emission is itself throttled** to at most one per bucket per second. Without this the
   abuse control becomes an amplifier: a client sending 1 000 frames/s would make the server emit
   1 000 unicast error frames/s.

2. **Sustained violation → connection closed.** More than **20 dropped frames within 10 seconds** on
   one connection means the client is ignoring the errors. The connection is closed with a STOMP
   `ERROR` frame (`code: RATE_LIMIT_ABUSE`).

3. **Reconnect lockout.** A close under (2) writes `rate:ws-lockout:{userId}` in **Redis** — the one
   piece of Tier 6 that must be distributed, because the client's next `CONNECT` may land on a
   different pod and pods restart. Subsequent `CONNECT` frames are rejected while the key is live:
   **30 s initially, doubling per repeat offence, capped at 15 minutes.** The offence counter decays
   after one hour without a violation.

**A closed connection during a game starts that player's grace period** (`reconnection-flow.md`
FR-GRACE-004), and the platform makes no distinction between a flooder's forced disconnect and any
other. This is intended and self-inflicted. Note how the numbers compose: a first offence (30 s
lockout) resolves well inside a 60 s grace period, so a user with a runaway client returns and keeps
their slot; a repeat offender's lockout eventually exceeds the grace window, their slot is released,
and the game backend receives `player_left` with reason `GRACE_PERIOD_EXPIRED`. The escalation removes
persistent abusers from live games without a separate mechanism.

### Connection cap

**Maximum 4 concurrent WebSocket connections per user.** A 5th `CONNECT` is rejected with a STOMP
`ERROR` (`code: TOO_MANY_CONNECTIONS`). Two or three tabs is ordinary; forty is an attempt to
multiply a per-principal budget by opening more sockets.

### Pod-local budgets, and what they do not cover

Under room affinity a user's frames for a given room all land on that room's pod, so the pod-local
bucket sees the user's whole stream. If a user somehow holds connections on **two** pods (e.g. two
tabs in two different rooms, if the product ever permits it), each pod enforces the full budget
independently and the user's effective ceiling is 2×.

This is accepted. These budgets are **abuse controls, not fairness quotas** — the question they answer
is "can one client melt a room or a game session", and the answer stays no at 2× or 4×. The connection
cap bounds the multiplier, and the expensive frames (`snapshot`) are additionally serialized by the
room and session locks they contend for. A Redis round trip per frame is not worth buying a tighter
constant here.

---

## 429 response shape (HTTP)

All HTTP rate-limit rejections return an RFC 9457 Problem Detail (see
[error-handling.md](error-handling.md)):

```json
{
  "type": "https://turnbase.io/errors/rate-limit-exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Too many requests. Please wait before retrying.",
  "instance": "/api/auth/login"
}
```

`Retry-After` is always present on a 429 and gives the minimum seconds to wait.

---

## Configuration and environments

**Every number on this page is a property.** GRMP hardcoded a 5-per-15-minute login limit and it
blocked every test session for months; the workaround was deleting Redis keys by hand (GRMP lesson
F6). That is a spec failure, not an ops failure.

```properties
turnbase.rate-limit.enabled=true

turnbase.rate-limit.auth.failures-before-lockout=5
turnbase.rate-limit.auth.initial-lockout=30s

turnbase.rate-limit.api.capacity=100
turnbase.rate-limit.api.window=10s

turnbase.rate-limit.upload.capacity=10
turnbase.rate-limit.upload.window=1h

turnbase.rate-limit.public.capacity=200
turnbase.rate-limit.public.window=1m

turnbase.rate-limit.minting.guest.capacity=5
turnbase.rate-limit.minting.guest.window=1h
turnbase.rate-limit.minting.registration.capacity=3
turnbase.rate-limit.minting.registration.window=1h

turnbase.rate-limit.ws.connection.capacity=30
turnbase.rate-limit.ws.connection.refill=10/1s
turnbase.rate-limit.ws.snapshot.capacity=2
turnbase.rate-limit.ws.snapshot.refill=1/3s
turnbase.rate-limit.ws.action.capacity=10
turnbase.rate-limit.ws.action.refill=5/1s
turnbase.rate-limit.ws.chat.capacity=5
turnbase.rate-limit.ws.chat.refill=1/1s
turnbase.rate-limit.ws.command.capacity=10
turnbase.rate-limit.ws.command.refill=2/1s
turnbase.rate-limit.ws.subscribe.capacity=20
turnbase.rate-limit.ws.subscribe.refill=1/1s

turnbase.rate-limit.ws.max-connections-per-user=4
turnbase.rate-limit.ws.violations-before-close=20
turnbase.rate-limit.ws.violation-window=10s
turnbase.rate-limit.ws.lockout.initial=30s
turnbase.rate-limit.ws.lockout.max=15m

turnbase.security.trusted-proxies=10.0.0.0/8,172.16.0.0/12
```

Two rules keep this from becoming the hole it is meant to close:

- **Absent property → strict default**, never "unlimited". A typo in a key name must fail closed.
- **`turnbase.rate-limit.enabled=false` is honoured only under the `test` or `e2e` Spring profile.**
  Under any other profile the application **fails to start**. The escape hatch that makes e2e runs
  bearable must not be the one that ships to production, so the guard is a startup assertion, not a
  convention.

Local development (`dev` profile) keeps limits **on**, with the same values. Rate limiting is a thing
you want to have exercised before it is the only thing between you and the public internet.

---

## Requirements traceability

| Requirement / gap | Realized by |
|---|---|
| `user-accounts.md` NFR-SEC-003 | Tier 1 |
| `user-accounts.md` NFR-SEC-006 (public endpoints) | Tier 4 |
| FR-GUEST-001/003 (guest minting) | Tier 5 |
| FR-AUTH-001 (registration) | Tier 1 (failures) + Tier 5 (successes) |
| **API-1** — WebSocket messages unthrottled | Tier 6 |
| **API-2** — guest creation unthrottled | Tier 5 |
| api-design review gap 8 — client-IP derivation | [Client identity](#client-identity-deriving-the-ip) |
| GRMP-F6 — per-environment configurability | [Configuration and environments](#configuration-and-environments) |
| `websocket.md` OQ-001 (resync cost under load) | `snapshot` bucket — bounds the *adversarial* case; the mass-reconnect case remains as specced there |

---

## Open questions

- **OQ-001 — Shared-IP guest throttling.** Tier 5 keys on IP, so a CGNAT or campus NAT shares one
  bucket. If real usage hits this, the options in order of cost are: raise the limit, key on IP + User-Agent
  entropy, or gate guest creation behind a proof-of-work. Not worth pre-solving for a local-first MVP.
- **OQ-002 — Tier 6 budgets are per-pod.** Documented above under
  [Pod-local budgets](#pod-local-budgets-and-what-they-do-not-cover). Revisit only if a multi-room
  concurrent membership feature lands.
