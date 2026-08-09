# ADR-0009: Grace deadlines are persisted absolute timestamps, fired by a sweep

- **Status:** Accepted
- **Date:** 2026-08-09
- **Deciders:** Project owner
- **Source:** GRMP lesson F3 — grace-period timers have no specified home or restart durability
- **Extends:** [ADR-0008](0008-room-ownership-lifecycle.md) (ownership claim); ADR-0001 (single
  non-HA Redis)

## Context

`reconnection-flow.md` FR-GRACE-* and FR-EXPIRY-* define *what* happens when a disconnected player's
grace period elapses — slot released, `player_left` sent to the game backend, `PLAYER_LOST`
broadcast, pinned card removed — but never say **where the timer lives** or that it survives a
restart. `room-websocket.md` serves `graceRemainingSeconds` in the `ROOM_STATE` snapshot, which
implies an absolute deadline exists somewhere, but no document gives it a home.

The GRMP prototype held these in an in-memory `ConcurrentHashMap`. They were lost on every restart
and were a direct contributor to rooms stuck in progress with players who could never be resolved.
That is the failure this decision exists to prevent.

## Decision

**A grace deadline is an absolute timestamp persisted in PostgreSQL at disconnect time, computed
with the database clock. Expiry is fired by a scheduled sweep. There is no in-process timer.**

1. **Postgres, not Redis.** The deadline lives next to the room state it guards, in the store already
   declared authoritative and written on every mutation. Redis is a single non-HA instance with an
   accepted loss window (ADR-0001, OPS-4); putting the reservation there would mean its failure mode
   is "the slot silently never expires" — precisely the bug being designed out — and would serve
   `graceRemainingSeconds` from the store most likely to have lost it.
2. **The sweep is the primary mechanism, not a backstop.** Two mechanisms enforcing one deadline
   means a dual write and a three-way race to arbitrate on every reconnect. One mechanism driven off
   a persisted timestamp is restart-durable by construction. The cost is bounded jitter (one sweep
   interval, default 5s, on a 60s window) and it is not user-visible: `PLAYER_DISCONNECTED` already
   carries `gracePeriodSeconds`, so the client renders its own countdown and does not depend on
   server punctuality.
3. **Expiry is a single conditional UPDATE, and its rowcount is the entire idempotency story.**
   The guard is a per-disconnect **reservation id** — not the deadline value, since two disconnects
   can produce the same timestamp — plus "not already released" and "actually due". Rowcount 1 means
   this caller won and owns *all* side effects; rowcount 0 means someone else resolved it, or it is
   not due. Reconnect, kick, early release (FR-EXPIRY-004) and expiry are the same statement with
   different guards. **No dedup table is required anywhere.** The reconnect path is the one caller
   that must distinguish *why* it lost — a released slot sends the client to late-join
   (`SLOT_RELEASED`, FR-REJOIN-007), whereas a superseded reservation just means the client is racing
   its own newer disconnect — so it re-reads state rather than branching on the bare zero.
4. **The database clock is the single time authority.** All deadlines are computed and compared with
   `now()` in Postgres. A pod with a fast clock that evaluates early updates zero rows and moves on;
   no other clock can release a slot early. Clock skew stops being a correctness concern by
   construction rather than by tolerance.
5. **Each cross-store side effect gets a transactional outbox.** The `player_left` notification to
   the game backend is a gRPC call to another service, so it cannot commit atomically with the row.
   The outbox row is inserted **inside** the expiry transaction and drained separately. Without it, a
   crash between commit and call loses the notification permanently and the game stalls on a turn
   that never comes. (An expiry that closes the room also produces a teardown record — ADR-0010 —
   so the transaction may write two such rows.)

   Delivery is at-least-once, and **making a repeat harmless requires the outbox row to carry its own
   `sequence`**. The Game Host deduplicates by `sequence`, but a sequence is normally allocated at
   *enqueue*: a re-drained row would arrive under a new one, the Game Host would treat it as a second
   distinct input, and `player_left` would apply twice. The drain therefore allocates the sequence
   once, persists it on the row, and reuses it on every retry.

