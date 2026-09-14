# Room Invitation REST API

The HTTP surface for the friends-only platform invitation of `notifications-invitations.md`
FR-INV-001…009 and `game-rooms.md` FR-HOST-001 — a host inviting a specific friend into their room.
This is a different mechanism from the invite link (`room-rest-api.md` §3.1, §8, which defers the
notification mechanism here): the link is a single reusable code shared outside the platform; this is
a row per invited friend, delivered as a `ROOM_INVITATION` notification.

Realizes `notifications-invitations.md` FR-INV-001…009 and `game-rooms.md` FR-HOST-001.

## Related

| Document | What it supplies |
|---|---|
| [rest-conventions.md](rest-conventions.md) | Status codes, the `Origin` check, self-scoped routing |
| [room-rest-api.md](room-rest-api.md) | §5 `POST /api/rooms/{roomId}/participants` — the join endpoint accept resolves to; §8's deferral of this surface here |
| [sse-notifications.md](sse-notifications.md) | The `ROOM_INVITATION` notification type and the `INVITATION_ACCEPTED`/`INVITATION_DECLINED` alert types this feature writes/publishes |
| [../platform/data-model-notifications.md](../platform/data-model-notifications.md) | `room_invitation`, and why it and not the room's `ON DELETE CASCADE` is what deletes a stale invitation |
| [social-rest-api.md](social-rest-api.md) | The nearest sibling: send/accept/decline over a request-row-plus-notification, same shape |
| [notification-rest-api.md](notification-rest-api.md) | Where a received `ROOM_INVITATION` notification is actually read — `GET /api/notifications` |
| [../../requirements/game-rooms.md](../../requirements/game-rooms.md) | FR-HOST-001 |
| [../../requirements/notifications-invitations.md](../../requirements/notifications-invitations.md) | FR-INV-001…009 |

---

## 1. Endpoints

| Method | Path | Auth | Success | Requirements |
|---|---|---|---|---|
| `POST` | `/api/rooms/{roomId}/invitations` | Session, host only | `201` | FR-HOST-001, FR-INV-001, FR-INV-002, FR-INV-007 |
| `DELETE` | `/api/rooms/{roomId}/invitations/me` | Session, invitee only | `204` | FR-INV-003 (decline half), FR-INV-006 |

Two endpoints. **Accept has no endpoint of its own** — §4.

## Authorization

`rest-conventions.md` §*Authorization and Ownership* carries both predicates: the send endpoint
re-checks `room.host_user_id = principal`; the decline endpoint is self-scoped by `me`, the same
pattern as `/api/rooms/{roomId}/participants/me`.

---

## 2. `POST /api/rooms/{roomId}/invitations` — send

```http
POST /api/rooms/{roomId}/invitations
Content-Type: application/json

{ "inviteeUsername": "bob" }
```

**No room-ownership claim.** `room-rest-api.md`'s claim/lease/affinity-header mechanism fences writes
to `room.version` and the pod holding the room's live WebSocket connections; `room_invitation` has
neither. An ordinary `@Transactional` `SELECT ... FOR UPDATE` on the `room` row is enough to serialize
against a concurrent host transfer or closure — no cross-pod coordination, no `X-TurnBase-Room-Instance`
header on either endpoint below.

### Evaluation order, inside one transaction

1. `SELECT ... FOR UPDATE` the room row; `room.host_user_id = principal`. Not the host → `403`.
2. `room.state <> 'CLOSED'` — inviting into a room that no longer exists is meaningless. Closed or
   missing → `404`.
3. Resolve `inviteeUsername` to a `REGISTERED`, non-deleted user. Miss → `404`.
4. Self-invite → `422`.
5. No `friendship` row for `(principal, invitee)` → `422` (FR-INV-002). The same direct-SQL check
   `room-rest-api.md` §3's `visible()` FRIENDS_ONLY term already runs against the `friendship` table —
   this package already reads across the `social` schema boundary this way (`RoomRepository#isVisible`),
   so this is that same established pattern, not a new one.
6. `room_invitation_pair_key (room_id, invitee_user_id)` already holds a row for this pair → `200`
   idempotently returns the existing row rather than `409` — a host clicking Invite twice on the same
   friend is not an error, and FR-INV-007 already guarantees multiple invitations to *different*
   friends coexist; nothing says a second click on the same one should fail.
