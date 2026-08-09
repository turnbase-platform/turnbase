# WebSocket

## Connection

Single STOMP-over-WebSocket connection per client, established at `/ws`. Spring's STOMP broker handles topic-based multiplexing — clients subscribe to specific topics rather than receiving all traffic on one channel.

SockJS is **not** used. Modern browsers and the React frontend support native WebSocket without a fallback transport.

## Authentication

The `httpOnly` session cookie is sent automatically by the browser with the WebSocket upgrade request (same-origin). A Spring `ChannelInterceptor` validates the session token on the STOMP `CONNECT` frame before the connection is established. Unauthenticated `CONNECT` frames are rejected with a STOMP `ERROR` frame and the connection is closed.

No separate WebSocket token is issued.

## Topics

| Destination | Direction | Audience | Used for |
|-------------|-----------|----------|----------|
| `/topic/room.{roomId}` | server→client | All room members and spectators | Lobby events: player join/leave, readiness toggle, team changes, parameter changes, presence |
| `/topic/room.{roomId}.chat` | server→client | Room players (not spectators) | Room-channel chat messages |
| `/topic/room.{roomId}.team.{teamId}` | server→client | Players assigned to that team | Team-channel chat messages |
| `/user/queue/room-state` | server→client | Individual user | Unicast room state snapshot in response to `REQUEST_ROOM_STATE` |
| `/app/room.{roomId}.member` | client→server | Room members and spectators | Member commands: readiness, role switch, snapshot request |
| `/app/room.{roomId}.host` | client→server | Current room host | Host commands: team management, kick, parameters, game start, host transfer |
| `/app/room.{roomId}.chat` | client→server | Room players (not spectators) | Send a chat message |
| `/topic/game.{sessionId}` | server→client | Session players + spectators | `broadcast` effects, game log, game-over, session-scoped player joined/left, session failure |
| `/topic/game.{sessionId}.team.{teamId}` | server→client | Session players assigned to that team | `send_to_team` effects |
| `/user/queue/game` | server→client | Individual user | `send_to_player` effects and the unicast `GAME_SYNC` snapshot |
| `/app/game.{sessionId}.action` | client→server | Active, non-spectator session players | Player action submission |
| `/app/game.{sessionId}.sync` | client→server | Session players and spectators | Game sync (snapshot) request |
| `/user/queue/errors` | server→client | Individual user | Per-user errors: kicked from room, rejected command, session displaced by new login |

## Message Envelope

All STOMP message payloads use a consistent envelope:

```json
{
  "type": "PLAYER_JOINED",
  "payload": { ... }
}
```

| Field | Description |
|-------|-------------|
| `type` | String constant identifying the event kind |
| `payload` | Event-specific data object |

