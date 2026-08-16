# Platform Data Model — Notifications and Invitations

## Scope

The relational schema behind the notification center and platform room invitations: the persisted
notification, its delivery and read state, the room invitation it may point at, and the reason alerts
have no table at all.

Sources:
[`../../requirements/notifications-invitations.md`](../../requirements/notifications-invitations.md),
[`../api-design/sse-notifications.md`](../api-design/sse-notifications.md),
[`../../requirements/admin-tooling.md`](../../requirements/admin-tooling.md) FR-REV-004/005.

Conventions are those of [`data-model.md`](data-model.md) *Convention*.

**The distinction this schema has to hold is alert versus notification.** An **alert** is transient,
never persisted, and shown once (FR-ALERT-001). A **notification** is durable, appears in the
notification center, and has read state (FR-NOTIF-003). Only the second has a table. Several
messages the corpus currently routes as notifications are alerts by that definition, and §4 lists
them.

---

## 1. `notification`

```sql
CREATE TABLE notification (
  notification_id    uuid PRIMARY KEY,
  event_seq          bigint GENERATED ALWAYS AS IDENTITY,
  user_id            uuid        NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
  type               text        NOT NULL,
  payload            jsonb       NOT NULL DEFAULT '{}'::jsonb,

  friend_request_id  uuid        NULL REFERENCES friend_request(request_id) ON DELETE CASCADE,
  invitation_id      uuid        NULL,   -- FK added after §2 creates the table

  created_at         timestamptz NOT NULL DEFAULT now(),
  delivered_at       timestamptz NULL,
  read_at            timestamptz NULL,

  CONSTRAINT notification_single_subject_ck CHECK (
    (friend_request_id IS NULL) OR (invitation_id IS NULL)
  )
);

CREATE UNIQUE INDEX notification_seq_key   ON notification (event_seq);
CREATE INDEX notification_user_recent_idx  ON notification (user_id, created_at DESC);
CREATE INDEX notification_unread_idx       ON notification (user_id) WHERE read_at IS NULL;
CREATE INDEX notification_undelivered_idx  ON notification (user_id, event_seq)
  WHERE delivered_at IS NULL;
CREATE INDEX notification_purge_idx        ON notification (created_at)
  WHERE friend_request_id IS NULL AND invitation_id IS NULL;

CREATE INDEX notification_friend_request_idx ON notification (friend_request_id)
  WHERE friend_request_id IS NOT NULL;
CREATE INDEX notification_invitation_idx     ON notification (invitation_id)
  WHERE invitation_id IS NOT NULL;
```

**The last two exist because PostgreSQL does not index the referencing side of a foreign key.** It
creates an index for the primary key it points *at*, never for the column doing the pointing — so
without these, every cascade in this schema is a sequential scan of the largest table in it. The
FR-FREQ-005 expiry job deleting 500 stale requests would fire the referential-integrity trigger 500
times, each one scanning `notification` end to end. Since §1's entire argument is that these cascades
*are* the deletion mechanism, an unindexed cascade would make the mechanism the slowest thing in the
platform.

`notification_seq_key` is not one of those. Identity columns are not implicitly unique in PostgreSQL
— a sequence restart or an `OVERRIDING SYSTEM VALUE` insert can duplicate one — and the SSE `id:`
field must be unique for `Last-Event-ID` to mean anything. No query needs it; it is an assertion.

### The subject foreign key is what makes a notification actionable

FR-FREQ-002 and FR-INV-003 give two notification types inline Accept/Decline actions. Those actions
operate on an underlying object — a friend request or a room invitation — that has its own lifecycle.
Rather than a generic `subject_type`/`subject_id` pair, the two possibilities are two nullable
foreign keys with `ON DELETE CASCADE`, and `notification_single_subject_ck` allows at most one.

This is not decoration. It is the mechanism that resolves the lifecycle coupling defect described in
[`data-model-social.md`](data-model-social.md) §2:

