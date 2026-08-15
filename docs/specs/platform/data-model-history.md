# Platform Data Model — Game History and Statistics

## Scope

The relational schema behind the per-session record of completed games: the per-player history
entries, the session-completion record that makes recording idempotent, and the per-game counter the
statistics surfaces read.

Sources: [`../../requirements/game-history.md`](../../requirements/game-history.md),
[`../../requirements/per-game-statistics.md`](../../requirements/per-game-statistics.md),
[`../../requirements/game-contracts.md`](../../requirements/game-contracts.md) FR-OUTCOME-001…004,
[ADR-0004](../../decisions/0004-account-erasure-pseudonymization.md).

Conventions are those of [`data-model.md`](data-model.md) *Convention*.

**This schema is deliberately disconnected from the rest.** History outlives the room it was played
in (`game-history.md` CON-004), the catalog row of the game it was played on
([`data-model-catalog.md`](data-model-catalog.md) §5), and the account of the person who played it
(ADR-0004). Every one of those independences is expressed as a *missing* foreign key, and each is
argued below rather than left to look like an oversight.

---

## 1. `game_session_completion`

```sql
CREATE TABLE game_session_completion (
  session_id    uuid PRIMARY KEY,
  game_id       uuid        NOT NULL,
  game_version  text        NOT NULL,
  completed_at  timestamptz NOT NULL,
  player_count  integer     NOT NULL,
  team_count    integer     NOT NULL,
  draw          boolean     NOT NULL,
  recorded_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX game_session_completion_game_idx ON game_session_completion (game_id, completed_at DESC);
```

One row per session that ended with a `game_over` effect (FR-HIST-001, FR-STATS-001). It exists for
two reasons that a per-player table cannot serve.

**It is the idempotency key for the counter.** FR-STATS-004 requires a denormalized per-game session
counter that is only ever incremented. A bare `UPDATE game SET completed_session_count = ... + 1` is
not safe against a re-delivered `game_over`: effects reach Orchestration over a path that retries, and
the room-lifecycle design makes at-least-once the norm rather than the exception
([ADR-0010](../../decisions/0010-session-teardown-ordering.md)). Recording is therefore

```sql
INSERT INTO game_session_completion (...) VALUES (...) ON CONFLICT (session_id) DO NOTHING;
-- increment the counter and write the per-player entries only if that inserted a row
```

all in one transaction. A repeat delivery inserts nothing, increments nothing, and writes no duplicate
entries. FR-EFF-007 already says only the first `game_over` per session is honored; this is where that
becomes true across a process restart rather than only within one.

**It counts sessions that produce no history entries.** FR-STATS-003 counts a guest's completed
sessions toward per-game totals while FR-HIST-003 gives guests no history entry, so a session played
entirely by guests contributes to `completed_session_count` and to nothing else. Deriving the counter
from `game_history_entry` would silently under-count exactly those sessions — and would keep working
in every test with a registered player in it.

**`game_id` carries no foreign key.** The catalog may archive and eventually discard artifacts for a
game whose owner deleted their account ([`data-model-catalog.md`](data-model-catalog.md) §5); a
foreign key here would make that operation either fail or cascade into the statistics it is supposed
to preserve (FR-ACCT-008). The same reasoning `game-history.md` CON-004 applies to the room applies
here to the game.

**`session_id` likewise has no foreign key**, and could not: the session it names lives in the Game
Host and in Redis, and `room.active_session_id` — the only relational trace of it — is cleared at
detach and purged with the room seven days after closure (FR-JOB-009). History must survive both.

---

## 2. `game_history_entry`

```sql
CREATE TABLE game_history_entry (
  entry_id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id          uuid        NOT NULL REFERENCES game_session_completion(session_id),
  user_id             uuid        NULL REFERENCES app_user(user_id),
  subject_token       text        NULL,

  game_id             uuid        NOT NULL,
  game_name_snapshot  text        NOT NULL,
  completed_at        timestamptz NOT NULL,

  placement           integer     NOT NULL,
  team_count          integer     NOT NULL,
  draw                boolean     NOT NULL,
  player_stats        jsonb       NOT NULL DEFAULT '{}'::jsonb,
  team_stats          jsonb       NOT NULL DEFAULT '{}'::jsonb,

  pseudonymized_at    timestamptz NULL,

  CONSTRAINT ghe_placement_ck CHECK (placement >= 1 AND placement <= team_count),
  CONSTRAINT ghe_subject_ck CHECK ((user_id IS NULL) = (subject_token IS NOT NULL))
);

CREATE UNIQUE INDEX ghe_session_user_key ON game_history_entry (session_id, user_id);
CREATE INDEX ghe_user_recent_idx ON game_history_entry (user_id, completed_at DESC)
  WHERE user_id IS NOT NULL;
CREATE INDEX ghe_user_game_idx ON game_history_entry (user_id, game_id)
  WHERE user_id IS NOT NULL;
CREATE INDEX ghe_user_name_trgm_idx ON game_history_entry
  USING gin (user_id, lower(game_name_snapshot) gin_trgm_ops)
  WHERE user_id IS NOT NULL;
```

