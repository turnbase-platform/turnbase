# Server-Sent Events — Notifications

Platform notifications are delivered over a Server-Sent Events stream. This is the implementation decision for `notifications-invitations.md FR-NOTIF-007` (real-time delivery mechanism) and `CON-001` (mechanism left as implementation decision at requirements stage).

SSE is appropriate here because the channel is unidirectional (server→client only) and HTTP/1.1 compatible. Notifications do not require client-to-server messages — interaction (accept, decline) is handled via REST.

## Endpoint

```
GET /api/notifications/stream
```

Requires authentication. Returns `Content-Type: text/event-stream`. The connection is long-lived; the server holds it open and pushes events as they arrive.

## Event Shape

```
id: 42
event: notification
data: {"type":"FRIEND_REQUEST","notificationId":"uuid","fromUser":"alice","timestamp":"2026-06-11T13:00:00Z"}

```

| Field | Description |
|-------|-------------|
| `id` | Monotonically increasing integer per user. Used for `Last-Event-ID` replay. |
| `event` | Always `notification`. |
| `data` | JSON object. `type` identifies the notification kind; remaining fields are type-specific. `notificationId` is always present and used for client-side deduplication. |

## Notification Types

| `type` | Description |
|--------|-------------|
| `FRIEND_REQUEST` | Another user sent a friend request (`notifications-invitations.md FR-FREQ-001`) |
| `FRIEND_REQUEST_ACCEPTED` | A sent friend request was accepted (`FR-FREQ-003`) |
| `FRIEND_REQUEST_DECLINED` | A sent friend request was declined (`FR-FREQ-004`) |
| `ROOM_INVITATION` | Host invited this user to a room (`FR-INV-001`) |
| `INVITATION_ACCEPTED` | An invitation sent by this user was accepted (`FR-INV-006`, sender alert) |
| `INVITATION_DECLINED` | An invitation sent by this user was declined (`FR-INV-006`, sender alert) |
| `BUNDLE_VALIDATION_COMPLETE` | Async game bundle validation finished (status ACTIVE or FAILED) — see [file-uploads.md](file-uploads.md) |
| `SESSION_DISPLACED` | This user's session was invalidated by a login from another device (`user-accounts.md FR-SESS-004`) |

## Offline Delivery

Notifications generated while a user is offline are persisted and delivered on their next connection (`FR-NOTIF-008`). When the client opens the SSE stream, the server immediately replays all undelivered notifications (those created after the user's last seen event ID).

On reconnect after a brief disconnect, the browser automatically sends `Last-Event-ID`. The server replays any buffered events the client missed.

**Buffer policy:** last 50 events per user **or** events from the last 5 minutes — whichever is smaller — for the live reconnect buffer. Full offline delivery (since last session) is handled separately from the buffer via the notification persistence store.

## Keepalive

A periodic comment (`:\n\n`) is sent every 30 seconds to prevent proxy and load balancer timeouts on idle connections.

## Implementation

Spring MVC `SseEmitter` (or reactive `Flux<ServerSentEvent>` if the notification path uses Spring WebFlux). An in-memory `NotificationEmitterRegistry` stores active emitters keyed by user ID. The notification dispatch service looks up the emitter and writes to it on event creation. When no emitter is registered for a user (offline), the notification is persisted only.

Connection cleanup: when a client disconnects, the emitter's `onCompletion` and `onTimeout` callbacks remove it from the registry.
