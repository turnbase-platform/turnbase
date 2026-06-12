# Reconnection Flow Requirements

## Stakeholders

| Role | Description |
|------|-------------|
| Player | Authenticated user (guest or registered) who disconnects from an in-progress game |
| Host | Player who also holds the host role; subject to immediate host transfer on disconnect |
| Room Participants | Other players and spectators present when a disconnect occurs |
| Platform | Detects disconnection, manages grace period and slot reservation, emits events |
| Game Engine | Receives notification only after the grace period expires; decides how to handle the loss |

---

## Definitions

| Term | Meaning |
|------|---------|
| **Disconnect** | Any loss of the player's WebSocket connection to the room, regardless of cause (browser close, network drop, voluntary leave). No distinction is made between voluntary and involuntary. |
| **Grace Period** | A platform-managed window (default 60 seconds) during which a disconnected player's slot is reserved and the game engine is not notified. |
| **Pinned Card** | A persistent UI element shown above the room list on the Active Rooms view, pointing the player back to the room they still hold a slot in. |

---

## Functional Requirements

### Disconnection Detection

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-DC-001 | Disconnect trigger | A disconnect is registered when a player's WebSocket connection to the room is lost. No distinction is made between voluntary (tab close, navigate away) and involuntary (network drop) causes. | Must |
| FR-DC-002 | Scope — In Progress only | The grace period and slot reservation mechanic applies only to rooms in **In Progress** state. A disconnect in Lobby state is treated as an immediate leave with no slot reservation. | Must |
| FR-DC-003 | Scope — Spectators | Spectators are dropped immediately on disconnect. No slot is reserved and no grace period is issued. Spectators may re-join freely subject to spectator capacity limits. | Must |
| FR-DC-004 | Scope — Post-game state | When a game ends, the room is already in Lobby state (game-rooms.md FR-LIFE-002). The post-game results view is a client-side UI overlay on the Lobby state (game-rooms.md FR-LIFE-003), not a distinct server-side state. A disconnect while the results overlay is visible is therefore a Lobby disconnect and follows FR-DC-002. | Must |

### Grace Period

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-GRACE-001 | Slot reservation | When a player disconnects from an In Progress room, their slot is reserved for the duration of the grace period. No other player may occupy that slot while it is reserved. | Must |
| FR-GRACE-002 | Grace period duration | The default grace period is 60 seconds from the moment of disconnect. The duration is configurable at the platform level. | Must |
| FR-GRACE-003 | Game engine isolation | The game engine is not notified during the grace period. From the game engine's perspective, the player is still present until the grace period expires or a kick is issued. | Must |
| FR-GRACE-004 | Participant alert | When a player disconnects, the platform emits a disconnect event to all other participants in the room. The event payload includes the grace period duration (in seconds). Clients render an alert stating that the player has disconnected and display the grace period duration from the event payload. The exact duration of the grace period is defined in FR-GRACE-002. | Must |

### Reconnection Entry Points

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-REJOIN-001 | Transient alert | A transient alert is displayed to the disconnected player (if they still have an active session on any tab/device) indicating they are still in a room and can rejoin. The alert includes a Rejoin button and auto-dismisses after approximately 5 seconds. | Must |
| FR-REJOIN-002 | Pinned card | After the transient alert dismisses, a pinned card is shown at the top of the Active Rooms view (`/rooms`) for as long as the player holds a reserved slot. The card shows the room identifier and a Rejoin button. It is removed when the player rejoins, the grace period expires, or the room closes. | Must |
| FR-REJOIN-003 | Direct URL | A player may also navigate directly to the room URL to trigger reconnection. | Must |

### Re-entry Flow

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-REJOIN-004 | Reconnection within grace period | If a player navigates to the room (via URL or Rejoin button) while their slot is still reserved, they are returned to the game immediately with no confirmation prompt. | Must |
| FR-REJOIN-005 | No intermediate screen | Re-entry during the grace period requires no confirmation step — the act of navigating to the room or clicking Rejoin is sufficient expression of intent. | Must |
| FR-REJOIN-006 | Reconnection after grace period | If the grace period has expired and the slot is no longer reserved, the player enters the standard late-join flow. Slot availability depends on whether the game supports late joins and whether a slot remains open. | Must |

### Grace Period Expiry

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-EXPIRY-001 | Slot release | When the grace period expires without the player reconnecting, the reserved slot is released. | Must |
| FR-EXPIRY-002 | Game engine notification | Upon grace period expiry, the platform sends a "player lost" event to the game engine. The game engine is responsible for deciding the outcome (e.g. replace with AI, continue without the player, forfeit the game). The standardized response set is defined in the Game SDK contracts document. | Must |
| FR-EXPIRY-003 | Pinned card removal | When the grace period expires, the pinned card (FR-REJOIN-002) is removed from the player's Active Rooms view. | Must |

### Kicking

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-KICK-001 | Kick in lobby | The host may kick any human player from the room while in Lobby state. The platform removes the player from the room immediately. | Must |
| FR-KICK-002 | Kick in progress | The host may kick any human player from an in-progress game. The platform sends a "player disconnected" event to the game engine with reason `kicked`. No grace period is issued. | Must |
| FR-KICK-003 | Kick during grace period | If a player is currently in their grace window when kicked, the grace period is voided immediately. The platform sends the "player disconnected" event with reason `kicked` to the game engine. | Must |
| FR-KICK-004 | Kick extends FR-HOST-006 | This requirement extends FR-HOST-006 from game-rooms.md, which already grants the host kick authority at all lifecycle stages. FR-KICK-001–003 define the mechanics specific to the reconnection flow and in-progress state. | Must |

### Host Disconnection

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-HDISC-001 | Immediate host transfer | When the host disconnects, host role transfers immediately to the next human player by join order (per FR-XFER-001). Host transfer does not wait for the grace period to elapse. | Must |
| FR-HDISC-002 | Disconnected host may reconnect | The former host's slot is still reserved for the standard grace period. If they reconnect, they return as a regular player — the transferred host role is not reclaimed. | Must |

---

## Non-Functional Requirements

| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-CONF-001 | Configurability | Grace period duration is configurable at the platform level without code changes | Default: 60s | Must |
| NFR-PERF-001 | Performance | Participant alert delivered on disconnect | < 500ms p95 | Should |
| NFR-PERF-002 | Performance | Reconnecting player resumes game view after re-entry | < 1s p95 | Should |

---

## Constraints

| ID | Description |
|----|-------------|
| CON-001 | Disconnect detection is WebSocket-based |
| CON-002 | The game engine is not contacted during the grace period — platform manages the window entirely |
| CON-003 | The standardized game engine response set (post-expiry actions) is defined in the Game SDK contracts document, not here |

---

## Out of Scope

- Game engine decision logic (forfeit, AI replacement, continue) — SDK contracts doc
- Spectator reconnection (spectators are dropped and re-join freely)
- Email or push notification of disconnection events
- Cross-device session handoff

---

## Open Questions

- **Game engine response set**: The full contract of what the game engine may respond with after receiving a "player lost" event (replace with AI, forfeit, continue without player, etc.) is deferred to the Game SDK contracts document.
