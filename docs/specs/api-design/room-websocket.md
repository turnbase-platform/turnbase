# Room WebSocket Protocol

## Overview

This specification defines the STOMP-over-WebSocket protocol for room lobby real-time events. It extends the base connection, authentication, and envelope established in [websocket.md](websocket.md) with the full room event catalogue, command catalogue, and the room affinity routing model.

**Scope:** room lifecycle, membership, team management, readiness, parameter changes, game start/end transitions, and reconnection presence events. In-room chat wire format is defined separately in [room-chat-websocket.md](room-chat-websocket.md). Game effect delivery during an active session is defined in [websocket.md](websocket.md) and [game-contracts.md](../../requirements/game-contracts.md).

## Related Documents

- [websocket.md](websocket.md) — base connection, authentication, envelope, and game event topics
- [room-chat-websocket.md](room-chat-websocket.md) — chat send/receive wire format
- [game-rooms.md](../../requirements/game-rooms.md) — room lifecycle, team management, and host control requirements
- [reconnection-flow.md](../../requirements/reconnection-flow.md) — grace period and reconnection requirements
- [ADR-0008](../../decisions/0008-room-ownership-lifecycle.md) — room ownership as a lease-gated claim; source of the V1/V2 rules below and the `RECONNECT_REQUIRED`/`ROOM_UNAVAILABLE_RETRY` codes
- [room-lifecycle.md](../platform/room-lifecycle.md) — the claim/release mechanism, key table, and adoption procedure behind § Room Affinity

---

## Room Affinity and WebSocket Routing

All real-time room events for a given room are produced by a single Platform Monolith pod — the pod that owns that room (ADR-0002). Ownership is **not** a lifetime assignment: it is a revocable claim gated on the incumbent's liveness lease, stored in Redis (`room:{roomId}:pod → podId`). A room may sit ownerless indefinitely — nothing reassigns it until a client or the reconciliation sweep next needs it. The claim mechanism (liveness lease, atomic claim/release scripts, split-brain prevention) is specified in [ADR-0008](../../decisions/0008-room-ownership-lifecycle.md) and [room-lifecycle.md](../platform/room-lifecycle.md); this section covers only what it means for the WebSocket protocol.

### Routing on join

When a player joins or creates a room via the REST endpoint, the server claims the room if it is ownerless (or confirms the existing claim) and returns the routing hint as the `X-TurnBase-Room-Instance` response header (`room-rest-api.md` § *The affinity hint is a response header*).

**The client carries the hint forward as the `instance` query parameter on the `/ws` connection URL** — `/ws?instance={podId}` — because a browser's native `WebSocket` constructor cannot set arbitrary headers on the handshake request, and the hint must reach the ingress in the one part of that request a client script controls: the URL. An ingress configured for it can route the upgrade by that parameter; `local-environment.md` §3's round-robin ingress is not so configured and ignores it, which is correct per FR-DEPLOY-002 — the hint is advisory and the receiving instance resolves ownership itself either way (§1.2). The client establishes this connection **after** receiving the join or create response, so the parameter is always the freshest hint available.

**In the common case** — the room already has a live owner and the ingress honours the hint — no reconnection or migration occurs at room entry. This does not hold across a claim change: see Pod failure below.

### Consequences

- All subscribers to `/topic/room.{roomId}` are connected to the same pod, for as long as that pod holds the claim.
- Per-room state mutations use a JVM-local `ReentrantLock` (keyed by room ID) — no distributed lock is required.
- Per-room version counters are in-JVM `AtomicLong` values, **committed to the database before publish** (V1, below) — no Redis counter is required.
- `SimpMessagingTemplate.convertAndSend(...)` and `convertAndSendToUser(...)` always reach their targets locally.

### Pod failure

If the owning pod crashes or is drained for a deploy, every client of its rooms loses its WebSocket connection simultaneously (ADR-0008 Invariant I1). The stale `room:{roomId}:pod` entry is **not** self-correcting: it still names the dead pod until something invalidates it. Reconnection therefore does not go through "the standard join flow assigns a new owning pod" — no step in that flow invalidates a live-looking entry. Instead:

