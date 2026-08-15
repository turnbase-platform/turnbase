# Flow 06 — Game Over, History, Rematch

The game ends. History and statistics are written, the room returns to Lobby, the players start a
second game, and the *first* session is torn down somewhere in the middle of all that. The overlap is
the interesting part.

**Components:** four browsers, Platform Monolith, PostgreSQL, Redis, Game Host.

---

## A. `game_over`

| # | Component | Action |
|---|---|---|
| 1 | Espresso | `onAction` returns effects ending with `game_over` |
| 2 | Game Host | Serializes: opaque results payload for the game FE, **structured outcome** for the platform |
| 3 | Orchestration | Processes effects **in order** (`FR-RESP-004`); anything after `game_over` in the same list is processed before the session terminates (`FR-EFF-006`) |
| 4 | Orchestration | Second `game_over` in a later response → **ignored** (`FR-EFF-007`) |

The structured outcome is `teamResults` (team id, 1-based placement, optional stats map),
`playerResults` (player id, optional stats map), and `draw`. The game FE never sees it — it gets the
separate opaque payload.

---

## B. Validate before writing

The outcome is validated **at the effect boundary**, before any transaction opens:

| Outcome | Action |
|---|---|
| Valid | Record (§C) |
| Structurally invalid — placement outside `[1, teamCount]`, empty `teamResults`, a `playerResults` entry naming a non-participant | Write the completion row and increment the counter; write **no** history entries; ERROR log naming session, game and version; metric |

This exists because the alternative is unrecoverable. `ghe_placement_ck` would reject a bad placement
and abort the *entire* recording transaction — no completion row, no counter increment, no entries
for any player — and `FR-EFF-006` makes `game_over` terminal, so no retry can succeed. One bad
integer from one game would erase a completed session from history *and* statistics.

The session did complete; the engine said so, which is all `FR-STATS-001` asks. So statistics stay
correct and only the malformed per-player history is lost. The CHECK stays as a backstop that should
never fire.

---

## C. Recording — one transaction

```sql
INSERT INTO game_session_completion (session_id, game_id, game_version, completed_at,
                                     player_count, team_count, draw)
VALUES (…) ON CONFLICT (session_id) DO NOTHING;
-- only if that inserted a row:
UPDATE game SET completed_session_count = completed_session_count + 1 WHERE game_id = :g;
INSERT INTO game_history_entry (…) …;   -- one per REGISTERED player
```

| Rule | Source |
|---|---|
| One entry per **registered player**; none for guests | `FR-HIST-002`, `FR-HIST-003` |
| None for spectators | `FR-HIST-002`, `FR-STATS-002` |
| Placement derived from the player's team's entry in `teamResults` | `FR-HIST-005` |
| `game_name_snapshot` captured now, from `game.title` | `FR-HIST-006` |
| No win/loss label stored — derived at read from `draw`, `placement`, `team_count` | `FR-HIST-010…013` |
| No `team_id` stored | Team ids are `room_team` rows that `FR-JOB-009` purges with the room |

**`ON CONFLICT DO NOTHING` is where `FR-EFF-007` becomes durable.** "Only the first `game_over` is
honored" is easy to hold in memory within one process; a re-delivered effect after a restart needs
the database to say it. The counter increments only if the insert actually inserted.

**A session played entirely by guests writes the completion row and no entries** — which is exactly
why the counter cannot be derived from `game_history_entry`. `FR-STATS-003` counts those sessions
toward per-game totals, and deriving would silently under-count them while passing every test that
had a registered player in it.

---

## D. Detach — the room returns to Lobby

`detachSession(roomId, sessionId, reason='game_over', nextState='LOBBY')`. Same method as every
closure path; only `nextState` differs.

```
0. Claim the room. On redirect: record the closure as owed, return.

TX — Postgres only. No gRPC, no Redis, no remote call.
  1. SELECT … FROM room WHERE room_id = :r FOR UPDATE
  2. room.active_session_id <> :sessionId → COMMIT, return       (idempotent)
  3. room.state = 'LOBBY'; room.active_session_id = NULL; reset all readiness
  4. INSERT INTO session_teardown (session_id, room_id, reason) ON CONFLICT DO NOTHING
  5. DELETE FROM game_input_outbox WHERE session_id = :s AND dispatched_at IS NULL
  6. COMMIT

after commit:
  7. broadcast GAME_ENDED { readinessReset: true }
  8. terminateAndCleanup(sessionId, 'game_over')
```

**Step 4 makes the teardown a durable to-do, keyed by `sessionId`.**
[ADR-0010](../../decisions/0010-session-teardown-ordering.md) settled this, and the keying is the
whole point: a room-scoped flag would be overwritten by the next session's start, silently dropping
the previous session's owed teardown. Keying by session is what pulled **normal game end** into the
fix — the most frequent detach path, which previously had no crash safety at all.

