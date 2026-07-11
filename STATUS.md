## Last Session Summary

**Date:** 2026-07-11 (session 5)

**Wrote the game-session WebSocket protocol** (review "New spec documents" #5; STATUS priority #4) —
the client half of the game execution chain, picking up exactly where session 4's Game Host spec
stopped ("Orchestration hands effect E to the Gateway, addressed to recipient set R, tagged with
`sequence` N"). Per owner decision it was written **into `websocket.md` in place** rather than as a
new doc. **Closes GAME-B1, GAME-I4, GAME-I6.**

**The load-bearing owner decision: catch-up by `resync`, not by an effect journal.**
The review recommended retaining every effect per session and replaying it on subscribe. The owner
chose instead to **ask the game backend** for an attaching viewer's current view. Rationale: a journal
means archiving every ≤10 MB effect payload of every live session in a single non-HA Redis (OPS-4);
and only the game backend *can* compose a per-viewer snapshot, since the platform is forbidden to read
game state (NFR-SEC-003) and each viewer is entitled to a different slice of it. ADR-0006 (first-party
games only) makes the contract addition cheap now and expensive later.

**How it closes I6 without a race.** The client subscribes *first*, then requests a sync. The backend's
read-only `onResync` returns the view plus the `asOfSequence` it reflects. Anything at or below that
watermark is inside the snapshot; anything above it was fanned out *after* the client was already
subscribed, so it was buffered and applies on top. One mechanism covers game start, reconnection, and
late join. Falls out for free: **the resync view is always the first `game_event` a freshly loaded game
FE receives**, so a game FE never has to distinguish a snapshot from a delta — which also resolves
frontend-gdk OQ-001.

**Design decisions recorded:**
1. **Destinations:** `broadcast`/log/lifecycle → `/topic/game.{sessionId}`; `send_to_team` →
   `/topic/game.{sessionId}.team.{teamId}` (membership-validated subscription); `send_to_player` →
   `/user/queue/game`. NFR-SEC-002 becomes mechanical rather than aspirational.
2. **`(sequence, index)`** is the wire dedup/ordering key; `index: -1` for platform lifecycle events
   sorts them ahead of the game's effects for the same input. **No gap detection** — the game stream is
   deliberately sparse (a `send_to_player` to someone else consumes a sequence you never see), unlike
   the room's dense `version` stream. Recovery is always by resync, never by gap.
3. **Session affinity follows room affinity** (ADR-0002) → effect fan-out is a local call.
4. **Action authorization (I4):** channel-level fast-fail + authoritative re-check under the session
   lock (participation is mutable — kick, grace expiry). Spectators can never act.
5. **`SESSION_FAILED` moved to the session topic** (it is session-wide, not a per-user command error).
6. A failed `onResync` fails **only that client's attach** — never the session, and it does not count
   toward the retry limit. A read cannot kill a game.

**Contract ripple (the price of the resync call — all edited now):** new `resync` input
(game-contracts FR-IN-006/FR-RESP-005, FR-DELIVER-005/006), dedicated `Resync` RPC in the proto
(deliberately *not* a `ProcessInput` variant: no sequence, no state write, no watermark), a 4th
required GDK hook (`onResync` → `ViewResult`), and the read-only dispatch path in the Game Host spec.
FR-FE-001's "initial state arrives via `send_to_player`" is now false and was corrected — `onInit`
effects are **not** delivery-guaranteed.

**Also fixed in passing:** the `GAME_STARTED` topic-separator bug (review API-4), and the missing
`PLAYER_LEFT_REASON_LEFT` proto/GDK enum value that FR-IN-005 requires.

**Files changed:**
- `docs/specs/api-design/websocket.md` — **the spec** (Game Session Protocol section)
- `docs/specs/api-design/{INDEX.md,room-websocket.md}` — index entry; `GAME_STARTED` fix
- `docs/requirements/game-contracts.md` — FR-IN-006, FR-RESP-005, FR-FE-001 correction, spec links
- `docs/requirements/platform-architecture.md` — FR-DELIVER-005/006, spec link
- `docs/requirements/game-development-experience.md` — FR-GDK-002/003, NFR-DX-002
- `docs/requirements/reconnection-flow.md` — Related API Specifications
- `docs/specs/internal-grpc/{gamehost.proto,orchestration-gamehost-protocol.md,INDEX.md}` — `Resync`
- `docs/specs/gdk-api/{backend-gdk-api.md,frontend-gdk-api.md,INDEX.md}` — `onResync`, OQ-001 resolved
- `docs/specs/game-host/game-host-internals.md` — read-only dispatch path, no-journal statement
- `docs/reviews/2026-07-02-mvp-readiness/INDEX.md`, `STATUS.md` — closure record

---

## Next Priorities

Continue the review's action plan (`docs/reviews/2026-07-02-mvp-readiness/INDEX.md`):

1. **Owner decisions** — ✅ done (ADR-0001…0005, 2026-07-10).
2. **Espresso feasibility spike** (ADR-0005) — ✅ done (2026-07-11). Outcome: untrusted Java not
   isolable in-JVM on CE → **ADR-0006** scopes MVP to official-only Java. Game Host isolation for the
   MVP = interrupt timeouts + container memory limit (no adversarial in-JVM enforcement).
3. **Game Host internals spec** — ✅ done (2026-07-11, session 4). Espresso-in-hardened-container;
   `docs/specs/game-host/game-host-internals.md`. Closed GAME-I1/I2, GAME-B2, exec-half of GAME-B1;
   reconciled GAME-M4, GAME-I5, and the I/O-denial contradiction.
4. **Game-session WebSocket spec** — ✅ done (2026-07-11, session 5). `websocket.md` § Game Session
   Protocol. Closed **GAME-B1** (client half), **I4**, **I6**. Catch-up is by read-only `resync`
   (new game-contract input), not by an effect journal.
5. **Remaining execution-chain blocker** — **GAME-B3**: game FE serving origin, iframe `sandbox`
   attributes, and CSP. It is the last hard prerequisite for the client path, and the FE GDK's
   bootstrap contract (frontend-gdk-api §9) plus the shell relay contract (websocket.md) both already
   depend on the origin decision. Pairs naturally with the bundle/upload-pipeline spec.
6. **WS abuse controls (API-1/2)** — `rate-limiting.md` WS message tier (chat flood, room-lock
   starvation, and now `SUBMIT_ACTION`/`REQUEST_GAME_SYNC`, all reachable by guests) + guest-creation
   bucket. The game-session spec explicitly leaves its destinations unthrottled and flags it.
7. **New specs (rescoped local-first):** local deployment & infrastructure spec (Docker Desktop K8s +
   compose per ADR-0001), data-operations spec (Postgres/Redis local, accepted game-state loss window
   — OPS-4), secrets & config spec, `input-validation.md` (API-6).
8. **Existing-doc edit checklist cluster** (review §): game-rooms/reconnection grace timers as
   persisted deadlines (GRMP-F2/F3), platform-operations reconciliation sweep (GRMP-F1) +
   Dependabot/Trivy + frontend in FR-CICD-001, rest-conventions authz/IDOR, platform-ui-library
   additions. *(Two items already done: the `left` proto reason value and the `GAME_STARTED`
   separator fix, session 5.)*
9. **Then** the previously planned queue: game bundle format + upload pipeline, test harness,
   platform-frontend shell spec (must fail closed on trust level — GRMP-F5; must honor the
   `websocket.md` relay contract and the `__TURNBASE__` bootstrap contract).

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
ADR-0006 (game trust model — official-only Java for MVP).

---

## Open Questions Remaining in Existing Docs

| Document | Open Question |
|----------|---------------|
| `reconnection-flow.md` | Game engine response set after "player lost" event — deferred to Game SDK contracts |
| `game-history.md` | OQ-002: Pagination reuse — shared UI component vs. API pattern deferred to implementation |
| `game-contracts.md` | OQ-001: Log color annotation syntax — deferred to GDK spec |
| `game-contracts.md` | OQ-002: AI/bot player interface — deferred to future spec |
| `game-contracts.md` | OQ-003: Platform-managed timer system — deferred to future spec |
| `websocket.md` | OQ-001: Resync cost under a mass reconnect (N resyncs serialize behind one session lock) — cache the per-viewer view against `lastAppliedSequence` if it becomes a hotspot |
| `websocket.md` | OQ-002: A game whose `onResync` returns an empty spectator view leaves spectators blank until the next `broadcast` — the test harness should warn |
| `admin-tooling.md` | OQ-001: Can a developer resubmit a rejected game, or is rejection terminal? |
| `admin-tooling.md` | OQ-002: Can an operator delist a Verified or Official game post-approval? |
