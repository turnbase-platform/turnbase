# Game Rooms Requirements

## Related API Specifications

- [rest-conventions.md](../specs/api-design/rest-conventions.md) — HTTP methods, status codes, authentication rules
- [room-rest-api.md](../specs/api-design/room-rest-api.md) — the room membership REST surface: create, list, get, join, leave, invite-code resolution (implements FR-CREATE-*, FR-JOIN-001–007, FR-LIST-*)
- [pagination-filtering-sorting.md](../specs/api-design/pagination-filtering-sorting.md) — Room list pagination, filtering, and sorting conventions (implements FR-LIST-003–004)
- [websocket.md](../specs/api-design/websocket.md) — STOMP topics for lobby and game real-time events
- [room-websocket.md](../specs/api-design/room-websocket.md) — Room WebSocket event and command catalogue: room affinity, lobby events, team management, reconnection presence
- [input-validation.md](../specs/api-design/input-validation.md) — `CHANGE_PARAMETERS` (FR-HOST-007) is whitelist-validated against the game manifest's declared parameter schema: unknown keys, wrong types, and out-of-range values are rejected
- [rate-limiting.md](../specs/api-design/rate-limiting.md) — Tier 6 WebSocket frame budgets for member and host commands; `REQUEST_ROOM_STATE` is throttled separately as an expensive snapshot command
- [room-lifecycle.md](../specs/platform/room-lifecycle.md) — the durability mechanism behind FR-XFER-005 and FR-LIFE-007: room ownership and adoption, the session-detach algorithm, and the reconciliation sweeps
- [data-model.md](../specs/platform/data-model.md) — the relational schema for rooms, participants and teams, including the team instantiation of FR-TEAM-012

## Stakeholders

| Role | Description |
|------|-------------|
| Player | Authenticated user browsing, creating, or joining rooms |
| Host | Player who created the room; manages configuration, slots, readiness, and game start |
| Spectator | Player observing a full or in-progress game; no gameplay role |
| AI Player | System-controlled slot occupant; not a real user |

---

## Definitions

| Term | Meaning |
|------|---------|
| **Blocked Slot** | A player slot unavailable for a late-joining human player. A slot is blocked if it is occupied by an AI player — no GDK mechanism exists for an AI to yield its slot (the AI player interface is deferred to a future specification). During a session, a grace-period reserved slot (`reconnection-flow.md`) is also blocked; it becomes available for late joining only if the disconnected player does not reconnect before the grace period expires. |

---

## Functional Requirements

### Room List

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-LIST-001 | Display room list | Show a paginated list of rooms the current player may join or spectate. A room is included if: it has an available player slot (in Lobby state, or in In Progress state when the game supports mid-game joins), or it is full or In Progress without late-join support but spectating is enabled and a spectator slot is available. Rooms the player cannot access (visibility-restricted, full with no spectating, In Progress with no late-join and no spectating) are excluded. | Must |
| FR-LIST-002 | Room list fields | Each entry shows: Game name, Host username, Player count (current/max, human + AI combined), Min players, Max players, Room status (Lobby / In Progress), Join button, Spectate button (visible only if the game supports spectating). Min and max player counts are stored server-side for efficient filtering; they are derived from the game's team templates as the sum of `size.min × count.min` and `size.max × count.max` respectively across all templates. | Must |
| FR-LIST-003 | Filter and sort | Text search filters by game name and host name simultaneously (case-insensitive substring match, server-side). Per-column filters are available for room status (multi-select: Lobby, In Progress) and player count (range). Sorting is available for: game name, min players, max players, player count, room status. | Must |
| FR-LIST-003a | Join and Spectate actions | Each row provides a Join button and a Spectate button. The Join button is enabled when a player slot is available and, if the room is In Progress, the game supports mid-game joins; otherwise it is hidden. The Spectate button is visible only when the room supports spectating; it is enabled when a spectator slot is available. Button state is pre-computed server-side. If the room state changes between list load and the join/spectate attempt, the operation fails with an alert and the list is refreshed automatically. | Must |
| FR-LIST-004 | Pagination | List is paginated with configurable page size. Total room count and total page count are shown. | Must |
| FR-LIST-005 | Manual refresh | Player refreshes the list via an explicit control. No automatic polling. | Must |
| FR-LIST-006 | Friends Only visibility | "Friends Only" rooms appear only to players who are friends with the host. | Must |
| FR-LIST-007 | Invite Only visibility | "Invite Only" rooms do not appear in the list for any player. | Must |

