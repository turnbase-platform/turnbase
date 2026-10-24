# ADR-0008: Room ownership is a lease-gated claim, not a lifetime assignment

- **Status:** Accepted
- **Amended by:** [ADR-0020](0020-platform-horizontal-scaling.md) (affinity routing by instance hint, release on scale-in; no consistent hashing)
- **Date:** 2026-08-09
- **Deciders:** Project owner
- **Source:** GRMP lesson F3 ("define pod-crash semantics"); self-contradiction found in
  `room-websocket.md` § Room Affinity during the room-lifecycle durability session
- **Extends:** [ADR-0002](0002-websocket-room-affinity.md) (room affinity)

## Context

ADR-0002 established that every real-time event for a room is produced by exactly one pod. It did
not say what happens when that pod dies. `room-websocket.md` then acquired three statements that
cannot all be true. As it stood before this ADR (commit `b46cfbf`), its § Room Affinity said:

- ownership "is assigned at room creation" and "persists for the lifetime of the room";
- but on crash, "clients reconnect via the standard join flow (**which assigns a new owning pod**)";
- and "no reconnection or migration is ever required at room entry."

The standard join flow as that section defined it assigns nothing on rejoin — it reads
`room:{roomId}:pod`, which still names the dead pod. **As written, post-crash rejoins route to a
corpse forever.** § Client Reconciliation conceded in passing that "pod restart during a session"
perturbs the version stream, while § Per-Room Serialization gave no rule making that perturbation
safe.

No document states how a stale ownership entry is invalidated, or under what mutual exclusion.
ADR-0002's entire correctness argument rests on a single producer per room, so an unspecified
invalidation is an unspecified split-brain.

A rolling deploy — not a crash — is the common case. The MVP is single-replica (ADR-0001), so the
crash path is exercised on **every restart of the local stack**.

## Decision

**Room ownership is a revocable claim, gated on the incumbent's liveness lease. Nobody watches for
dead pods; the liveness check is folded into the claim itself. A room may sit ownerless
indefinitely.**

1. **Per-pod liveness lease.** Each pod maintains `pod:{podId}:alive` in Redis (TTL 10s, renewed
   every 3s). This is the only liveness mechanism; there is no *instance* watcher, no placement
   policy, and no dead-pod detector as a distinct subsystem. `podId` is **per-incarnation** — the
   instance name plus a boot UUID — so a restarted instance never matches its own prior claim and
   skips adoption.
2. **Claim is a single atomic Lua script**, which also `INCR`s an **owner epoch** for the room in the
   same atomic step. Already mine → no-op. Incumbent's lease present → redirect to the live owner.
   Free, or incumbent's lease absent → take over on a fresh epoch. Three actors may claim: a client
   entering or re-entering a room, the reconciliation sweep when it must act on a room whose owner is
   gone, or nobody.
3. **Release is a compare-and-delete**, performed only on graceful shutdown.
4. **Split-brain is prevented in four layers:** atomicity of the claim script; the liveness gate;
   pod self-eviction on lease **lapse**; and — the correctness bound — **the owner epoch used as a
   fence token**. Every mutation commits
   `WHERE room_id = :id AND version = :expected AND owner_epoch = :myEpoch`; a stale owner's update
   touches zero rows, aborts, publishes nothing, and self-evicts.

   **The room version cannot serve as the fence, and an earlier draft of this decision wrongly said
   it could.** The version is *room*-scoped and both producers advance it densely from the same
   sequence, so a stale owner holding a fixed expected value is eventually *reached* by the
   legitimate owner — at which point the stale CAS matches and commits on top of it. The epoch moves
   only at a change of tenure, so a stale owner's value is never reissued and never reachable.

   **Self-eviction triggers on lease lapse, not on renewal failure.** Renewal uses `SET … XX`, so a
   nil reply proves the lease is gone and is unconditionally fatal; the key is never recreated.
   Triggering on consecutive renewal failures would miss the dangerous case: a pod that stalls longer
   than the TTL loses its lease, is taken over, resumes, and its *next* renewal succeeds — having
   observed no failure at all.

   **The fence covers the room row only.** Redis counters, the session queue, gRPC calls and STOMP
   publishes are outside it, so one ordering rule governs the rest: every externally visible side
   effect is issued **only after** the fenced commit returns success.

   **The write that installs a new epoch is the one mutation that cannot fence on equality**, and it
   must fence on `owner_epoch < :myEpoch` instead. The claim script is atomic, so no two tenures share
   an epoch — but it does not order the claimants' *Postgres* writes, and a claimant that stalls after
   claiming could otherwise stamp a lower epoch over a later tenure's, evicting the legitimate owner
   with its own fence. Monotonicity is what makes the `<` comparison sound.
