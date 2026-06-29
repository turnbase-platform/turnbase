## Last Session Summary

**Date:** 2026-06-29

Wrote the implementation-level specs for the **public GDK API** — both the Java
backend surface (`TurnBaseGame`, lifecycle hooks, effect/input types) and the
TypeScript frontend surface (`TurnBaseClient`, event callbacks, `sendAction`).

**Backend key decisions:**
- `TurnBaseGame<S extends GameState>` — single type param; action type supplied per call via `ActionContext.action(Class<A>)`
- State is a **method parameter + return value** on every hook except `onInit`; never on the context, never on the gRPC wire
- `Effect` is a **sealed interface** (one record per type), constructed only via the static `Effects` factory — gives the GDK Host an exhaustive proto mapping
- Per-hook result types (`InitResult`…`PlayerLeftResult`) with a shared fluent builder; `onPlayerJoined` is a `default` no-op (minimal game = 3 methods)
- **Proto amended:** added `string name = 3` to the gRPC `Team` message to back `Team.name()` (FR-GDK-011); `buf lint` clean
- Rich log color syntax stays **deferred** (game-contracts.md OQ-001); only basic Markdown in scope
- API is **pre-release** — breaking changes acceptable; NFR-COMPAT-001 backward-compat not yet in force

**Frontend key decisions:**
- `TurnBaseClient<TAction, TEvent>` — class-level generics, one replaceable handler per event, explicit `start()` drives the ready handshake
- **Shell-injected bootstrap global** (`window.__TURNBASE__ = { parentOrigin, sessionId }`) supplies the trusted origin — never inferred from message traffic; rich init context arrives as the first `init` postMessage
- **Spectators** handled in one `onInit` via `role: 'player' | 'spectator'` + nullable `self`
- Origin validation requires `event.origin === parentOrigin` **and** `event.source === window.parent`; outbound posts never `'*'`-targeted
- Defined a **bootstrap contract** the future platform-frontend shell spec must honor

**Files changed:**
- `docs/specs/gdk-api/backend-gdk-api.md`, `frontend-gdk-api.md` — new specs
- `docs/specs/gdk-api/INDEX.md` — new subdirectory index (both files registered)
- `docs/specs/INDEX.md` — registered `gdk-api/`
- `docs/specs/internal-grpc/gamehost.proto` — added `Team.name` field
- `docs/requirements/game-development-experience.md`, `game-contracts.md` — linked both specs

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