### Session-level facts are repeated on every entry, on purpose

`game_id`, `game_name_snapshot`, `completed_at`, `team_count` and `draw` are all properties of the
session and are already on the §1 row. Duplicating them is what FR-HIST-005 literally asks for
("each history entry must store: session ID, game ID, game name snapshot, session completed-at
timestamp, …"), and it is also what makes the profile History tab a single-table query:
FR-HIST-024 sorts by `completed_at` descending *within a user*, which `ghe_user_recent_idx` answers
directly, and FR-HIST-025 searches `game_name_snapshot` *within a user*, which a join would force
into a filter after the join rather than a scan of one index.

**The search index has to carry `user_id` inside it, and that costs a second extension.** A plain
`gin (lower(game_name_snapshot) gin_trgm_ops)` is not scoped by user, so the planner's only options
for `WHERE user_id = :u AND lower(game_name_snapshot) LIKE '%chess%'` are a trigram scan of *every*
user's history followed by a filter, or `ghe_user_recent_idx` followed by a filter on the name —
neither of which is the single index scan this design claims, and the first degrades with total
platform history, which is precisely what NFR-HIST-002 is written against. A GIN index over
`(user_id, lower(...) gin_trgm_ops)` does scope it, and a multi-column GIN with a scalar leading
column requires the **`btree_gin`** extension. That makes it a baseline concern rather than an
additive migration ([`../deployment/schema-migrations.md`](../deployment/schema-migrations.md) §5).

Like its two neighbours it is partial on `user_id IS NOT NULL`: §4 says pseudonymized entries surface
nowhere, and an index that still contained them would be the one place that was not true.

The duplication is safe because the table is append-only in every field but two — the erasure columns
of §4 — and the multiplier is the player count of one session, not a growth factor.

### `game_name_snapshot` is a snapshot, not a lookup

FR-HIST-006 captures the title at session completion and FR-HIST-023 renders it as plain text when
the game is soft-deleted. The snapshot is what makes both FR-HIST-025's search and FR-HIST-021's card
correct after a title change or a deletion, and it is the reason a history row remains meaningful
even if the catalog row for `game_id` is gone entirely.

`game_id` is still stored, because FR-HIST-021 links the card to `/games/:id` when the game is not
soft-deleted, and FR-STATS-021 groups by game to find the most played one. The link is rendered only
if the lookup succeeds — a missing or soft-deleted row degrades to plain text, which is the same
rendering FR-HIST-023 already specifies.

### `placement` and `team_count` are stored; the label is not

FR-HIST-010…013 derive one of "Draw", "Victory", "Defeat" or an ordinal from `draw`, `placement` and
`team_count`. The label is a pure function of three stored columns and is computed at read time. A
stored label would freeze the wording of a presentation rule into ten thousand rows and would have to
be backfilled to change "Defeat" to anything else.

`ghe_placement_ck` bounds the placement by the team count. FR-OUTCOME-003 permits multiple teams to
share a placement when `draw` is true, so the check is an upper bound, not a uniqueness constraint —
two entries in the same session may legitimately both hold `placement = 1`.

**The check must never be the thing that rejects a bad outcome, and the reason is that there is no
second attempt.** `placement` and `team_count` come straight from the game backend's structured
outcome, and FR-OUTCOME-001 bounds neither — it says only "a placement (integer, 1-based finishing
position)". A game that emits two `teamResults` with placements 1 and 3 — standard competition
ranking, a plausible bug — would fail this check, abort the whole §1 recording transaction, and
therefore write *nothing*: no completion row, no counter increment, no entries for any player.
FR-EFF-006 makes `game_over` terminal, so there is no retry that can succeed, and the session
disappears from history and from statistics alike over one malformed field.

The outcome is therefore **validated at the effect boundary**, before the transaction opens:

| Outcome | Action |
|---|---|
| Valid | Record normally (§1). |
| Structurally invalid — placement out of range, `teamResults` empty, a `playerResults` entry naming a player not in the session | Write the `game_session_completion` row and increment the counter; write **no** history entries; log ERROR with the session, game and version, and count it on a metric. |