- A crash is invalidated by the liveness gate: the claim script sees the incumbent's `pod:{podId}:alive` lease has expired (TTL 10s) and takes over.
- A graceful drain releases the claim explicitly before the pod exits, so the next claimant hits the free branch immediately — no lease wait.
- The reconciliation sweep can also claim an ownerless room on demand (e.g. to fire a grace deadline) with no client attached.

A rejoin attempt that lands while the old claim is still live (within the lease TTL after a crash) is redirected to retry rather than routed to a corpse; worst case ≈10s (ADR-0008 Consequences). Room state itself is unaffected — it is persisted to the database on every mutation (V1, below), independent of which pod currently holds the claim.

---

## Destinations

The following destinations extend [websocket.md](websocket.md). The game-session destinations (`/topic/game.*`, `/user/queue/game`, `/app/game.*.action`, `/app/game.*.sync`) and `/user/queue/errors` are defined in [websocket.md](websocket.md) and are unchanged here.

| Destination | Direction | Authorized subscribers / senders | Purpose |
|---|---|---|---|
| `/topic/room.{roomId}` | server→client | Room players and spectators | All room lifecycle, membership, team, readiness, and presence events |
| `/topic/room.{roomId}.chat` | server→client | Room players only (not spectators) | Room-channel chat messages |
| `/topic/room.{roomId}.team.{teamId}` | server→client | Players assigned to that team | Team-channel chat messages |
| `/topic/room.{roomId}.start` | server→client | Current room participants — players and spectators | `GAME_START_STATUS` progress while a `START_GAME` is being carried out. Ephemeral and unversioned; never replayed |
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
4. Increment the room version counter and **commit the new version and state to the database.**
5. Publish the delta event to `/topic/room.{roomId}` via the local broker, only after the commit succeeds.
6. Release the lock.

Publishing the event inside the lock (step 5) guarantees that no delta with a higher version can be queued before a lower-version delta. STOMP's per-destination FIFO order then delivers them in sequence. Clients can apply deltas strictly in version order without additional coordination.

The version counter is an in-JVM `AtomicLong` per room, initialised from the database when the room is claimed by this pod.

**V1 — persist before publish (ADR-0008).** Step 4's commit must complete before step 5's publish. This is not merely lock hygiene: it guarantees `room.version >= every version ever broadcast`, so an adopting pod resuming from the database can never reuse a version a client has already applied. If a pod published before committing, a crash between the two would let an adopting pod — which initialises its counter from the database — re-issue a version a client has already seen. Clients discard `delta.version <= localVersion` (Client Reconciliation, below), so that divergence would be silent and permanent rather than a detectable gap.

The commit is a **fenced** conditional update, `WHERE room_id = :id AND version = :expected AND owner_epoch = :myEpoch` — the epoch, not the version, is what excludes a stale owner. A room-scoped version cannot fence, because the legitimate owner advances through the very value a stale owner is holding. The nesting is normative: **lock outer → transaction inner → publish after the commit returns, before the lock is released.** The natural `@Transactional`-on-the-handler arrangement commits after the method returns — that is, after the publish — which silently reinstates the race V1 exists to close. See [room-lifecycle.md](../platform/room-lifecycle.md) §1.5 and §2.1.

---

## Server→Client Event Catalogue

All events below are delivered on `/topic/room.{roomId}` and carry the `version` field. Spectators receive all events on this topic. Chat events are on separate topics (see [room-chat-websocket.md](room-chat-websocket.md)) and are not received by spectators.

