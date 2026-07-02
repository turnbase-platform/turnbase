## Last Session Summary

**Date:** 2026-07-02

**Ran the Phase-0 exit MVP readiness review** — five parallel domain reviews (platform-core
requirements, API design/sanitation, game execution stack, DevOps/deployment for AWS,
GRMP prototype lessons) answering: are the specs sufficient to implement and ship the
first MVP online?

- **Verdict: not yet, but close** — 15 blocking gaps + ~30 important ones, clustered in
  three areas: room-lifecycle contradictions on the happy path, unspecified connective
  tissue at both ends of the game-execution chain (effect delivery destinations,
  crash-recovery double-apply, game FE serving origin), and an almost entirely
  undecided deployment path (provider "TBD", no IaC, no migration tool, no secrets
  strategy, Redis durability contradiction, ingress/TLS undefined).
- New `docs/reviews/2026-07-02-mvp-readiness/` directory: `INDEX.md` (synthesis —
  consolidated blockers, strategic decisions needing the owner, new-spec plan,
  existing-doc edit checklist) plus the five full domain reports.
- Estimated closure effort: 3–4 focused spec sessions + one technical spike (Espresso
  sandbox/startup feasibility on GraalVM CE, which may force the OQ-002
  process-isolation fallback).
- GRMP mining confirmed several TurnBase design choices (single WS gateway, effects-push
  hidden-information safety, host-driven start) and surfaced missing lifecycle hygiene:
  reconciliation sweep, durable grace timers, session-teardown ordering, shared
  serialization component.

**Files changed:**
- `docs/reviews/2026-07-02-mvp-readiness/` — new (INDEX.md + 5 domain reports)
- `STATUS.md` — this update

---

## Next Priorities

Work the review's action plan (`docs/reviews/2026-07-02-mvp-readiness/INDEX.md`) before
starting new feature specs:

1. **Owner decisions** (review §Strategic decisions): AWS/EKS + gVisor timing,
   compose-first MVP profile, WS scaling model (room affinity vs Redis pub/sub),
   availability target, GDPR/account-erasure, spike scheduling.
2. **Blocker spec fixes** — room lifecycle (CORE-1/2/3), WS abuse controls (API-1/2),
   game-effect delivery + crash-recovery idempotency + FE serving origin (GAME-B1/B2/B3).
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