### Room Joining

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-JOIN-001 | Join public room | Player can join any Public room with an available slot. | Must |
| FR-JOIN-002 | Join Friends Only room | Player can join a Friends Only room if they are friends with the host and a slot is available. | Must |
| FR-JOIN-003 | Join via invite link | Any player with a valid invite link or identifier can join the room regardless of its visibility, subject to slot availability. | Must |
| FR-JOIN-004 | Invite link validity | A link is invalid when: the room no longer exists, or the game has started and the player cannot join (no available slot and spectating is unavailable). If the player can join as spectator only, they are presented that option. | Must |
| FR-JOIN-005 | Join as spectator | If a room is full but spectating is enabled (game supports it and host allowed it), the player may join as a spectator, up to the platform spectator capacity limit. | Must |
| FR-JOIN-006 | Late-join as player | If a game is in progress, the game supports mid-game joins, and an unoccupied non-blocked slot existed at game start (see Definitions — Blocked Slot), the player may join as a player. If spectating is also available, two distinct actions are presented: join as player and join as spectator. A grace-period reserved slot that becomes unblocked mid-session is also available for late joining at that point. | Should |
| FR-JOIN-007 | Single room constraint | A player occupies only one room at a time. Joining a new room removes them from their current one. If the player currently holds a grace-period reserved slot in another In Progress room (reconnection-flow.md), joining or creating a new room voids that reservation immediately (early expiry per reconnection-flow.md FR-EXPIRY-004): the old slot is released and the game engine is notified. The single-room constraint takes precedence over an outstanding slot reservation. | Must |
| FR-JOIN-008 | Abandonment prompt — active game | A player in an active game must confirm before leaving to join another room. | Must |
| FR-JOIN-009 | Abandonment prompt — ready in lobby | A player who has declared readiness in a lobby must confirm before leaving. | Must |
| FR-JOIN-010 | No prompt — unready lobby | No confirmation is required when leaving a lobby where the player has not declared readiness. | Must |
| FR-JOIN-011 | Reconnection notification | If a player was disconnected from a room they can re-enter, the platform displays a transient alert with options to rejoin or dismiss, followed by a pinned card on the Active Rooms view. Full reconnection flow is described in reconnection-flow.md. | Must |

### Room Creation

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-CREATE-001 | Create room | A player initiates room creation by selecting a game, a visibility level, and — if the game supports spectating — whether spectating is allowed in this room. | Must |
| FR-CREATE-002 | Visibility levels | Supported levels: Public, Friends Only, Invite Only. | Must |
| FR-CREATE-003 | Auto host join | On confirmation, the player becomes the host and is placed in the room automatically. The room's initial teams are instantiated per FR-TEAM-012 before the host is auto-assigned to a team (FR-TEAM-005). | Must |
| FR-CREATE-004 | Game lock | The game cannot be changed after room creation. The host must leave and create a new room to switch games. | Must |

