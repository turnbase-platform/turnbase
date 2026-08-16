# Flow 04 — Disconnect, Grace Period, Return or Expiry

Bob's network drops mid-game. The same trace runs twice: once ending in a reconnect, once in expiry.
The two are the same statement with different guards, which is the point.

**Components:** browser, Platform Monolith, PostgreSQL, Redis, Game Host.

---

## A. The disconnect is observed

| # | Actor | Action | Durable state |
|---|---|---|---|
| 1 | Network | Bob's TCP connection dies | — |
| 2 | Monolith | STOMP session closes; `SessionDisconnectEvent` fires | — |
| 3 | Monolith | Under the room lock: `room_participant.connection_count--` for Bob | **`room_participant`** |
| 4 | Monolith | Still `> 0`? **Stop.** Bob has another tab open | — |
| 5 | Monolith | Reached 0, room is `IN_PROGRESS`, Bob is a player → open a reservation: fresh `grace_reservation_id`, `grace_expires_at = now() + :grace` **with the database clock**, `left_at` stays NULL | **`room_participant`** |
| 6 | Monolith | `version++`, commit, broadcast `PLAYER_DISCONNECTED {playerId, graceSeconds}` | — |
| 7 | Other clients | Render "Bob disconnected — 60s", counting down from the payload | — |

**Step 4 is why `connection_count` is a refcount and not a boolean.** A player may hold several
connections (`rate-limiting.md` caps them at 4 per user), and `FR-GRACE-006` opens the window when
the *last* closes and ends it when the *first* returns. A boolean would show a player as disconnected
the moment they closed one of several tabs.

**Step 5 branches on room state and role, and both branches matter:**

| Situation | Behaviour |
|---|---|
| Room in `LOBBY` | Immediate leave, no reservation (`FR-DC-002`) — **unless** this is owner-instance loss (`FR-DC-007`) |
| Spectator | Dropped immediately, no slot held (`FR-DC-003`) |
| Player, `IN_PROGRESS` | Reservation opened |

**Step 5 writes an absolute timestamp and starts no timer.** [ADR-0009](../../decisions/0009-grace-deadline-durability.md)
made the deadline a persisted `timestamptz` written with `now()` — the database clock — so it
survives restart, rolling deploy and transfer of ownership, and so **clock skew is removed by
construction rather than by tolerance**. Any instance can read it and report the remaining time.

**The game engine is told nothing.** `FR-GRACE-003`: from the game's perspective Bob is still
present. This is what makes a 60-second network blip invisible to game logic.

---

## B. Sweep enforcement

The deadline sweep runs every 5 seconds (`FR-JOB-006`) over
`room_participant_grace_due_idx` — partial on `grace_expires_at IS NOT NULL AND left_at IS NULL`, so
it scans an index that holds only players *currently in grace*, typically tens of rows.

**This sweep is the primary mechanism, not a backstop.** Two mechanisms enforcing one deadline would
be a dual write and a three-way race to arbitrate on every reconnect.

**It is partitioned by room ownership** — an instance sweeps only rooms it owns, and must hold the
claim before mutating or broadcasting. A room whose owner is gone is not swept at all until adopted;
that gap is bounded by `NFR-JOB-002` (90 s), and the two bounds add.

**One duty is exempt from the partitioning**: draining `game_input_outbox`. Delivering a
notification to the Game Host is a gRPC call, not an event broadcast, and needs no ownership.
Partitioning it would leave a player's departure undelivered for as long as their room sat unowned —
and the game would sit on a turn that never comes, which is exactly what the outbox exists to
prevent.

---

## C1. Bob comes back — 40 seconds in

| # | Actor | Action | Durable state |
|---|---|---|---|
| 1 | Bob | Clicks **Rejoin** on the pinned card at `/rooms` (`FR-REJOIN-002`), or navigates to `/rooms/{roomId}` | — |
| 2 | Monolith | Claim script — Bob's socket may land on any instance; if the room is unowned, **this attach adopts it** | Redis + `room` |
| 3 | Monolith | Conditional update: `SET connection_count=1, grace_reservation_id=NULL, grace_expires_at=NULL WHERE room_id=… AND user_id=… AND grace_reservation_id=:seenId` | **`room_participant`** |
| 4 | Monolith | Row count 1 → Bob owns the outcome. Row count 0 → the sweep won; Bob is no longer a member and gets `ROOM_CLOSED`/rejoin-denied | — |
| 5 | Monolith | `version++`, commit, broadcast `PLAYER_RECONNECTED` | — |
| 6 | Bob | Subscribes to the room topic, `REQUEST_ROOM_STATE`; sees `state: IN_PROGRESS` and `sessionId` | — |
| 7 | Bob | Subscribes to `/topic/game.{sessionId}`, `/user/queue/game`, his team topic — **buffering from this moment** | — |
| 8 | Bob | `REQUEST_GAME_SYNC` (charged the `snapshot` bucket: 1 per 3 s) | — |
| 9 | Orchestration | Read-only `Resync` to the Game Host under the session's single-flight lock → `onResync(state, viewer)` → `{viewPayload, asOfSequence}`. **No state write, no sequence allocated, no watermark moved** | — |
| 10 | Bob | `GAME_SYNC`; discards buffered `sequence <= asOfSequence`, applies the rest, resumes live | — |

