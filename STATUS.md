## Last Session Summary

**Date:** 2026-06-29

**Cross-spec cleanup** of the loose ends opened by last session's GDK API specs.

- **`Team.name` resolution documented.** Pinned down the open ambiguity: `Team.name`
  is the **instance** display name (`"{template.name} {index}"`, e.g. `"Attacker 1"`,
  `"Team 2"`), not the bare template name — keeps names unique when a template has
  `count.max > 1` and matches `game-rooms.md` FR-TEAM's `{name} N` display rule.
  Added a "Roster and team-name resolution" note to the orchestration protocol spec
  (Orchestration populates it when building `CreateSessionRequest`); aligned the proto
  comment and both `backend-gdk-api.md` mentions. `buf lint` clean.
- **NFR-COMPAT-001 pre-release carve-out made official** in
  `game-development-experience.md`: the same-major-version backward-compat guarantee is
  effective **from v1.0.0**; during 0.x the API may break without a major bump. This
  was previously stated only in the GDK specs.
- **FE bootstrap contract** (`window.__TURNBASE__`) — confirmed it is already the
  authoritative definition in `frontend-gdk-api.md §9` and that the test harness must
  satisfy it too. It cannot be *closed* until the platform-frontend shell spec is
  written, so it remains a tracked dependency (see Next Priorities).

**Files changed:**
- `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` — added team-name resolution note
- `docs/specs/internal-grpc/gamehost.proto` — clarified `Team.name` comment (instance display name)
- `docs/specs/gdk-api/backend-gdk-api.md` — aligned `Team.name()` wording (§6 and §10)
- `docs/requirements/game-development-experience.md` — NFR-COMPAT-001 pre-1.0 carve-out

---

## Next Priorities

- **Remaining GDK-adjacent specs not yet written** (requirements done; specs missing):
  - **Manifest schema** (FR-MANIFEST-*) — single source of truth; referenced by upload
    pipeline, bundle format, team templates, GDK version compat. Recommended next; unblocks the others.
  - **Game bundle format + upload pipeline** (FR-BUNDLE-*, FR-UPLOAD-*) — depends on manifest schema.
  - **Test harness** (FR-HARNESS-*) — has open distribution questions (OQ-001/002) to resolve first.
- **Platform-frontend shell spec** (not yet written) — must inject and honor the FE
  bootstrap contract `window.__TURNBASE__ = { parentOrigin, sessionId }` (CON-006),
  authoritatively defined in `frontend-gdk-api.md §9`.
- **GDK spec open questions** to revisit when real games exercise them: generic action payloads & enum-typed parameters (backend); reconnection re-init and multi-listener events (frontend).

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