The lobby event type catalogue, command catalogue, and room affinity routing model are defined in [room-websocket.md](room-websocket.md). The chat event and command formats are defined in [room-chat-websocket.md](room-chat-websocket.md). The **game session protocol** — destinations, envelope extensions, event catalogue, catch-up, and authorization — is defined in the second half of this document ([Game Session Protocol](#game-session-protocol)).

## Authorization

Subscriptions to `/topic/room.{roomId}` and `/topic/game.{sessionId}` are validated server-side by a `SubscriptionInterceptor`. The interceptor checks that the subscribing user is a member or spectator of the referenced room or session. Unauthorized subscriptions are silently dropped — no data is sent and no error is returned to the client. The full per-destination matrix for game destinations is in [Authorization model](#authorization-model-game) below.

## Relationship to Notifications

Platform notifications (friend requests, room invitations) are delivered over a separate SSE channel, not over WebSocket. See [sse-notifications.md](sse-notifications.md). WebSocket is reserved for bidirectional, low-latency game and lobby real-time events.

---

# Game Session Protocol

The client-facing half of game execution: how the effects a game backend produces reach the right players' iframes and no one else's, how a client that attaches mid-session obtains a consistent picture, and how a player action gets from the iframe to the game backend.

**Upstream seam.** [`game-host/game-host-internals.md`](../game-host/game-host-internals.md) §10 carries the execution pipeline as far as *"Orchestration hands effect E to the WebSocket Gateway, addressed to recipient set R, tagged with `sequence` N."* This section takes it from there. Together they close review blocker **GAME-B1**, plus **I4** (action-send authorization) and **I6** (initial effect delivery race).

**Requirements realized:** `game-contracts.md` FR-EFF-001…005, FR-FE-001…006, FR-FA-001…003, FR-LOG-001…005, FR-RESP-004, NFR-SEC-001/002; `platform-architecture.md` FR-DELIVER-001…004.

**Out of scope (seams):**

| Seam | Owned by |
|------|----------|
| The platform HTML shell that frames the iframe, injects the `__TURNBASE__` bootstrap, and performs the STOMP↔`postMessage` relay | Platform-frontend shell spec (planned). This section defines the [relay contract](#platform-shell-relay-contract) it must satisfy. |
| Game asset serving origin, iframe `sandbox` attributes, CSP | [game-frontend/game-asset-serving.md](../game-frontend/game-asset-serving.md) |
| WebSocket frame rate limiting and size caps | [rate-limiting.md](rate-limiting.md) Tier 6; [input-validation.md](input-validation.md) § Size limits |
| The `resync` input's backend contract | [`game-contracts.md`](../../requirements/game-contracts.md) FR-IN-006, [`gdk-api/backend-gdk-api.md`](../gdk-api/backend-gdk-api.md) §3 |

---

## Session affinity and fan-out locality

**Session affinity follows room affinity** (ADR-0002). A session belongs to exactly one room, and the pod that owns that room ([room-websocket.md](room-websocket.md) § Room Affinity) also owns the session's Orchestration dispatcher and its effect fan-out.

Consequences:

- Every participant's WebSocket connection is on the owning pod, so effect delivery is a **local** `SimpMessagingTemplate.convertAndSend(...)` / `convertAndSendToUser(...)` call — no broker relay, no cross-pod fan-out.
- There is a **single producer** per session, so per-destination publish order is the order the Orchestration Service intends.
- Orchestration remains stateless and its state Redis-resident (game-host-internals.md §13); affinity pins only *which replica runs the live dispatcher*, not where the state lives. A pod loss is recovered by **claiming** the room, not by an automatic reassignment: the dead pod's ownership becomes claimable once its liveness lease expires (or immediately, if it drained and released), the first returning client or the reconciliation sweep claims it, and the adopting pod re-creates the dispatcher and re-dispatches the head of `queue:{sessionId}`. Clients then re-sync (below). Exactly-once survives this with no Game Host change — replay by `sequence`, the delivery watermark, and client-side `asOfSequence` dedup already compose to give it. See [ADR-0008](../../decisions/0008-room-ownership-lifecycle.md) and [`../platform/room-lifecycle.md`](../platform/room-lifecycle.md) §1.

The broker is configured with `setPreservePublishOrder(true)` so that messages addressed to one client session preserve publish order **across destinations** — necessary because a single game result can produce effects on the session topic, a team topic, and a user queue, whose relative order is significant (FR-RESP-004).

---

## Envelope: `sequence` and `index`

Game messages extend the base envelope with three fields:

```json
{
  "type": "GAME_EVENT",
  "sessionId": "uuid",
  "sequence": 42,
  "index": 1,
  "payload": { }
}
```

| Field | Description |
|---|---|
| `sessionId` | The session the message belongs to. Required on every game message — `/user/queue/game` is not session-scoped in its destination. |
| `sequence` | The monotonic per-session input sequence allocated by the Orchestration Service in Redis at enqueue time (game-host-internals.md §9.2). `CreateSession` is sequence `0`. |
| `index` | 0-based position of the originating effect within that result's effect list. Platform-generated lifecycle events carry `index: -1` (see below). |

`(sequence, index)` is a **unique, totally ordered key** for every message a client can receive in a session. It is what carries the backend's effect-ordering guarantee (FR-RESP-004) onto the wire, and it is the client's dedup key.

**`index: -1`.** `GAME_PLAYER_JOINED` and `GAME_PLAYER_LEFT` are generated by the platform, not by the game, but they are *caused* by an input the game also processes. They are emitted at that input's `sequence` with `index: -1`, so a single `(sequence, index)` comparator sorts them ahead of the effects the game returned for the same input — which is the order a game FE needs ("player left" before the effects reacting to it).

**Messages with no sequence.** `GAME_SYNC` carries `asOfSequence` instead (it is a snapshot, not an effect). `SESSION_FAILED` and errors on `/user/queue/errors` carry neither.

### There is no gap detection on the game stream

`room-websocket.md` uses a per-room `version` for gap detection, and that works because every room event reaches every subscriber, so the sequence a client observes is dense.

**The game stream is deliberately sparse.** A `send_to_player` addressed to another player consumes a `sequence` this client will never see; so does a `send_to_team` for another team. Holes are normal and carry no information.

Therefore: **`sequence` is an ordering and dedup key only. Clients must not attempt gap detection on it, and must never request a snapshot because of a "missing" sequence.** The recovery mechanism for a client that may have missed messages is a re-sync (below), triggered by reconnection — never by a gap.

---

## Catch-up: the sync flow (closes I6)

A game's authoritative state lives only in the game backend, opaque to the platform (NFR-SEC-003). A game FE holds no authoritative state of its own — it renders what the backend has pushed it. A client that was not subscribed when an effect went out has therefore lost that information permanently.

Three normal situations produce exactly that:

1. **Game start.** `CreateSession` runs the backend's `onInit` immediately, which typically emits each player's opening state via `send_to_player` — while every player is still navigating from lobby to game view and loading their iframe. No one is subscribed yet.
2. **Reconnection.** The returning client's iframe is brand new and missed everything during the outage.
3. **Mid-game join.**

All three are answered by one mechanism, structurally identical to the room's `REQUEST_ROOM_STATE`/`ROOM_STATE` snapshot — with one difference forced by NFR-SEC-003: the platform **cannot** compose a game snapshot itself. It cannot read game state, and each viewer is entitled to a different slice of it (my hand is not your hand; a spectator sees neither). Only the game backend can answer *"what does this viewer see right now"*, so the platform asks it, via the read-only **`resync`** input (game-contracts.md FR-IN-006).

### Sequence of events

```
1. Client learns sessionId          (GAME_STARTED on the room topic, or ROOM_STATE
                                     when entering a room already In Progress)
2. Client SUBSCRIBEs:               /topic/game.{sessionId}
                                    /user/queue/game
                                    /topic/game.{sessionId}.team.{teamId}   (players with a team)
   ── and begins BUFFERING every game message it receives ──
3. Client SENDs REQUEST_GAME_SYNC   on /app/game.{sessionId}.sync
4. Orchestration:
     a. validates the sender is a participant of an active session
     b. composes the init context (role, self, roster, teams) from room state
     c. dispatches a read-only Resync to the Game Host, under the session's
        single-flight lock, which invokes the game's onResync(state, viewer)
        → { viewPayload, asOfSequence = lastAppliedSequence }
        (no state write, no sequence allocation, no delivery-watermark change)
     d. reads the retained game log for the session
5. Server unicasts GAME_SYNC on /user/queue/game
6. Client discards buffered messages with sequence <= asOfSequence, applies the
   remainder in (sequence, index) order, then processes live messages normally.
```

### Why this is race-free

The client subscribes **before** it requests the sync. Therefore:

- Any effect at or below `asOfSequence` is, by definition, already reflected in the view the backend just computed — so discarding it is correct.
- Any effect above `asOfSequence` was fanned out **after** the client was already subscribed, so the client received it (buffered) and applies it on top of the snapshot.

There is no window in which a message is neither in the snapshot nor delivered. This holds identically at game start, on reconnect, and on late join.

### Consequences worth stating

- **`onInit` effects are not delivery-guaranteed.** They are fanned out to whoever is subscribed at sequence 0, which at game start is typically nobody. A game backend must not rely on them to establish a player's view; that is `onResync`'s job. (This is why `game-contracts.md` FR-FE-001 no longer promises initial state via `send_to_player`.)
- **The resync view is always the first `game_event` a freshly loaded game FE receives** — at start, on reconnect, and on late join alike. A game FE therefore needs no discriminator to tell a snapshot from a delta: its first event is always the full view. Recorded as the resolution of frontend-gdk-api OQ-001.
- **The game log is the only thing the platform retains per session** (FR-DELIVER-003, FR-LOG-004): bounded text entries, not opaque effect payloads. There is no effect journal.
- **After `GAME_OVER` the session is terminated** and sync is no longer available. A client reconnecting after game end returns to the room lobby (game-rooms.md FR-LIFE-002; the results view is a client-side overlay, reconnection-flow.md FR-DC-004).

---

## Server→client event catalogue

### `GAME_SYNC`

Unicast on `/user/queue/game` in response to `REQUEST_GAME_SYNC`. The client's complete starting picture.

```json
{
  "type": "GAME_SYNC",
  "sessionId": "uuid",
  "asOfSequence": 42,
  "correlationId": "uuid",
  "payload": {
    "init": {
      "sessionId": "uuid",
      "role": "player | spectator",
      "self": { "id": "uuid", "displayName": "string", "teamId": "uuid" },
      "roster": [ { "id": "uuid", "displayName": "string", "teamId": "uuid" } ],
      "teams": [
        {
          "id": "uuid",
          "name": "Attacker 1",
          "players": [ { "id": "uuid", "displayName": "string", "teamId": "uuid" } ]
        }
      ]
    },
    "view": { },
    "log": [ { "sequence": 3, "index": 0, "entry": "**Alice** played the Queen of Spades" } ]
  }
}
```

| Field | Description |
|---|---|
| `asOfSequence` | The `lastAppliedSequence` the `view` reflects. The client discards buffered messages at or below it. |
| `payload.init` | Exactly the `InitContext` of [frontend-gdk-api.md](../gdk-api/frontend-gdk-api.md) §5, relayed verbatim into the iframe as the `init` event (FR-FE-001). `self` is `null` for spectators. Field names follow the GDK's `Player`/`Team` shape (`id`/`displayName`/`teamId`), not the room catalogue's (`playerId`/`username`). |
| `payload.view` | The opaque view returned by the game's `onResync` for this viewer. Relayed into the iframe as the first `game_event` (FR-FE-002). May be an empty object; never `null`. |
| `payload.log` | The full game log from session start (FR-LOG-004), ordered by `(sequence, index)`. Rendered by the platform UI, never relayed into the iframe (FR-LOG-005). |

`correlationId` echoes the value from the `REQUEST_GAME_SYNC` command.

### `GAME_EVENT`

An opaque game payload from a `broadcast`, `send_to_player`, or `send_to_team` effect. Destination determines the audience; the message shape is identical in all three cases, and the client cannot tell which effect type produced it (FR-FE-002).

| Origin effect | Destination | Requirement |
|---|---|---|
| `broadcast` | `/topic/game.{sessionId}` — all players **and** spectators | FR-EFF-001, FR-DELIVER-002 |
| `send_to_team` | `/topic/game.{sessionId}.team.{teamId}` — subscription validated against team membership | FR-EFF-003 |
| `send_to_player` | `/user/queue/game` — resolved by Spring from the target principal | FR-EFF-002 |

```json
{ "type": "GAME_EVENT", "sessionId": "uuid", "sequence": 42, "index": 1, "payload": { } }
```

This routing is what makes NFR-SEC-002 mechanically true rather than aspirational: a `send_to_player` payload rides a per-user queue whose destination a client cannot guess or subscribe to on another's behalf, and a `send_to_team` payload rides a topic whose subscription is membership-validated server-side. Spectators are refused team-topic subscriptions outright, so they can receive `broadcast`-originated events only (FR-FE-006).

### `GAME_LOG`

A platform-managed log entry from a `log` effect (FR-EFF-004). Delivered on `/topic/game.{sessionId}` to all players and spectators (FR-LOG-001). Rendered by the platform UI **outside** the iframe and never relayed to the game FE (FR-LOG-005).

```json
{
  "type": "GAME_LOG",
  "sessionId": "uuid",
  "sequence": 42,
  "index": 0,
  "payload": { "entry": "**Alice** played the Queen of Spades" }
}
```

`entry` supports basic Markdown and the GDK's color annotations (FR-LOG-002; syntax deferred — game-contracts.md OQ-001). Ordering with respect to other effects of the same result is carried by `index` (FR-LOG-003).

### `GAME_PLAYER_JOINED`

A player joined the session mid-game (FR-FE-003). Emitted on `/topic/game.{sessionId}` at the `sequence` of the `player_joined` input, with `index: -1`.

```json
{
  "type": "GAME_PLAYER_JOINED",
  "sessionId": "uuid",
  "sequence": 43,
  "index": -1,
  "payload": { "player": { "id": "uuid", "displayName": "string", "teamId": "uuid" } }
}
```

Distinct from the room topic's `PLAYER_JOINED`, which is a lobby-presence event with different semantics and a different payload shape.

### `GAME_PLAYER_LEFT`

A player was **confirmed lost** — grace period expired, host kick, or voluntary leave (FR-FE-004; the three reasons of FR-IN-005). Emitted at the `player_left` input's `sequence` with `index: -1`.

```json
{
  "type": "GAME_PLAYER_LEFT",
  "sessionId": "uuid",
  "sequence": 44,
  "index": -1,
  "payload": {
    "player": { "id": "uuid", "displayName": "string", "teamId": "uuid" },
    "reason": "GRACE_PERIOD_EXPIRED | KICKED | LEFT"
  }
}
```

A transient disconnect is **never** signalled here — the game learns nothing until the grace period resolves (game-contracts.md CON-007, reconnection-flow.md FR-GRACE-003). Disconnect/reconnect presence during the grace period is a *room* concern and is carried by `PLAYER_DISCONNECTED`/`PLAYER_RECONNECTED` on the room topic, which the platform UI renders and the shell does not relay into the iframe.

`reason` is for the platform UI. The shell drops it when relaying, since the FE GDK's `player_left` event carries only the player (FR-FE-004).

### `GAME_OVER`

The game ended (FR-EFF-005, FR-FE-005). Delivered on `/topic/game.{sessionId}` to all players and spectators.

```json
{
  "type": "GAME_OVER",
  "sessionId": "uuid",
  "sequence": 51,
  "index": 2,
  "payload": { "results": { } }
}
```

`results` is the **opaque results payload** for the game FE. The structured `GameOutcome` (placements, stats) is platform-only — it feeds game history and statistics and is **never** sent to any client (FR-FE-005, FR-OUTCOME-*).

Terminal: no further game messages are sent for the session. Effects that followed `game_over` in the same result are still delivered first, in `index` order (FR-EFF-006).

### `SESSION_FAILED`

The session failed permanently and was terminated by the platform — the retry limit was reached (FR-FAIL-003/005) or the game backend could not be recovered (NFR-REL-001). Delivered on `/topic/game.{sessionId}` to all participants; carries no `sequence`.

```json
{
  "type": "SESSION_FAILED",
  "sessionId": "uuid",
  "payload": {
    "reason": "GAME_ERROR | RETRY_LIMIT | HOST_UNAVAILABLE",
    "message": "The game encountered an error and could not continue."
  }
}
```

`message` is player-safe text. Diagnostic detail from `GameFailure.message` is for platform logs only and is never sent to clients. The room returns to Lobby state independently, signalled by `GAME_ENDED` on the room topic.

> Session failure is a **session-wide** event and therefore belongs on the session topic. It is not a per-user command error, and it is not delivered on `/user/queue/errors`.

---

## Client→server command catalogue

Both commands use the room command envelope: `{ "type", "correlationId", "payload" }`, where `correlationId` is a client-generated UUID echoed in any error response.

### `REQUEST_GAME_SYNC` — `/app/game.{sessionId}.sync`

```json
{ "type": "REQUEST_GAME_SYNC", "correlationId": "uuid" }
```

Authorized for any participant of an active session — players **and** spectators. Triggers the sync flow above. Idempotent and safe to repeat: it mutates no game state (`onResync` is read-only), so a client may re-request after any reconnection.

### `SUBMIT_ACTION` — `/app/game.{sessionId}.action`

```json
{ "type": "SUBMIT_ACTION", "correlationId": "uuid", "payload": { } }
```

`payload` is the opaque, game-defined action payload from the iframe's `sendAction` (FR-FA-001).

**Player identity is never supplied by the client** (FR-FA-002, NFR-SEC-001). The Orchestration Service resolves the acting player from the STOMP principal and attaches it to the `ActionInput` before routing to the game backend. A payload field purporting to carry identity is ignored — it is opaque game data, and the game backend receives the platform's `PlayerRef`, never the client's claim.

Accepted actions are enqueued on the session's Redis queue, where they receive their `sequence` (game-host-internals.md §9.2). The client receives no acknowledgement; the action's observable outcome is whatever effects the game returns. Rejected actions produce an error on `/user/queue/errors` carrying the `correlationId`.

**Inbound size limit.** The STOMP inbound message size limit applies (Spring `setMessageSizeLimit`, default **256 KB**, configurable per environment). Oversized frames are rejected with `ACTION_TOO_LARGE`. This is an inbound client cap and is unrelated to NFR-SIZE-002's 10 MB *outbound* effect payload limit.

**Rate limiting.** Action and sync frames are bounded by Tier 6 of [rate-limiting.md](rate-limiting.md) (per-user, pod-local): `SUBMIT_ACTION` draws on the `action` bucket (5/s, burst 10) and `REQUEST_GAME_SYNC` on the far stricter `snapshot` bucket (1 per 3s, burst 2) — it re-enters the guest VM under the session's single-flight lock, which makes it the most expensive frame a client can send.

---

## Authorization model (game)

Enforced in two layers, matching the room pattern ([room-websocket.md](room-websocket.md) § Authorization Model).

### Channel-level (fast-fail)

| Destination | Check | On failure |
|---|---|---|
| `/topic/game.{sessionId}` (subscribe) | Sender is a participant of the session (player **or** spectator) | Silent drop |
| `/topic/game.{sessionId}.team.{teamId}` (subscribe) | Sender is a **player** of the session **assigned to `teamId`** | Silent drop |
| `/user/queue/game` (subscribe) | Inherent: Spring resolves user queues from the authenticated principal | n/a |
| `/app/game.{sessionId}.sync` (send) | Sender is a participant of an **active** session | Error on `/user/queue/errors` |
| `/app/game.{sessionId}.action` (send) | Sender is an **active, non-spectator player** of an **active** session | Error on `/user/queue/errors` |

Principal resolution uses `SimpMessageHeaderAccessor.getUser()`, not `SecurityContextHolder`, which is not populated on STOMP channel threads.

Team-topic subscription validation is what prevents a player from reading another team's `send_to_team` payloads by guessing a team ID — the same guard the team chat channel uses, and the reason `send_to_team` is sound under NFR-SEC-002.

### Handler-level (authoritative)

Participation is **mutable runtime state**: a player can be kicked, lose their slot to grace-period expiry, or leave voluntarily between the channel check and the handler. Every `SUBMIT_ACTION` and `REQUEST_GAME_SYNC` therefore **re-validates** membership, role, and session liveness inside the `@MessageMapping` handler under the session lock. The channel-level check is a fast-fail optimisation only; the handler check is authoritative.

Specifically, `SUBMIT_ACTION` is accepted only when, at handler time:

1. the session exists and is active (not terminated, not past `game_over`),
2. the sender is a current participant of that session,
3. the sender's role is **player**, not spectator (spectators can never act — FR-FE-006 has no action counterpart),
4. the sender is not currently a lost/removed player.

### `AntPathMatcher` destination patterns

Spring STOMP uses `.` as the path separator; `*` matches exactly one segment.

| Pattern | Matches |
|---|---|
| `/topic/game.*` | Session topic for any session (does **not** match the team topic) |
| `/topic/game.*.team.*` | Team topic for any session and team |
| `/app/game.*.action` | Action submission for any session |
| `/app/game.*.sync` | Sync request for any session |

Session and team IDs must not contain `.` characters. UUIDs satisfy this.

---

## Client reconciliation

The client maintains `lastApplied = (sequence, index)`, initialised to `(asOfSequence, +∞)` from `GAME_SYNC`.

| Condition | Action |
|---|---|
| Message received before `GAME_SYNC` has arrived | Buffer it |
| `sequence <= asOfSequence` | Discard — already reflected in the snapshot |
| `(sequence, index) <= lastApplied` | Discard — duplicate |
| Otherwise | Apply; set `lastApplied = (sequence, index)` |
| Gap in `sequence` | **Nothing.** Sparse sequences are normal (see above) |
| WebSocket reconnect | Re-subscribe, re-buffer, re-issue `REQUEST_GAME_SYNC` |

Dedup is required because delivery is **at-least-once**: the exactly-once machinery guarantees an action is *applied* exactly once, but a re-dispatched result or a client reconnect can cause a message to be *delivered* twice (game-host-internals.md §9.2 — "final client-side dedup keyed by `sequence` in the WS layer"). `(sequence, index)` is that key.

---

## Platform-shell relay contract

The platform shell owns the iframe and is the only component that speaks `postMessage` (CON-002, CON-006). It never forwards a STOMP frame verbatim; it translates. The game FE never sees STOMP, `sequence`, or any platform envelope.

| STOMP message | Relayed to the iframe as |
|---|---|
| `GAME_SYNC` | `init` (from `payload.init`), **then** `game_event` (from `payload.view`) |
| `GAME_EVENT` | `game_event` with `payload` |
| `GAME_LOG` | *nothing* — rendered in the platform UI (FR-LOG-005) |
| `GAME_PLAYER_JOINED` | `player_joined` with `payload.player` |
| `GAME_PLAYER_LEFT` | `player_left` with `payload.player` (`reason` dropped) |
| `GAME_OVER` | `game_over` with `payload.results` |
| `SESSION_FAILED` | *nothing* — rendered in the platform UI |
| room-topic presence events | *nothing* — platform UI only |

| Iframe message | Relayed to the platform as |
|---|---|
| `{ type: 'ready' }` | *nothing* — consumed by the shell (handshake gate, below) |
| `{ type: 'action', payload }` | `SUBMIT_ACTION` on `/app/game.{sessionId}.action` |

**Two gates the shell must satisfy** (frontend-gdk-api.md §4 guarantees `init` is the game FE's first event, and it must be true):

1. It must not post `init` until it has **both** received `GAME_SYNC` **and** received the iframe's `ready` handshake.
2. It must hold every subsequent game message until `init` has been posted, then flush in `(sequence, index)` order.

The shell is also the component that must inject the `__TURNBASE__` bootstrap (`parentOrigin`, `sessionId`) before the game bundle's JS runs (frontend-gdk-api.md §9) and validate the origin of every inbound iframe message (NFR-SEC-004).

---

## Requirements traceability

| Requirement | Realized by |
|---|---|
| FR-EFF-001/002/003 → delivery | `GAME_EVENT` on session topic / user queue / team topic |
| FR-EFF-004, FR-LOG-001…005 | `GAME_LOG`; log retained per session; replayed in `GAME_SYNC`; never relayed to the iframe |
| FR-EFF-005/006, FR-FE-005 | `GAME_OVER` (opaque results only; structured outcome withheld) |
| FR-RESP-004 (effect ordering) | `index` + `setPreservePublishOrder(true)` + client `(sequence, index)` ordering |
| FR-FE-001 (init) | `GAME_SYNC.payload.init` → shell posts `init` |
| FR-FE-002 (unified event stream) | `GAME_EVENT`, identical shape on all three destinations |
| FR-FE-003/004 | `GAME_PLAYER_JOINED` / `GAME_PLAYER_LEFT` (confirmed loss only) |
| FR-FE-006 (spectator filtering) | Spectators refused team-topic subscription; `send_to_player` on user queues only |
| FR-FA-001/002/003, NFR-SEC-001 | `SUBMIT_ACTION`; identity attached from the principal, never from the client |
| FR-IN-006 (`resync`) | The sync flow; `REQUEST_GAME_SYNC` → `onResync` → `GAME_SYNC` |
| FR-DELIVER-001/002 | Local fan-out under session affinity; per-destination audience matrix |
| FR-DELIVER-003 | Game log retention + `GAME_SYNC.payload.log` |
| NFR-SEC-002 (no unauthorized recipients) | Per-user queue + membership-validated team topic; no shared game topic carries private payloads |
| NFR-REL-001 | `SESSION_FAILED` |
| GAME-B1 | This section (client half); game-host-internals.md §10 (execution half) |
| GAME-I4 | [Authorization model](#authorization-model-game) — handler-level authoritative re-check |
| GAME-I6 | [Catch-up: the sync flow](#catch-up-the-sync-flow-closes-i6) |

---

## Open questions

- **OQ-001 — Resync cost under load.** `onResync` is invoked once per attaching client and runs under the session's single-flight lock, so a mass reconnect (pod restart) serializes N resyncs behind one session. Bounded by MVP session sizes; if it becomes a hotspot, cache the per-viewer view against `lastAppliedSequence` and serve repeat requests from the cache without re-entering the guest. The *adversarial* case — one client re-requesting sync in a loop — is closed by the `snapshot` bucket ([rate-limiting.md](rate-limiting.md) Tier 6); this OQ concerns only the legitimate mass-reconnect case, where each client sends exactly one request.
- **OQ-002 — Spectator sync of a game with no spectator view.** A game whose `onResync` returns an empty view for spectators leaves them with a blank iframe until the next `broadcast`. This is a game-authoring concern, not a platform one, but the local test harness should warn on it.
