# Platform Data Model — Rooms, Participants and Durable Work

## Scope

The relational schema behind room lifecycle: rooms, participants, teams, room ownership, and the two
durable work tables that make cross-store side effects survive a crash. This is the **first**
relational schema document in the corpus; before it, four independent designs each invented their own
column names for the same concepts.

It covers only what room lifecycle requires. The rest of the relational schema lives in sibling
documents that share this document's conventions:
[accounts](data-model-accounts.md), [social](data-model-social.md), [catalog](data-model-catalog.md),
[history & statistics](data-model-history.md), [notifications](data-model-notifications.md).
`app_user`, referenced below by `room.host_user_id` and `room_participant.user_id`, is defined in the
accounts document; `game`, referenced by `room.game_id`, in the catalog document.

**Authority.** PostgreSQL is authoritative for everything in this document. Redis holds live game
state, routing and leases ([`../game-host/game-host-internals.md`](../game-host/game-host-internals.md)
§13); nothing in this document may be reconstructed from Redis, because Redis is a single non-HA
instance with an accepted loss window (ADR-0001).

**Convention.** Types are PostgreSQL. Column names are normative — specs and requirements refer to
these concepts by name, and the point of this document is that they agree. Timestamps are
`timestamptz` and are always written with the **database** clock (`now()`), never an application
clock; see [ADR-0009](../../decisions/0009-grace-deadline-durability.md).

**Auto-incrementing integer keys use `bigint GENERATED ALWAYS AS IDENTITY`, never `serial` or
`bigserial`.** This holds across all six schema documents. PostgreSQL has recommended the identity
form since version 10: `bigserial` is a macro that creates a sequence the column merely *defaults*
to, so the sequence is separately grantable, separately droppable, and does not follow the column
through a `CREATE TABLE … LIKE`. The two idioms produce an equally working schema, which is why an
inconsistency here survives review — the reason to pick one is that a baseline containing both
leaves a transcriber unable to tell whether the difference was meant.

The one deliberate exception is `guest_serial_seq`
([`data-model-accounts.md`](data-model-accounts.md) §1), which is a **standalone sequence** rather
than a column default. It is declared explicitly because FR-GUEST-002 needs it to start at 0.

**Authority over the migrations.** These six documents are normative for **names** and for
**reasons**. They are not what the database is: the Flyway migrations in the `turnbase-platform`
submodule are, and when the two disagree the migration wins
([ADR-0011](../../decisions/0011-schema-migrations.md) §4). A schema change is incomplete until both
are updated, and the DDL here is the design of the change rather than a transcript of it — see
[`../deployment/schema-migrations.md`](../deployment/schema-migrations.md).

---

## 1. `room`

```sql
CREATE TABLE room (
  room_id             uuid PRIMARY KEY,
  game_id             uuid        NOT NULL REFERENCES game(game_id),
  game_version        text        NOT NULL,
  host_user_id        uuid        NULL REFERENCES app_user(user_id),
  visibility          text        NOT NULL,       -- PUBLIC | FRIENDS_ONLY | INVITE_ONLY
  state               text        NOT NULL,       -- LOBBY | IN_PROGRESS | CLOSED
  spectating_enabled  boolean     NOT NULL DEFAULT false,
  invite_code         text        NULL UNIQUE,
  parameters          jsonb       NOT NULL DEFAULT '{}'::jsonb,

  version             bigint      NOT NULL DEFAULT 0,
  active_session_id   uuid        NULL,

  owner_instance_id   text        NULL,
  owner_epoch         bigint      NOT NULL DEFAULT 0,
  ownerless_since     timestamptz NULL,
  migration_window_expires_at timestamptz NULL,

  last_activity_at    timestamptz NOT NULL DEFAULT now(),
  closed_at           timestamptz NULL,
  closed_reason       text        NULL,           -- see § Closure reasons
  reconcile_flagged_at timestamptz NULL,

  created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX room_open_state_idx ON room (state) WHERE state <> 'CLOSED';
CREATE INDEX room_idle_lobby_idx ON room (last_activity_at) WHERE state = 'LOBBY';
CREATE INDEX room_closed_purge_idx ON room (closed_at) WHERE state = 'CLOSED';
CREATE INDEX room_active_session_idx ON room (active_session_id)
  WHERE active_session_id IS NOT NULL;
CREATE INDEX room_open_game_idx ON room (game_id, game_version) WHERE state <> 'CLOSED';
```