**Step 3's row count is the entire idempotency story.** There is no deduplication table anywhere in
this design. Expiry, reconnect, kick and early release are one conditional `UPDATE` with different
guards; exactly one actor matches a row, and that actor owns all the side effects. A concurrent
reconnect and sweep cannot both take effect (`FR-EXPIRY-005`).

**Step 3 CASes on `grace_reservation_id`, not on `grace_expires_at`.** Two disconnects can produce an
identical deadline, and a boolean could not tell a stale actor *which* reservation it was acting on.
The id doubles as the correlation id in logs and metrics.

**Step 9 is read-only but not free.** It re-enters the guest VM under the session lock, which makes
it the most expensive frame a client can send — hence the strictest rate-limit bucket in the
platform. Under a legitimate mass reconnect, N resyncs serialize behind one lock; that is
`websocket.md` OQ-001, and the mitigation if it becomes a hotspot is caching the per-viewer view
against `lastAppliedSequence`.

---

## C2. Bob does not come back

| # | Actor | Action | Durable state |
|---|---|---|---|
| 1 | Sweep | Finds `grace_expires_at < now()` with the reservation outstanding | — |
| 2 | Sweep | Holds the room claim (or skips the row) | — |
| 3 | Sweep | One transaction: `left_at = now()`, `leave_reason = 'GRACE_EXPIRED'`, slot released, `version++`, **and** `INSERT INTO game_input_outbox` a `player_left` for this session | **`room_participant`, `game_input_outbox`** |
| 4 | Sweep | Commit, broadcast `PLAYER_LOST` | — |
| 5 | Drain | Allocate `sequence` once via `UPDATE … SET sequence=:seq WHERE id=:id AND sequence IS NULL`; `SubmitInput(player_left)`; stamp `dispatched_at` **on ACK** | **`game_input_outbox`** |
| 6 | Game Host | `onPlayerLeft` — the game decides: replace with AI, continue, forfeit (`FR-EXPIRY-002`) | — |

**Step 3 writes the outbox row inside the same transaction as the slot release**, and that is the
whole reason the table exists. A crash between committing the release and calling the Game Host would
otherwise lose the notification permanently, and the game would stall waiting for a player the
platform has already removed.

**Step 5 allocates the sequence once and persists it.** A re-drained row enqueued under a *new*
sequence would look like a second distinct input, `player_left` would be applied twice, and the
replay path would never engage.

**`dispatched_at` is stamped on acknowledgement, never on attempt.** A row whose RPC timed out but
was marked dispatched would escape the teardown discard, outlive its session, and later draw a
`NOT_FOUND` for a session no longer attached to any room.

### `NOT_FOUND` on the drain

Terminal **only while the session is still attached to a room** —
`SELECT 1 FROM room WHERE active_session_id = :sessionId`, served by `room_active_session_idx`.

The obvious test, "was a teardown ever recorded", cannot be answered: `terminateAndCleanup` deletes
the `session_teardown` row on success, so a completed teardown leaves no trace. A rule conditioned on
that history produces the exact failure it was written to prevent — a re-driven teardown succeeds,
deletes its row, and a surviving outbox row then reads as "session lost" and fails a **healthy live
rematch** back to Lobby.

`room.active_session_id` is the durable form of the same fact, needs no schema addition, and stays
correct after `FR-JOB-009` purges the room: no row means no attachment, which is the benign case.

---

## D. Special cases

**Grace expiry in a Lobby room.** The sweep must not re-delete the rooms `FR-DC-007` exists to save.
A Lobby disconnect opens no reservation in the first place, so the only way a Lobby room has one is
that the room transitioned after the reservation opened — handled by the state check, not by an
absence of rows.

**Bob joins another room while holding a reservation.** `FR-EXPIRY-004`: the reservation is voided
early with `leave_reason = 'EARLY_RELEASE'` — a distinct value, because neither neighbour fits. He did
not leave *this* room deliberately, and the grace period did not run out.

If the instance handling that join does not own the old room, it can perform the release (a database
write) but cannot broadcast into the old room's topic — there is no cross-instance event path
(ADR-0002). `lost_announced_at` records that the release happened and the announcement has not, and
the owning instance emits it on its next sweep. Without that column the event is simply lost the
first day the platform runs more than one instance.

**Bob is the host.** Host role transfers immediately if another human is connected; otherwise
transfer *and* closure are deferred for the grace period (`FR-HDISC-003`). A room stays viable while
any human still holds a reserved slot — which is a single predicate, because a participant in grace
still has `left_at IS NULL`.

**Flapping.** Each disconnect starts a fresh window (`FR-GRACE-006`), so a connect/disconnect loop can
hold a slot indefinitely. The Tier 6 reconnect lockout dampens it; whether a hard cap per session is
needed is `room-lifecycle.md` OQ-003, deferred until observed.

---

## Defects surfaced

None new. This flow is the one the previous session rebuilt end to end, and the traces confirm the
repairs compose — in particular that the outbox drain's ownership exemption and the
`active_session_id` test are both load-bearing on the *same* path (C2 → drain → `NOT_FOUND`), which
is where the earlier version broke.

One clarification worth recording: **the deadline sweep's 5-second interval and the grace period's 60
seconds are not independent knobs.** `NFR-JOB-001` bounds enforcement at "deadline plus one sweep
interval", so raising the interval loosens a stated correctness bound rather than saving work. Both
are now in the configuration surface with that noted
([`local-environment.md`](../deployment/local-environment.md) §7.2).