### Host Management

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-HOST-001 | Invite friends | Host can invite friends via the platform notification system. Invitees receive a notification and may accept, decline, or ignore it. Accepting abandons their current room or game (per FR-JOIN-008–010). | Must |
| FR-HOST-002 | Share invite link | Host can share a single, reusable room invite link or identifier. The same link is used for all invitees. All visibility types support this. | Must |
| FR-HOST-003 | Add AI players | If the game supports AI players, the host can add AI-controlled players to fill available slots. **Deferred to post-MVP** with the AI player interface (`game-contracts.md` OQ-002); no v1 game declares AI support, so `ADD_AI_PLAYER` returns `AI_NOT_SUPPORTED` unconditionally (`../specs/api-design/room-websocket.md`). | Should |
| FR-HOST-006 | Kick players | Host can remove any human or AI player at any point in the room lifecycle — including during an active game or during post-game results viewing. | Must |
| FR-HOST-007 | Configure game parameters | If the game exposes configurable parameters, the host can modify them in the lobby. Changes are visible in real-time to all players. Other players observe only — they cannot modify parameters. | Should |
| FR-HOST-008 | Parameters preserved on rematch | Game parameters are retained when the room returns to Lobby state after a game ends. | Should |
| FR-HOST-009 | Start game | Host can start the game when all team validity conditions in FR-TEAM-009 are met. | Must |

### Team Management

A game declares a `teamTemplates` array as part of its capability metadata. Each entry describes one *type* of team:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Conditional | Display name for teams of this type. Required when multiple templates are declared. Optional for a single template; defaults to `"Team"`. |
| `size.min` | integer ≥ 1 | Yes | Minimum number of players per team of this type |
| `size.max` | integer ≥ min | Yes | Maximum number of players per team of this type |
| `count.min` | integer ≥ 1 | Yes | Minimum number of teams of this type required to start |
| `count.max` | integer ≥ min | Yes | Maximum number of teams of this type allowed |

Teams are displayed as `{name} N` (e.g. "Attacker 1", "Defender 1", "Team 1", "Team 2"). For a single-template game where `name` is omitted, the platform renders teams as "Team 1", "Team 2", etc.

| Game type | Example template declaration |
|-----------|------------------------------|
| 1v1 | `[{ size:{1,1}, count:{2,2} }]` |
| 2v2–4v4 symmetric | `[{ size:{2,4}, count:{2,2} }]` |
| 1 vs 3 asymmetric | `[{ name:"Attacker", size:{1,1}, count:{1,1} }, { name:"Defender", size:{3,3}, count:{1,1} }]` |
| Free-for-all (2–6) | `[{ size:{1,1}, count:{2,6} }]` |

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-TEAM-001 | Lobby team display | The lobby displays all currently instantiated teams, each with its configured size, current members, and available slots. | Must |
| FR-TEAM-002 | Host adds team | Host can add a new team instance for a template, choosing a configured size within `[size.min, size.max]`, provided the current count for that template is below `count.max`. | Must |
| FR-TEAM-003 | Host removes team | Host can remove a team instance only if it currently has no players. To remove a non-empty team the host must first move or kick its players. | Must |
| FR-TEAM-004 | Host resizes team | Host can tune the number of slots in any team by increasing or decreasing its configured size within the template's `[size.min, size.max]` range. Increasing opens new slots immediately. Decreasing is blocked if the team's current player count would exceed the new size. | Should |
| FR-TEAM-005 | Auto-assignment on join | When a player joins, the platform auto-assigns them to the team with the fewest current members. Ties are broken by template order, then team index. | Must |
| FR-TEAM-006 | Host manual reassignment | Host can move any player (human or AI) to any team with an available slot at any time while in Lobby state. | Must |
| FR-TEAM-007 | Readiness reset on reassignment | When the host moves a player to a different team, that player's readiness is reset. All other players' readiness is unaffected. | Must |
| FR-TEAM-008 | AI player team assignment | When the host adds an AI player, they designate which team the AI occupies. AI players are subject to the same slot constraints as humans. **Deferred to post-MVP** with the AI player interface (`game-contracts.md` OQ-002); no v1 game declares AI support. | Should |
| FR-TEAM-009 | Team-valid start condition | The host can start the game only when all of the following hold: (a) each template's instantiated team count is within `[count.min, count.max]`; (b) each team's player count is within its template's `[size.min, size.max]`; (c) all human non-host players are ready. The start control is disabled and displays the unmet condition(s) until all are satisfied. | Must |
| FR-TEAM-010 | Structural change blocked when over capacity | Any operation that would reduce total team capacity below the current player count is rejected. The host must kick players before shrinking. | Must |
| FR-TEAM-011 | Mid-game join team assignment | When a player joins a game in progress (FR-JOIN-006), the platform auto-assigns them to the team with the fewest current human players, subject to the template's `size.max` constraint. Ties are broken by template order, then team index. This mirrors the lobby assignment algorithm (FR-TEAM-005) applied to the current in-progress team state. The assigned team ID is included in the `player_joined` input sent to the game BE (game-contracts.md FR-IN-004). | Should |
| FR-TEAM-012 | Initial team instantiation | On room creation, before the host is auto-assigned, the platform instantiates `count.min` team instances for **each** declared template, each with `configuredSize = size.max`. The host is then auto-assigned per FR-TEAM-005; because all teams are empty at t=0, the host occupies the first team of the first declared template. The room's initial player capacity is therefore `Σ (size.max × count.min)` across all templates. The advertised min/max player counts (FR-LIST-002) are the template-derived bounds and are independent of the current instantiation. The host may subsequently add, remove, or resize teams (FR-TEAM-002/003/004). | Must |

