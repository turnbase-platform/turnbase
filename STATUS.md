## Last Session Summary

**Date:** 2026-07-12 (session 7)

**Wrote the abuse-control specs** (STATUS priority #6) — `rate-limiting.md` rewritten and
`input-validation.md` written new. **Closes API-1, API-2 and API-6**, plus api-design review gap 8
(client-IP derivation) and GRMP lesson F6 (per-env configurability). These were the review's
"unthrottled spam vectors" — the reason its verdict was *"not yet safe to expose on the public
internet."*

**The architectural call: WebSocket rate limiting is pod-local, not Redis-backed.** The existing doc
opened with "Bucket4j backed by Redis" and the review assumed the same. But **room affinity (ADR-0002)
pins every frame a user sends about a room to that room's pod**, so an in-JVM bucket keyed by principal
observes that user's *entire* frame stream — it is exact, not approximate. Redis would have put a
network round trip on the inbound path of every chat message and every game action to buy nothing.
Rate-limit locality follows the same affinity argument as effect fan-out. HTTP tiers stay Redis-backed:
they are IP-keyed and run *before* authentication, so any pod may serve them.

**Two places the review's suggested fix was weaker than what the specs already allowed:**

1. **`parameters` is a whitelist, not a size cap.** The review proposed capping the `CHANGE_PARAMETERS`
   object at 4 KB. But `manifest-schema.md` **already declares a typed parameter schema**
   (`key`/`type`/`default`/`min`/`max`/`options`), so unknown keys can simply be *rejected*. The
   amplification vector is gone **by construction** rather than merely bounded, and a host can no
   longer push attacker-chosen data through the platform into every room member's client.
2. **NFC does not stop impersonation.** The review proposed NFC-normalizing usernames. NFC does nothing
   about `Аlice` (Cyrillic А) vs `Alice` — they are distinct strings that render identically. Usernames
   now carry an ICU4J **confusable-skeleton uniqueness index** plus a **mixed-script restriction**
   (`MODERATELY_RESTRICTIVE`), which is where homoglyph attacks actually live. The `guest-` reserved
   prefix (FR-AUTH-013) is checked against the *skeleton* too — otherwise a Cyrillic `е` walks past it.

**Design decisions recorded:**
1. **Tier 6 buckets are sized by cost, not uniformly.** The strictest is `snapshot` (1 per 3s):
   `REQUEST_GAME_SYNC` **re-enters the guest VM** (`onResync`) under the session's single-flight lock,
   making it the most expensive frame a client can send — a flood is a self-DoS of the whole session,
   strictly worse than a chat flood. `REQUEST_ROOM_STATE` shares a destination with other member
   commands, so it is charged the cheap `command` bucket at the interceptor and the `snapshot` bucket
   *inside its handler*, where `type` is already deserialized — the same fast-fail/authoritative split
   the authorization model uses.
2. **Penalty ladder: drop → close → Redis reconnect lockout** (30s, doubling, capped 15m). Closing a
   connection mid-game starts the flooder's *own* grace period, so escalation removes persistent
   abusers from live games with no separate mechanism. The numbers compose: a first offence (30s)
   resolves inside a 60s grace period; a repeat offender's lockout outlives it and they are dropped.
   **The error emission is itself throttled** (1/bucket/second) — otherwise the abuse control becomes
   an amplifier, emitting 1 000 unicast errors/s at a client sending 1 000 frames/s.
3. **Tier 5 counts *successes*.** Tier 1 counts only failures, and guest creation *always succeeds* —
   which is precisely why it leaked past it. 5 guests + 3 registrations per IP/hour; the two counters
   coexist on the same endpoints and do not interact. (New requirement: NFR-SEC-007.)
4. **IPv6 IP-tiers key on the /64 prefix.** A routed /64 gives one attacker 2^64 addresses; keying on
   the full address makes every IP-based tier silently worthless.
5. **`enabled=false` is permitted only under the `test`/`e2e` profile** — the app fails to start
   otherwise. GRMP's hardcoded login limit blocked every test session for months (workaround: deleting
   Redis keys by hand), so the escape hatch is mandatory *and* must not be shippable.
6. **The game log is the platform's only non-plain-text render surface**, and its content is composed
   by *game code* — the one place "React escapes by default" does not save us. Markdown renderer runs
   with raw HTML disabled, no links, no autolinking. Accepted residual: a username containing Markdown
   metacharacters can corrupt log *formatting* (cosmetic, never markup).
7. **BCrypt silently truncates at 72 bytes**, so a 128-char Unicode password loses entropy without a
   word. Argon2id (already NFR-SEC-001) is now load-bearing, not merely preferred.