**`version`** is the per-room event version carried by every WebSocket delta
([`../api-design/room-websocket.md`](../api-design/room-websocket.md)). It is **persisted before the
delta is published**; without that, an adopting instance re-issues versions clients have already seen
and clients discard them silently.

**`owner_epoch`** is the fencing token, incremented in Redis by the claim script on each change of
ownership and written here at adoption. Every mutation commits
`WHERE room_id = :id AND version = :expected AND owner_epoch = :myEpoch`. The **version cannot fence
on its own**: it is room-scoped, and a stale owner holding a fixed `expected` value is eventually
*reached* by the legitimate owner advancing densely from below, at which point the stale CAS matches.
The epoch only moves at a change of tenure, so a stale owner's value is unreachable (ADR-0008).

**`host_user_id` is nullable.** When the host's own reservation is resolved while another human's is
still outstanding, the room survives — a human still holds a slot — but there is nobody connected to
transfer the role to, so it legitimately has no host until someone reconnects. Modelling this as null
is the honest representation; the alternative is a dangling reference to a released participant. This
state was not covered by FR-HDISC-003 as originally written, which addressed the host's *own* grace
window and stopped at the point where the host is released; the rule is now stated there explicitly
rather than left to be inferred from a schema decision.

**`owner_instance_id` / `ownerless_since`** mirror the Redis ownership key. Redis holds the claim
because the claim must be atomic and cheap; Postgres holds the mirror because reconciliation must be
able to *find* rooms whose owner is gone without scanning Redis, and because a Redis flush must not
erase the knowledge that a room exists. The Redis key is the lock; this column is the index.

`ownerless_since` is stamped by a **graceful release** (`room-lifecycle.md` §1.3), which is its only
writer. It exists because the two ways of losing an owner leave different traces: a crash leaves
`owner_instance_id` naming a dead instance, whereas a clean drain leaves it null — and a null column
with no timestamp is indistinguishable from a room that was never owned. `owner_epoch` is **never**
reset by a release; it must advance monotonically across the ownerless gap or the next tenure's fence
would compare against a recycled value.

**`migration_window_expires_at`** holds the FR-HDISC-004 window opened at adoption
(`room-lifecycle.md` §1.4 step 7) and cleared by the sweep duty that acts on its expiry (§5.1 duty 3).
It is a persisted absolute timestamp rather than an in-JVM timer for exactly the reason grace
deadlines are (ADR-0009): the window exists to survive an owner-instance loss, so holding it in the
memory of an instance that can itself vanish would void it during the one event it was written for.

**`reconcile_flagged_at`** implements the two-strike rule (FR-JOB-008): a divergence must be observed
on two consecutive runs before repair. It is persisted rather than held in memory precisely so a
restart cannot reset the count and turn a repair into a permanent no-op.

**`last_activity_at`** is touched on every room mutation and every participant connect. It is the
second leg of the idle-Lobby predicate (FR-JOB-007d): "zero connected participants" alone is unsafe
because a crash can leave connection flags stale, but a genuinely live room cannot have an old
`last_activity_at` regardless of what the flags say.

### Closure reasons

`closed_reason` is a closed set, surfaced to clients as `ROOM_CLOSED.reason`:

| Value | Meaning | Source |
|---|---|---|
| `NO_PLAYERS_REMAINING` | Host left explicitly with no other human present | FR-XFER-002 |
| `GRACE_EXPIRED_NO_HUMAN` | Deferred closure elapsed with no human connected | FR-HDISC-003 |
| `ACCOUNT_DELETED` | Host's account was deleted | FR-LIFE-004 |
| `IDLE_TIMEOUT` | Lobby room with no participants past the idle window | FR-JOB-007d |
| `SESSION_UNRECOVERABLE` | In Progress room whose session state is gone and could not be failed back | FR-JOB-007c |

