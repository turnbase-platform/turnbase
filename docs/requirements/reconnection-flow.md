# Reconnection Flow Requirements

## Related API Specifications

- [websocket.md § Game Session Protocol](../specs/api-design/websocket.md#game-session-protocol) — how a reconnecting player is restored to an in-progress game (FR-REJOIN-004): the client re-subscribes and requests a sync, and the game backend composes that player's current view via the read-only `resync` input (game-contracts.md FR-IN-006). No effect history is replayed; the retained game log is delivered alongside the view.
- [room-websocket.md](../specs/api-design/room-websocket.md) — `PLAYER_DISCONNECTED` / `PLAYER_RECONNECTED` / `PLAYER_LOST` presence events, and the `ROOM_STATE` snapshot that carries in-flight grace timers (FR-GRACE-004).
- [room-lifecycle.md](../specs/platform/room-lifecycle.md) — the mechanism behind FR-GRACE-005/006 and FR-EXPIRY-005: persisted deadlines, the conditional transition that resolves a reservation exactly once, room adoption after owner-pod loss, and the sweeps that drive them.
- [ADR-0008](../decisions/0008-room-ownership-lifecycle.md) — room ownership as a lease-gated claim; the source of FR-DC-006/007 and FR-HDISC-004.
- [ADR-0009](../decisions/0009-grace-deadline-durability.md) — why deadlines are persisted absolute timestamps fired by a sweep rather than in-process timers.

## Stakeholders

| Role | Description |
|------|-------------|
| Player | Authenticated user (guest or registered) who disconnects from an in-progress game |
| Host | Player who also holds the host role; on disconnect, host role transfers immediately if another human is connected, otherwise transfer and closure are deferred for the grace period (FR-HDISC-003) |
| Room Participants | Other players and spectators present when a disconnect occurs |
| Platform | Detects disconnection, distinguishes voluntary leave from involuntary disconnect, manages grace period and slot reservation, emits events |
| Game Engine | Not notified during the grace period of an involuntary disconnect; notified immediately on a voluntary leave (FR-DC-005) or kick (FR-KICK-002/003), and on grace-period expiry (FR-EXPIRY-002) |

---

## Definitions

| Term | Meaning |
|------|---------|
| **Disconnect (involuntary)** | A bare loss of the player's WebSocket connection to the room with no explicit in-app intent — network drop, crash, tab or browser close, navigating away. This is the event that triggers the grace period and slot reservation. Unqualified "disconnect" in this document means an involuntary disconnect. |
| **Voluntary Leave** | An **explicit, confirmed** in-app departure: clicking "Leave Room", confirming abandonment to join or create another room (game-rooms.md FR-JOIN-007/008), or deleting the account. A voluntary leave is processed immediately with **no** grace period and **no** slot reservation. The distinguishing signal is a deliberate user action, not merely the WebSocket closing. |
| **Grace Period** | A platform-managed window (default 60 seconds) during which an involuntarily disconnected player's slot is reserved and the game engine is not notified. |
| **Pinned Card** | A persistent UI element shown above the room list on the Active Rooms view, pointing the player back to the room they still hold a slot in. |
| **Owner-Pod Loss** | Loss of the Platform Monolith instance that owns a room — by crash or by graceful drain during a deploy. Every participant of that room is disconnected at once. Treated as a mass involuntary disconnect (FR-DC-006), never as a set of voluntary leaves. |
| **Migration Window** | A short interval after a room is adopted by a new owning instance (default 20s) during which host transfer is deferred, so a deploy does not reassign the host role to whoever reconnects first (FR-HDISC-004). |

---

## Functional Requirements

### Disconnection Detection

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-DC-001 | Disconnect trigger | An **involuntary** disconnect is registered when a player's WebSocket connection to the room is lost without an explicit in-app leave action. This includes network drop, crash, tab close, browser close, and navigating away — the platform cannot observe intent from a bare socket loss, so all such losses are treated as involuntary and receive the grace period (In Progress) per FR-GRACE-001. An explicit, confirmed departure is instead a voluntary leave (FR-DC-005), not a disconnect. | Must |
| FR-DC-002 | Scope — In Progress only | The grace period and slot reservation mechanic applies only to rooms in **In Progress** state. A disconnect in Lobby state is treated as an immediate leave with no slot reservation. | Must |
| FR-DC-003 | Scope — Spectators | Spectators are dropped immediately on disconnect. No slot is reserved and no grace period is issued. Spectators may re-join freely subject to spectator capacity limits. | Must |
| FR-DC-004 | Scope — Post-game state | When a game ends, the room is already in Lobby state (game-rooms.md FR-LIFE-002). The post-game results view is a client-side UI overlay on the Lobby state (game-rooms.md FR-LIFE-003), not a distinct server-side state. A disconnect while the results overlay is visible is therefore a Lobby disconnect and follows FR-DC-002. | Must |
| FR-DC-005 | Voluntary leave is immediate | A voluntary leave (Definitions) from an In Progress room is processed immediately, bypassing the grace period entirely: the platform removes the player, emits `PLAYER_LEFT` (distinct from the involuntary `PLAYER_DISCONNECTED`), releases the slot with no reservation, and notifies the game engine at once that the player has departed (reason `left`; the exact input event is defined in game-contracts.md). No pinned card or reconnection alert is issued, because no slot is held. This resolves the apparent conflict with the single-room and abandonment requirements (game-rooms.md FR-JOIN-007/008, FR-LIFE-004). | Must |
| FR-DC-006 | Owner-pod loss is a mass involuntary disconnect | When the Platform Monolith pod that owns a room is lost — crash, or a rolling deploy draining the pod — every connected participant of that room loses their WebSocket simultaneously. All such losses are **involuntary disconnects** (FR-DC-001) and receive the standard treatment for the room's state. Grace deadlines are established when the loss is *observed* — at adoption of the room by another pod, or by the reconciliation sweep — and an already-running deadline is **never reset**: a player 45 seconds into their grace period when the pod died does not receive a fresh window. Room ownership and adoption are specified in [ADR-0008](../decisions/0008-room-ownership-lifecycle.md). | Must |
| FR-DC-007 | Lobby carve-out for owner-pod loss | FR-DC-002's rule that a Lobby disconnect is an immediate leave applies only to an *individual* player's disconnect. A disconnect caused by owner-pod loss (FR-DC-006) is **never** treated as an immediate leave, in any room state. Without this carve-out, a rolling deploy would make every player of every Lobby room "leave", which makes the host's departure trigger room closure (game-rooms.md FR-XFER-002) — deleting every Lobby room on the platform on every deploy. Lobby rooms therefore survive owner-pod loss for the same window as In Progress rooms, and participants rejoin by reconnecting. | Must |

### Grace Period

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-GRACE-001 | Slot reservation | When a player disconnects from an In Progress room, their slot is reserved for the duration of the grace period. No other player may occupy that slot while it is reserved. | Must |
| FR-GRACE-002 | Grace period duration | The default grace period is 60 seconds from the moment of disconnect. The duration is configurable at the platform level. | Must |
| FR-GRACE-003 | Game engine isolation | The game engine is not notified during the grace period. From the game engine's perspective, the player is still present until the grace period expires or a kick is issued. | Must |
| FR-GRACE-004 | Participant alert | When a player disconnects, the platform emits a disconnect event to all other participants in the room. The event payload includes the grace period duration (in seconds). Clients render an alert stating that the player has disconnected and display the grace period duration from the event payload. The exact duration of the grace period is defined in FR-GRACE-002. | Must |
| FR-GRACE-005 | Deadlines are persisted and absolute | A grace period is recorded as an **absolute expiry timestamp persisted in the platform database** at the moment the disconnect is observed, not as an in-process timer. The deadline survives process restart, rolling deploy, and transfer of room ownership to another instance, and any instance can read it to report the remaining time. Expiry is enforced by the scheduled sweep in `platform-operations.md` FR-JOB-006. Rationale and rejected alternatives: [ADR-0009](../decisions/0009-grace-deadline-durability.md). | Must |
| FR-GRACE-006 | Connection counting and repeated disconnects | A player may hold several concurrent connections to the platform (`rate-limiting.md` caps this per user). The grace period opens when the **last** of that player's connections to the room closes, and ends when the **first** reconnects — closing one of several open tabs must not present a player as disconnected while they are still playing. Each disconnect starts a **fresh** window rather than resuming a previous one. A change to the configured grace duration (FR-GRACE-002) never moves a deadline that is already running. | Must |

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
| FR-REJOIN-007 | Losing the race to expiry | A reconnection attempt that arrives after the reservation has already been resolved (FR-EXPIRY-005) must be handled as a late join (FR-REJOIN-006) and told plainly that the slot was released — not failed with a generic error. This is an ordinary outcome of a player returning at the moment their window closes, not an error condition. | Must |
| FR-REJOIN-008 | Rejoining a room that no longer exists | If the room was closed while the player held a reservation — by grace expiry with no human connected (FR-HDISC-003), by the platform (`platform-operations.md` FR-JOB-007), or by any other closure path — the rejoin entry points must report the room as closed. The pinned card (FR-REJOIN-002) is removed on closure as well as on expiry. | Must |

### Grace Period Expiry

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-EXPIRY-001 | Slot release | When the grace period expires without the player reconnecting, the reserved slot is released. | Must |
| FR-EXPIRY-002 | Game engine notification | Upon grace period expiry, the platform sends a "player lost" event to the game engine. The game engine is responsible for deciding the outcome (e.g. replace with AI, continue without the player, forfeit the game). The standardized response set is defined in the Game SDK contracts document. | Must |
| FR-EXPIRY-003 | Pinned card removal | When the grace period expires, the pinned card (FR-REJOIN-002) is removed from the player's Active Rooms view. | Must |
| FR-EXPIRY-004 | Early release on joining another room | If a player who holds a reserved slot joins or creates another room (game-rooms.md FR-JOIN-007), the reservation is voided immediately rather than waiting for the timer: the slot is released and the game engine is notified exactly as on normal expiry (FR-EXPIRY-001/002), and the pinned card is removed (FR-EXPIRY-003). The one-room-at-a-time invariant takes precedence over the reservation. Because the player may be acting on an instance other than the one that owns the old room, the slot release and the game-engine notification are performed by the acting instance, while the `PLAYER_LOST` event is emitted by the room's owning instance when it next observes the release. | Must |
| FR-EXPIRY-005 | Resolution happens at most once | Expiry, reconnection, kick (FR-KICK-003) and early release (FR-EXPIRY-004) all compete to resolve the same reservation. Exactly one of them takes effect: resolution is a conditional state transition guarded on the reservation still being outstanding, and only the winner performs the associated side effects (slot release, participant events, pinned-card removal, room-closure evaluation). A loser is a no-op, never an error. The game-engine notification is delivered from a durable record so it survives a crash between the state change and the call; it is therefore at-least-once, and must be delivered in a form the game engine can recognise as a repeat, so that a redelivery changes nothing. | Must |
| FR-EXPIRY-006 | Game end resolves outstanding reservations | When a game ends, the room returns to Lobby (game-rooms.md FR-LIFE-002), where slot reservations have no meaning (FR-DC-002). Every reservation still outstanding at that moment is resolved immediately as a departure, with no game-engine notification — the session it referred to is over. | Must |

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
| FR-HDISC-001 | Immediate host transfer | When the host disconnects **and at least one other human player is currently connected**, host role transfers immediately to the next connected human player by join order (per FR-XFER-001). Host transfer does not wait for the grace period to elapse. If no other human is connected, FR-HDISC-003 applies instead. | Must |
| FR-HDISC-002 | Disconnected host may reconnect | The former host's slot is still reserved for the standard grace period. If they reconnect, they return as a regular player — the transferred host role is not reclaimed. | Must |
| FR-HDISC-003 | Last-connected-human host disconnect | When the host **involuntarily** disconnects from an **In Progress** room and no other human player is currently connected (e.g. a 1-player-vs-AI room, or all other humans are themselves in their own grace windows), host transfer and room closure are both **deferred**: the room and its game session are kept alive for the grace period. If the host reconnects within the window, they resume as host and play continues. If another human player reconnects within the window, the room becomes viable again and host role transfers to them (FR-XFER-001 / FR-HDISC-001). If the grace period expires with no human connected, the room is closed and the game session terminated (game-rooms.md FR-XFER-002/FR-XFER-003). This overrides the immediate-closure rule (game-rooms.md FR-XFER-002) for involuntary In Progress disconnects. **If the host's own reservation is resolved while another human's is still outstanding, the room is not closed — a human still holds a slot — and it is left with no host at all** until someone reconnects, at which point the role transfers to them by join order (FR-XFER-001). The host role is never held by a released participant. | Must |
| FR-HDISC-004 | Migration window after owner-pod loss | Following an owner-pod loss (FR-DC-006), host transfer is deferred for a configurable **migration window** (default 20 seconds) after the room is adopted. If the original host reconnects within the window they retain the host role. Without this, every rolling deploy would hand the host role to whichever participant reconnects fastest, because FR-HDISC-001 sees a disconnected host and an available human. FR-HDISC-001's immediate transfer applies to *individual* host disconnects, not to mass disconnects. The window is a **persisted absolute deadline**, not an in-process timer — it exists to survive the loss of an instance, so holding it in that instance's memory would void it during the very event it covers — and its expiry is acted on by the sweep (`platform-operations.md` FR-JOB-006), which performs the deferred transfer. Deferral alone is not enough: something must also *end* the deferral, or a host who never returns leaves the room with no host at all. | Must |

---

## Non-Functional Requirements

| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-CONF-001 | Configurability | Grace period duration is configurable at the platform level without code changes. A change never moves a deadline already running (FR-GRACE-006) | Default: 60s | Must |
| NFR-CONF-002 | Configurability | The migration window (FR-HDISC-004) is configurable at the platform level | Default: 20s | Must |
| NFR-CONF-003 | Deployment safety | The grace period must exceed the worst-case **cumulative** period during which a single room is unreachable or unclaimable across a full rolling deploy — the sum of per-instance unavailability, ownership reclaim latency, and client reconnect backoff. The player at risk is not one who reconnected between restarts (a reconnect clears the reservation, and a later disconnect starts a fresh window per FR-GRACE-006) but one who never managed to reconnect at all: their original absolute deadline runs straight through every outage. A *graceful* drain (`platform-operations.md` FR-DEPLOY-001) releases ownership and normally opens no grace windows, so this bound binds on **ungraceful** loss — drain timeout exceeded, OOM kill, SIGKILL | Grace period > cumulative per-room reconnect blackout | Must |
| NFR-PERF-003 | Performance | Grace expiry and deferred closure take effect no later than their persisted deadline plus one sweep interval (`platform-operations.md` FR-JOB-006), **for a room that has a live owner**. A room whose owning instance was lost is not swept until it is adopted; that delay is bounded separately by `platform-operations.md` NFR-JOB-002 and adds to this one. This is the FR-DC-006 case, so the two bounds must be read together whenever a deploy or crash is in scope | deadline + 5s p99 | Must |
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