**Step 5 discards undelivered outbox rows.** A `player_left` describing a session being torn down is
moot, and delivering it would produce a `NOT_FOUND` the drain would then have to interpret.

**The gRPC call is never inside the transaction.** The room row is taken `FOR UPDATE` by every join,
leave, reconnect and readiness path; holding it across a call to a service that can hang turns one
slow Game Host into room-wide lock contention. It buys nothing anyway — Postgres and the Game Host
cannot commit atomically regardless. The outbox row *is* the substitute for that atomicity.

**Broadcast after commit, before teardown.** Membership is settled the instant the transaction
commits; making players wait on a Game Host RPC to learn their game ended couples client-visible
latency to bookkeeping they have no stake in. Never *before* commit — a rollback would leave clients
believing a live game was over.

---

## E. Results, then Lobby

There is no server-side "post-game" state. The room is already `LOBBY` (`FR-LIFE-001/002`); the
results view is a **client-side overlay** (`platform-views.md`, `FR-LIFE-003`): the iframe stays
rendered showing results, with a **Return to Lobby** control over it.

`readinessReset: true` on `GAME_ENDED` carries `FR-READY-004` — no separate `READINESS_RESET` event
follows, and clients reset all players' local readiness on this one event.

A client that reconnects *after* game end returns to the lobby and cannot resync: the session is
terminated and sync is no longer available (`FR-DC-004`).

---

## F. Rematch, overlapping the teardown

Alice presses **Start Game** again ~4 seconds later. The Game Host is restarting and
`terminateAndCleanup(session-1)` has failed.

| # | What happens |
|---|---|
| 1 | `session_teardown` still holds a row for **session-1** with `attempts=1`, `next_attempt_at` backed off |
| 2 | `START_GAME` re-validates conditions under the lock; readiness was reset, so players must ready up again |
| 3 | `CreateSession(session-2)` — a *new* session id |
| 4 | `room.active_session_id = session-2`, `state='IN_PROGRESS'` |
| 5 | The reconcile sweep re-drives session-1's teardown until the Game Host confirms it |

**This is the scenario that forced the teardown table to be session-keyed.** A `teardown_owed`
boolean on `room` would have been cleared or overwritten by step 4, and session-1's Espresso context
would be pinned for the life of the Game Host process — the exact leak ADR-0010 exists to prevent,
reintroduced by the most ordinary user action in the platform.

**And it is the scenario that broke an earlier `NOT_FOUND` rule.** That rule made `NOT_FOUND`
"terminal only if no teardown was ever recorded" — but `terminateAndCleanup` **deletes** the
`session_teardown` row on success, so the history it read is erased by the very event it detects. A
re-driven teardown for session-1 succeeds, deletes its row, and a surviving outbox row from session-1
then reads as "session lost" and fails this **healthy live rematch** back to Lobby.

Replaced with a test of the durable fact: `room.active_session_id = :sessionId`. For a session-1
outbox row that is false — the room now claims session-2 — so the row is dropped as a benign no-op,
which is correct. It needs no schema addition and stays correct after the room is purged.

**A teardown outstanding for more than 15 minutes raises `FR-ALERT-007`.** A session never torn down
pins guest-execution resources for the life of the process, so an unbounded backlog degrades the Game
Host rather than merely leaving stale data.

---

## G. What the second game inherits

| Carried over | Reset |
|---|---|
| Room, participants, teams, host | Readiness for every player (`FR-READY-004`) |
| `room.version`, monotonic across both games | Session id, sequence counter (`CreateSession` is sequence 0) |
| `room.game_version` — still the version pinned at **room creation** | Game state, entirely |
| Chat history in connected clients (never persisted, `FR-RET-004`) | The game log, which is per session |

**`room.game_version` does not move**, even if the developer published a new version between the two
games. The version is pinned per room, not per session — so a rematch plays the same code the first
game did, and `FR-GAME-011` keeps that version alive for as long as this room references it.

---

## Defects surfaced

| Defect | Fix |
|---|---|
| A structurally invalid `GameOutcome` would abort the recording transaction with no possible retry, losing the session from both history and statistics | Boundary validation (§B); CHECK demoted to backstop ([history §2](../platform/data-model-history.md)) |
| The per-game counter had no idempotency key, so a re-delivered `game_over` would double-count it — and `FR-STATS-004` forbids decrementing, so the error would be permanent | `game_session_completion` with `ON CONFLICT (session_id) DO NOTHING`; the counter increments only on a real insert |

The second is the sharper one: the counter is *explicitly* required to be monotonic and never
decremented, which means every over-count is unfixable. A denormalized counter with no independent
derivation is also a number nobody can ever check — so the completion table serves twice, as the
idempotency key and as the thing that makes the counter verifiable.
</content>