**Every one of these five paths owes the same two side effects**, and they are listed here because
this is the only place the producers appear together. Closure must, in the transaction that sets
`state = 'CLOSED'`:

1. record the owed session teardown, if a session is attached (FR-XFER-005, §4.1); and
2. delete the room's `room_invitation` rows (FR-INV-008), whose notifications then cascade
   ([`data-model-notifications.md`](data-model-notifications.md) §2).

The second is easy to miss because a foreign-key cascade already exists for it — but that cascade
fires at FR-JOB-009's purge, seven days later, not at closure.

`IDLE_TIMEOUT` and `SESSION_UNRECOVERABLE` are the two platform-initiated causes named by FR-LIFE-007
and are kept distinct rather than collapsed into one "reconciliation" value: they mean different
things to the player — an abandoned lobby was reclaimed, versus a game was lost — and only the second
is evidence of a defect.

---

## 2. `room_participant`

One row per user who has ever occupied a slot in the room. Rows are **not deleted** on departure —
`left_at` marks release — so that a slot's history is auditable and so a re-join is distinguishable
from a first join.

```sql
CREATE TABLE room_participant (
  room_id               uuid        NOT NULL REFERENCES room(room_id) ON DELETE CASCADE,
  user_id               uuid        NOT NULL REFERENCES app_user(user_id),
  role                  text        NOT NULL,      -- PLAYER | SPECTATOR
  team_id               uuid        NULL REFERENCES room_team(team_id),
  joined_at             timestamptz NOT NULL DEFAULT now(),
  join_order            integer     NOT NULL,

  connection_count      integer     NOT NULL DEFAULT 0,
  ready                 boolean     NOT NULL DEFAULT false,

  grace_reservation_id  uuid        NULL,
  grace_expires_at      timestamptz NULL,

  left_at               timestamptz NULL,
  leave_reason          text        NULL,          -- LEFT | KICKED | GRACE_EXPIRED | EARLY_RELEASE
                                                   -- | ROOM_CLOSED | GAME_ENDED
  lost_announced_at     timestamptz NULL,

  PRIMARY KEY (room_id, user_id)
);

CREATE INDEX room_participant_grace_due_idx
  ON room_participant (grace_expires_at)
  WHERE grace_expires_at IS NOT NULL AND left_at IS NULL;

CREATE INDEX room_participant_unannounced_idx
  ON room_participant (room_id)
  WHERE left_at IS NOT NULL AND lost_announced_at IS NULL;
```

`ON DELETE CASCADE` is deliberate and load-bearing: the GRMP prototype needed a scheduled job purely
to collect orphaned participant rows, which is permanent penance for a missing constraint. With the
cascade, FR-JOB-009's purge of closed rooms needs no participant logic at all.

**Three total row states**, and every query in the lifecycle spec keys off them:

| State | Predicate |
|---|---|
| Present | `left_at IS NULL AND grace_reservation_id IS NULL` |
| In grace | `left_at IS NULL AND grace_reservation_id IS NOT NULL` |
| Released | `left_at IS NOT NULL` |

Note that a participant in grace still has `left_at IS NULL`. This is what makes the last-human test
a single predicate: a room stays viable while *any* human still holds a reserved slot, which is
exactly FR-HDISC-003.

**A released row is reused on re-join, never left to collide with a new one (`IMP-GATE-50`).**
Because the primary key is `(room_id, user_id)` and rows are never deleted, a caller re-joining a
room they previously departed — voluntary leave, kick, or grace expiry — already owns a row for that
key; a plain `INSERT` violates it. The join transaction (`room-rest-api.md` §5 step 6) must `INSERT
... ON CONFLICT (room_id, user_id) DO UPDATE` in this case: reinitialize every per-membership column
(`joined_at = now()`, `join_order`, `role`, `team_id`, `connection_count = 0`, `ready = false`) and
clear every departure column (`left_at`, `leave_reason`, `lost_announced_at`, `grace_reservation_id`,
`grace_expires_at` all to `NULL`). The conflict path fires only when the existing row is genuinely
Released (`left_at IS NOT NULL`) — a live row never reaches step 6 at all, since step 2 of that
transaction already turns a request from a current participant into a no-op before any insert is
attempted.