**Design rule, and it is testable: the system must remain correct with any latency optimization
removed.** If an eager in-JVM fire is ever added for latency, it must call the identical conditional
UPDATE, and the integration suite must pass with eager firing disabled. The moment that suite fails,
the optimization has acquired logic it was never allowed to have.

## Consequences

- **Positive:** grace periods survive restart, rolling deploy, and pod takeover. `ROOM_STATE`'s
  `graceRemainingSeconds` becomes derivable (`deadline − now()`) and correct across ownership change,
  which is what `room-websocket.md` promises today and the current design cannot deliver. The
  ownerless-room case in ADR-0008 has something durable to act on.
- **Negative:** expiry latency is bounded by the sweep interval rather than immediate. Accepted, and
  captured as an NFR (deadline + 5s p99) so it is measurable rather than assumed.
- **The sweep must hold room ownership before it mutates or broadcasts** (ADR-0008), or ADR-0002's
  single-producer invariant breaks. Firing a deadline is exactly the case that justifies the sweep
  being able to claim an ownerless room.
- **Adoption must never reset an in-flight deadline** — a player 45s into their grace period when the
  pod died must not receive a fresh 60s. Deadlines are set with `COALESCE`, never overwritten.
- **Several previously unspecified behaviours are now forced into the open** and are specified in
  `reconnection-flow.md`: grace opens when the *last* of a user's connections to that room closes and
  ends when the *first* reopens (a user may hold up to 4 concurrent connections per
  `rate-limiting.md`, so closing one tab must not disconnect a player who is visibly still playing);
  a reconnect that loses the race to expiry falls into the late-join path rather than failing
  opaquely; a config change to the grace duration never moves an already-running deadline; and
  outstanding reservations are resolved immediately when a game ends, since reservations are
  meaningless in Lobby.
- **An ungraceful loss of a pod opens a grace period for every player in every room it owned**, which
  creates a deployment constraint that existed in no document: the grace duration must exceed the
  **cumulative** time a single room spends unreachable across a full rolling deploy, including client
  reconnect backoff and ownership reclaim latency (NFR-CONF-003).

  The mechanism is worth stating precisely, because the obvious framing is wrong. The player at risk
  is **not** one who reconnected between restarts — a reconnect clears the reservation, and any later
  disconnect starts a fresh window (FR-GRACE-006). It is the player who never manages to reconnect at
  all: their one absolute deadline keeps running, correctly, straight through every outage. So the
  binding quantity is total deploy duration, not the interval between restarts. And a *graceful*
  drain releases ownership and normally opens no grace windows at all, so this binds on the
  ungraceful path — drain timeout exceeded, OOM kill, SIGKILL.

## Alternatives rejected

- **Redis key with TTL + keyspace notifications.** Keyspace notifications are fire-and-forget: not
  delivered without a live subscriber, never replayed, gone on restart. Combined with a single non-HA
  Redis, the failure mode is a reservation that never expires. It also reintroduces the cross-pod
  pub/sub that ADR-0002 deliberately removed.
- **In-JVM `ScheduledFuture` only.** GRMP's failure verbatim. Additionally voids every in-flight grace
  period on a rolling deploy and cannot serve `graceRemainingSeconds` to a client that lands on a
  different pod.
- **Persisted deadline with an in-JVM timer as primary and the sweep as a net.** Correct, but it is
  two mechanisms and a three-way race (timer / sweep / reconnect) where one mechanism and a two-way
  race suffice. The ≤5s it buys is invisible on an event the user already watched count down from 60.

## Affected documents

- `docs/specs/platform/room-lifecycle.md` — the conditional UPDATE statements, the reservation-id
  guard, deadline derivation, outbox drain.
- `docs/specs/platform/data-model.md` — participant columns, the game-input outbox table.
- `docs/requirements/reconnection-flow.md` — FR-GRACE-005/006, FR-EXPIRY-005, FR-REJOIN-007;
  NFR-CONF-001 amended.
- `docs/requirements/platform-operations.md` — the deadline sweep (FR-JOB-006) and its NFR.
- `docs/specs/api-design/room-websocket.md` — `graceRemainingSeconds` derivation; `SLOT_RELEASED`.
- `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` — `player_left` may be re-delivered
  from a durable outbox.