7. Otherwise: insert `room_invitation` with `expires_at = now() + turnbase.retention.notification`
   (FR-INV-009, sharing the notification retention window — `data-model-notifications.md` §2), write a
   `ROOM_INVITATION` notification to the invitee with `invitation_id` set and payload `{"roomId":
   ..., "hostUsername": ..., "gameName": ...}` (`sse-notifications.md`'s type table names the type;
   the payload shape is this document's to fix, since no other document states it).

### Response

```json
{ "invitationId": "9c1e…", "inviteeUsername": "bob", "createdAt": "…", "expiresAt": "…" }
```

`201` with no `Location` — there is no `GET /api/rooms/{roomId}/invitations/{id}` (§6); the resource
is reached through the invitee's notification center, not this API.

---

## 3. `DELETE /api/rooms/{roomId}/invitations/me` — decline

FR-INV-003's decline action. Deletes the caller's own pending `room_invitation` row for this room
(`(room_id, invitee_user_id) = (roomId, principal)`), which cascades to delete the notification
(`data-model-notifications.md` §2). Publishes an `INVITATION_DECLINED` alert (`sse-notifications.md`)
to the inviting host (FR-INV-006) — dropped silently if the host is offline, per FR-ALERT-010; alerts
are never queued for later delivery.

**`204` whether or not a matching row exists** — the same idempotency rule `social-rest-api.md` §6
gives `DELETE /api/friend-requests/{id}`: a client racing an expiry job, or double-clicking Decline
after the first response was lost, gets the same terminal state either way. No alert is published on
the no-op path — an alert with no invitation behind it has nothing true to report.

**Ignoring an invitation is not this endpoint.** FR-INV-003's third option, doing nothing, is simply
never calling this route or `POST …/participants`; the row (and its notification) is removed only by
this action, by acceptance (§4), by the room closing (FR-INV-008, `IMP-M2-09`'s `detachSession`), or by
its own FR-INV-009 expiry (`platform-operations.md`'s notification-retention purge job).

---

## 4. Acceptance is the ordinary join, not a route here

FR-INV-004: "the player is taken to the room view... Room joining follows the rules in game-rooms
FR-JOIN-003 through FR-JOIN-008" — that is `room-rest-api.md` §5, `POST
/api/rooms/{roomId}/participants`, called with no change to its own request shape. This document adds
one clause to that endpoint's transaction, not a new endpoint:

**On a successful join** (the response the caller receives is `201`, not a rejection), the handler
additionally: deletes the caller's pending `room_invitation` row for this room if one exists (a no-op
`DELETE` when the caller joined via the invite link or the room list instead of an invitation), and,
only if a row was deleted, publishes an `INVITATION_ACCEPTED` alert to that invitation's
`inviter_user_id` (FR-INV-006). Both happen inside the same transaction as the join, under the same
room lock — no second write path, no window where a join can succeed while its invitation lingers.

**On a failed join** (FR-INV-005 — no slot, no spectating, room closed), the invitation row is left
untouched. The join failing is not the same fact as the invitation being resolved, and leaving the row
pending is what lets the player retry, or accept later if the room's state changes, without the host
re-sending anything. `data-model-notifications.md` §2's "accepting... deletes the row" describes the
row's fate on a join that actually succeeds — the only "accept" this corpus defines.

**Multiple pending invitations to the *same* room don't exist** — `room_invitation_pair_key` is unique
on `(room_id, invitee_user_id)` — so "the caller's pending row for this room" is unambiguous. FR-INV-007
("accepting one does not decline others") is about invitations to *other* rooms, which this clause
does not touch; only the joined room's own row is deleted.

---

## 5. Errors

Beyond the standard `rest-conventions.md` set: `403` (not host, §2 step 1), `404` (room missing/closed,
invitee username unknown), `422` (self-invite, not friends).

## 6. What is deliberately absent

- **No `GET` listing endpoint for sent or received invitations.** A received invitation is read from
  the notification center (`FR-NOTIF-001`, `GET /api/notifications` —
  [`notification-rest-api.md`](notification-rest-api.md) §2); a sent one has no UI surface in
  this corpus's scope (`notifications-invitations.md` *Out of Scope*: "Invitation status tracking in
  the room lobby UI"). Adding a list route here would be the first reader of `room_invitation` outside
  the notification it produced, for a view nothing asks for.
- **No accept endpoint.** §4.
- **No update/resend.** An invitation has no mutable field; resending is declining then re-inviting,
  or simply inviting again (§2 step 6's idempotent re-send).

---

## 7. Requirements traceability

| Requirement | Realized by |
|---|---|
| FR-HOST-001 | §2 — host-only send, `ROOM_INVITATION` notification |
| FR-INV-001 | §2 |
| FR-INV-002 | §2 step 5 |
| FR-INV-003 | §2 (accept/decline actions exist); §3 (decline); §4 (accept) |
| FR-INV-004 | §4 |
| FR-INV-005 | §4 — failed join leaves the invitation pending |
| FR-INV-006 | §3, §4 — `INVITATION_ACCEPTED`/`INVITATION_DECLINED` alerts |
| FR-INV-007 | §2 step 6 note; §4's "same room only" note |
| FR-INV-008 | `IMP-M2-09`'s `detachSession`, not this document — cross-referenced in §3 |
| FR-INV-009 | §2 step 7 — `expires_at` at insert |
