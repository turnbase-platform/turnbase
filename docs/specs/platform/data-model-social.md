# Platform Data Model — Friendships and Friend Requests

## Scope

The relational schema behind the social graph: friendships, pending friend requests, and the
guest-exclusion and cap rules that constrain both.

Source: [`../../requirements/social-friends.md`](../../requirements/social-friends.md), with the
notification coupling in
[`../../requirements/notifications-invitations.md`](../../requirements/notifications-invitations.md)
FR-FREQ-001…005.

Conventions are those of [`data-model.md`](data-model.md) *Convention*. `app_user` is defined in
[`data-model-accounts.md`](data-model-accounts.md).

---

## 1. `friendship`

```sql
CREATE TABLE friendship (
  user_id_low   uuid NOT NULL,
  user_id_high  uuid NOT NULL,
  kind_low      text NOT NULL DEFAULT 'REGISTERED',
  kind_high     text NOT NULL DEFAULT 'REGISTERED',
  created_at    timestamptz NOT NULL DEFAULT now(),

  PRIMARY KEY (user_id_low, user_id_high),
  CONSTRAINT friendship_order_ck CHECK (user_id_low < user_id_high),
  CONSTRAINT friendship_low_registered_ck  CHECK (kind_low  = 'REGISTERED'),
  CONSTRAINT friendship_high_registered_ck CHECK (kind_high = 'REGISTERED'),
  CONSTRAINT friendship_low_fk  FOREIGN KEY (user_id_low,  kind_low)
    REFERENCES app_user (user_id, kind) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT friendship_high_fk FOREIGN KEY (user_id_high, kind_high)
    REFERENCES app_user (user_id, kind) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX friendship_high_idx ON friendship (user_id_high);
```

### One row per friendship, with the pair ordered

A friendship is defined as **mutual and bidirectional** (`social-friends.md` Definitions), and
FR-SOC-011 makes removal "immediate and mutual — both users are removed from each other's friend list
simultaneously". A two-row model (`A→B` and `B→A`) can represent a half-friendship, which is not a
state the requirements admit; every write would then need both rows and every read would need to
check that both exist. Storing one row with `user_id_low < user_id_high` makes the mutuality
**structural**: there is no way to write half of it, and FR-SOC-011 is one `DELETE`.

The cost is that "my friends" is not a single-column scan. It is:

```sql
SELECT CASE WHEN user_id_low = :me THEN user_id_high ELSE user_id_low END AS friend_id
FROM friendship WHERE user_id_low = :me OR user_id_high = :me;
```

which is why `friendship_high_idx` exists — the primary key covers the `user_id_low` leg, and without
a second index the `user_id_high` leg is a sequential scan. At the FR-SOC-009 cap of 50 friends per
user the result set is trivial; the index is about not scanning the whole table to find it.

FR-SOC-010 sorts the list alphabetically, case-insensitively, by username. That is an `ORDER BY
lower(u.username)` over at most 50 joined rows and needs no index of its own.

### Guest exclusion is a foreign key, not a service-layer check

FR-SOC-020 and `user-accounts.md` FR-GUEST-007 forbid guests from having friends. The usual
implementation is a check in the friend-request service, which is one place a future caller can
forget. Referencing the redundant `app_user (user_id, kind)` unique index
([`data-model-accounts.md`](data-model-accounts.md) §1) and pinning `kind` to `'REGISTERED'` with a
local `CHECK` moves the rule into the schema: an attempt to befriend a guest fails on the foreign
key, from any code path, including a migration or a manual fix-up.

`ON DELETE CASCADE` implements FR-SOC-012 for the *hard*-delete path (a purged guest, which by this
constraint has no rows here anyway) and is a backstop for the soft-delete path, which deletes these
rows explicitly ([`data-model-accounts.md`](data-model-accounts.md) §5).

### The cap is not a constraint