**`grace_reservation_id`** is a fresh UUID per disconnect and is the CAS token for resolving a
reservation. It is used rather than comparing `grace_expires_at` because two disconnects can produce
an identical deadline, and rather than a boolean because a stale actor must be able to prove *which*
reservation it was acting on. It doubles as the correlation id in logs and metrics.

**`EARLY_RELEASE` is a distinct `leave_reason`, not a reuse of `LEFT` or `GRACE_EXPIRED`.** It records
FR-EXPIRY-004: the player's reservation was voided because they joined another room, before their
deadline elapsed. Neither neighbour fits — they did not leave *this* room deliberately, and the grace
period did not run out — and the value surfaces in `PLAYER_LOST` and in history, so leaving it to an
implementer's judgement would produce a user-visible inconsistency between two rooms closed the same
way.

**`connection_count`** is a refcount, not a flag. A user may hold several concurrent connections
(`../api-design/rate-limiting.md` caps them per user); the grace period opens when it reaches zero
and ends when it leaves zero (FR-GRACE-006). A boolean would emit a disconnect the moment a player
closed one of several tabs.

**`lost_announced_at`** exists for one case: a player holding a reservation joins another room, and
the instance handling that join is not the one that owns the old room. It can perform the release
(a database write) but cannot broadcast into the old room's topic, because there is no cross-instance
event path (ADR-0002). The column records that the release happened but the announcement has not, so
the owning instance emits it on its next sweep. Without it the event is simply lost the first day the
platform runs more than one instance.

It is written by **every** path that sets `left_at`, not only by grace expiry: `now()` when the acting
instance owns the room and broadcasts immediately, null when it does not. A null value is therefore
the assertion "this departure is owed an announcement", and `room_participant_unannounced_idx` (§5)
is the index that makes finding those cheap. The sweep duty that consumes it is narrowed on
`leave_reason` as well, as a backstop against a writer that forgets — see `room-lifecycle.md` §5.1.

---

## 3. `room_team`

```sql
CREATE TABLE room_team (
  team_id          uuid PRIMARY KEY,
  room_id          uuid    NOT NULL REFERENCES room(room_id) ON DELETE CASCADE,
  template_index   integer NOT NULL,   -- index into the game's teamTemplates array
  team_index       integer NOT NULL,   -- ordinal within that template, for "{name} N" display
  configured_size  integer NOT NULL,   -- within [size.min, size.max]
  UNIQUE (room_id, template_index, team_index)
);
```

Instantiated at room creation as `count.min` teams per declared template, each at
`configuredSize = size.max` (`game-rooms.md` FR-TEAM-012). `template_index` and `team_index` together
give the deterministic tie-break that auto-assignment requires (FR-TEAM-005: fewest members, then
template order, then team index).

---

## 4. Durable work: two tables, not one

Both tables exist for the same reason — a state change in PostgreSQL and a side effect in another
process cannot commit atomically — and both are written **inside** the transaction that makes the
state change. They are kept separate because their drain semantics differ in every respect that
matters:

| | `session_teardown` | `game_input_outbox` |
|---|---|---|
| Retry horizon | Indefinite, with backoff | Bounded attempts, then dead-letter |
| Failure meaning | The Game Host is unreachable; try again | The session is gone; the game may be unrecoverable |
| `NOT_FOUND` response | **Success** (idempotent no-op) | **Conditional** — see below |
| Ordering constraint | None | Must not outlive its session |

**`NOT_FOUND` on the game-input drain is terminal only while the session is still attached to a
room** — that is, only if `SELECT 1 FROM room WHERE active_session_id = :sessionId` returns a row.
If it does not, the session has been *retired* from its room, the absent session is the expected
outcome, and the outbox row is dropped as a benign no-op.