5. **Graceful drain is a distinct fast lane.** Fail readiness → refuse new claims → flush → send
   `RECONNECT_REQUIRED` to attached clients → release ownership → exit. Because the key is
   *released*, the next claimant hits the free branch with no lease wait: reconnection is sub-second
   instead of ~10s, and the event is normally absorbed with no grace periods opened at all.
6. **Invariant I1 — for every claim path, the previous owner either has no live sockets for that
   room, or severs them within the eviction guard band.** Crash satisfies the first clause (sockets
   died with the pod); drain satisfies it (evict, then release); **the sweep satisfies only the
   second**. The weaker second clause is necessary and is not a hedge: the takeover trigger is lease
   *absence*, which covers partition, flush and long pauses as well as death, and in most of those
   the previous owner's sockets are still alive. An unowned room is therefore **not** necessarily a
   clientless one — asserting otherwise would be circular, since layer 4 exists precisely because
   "lease absent ⇒ pod dead" is false. In this bounded form the invariant still carries the
   no-disconnect-events consequence below, and it states what a future live-migration proposal must
   replace.

**Two defects in the current specs are fixed as part of this decision**, because the ownership model
is unsound without them:

- **V1 — persist before publish.** The room version must be committed to the database *before* the
  delta is published. The sequence previously incremented an in-JVM `AtomicLong` and published, with
  no stated ordering against the commit; an adopting pod initialises its counter from the database
  and could therefore **re-issue versions clients have already seen**. Clients discard
  `delta.version <= localVersion`, so the divergence is *permanent and undetected* — strictly worse
  than a gap, which at least triggers a resnapshot. With V1,
  `rooms.version >= every version ever broadcast`, so a crash yields a forward gap, which is
  detected and repaired.
- **V2 — assign, never `max()`** (a clarification, not a defect fix). The snapshot-delivery flow
  already said "assign", and V1 makes a backwards jump unreachable. V2 is written down as defence in
  depth for the one window where the fence has failed — a wrongful takeover under a Redis flush or
  key eviction — which is exactly when a client could hold a `localVersion` above the truth. It also
  pins the companion rule: pending optimistic state is discarded, not replayed, when a snapshot moves
  `localVersion` backwards.

## Consequences

- **Positive:** dead-pod detection stops being a subsystem. The design degenerates correctly to the
  single-replica MVP, where "first client back claims" is exactly right and is exercised on every
  restart — the crash path is continuously tested rather than dormant. No new policy is needed for
  the last-human case: FR-HDISC-003 already governs an In Progress room with no connected human.
- **Negative:** for up to one lease TTL after a hard crash, a claim returns a redirect naming the
  dead pod. Mitigated by a short internal retry (a few hundred ms — not seconds, which would hold a
  request thread per reconnecting client and turn a rolling deploy into thread-pool exhaustion)
  before returning a bounded retry directive; worst case ≈10s of client-side retrying.
- **A Redis flush or a `maxmemory` eviction can drop a healthy pod's lease key and permit a wrongful
  takeover.** Scoped honestly: **no divergence becomes durable in the `room` table**, and
  client-visible divergence is bounded by the stale owner's next write *or its next ownership
  re-check*, whichever comes first. Reads are not fenced, so until one of those the stale pod can
  still serve snapshots from stale memory. Because eviction reaches this state with no operator
  action, the platform Redis must run `maxmemory-policy noeviction` (or hold ownership keys in a
  dedicated logical database). That is the right trade against a single non-HA Redis (ADR-0001,
  OPS-4), but it is a bounded fault, not a free one.
- **Requires an ingress that treats the affinity hint as a hint** — when the named pod is absent from
  the ready endpoint set, the ingress must fall back to normal load balancing. Standard behaviour in
  nginx/Traefik/Envoy, but load-bearing here, so it is written down. The WebSocket handler must also
  **re-verify ownership at subscribe time**: a claim runs on the REST join, and a sweep can take a
  free room in the interval before the client subscribes. Holding a socket is not evidence of owning
  the room.
- **This decision introduces two columns** — `room.version` (which existed only as an in-JVM counter)
  and `room.owner_epoch` — defined in [`../specs/platform/data-model.md`](../specs/platform/data-model.md).