FR-SOC-009 caps a user at 50 friends and NFR-SOC-SCALE-001 requires that number to be configurable
without a code change. Both facts rule out a database constraint: the cap is a predicate over a
*count* of rows matching either of two columns, and a configurable limit cannot live in DDL. It is
enforced in the application, inside the transaction that creates the friendship, by counting both
legs.

The cap applies asymmetrically, and the schema has to allow that. FR-SOC-009 says an incoming request
is still **created and recorded** when the recipient is at cap — only *acceptance* is blocked. So
`friend_request` has no cap-related constraint at all, and the check runs at accept time on the
accepting user only. A sender at cap is blocked from *sending* (FR-SOC-009 first sentence), which is
checked on insert.

---

## 2. `friend_request`

```sql
CREATE TABLE friend_request (
  request_id      uuid PRIMARY KEY,
  sender_id       uuid NOT NULL,
  recipient_id    uuid NOT NULL,
  sender_kind     text NOT NULL DEFAULT 'REGISTERED',
  recipient_kind  text NOT NULL DEFAULT 'REGISTERED',
  created_at      timestamptz NOT NULL DEFAULT now(),
  expires_at      timestamptz NOT NULL,

  CONSTRAINT friend_request_self_ck CHECK (sender_id <> recipient_id),
  CONSTRAINT friend_request_sender_registered_ck    CHECK (sender_kind    = 'REGISTERED'),
  CONSTRAINT friend_request_recipient_registered_ck CHECK (recipient_kind = 'REGISTERED'),
  CONSTRAINT friend_request_sender_fk FOREIGN KEY (sender_id, sender_kind)
    REFERENCES app_user (user_id, kind) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT friend_request_recipient_fk FOREIGN KEY (recipient_id, recipient_kind)
    REFERENCES app_user (user_id, kind) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE UNIQUE INDEX friend_request_pair_key ON friend_request (sender_id, recipient_id);
CREATE INDEX friend_request_recipient_idx   ON friend_request (recipient_id, created_at DESC);
CREATE INDEX friend_request_expiry_idx      ON friend_request (expires_at);
```

### The table holds pending requests only

There is no `resolution` column and no resolved rows. Accepting deletes the request and inserts the
friendship in one transaction; declining, cancelling and expiring delete it. Nothing in the
requirements reads a resolved request: FR-SOC-013's Pending tab shows unresolved requests only,
FR-SOC-003's duplicate check asks whether a request is *pending*, and the accept/decline
notifications (FR-FREQ-003/004) are self-contained messages that outlive the request by design.

Keeping only pending rows is what lets `friend_request_pair_key` be a plain unique index rather than
a partial one over a resolution predicate — and a plain unique index is what makes FR-SOC-003's
duplicate prevention a constraint instead of a race between two concurrent sends.

A **reverse** request (FR-SOC-004) is not a duplicate and is not blocked by that index, which is
keyed on the ordered pair `(sender, recipient)`. `B→A` while `A→B` is pending is a distinct key, and
the handler detects the existing opposite row and auto-accepts both — deleting the pending row,
inserting the friendship, and never writing the second request at all.

The index therefore covers **one** of FR-SOC-003's three prohibitions. That requirement forbids
sending to someone you are already friends with, sending a duplicate outgoing request, and sending
when a request from them is already pending; only the second is a constraint. The first is a lookup
in `friendship` and the third is the reverse-request path above, which is not a rejection at all.
This is worth stating because the constraint is the only one of the three that survives a concurrent
double-send, and the other two need the enclosing transaction to be doing the reads.

### `expires_at` is stored, not derived

FR-FREQ-005 gives friend requests a 30-day life and NFR-SOC-SCALE-001 makes the window configurable.
Deriving expiry as `created_at + :window` at query time would mean that changing the configuration
retroactively expires — or resurrects — requests that were already created, which is a visible and
unexplainable change to a user's Pending tab. Storing the absolute deadline, written with the
database clock at insert as `now() + :window`, is the same reasoning ADR-0009 applies to grace
deadlines: the deadline is a property of the request, not of the current configuration.

