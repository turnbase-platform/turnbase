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
| `/topic/game.{sessionId}` | server→client | Session players + spectators | Game effects delivered by the Orchestration Service |
| `/app/game.{sessionId}.action` | client→server | Sending player | Player action submission |
| `/user/queue/errors` | server→client | Individual user | Per-user errors: kicked from room, session failed, session displaced by new login |

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

The game event type catalogue is defined in `game-contracts.md`. The lobby event type catalogue, command catalogue, and room affinity routing model are defined in [room-websocket.md](room-websocket.md). The chat event and command formats are defined in [room-chat-websocket.md](room-chat-websocket.md).

## Authorization

Subscriptions to `/topic/room.{roomId}` and `/topic/game.{sessionId}` are validated server-side by a `SubscriptionInterceptor`. The interceptor checks that the subscribing user is a member or spectator of the referenced room or session. Unauthorized subscriptions are silently dropped — no data is sent and no error is returned to the client.

## Relationship to Notifications

Platform notifications (friend requests, room invitations) are delivered over a separate SSE channel, not over WebSocket. See [sse-notifications.md](sse-notifications.md). WebSocket is reserved for bidirectional, low-latency game and lobby real-time events.