Without this condition the rule is actively harmful on the game-end path: game end detaches the
session but returns the room to **Lobby**, so an in-flight `player_left` returning `NOT_FOUND`
afterwards would close a perfectly healthy room — possibly one that has already started a rematch.

**The test is deliberately *not* "was a teardown ever recorded", which cannot be answered.**
`session_teardown` rows are deleted on confirmed termination (§4.1), so a completed teardown leaves no
trace and is indistinguishable from one that never existed — the moment the re-drive succeeds, the
history the rule depended on is gone. `room.active_session_id` is the durable form of the same fact,
needs no schema addition, and stays correct after FR-JOB-009 purges the room: no row means no
attachment, which is the benign case. Only a `NOT_FOUND` for a session a room still claims as active
means the session was lost rather than retired, and only that case hands the room to reconciliation
(FR-JOB-007c), which fails it back to Lobby rather than closing it outright. The lookup is served by
`room_active_session_idx` (§1).

Merging them would require a discriminator column plus a branch on that discriminator at every step
of the drain — which is two tables wearing one table's clothes.

### 4.1 `session_teardown`

```sql
CREATE TABLE session_teardown (
  session_id      uuid PRIMARY KEY,
  room_id         uuid        NOT NULL,
  reason          text        NOT NULL,     -- maps 1:1 onto proto TerminationReason
  requested_at    timestamptz NOT NULL DEFAULT now(),
  attempts        integer     NOT NULL DEFAULT 0,
  next_attempt_at timestamptz NOT NULL DEFAULT now(),
  last_error      text        NULL
);

CREATE INDEX session_teardown_due_idx ON session_teardown (next_attempt_at);
```

**Keyed by `session_id`, never by room.** A room outlives its sessions: a game ends, the room returns
to Lobby, and a rematch starts a new session. A room-scoped flag would be overwritten by the next
session's start, silently dropping the previous session's owed teardown — which is precisely the bug
class this table exists to prevent ([ADR-0010](../../decisions/0010-session-teardown-ordering.md)).

`room_id` carries **no foreign key**, deliberately: a teardown may still be owed after its room has
been purged (FR-JOB-009), and the debt is to the Game Host, not to the room.

Insertion uses `ON CONFLICT (session_id) DO NOTHING`, so two concurrent closers cannot conflict.
Rows are deleted only on confirmed termination. A row older than 15 minutes raises FR-ALERT-007.

### 4.2 `game_input_outbox`

```sql
CREATE TABLE game_input_outbox (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id    uuid        NOT NULL,
  sequence      bigint      NULL,        -- allocated once, before first dispatch
  payload       jsonb       NOT NULL,
  created_at    timestamptz NOT NULL DEFAULT now(),
  attempts      integer     NOT NULL DEFAULT 0,
  dispatched_at timestamptz NULL,        -- stamped on ACK, never on attempt
  last_error    text        NULL
);

CREATE INDEX game_input_outbox_pending_idx ON game_input_outbox (session_id, id)
  WHERE dispatched_at IS NULL;
```

Carries the `player_left` notification produced when a grace period expires (FR-EXPIRY-002). Without
it, a crash between committing the slot release and calling the Game Host loses the notification
permanently, and the game stalls waiting for a player the platform has already removed.

**The `sequence` column is what makes redelivery safe, and it is not optional.** The Game Host
deduplicates by `sequence`, but a `sequence` is normally allocated by Orchestration *at enqueue*
(a Redis `INCR`). A re-drained outbox row would therefore be enqueued under a **new** sequence, the
Game Host would see a second distinct input, and `player_left` would be applied twice — the replay
path never engaging. The drain instead allocates the sequence once and persists it before
dispatching:

```sql
UPDATE game_input_outbox SET sequence = :seq WHERE id = :id AND sequence IS NULL;
```

Every subsequent attempt reuses the stored value, so the Game Host's existing at-most-once rule
applies and a repeat really is a replay. Allocating at drain rather than inside the expiry
transaction avoids burning sequence numbers on a rollback.

