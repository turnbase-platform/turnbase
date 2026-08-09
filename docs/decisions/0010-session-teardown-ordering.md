# ADR-0010: Session teardown is a durable to-do, not an ordering

- **Status:** Accepted
- **Date:** 2026-08-09
- **Deciders:** Project owner
- **Source:** GRMP lesson F2 — room closure mid-game does not spec game-session teardown or ordering
- **Related:** [ADR-0009](0009-grace-deadline-durability.md) (the same outbox pattern)

## Context

The room-closure → session-teardown direction is specified only in fragments, and nowhere with a
mechanism. `reconnection-flow.md` FR-HDISC-003 does say the room is "closed **and the game session
terminated**" on grace expiry — but names no mechanism, no ordering, and no failure semantics.
`game-rooms.md` FR-XFER-002 closes a room immediately when the host leaves with no humans remaining,
including during an active game, and says **nothing** about the session at all. The gRPC contract
maps `TerminateSession` only to `game_over` (FR-SESS-005) and the retry limit (FR-FAIL-005). So one
of the two closure paths asserts termination without saying how, the other omits it entirely, and the
contract knows about neither.

The GRMP prototype hit exactly this: it terminated the worker session *after* deleting the room
record, so the reference needed to terminate was already gone, and sessions leaked. Its fix pinned
the ordering: terminate → broadcast → delete.

**That fix solves a problem TurnBase does not have.** GRMP's leak came from destroying the reference
with a `DELETE`; TurnBase never deletes the room row. Copying the ordering without the premise buys
nothing while making closure block on a service that can hang, and it has no answer for the case
where teardown simply fails.

A leaked session is not free. Per `game-host-internals.md` §6.3 a context with any active session is
never evicted, and §7.1 pins its JAR. **One leaked session pins an Espresso context and its game
artifact for the life of the Game Host process**, defeating idle eviction (FR-CTX-009) and
memory-pressure LRU (FR-CTX-010). On a single-instance MVP under a pod-wide memory cap, a handful
across distinct game versions is a slow march to OOM. A Game Host restart clears the contexts; what
survives a restart is the orphaned Redis key family, which is why those keys also carry a TTL
backstop.

## Decision

**The right primitive is not "close a room" but "detach a session from a room", parameterised by the
room's next state. Teardown is recorded as a durable to-do in the same transaction as the state
change, then attempted best-effort. Ordering is not the mechanism; durability is.**

1. **One method, five callers.** Host explicit leave with no humans left; grace expiry with no human
   connected (FR-HDISC-003); **normal game end**; retry-limit permanent failure; and the
   reconciliation sweep. The next state is `CLOSED` for closure paths and `LOBBY` for game end.
2. **The to-do is a row keyed by `sessionId`, never a flag on the room.** A room outlives its
   sessions: game end returns it to Lobby (FR-LIFE-002) and a rematch starts a new one. A room-level
   flag would be overwritten by the next session's start, silently dropping the previous session's
   owed teardown: GRMP's bug class reintroduced through the shortcut.

   **This decision therefore requires, normatively, that each game start allocates a fresh
   `sessionId`** — previously an unstated assumption. The requirement is not merely bookkeeping:
   `CreateSession` is idempotent on the existence of the session record, so a reused id whose record
   had leaked would **silently resume the finished game** instead of starting a new one. Game history
   also stores one entry per player per session id (FR-HIST-002), which a reused id would collide.
   And because every Redis key in the session family is `{sessionId}`-scoped
   (`game-host-internals.md` §13), a teardown re-driven by the sweep minutes later deletes
   `session:`/`routing:`/`queue:`/`seq:`/`delivered:`/`failcount:` by that id — so a rematch that
   reused it would have its live state deleted out from under it by the *previous* game's owed
   teardown. Fresh ids are what make `data-model.md` §4.1's indefinite retry horizon safe.
3. **Ordering: commit, then broadcast, then terminate.** The state change and the outbox row commit
   together in one local transaction. `ROOM_CLOSED` is broadcast after commit — room membership is a
   platform fact, settled the instant the transaction commits, and making players wait on a Game Host
   RPC to learn their room closed couples client-visible latency to bookkeeping they have no stake
   in. Never before commit: a rollback would leave clients believing a live room was gone. Teardown
   follows, best-effort, bounded.
4. **The gRPC call is never inside the database transaction.** The room row is taken for update by
   every join, leave, reconnect and readiness path; holding it across a call to a service that can
   hang converts one slow Game Host into room-wide lock contention and connection-pool exhaustion.
   It also buys nothing — Postgres and the Game Host cannot commit atomically regardless. **The
   outbox is the substitute for that atomicity.**
5. **Failure never blocks closure.** A failed or timed-out terminate leaves the row; the sweep
   re-drives it with backoff. The room is closed either way.

