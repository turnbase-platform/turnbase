# Room WebSocket Protocol

## Overview

This specification defines the STOMP-over-WebSocket protocol for room lobby real-time events. It extends the base connection, authentication, and envelope established in [websocket.md](websocket.md) with the full room event catalogue, command catalogue, and the room affinity routing model.

**Scope:** room lifecycle, membership, team management, readiness, parameter changes, game start/end transitions, and reconnection presence events. In-room chat wire format is defined separately in [room-chat-websocket.md](room-chat-websocket.md). Game effect delivery during an active session is defined in [websocket.md](websocket.md) and [game-contracts.md](../../requirements/game-contracts.md).

## Related Documents

- [websocket.md](websocket.md) — base connection, authentication, envelope, and game event topics
- [room-chat-websocket.md](room-chat-websocket.md) — chat send/receive wire format
- [game-rooms.md](../../requirements/game-rooms.md) — room lifecycle, team management, and host control requirements
- [reconnection-flow.md](../../requirements/reconnection-flow.md) — grace period and reconnection requirements

---

## Room Affinity and WebSocket Routing

All real-time room events for a given room are produced by a single Platform Monolith pod — the pod that owns that room. Room ownership is assigned at room creation and stored in Redis (`room:{roomId}:pod → podId`). Ownership persists for the lifetime of the room.

### Routing on join

When a player joins or creates a room via the REST endpoint, the server sets a routing hint in the response (implementation detail: an HTTP cookie or header, e.g. `X-Room-Pod: {podId}`). The ingress layer uses this hint to route all subsequent requests from that client — including the WebSocket upgrade — to the owning pod.

The client establishes its WebSocket connection (`/ws`) **after** receiving the join or create response. Because the routing hint is set before the connection is opened, the WebSocket upgrade goes directly to the owning pod. No reconnection or migration is ever required at room entry.

### Consequences

- All subscribers to `/topic/room.{roomId}` are connected to the same pod.
- Per-room state mutations use a JVM-local `ReentrantLock` (keyed by room ID) — no distributed lock is required.
- Per-room version counters are in-JVM `AtomicLong` values — no Redis counter is required.
- `SimpMessagingTemplate.convertAndSend(...)` and `convertAndSendToUser(...)` always reach their targets locally.

### Pod failure

If the owning pod crashes, all users in its rooms lose their WebSocket connections simultaneously. Room state is persisted to the database on every mutation. Clients reconnect via the standard join flow (which assigns a new owning pod) and re-request a state snapshot.

---

## Destinations

The following destinations extend [websocket.md](websocket.md). The game-session destinations (`/topic/game.*`, `/user/queue/game`, `/app/game.*.action`, `/app/game.*.sync`) and `/user/queue/errors` are defined in [websocket.md](websocket.md) and are unchanged here.

| Destination | Direction | Authorized subscribers / senders | Purpose |
|---|---|---|---|
| `/topic/room.{roomId}` | server→client | Room players and spectators | All room lifecycle, membership, team, readiness, and presence events |
| `/topic/room.{roomId}.chat` | server→client | Room players only (not spectators) | Room-channel chat messages |
| `/topic/room.{roomId}.team.{teamId}` | server→client | Players assigned to that team | Team-channel chat messages |
| `/user/queue/room-state` | server→client | Individual user | Unicast `ROOM_STATE` snapshot in response to `REQUEST_ROOM_STATE` |
| `/app/room.{roomId}.member` | client→server | Room players and spectators | Member commands: readiness, role switch, snapshot request |
| `/app/room.{roomId}.host` | client→server | Current room host | Host commands: team management, kick, parameters, game start, host transfer |

Chat send (`/app/room.{roomId}.chat`) is defined in [room-chat-websocket.md](room-chat-websocket.md).

---

## Message Envelope

All messages extend the base `{ "type", "payload" }` envelope from [websocket.md](websocket.md).

**Server→client events** (all room topics):

```json
{
  "type": "PLAYER_JOINED",
  "version": 42,
  "payload": { ... }
}
```

`version` is a per-room monotonically increasing integer allocated under the room lock. It is incremented exactly once per state-mutating event. The `ROOM_STATE` snapshot and every subsequent delta carry this field. Error messages on `/user/queue/errors` do not carry `version`.

**Client→server commands** (`.member` and `.host` channels):