- FR-SOC-005 (cancel) — deleting the request deletes the recipient's notification. No second
  statement, no missed path.
- FR-SOC-006/007 (accept/decline) — the same.
- FR-FREQ-005 (30-day expiry) — the expiry job deletes requests; notifications follow.
- FR-INV-008 (room closed) — deleting the room's invitations deletes their notifications.

And it produces a clean rule for the generic retention purge: `notification_purge_idx` is **partial on
having no subject**, so the FR-NOTIF-006 purge can only ever remove notifications whose meaning is
self-contained. An actionable notification is removed by its subject and by nothing else. Without
that predicate, the 30-day purge (FR-JOB-002, keyed on `created_at`) and the request expiry
(keyed on `friend_request.expires_at`) are two clocks on one object, and the recipient of a
long-lived request loses the ability to act on it from their bell while it is still listed in their
Pending tab (FR-SOC-014).

**Outcome notifications deliberately have no subject.** FR-FREQ-003/004 notify the sender that their
request was accepted or declined — at the exact moment the request row is deleted. Giving those
notifications a foreign key to the request would cascade them out of existence on creation. They are
informational, self-contained in `payload`, and outlive the object they describe. The presence of a
subject foreign key is therefore a precise marker: **subject present ⇒ actionable and coupled;
subject absent ⇒ informational and independently retained.**

### `delivered_at` is how offline delivery works, and it replaces sequence arithmetic

FR-NOTIF-008 requires notifications generated while a user is offline to be delivered on their next
session. `sse-notifications.md` currently implements that by replaying "events created after the
user's last seen event ID". That is fragile in a way that only shows up under concurrency: `event_seq`
is assigned at `INSERT` but becomes *visible* at `COMMIT`, so two overlapping transactions can commit
out of sequence order. A client that has seen 101 will never be sent 100, and 100 is not resent
because nothing records that it was missed.

`delivered_at` records the fact directly. On stream open the server sends every row for that user
`WHERE delivered_at IS NULL ORDER BY event_seq`, stamping each as it writes; catch-up is a query over
`notification_undelivered_idx` and needs no client state at all. Out-of-order commits are irrelevant
because the predicate is a property of the row, not a comparison against a moving watermark.

`event_seq` is retained as the SSE `id:` field so `Last-Event-ID` remains meaningful *within* a live
connection, and as a total order for replay. It is a **global** identity column, not a per-user
counter: `sse-notifications.md` describes the id as "monotonically increasing per user", which a
global sequence satisfies (with gaps) and which a per-user counter would buy at the price of a
serialization point on every notification write.

**Delivery is at-least-once at best, and the notification center is the backstop.** SSE has no
acknowledgement, so `delivered_at` is stamped when the bytes are written to the emitter, and a
connection that dies mid-write loses a notification that is now marked delivered. That is acceptable
precisely because the stream is an accelerator, not the system of record: FR-NOTIF-001's center and
FR-NOTIF-002's unread badge read this table over `notification_unread_idx`, so anything the push
missed appears at the next panel open or badge refresh. Clients also deduplicate on
`notification_id`, so the reverse error — a redelivery — is invisible.

### Read state is one-way, and the index is partial

FR-NOTIF-003 makes read a terminal state ("once read, it cannot become unread"). `read_at` is
therefore only ever written `NULL → now()`, by a guarded update that is a no-op on the second call.
FR-NOTIF-004's mark-all is the same statement without the `notification_id` predicate.

`notification_unread_idx` is partial on `read_at IS NULL` because FR-NOTIF-002's badge is a count of
that subset and nothing else scans it. A full index on `(user_id, read_at)` would be dominated by
read rows that no query wants.

FR-NOTIF-009's paginated list uses `notification_user_recent_idx`, which is total: the center shows
read and unread together.

### `payload` is typed by convention, not by schema