**Files changed:**
- `docs/specs/api-design/rate-limiting.md` — **rewritten**: two enforcement domains, client-IP
  derivation, Tier 5 (minting), Tier 6 (WebSocket), penalty ladder, configuration
- `docs/specs/api-design/input-validation.md` — **new**: pipeline, canonicalization, field catalogue,
  size limits, `CHANGE_PARAMETERS` whitelist, output encoding
- `docs/requirements/user-accounts.md` — FR-AUTH-014/015 (username charset, impersonation safety),
  NFR-SEC-007 (minting throttle); FR-AUTH-003/013 amended to run on the skeleton
- `docs/specs/api-design/websocket.md` — the two "unthrottled / known gap" hedges replaced with the
  real budgets; OQ-001 narrowed to the legitimate mass-reconnect case
- `docs/specs/api-design/room-websocket.md` — 6 new error codes (parameters, validation, rate limit)
- `docs/specs/api-design/room-chat-websocket.md`, `rest-conventions.md` (413), `INDEX.md`
- `docs/requirements/game-rooms.md`, `in-room-chat.md` — spec links
- `docs/reviews/2026-07-02-mvp-readiness/INDEX.md`, `STATUS.md`

---

## Next Priorities

Continue the review's action plan (`docs/reviews/2026-07-02-mvp-readiness/INDEX.md`).

**Blocker status: of the review's 15, the game-execution chain (GAME-B1/B2/B3) and the API abuse
surface (API-1/API-2) are fully closed. API-3 and OPS-1…6 are *decided* (ADR-0001…0006) but still need
their doc edits and specs written. Only CORE-1/2/3 — the room-lifecycle contradictions — remain
genuinely undecided, which makes them the top of the queue.**

1. **Owner decisions** — ✅ done (ADR-0001…0005, 2026-07-10).
2. **Espresso feasibility spike** (ADR-0005) — ✅ done (2026-07-11) → **ADR-0006** (official-only Java).
3. **Game Host internals spec** — ✅ done (session 4). Closed GAME-I1/I2, GAME-B2, exec-half of B1.
4. **Game-session WebSocket spec** — ✅ done (session 5). Closed **GAME-B1**, **I4**, **I6**.
5. **Game FE serving origin / sandbox / CSP** — ✅ done (session 6). Closed **GAME-B3**, **API-5**.
6. **WS abuse controls + input validation** — ✅ done (2026-07-12, session 7). `rate-limiting.md`
   (rewritten) + `input-validation.md` (new). Closed **API-1**, **API-2**, **API-6**, review gap 8,
   GRMP-F6.
7. **Room-lifecycle contradictions (CORE-1/2/3)** — ← **next.** The last undecided blockers, and they
   sit on the room *happy path*: initial team instantiation at room creation is undefined (the flow
   forks there); voluntary "Leave Room" mid-game contradicts the no-distinction disconnect model
   (`reconnection-flow.md` vs `game-rooms.md`); host disconnect with no other human points both ways
   (immediate closure vs grace). Needs decisions, then edits to `game-rooms.md` +
   `reconnection-flow.md`. Group with the rest of that cluster: grace timers as **persisted absolute
   deadlines** + sweep (GRMP-F3), room-closure → `TerminateSession` ordering (GRMP-F2).
8. **Existing-doc edit checklist, remainder:** `platform-operations.md` (reconciliation sweep GRMP-F1;
   **replace the Redis-pub/sub scaling text with room affinity — the API-3 doc edit**;
   Dependabot/Trivy + frontend in FR-CICD-001), `rest-conventions.md` (authz/IDOR ownership model,
   actuator on a separate management port, logout endpoint, idempotency), `user-accounts.md` (password
   change FR, logout FR, OAuth email-collision rule, lockout decay), notifications/SSE event classes,
   `platform-ui-library.md` (Tabs/Select/Switch/Badge; Avatar contradiction), gRPC proto sweep
   (GAME-I3 failed-action drop semantics, `GameOutcome` validation).
9. **New specs (rescoped local-first):** local deployment & infrastructure (Docker Desktop K8s +
   compose per ADR-0001), data-operations (Postgres/Redis local, accepted game-state loss window —
   OPS-4), secrets & config (OPS-5).
10. **Then** the previously planned queue: game bundle format + upload pipeline (must unpack into the
    `/g/{gameId}/{version}/` layout `game-asset-serving.md` §4.1 serves; `gdkApiVersion` check
    GAME-I7), test harness, platform-frontend shell spec (must honor the `websocket.md` relay contract
    and the iframe embedding contract in `game-asset-serving.md` §6).