### Player Readiness

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-READY-001 | Declare readiness | All human non-host players in the lobby must declare readiness before the game can be started. The host does not declare readiness separately — clicking Start Game serves as their implicit confirmation. | Must |
| FR-READY-002 | AI readiness | AI players are always considered ready. | Must |
| FR-READY-003 | Toggle readiness | A player may toggle their readiness on or off at any time before the host starts the game. | Must |
| FR-READY-004 | Readiness reset | All readiness is reset when the room returns to Lobby state after a game ends. | Must |

### Host Transfer & Room Closure

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-XFER-001 | Automatic host transfer | If the host leaves or disconnects, host role transfers to the next human player by join order. Host role is never transferred to a spectator. The host is always a player; a host cannot switch to spectator role. | Must |
| FR-XFER-002 | Room closure — no players | If the host leaves and no other human players remain, the room is immediately and permanently closed. Any spectators present are evicted. Spectators do not count toward room viability. This immediate closure applies in **Lobby** state and to **explicit** host departures in any state (confirmed voluntary leave per FR-LIFE-004, account deletion) — that is, to an *individual* player's leave or disconnect. An **involuntary** host disconnect during **In Progress** that leaves no other connected human does **not** close the room immediately; it is handled by the grace-period deferral in reconnection-flow.md FR-HDISC-003, closing only if the grace period expires. The Lobby-state immediate closure likewise does **not** apply when the disconnect is a mass owner-pod-loss event (reconnection-flow.md FR-DC-006): FR-DC-007 excludes owner-pod loss from "immediate leave" in every room state, precisely so that a rolling deploy — which disconnects every participant of every Lobby room at once — does not read as every host leaving and close them all. | Must |
| FR-XFER-003 | Closed room inaccessible | A closed room cannot be joined, found via invite link, or appear in any listing. | Must |
| FR-XFER-004 | Voluntary host transfer | The host may transfer their host role to any other human player in the room at any time, in both Lobby and In Progress states. The former host retains their player slot and remains in the room as a regular player. | Must |
| FR-XFER-005 | Session teardown on closure | Closing a room that has a live game session must tear that session down. The room-state change and a **durable record that the teardown is owed** are committed together; the teardown itself is then attempted best-effort and bounded, and its failure never blocks or reverses the closure. An owed teardown that does not complete is re-driven by `platform-operations.md` FR-JOB-007 until it does. The same mechanism covers the ordinary end of a game, where the room returns to Lobby rather than closing (FR-LIFE-002) but the session is still torn down. Rationale and rejected orderings: [ADR-0010](../decisions/0010-session-teardown-ordering.md). | Must |