Each `type` implies a payload shape — `FRIEND_REQUEST` carries the sender's username,
`ROOM_INVITATION` the room and host, `GAME_REJECTED` the rejection reason. Those shapes are the wire
contract of `sse-notifications.md` and are documented there; the column is `jsonb` so adding a type
is not a migration. The payload is rendered as text and never as markup — the notification center is
not the game log, and
[`../api-design/input-validation.md`](../api-design/input-validation.md)'s output-encoding rules
apply unchanged.

---

## 2. `room_invitation`

```sql
CREATE TABLE room_invitation (
  invitation_id     uuid PRIMARY KEY,
  room_id           uuid        NOT NULL REFERENCES room(room_id) ON DELETE CASCADE,
  inviter_user_id   uuid        NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
  invitee_user_id   uuid        NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
  created_at        timestamptz NOT NULL DEFAULT now(),
  expires_at        timestamptz NOT NULL,

  CONSTRAINT room_invitation_self_ck CHECK (inviter_user_id <> invitee_user_id)
);

CREATE UNIQUE INDEX room_invitation_pair_key ON room_invitation (room_id, invitee_user_id);
CREATE INDEX room_invitation_invitee_idx ON room_invitation (invitee_user_id);
CREATE INDEX room_invitation_inviter_idx ON room_invitation (inviter_user_id);
CREATE INDEX room_invitation_expiry_idx  ON room_invitation (expires_at);

ALTER TABLE notification ADD CONSTRAINT notification_invitation_fk
  FOREIGN KEY (invitation_id) REFERENCES room_invitation(invitation_id) ON DELETE CASCADE;
```

The foreign key is attached here rather than inline in §1 because `notification` is declared first
and PostgreSQL will not reference a table that does not exist yet. The same idiom appears in
[`data-model-catalog.md`](data-model-catalog.md) §2 for `game.active_version_id`. Both could
alternatively be resolved by ordering the baseline
([`../deployment/schema-migrations.md`](../deployment/schema-migrations.md) §5 does order them
correctly), but a document that only works when read alongside a migration file in another repository
is a document that can be broken by an edit nobody made to it.

`room_invitation_inviter_idx` covers the second referencing leg for the same reason as the two
indexes in §1: a guest hard-delete cascades on `inviter_user_id`, and `room_invitation_pair_key`
leads with `room_id` so it cannot serve that lookup.

### `expires_at` is what keeps its notification purgeable

An invitation needs a deadline of its own, and the reason is not tidiness — it is that without one,
the notification pointing at it can never be purged.

`notification_purge_idx` is partial on having no subject (§1), so FR-JOB-002's 30-day sweep skips
every actionable notification by design: an actionable message must be removed by its subject, not by
a clock that knows nothing about whether the subject is still live. That rule closes for
`FRIEND_REQUEST` only because `friend_request` carries `expires_at` and the expiry purge job
(`platform-operations.md` FR-JOB-013), so every request is guaranteed a deleter. That job is the sole
deleter for `room_invitation` too, and it scans `room_invitation_expiry_idx`. Give `room_invitation` no deadline and the guarantee fails on its second
leg: an ignored invitation to a room that never closes — an In-Progress room with connected players
never trips FR-JOB-007d's idle sweep — keeps its notification alive forever, in direct violation of
FR-NOTIF-006, FR-JOB-002 and FR-RET-001, all three of which state the 30-day purge with no exception.

The window is `turnbase.retention.notification`, the same value the notification purge uses, and
sharing it is deliberate: two clocks on one object is the defect this whole section exists to avoid,
and the invitation's deadline arriving first — by however little — is what makes the subject the
thing that expires and the notification merely the thing that follows.

This is recorded as `notifications-invitations.md` FR-INV-009. Written absolutely, at insert, with
the database clock, for the reason `friend_request.expires_at` is
([`data-model-social.md`](data-model-social.md) §2): a configuration change must not move a deadline
that is already running.

