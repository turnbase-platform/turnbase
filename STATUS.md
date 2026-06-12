## Last Session Summary

**Date:** 2026-06-11

Defined the gRPC service contract for Orchestration Service ↔ Game Host communication (a "Significant" requirements gap). Drove an explicit topology decision with an independent reviewer agent, then authored the proto + design spec.

**New specs** (`docs/specs/internal-grpc/`):

- `gamehost.proto` — proto3 contract (validated + linted clean with `buf`, STANDARD ruleset). Two services: `GameHostService` (dispatch, served by Game Host — `CreateSession`/`ProcessInput`/`TerminateSession`, unary) and `GameHostRegistryService` (control, served by Orchestration — `Register`/`Heartbeat`/`ReportContexts`/`Deregister`). Effects, structured `game_over` outcome, two-tier failure model, per-session `sequence` for idempotent re-dispatch.
- `buf.yaml` — buf module config (STANDARD lint; `PACKAGE_DIRECTORY_MATCH` excepted while the proto lives in the docs tree).
- `orchestration-gamehost-protocol.md` — design rationale: topology decision (dual-service unary dispatch chosen over single-bidi-stream and server-streaming), pod addressing, idempotency/exactly-once semantics, error model, message-size handling, security/observability.
- `INDEX.md` — new `internal-grpc` spec subdirectory entry point.

**Topology decision (educational record in the protocol doc):** Chose **dual service, unary dispatch**. The deciding constraint is Orchestration statelessness (FR-ORCH-002/006/007): the channel of record is the Redis routing table + action queue, so gRPC connections must be disposable. A single Game-Host-initiated bidi stream was rejected because it pins each session to one Orchestration replica (smuggling in session affinity). Verdict was reached independently by both the lead analysis and a reviewer agent (A > C > B; B disqualified).

**Cross-links updated:** `docs/specs/INDEX.md`, `api-design/INDEX.md`, `platform-architecture.md` (Related API Specifications), `game-contracts.md` (new Related API Specifications section), `requirements-gaps.md` (item checked off).

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

---

## Open Questions Remaining in Existing Docs

| Document | Open Question |
|----------|---------------|
| `reconnection-flow.md` | Game engine response set after "player lost" event — deferred to Game SDK contracts |
| `game-history.md` | OQ-002: Pagination reuse — shared UI component vs. API pattern deferred to implementation |
| `game-contracts.md` | OQ-001: Log color annotation syntax — deferred to GDK spec |
| `game-contracts.md` | OQ-002: AI/bot player interface — deferred to future spec |
| `game-contracts.md` | OQ-003: Platform-managed timer system — deferred to future spec |
