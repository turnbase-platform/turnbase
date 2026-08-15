# Flow 05 — The Owning Instance Dies Mid-Game

Four players are mid-game. The Platform Monolith instance that owns their room is `SIGKILL`ed — OOM,
node failure, or a drain that overran its grace period. Nobody's game state is lost, because none of
it was ever in that process. Everything else has to be re-established.

**Components:** four browsers, the dying instance, a surviving/successor instance, PostgreSQL, Redis,
Game Host.

This is the flow [ADR-0008](../../decisions/0008-room-ownership-lifecycle.md),
[ADR-0009](../../decisions/0009-grace-deadline-durability.md) and
[ADR-0010](../../decisions/0010-session-teardown-ordering.md) were written for.

---

## A. The instant of death

| What was in the dying process | Fate |
|---|---|
| Four WebSocket connections | Gone. Every client sees a socket close |
| The in-JVM room lock | Gone; irrelevant — the durable guard is the fenced `UPDATE` |
| Its liveness lease `pod:{podId}:alive` | **Expires 10 s later**. Nothing deletes it; the TTL does |
| `room:{roomId}:pod` naming it | **Persists.** No TTL — the claim script is the only writer |
| Game state | Never was there. It is in Redis and the Game Host's Espresso context |
| Grace deadlines | Never were there. `timestamptz` columns in Postgres (ADR-0009) |

**Nothing is lost that anyone needs.** That is the property the three ADRs bought, and it is why
this flow is recoverable at all.

`room:{roomId}:pod` deliberately outlives its owner. If it expired with the lease, a Redis blip would
unown every room at once; because it persists, the claim script can see *who* claimed to own it and
test that instance's liveness separately.

---

## B. What the clients see

All four sockets close simultaneously. Under `FR-DC-006` this is a **mass involuntary disconnect**,
and every one of them is treated as `FR-DC-001` — the platform cannot distinguish a dead instance
from four simultaneous network failures, and should not try.

Two rules keep this from cascading:

- **`FR-DC-007`: owner-instance loss is not an "immediate leave" in any room state.** Without it, a
  rolling deploy would delete every Lobby room on the platform: `FR-DC-002` makes a Lobby disconnect
  an immediate leave, and `FR-XFER-002` closes a room whose host has left with no humans remaining.
  Chain them at drain and every Lobby room deletes itself.
- **`FR-DC-006`: an already-running deadline is never reset.** A player 45 seconds into a grace period
  when the instance died does not get a fresh 60. Their absolute deadline runs through the outage,
  which is also what makes `FR-DEPLOY-003`'s bound *cumulative* — a player who never manages to
  reconnect has one deadline running through every restart of the deploy.

Clients reconnect on their own schedule. STOMP heartbeats mean they notice within seconds rather than
waiting for a TCP timeout.

---

## C. Adoption, path 1 — a client returns

The common case, and the fast one.

| # | Actor | Action | State |
|---|---|---|---|
| 1 | Carol's browser | Reconnects; the ingress routes anywhere — the affinity hint names a dead instance and is **advisory** (`FR-DEPLOY-002`) | — |
| 2 | Instance B | `SUBSCRIBE /topic/room.{roomId}` → runs the claim script | — |
| 3 | Redis (atomic) | `room:{roomId}:pod` names instance A; `pod:A:alive` is **absent** → overwrite with B, `INCR room:{roomId}:epoch` | **Redis** |
| 4 | Instance B | `UPDATE room SET owner_instance_id='B', owner_epoch=:myEpoch, ownerless_since=NULL, migration_window_expires_at=now()+:window WHERE room_id=… AND owner_epoch < :myEpoch` | **`room`** |
| 5 | Instance B | Loads `room.version` from Postgres and **assigns** its counter to it — never `max()` | — |
| 6 | Instance B | Emits **no** disconnect events for the other three | — |
| 7 | Carol | `REQUEST_ROOM_STATE`, then the game attach flow of [flow 03](03-game-turn.md) §E | — |

**Step 3 is the failure detector.** There is no dead-instance watcher in the platform. The claim
script's precondition — "the incumbent's liveness key is gone" — *is* the detection, evaluated
atomically at the moment it matters rather than by a background process that could itself be the
thing that died.

**Step 5 is the fix for a defect that would have been silent and permanent.** The room `version` was
originally an in-JVM `AtomicLong`. An instance adopting a room whose in-memory counter started at
zero would re-issue versions clients had already applied — and clients **discard**
`delta.version <= localVersion`. Not a gap, which is detected; a silent, permanent divergence.

**Step 6 is why eager reassignment was rejected.** Adoption emits no disconnect events because
invariant I1 holds in its bounded form: the previous owner either has no live sockets for this room
(it crashed — this case) or severs them within the eviction guard band. Note the invariant is
*bounded*, not absolute: a Redis flush unowns a room whose sockets are all still alive, which is why
layer 4 of the fence exists.

---

## D. Adoption, path 2 — nobody returns

The three remaining players' browsers are closed. Nobody is coming back, and the room has grace
deadlines that must still fire.

| # | Actor | Action |
|---|---|---|
| 1 | Reconcile sweep (60 s, `FR-JOB-007e`) | Finds rooms whose `owner_instance_id` names an instance with no liveness key |
| 2 | Sweep | Runs the same claim script — steps 3–5 above |
| 3 | Sweep | The room is now owned; the 5-second deadline sweep begins covering it |

**This duty is exempt from both `FR-JOB-008` guards, and both exemptions were necessary rather than
convenient:**

