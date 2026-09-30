# Flow 07 — Closing a Room That Has a Live Session

One method, `detachSession`, five callers. Four close the room; one returns it to Lobby. They differ
in who is on the calling thread, what audience is still attached, and whether the caller can
broadcast at all.

**Components:** Platform Monolith (possibly two instances), PostgreSQL, Redis, Game Host.

The mechanism is [`room-lifecycle.md`](../platform/room-lifecycle.md) §4; the game-end variant is
[flow 06](06-game-end-and-rematch.md) §D. This file is about the *differences* between the callers,
which is where the hazards are.

---

## The five callers

| # | Caller | Trigger | Next state | `closed_reason` | Thread owns the room? |
|---|---|---|---|---|---|
| 1 | Host leave, no humans left | `FR-XFER-002` | `CLOSED` | `NO_PLAYERS_REMAINING` | **Sometimes** |
| 2 | Grace expiry, no human connected | `FR-HDISC-003` | `CLOSED` | `GRACE_EXPIRED_NO_HUMAN` | Yes — the sweep claims first |
| 3 | Normal game end | `FR-LIFE-002` | **`LOBBY`** | — | Yes |
| 4 | Retry-limit permanent failure | `FR-FAIL-003/005` | `LOBBY` | — | Yes |
| 5 | Reconciliation sweep | `FR-JOB-007c/d` | `LOBBY` or `CLOSED` | — / `IDLE_TIMEOUT` | Yes — claims first |

Plus one that is not a `detachSession` caller because there is no session to detach: **account
deletion** (`FR-LIFE-004`, `FR-XFER-002`, `closed_reason = 'ACCOUNT_DELETED'`) closes a hosted room
whose host deletes their account. If that room *does* have a live session, it enters through caller 1.

---

## The shared skeleton

```
0. Claim the room (§1.2). On redirect: record the closure as owed, return.
   Never commit or broadcast without the claim.

TX — Postgres only. No gRPC, no Redis, no remote call of any kind.
  1. SELECT … FROM room WHERE room_id = :r FOR UPDATE
  2. if room.active_session_id <> :sessionId: COMMIT; return       -- idempotent
  3. room.state = nextState; room.active_session_id = NULL
     if CLOSED: closed_at = now(), closed_reason = :reason
     release slots / clear reservations / reset readiness, per the path
  3b. DELETE FROM room_invitation WHERE room_id = :r              -- FR-INV-008
  4. INSERT INTO session_teardown (session_id, room_id, reason) ON CONFLICT DO NOTHING
  5. DELETE FROM game_input_outbox WHERE session_id = :s AND dispatched_at IS NULL
  6. COMMIT

after commit, best-effort, outside any transaction:
  7. broadcast ROOM_CLOSED (or GAME_ENDED); evict spectators
  8. terminateAndCleanup(sessionId, reason)
```

**Step 2 is the whole idempotency story**, and it is a comparison rather than a flag. Any caller
arriving second finds the session already detached and returns having done nothing.

**Step 3b is easy to lose**, and it is the one addition this trace forced. `room_invitation.room_id`
carries `ON DELETE CASCADE`, so a reader assumes invitations are handled — but that cascade fires
when the room *row* is purged, seven days later (`FR-JOB-009`), not at closure. `FR-INV-008` requires
deletion at closure, and its five producers are exactly the five rows above. The
[closure-reason table](../platform/data-model.md) now names this obligation where the producers are
enumerated, and `room_invitation.expires_at` bounds the damage if a path still forgets.

---

## Caller 1 — host leaves, and the thread that owns nothing

`FR-XFER-002` closes a room when the host departs explicitly with no other human present. The
departure can arrive three ways, and only one of them is on an owning thread:

| Arrival | Owns the room? |
|---|---|
| `LEAVE_ROOM` over the room's WebSocket | **Yes** — affinity put it there |
| `DELETE /api/users/me` (account deletion) | **No** — a REST call lands on an arbitrary instance |
| Guest-account cleanup (`FR-JOB-001`) | **No** — a scheduled job |

For the second and third, step 0's claim fails. That is not an edge case to shrug at: under ADR-0002
there is **no cross-instance fan-out**, so a non-owner's `ROOM_CLOSED` reaches *nobody* — and the
audience is real, because closure evicts **spectators**, who are connected at that moment and are not
counted by the "no human player remains" test that triggered the closure.

So a caller that cannot claim **records the closure as owed and returns**, and the reconciliation
sweep performs it, claiming first. REST- and job-initiated closure is therefore asynchronous, which
is the correct trade: a spectator silently stranded in a subscription to a dead room has nothing to
repair it, whereas a few seconds of delay costs nobody anything.

---

## Caller 2 — grace expiry with no human connected

The deferred-closure half of `FR-HDISC-003`. The host disconnected involuntarily during In Progress
with no other connected human; the room survives while any human still holds a **reserved** slot,
because a participant in grace still has `left_at IS NULL` — which makes the last-human test a single
predicate.

When the last reservation expires with nobody back, the room closes.

**In a Lobby room this must not fire.** A Lobby disconnect opens no reservation at all (`FR-DC-002`),
so the only route to one is a state transition after the reservation opened. Getting this wrong would
re-delete the rooms `FR-DC-007` exists to save.