### Room Lifecycle

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-LIFE-001 | Room states | A room is in one of three states: Lobby, In Progress, Closed. | Must |
| FR-LIFE-002 | Post-game lobby transition | When a game ends, the room immediately transitions to Lobby state on the server and all readiness is reset. The game's UI component is responsible for displaying results — the platform does not define a separate server-side post-game state. | Must |
| FR-LIFE-003 | Per-player results dismiss | While the room is in Lobby state after a game ends, each player's client still renders the game iframe (which shows results). A dismiss control is presented by the platform (e.g. a button or overlay) allowing the player to exit the game UI and return to the lobby view. This is a client-side transition only — no server round-trip is required. Because no player is ready by default, the next game cannot start until all players confirm readiness. | Must |
| FR-LIFE-004 | Voluntary departure | Any non-host participant (player or spectator) may leave the room at any time, subject to abandonment prompts (FR-JOIN-008–010). A **confirmed** voluntary departure (explicit "Leave Room", an abandonment confirmation when joining/creating another room, or account deletion) is an immediate leave: during In Progress the platform emits `PLAYER_LEFT`, releases the slot with **no** grace period or reservation, and notifies the game engine at once (reason `left`). This is distinct from an involuntary disconnect, which reserves the slot for the grace period (reconnection-flow.md FR-DC-005). A bare loss of the WebSocket — including tab or browser close — is **not** a voluntary departure; it is an involuntary disconnect. | Must |
| FR-LIFE-005 | Player switches to spectator | A non-host player in Lobby state may voluntarily switch to spectator role, provided the room supports spectating and a spectator slot is available. Switching vacates the player's team slot and clears their readiness. This action is not available during In Progress. | Must |
| FR-LIFE-006 | Spectator switches to player | A spectator in Lobby state may switch to player role if a player slot is available. They are auto-assigned to a team as if joining fresh (FR-TEAM-005). The host may subsequently reassign them (FR-TEAM-006). This action is not available during In Progress. | Must |
| FR-LIFE-007 | Platform-initiated closure | A room may be closed by the platform with no host action, in two cases: it has sat in Lobby with no connected participant past the configured idle window, or its game session is unrecoverable (`platform-operations.md` FR-JOB-007). The closure reason is surfaced to any participant still attached, and the room becomes inaccessible per FR-XFER-003. FR-XFER-002 remains the ordinary path; this requirement is its safety net for rooms that no participant ever returns to. | Must |

---

## Non-Functional Requirements

| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-PERF-001 | Performance | Room list initial load | < 500ms p95 | Should |
| NFR-PERF-002 | Performance | Real-time lobby updates (parameters, readiness, player events) delivered to all participants | < 300ms p95 end-to-end | Should |
| NFR-SEC-001 | Security | Visibility and access rules enforced server-side on every join attempt | No client-side trust | Must |
| NFR-SEC-002 | Security | Invite link identifiers are cryptographically random and not sequentially enumerable | — | Must |
| NFR-USAB-001 | Usability | Pagination metadata includes: total items, total pages, current page, page size | — | Must |
| NFR-SPEC-001 | Scalability | Maximum spectators per room is configurable at the platform level; default is 8; hosts have no control over this limit. The key is `turnbase.room.spectator-capacity` (`local-environment.md` §7.1) | Default: 8 | Must |

---

## Constraints

| ID | Description |
|----|-------------|
| CON-001 | Real-time lobby communication (readiness, parameter changes, player join/leave) must use WebSockets — no polling |
| CON-002 | Backend: Java 21, Spring Boot 3.5+ |
| CON-003 | Frontend: React 19, TypeScript |
| CON-004 | Game capability metadata (spectator support, AI support, team templates, configurable parameters, mid-game join support) is defined and owned by the game itself. Min/max player counts are derived from team templates and stored by the platform for efficient filtering. |

---

## Out of Scope

- User authentication and session management
- Reconnection flow after disconnect (separate document)
- In-room chat and platform notification/messaging system (separate document)
- Game SDK and game engine contracts (separate document)
- Gameplay rendering and logic
- Post-game statistics and history