- **Two-strike rule (b).** An absent liveness lease is not a divergence needing corroboration — it is
  the claim script's own precondition, re-evaluated atomically at the moment of the claim. Requiring
  a second observation would double `NFR-JOB-002`.
- **Startup suppression (a), 120 s.** Adoption repairs nothing and infers nothing about Game Host
  state. Subjecting it to the guard would be actively harmful in the single-replica MVP, where a
  full-stack restart is the path that actually runs: every room would be unswept for two minutes,
  blocking expiries, deferred announcements and closures, and breaching `NFR-JOB-002` outright.

The other three duties — orphaned artifacts, In-Progress-without-a-session, idle Lobby — *are*
inferences about missing state and keep both guards.

**`NFR-JOB-002` is 90 seconds**, not 30. An earlier version required re-ownership in under 30 s from
a sweep that runs every 60 — a bound the mechanism could not meet.

---

## E. The migration window

Step 4 sets `migration_window_expires_at`, and it exists because of a requirement that had no
mechanism on its only path.

`FR-HDISC-004` gives a disconnected host a window to return before the role transfers. `§3.1`'s
host-transfer line sits on the *individual*-disconnect path — which adoption never routes through,
because adoption emits no disconnect events (step 6). So on the owner-loss path the window was
"started" by nothing and ended by nothing, and a host who did not return left the room **permanently
headless**: no `START_GAME`, no kick, no team management, forever.

The fix is a persisted absolute timestamp plus a sweep duty that closes it and performs the deferred
transfer. It is persisted rather than held in memory for exactly the reason grace deadlines are: the
window exists to survive an owner-instance loss, so holding it in the memory of an instance that can
itself vanish would void it during the one event it was written for.

---

## F. Meanwhile, the Game Host

It noticed nothing. It holds no connection to a particular monolith instance — the channel of record
is Redis — and its Espresso context for this session is untouched, with `lastAppliedSequence` intact.

When Carol resyncs (C7), instance B dispatches `Resync` and the game answers from state that never
moved.

**If the Game Host had died instead**, the trace is different and simpler: its session record is in
Redis, it recovers from that record on restart, and `NOT_FOUND` for a session with no record is
terminal by definition. The monolith does **not** probe the Game Host during reconciliation — the
session record is the source of truth, so a probe would add a failure mode and no information.

---

## G. Redis eviction — the one hole, deliberately bounded

The claim script triggers on *lease absence*, which covers crash, partition, flush, key eviction and
a stop-the-world pause longer than the TTL. In most of those the previous owner's sockets are still
alive.

So a `maxmemory` eviction of a healthy instance's lease permits a **wrongful takeover** with no
operator action and no error. Four layers bound it:

1. Renew every 3 s against a 10 s TTL — a single missed renewal is survivable.
2. Self-eviction: an instance that observes its lease **lapsed** (not merely a failed renewal — a
   long pause slips past a failure) stops acting after 6 s, inside the guard band.
3. Ownership re-check on a cadence, so a stale owner discovers the loss on a *read* path too, not
   only when it next writes.
4. **The fence.** Every mutation commits `WHERE room_id=… AND version=:expected AND owner_epoch=:myEpoch`.
   A stale owner matches zero rows, publishes nothing, and self-evicts.

Layer 4 is what makes layer 2's residual hole acceptable: **no divergence becomes durable in the
`room` table.** Reads are not fenced, so a stale owner can serve `REQUEST_ROOM_STATE` from stale
memory until layer 2 or 3 fires — bounded, not free.

**The epoch is the fence token and the room version cannot be.** The version is room-scoped and both
producers advance it densely from the same sequence, so a stale owner holding a fixed `expected` is
eventually *reached* by the legitimate owner — at which point the stale CAS matches and commits on
top. The epoch only moves at a change of tenure, so a stale owner's value is unreachable.

Because eviction produces this state silently, **Redis must run `maxmemory-policy noeviction`**, and
the monolith asserts it at startup rather than trusting it
([`local-environment.md`](../deployment/local-environment.md) §2).

---

## H. The graceful version

A rolling deploy runs the same machinery on a fast lane (`FR-DEPLOY-001`): fail readiness → stop
claiming → flush in-flight mutations → tell clients to reconnect → **release** every owned room →
exit.

Releasing rather than expiring is what makes a deploy fast: the successor claims a free room
immediately instead of waiting out a 10-second lease. A graceful drain normally opens **no grace
windows at all**.

`ownerless_since` is stamped only by a graceful release, and it is its only writer. It exists because
the two ways of losing an owner leave different traces: a crash leaves `owner_instance_id` naming a
dead instance, a clean drain leaves it null — and a null column with no timestamp is
indistinguishable from a room that was never owned.

`owner_epoch` is **never** reset by a release. It must advance monotonically across the ownerless gap
or the next tenure's fence would compare against a recycled value.

---

## Defects surfaced

None new. Every hazard on this path was found and fixed in the previous session; this trace exists so
the reasoning is followable in one reading rather than reconstructable from three ADRs and a
676-line spec.

Two things the trace makes visible that no single document states:

- **The `podId` is per-incarnation, not per-name** — instance name plus a boot UUID. A stable name
  would let a *restarted* instance match the "already mine" branch of the claim script, skip adoption
  entirely, and then produce versions from a freshly-zeroed counter: the divergence of §C5,
  self-inflicted. This bites hardest in the single-replica MVP, where restart is the path that
  actually runs.
- **Adoption and the Game Host are fully decoupled.** Nothing in C or D talks to it, and the flow
  completes whether it is up or down. That is what lets the monolith's readiness probe exclude it
  ([`local-environment.md`](../deployment/local-environment.md) §3) without weakening recovery.
</content>
