# Server-Sent Events — Notifications

Platform notifications are delivered over a Server-Sent Events stream. This is the implementation decision for `notifications-invitations.md FR-NOTIF-007` (real-time delivery mechanism) and `CON-001` (mechanism left as implementation decision at requirements stage).

SSE is appropriate here because the channel is unidirectional (server→client only) and HTTP/1.1 compatible. Notifications do not require client-to-server messages — interaction (accept, decline) is handled via REST.

## Endpoint

```
GET /api/notifications/stream
```

Requires authentication. Returns `Content-Type: text/event-stream`. The connection is long-lived; the server holds it open and pushes events as they arrive.

## Two event classes

The stream carries **two** kinds of message, and the distinction is not cosmetic — it decides whether
a message is stored, replayed, or dropped (`notifications-invitations.md` FR-ALERT-010).

| | `event: notification` | `event: alert` |
|---|---|---|
| Persisted | Yes, in `notification` | **Never** (FR-ALERT-001) |
| `id:` field | Present | Absent |
| `notificationId` in `data` | Always | Never |
| Read state | Yes (FR-NOTIF-003) | No |
| Recipient offline | Replayed on next connection (FR-NOTIF-008) | **Dropped** |
| Appears in the notification center | Yes | No |

```
id: 42
event: notification
data: {"type":"FRIEND_REQUEST","notificationId":"uuid","fromUser":"alice","timestamp":"2026-06-11T13:00:00Z"}

event: alert
data: {"type":"INVITATION_ACCEPTED","user":"bob","roomId":"uuid"}

```

| Field | Description |
|-------|-------------|
| `id` | Monotonically increasing integer, globally allocated (gaps are expected — a user sees only their own subset). Used for `Last-Event-ID` continuity within a connection. **Notification events only.** |
| `event` | `notification` or `alert`. |
| `data` | JSON object. `type` identifies the kind; remaining fields are type-specific. |

An earlier revision of this document put all eight types on one `notification` event and declared
`notificationId` "always present", while simultaneously annotating two of them as "sender alert". The
split resolves that: it is the event class that was missing, not the classification.

## Notification types — persisted

| `type` | Description |
|--------|-------------|
| `FRIEND_REQUEST` | Another user sent a friend request (`notifications-invitations.md FR-FREQ-001`). Actionable; deleted when the request resolves or expires (FR-FREQ-006) |
| `FRIEND_REQUEST_ACCEPTED` | A sent friend request was accepted (`FR-FREQ-003`) |
| `FRIEND_REQUEST_DECLINED` | A sent friend request was declined (`FR-FREQ-004`) |
| `FRIEND_ADDED` | Confirmation to the user who accepted (`FR-FREQ-003`, second sentence) |
| `ROOM_INVITATION` | Host invited this user to a room (`FR-INV-001`). Actionable; deleted when the invitation resolves, the room closes (`FR-INV-008`), or it expires (`FR-INV-009`) |
| `GAME_APPROVED` | A submitted game passed review (`admin-tooling.md FR-REV-004`) |
| `GAME_REJECTED` | A submitted game was rejected; carries the operator's reason (`FR-REV-005`) |
| `BUNDLE_VALIDATION_COMPLETE` | Async game bundle validation finished (status ACTIVE or FAILED) — see [file-uploads.md](file-uploads.md) |

## Alert types — transient

| `type` | Description |
|--------|-------------|
| `INVITATION_ACCEPTED` | An invitation sent by this user was accepted (`FR-INV-006` — "the host receives an alert") |
| `INVITATION_DECLINED` | An invitation sent by this user was declined (`FR-INV-006`) |
| `SESSION_DISPLACED` | This user's session was invalidated by a login from another device (`user-accounts.md FR-SESS-004`). Delivered immediately before the stream is closed (`FR-SESS-010`) |

## Offline delivery

Catch-up is driven by a **per-row delivery flag**, not by comparing against a client-supplied
watermark. On stream open the server sends every notification for that user with
`delivered_at IS NULL`, oldest first, stamping each as it writes
([`../platform/data-model-notifications.md`](../platform/data-model-notifications.md) §1).

This replaces "replay everything created after the user's last seen event ID", which is unsound under
concurrency: `event_seq` is assigned at `INSERT` but becomes visible at `COMMIT`, so two overlapping
transactions can commit out of order. A client that has seen 101 would never be sent 100, and nothing
would record that it was missed. A per-row predicate has no such window — the flag is a property of
the row, not a comparison against a moving watermark.

Alerts are not replayed at all. There is no undelivered alert; if nobody was listening, it did not
happen.

**`Last-Event-ID` is honoured but is not the mechanism.** On a brief reconnect the browser sends it
automatically and the server may use it to avoid re-sending within the same session's window;
correctness does not depend on it, and a client that never sends one loses nothing.

**Delivery is at-least-once at best.** SSE has no acknowledgement, so `delivered_at` is stamped when
the bytes are written to the emitter and a connection that dies mid-write loses a notification now
marked delivered. That is acceptable because the stream is an accelerator, not the system of record:
the notification center (`FR-NOTIF-001`) and the unread badge (`FR-NOTIF-002`) read the table
directly, so anything the push missed appears at the next panel open. Clients deduplicate on
`notificationId`, so the opposite error — a redelivery — is invisible.

## Keepalive

A periodic comment (`:\n\n`) is sent every 30 seconds to prevent proxy and load balancer timeouts on idle connections.

## Implementation

Spring MVC `SseEmitter` (or reactive `Flux<ServerSentEvent>` if the notification path uses Spring WebFlux). An in-memory `NotificationEmitterRegistry` stores active emitters keyed by user ID. The notification dispatch service looks up the emitter and writes to it on event creation. When no emitter is registered for a user (offline), the notification is persisted only.

Connection cleanup: when a client disconnects, the emitter's `onCompletion` and `onTimeout` callbacks remove it from the registry.
