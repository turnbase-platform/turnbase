# Requirements Gaps — Pre-Implementation TODO

## Critical (block implementation)

- [x] Fix version inconsistencies across all requirements docs (React 18→19, Java 25→21, Spring Boot 4→3.5+, GraalVM 25→CE 23)
- [x] Specify room WebSocket protocol — message envelope/format for lobby real-time events (readiness, parameters, player join/leave); defined in `docs/specs/api-design/room-websocket.md` and `docs/specs/api-design/room-chat-websocket.md`
- [x] Specify API design conventions — HTTP error response format, validation error schema, API versioning strategy, general rate limiting policy; defined in `docs/specs/api-design/`
- [x] Specify client-side token storage — httpOnly, Secure, SameSite=Strict cookie; added to `user-accounts.md` CON-004
- [x] Add OAuth callback route and view to `platform-views.md` — added `/auth/callback` and `/auth/complete-registration`

## Significant (important, workable with assumptions)

- [x] Add invite link route to `platform-views.md` — added `/rooms/join/:code`
- [x] Add in-room chat UI elements to Room Lobby and Room In Progress views in `platform-views.md`; add reconnection pinned card to Active Rooms view
- [x] Define at minimum the MVP scope for admin tooling — defined in `admin-tooling.md`: internal-only HTTP port, basic auth, game review queue (approve/reject), Official/Verified/Unverified badge model, private game behaviour
- [x] Specify background job operational model — added `FR-JOB-001–005` to `platform-operations.md` (ShedLock, Spring Scheduler, failure handling, observability)
- [x] Define the gRPC service contract (proto file) for Orchestration ↔ Game Host communication — defined in `docs/specs/internal-grpc/` (`gamehost.proto` + `orchestration-gamehost-protocol.md`)
- [x] Define "blocked slot" used in `game-rooms.md` FR-JOIN-006 — added to Definitions; AI slots blocked permanently, grace-period slots temporarily blocked

## Open Questions Requiring Decisions

- [ ] `game-contracts.md` OQ-001 / `game-development-experience.md` OQ-004 — Log color annotation syntax (blocks GDK API spec)
- [ ] `reconnection-flow.md` OQ — Game engine response set after `player_lost` event (replace with AI, forfeit, continue, etc.)
- [ ] `game-contracts.md` OQ-003 — Platform-managed timer mechanism; current design has no way to trigger timed game events without a player action
- [ ] `platform-architecture.md` OQ-001 — Truffle context memory overhead; needs prototype benchmark to set production scale-out thresholds
- [ ] `platform-architecture.md` OQ-003 — Scale-in session draining mechanism (wait for natural completion vs. active migration)
- [ ] `platform-ui-library.md` OQ-001–004 — Exact border radius, neon accent color values, WCAG contrast decision, backdrop-filter fallback
- [ ] `admin-tooling.md` OQ-001 — Can a developer resubmit a rejected game for another review attempt, or is rejection terminal?
- [ ] `admin-tooling.md` OQ-002 — Can an operator delist a Verified or Official game after it has gone public?

## Minor Cleanup

- [x] Add terminology note to `platform-architecture.md` clarifying "Orchestration Service" = domain within Platform Monolith
- [x] Reconcile CLAUDE.md project overview — removed "leaderboards" from feature list