---

## Caller 3 — game end

The only caller with `nextState = 'LOBBY'`, the most frequent by far, and the one that had **no crash
safety at all** before ADR-0010 keyed the teardown by session. [Flow 06](06-game-end-and-rematch.md).

---

## Caller 4 — retry-limit failure

The game has thrown three times (`FR-FAIL-003`). The session is unrecoverable, but the *room* is
fine.

**It fails back to Lobby, not closed.** Closing destroys a room people may still be sitting in;
Lobby is recoverable, reuses `FR-FAIL-005`'s existing path, and has a client story already. If the
room really is abandoned, the idle duty collects it 30 minutes later.

Clients receive `SESSION_FAILED`, not `ROOM_CLOSED`.

**No history entry is written** (`game-history.md` `CON-001`) and the per-game counter does not move:
there was no `game_over`.

---

## Caller 5 — reconciliation

Two duties reach `detachSession`:

| Duty | Condition | Outcome |
|---|---|---|
| `FR-JOB-007c` | `IN_PROGRESS` with no session state | **Fail back to Lobby** via `FR-FAIL-005`. No closure branch: the shared skeleton's only non-success outcomes are a deferred claim (§ Caller 1, retried next tick) and step 2's idempotent no-op, neither of which is this duty's to close (`IMP-GATE-55`) |
| `FR-JOB-007d` | `LOBBY`, zero connected participants, `last_activity_at` older than the idle window | `CLOSED`, `IDLE_TIMEOUT` |

Both keep both `FR-JOB-008` guards — two consecutive observations, and no repair within 120 s of
startup — because both are *inferences about missing state*. Only the adoption duty is exempt, and
[flow 05](05-owner-loss-and-adoption.md) §D says why.

**Duty (c) does not probe the Game Host.** The session record is the source of truth: a host that
lost local state recovers from it, and a host with no record returns `NOT_FOUND`. If the record is
absent the session is unrecoverable *by definition*, so a probe adds a failure mode and no
information.

**`last_activity_at` is the second leg of duty (d)** and it is load-bearing. "Zero connected
participants" alone is unsafe, because a crash can leave connection flags stale — but a genuinely
live room cannot have an old `last_activity_at` regardless of what the flags say.

Duty (c)'s notification is `GAME_ENDED` (`readinessReset: true`), not `ROOM_CLOSED` — the room isn't
closed — reusing the ordinary game-end event's contract since the client-facing behaviour is
identical: back in Lobby, forget local readiness (`IMP-GATE-55`).

---

## The window between broadcast and terminate

Between step 7 and step 8 the room is closed and the session is briefly still live. This needs no
machinery — but **not** for the reason it first appears.

There is **no room-scoped authorization rule** to lean on. Game-destination authorization is
*session*-scoped ("the session exists and is active, not terminated, not past `game_over`"), so
closing a room rejects nothing by itself. Nor is the room empty: closure evicts spectators, who are
attached at that moment, and at game end everyone is attached in Lobby.

The window is safe **per caller**:

| Caller | Why nothing can be submitted |
|---|---|
| 1, 2 | No human player remains by construction — nobody is authorized to send an action |
| 3 | "not past `game_over`" plus `FR-EFF-006`/`FR-EFF-007` |
| 4 | "not terminated" |
| 5 | There is no live session; that is the trigger |

An earlier draft justified this window with an argument ADR-0010 had already disproven. The
per-caller enumeration is the honest form.

---

## Teardown, and what happens when it fails

```
terminateAndCleanup(sessionId, reason):
  a. TerminateSession(sessionId, reason), deadline 2s
  b. on OK:  delete session:/routing:/gamekey:/queue:/seq:/delivered:/failcount:{sessionId}
             DELETE FROM session_teardown WHERE session_id = :sessionId
  c. on any error: WARN; record attempts++/last_error/next_attempt_at; leave it for the sweep.
     Never throw to the caller.
```

**`TerminateSession` must be idempotent, and `NOT_FOUND` must mean success** — the entire re-drive
depends on it. A retried teardown for a session already gone is the *expected* outcome, not a hard
failure. Both of those were in the implementation spec and missing from the contract until the
previous session put them there.

**The inline attempt (c) records its bookkeeping** rather than leaving it to the sweep, because a
Game Host restart is the *common* failure and skipping it would hide the first and most frequent one.

The six Redis session keys deleted in (b) all carry TTLs as a backstop, so a teardown that never
completes leaks bounded state rather than unbounded.

---

## Defects surfaced

| Defect | Fix |
|---|---|
| `FR-INV-008` requires pending invitations to be deleted when a room closes, but the only mechanism in the schema was a foreign-key cascade that fires seven days later at purge. The rule existed in one document; its five producers are enumerated in another and none mentioned it | Step 3b added to the skeleton; the obligation named in [`data-model.md`](../platform/data-model.md) §1's closure-reason table, where the producers are listed; `room_invitation.expires_at` (`FR-INV-009`) bounds a forgotten path |

Same shape as last session's worst finding: a correct rule, stated once, in a document that none of
its producers is written from. The fix is not only to state it in the right place but to make the
failure *bounded* if somebody still misses it — which is what the expiry does.