---

## Coverage Summary

| Document | Coverage |
|----------|----------|
| `user-accounts.md` | Registration, auth, sessions, account management, profiles, guests, per-section privacy settings, block-requests toggle |
| `game-rooms.md` | Room list, creation, joining, host management, teams, readiness, lifecycle, mid-game join assignment |
| `game-catalog.md` | Catalog listing, game detail, game management, profile games tab |
| `notifications-invitations.md` | Alerts, notification center, invitations, friend request notifications |
| `reconnection-flow.md` | Disconnect detection, grace period, re-entry, kick mechanics |
| `in-room-chat.md` | Room/team channels, messaging, delivery model, late-join team chat access |
| `per-game-statistics.md` | Session counting, game detail stats, profile stats |
| `platform-views.md` | All views, navigation, redirects, auth tier gating |
| `game-development-experience.md` | GDK, game packaging, upload pipeline, local dev workflow |
| `game-contracts.md` | Platform ↔ game BE/FE protocol, effect types, structured outcome, postMessage API |
| `platform-architecture.md` | Game execution infrastructure, Game Host, Orchestration Service, sandboxing, scaling |
| `game-history.md` | Per-session history recording, win condition labels, profile history tab, privacy, deletion pseudonymization |
| `social-friends.md` | Friendship model, request lifecycle, friend cap, discovery, visibility, guest exclusion, block-requests toggle |
| `platform-operations.md` | Service topology (monolith), availability, observability stack, CI/CD pipeline, data retention |
| `onboarding-wizard.md` | First-time wizard overlay, pane structure, localStorage suppression, landing page re-entry |
| `admin-tooling.md` | Internal admin API, game badge model (Official/Verified/Unverified), review queue, private game behaviour |

**Decisions:** `docs/decisions/` — ADR-0001 (local-first platform), ADR-0002 (WS room affinity),
ADR-0003 (availability), ADR-0004 (erasure pseudonymization), ADR-0005 (sandbox / Espresso spike),
ADR-0006 (game trust model — official-only Java for MVP), ADR-0007 (game FEs on a separate
registrable domain).

---

## Open Questions Remaining in Existing Docs

| Document | Open Question |
|----------|---------------|
| `reconnection-flow.md` | Game engine response set after "player lost" event — deferred to Game SDK contracts |
| `game-history.md` | OQ-002: Pagination reuse — shared UI component vs. API pattern deferred to implementation |
| `game-contracts.md` | OQ-001: Log color annotation syntax — deferred to GDK spec |
| `game-contracts.md` | OQ-002: AI/bot player interface — deferred to future spec |
| `game-contracts.md` | OQ-003: Platform-managed timer system — deferred to future spec |
| `websocket.md` | OQ-001: Resync cost under a *legitimate* mass reconnect (N resyncs serialize behind one session lock) — cache the per-viewer view against `lastAppliedSequence` if it becomes a hotspot. The adversarial case is now closed by the Tier 6 `snapshot` bucket |
| `websocket.md` | OQ-002: A game whose `onResync` returns an empty spectator view leaves spectators blank until the next `broadcast` — the test harness should warn |
| `admin-tooling.md` | OQ-001: Can a developer resubmit a rejected game, or is rejection terminal? |
| `admin-tooling.md` | OQ-002: Can an operator delist a Verified or Official game post-approval? |
| `game-asset-serving.md` | OQ-001: Fullscreen — `allow=""` grants no Permissions-Policy features; whether to add `allow="fullscreen"` is a shell-spec UX call |
| `game-asset-serving.md` | OQ-002: Private-bundle exposure — bundle assets are unauthenticated; a signed-token variant is additive if genuinely private third-party bundles become a requirement post-MVP |
| `game-asset-serving.md` | OQ-003: Manifest-declared stylesheets — CSS must currently be imported from JS; deferred to the bundle spec |
| `rate-limiting.md` | OQ-001: Shared-IP (CGNAT/campus NAT) guest throttling — accepted for a local-first MVP; escalation path is raise limit → add entropy to the key → proof-of-work |
| `rate-limiting.md` | OQ-002: Tier 6 budgets are per-pod, so a user connected to two pods gets 2× — accepted (these are abuse controls, not fairness quotas); revisit only if concurrent multi-room membership lands |
| `input-validation.md` | OQ-001: No emoji or symbols in usernames — the clean fix, if users push back, is a separate free-form display name alongside a strict username (post-MVP model change) |
| `input-validation.md` | OQ-002: ASCII-only email rejects IDN/EAI addresses — revisit if a real user is blocked; there is no mail system in the MVP to normalize against (no verification email is sent) |