```json
{
  "type": "KICK_PLAYER",
  "correlationId": "c8f3a1b2-4e5d-...",
  "payload": { ... }
}
```

`correlationId` is a client-generated UUID echoed back in any error response for the originating command. Commands with no required payload may omit the `payload` field.

---

## Per-Room Serialization and Versioning

Every room state mutation — whether REST-originated (join, leave, create) or STOMP-originated (any command below) — acquires the room's `ReentrantLock` before reading or writing room state. The sequence inside the lock is:

1. Read current room state.
2. Validate preconditions (room state, role, capacity, business rules).
3. Apply the mutation.
4. Increment the room version counter.
5. Publish the delta event to `/topic/room.{roomId}` via the local broker.
6. Release the lock.

Publishing the event inside the lock (step 5) guarantees that no delta with a higher version can be queued before a lower-version delta. STOMP's per-destination FIFO order then delivers them in sequence. Clients can apply deltas strictly in version order without additional coordination.

The version counter is an in-JVM `AtomicLong` per room, initialised from the database when the room is assigned to this pod.

---

## Server→Client Event Catalogue

All events below are delivered on `/topic/room.{roomId}` and carry the `version` field. Spectators receive all events on this topic. Chat events are on separate topics (see [room-chat-websocket.md](room-chat-websocket.md)) and are not received by spectators.

---

### Membership and Lifecycle

#### `ROOM_STATE`