The session did complete — the engine said so, which is all FR-STATS-001 asks — so the statistics
stay correct, and only the per-player history that was malformed to begin with is lost. Nothing
aborts, and the failure is attributable to a game rather than surfacing as a bare constraint
violation with no session context. `ghe_placement_ck` stays as the backstop it should always have
been: a constraint that fires only if the validation was skipped.

This makes `GameOutcome` validation load-bearing rather than a nicety. It is already on the proto
sweep in STATUS.md item 9, and belongs in
[`../internal-grpc/orchestration-gamehost-protocol.md`](../internal-grpc/orchestration-gamehost-protocol.md)
alongside the other inbound-effect checks.

**No `team_id`.** FR-OUTCOME-001 identifies teams by UUID, and those UUIDs are `room_team.team_id`
rows that FR-JOB-009 purges with the room. Storing them would create the dangling reference `game-history.md` CON-004
exists to prevent, and nothing in `game-history.md` reads a team identity — FR-HIST-005 asks for the
player's team's *stats map*, which is copied into `team_stats`.

### `player_stats` and `team_stats` are opaque

FR-OUTCOME-004 and `game-history.md` CON-003 both say the platform stores the stats maps and does not
interpret them.
`jsonb` rather than `json` so equal documents compare equal and duplicate keys cannot survive a
round trip; no schema, no index, and no validation beyond it being an object. FR-HIST-022 renders
each as a labelled key-value section and omits the section when the map is empty, which the
`'{}'` default makes a uniform test rather than a null check.

### `ghe_session_user_key` is the second half of idempotency

`UNIQUE (session_id, user_id)` prevents one player from receiving two entries for one session even if
the §1 guard is bypassed by a code path that writes entries directly. After erasure `user_id` becomes
NULL, and PostgreSQL treats NULLs as distinct in a unique index — so several erased players in the
same session coexist without a conflict, while live players remain constrained. That behaviour is
usually a hazard; here it is exactly the semantics wanted, and it is the reason the erasure design of
§4 needs no partial index or surrogate key to work.

---

## 3. The per-game counter and its writer

`game.completed_session_count` ([`data-model-catalog.md`](data-model-catalog.md) §1) is incremented
by exactly one statement, in the recording transaction of §1, and only when the completion row was
actually inserted:

```sql
UPDATE game SET completed_session_count = completed_session_count + 1 WHERE game_id = :g;
```

FR-STATS-004 forbids decrementing it and FR-ACCT-008 confirms account deletion must not touch it, so
there is no other writer anywhere in the platform.

**The counter is denormalized but not unverifiable.** `SELECT count(*) FROM game_session_completion
WHERE game_id = :g` is the same number, served by `game_session_completion_game_idx`, so a drift can
be detected and repaired rather than merely suspected. The drift is one-directional: `game_id` has no
foreign key, so if no `game` row matches, the `UPDATE` affects zero rows while the completion row
commits — the counter can only ever be **under** the count, never over. That is the safe direction
for a number FR-STATS-004 forbids decrementing, and it makes the check a comparison rather than a
reconciliation. That is the whole reason §1 exists as a table
rather than as a `session_id` column on a deduplication set: FR-STATS-004 demands a counter, and a
counter with no independent derivation is a number nobody can ever check.

FR-STATS-012 reads the counter, not the count — one column read on a row the detail page already
loads.

### The other statistics are queries, not columns

| Requirement | Query |
|---|---|
| FR-STATS-020 total played | `count(*) FROM game_history_entry WHERE user_id = :u` — `ghe_user_recent_idx` |
| FR-STATS-021 most played | `GROUP BY game_id ORDER BY count(*) DESC, g.title ASC LIMIT 1` — `ghe_user_game_idx`, joined to `game` for the tie-break title |
| FR-STATS-023 zero state | the same queries returning `0` / no row |

CON-001 of `per-game-statistics.md` states these are live queries with no pre-aggregation, and
FR-STATS-025 fetches them per page load. The two partial indexes are what make that hold within
NFR-STATS-002's 300 ms as the table grows; the alphabetical tie-break of FR-STATS-021 is a sort over
the handful of games one user has played, not over the catalog.

---

## 4. Erasure

On account deletion, one statement rewrites every entry belonging to the departing user:

```sql
UPDATE game_history_entry
   SET user_id = NULL, subject_token = :token, pseudonymized_at = now()
 WHERE user_id = :u;
```

