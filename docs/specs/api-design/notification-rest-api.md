# Notification REST API

The HTTP surface for the notification center: `notifications-invitations.md` FR-NOTIF-001…009. The
real-time push half of the same feature — the SSE stream, the two event classes, and why alerts have
no REST surface at all — is [sse-notifications.md](sse-notifications.md); this document covers only
what the notification center reads and mutates over plain HTTP.

Realizes `notifications-invitations.md` FR-NOTIF-001…009.

## Related

| Document | What it supplies |
|---|---|
| [rest-conventions.md](rest-conventions.md) | Status codes, the `/api/notifications/{id}` ownership predicate (`notification.user_id = principal` → `404`), the principal-scoped collection rule |
| [pagination-filtering-sorting.md](pagination-filtering-sorting.md) | The offset-pagination envelope and the total-ordering requirement this list's default sort follows |
| [sse-notifications.md](sse-notifications.md) | The two event classes, the notification `type` catalogue, and why alerts never appear here |
| [../platform/data-model-notifications.md](../platform/data-model-notifications.md) | `notification`'s columns and indexes — `notification_user_recent_idx`, `notification_unread_idx`, `notification_seq_key` |
| [room-invitation-rest-api.md](room-invitation-rest-api.md) | The nearest consumer: assumes `GET /api/notifications` is where a `ROOM_INVITATION` notification is read, without itself defining it |

---

## 1. Endpoints

| Method | Path | Auth | Success | Requirements |
|---|---|---|---|---|
| `GET` | `/api/notifications` | Session | `200` | FR-NOTIF-001, FR-NOTIF-009 |
| `GET` | `/api/notifications/unread-count` | Session | `200` | FR-NOTIF-002 |
| `PATCH` | `/api/notifications/{id}` | Session, owner only | `200` | FR-NOTIF-003 |
| `POST` | `/api/notifications/read-all` | Session | `204` | FR-NOTIF-004 |
| `DELETE` | `/api/notifications/{id}` | Session, owner only | `204` | FR-NOTIF-005 |

Five endpoints. The stream (`GET /api/notifications/stream`) is `sse-notifications.md`'s, not
repeated here.

## Authorization

`rest-conventions.md` §*Authorization and Ownership* already names the single-resource predicate —
`notification.user_id = principal`, `404` on mismatch, existence never confirmed — and the
principal-scoping rule for the collection (`WHERE user_id = :principal`, never a client-supplied
filter). Both apply unchanged to every endpoint below.

---

## 2. `GET /api/notifications` — list

Standard `pagination-filtering-sorting.md` query params (`page`, `size`). No filter or sort params are
exposed — the notification center shows one principal-scoped, always-newest-first stream, not a
queryable collection, and `notifications-invitations.md` names no other ordering.

**Default and only sort:** `ORDER BY created_at DESC, notification_id DESC` — `created_at` per
`notification_user_recent_idx`, `notification_id` as the primary-key tiebreaker
`pagination-filtering-sorting.md`'s total-ordering rule requires (two rows can share a `created_at`
timestamp; `event_seq` is not used here because it does not track `created_at` under concurrent
commits — the exact property `data-model-notifications.md` §1 gives as the reason `delivered_at`
exists instead of sequence arithmetic).

### Response

```json
{
  "content": [
    {
      "notificationId": "9c1e…",
      "type": "ROOM_INVITATION",
      "payload": { "roomId": "…", "hostUsername": "alice", "gameName": "Chess" },
      "createdAt": "2026-09-14T10:00:00Z",
      "readAt": null
    }
  ],
  "pagination": { "page": 1, "size": 25, "totalElements": 3, "totalPages": 1 }
}
```

`readAt` is `null` for an unread notification, otherwise the timestamp FR-NOTIF-003's transition
wrote. `payload` is rendered as plain text by the client (`input-validation.md`'s output-encoding
rules, per `data-model-notifications.md` §1) — never as markup.

**This is the only read path.** Opening the list does not implicitly mark anything read — FR-NOTIF-003
ties the transition to the user clicking or tapping a specific notification, not to it entering view.

---

## 3. `GET /api/notifications/unread-count` — badge