**`dispatched_at` is stamped on acknowledgement, never on attempt**, and the distinction is
load-bearing rather than pedantic. `room-lifecycle.md` §4 step 5 discards a detached session's rows
`WHERE dispatched_at IS NULL`, so this column decides which rows survive a teardown. Stamped on
*attempt*, a row whose RPC timed out would be marked dispatched without ever being delivered, escape
the discard, outlive its session, and later draw a `NOT_FOUND` for a session no longer attached to any
room. Stamped on ACK, a row is either confirmed delivered or still a candidate for both retry and
discard, which is the property the rest of the design assumes. The in-flight record lives in
`attempts` and `last_error`, which are written on every failure regardless of who observed it — the
inline attempt at detach time as well as the sweep's re-drive.

**Interaction with teardown — the one ordering rule.** When a teardown is recorded for a session, any
undelivered rows for that session are discarded in the same transaction. A `player_left` describing a
session that is being torn down is moot, and delivering it would produce a `NOT_FOUND` that the drain
would then have to interpret as an unrecoverable game — closing a room that is already closing. The
`(session_id, id)` index exists to make that discard cheap.

---

## 5. Index rationale

Every index above is partial where the working set is small, because these tables are dominated by
rows in a terminal state:

- `room_participant_grace_due_idx` spans only players *currently in grace*, not the participant
  table. At any plausible scale this is tens of rows, so the 5-second deadline sweep is an index-only
  scan of a nearly empty index rather than a table scan.
- `room_participant_unannounced_idx` spans only released participants whose departure has not been
  announced — the deferred tails of `room-lifecycle.md` §5.1 duty 2. Its steady-state size is zero,
  because the sweep's success is what removes a row from it. It is partial on the *opposite*
  predicate to `room_participant_grace_due_idx`, and both are needed: the 5-second sweep runs two
  queries per tick and neither would otherwise have an index.
- `room_open_state_idx` and `room_idle_lobby_idx` exclude closed rooms, which accumulate for 7 days
  (FR-RET-006) and are never of interest to the sweeps.
- `session_teardown_due_idx` is over a table whose steady-state size is zero.
- `room_active_session_idx` spans only rooms with a live session, and answers the one question the
  game-input drain asks on `NOT_FOUND` (§4): is this session still attached to a room? Partial,
  because a room without an active session can never be the answer.
- `room_open_game_idx` spans only non-closed rooms and serves the two questions the catalog asks of
  the room table: how many players are currently in rooms for a game (FR-GDET-005), and whether a
  superseded game version may be discarded (`game-catalog.md` FR-GAME-011). Both are
  questions about *live* rooms only, and the 7-day tail of closed rooms would otherwise dominate the
  scan.

---

## 6. What is deliberately absent

- **No `connected` boolean.** Superseded by `connection_count`; a boolean cannot represent a user
  with two tabs open.
- **No stored `grace_remaining_seconds`.** Derived as `grace_expires_at − now()` at read time. A
  stored countdown would be wrong the moment the process holding it stopped ticking, which is the
  entire failure this design removes.
- **No room foreign key on game history.** History is keyed by session and outlives the room
  (FR-RET-006, `game-history.md` CON-004). A foreign key here would make the closed-room purge
  either destroy history or fail.
- **No `is_host` flag on the participant.** The host is `room.host_user_id`; a flag would be a second
  source of truth for a single-valued fact.
- **No AI participant representation.** `room_participant` is keyed `(room_id, user_id)` against
  `app_user`, so it models humans only. The wire protocol carries an `aiPlayers` array
  ([`../api-design/room-websocket.md`](../api-design/room-websocket.md)) that is always empty in v1,
  because the AI player interface and its execution environment are both deferred
  (`game-contracts.md` OQ-002, `platform-architecture.md` *Out of Scope*). Adding AI later is a new
  table rather than a column: a synthetic `app_user` row per AI would put bots into friend search,
  statistics and the guest purge. That is a design note, not a decision made here.