**Normal game end is included deliberately, and it is the common case.** `game-host-internals.md`
§10 already calls `TerminateSession` there with no crash-safety at all: a crash between "notify Room
Service" and the terminate leaks identically to a closure crash. Fixing only closure would have left
the far more frequent path leaking.

## Consequences

- **Positive:** teardown becomes crash-safe on every path including game end; the reconciliation
  sweep gains a precise lookup instead of a heuristic; a leaked session becomes a queryable debt with
  an alertable age rather than an invisible one.
- **Negative:** one additional table and a drain job. Accepted — the same outbox pattern already
  arrived at independently for the grace-expiry notification (ADR-0009), so this is one mechanism
  used twice, not two mechanisms.
- **Idempotency of `TerminateSession` becomes load-bearing** and is currently guaranteed only in
  `game-host-internals.md` §9.1, not in the protocol contract. A lost ACK is indistinguishable from a
  real failure, so every re-drive must be safe. The guarantee is promoted to the protocol spec.
- **Terminate must not wait on the per-session single-flight lock**, or the bounded timeout is
  fiction. Required semantics: mark terminated, delete the Redis record, return immediately, dispose
  the guest instance when the lock frees, discard the in-flight result. It must not use
  `Context.interrupt`, which is context-scoped and would hit sibling sessions.
- **Two gaps in the gRPC surface are exposed.** There is no termination reason for the normal
  `game_over` teardown, so §10 would send `UNSPECIFIED`; and `TERMINATION_REASON_HOST_ENDED` has no
  requirement anywhere that produces it — no host abort-game feature exists, and the host cannot kick
  themselves. The first is added; the second is reserved.
- **`TerminateSession` deletes only `session:{sessionId}`**, while the retry-limit path also cleans
  the queue and counters. Room-closure-driven teardown goes through `TerminateSession`, so
  `routing:`/`queue:`/`seq:`/`delivered:`/`failcount:` are left behind on exactly the path room
  closure uses — `routing:` on *every* path, since it is otherwise cleared only on host failure.
  Cleanup of the full key family becomes part of the teardown routine, and the sweep collects any
  strays.
- A window exists between the broadcast and the terminate where the session is still live, and on the
  failure path it is **unbounded** — it lasts until the sweep succeeds. It still needs no machinery,
  but not for the reason a first draft of this ADR gave: there is **no room-scoped authorization
  rule**. Game-destination authorization in `websocket.md` is *session*-scoped ("the session exists
  and is active, not terminated, not past `game_over`"), so closing a room rejects nothing by itself.
  The window is safe per caller instead: on the closure paths **no human player remains by
  construction**, so nobody is authorized to send an action; game end is covered by "not past
  `game_over`" plus FR-EFF-006/007; retry-limit failure by "not terminated". Note also that "fans out
  to a room with no subscribers" is false — spectators are still attached at closure, and at game end
  the room is in Lobby with everyone attached.
- **A partially delivered `ROOM_CLOSED` is not repaired by the version-gap mechanism**, because a
  closed room emits no further events for a client to detect a gap against. Deliberate: the broadcast
  is best-effort, not durable. A client that misses it discovers the closure on its next command
  (rejected by the handler's room check) or through the rejoin flow reporting the room closed
  (FR-REJOIN-008), and its pinned card is removed by the same path.

## Alternatives rejected

- **GRMP's ordering applied literally (terminate → broadcast → persist).** Its premise — that
  persisting destroys the reference — does not hold here. It makes closure block on a hangable remote
  call, and a crash between terminate and persist leaves a room durably marked in progress pointing
  at a session that no longer exists, so reconnecting players are routed into it and fail. Combined
  with "teardown failure never blocks closure", it degenerates into the fire-and-forget option on
  every failure while keeping all of its costs.
- **Persist, then fire-and-forget terminate with no durable record.** A transient `UNAVAILABLE`
  during a Game Host restart is routine, and each one leaks a session with nothing recording the
  debt. Recovery then requires the sweep to *infer* orphanhood by diffing Redis against Postgres — a
  race against live session creation. The outbox turns inference into a lookup for the price of one
  small table.

## Affected documents

- `docs/specs/platform/room-lifecycle.md` — the detach algorithm, transaction boundary, timeout,
  re-drive.
- `docs/specs/platform/data-model.md` — the teardown outbox table.
- `docs/requirements/game-rooms.md` — a requirement that detaching a session records a durable owed
  teardown; FR-XFER-002 cross-reference.
- `docs/requirements/platform-operations.md` — the re-drive duty in the reconciliation job.
- `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` — normative idempotency, `NOT_FOUND`
  scoped to the dispatch RPCs, in-flight semantics, terminate deadline, the new callers.
- `docs/specs/internal-grpc/gamehost.proto` — add a `GAME_OVER` reason; reserve `HOST_ENDED`.
- `docs/specs/game-host/game-host-internals.md` — §9.1 terminate semantics, §10 outbox step, §13 key
  TTLs.