```json
{ "unreadCount": 3 }
```

`SELECT count(*) FROM notification WHERE user_id = :principal AND read_at IS NULL`, served by
`notification_unread_idx`. A dedicated endpoint rather than a field folded into §2's envelope because
the bell badge (`platform-views.md` VW-NAV-005) is visible, and must be populated, before the
notification center panel is ever opened — `shell-architecture.md` §7 calls for the count to refresh
"on panel open and on each pushed notification", the second of which has no list request to piggyback
on.

---

## 4. `PATCH /api/notifications/{id}` — mark read

```http
PATCH /api/notifications/9c1e…
Content-Type: application/json

{ "read": true }
```

Sets `read_at = now()` if currently `NULL`; a no-op, `200` with the unchanged resource, if already
read — the guarded one-way update `data-model-notifications.md` §1 describes (FR-NOTIF-003: "once
read, it cannot become unread"). `{ "read": false }` is rejected with `422`: there is no operation
that un-reads a notification for this endpoint's absolute-value `PATCH` semantics to set.

### Response

```json
{ "notificationId": "9c1e…", "type": "ROOM_INVITATION", "payload": { … }, "createdAt": "…", "readAt": "2026-09-14T10:05:00Z" }
```

Same shape as a single §2 list item.

---

## 5. `POST /api/notifications/read-all` — mark all as read

No request body. `UPDATE notification SET read_at = now() WHERE user_id = :principal AND read_at IS
NULL`. `POST`, not a collection-level `PATCH`, because — as with `POST /api/auth/logout`
(`rest-conventions.md`) — the caller is not naming an addressable resource, only invoking an action
over an implicit set. `204`, always, whether or not any row was actually unread.

---

## 6. `DELETE /api/notifications/{id}` — delete

FR-NOTIF-005: "permanently delete any individual notification... irreversible." Deletes the row
outright — no soft-delete or tombstone, matching §5's "irreversible" and the absence of any undo
affordance in `platform-views.md`.

**`204` whether or not a matching row exists**, per `rest-conventions.md`'s general `DELETE`
idempotency rule and the same pattern `room-invitation-rest-api.md` §3 and `social-rest-api.md` §6
already use for this shape: a client racing the FR-NOTIF-006 retention purge, or double-clicking
Delete after the first response was lost, gets the same terminal state either way.

**Deleting an actionable notification does not touch its subject.** A `ROOM_INVITATION` or
`FRIEND_REQUEST` notification's subject (`room_invitation`, `friend_request`) is untouched by this
endpoint — only the reverse direction cascades (`data-model-notifications.md` §1). Deleting the
notification while leaving the invitation or request pending is deliberate: FR-NOTIF-005 lets a player
clear their center without forfeiting an action they can still take from the room or friends UI.

---

## 7. Errors

Beyond the standard `rest-conventions.md` set: `404` (`{id}` not found or not owned, §*Authorization*),
`422` (`PATCH` body sets `read: false`).

## 8. What is deliberately absent

- **No `POST` to create a notification.** Every row is written by a server-side event producer
  (`IMP-M1-09`'s friend-request transactions, `IMP-M2-12`'s invitation send, the admin review flow) —
  never by a client request. This surface is read-and-mutate-state-only.
- **No filter or sort query params on §2.** See §2 — the center is one fixed-order stream, not a
  queryable list.
- **No bulk delete.** FR-NOTIF-005 is stated per-notification; nothing asks for a "clear all," and
  §5's mark-all-read already covers the one bulk action the requirements name.

---

## 9. Requirements traceability

| Requirement | Realized by |
|---|---|
| FR-NOTIF-001 | §2 |
| FR-NOTIF-002 | §3 |
| FR-NOTIF-003 | §4 |
| FR-NOTIF-004 | §5 |
| FR-NOTIF-005 | §6 |
| FR-NOTIF-006 | Not this document — the retention purge job (`platform-operations.md` FR-JOB-013, `IMP-M5-03`'s own `notification_purge_idx` clause) |
| FR-NOTIF-007/008 | Not this document — `sse-notifications.md` |
| FR-NOTIF-009 | §2 |