**This is the friends-only platform invitation of FR-INV-001, and it is not the invite link.** The
shareable join link is `room.invite_code` ([`data-model.md`](data-model.md) §1), which is a single
code per room, shared outside the platform (FR-LINK-001), usable by anyone who holds it. The two are
called "invite" in the UI and are unrelated objects: one is a row per invited friend, the other a
column on the room.

**Pending rows only, like `friend_request`.** Accepting or declining deletes the row; so does the room
closing. Nothing reads a resolved invitation — FR-INV-006's sender feedback is an alert (§4), and
`notifications-invitations.md` explicitly puts invitation status tracking in the lobby UI out of
scope. Keeping only pending rows is what makes `room_invitation_pair_key` a plain unique index, which
in turn makes "you have already invited this player" a constraint rather than a check.

**FR-INV-008 is an explicit delete at closure, not the cascade.** The `ON DELETE CASCADE` on `room_id`
fires when the room *row* is purged — seven days after closure (FR-JOB-009) — which is far too late
for a requirement that says a pending invitation to a closed room must be deleted. Closure therefore
deletes the room's invitations in the transaction that sets `state = 'CLOSED'`, and the notifications
follow through §1's cascade. The foreign-key cascade remains as the backstop for a room deleted by
any other path.

**That rule has five producers and no constraint can catch a path that forgets it.**
`room.state = 'CLOSED'` is written by FR-XFER-002, FR-HDISC-003, FR-JOB-007c, FR-JOB-007d and
FR-LIFE-004 — the five reasons enumerated in [`data-model.md`](data-model.md) §1's closure-reason
table, two of them owned by sweep duties in [`room-lifecycle.md`](room-lifecycle.md) §5. A prose rule
stated once in a document none of those five paths is written from is the shape of last session's
`ownerless_since`: correct, and with no owner.

Two things address it. The closure-reason table in `data-model.md` §1 now names the invitation delete
as part of what closure owes, so it is stated where the producers are enumerated rather than only
here. And `expires_at` above means that a forgotten path degrades to a delayed cleanup rather than a
permanent leak — the invitation and its notification are collected at the retention window instead of
at closure. Neither is enforcement; the second is the difference between a bug and an unbounded one.

FR-INV-008's second sentence — a stale invitation acted on before deletion fails gracefully — is
handled at join time, not here; the room state check that FR-INV-005 already performs covers it.

**Invitations do not reserve slots** (FR-INV-003), so there is no relationship between this table and
`room_participant`, and `FR-INV-007`'s multiple simultaneous pending invitations need no constraint:
the single-room rule is enforced at join (`game-rooms.md` FR-JOIN-007), not at invite.

**Guests are excluded by transitivity, not by a constraint.** FR-INV-002 restricts invitations to
friends of the host, and guests cannot have friends
([`data-model-social.md`](data-model-social.md) §1). No `kind` check is needed here because there is
no path to a row naming a guest that does not first require a `friendship` row that cannot exist.

---

## 3. Notification types

| `type` | Class | Subject | Source |
|---|---|---|---|
| `FRIEND_REQUEST` | actionable | `friend_request_id` | FR-FREQ-001 |
| `FRIEND_REQUEST_ACCEPTED` | informational | — | FR-FREQ-003 (to the sender) |
| `FRIEND_REQUEST_DECLINED` | informational | — | FR-FREQ-004 (to the sender) |
| `FRIEND_ADDED` | informational | — | FR-FREQ-003 (confirmation to the accepter) |
| `ROOM_INVITATION` | actionable | `invitation_id` | FR-INV-001 |
| `GAME_APPROVED` | informational | — | FR-REV-004 |
| `GAME_REJECTED` | informational | — | FR-REV-005 (carries the reason) |
| `BUNDLE_VALIDATION_COMPLETE` | informational | — | `file-uploads.md` |

`GAME_APPROVED` and `GAME_REJECTED` are required by FR-REV-004 and FR-REV-005 — "the developer
receives a platform notification" — and are absent from `sse-notifications.md`'s type table. They are
added here and to that spec.