- **Relationship to the deferred multi-instance scope.** `platform-operations.md` NFR-SCALE-001 defers
  multi-instance deployment to post-MVP, while this ADR specifies a claim protocol. There is no
  conflict: layers 2–4 cannot fire with a single replica and are post-MVP insurance, but the *claim
  and adoption path itself* runs on every restart of the local stack, which is why it is specified
  now rather than later. Likewise ADR-0002's "crash recovery still depends on Redis-persisted state"
  refers to **game** state; room state is authoritative in Postgres, and this ADR is what a reader
  will consult on that point.
- **Two consequential requirement changes fall out** and are specified in `reconnection-flow.md`:
  a **Lobby carve-out** (a disconnect caused by owner-pod loss is never an immediate leave — without
  this, FR-DC-002 plus FR-XFER-002 make a rolling deploy delete every Lobby room), and a **migration
  window** deferring host transfer after adoption, so a deploy does not hand the host role to
  whoever reconnects fastest.
- Adoption emits no per-player disconnect events: by I1 every client of that room is disconnected,
  so the events would reach nobody and burn a version each. State reaches reattaching clients via
  `ROOM_STATE.disconnectedPlayers`, which already carries `graceRemainingSeconds`.
- Exactly-once game input survives a platform-pod crash **with no Game Host change** — replay by
  `sequence`, the `delivered:{sessionId}` watermark, and client-side `asOfSequence` dedup already
  compose to give it. This was true and simply never written down.

## Alternatives rejected

- **Eager reassignment** (a detector reassigns orphaned rooms to a live pod immediately). Adopting a
  room with no clients attached computes nothing — TurnBase games are turn-based and driven by human
  input. The one case that needs a live owner with nobody attached (firing a deadline) is already
  covered by the sweep claiming on demand. Eager reassignment pays the full fencing cost *plus* a
  detector and a placement policy for identical observable behaviour. It also takes over rooms whose
  clients may still be attached to a partitioned-but-reachable pod more often — though note the
  difference is **frequency, not kind**: as I1 makes explicit, lazy claiming has the same exposure
  via the sweep and via a Redis flush.
- **Consistent hashing at the ingress** over the ready endpoint set, with no ownership key and no
  lease at all. Genuinely simpler in steady state, and the first thing a reviewer asks for. Rejected
  because a membership change rehashes a share of *all* rooms, not just those on the departed pod —
  so an unrelated room's clients migrate mid-game on every scale event — and because two pods
  transiently disagreeing about the ring is precisely the split-brain the fence exists to stop,
  without any of the machinery to stop it.
- **A PostgreSQL advisory lock as the ownership primitive.** Attractive because the database is
  already authoritative and is the thing being fenced, which would collapse two stores into one.
  Rejected because a session-scoped advisory lock ties room ownership to a pooled connection's
  lifetime — a pool eviction silently drops ownership, and a leaked connection holds it indefinitely
  — and because it puts room routing on the availability of the database rather than leaving it on a
  store the platform already tolerates losing.
- **Crash is fatal to the room.** Voids FR-GRACE-001 and FR-HDISC-003, destroys every live game on
  every rolling deploy, and discards the Game Host's §8.1/§9.3 design, which exists precisely so a
  session survives a process death.

## Affected documents

- `docs/specs/platform/room-lifecycle.md` — the mechanism: key table, claim/release scripts,
  adoption procedure, drain sequence, the four split-brain layers.
- `docs/specs/api-design/room-websocket.md` — rewrite § Room Affinity; scope the "no migration is
  ever required" claim to a single owner's lifetime; add V1 to § Per-Room Serialization and V2 to
  § Client Reconciliation; new codes `RECONNECT_REQUIRED`, `ROOM_UNAVAILABLE_RETRY`, `SLOT_RELEASED`.
- `docs/requirements/reconnection-flow.md` — FR-DC-006 (owner-pod loss), FR-DC-007 (Lobby
  carve-out), FR-HDISC-004 (migration window).
- `docs/requirements/platform-operations.md` — pod liveness lease, graceful-drain requirement,
  takeover NFR.
- `docs/specs/api-design/websocket.md` — replace the "the room is reassigned" hand-wave with the
  claim protocol.
- `docs/specs/game-host/game-host-internals.md` — §9.3 gains a "platform pod crash" paragraph
  documenting the existing property.
