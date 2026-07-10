## Last Session Summary

**Date:** 2026-07-10

**Resolved the room-lifecycle blocker cluster (CORE-1/2/3)** from the MVP readiness
review — the three top blockers, all requirements-level contradictions on the
create→play→finish happy path. Ran an interactive requirements-engineering session; all
four decisions taken on the review's recommended path:

- **CORE-1 (initial teams):** On room creation, instantiate `count.min` teams per template
  at `size.max`; host auto-assigns via FR-TEAM-005 (first team, first template). Initial
  capacity = Σ(size.max × count.min); advertised min/max (FR-LIST-002) unchanged. New
  **FR-TEAM-012** + FR-CREATE-003 cross-ref.
- **CORE-2 (voluntary leave vs disconnect):** Reversed the old "no distinction" model. A
  **confirmed** in-app action (Leave Room, abandonment-to-join-elsewhere, account deletion)
  = immediate departure: `PLAYER_LEFT`, notify game engine now (reason `left`), no grace.
  A bare WS loss — **including tab/browser close** — is involuntary → grace period. Joining
  another room voids any held reservation (early expiry). New **FR-DC-005**, **FR-EXPIRY-004**;
  amended Disconnect definition + added Voluntary Leave definition; amended FR-DC-001,
  FR-JOIN-007, FR-LIFE-004.
- **CORE-3 (last-human host disconnect):** In Progress + no other connected human → defer
  host transfer and closure for the grace period; close + terminate session only on expiry.
  FR-XFER-002's immediate closure now scoped to Lobby + explicit leaves. New **FR-HDISC-003**;
  amended FR-HDISC-001, FR-XFER-002.
- **Downstream contract fix:** extended `game-contracts.md` FR-IN-005 (and FR-FE-004)
  `player_left` reason enum with `left` for immediate voluntary departures — closing the new
  contradiction the CORE-2 decision would otherwise have introduced. The wire proto
  (`gamehost.proto`) reason enum still needs the `left` value (already in the review's gRPC
  edit checklist).

**Files changed:**
- `docs/requirements/game-rooms.md` — FR-CREATE-003, new FR-TEAM-012, FR-JOIN-007,
  FR-LIFE-004, FR-XFER-002
- `docs/requirements/reconnection-flow.md` — Definitions, Stakeholders, FR-DC-001,
  new FR-DC-005, new FR-EXPIRY-004, FR-HDISC-001, new FR-HDISC-003
- `docs/requirements/game-contracts.md` — FR-IN-005, FR-FE-004 (`left` reason)
- `STATUS.md` — this update

---

## Next Priorities

Work the review's action plan (`docs/reviews/2026-07-02-mvp-readiness/INDEX.md`) before
starting new feature specs:

1. **Owner decisions** (review §Strategic decisions): AWS/EKS + gVisor timing,
   compose-first MVP profile, WS scaling model (room affinity vs Redis pub/sub),
   availability target, GDPR/account-erasure, spike scheduling.
2. **Blocker spec fixes** — ~~room lifecycle (CORE-1/2/3)~~ ✅ resolved 2026-07-10;
   WS abuse controls (API-1/2), game-effect delivery + crash-recovery idempotency +
   FE serving origin (GAME-B1/B2/B3).
3. **New ops specs** — deployment & infrastructure, data operations, secrets &
   production observability.
4. **Espresso feasibility spike** — before freezing FR-CTX enforcement design and the
   3s/5s startup Musts.
5. **Then resume the previously planned queue**: game bundle format + upload pipeline
   (FR-BUNDLE-*/FR-UPLOAD-*, now also owns gdkApiVersion check, serialization
   round-trip test, asset-origin decision), test harness (FR-HARNESS-*), platform-frontend
   shell spec (must fail closed on trust level — GRMP-F5).

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
| `game-history.md` | Per-session history recording, win condition labels, profile history tab, privacy |
| `social-friends.md` | Friendship model, request lifecycle, friend cap, discovery, visibility, guest exclusion, block-requests toggle |
| `platform-operations.md` | Service topology (monolith), availability, observability stack, CI/CD pipeline, data retention |
| `onboarding-wizard.md` | First-time wizard overlay, pane structure, localStorage suppression, landing page re-entry |
| `admin-tooling.md` | Internal admin API, game badge model (Official/Verified/Unverified), review queue, private game behaviour |

---

## Open Questions Remaining in Existing Docs

| Document | Open Question |
|----------|---------------|
| `reconnection-flow.md` | Game engine response set after "player lost" event — deferred to Game SDK contracts |
| `game-history.md` | OQ-002: Pagination reuse — shared UI component vs. API pattern deferred to implementation |
| `game-contracts.md` | OQ-001: Log color annotation syntax — deferred to GDK spec |
| `game-contracts.md` | OQ-002: AI/bot player interface — deferred to future spec |
| `game-contracts.md` | OQ-003: Platform-managed timer system — deferred to future spec |
| `admin-tooling.md` | OQ-001: Can a developer resubmit a rejected game, or is rejection terminal? |
| `admin-tooling.md` | OQ-002: Can an operator delist a Verified or Official game post-approval? |