Full room state snapshot. Delivered unicast on `/user/queue/room-state` in response to a `REQUEST_ROOM_STATE` command. See [Snapshot Delivery](#snapshot-delivery) for the request/response flow.

```json
{
  "type": "ROOM_STATE",
  "version": 42,
  "payload": {
    "roomId": "uuid",
    "state": "LOBBY | IN_PROGRESS",
    "gameId": "uuid",
    "gameName": "string",
    "spectatingEnabled": true,
    "spectatorCapacity": 8,
    "hostId": "uuid",
    "players": [
      {
        "playerId": "uuid",
        "username": "string",
        "teamId": "uuid | null",
        "ready": false,
        "connected": true,
        "joinOrder": 1
      }
    ],
    "aiPlayers": [
      {
        "aiPlayerId": "uuid",
        "displayName": "string",
        "teamId": "uuid"
      }
    ],
    "spectators": [
      {
        "playerId": "uuid",
        "username": "string"
      }
    ],
    "teams": [
      {
        "teamId": "uuid",
        "templateName": "string",
        "configuredSize": 4,
        "index": 0,
        "memberIds": ["uuid"]
      }
    ],
    "parameters": {},
    "disconnectedPlayers": [
      {
        "playerId": "uuid",
        "graceRemainingSeconds": 45
      }
    ],
    "sessionId": "uuid | null"
  }
}
```

`sessionId` is non-null when `state == IN_PROGRESS`. `disconnectedPlayers` contains only players currently within an active grace period; it is empty when no player is disconnected. `teams[i].memberIds` contains all player IDs assigned to that team (human and AI); cross-reference with `aiPlayers` to determine AI status. Chat history is not included — per [in-room-chat.md](../../requirements/in-room-chat.md) FR-MSG-005, the platform does not persist chat messages.

#### `PLAYER_JOINED`

A human player or spectator has joined the room. Emitted after the REST join call completes and the participant is added to room state.

```json
{
  "type": "PLAYER_JOINED",
  "version": 43,
  "payload": {
    "playerId": "uuid",
    "username": "string",
    "role": "PLAYER | SPECTATOR",
    "teamId": "uuid | null",
    "joinOrder": 5
  }
}
```

`teamId` is null for spectators. For players it reflects the auto-assigned team (FR-TEAM-005 in game-rooms.md). `joinOrder` is a monotonically increasing integer used for host transfer ordering (FR-XFER-001).

#### `AI_PLAYER_ADDED`

Host added an AI-controlled player to a team (FR-HOST-003).

```json
{
  "type": "AI_PLAYER_ADDED",
  "version": 44,
  "payload": {
    "aiPlayerId": "uuid",
    "displayName": "string",
    "teamId": "uuid"
  }
}
```

#### `PLAYER_LEFT`

A player or spectator has voluntarily departed the room (FR-LIFE-004). Not emitted for kicks (see `PLAYER_KICKED`).

```json
{
  "type": "PLAYER_LEFT",
  "version": 45,
  "payload": {
    "playerId": "uuid",
    "role": "PLAYER | SPECTATOR"
  }
}
```

A disconnect in Lobby state is treated as an immediate leave (FR-DC-002 in reconnection-flow.md) and also emits `PLAYER_LEFT`.

#### `PLAYER_KICKED`

Host removed a player (human or AI) from the room (FR-HOST-006). Valid in any room state.

```json
{
  "type": "PLAYER_KICKED",
  "version": 46,
  "payload": {
    "playerId": "uuid",
    "byHostId": "uuid"
  }
}
```

The kicked player additionally receives a unicast notification on `/user/queue/errors`. This notification does not carry `version` and has no `correlationId` (it is not a response to a command):

```json
{
  "type": "ERROR",
  "payload": {
    "code": "KICKED",
    "message": "You were removed from the room by the host.",
    "roomId": "uuid"
  }
}
```

#### `PLAYER_ROLE_CHANGED`

A human player switched between player and spectator roles (FR-LIFE-005, FR-LIFE-006).

```json
{
  "type": "PLAYER_ROLE_CHANGED",
  "version": 47,
  "payload": {
    "playerId": "uuid",
    "newRole": "SPECTATOR | PLAYER",
    "teamId": "uuid | null",
    "readinessCleared": true
  }
}
```

`teamId` is the newly assigned team when `newRole == PLAYER` (auto-assigned per FR-TEAM-005), or null when `newRole == SPECTATOR`. `readinessCleared` is always true when switching to spectator.

#### `HOST_TRANSFERRED`

Host role has changed — voluntarily (FR-XFER-004), automatically on host departure (FR-XFER-001), or immediately on host disconnect (FR-HDISC-001 in reconnection-flow.md).

```json
{
  "type": "HOST_TRANSFERRED",
  "version": 48,
  "payload": {
    "newHostId": "uuid",
    "previousHostId": "uuid",
    "reason": "VOLUNTARY | HOST_LEFT | HOST_DISCONNECTED"
  }
}
```

#### `ROOM_CLOSED`

The room has been permanently closed (FR-XFER-002). Delivered to all current subscribers before the room is torn down.

```json
{
  "type": "ROOM_CLOSED",
  "version": 49,
  "payload": {
    "roomId": "uuid",
    "reason": "NO_PLAYERS_REMAINING"
  }
}
```

After receiving this event, clients should unsubscribe and navigate away. The room cannot be rejoined (FR-XFER-003).

---

### Game Lifecycle

#### `GAME_STARTED`

The host has started the game (FR-HOST-009). Clients transition to the game view and enter the game-session attach flow: subscribe to the game destinations, then request a sync. See [websocket.md § Game Session Protocol](websocket.md#game-session-protocol).

```json
{
  "type": "GAME_STARTED",
  "version": 50,
  "payload": {
    "sessionId": "uuid"
  }
}
```

The client derives its game destinations from `sessionId` (`/topic/game.{sessionId}`, `/topic/game.{sessionId}.team.{teamId}`, `/user/queue/game`); no topic string is sent. STOMP's path separator is `.`, not `/`.

#### `GAME_ENDED`

The game session has ended and the room has returned to Lobby state (FR-LIFE-002). All player readiness is reset (FR-READY-004). Clients should unsubscribe from the game topic.

```json
{
  "type": "GAME_ENDED",
  "version": 51,
  "payload": {
    "roomId": "uuid",
    "readinessReset": true
  }
}
```

`readinessReset: true` signals that all players are now unready. The client should reset its local readiness state for all players on receiving this event. No separate `READINESS_RESET` event follows for the post-game reset.

---

### Readiness

#### `READINESS_CHANGED`

A player has toggled their readiness state (FR-READY-003).

```json
{
  "type": "READINESS_CHANGED",
  "version": 52,
  "payload": {
    "playerId": "uuid",
    "ready": true
  }
}
```

---

### Team Management

#### `TEAM_ADDED`

Host instantiated a new team from a template (FR-TEAM-002).

```json
{
  "type": "TEAM_ADDED",
  "version": 54,
  "payload": {
    "teamId": "uuid",
    "templateName": "string",
    "configuredSize": 4,
    "index": 1
  }
}
```

#### `TEAM_REMOVED`

Host removed an empty team (FR-TEAM-003).

```json
{
  "type": "TEAM_REMOVED",
  "version": 55,
  "payload": {
    "teamId": "uuid"
  }
}
```

#### `TEAM_RESIZED`

Host changed the configured size of a team (FR-TEAM-004).

```json
{
  "type": "TEAM_RESIZED",
  "version": 56,
  "payload": {
    "teamId": "uuid",
    "newConfiguredSize": 3
  }
}
```

#### `PLAYER_REASSIGNED`

Host moved a player (human or AI) to a different team (FR-TEAM-006). For human players, `readinessReset: true` indicates the moved player's readiness was cleared (FR-TEAM-007). For AI players, `readinessReset` is always false (AI is always ready per FR-READY-002).

```json
{
  "type": "PLAYER_REASSIGNED",
  "version": 57,
  "payload": {
    "playerId": "uuid",
    "fromTeamId": "uuid",
    "toTeamId": "uuid",
    "readinessReset": true
  }
}
```

#### `PARAMETERS_CHANGED`

Host updated game parameters (FR-HOST-007). The full parameter set is always broadcast — no delta encoding.

```json
{
  "type": "PARAMETERS_CHANGED",
  "version": 58,
  "payload": {
    "parameters": {
      "key": "value"
    }
  }
}
```

---

### Reconnection and Presence

#### `PLAYER_DISCONNECTED`

A player's WebSocket connection was lost. The grace period begins (FR-GRACE-004 in reconnection-flow.md). Delivered to all other participants, including spectators.

```json
{
  "type": "PLAYER_DISCONNECTED",
  "version": 59,
  "payload": {
    "playerId": "uuid",
    "gracePeriodSeconds": 60
  }
}
```

`gracePeriodSeconds` is the total grace period duration (FR-GRACE-002). The client may combine this with the local timestamp at receipt to derive the expiry time.

#### `PLAYER_RECONNECTED`

A disconnected player reconnected within their grace period (FR-REJOIN-004 in reconnection-flow.md).

```json
{
  "type": "PLAYER_RECONNECTED",
  "version": 60,
  "payload": {
    "playerId": "uuid"
  }
}
```

If the reconnecting player was the former host, they return as a regular player — `HOST_TRANSFERRED` was already emitted at disconnect time (FR-HDISC-001/002). No further host event is emitted on reconnect.

#### `PLAYER_LOST`

The grace period expired without the player reconnecting. The player's slot is released (FR-EXPIRY-001). The game backend is separately notified via the `player_left` input (FR-IN-005 in game-contracts.md).

```json
{
  "type": "PLAYER_LOST",
  "version": 61,
  "payload": {
    "playerId": "uuid",
    "teamId": "uuid",
    "reason": "GRACE_PERIOD_EXPIRED"
  }
}
```

---

## Client→Server Command Catalogue

All commands use the envelope `{ "type", "correlationId", "payload" }`. Receiving an unknown `type` returns an `UNKNOWN_COMMAND` error to `/user/queue/errors`; the connection is never closed for an unknown command type.

### Member Commands — `/app/room.{roomId}.member`

Authorized for any room member (player or spectator). The channel-level guard validates that the sender is a current room member. Per-command role and state checks are enforced inside the handler.

| `type` | Payload fields | Authorized sender | Preconditions |
|---|---|---|---|
| `TOGGLE_READY` | `ready: boolean` | Non-host human player | Room in Lobby state |
| `SWITCH_TO_SPECTATOR` | *(none)* | Non-host human player | Lobby; spectating enabled for room; spectator capacity not exceeded (NFR-SPEC-001 in game-rooms.md) |
| `SWITCH_TO_PLAYER` | *(none)* | Spectator | Lobby; at least one player slot available |
| `REQUEST_ROOM_STATE` | *(none)* | Any member or spectator | Always valid |

**`TOGGLE_READY`:** The host never sends this command — the host's readiness is implicit in `START_GAME` (FR-READY-001). AI players are always ready (FR-READY-002) and have no command.

**`SWITCH_TO_SPECTATOR`:** Vacates the player's team slot and clears their readiness. Broadcasts `PLAYER_ROLE_CHANGED`. The host cannot switch to spectator (FR-XFER-001).

**`SWITCH_TO_PLAYER`:** Auto-assigns the spectator to the team with the fewest current members (FR-TEAM-005, FR-LIFE-006). Broadcasts `PLAYER_ROLE_CHANGED`.

**`REQUEST_ROOM_STATE`:** Triggers a unicast `ROOM_STATE` snapshot on `/user/queue/room-state`. See [Snapshot Delivery](#snapshot-delivery).

---

### Host Commands — `/app/room.{roomId}.host`

Authorized only for the current room host. The channel-level guard evaluates `principal.id == room.hostId` using the session-bound Principal from `SimpMessageHeaderAccessor.getUser()`. Because host identity is mutable runtime state, the authoritative host check is **re-validated inside the handler under the room lock** — the channel-level check is a fast-fail optimisation only.

| `type` | Payload fields | Preconditions |
|---|---|---|
| `KICK_PLAYER` | `playerId: uuid` | Target is a current member (player, spectator, or AI); valid in any room state |
| `ADD_TEAM` | `templateName: string, configuredSize: integer` | Lobby; template count `<` `count.max`; `configuredSize ∈ [size.min, size.max]` |
| `REMOVE_TEAM` | `teamId: uuid` | Lobby; team has zero current members |
| `RESIZE_TEAM` | `teamId: uuid, newSize: integer` | Lobby; `newSize ∈ [size.min, size.max]`; `newSize ≥` current member count (FR-TEAM-010) |
| `REASSIGN_PLAYER` | `playerId: uuid, toTeamId: uuid` | Lobby; target team has an available slot |
| `ADD_AI_PLAYER` | `teamId: uuid` | Lobby; game supports AI players (FR-HOST-003); target team has an available slot |
| `CHANGE_PARAMETERS` | `parameters: object` | Lobby; game exposes configurable parameters (FR-HOST-007) |
| `START_GAME` | *(none)* | Lobby; all FR-TEAM-009 conditions satisfied |
| `TRANSFER_HOST` | `newHostId: uuid` | Target is a human player (not spectator or AI) in the room; valid in Lobby and In Progress |

**`KICK_PLAYER`:** Works for human players, AI players, and spectators. In In Progress state, kicking a human player voids any active grace period and triggers the `player_left` game backend input with `reason: kicked`. The kicked party receives a unicast `KICKED` error on `/user/queue/errors`.

**`START_GAME`:** Preconditions are evaluated atomically under the room lock. If a condition fails at lock time (e.g., a player un-readied between the host's UI check and the command arrival), the command is rejected with `START_CONDITIONS_NOT_MET` listing the failed conditions.

**`TRANSFER_HOST`:** The former host retains their player slot and remains in the room as a regular player (FR-XFER-004).

---

## Authorization Model

Authorization is enforced at two layers.

### Channel-level (fast-fail)

| Destination | Check | On failure |
|---|---|---|
| `/topic/room.{roomId}` (subscribe) | Sender is a member or spectator of the room | Silent drop |
| `/topic/room.{roomId}.chat` (subscribe) | Sender is a non-spectator player in the room | Silent drop |
| `/topic/room.{roomId}.team.{teamId}` (subscribe) | Sender is a player assigned to `teamId` | Silent drop |
| `/app/room.{roomId}.member` (send) | Sender is a member or spectator of the room | Error on `/user/queue/errors` |
| `/app/room.{roomId}.host` (send) | `principal.id == room.hostId` (evaluated at message time) | Error on `/user/queue/errors` |

Principal resolution uses `SimpMessageHeaderAccessor.getUser()` — not `SecurityContextHolder`, which is not populated on STOMP channel threads.

### Handler-level (authoritative)

All per-command role, state, and business-rule checks are enforced inside the `@MessageMapping` handler under the room lock. These are the authoritative checks; the channel-level checks provide early rejection without acquiring the lock.

Handler violations throw typed exceptions caught by `@MessageExceptionHandler`, which routes the error to `/user/queue/errors` via `@SendToUser("/queue/errors", broadcast=false)`.

The host re-check inside the handler is required because host identity is mutable: a `TRANSFER_HOST` command or host disconnect can change `room.hostId` between the channel-level check and the handler acquiring the lock.

### `AntPathMatcher` destination patterns

Spring STOMP uses `.` as the path separator. The `*` wildcard matches exactly one segment. Destination patterns must be written as non-overlapping entries:

| Pattern | Matches |
|---|---|
| `/topic/room.*` | Lobby/room event topic for any room |
| `/topic/room.*.chat` | Room-channel chat for any room |
| `/topic/room.*.team.*` | Team-channel chat for any room and team |

Room and team IDs must not contain `.` characters. UUIDs satisfy this constraint.

---

## Snapshot Delivery

The client follows this sequence on entering a room:

1. REST join or create → response sets routing hint directing traffic to the owning pod.
2. Client establishes WebSocket (`/ws`) to the owning pod.
3. Client subscribes to `/topic/room.{roomId}`, `/user/queue/room-state`, `/user/queue/errors`, and — if a player — `/topic/room.{roomId}.chat`; and — if team-assigned — `/topic/room.{roomId}.team.{teamId}`.
4. Client sends `REQUEST_ROOM_STATE` on `/app/room.{roomId}.member`.
5. Server acquires room lock → reads current state → stamps snapshot with current version → sends `ROOM_STATE` to `/user/queue/room-state` for the requesting user → releases lock.
6. Client receives snapshot, sets `localVersion = snapshot.version`.
7. Client applies subsequent delta events as described in [Client Reconciliation](#client-reconciliation).

The snapshot includes `disconnectedPlayers` with `graceRemainingSeconds` for players currently within a grace period — the only mechanism by which a newly joined or reconnected client learns of in-flight grace timers (FR-GRACE-004 in reconnection-flow.md).

---

## Error Handling

Command failures are returned on `/user/queue/errors` using the base error envelope:

```json
{
  "type": "ERROR",
  "payload": {
    "correlationId": "uuid",
    "code": "NOT_HOST",
    "message": "Human-readable description.",
    "roomId": "uuid",
    "details": {}
  }
}
```

`correlationId` echoes the value from the originating command. `code` is a stable machine-readable string. `details` is optional and may contain field-level validation information. Error messages do not carry `version`.

### Error codes

| Code | Trigger |
|---|---|
| `NOT_HOST` | Host-only command sent by non-host |
| `NOT_MEMBER` | Command sent by a non-member of the room |
| `ROOM_NOT_LOBBY` | Lobby-only command sent while room is In Progress |
| `TEAM_NOT_EMPTY` | `REMOVE_TEAM` on a team with current members |
| `TEAM_FULL` | Assignment to a team already at configured capacity |
| `OVER_CAPACITY` | Resize would reduce capacity below current member count |
| `TEMPLATE_MAX_TEAMS` | `ADD_TEAM` would exceed `count.max` for the template |
| `SIZE_OUT_OF_RANGE` | `configuredSize` outside `[size.min, size.max]` |
| `START_CONDITIONS_NOT_MET` | `START_GAME` when FR-TEAM-009 conditions are not satisfied; `details` lists the unmet conditions |
| `TARGET_NOT_PLAYER` | `TRANSFER_HOST` targeting a spectator or AI player |
| `SPECTATOR_CAPACITY_FULL` | `SWITCH_TO_SPECTATOR` when spectator limit is reached |
| `SPECTATING_NOT_ENABLED` | `SWITCH_TO_SPECTATOR` when spectating is disabled for the room |
| `PLAYER_NOT_FOUND` | Targeted `playerId` does not exist in this room |
| `AI_NOT_SUPPORTED` | `ADD_AI_PLAYER` when the game does not support AI players |
| `KICKED` | Unicast notification to a player removed by the host (no `correlationId`) |
| `UNKNOWN_COMMAND` | Unrecognised `type` in command envelope |

---

## Client Reconciliation

The client maintains `localVersion` initialised from the `ROOM_STATE` snapshot.

| Condition | Action |
|---|---|
| `delta.version == localVersion + 1` | Apply delta; set `localVersion = delta.version` |
| `delta.version <= localVersion` | Discard (state already reflected) |
| `delta.version > localVersion + 1` | Gap detected — send `REQUEST_ROOM_STATE`; discard deltas until new snapshot arrives |

Under the room affinity model, gaps should not occur in normal operation (single producer, STOMP per-destination FIFO delivery). The gap-detection path guards against edge cases such as pod restart during a session.

---

## Spectator Event Visibility

Spectators subscribe to `/topic/room.{roomId}` and receive all events in that topic, including readiness, team, and parameter events. They do not subscribe to chat topics (`/topic/room.{roomId}.chat`, `/topic/room.{roomId}.team.{teamId}`); the `SubscriptionInterceptor` rejects spectator subscriptions to those destinations silently.

Spectator visibility of game effects during an active session is governed by game-contracts.md (FR-DELIVER-002, FR-FE-006), which restricts spectators to `broadcast` effects only. The permissive lobby visibility policy does not extend to the game topic.