---

## 4. Alerts have no table, and three current "notifications" are alerts

FR-ALERT-001 defines an alert as transient and explicitly "never stored or shown in the notification
center". There is consequently no `alert` table, no delivery record, and no retention rule: an alert
that misses its recipient is simply gone, which is the semantics the requirement asks for.

Three messages that `sse-notifications.md` currently lists as notification types fail the
notification test:

| Message | Why it is an alert |
|---|---|
| `INVITATION_ACCEPTED` | FR-INV-006 says the host "receives an **alert**". A persisted notification would put a one-off acknowledgement in the center with unread state and a 30-day life. |
| `INVITATION_DECLINED` | Same requirement, same reasoning. |
| `SESSION_DISPLACED` | FR-SESS-004 is an error response, not a notification. Persisting it would leave a permanent record addressed to a session that has just been invalidated — and the recipient cannot read their notification center, because their session is gone. |

They remain on the SSE stream; they move to a second event class. The stream therefore carries
`event: notification` (persisted, `notificationId` present, deliverable offline) and `event: alert`
(transient, no id, dropped if nobody is listening) — which is also what makes the offline-replay rule
of §1 well-defined, since replaying a stale "your invite was accepted" from three days ago is not a
behaviour any requirement asks for.

**`sse-notifications.md` already half-knows this**: its type table annotates both invitation events
as "sender alert" and cites FR-INV-006 for them. What that spec is missing is not the
classification — it is the *event class*, which is why those rows sit in a table whose contract says
"`notificationId` is always present". The correction is structural, not a change of mind.

---

## 5. What is deliberately absent

- **No `alert` table.** §4.
- **No per-user sequence counter.** §1. A global identity column with gaps satisfies every use.
- **No delivery-attempt or retry table.** SSE has no acknowledgement to retry against; the durable
  view is the notification center, and `delivered_at` is a single stamp rather than a work queue.
- **No notification preferences or mute table.** Out of scope in `notifications-invitations.md`.
- **No `room_invitation` response history.** §2.
- **No FK from `notification` to `game`.** `GAME_APPROVED` / `GAME_REJECTED` name the game in
  `payload`; coupling them to the catalog row would cascade a developer's rejection notice out of
  existence if the game were later deleted, and the reason is the whole content of the message.
- **No notifications for guests in practice.** Every type in §3 requires a capability guests do not
  have (friends, invitations, uploads), so a guest's center is always empty even though VW-NAV-005
  shows them the bell. That is a UI observation, not a schema gap — `notification.user_id` has no
  `kind` restriction, and adding one would forbid a future guest-addressable message for no benefit.

---

## 6. Requirements traceability

| Requirement | Realized by |
|---|---|
| FR-NOTIF-001/009 | `notification_user_recent_idx` |
| FR-NOTIF-002 | `notification_unread_idx` |
| FR-NOTIF-003/004 | `read_at`, one-way guarded update |
| FR-NOTIF-005 | row delete |
| FR-NOTIF-006 / FR-JOB-002 | `notification_purge_idx`, partial on having no subject |
| FR-NOTIF-007/008 | `delivered_at`, `notification_undelivered_idx` |
| FR-ALERT-001 | no table (§4) |
| FR-INV-001/002 | `room_invitation` |
| FR-INV-003/007 | no slot reservation, no cross-room constraint |
| FR-INV-006 | alert class (§4) |
| FR-INV-008 | explicit delete at closure (`data-model.md` §1) + cascade backstop |
| FR-INV-009 | `room_invitation.expires_at`, `room_invitation_expiry_idx` |
| FR-FREQ-001…005 | §1 subject foreign keys, §3 type table |
| FR-REV-004/005 | `GAME_APPROVED`, `GAME_REJECTED` |
| FR-LINK-001 | `room.invite_code`, not this table |
| NFR-SEC-001 (notifications) | `user_id` scoping on every query; no cross-user read path |