`:token` is a **freshly generated random value**, minted once per erasure and stored nowhere but
these rows. The alternative — `HMAC(user_id, pepper)` — satisfies "stable" but not
"non-reversible": the user-id space is small enough to enumerate offline, so anyone holding a
database dump and the key can re-link every erased row, which is the property ADR-0004 explicitly
rules out. Only a construction that discards its input is non-reversible, and randomness is that
construction. Stability comes from minting the token once and applying it in a single `UPDATE`, not
from deriving it.

`ghe_subject_ck` makes the two states exclusive: an entry has either a live `user_id` or a
`subject_token`, never both and never neither. Without it a partially applied erasure — a live
`user_id` alongside a token — would look pseudonymized to one reader and identified to another.

**`user_id` has no `ON DELETE` action, deliberately.** A hard `DELETE` of an `app_user` row raises a
foreign-key violation rather than silently taking history with it. Registered accounts are never hard
deleted (they become tombstones — [`data-model-accounts.md`](data-model-accounts.md) §5) and guests
never have history (FR-HIST-003), so this constraint should never fire. That is the point: it is
there to catch the future change that would otherwise destroy opponents' records without a single
test failing.

`pseudonymized_at` records that erasure happened, which ADR-0004's "requires an audit trail" needs
and which no other column can supply once the identity is gone.

**`subject_token` currently has no reader**, and that is worth admitting. Nothing selects it, groups
by it, or renders it: cross-player history queries are out of scope in `game-history.md`, and a
pseudonymized entry appears on no profile. Its only live function is to satisfy `ghe_subject_ck`,
which exists to police it. ADR-0004 asks for a *stable* token, and stability only matters to a
consumer that groups by it — so the column is provision for a requirement that does not yet exist.
It is kept because minting it at erasure costs nothing and re-deriving it later is impossible: once
the `user_id` is gone, there is no input from which a token could be reconstructed to group rows that
were erased before the column existed.

**Pseudonymized entries surface nowhere.** They no longer match `ghe_user_recent_idx` (partial on
`user_id IS NOT NULL`), so the profile queries of §3 cannot return them, and the account itself is a
tombstone (FR-ACCT-009). They continue to contribute to `game_session_completion` and therefore to
`completed_session_count`, which is FR-ACCT-008 and FR-STATS-004 holding.

---

## 5. What is deliberately absent

- **No room reference.** `game-history.md` CON-004. Rooms are purged at 7 days (FR-RET-006); history
  is retained indefinitely (FR-RET-003).
- **No foreign key to `game`.** §1. History must not be able to block a catalog operation, nor be
  broken by one.
- **No spectator entries.** FR-HIST-002 and FR-STATS-002 exclude spectators from history and from
  personal statistics; there is no row to write and no `role` column to distinguish.
- **No entries for sessions that ended any other way.** `game-history.md` CON-001: a room closed mid-game, or a session
  failed back to Lobby by reconciliation (FR-JOB-007c), produces no `game_over` and therefore no row
  in either table. Neither the counter nor the history moves.
- **No win/loss/draw aggregate columns.** Out of scope in `per-game-statistics.md`; derivable from
  `placement` and `draw` if that changes.
- **No `started_at`.** Nothing displays a session duration, and the value would have to be carried
  across a session that may have been adopted by a different instance mid-game.
- **No retention or purge job.** FR-RET-003 retains history indefinitely, which is the one table in
  the platform with no purge.

---

## 6. Requirements traceability

| Requirement | Realized by |
|---|---|
| FR-HIST-001 / `game-history.md` CON-001 | rows written only on `game_over` |
| FR-HIST-002/003 | one entry per registered player; none for guests or spectators |
| FR-HIST-004/005 | columns copied verbatim from the structured outcome |
| FR-HIST-006/023 | `game_name_snapshot` |
| FR-HIST-010…013 | `draw`, `placement`, `team_count`; label derived at read |
| FR-HIST-022 | `player_stats`, `team_stats` |
| FR-HIST-024/025/026 | `ghe_user_recent_idx`, `ghe_user_name_trgm_idx` |
| FR-HIST-030 / ADR-0004 | §4 |
| FR-STATS-001 | `game_session_completion` |
| FR-STATS-003 | guest-only sessions counted in §1, absent from §2 |
| FR-STATS-004 / FR-STATS-012 | `game.completed_session_count`, incremented once per §1 insert |
| FR-STATS-020/021/023 | §3 query table |
| FR-ACCT-008 | counter untouched by erasure |
| NFR-HIST-002 | the three partial indexes on `game_history_entry` (§2) |
| FR-OUTCOME-001 (validation) | outcome checked at the effect boundary; `ghe_placement_ck` as backstop (§2) |
| FR-EFF-007 | `ON CONFLICT (session_id) DO NOTHING` |