`friend_request_expiry_idx` serves the expiry purge job (`platform-operations.md` FR-JOB-013). Unlike the room sweeps it is not partial — every
row in this table has a deadline, so there is no subset to narrow to.

### The request is the durable object; the notification is a pointer to it

FR-FREQ-001 delivers an incoming request *as* a notification, and FR-FREQ-005 says requests "follow
the standard 30-day notification retention policy". Read literally, that is two independently purged
objects representing one thing: the notification purge (FR-JOB-002, `created_at` based) and the
request expiry could fire at different times, leaving either an actionable notification whose request
is gone, or a request the recipient can no longer see in their bell.

The resolution — recorded in `notifications-invitations.md` FR-FREQ-006 and realised by
[`data-model-notifications.md`](data-model-notifications.md) §1 — is that the notification carries a
`subject_type`/`subject_id` pointing at `request_id`, and the request's lifecycle drives the
notification's: resolving or expiring a request deletes the notifications that reference it, in the
same transaction. The generic notification purge never removes a notification whose subject is still
live. One object, one deadline.

FR-SOC-005's "the recipient's pending notification is removed" on cancel is the same mechanism, not a
special case.

---

## 3. Interaction with `block_friend_requests`

FR-SOC-021 rejects *new* requests when the recipient has the toggle on, while "existing friendships
and already-pending requests are unaffected". The setting therefore has no representation in this
schema at all — it is read from
[`user_privacy_settings`](data-model-accounts.md#4-user_privacy_settings) at insert time and never
consulted again. Modelling it as a constraint would have exactly the wrong effect: it would
retroactively invalidate the pending rows the requirement explicitly preserves.

---

## 4. What is deliberately absent

- **No `user_block` table.** Per-user blocking and abuse reporting are out of scope in
  `social-friends.md`. The only "block" in the requirements is the global toggle above, which is a
  boolean on the privacy settings row. A per-user block table would also change the meaning of
  FR-SOC-002's search results and FR-SOC-017's Friends Only visibility, neither of which is
  specified — so the table would arrive with no rules attached.
- **No `friendship_request_history` / audit table.** Nothing reads it (§2), and it would be the
  largest table in the social schema.
- **No `mutual_friend_count` or suggestion cache.** Both are out of scope.
- **No presence or online-status column.** Out of scope; presence is per-connection state that
  belongs to the WebSocket layer, not to a durable row that would be wrong after every crash.
- **No denormalized `friend_count` on `app_user`.** The cap makes the exact count a 50-row aggregate;
  a counter would be a second source of truth for a number that must be *correct* to enforce
  FR-SOC-009, and its drift would be silent.

---

## 5. Requirements traceability

| Requirement | Realized by |
|---|---|
| FR-SOC-001/002 | `friend_request` insert; `app_user_username_trgm_idx` serves prefix search |
| FR-SOC-003 | `friend_request_pair_key` covers the duplicate-outgoing leg only; the existing-friend and pending-incoming legs are checks at insert (§2) |
| FR-SOC-004 | opposite-row detection; no second row written |
| FR-SOC-005/007/008 | row deletion; §2 notification coupling |
| FR-SOC-006 | delete request + insert `friendship`, one transaction |
| FR-SOC-009 | application count over both legs, at send and at accept |
| FR-SOC-010 | `ORDER BY lower(username)` over the joined set |
| FR-SOC-011 | single `DELETE` on `friendship` |
| FR-SOC-012 | explicit deletes ([accounts §5](data-model-accounts.md#5-erasure--what-account-deletion-actually-writes)) plus `ON DELETE CASCADE` |
| FR-SOC-020 / FR-GUEST-007 | composite FK to `app_user (user_id, kind)` + `CHECK kind = 'REGISTERED'` |
| FR-SOC-021 | read of `user_privacy_settings.block_friend_requests` at insert |
| FR-FREQ-005/006 | `friend_request.expires_at`, subject-scoped notification deletion |