Chat events carry `version: null` and do **not** advance the counter, because their topics reach a
subset of this topic's subscribers and a partially-delivered sequence cannot be gap-detected — see
[room-chat-websocket.md](room-chat-websocket.md).

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
    "sessionId": "uuid | null",
    "gameFrontendUrl": "string | null"
  }
}
```

`sessionId` is non-null when `state == IN_PROGRESS`; `gameFrontendUrl` is non-null exactly when `sessionId` is, so a reconnecting or late-joining client can construct the game iframe from the snapshot alone, with no extra round-trip. Both fields carry the same meaning as in `GAME_STARTED`. `disconnectedPlayers` contains only players currently within an active grace period; it is empty when no player is disconnected. `teams[i].memberIds` contains all player IDs assigned to that team (human and AI); cross-reference with `aiPlayers` to determine AI status. Chat history is not included — per [in-room-chat.md](../../requirements/in-room-chat.md) FR-MSG-005, the platform does not persist chat messages.

`spectatorCapacity` is the resolved value of the platform property
`turnbase.room.spectator-capacity` (default `8`, `local-environment.md` §7.1) — a platform limit, not
a per-room or per-game one, per `game-rooms.md` NFR-SPEC-001. It is sent in the snapshot so a client
can render occupancy without reading configuration, and it is **not** versioned state: a config change
is picked up by the next snapshot and emits no delta.

**`aiPlayers` is always empty in v1.** The AI player interface is deferred (`game-contracts.md`
OQ-002) and the AI execution environment with it (`platform-architecture.md` *Out of Scope*), so no v1
game declares `capabilities.ai` and no AI can be seated. The field is present rather than removed
because its shape is settled and removing it would be a breaking change to add back; a client must
render an empty array as "no AI players", never as an error.

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

The room has been permanently closed. Delivered to all current subscribers before the room is torn down.

```json
{
  "type": "ROOM_CLOSED",
  "version": 49,
  "payload": {
    "roomId": "uuid",
    "reason": "NO_PLAYERS_REMAINING | GRACE_EXPIRED_NO_HUMAN | ACCOUNT_DELETED | IDLE_TIMEOUT"
  }
}
```

`reason` is the closed set persisted as `room.closed_reason` ([data-model.md](../platform/data-model.md) § Closure reasons):

| Reason | Trigger |
|---|---|
| `NO_PLAYERS_REMAINING` | An explicit host leave with no other human player remaining (FR-XFER-002). |
| `GRACE_EXPIRED_NO_HUMAN` | An In Progress room's last-connected-human host disconnected and the grace period expired with no human reconnecting (reconnection-flow.md FR-HDISC-003), closing the room via FR-XFER-002/FR-XFER-003. |
| `ACCOUNT_DELETED` | The host's account was deleted, which counts as a confirmed voluntary departure (FR-LIFE-004). |
| `IDLE_TIMEOUT` | A Lobby room sat with no connected participant past the configured idle window (`platform-operations.md` FR-JOB-007d, `game-rooms.md` FR-LIFE-007). |

`IDLE_TIMEOUT` is the one platform-initiated closure cause. An In Progress room whose game session is
unrecoverable is **not** closed — `platform-operations.md` FR-JOB-007c fails it back to Lobby instead
(`IMP-GATE-55`); see `GAME_ENDED` below, which is that path's client notification.

After receiving this event, clients not already told the room was closed by one of the above (e.g. a client that was never attached, or was mid-reconnect when the sweep acted) still learn the outcome via `ROOM_CLOSED` if subscribed, or via the standard rejoin flow reporting the room as closed (reconnection-flow.md FR-REJOIN-008) otherwise. Clients should unsubscribe and navigate away on receipt. The room cannot be rejoined (FR-XFER-003).

---

### Game Lifecycle

#### `GAME_START_STATUS`

Published on `/topic/room.{roomId}.start` while a `START_GAME` whose preconditions hold is being carried
out, so that every participant sees why the lobby is waiting. It is **not** on `/topic/room.{roomId}`:
that topic is versioned and its state is reconstructible from `ROOM_STATE`, while a start phase is
transient and would be replayed stale. It carries no `version`, is never replayed, and a client that
subscribes mid-start sees nothing until the next phase or `GAME_STARTED`.

```json
{ "type": "GAME_START_STATUS", "payload": { "phase": "WAITING_FOR_HOST" } }
```

| `phase` | Meaning |
|---|---|
| `STARTING` | The start was accepted; a Game Host is being chosen |
| `WAITING_FOR_HOST` | No Game Host is eligible yet; the platform is waiting up to `turnbase.orchestration.host-wait` for one to register (a cold stack) |
| `LOADING_GAME` | `CreateSession` is in flight; the host is loading the game bundle and running `onInit` |
| `RETRYING` | An attempt failed at the transport or timed out; another is under way, on a different host if one is eligible |
| `FAILED` | The start was abandoned; `payload.reason` is the `GAME_START_FAILED` reason. The unicast error follows |

Success has no phase of its own: `GAME_STARTED` on `/topic/room.{roomId}` ends the sequence. Every
sequence ends in `GAME_STARTED` or `FAILED`; a client clears its progress display on either.
([ADR-0018](../../decisions/0018-game-start-resilience.md))

#### `GAME_STARTED`

The host has started the game (FR-HOST-009). Clients transition to the game view and enter the game-session attach flow: subscribe to the game destinations, then request a sync. See [websocket.md § Game Session Protocol](websocket.md#game-session-protocol).

```json
{
  "type": "GAME_STARTED",
  "version": 50,
  "payload": {
    "sessionId": "uuid",
    "gameFrontendUrl": "http://{gameId}.games.localhost:8080/play/{sessionId}"
  }
}
```

The client derives its game destinations from `sessionId` (`/topic/game.{sessionId}`, `/topic/game.{sessionId}.team.{teamId}`, `/user/queue/game`); no topic string is sent. STOMP's path separator is `.`, not `/`.

`gameFrontendUrl` is the **absolute** URL the client loads into the game iframe. It is composed server-side from the deploy-time origin template and the game version pinned at session creation; the client never assembles it, and never derives the game origin from a build-time constant. The shell's trusted game origin for postMessage is exactly `new URL(gameFrontendUrl).origin`. See [game-frontend/game-asset-serving.md](../game-frontend/game-asset-serving.md) §3.1 and §7.

#### `GAME_ENDED`

The game session has ended and the room has returned to Lobby state (FR-LIFE-002). All player readiness is reset (FR-READY-004).

The same event, with the same payload shape, is also the client notification for `platform-operations.md` FR-JOB-007c (`IMP-GATE-55`): an In Progress room whose game session state was found gone is failed back to Lobby by reconciliation rather than closed, and this is what tells attached clients. The wire contract does not distinguish the two triggers — both mean "the game is over, you are back in Lobby, forget your local readiness state" — the difference (a `game_session_completion` history row is written for FR-LIFE-002 and never for FR-JOB-007c) is server-side only. Clients should unsubscribe from the game topic.

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

**The *Authorized sender* column is server-enforced, not merely a client-side expectation** — unlike
FR-JOIN-008–010's abandonment prompts (`room-rest-api.md` §5), nothing here states the server accepts
the command regardless of role. A command sent by a member whose current role does not satisfy its
*Authorized sender* column (the host sending `TOGGLE_READY` or `SWITCH_TO_SPECTATOR`; a non-spectator
sending `SWITCH_TO_PLAYER`) fails with `ROLE_NOT_ELIGIBLE` (`IMP-GATE-45`).

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
| `ADD_AI_PLAYER` | `teamId: uuid` | Lobby; game supports AI players (FR-HOST-003); target team has an available slot. **In v1 this always fails with `AI_NOT_SUPPORTED`** — see below |
| `CHANGE_PARAMETERS` | `parameters: object` | Lobby; game exposes configurable parameters (FR-HOST-007) |
| `START_GAME` | *(none)* | Lobby; all FR-TEAM-009 conditions satisfied |
| `TRANSFER_HOST` | `newHostId: uuid` | Target is a human player (not spectator or AI) in the room; valid in Lobby and In Progress |

**`ADD_AI_PLAYER` is specified but unreachable in v1.** The handler is implemented and returns
`AI_NOT_SUPPORTED` unconditionally, because no v1 game may declare `capabilities.ai` — bundle
validation rejects a manifest that sets it while `game-contracts.md` OQ-002 is open
([`../manifest/manifest-schema.md`](../manifest/manifest-schema.md) § `capabilities`). Implementing
the rejection rather
than omitting the command keeps the error catalogue honest and gives the frontend a defined response
to a button it may still render disabled.

**`KICK_PLAYER`:** Works for human players, AI players, and spectators. In In Progress state, kicking a human player voids any active grace period and triggers the `player_left` game backend input with `reason: kicked`. The kicked party receives a unicast `KICKED` error on `/user/queue/errors`.

**`START_GAME`:** Preconditions are evaluated atomically under the room lock. If a condition fails at lock time (e.g., a player un-readied between the host's UI check and the command arrival), the command is rejected with `START_CONDITIONS_NOT_MET` listing the failed conditions.

A `START_GAME` whose preconditions hold but whose session cannot be created — no Game Host is eligible
to take it (`game-host-internals.md` §11's selection finds none), or `CreateSession` fails at the
transport or in-band (`orchestration-gamehost-protocol.md` *Error model*) — is rejected with
`GAME_START_FAILED`, unicast to the host. `details.reason` is `NO_HOST_AVAILABLE` (no host registered
within `host-wait`), `HOST_UNRESPONSIVE` (a host accepted the call and did not answer within the
dispatch deadline, on every attempt; it is set aside for `quarantine-ttl`) or
`SESSION_CREATION_FAILED` (the call failed in-band or at the transport for a reason a retry cannot
help); each carries a message that says what the host can do next. The platform makes at most three
attempts, and waits for a host to register before each; progress is published as
`GAME_START_STATUS`. The failure's own message is never forwarded (it can be text from game
code). Nothing about the room changes: it stays in Lobby with `active_session_id` unset, no
`GAME_STARTED` is broadcast, and the host may send `START_GAME` again (`IMP-GATE-88`).

**`TRANSFER_HOST`:** The former host retains their player slot and remains in the room as a regular player (FR-XFER-004).

---

## Authorization Model

Authorization is enforced at two layers.

### Channel-level (fast-fail)

| Destination | Check | On failure |
|---|---|---|
| `/topic/room.{roomId}` (subscribe) | Sender is a member or spectator of the room | Silent drop — **except** the one case below |
| `/topic/room.{roomId}.chat` (subscribe) | Sender is a non-spectator player in the room | Silent drop |
| `/topic/room.{roomId}.team.{teamId}` (subscribe) | Sender is a player assigned to `teamId` | Silent drop |
| `/topic/room.{roomId}.start` (subscribe) | Sender is a current participant (player or spectator) of the room | Silent drop |
| `/app/room.{roomId}.member` (send) | Sender is a member or spectator of the room | Error on `/user/queue/errors` |
| `/app/room.{roomId}.host` (send) | `principal.id == room.hostId` (evaluated at message time) | Error on `/user/queue/errors` |

Principal resolution uses `SimpMessageHeaderAccessor.getUser()` — not `SecurityContextHolder`, which is not populated on STOMP channel threads.

**`SLOT_RELEASED` (`IMP-GATE-51`, `reconnection-flow.md` FR-REJOIN-007).** A `SUBSCRIBE` to
`/topic/room.{roomId}` from a sender who is not a current member is not always a stranger: `data-model.md`
§2's row-reuse rule (`IMP-GATE-50`) means the room keeps exactly one `room_participant` row per
`(room_id, user_id)` for the caller's entire history there, so its `leave_reason` is inspectable. When
that row exists with `left_at IS NOT NULL AND leave_reason = 'GRACE_EXPIRED'`, the caller lost the race
to their own grace expiry (a rejoin attempt that arrived after the sweep had already resolved it) — the
subscription is rejected with `SLOT_RELEASED` on `/user/queue/errors` (`retryAfterMs: 0`, not
retryable) rather than silently dropped, so the client can fall straight into the late-join flow
(FR-REJOIN-006) instead of reading silence as "room not found." Every other terminal `leave_reason`
(`LEFT`, `KICKED`, `ROOM_CLOSED`, `GAME_ENDED`, `EARLY_RELEASE`) is an intentional past departure, not
a race, and stays a silent drop — as does no row existing at all.

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
3. Client subscribes to `/topic/room.{roomId}`, `/user/queue/room-state`, `/user/queue/errors`, and — if a player — `/topic/room.{roomId}.chat`; and — if team-assigned — `/topic/room.{roomId}.team.{teamId}`; and `/topic/room.{roomId}.start`.
   Each `SUBSCRIBE` carries a `receipt` header. The server answers it with a `RECEIPT` frame (`receipt-id` = the header's value) once the broker has registered the subscription, and **a client must not act on the room before the receipts for step 3 have arrived** — not send `REQUEST_ROOM_STATE` or any other command. The broker registers a `SUBSCRIBE` on an executor, independently of the frames the client sends next: a `REQUEST_ROOM_STATE` can be answered before `/user/queue/room-state` is registered, and an event broadcast in between never reaches `/topic/room.{roomId}` (a `READINESS_CHANGED` lost that way is the `ready_timeout` of `load-testing.md` §13 finding 4). A `SUBSCRIBE` the server drops or rejects (an unauthorized destination, Tier 6) gets no `RECEIPT`; the client treats that as an incomplete attach.
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

**This table is the registry for every WebSocket error code in the corpus, not only the room's.**
It aggregates codes owned by `rate-limiting.md`, `input-validation.md` and `websocket.md`, and the
last two rows are game-session codes delivered on the *game* destination rather than the room's. One
table exists because the alternative — a client-side enum assembled from three documents — reliably
loses whichever code was only ever written in prose. Nothing here is Problem Details; WebSocket
errors use the envelope above, and REST errors use [error-handling.md](error-handling.md)'s.

| Code | Trigger |
|---|---|
| `NOT_HOST` | Host-only command sent by non-host |
| `ROLE_NOT_ELIGIBLE` | A member command's *Authorized sender* precondition failed for a reason other than host/non-host: the host sending `TOGGLE_READY` or `SWITCH_TO_SPECTATOR`, or a non-spectator sending `SWITCH_TO_PLAYER` |
| `NOT_MEMBER` | Command sent by a non-member of the room |
| `ROOM_NOT_LOBBY` | Lobby-only command sent while room is In Progress |
| `TEAM_NOT_EMPTY` | `REMOVE_TEAM` on a team with current members |
| `TEAM_FULL` | Assignment to a team already at configured capacity |
| `OVER_CAPACITY` | Resize would reduce capacity below current member count |
| `TEMPLATE_MAX_TEAMS` | `ADD_TEAM` would exceed `count.max` for the template |
| `SIZE_OUT_OF_RANGE` | `configuredSize` outside `[size.min, size.max]` |
| `START_CONDITIONS_NOT_MET` | `START_GAME` when FR-TEAM-009 conditions are not satisfied; `details` lists the unmet conditions |
| `GAME_START_FAILED` | `START_GAME` when the preconditions hold but the session could not be created; `details.reason` is `NO_HOST_AVAILABLE`, `HOST_UNRESPONSIVE` or `SESSION_CREATION_FAILED`. The room stays in Lobby |
| `TARGET_NOT_PLAYER` | `TRANSFER_HOST` targeting a spectator or AI player |
| `SPECTATOR_CAPACITY_FULL` | `SWITCH_TO_SPECTATOR` when spectator limit is reached |
| `SPECTATING_NOT_ENABLED` | `SWITCH_TO_SPECTATOR` when spectating is disabled for the room |
| `PLAYER_NOT_FOUND` | Targeted `playerId` does not exist in this room |
| `AI_NOT_SUPPORTED` | `ADD_AI_PLAYER` when the game does not support AI players |
| `KICKED` | Unicast notification to a player removed by the host (no `correlationId`) |
| `SLOT_RELEASED` | A reconnection attempt lost the race to its own grace expiry — the reservation was resolved before the client returned (reconnection-flow.md FR-EXPIRY-005). The client falls into the late-join path (FR-REJOIN-007); this is an ordinary outcome of returning as the window closes, not a fault |
| `ROOM_UNAVAILABLE_RETRY` | `SUBSCRIBE` to a room this pod does not own — ownership changed between the REST join and the subscription (see below). Carries `retryAfterMs`; the client backs off and re-runs the join flow. Also returned by the REST join/rejoin call, where it is an HTTP error rather than a frame |
| `UNKNOWN_COMMAND` | Unrecognised `type` in command envelope |
| `UNKNOWN_PARAMETER` | `CHANGE_PARAMETERS` with a key not declared in the game's manifest |
| `PARAMETER_TYPE_MISMATCH` | `CHANGE_PARAMETERS` value does not match the manifest's declared type |
| `PARAMETER_OUT_OF_RANGE` | `CHANGE_PARAMETERS` value outside the manifest's declared `min`/`max`, `maxLength`, or `options` |
| `VALIDATION_FAILED` | Command payload failed field validation ([input-validation.md](input-validation.md)); `details` names the failed fields |
| `MESSAGE_TOO_LARGE` | Frame exceeds the per-destination size cap (input-validation.md § Size limits) |
| `RATE_LIMIT_EXCEEDED` | Frame dropped by the Tier 6 rate limiter ([rate-limiting.md](rate-limiting.md)); carries `retryAfterMs`. Emitted from the channel interceptor without a `correlationId`, since the payload was never deserialized |
| `ACTION_TOO_LARGE` | **Game session.** A `/app/game.*.action` frame exceeds the 256 KB `setMessageSizeLimit` cap ([websocket.md](websocket.md) § *Client→server command catalogue*). Rejected at admission; the game never sees it |
| `ACTION_REJECTED` | **Game session.** An admitted action failed *inside* the game handler — threw, timed out in-context, or produced malformed output (`PROCESS_STATUS_FAILED`). Carries `correlationId` and the failure **kind**, never the failure message, which is text from untrusted game code ([websocket.md](websocket.md)). `kind` is the `GameFailureKind` name without its prefix (`HANDLER_EXCEPTION`, `TIMEOUT`, …), or `UNAVAILABLE` when the input was dropped for an infrastructure reason (host unreachable, session unservable) — never re-dispatched either way |

**Game-session admission reuses two room codes** (`websocket.md` § `SUBMIT_ACTION`, `IMP-M3-06`): a
`SUBMIT_ACTION` from someone who is not a current participant of the session — or for a session that
is unknown, ended or not In Progress, which the sender is not told apart from the first — draws
`NOT_MEMBER`; one from a spectator draws `ROLE_NOT_ELIGIBLE`. The frame carries `sessionId` where a
room error carries `roomId`.

The last two are the only codes here that a room client never sees. They are listed anyway because
the point of a registry is that the enum is complete — and they are the two that were previously
stated in prose only, with no table entry anywhere.

Three further codes are carried on the STOMP `ERROR` frame that **closes** the connection rather than on
`/user/queue/errors`: `RATE_LIMIT_ABUSE` (sustained rate-limit violation) and `TOO_MANY_CONNECTIONS`
(more than 4 concurrent connections for one user), both defined in
[rate-limiting.md](rate-limiting.md) Tier 6; and `RECONNECT_REQUIRED`, sent to every client attached to
a room whose owning pod is gracefully draining, immediately before the pod releases its ownership claim
and exits (ADR-0008 decision point 5). Unlike a crash, a drain is a clean signal: clients receiving
`RECONNECT_REQUIRED` should immediately re-run the standard join flow rather than waiting out a
disconnect-detection timeout, because the claim is released (not merely expiring) and the next claimant
lands on the free branch with no lease wait.

A claim attempt that instead arrives while the *previous* owner's liveness lease is still live (the
crash case, not drain) cannot be satisfied immediately. The receiving pod retries the claim internally
for **a few hundred milliseconds** — deliberately not seconds: the retry holds a request thread, and on
a rolling deploy every client reconnects at once, so a multi-second internal retry converts a routing
hiccup into thread-pool exhaustion ([room-lifecycle.md](../platform/room-lifecycle.md) §1.7). If the
claim is still unresolved when the call must respond, it returns `ROOM_UNAVAILABLE_RETRY` with a
bounded `retryAfterMs`; worst case ≈10s of client-side retrying, bounded by the liveness lease TTL
(ADR-0008 Consequences). The client retries rather than treating this as a terminal failure.

`ROOM_UNAVAILABLE_RETRY` arises at **two** points, not one, and a client must handle both:

- On the REST join/rejoin call, as above — a REST-layer error, since no WebSocket exists yet.
- On `SUBSCRIBE` to `/topic/room.{roomId}`, as a frame on `/user/queue/errors`. The claim runs during
  the REST join, but between that call and the client's `SUBSCRIBE` another pod's reconciliation sweep
  can take a room that was momentarily free. The handler therefore **re-verifies ownership at subscribe
  time** and rejects rather than serving a subscription to a room it does not own — holding a client's
  socket is never evidence of owning that client's room. The client's response is the same: back off
  for `retryAfterMs` and re-run the join flow, which re-resolves the affinity hint.

`CHANGE_PARAMETERS` is validated as a **whitelist** against the manifest of the game version pinned to
the room — unknown keys are rejected outright, so the broadcast `parameters` object is bounded by the
manifest's own declared bounds. See [input-validation.md](input-validation.md).

---

## Client Reconciliation

The client maintains `localVersion`, set from the `ROOM_STATE` snapshot.

**V2 — assign, never `max()` (ADR-0008).** On receiving a `ROOM_STATE` snapshot, the client sets `localVersion = snapshot.version` **unconditionally** — it must not keep a previously-held value if that value happens to be higher. After a takeover, the new owning pod's counter is initialised from the database (V1 guarantees this is never behind what clients have seen, but a client's in-memory `localVersion` from a stale in-page state is not authoritative once a new snapshot arrives); the snapshot is always the source of truth.

| Condition | Action |
|---|---|
| `delta.version == localVersion + 1` | Apply delta; set `localVersion = delta.version` |
| `delta.version <= localVersion` | Discard (state already reflected) |
| `delta.version > localVersion + 1` | Gap detected — send `REQUEST_ROOM_STATE`; discard deltas until new snapshot arrives (apply V2 on receipt) |

Within a single, uninterrupted claim, gaps should not occur (single producer, STOMP per-destination FIFO delivery). The gap-detection path is not just an edge-case guard: it is the mechanism that makes a claim change safe. A takeover (Pod failure, above) always produces a forward gap for attached clients reconnecting to the new owner — V1 guarantees the new pod's version is never lower than the last one broadcast, so "gap" and "stale/wrong" cannot be confused — and the client's normal `REQUEST_ROOM_STATE` path resolves it with no special-cased reconnection logic.

---

## Spectator Event Visibility

Spectators subscribe to `/topic/room.{roomId}` and receive all events in that topic, including readiness, team, and parameter events. They also subscribe to `/topic/room.{roomId}.start`, so the start progress is visible to them too. They do not subscribe to chat topics (`/topic/room.{roomId}.chat`, `/topic/room.{roomId}.team.{teamId}`); the `SubscriptionInterceptor` rejects spectator subscriptions to those destinations silently.

Spectator visibility of game effects during an active session is governed by `platform-architecture.md` FR-DELIVER-002 and `game-contracts.md` FR-FE-006, which restrict spectators to `broadcast` effects only. The permissive lobby visibility policy does not extend to the game topic.
