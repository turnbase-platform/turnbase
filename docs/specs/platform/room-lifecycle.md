# Room Lifecycle — Ownership, Deadlines and Reconciliation

## Scope

How the Platform Monolith keeps room state correct across process death: which instance owns a room
and how that changes, how grace deadlines are enforced without in-process timers, how a game session
is torn down when a room stops needing it, and how the sweeps repair what crashes leave behind.

This is the mechanism behind three decisions — read them first for the reasoning; this document does
not repeat it:

- [ADR-0008](../../decisions/0008-room-ownership-lifecycle.md) — ownership is a lease-gated claim
- [ADR-0009](../../decisions/0009-grace-deadline-durability.md) — deadlines are persisted, swept
- [ADR-0010](../../decisions/0010-session-teardown-ordering.md) — teardown is a durable to-do

**Related:** [`data-model.md`](data-model.md) (every column named here),
[`../api-design/room-websocket.md`](../api-design/room-websocket.md) (the wire protocol this
produces), [`../../requirements/reconnection-flow.md`](../../requirements/reconnection-flow.md) and
[`../../requirements/game-rooms.md`](../../requirements/game-rooms.md) (the requirements),
[`../../requirements/platform-operations.md`](../../requirements/platform-operations.md) (FR-JOB-006…011).

**Out of scope:** the room event catalogue and command authorization (room-websocket.md), game
execution and Game Host recovery (`../game-host/game-host-internals.md`).

---

## 1. Ownership

### 1.1 Keys

> **Terminology.** "Pod" and "instance" refer to the same thing — one running Platform Monolith
> process. Redis keys and the WebSocket spec use `pod` (established by ADR-0002 and
> `room-websocket.md`); requirements and the relational schema use `instance`. They are
> interchangeable throughout this document.

| Key | Store | TTL | Written by |
|---|---|---|---|
| `pod:{podId}:alive` | Redis | 10s, renewed every 3s | each instance, for itself |
| `room:{roomId}:pod` | Redis | none | the claim and release scripts only |
| `room:{roomId}:epoch` | Redis | none | `INCR` by the claim script on every successful claim |
| `room.owner_instance_id`, `room.owner_epoch`, `room.ownerless_since` | Postgres | — | claim / release / sweep |
| `room.version` | Postgres | — | the owning instance, under the room lock |

One liveness key **per instance**, not per room: renewals are O(instances), and the ownership key
needs no renewal traffic at all. The Postgres columns mirror the Redis claim so that reconciliation
can *find* rooms whose owner is gone without scanning Redis, and so a Redis flush cannot erase the
knowledge that a room exists.

**`podId` is per-incarnation, not per-name** — the instance name plus a UUID generated at boot. A
stable name would let a *restarted* instance match the "already mine" branch of the claim script,
skip adoption entirely, and then produce versions from a freshly-zeroed in-memory counter: the
divergence of §2.1, self-inflicted. This bites hardest in the single-replica MVP, where restart is
the path that actually runs.

**`room:{roomId}:epoch` is the fencing token, and the room version is not.** The version is
*room*-scoped and both producers advance it through the same dense sequence, so a stale owner's
retained `expected` value is eventually *reached* by the legitimate owner, at which point the stale
CAS matches and commits. The epoch is *owner*-scoped and monotonic: an incumbent's epoch is strictly
ahead, so a stale owner's value is unreachable. See §1.5 layer 4.

### 1.2 Claim

A single atomic script. It is both the mutual exclusion and the failure detector — there is no
separate *instance* watcher anywhere in the platform. (The reconciliation sweep of §5.2 is a loop,
but it watches deadlines and divergence, not instance liveness.)

```lua
-- KEYS[1] = room:{roomId}:pod ; KEYS[2] = room:{roomId}:epoch
-- ARGV[1] = myPodId  (name + boot UUID)
local cur = redis.call('GET', KEYS[1])
if cur == ARGV[1] then
  return {1, cur, redis.call('GET', KEYS[2])}                        -- ALREADY MINE
end
if cur ~= false and redis.call('EXISTS', 'pod:' .. cur .. ':alive') == 1 then
  return {0, cur, 0}                                                 -- REDIRECT (owner alive)
end
-- free, or incumbent's lease has lapsed: take it and burn a new epoch
redis.call('SET', KEYS[1], ARGV[1])
local ep = redis.call('INCR', KEYS[2])
return {2, ARGV[1], ep}                                              -- ADOPTED
```

| Result | Caller does |
|---|---|
| `0` — redirect | Refresh the client's affinity hint to the named live owner and return a retry directive. Do **not** proxy. |
| `1` — already mine | Proceed, using the returned epoch. |
| `2` — adopted | Run the adoption procedure (§1.4) with the new epoch, then proceed. |

The epoch is incremented **inside** the same atomic script that transfers the key, so an epoch value
is bound to exactly one ownership tenure and no two tenures can share one.

Three actors claim: a client entering or re-entering a room, the reconciliation sweep when it must
act on a room whose owner is gone, and nobody. A room may remain unowned indefinitely; that is a
legitimate resting state, not a fault.

### 1.3 Release

```lua
-- KEYS[1] = room:{roomId}:pod ; ARGV[1] = myPodId
if redis.call('GET', KEYS[1]) == ARGV[1] then return redis.call('DEL', KEYS[1]) end
return 0
```

Compare-and-delete: an instance that has already lost ownership cannot release someone else's claim.
Release happens **only** on graceful shutdown (§1.6). A crash leaves the key, and it becomes
claimable once the liveness lease expires.

**A successful release also writes the Postgres mirror**, guarded on the releasing instance's own
epoch so a superseded instance cannot blank a live owner's row:

```sql
UPDATE room SET owner_instance_id = NULL, ownerless_since = now()
 WHERE room_id = :roomId AND owner_epoch = :myEpoch;
```

`owner_epoch` itself is **never** cleared — it must keep advancing monotonically across the gap, or
the next tenure's fence would be comparing against a reset value. This write is the only producer of
`ownerless_since`, and it is what makes the second branch of §5.2's unowned-room predicate reachable:
after a *crash* the row still names the dead instance (branch one), but after a clean drain it names
nobody, and without this statement a cleanly drained room would be invisible to reconciliation until
a client happened to return.

### 1.4 Adoption

Run by whichever instance receives result `2`:

1. Load the room from Postgres. It is authoritative; nothing is reconstructed from Redis.
2. Initialise the in-JVM version counter from `room.version`.
3. Set `owner_instance_id` and `owner_epoch` (the epoch returned by the claim script) and clear
   `ownerless_since` — **guarded on `WHERE room_id = :id AND owner_epoch < :myEpoch`**. If the guard
   fails, a later tenure has already recorded itself: abandon the adoption, do not run steps 4–8, and
   self-evict. Every subsequent mutation carries this epoch in its CAS (§1.5 layer 4).

   The guard is not decoration. The claim script is atomic, so two instances cannot hold the same
   epoch — but nothing orders their *Postgres* writes. An instance that claims epoch 5, stalls past
   its lease, and is superseded by epoch 6 would otherwise resume and stamp `owner_epoch = 5` over
   the incumbent's 6. Every one of instance 6's fenced mutations would then match zero rows and it
   would self-evict, dropping all of its clients, while steps 4–5 of the stale adoption put its
   *connected* players into grace windows and zeroed their `connection_count`. The epoch is monotonic
   precisely so that a `<` comparison can reject this; the room-scoped version could not.
4. For every participant with `connection_count > 0` and **no** reservation already outstanding, open
   a grace period at `now() + graceSeconds` — using `COALESCE`, so a reservation already running is
   **never** reset. A player 45 seconds into their window does not get a fresh 60.
5. Zero those participants' `connection_count`: their connections died with the previous owner.
6. If the room is `IN_PROGRESS`, re-create the session dispatcher and re-dispatch the head of
   `queue:{sessionId}`. This is safe with no Game Host change — replay by `sequence` and the delivery
   watermark already make it exactly-once.
7. Start the migration window (FR-HDISC-004) by setting
   `room.migration_window_expires_at = now() + 20s`. It is **persisted, not an in-JVM timer**, for the
   same reason grace deadlines are (ADR-0009): the instance holding it can die, and a window that
   evaporates on restart would silently re-enable instant host transfer during exactly the event it
   exists to cover. Its *expiry* is acted on by §5.1, not here — see the host-transfer duty there.
8. Emit **no** per-player disconnect events. By the invariant in §1.5 every client of this room is
   already disconnected, so the events would reach nobody and burn a version each. Reattaching
   clients learn the state from `ROOM_STATE.disconnectedPlayers`, which already carries
   `graceRemainingSeconds`.

### 1.5 Why two instances cannot both produce

Four layers, of which only the last is a correctness bound:

1. **Atomicity.** Only the script transitions the key; two claimants cannot both win.
2. **Liveness gate.** Takeover requires the incumbent's lease to be *absent* — at least one lease TTL
   of silence.
3. **Self-eviction, triggered on lease *lapse* — not on renewal failure.** Renewal is
   `SET pod:{podId}:alive <v> XX PX 10000`. The `XX` is the whole point: it succeeds only if the key
   still exists, so a **nil reply proves the lease lapsed** and is unconditionally fatal — drop every
   owned room, close those sockets with `RECONNECT_REQUIRED`, drop in-memory state, and **never
   recreate the key**. Those closes are instance-initiated in the sense of §1.6 and are suppressed
   identically: self-eviction is the ungraceful sibling of a drain — the instance has lost its lease
   and is severing sockets it may no longer serve, not observing players leaving.
   Triggering on "N consecutive renewal failures" instead would miss the
   dangerous case entirely: an instance that stalls for longer than the TTL (a stop-the-world pause)
   loses its lease, is taken over, then resumes and its *next* renewal succeeds — resurrecting a
   valid-looking lease having never observed a single failure. On the same tick the instance also
   re-verifies `room:{roomId}:pod == self` for each owned room and evicts per-room on mismatch, which
   bounds detection in the cases where the key changed but the lease did not (§5.4, flush).
4. **Owner-epoch fence.** Every room mutation commits
   `UPDATE room SET version = :new, ... WHERE room_id = :id AND version = :expected AND owner_epoch = :myEpoch`.
   A stale owner's epoch is strictly behind the incumbent's and is never reissued, so its update
   touches zero rows: it aborts, publishes nothing, and self-evicts.

   **The version alone would not do this.** It is room-scoped, and `:expected` must come from the
   instance's in-memory counter (re-reading the row inside the transaction would make the CAS
   vacuous). A stale owner therefore holds a fixed `expected` value while the legitimate owner
   advances the version densely from a lower number — and *passes through* that value, at which point
   the stale CAS matches and commits on top of the live owner. That is not an exotic interleaving; it
   is the expected outcome of any stale owner that retries. The epoch closes it because it only ever
   moves at a change of tenure.

**One deliberate carve-out.** "Every room mutation" means every mutation of the **`room` row**.
Resolving a reservation (§3.2) touches `room_participant` only, carries no version CAS, and never
bumps `room.version` — it is guarded by the reservation-id CAS instead. This is what lets a
*non-owning* instance perform an early release (FR-EXPIRY-004) safely: if it took the version fence
it would move the healthy owner's expected version out from under it and evict the owner of an
unrelated room, dropping every client attached to it. Only the owning instance performs
version-bumping mutations.

**Scope, stated precisely: the fence covers the `room` row.** It does not cover Redis counters, the
session queue, gRPC calls, or STOMP publishes. Therefore one ordering rule governs everything else:
**every externally visible side effect — STOMP publish, gRPC to the Game Host, session-queue enqueue,
`seq:` allocation — is issued only after the fenced commit returns success.** Without this a stale
owner could allocate a fresh valid `sequence` (which neither replay nor the delivery watermark
dedups, since both defend against a repeated sequence rather than two producers) or send a
`player_left` before its CAS was ever attempted.

Layer 4 is what makes layer 2's residual hole acceptable: a Redis flush or a `maxmemory` eviction
drops a healthy instance's lease key and permits a wrongful takeover. **No divergence becomes durable
in the `room` table**, and client-visible divergence is bounded by the stale owner's next write *or
its next ownership re-check* (layer 3), whichever comes first — rather than being unbounded, which is
what it would be if only writes could reveal the loss. Reads are not fenced: a stale owner can serve
`REQUEST_ROOM_STATE` from stale memory until one of those two events. Because eviction produces this
state with no operator action, the platform Redis is required to run `maxmemory-policy noeviction`,
or to hold ownership keys in a dedicated logical database.

> **Invariant I1 — for every claim path, the previous owner either has no live sockets for that room,
> or severs them within the eviction guard band.**
> A crash satisfies the first clause (sockets died with the instance); a drain satisfies it (evict,
> then release). The **sweep satisfies only the second**, and the distinction matters: the takeover
> trigger is lease *absence*, which covers crash, partition-from-Redis, flush, key eviction and long
> pauses — and in most of those the previous owner's sockets are alive. An unowned room is therefore
> **not** guaranteed to be a clientless one, and any argument assuming otherwise is circular, since
> layer 4 exists precisely because "lease absent ⇒ instance dead" is false. Stated in this bounded
> form, I1 is still strong enough to support §1.4's decision to emit no disconnect events on
> adoption. A future live-migration feature would have to replace it — and would then need the
> `epoch` envelope escape hatch in §2.3.

### 1.6 Graceful shutdown

Same policy as a crash — these are involuntary disconnects — but a distinct fast lane, because
applying the crash path to a deploy means a lease wait plus a full grace-period scare for every
player on the instance.

**Every socket this sequence closes is marked instance-initiated, and the disconnect handler must
skip such closures entirely.** Closing a socket fires `SessionDisconnectEvent` exactly as a network
drop does, and in a Lobby room `../../requirements/reconnection-flow.md` FR-DC-002 makes a disconnect
an immediate leave. Chained with `../../requirements/game-rooms.md` FR-XFER-002 — close a room whose
host has left with no humans remaining — an unsuppressed drain closes every Lobby room on the
instance, which is precisely the cascade FR-DC-007 exists to prevent, reached by a route its wording
does not cover. FR-DC-006/007 classify owner-instance loss as a mass event in *every* room state; a
drain is the graceful form of the same event and inherits the same classification.

Mechanically: the drain tags the STOMP session before closing it, and the disconnect handler returns
early on a tagged session without decrementing `connection_count`, without opening a reservation and
without evaluating FR-XFER-002. The participants' `connection_count` is instead zeroed by the *next*
owner during adoption (§1.4 step 5), which is the actor that can also open the reservations FR-DC-007
does permit.

1. Fail readiness; the ingress stops routing new traffic here.
2. **Enter drain mode: refuse to claim ownership of any new room.** An in-flight room creation can
   arrive after the shutdown signal, so the readiness gate alone is not sufficient.
3. Finish in-flight mutations per owned room and flush.
4. Send `RECONNECT_REQUIRED` to attached clients as a STOMP `ERROR` frame — which closes the
   connection, matching the other connection-terminating codes in
   [`../api-design/room-websocket.md`](../api-design/room-websocket.md) § Error Codes. It is an
   explicit instruction to clear the affinity hint and re-run the join flow immediately rather than
   wait out disconnect detection.
5. Release each owned room (§1.3); delete `pod:{podId}:alive`.
6. Exit. The container termination grace period must exceed steps 3–5.

Because ownership is *released*, the next claimant takes the free branch with **no lease wait**:
reconnection is sub-second, and the whole event is normally absorbed inside the migration window with
no grace periods opened at all.

### 1.7 Routing

The affinity hint is a hint. When the instance it names is absent from the ready endpoint set, the
ingress falls back to normal load balancing (FR-DEPLOY-002); the receiving instance then resolves
ownership itself via §1.2.

For up to one lease TTL after a hard crash, the claim returns `0` naming the dead instance, and a
client would bounce. The landing instance retries the claim internally with backoff for a few hundred
milliseconds, then returns `ROOM_UNAVAILABLE_RETRY` with a `retryAfterMs`. The retry is deliberately
short: it holds a request thread, and on a rolling deploy *every* client reconnects at once, so a
multi-second internal retry converts a routing hiccup into thread-pool exhaustion. Worst case ≈10s
of client-side retrying, bounded by the lease TTL.

**Claiming and subscribing must interlock.** The claim runs on the REST join or rejoin that sets the
affinity hint — but between that call and the client's STOMP `SUBSCRIBE`, another instance's sweep
can take a free room. The WebSocket handler therefore **re-verifies ownership at subscribe time** and
rejects a subscription to a room it does not own with `ROOM_UNAVAILABLE_RETRY`, rather than serving
it. Holding a client's socket is never evidence of owning that client's room.

---

## 2. Versioning

### 2.1 Mutation sequence

Inside the room lock:

1. Read state.
2. Validate preconditions.
3. Apply the mutation **and commit `version = n`** — the fence CAS of §1.5.
4. Publish the delta at version `n`.
5. Release the lock.

**The nesting is normative: lock outer → transaction inner → publish after the commit returns, before
the lock is released.** The obvious Spring idiom — `@Transactional` on the handler with the lock
taken inside it — commits *after* the method returns, which is after the publish and after the lock
is released, silently reinstating the exact race V1 exists to close. This is too easy to get wrong to
leave implicit.

Two consequences of holding a lock across a commit, both requiring bounds rather than hope:

- A stalled database now blocks **every** operation on that room, including `REQUEST_ROOM_STATE` and
  REST joins, and piles inbound STOMP threads behind it — an instance-wide exhaustion path rather
  than a room-local slowdown. Set a statement timeout and a lock-acquisition timeout; on expiry, fail
  the command and publish nothing, but **do not** self-evict: a timeout is not proof of lost
  ownership.
- A failed CAS leaves the in-memory room state dirty, since step 3 mutated it before committing. This
  is why self-eviction (§1.5 layer 3) drops in-memory state rather than attempting to repair it. If
  the commit succeeded but its response was lost, do not publish — the client repairs from the
  resulting forward gap.

**Step 3 must precede step 4.** Moving the commit earlier *within the same critical section* cannot
let a higher-version delta be queued before a lower one, so the ordering guarantee that
`room-websocket.md` derives from publishing inside the lock is untouched. With commit-before-publish,
`room.version ≥ every version ever broadcast`, so an adopting instance resuming at
`room.version + 1` can never reuse a version a client has already applied. A crash between commit and
publish leaves a forward *gap*, which the client detects and repairs with a resnapshot.

Publishing inside the lock still guarantees that no higher-version delta is queued before a lower one,
which is the ordering property room-websocket.md relies on.

### 2.2 Client rule

A client **assigns** `localVersion` from every `ROOM_STATE` snapshot; it never takes the maximum of
the snapshot and its current value. After an ownership change a stale-high `localVersion` must adopt
the snapshot's lower value, or the client will silently discard every subsequent delta.

This is **defence in depth, not a fix for a stated defect**: the snapshot-delivery flow already said
"assign", and §2.1 makes a backwards jump unreachable in the first place. It earns its place by
covering the window where the fence has failed — a wrongful takeover under flush or eviction (§1.5)
— which is exactly when a client could hold a `localVersion` above the truth. A client that has
optimistic local state pending when a snapshot moves `localVersion` backwards must discard that
pending state rather than replay it.

### 2.3 If I1 is ever relaxed

Add an `epoch` to the event envelope, incremented on every ownership change, with the rule "epoch
changed ⇒ force resnapshot regardless of version." Not built now: under I1 it is dead weight, because
ownership never changes without the client reconnecting and resnapshotting anyway. Recorded so that a
future live-migration proposal knows the cost it must pay.

---

## 3. Grace deadlines

### 3.1 Opening

Under the room lock, on the owning instance, when a participant's `connection_count` reaches zero in
an `IN_PROGRESS` room:

```sql
UPDATE room_participant
   SET connection_count = 0,
       grace_reservation_id = :newReservationId,
       grace_expires_at     = now() + :graceSeconds * interval '1 second'
 WHERE room_id = :roomId AND user_id = :userId
   AND role = 'PLAYER'
   AND left_at IS NULL
   AND grace_reservation_id IS NULL;
```

`now()` is the **database** clock — the single time authority for the whole mechanism.
`:graceSeconds` is read at disconnect time; because the stored deadline is absolute, a later config
change never moves a window already running.

After commit: bump the version, broadcast `PLAYER_DISCONNECTED`, and apply host transfer
(FR-HDISC-001) unless the migration window is open.

### 3.2 Resolving — one statement, every path

```sql
UPDATE room_participant
   SET left_at = now(), leave_reason = :reason,
       grace_reservation_id = NULL, grace_expires_at = NULL,
       lost_announced_at = CASE WHEN :announceInline THEN now() ELSE NULL END
 WHERE room_id = :roomId AND user_id = :userId
   AND grace_reservation_id = :reservationId
   AND left_at IS NULL
   AND (:dueCheck = false OR grace_expires_at <= now())
RETURNING team_id;
```

Every predicate earns its place:

- **`grace_reservation_id = :reservationId`** — a stale actor holding a previous reservation (the
  player reconnected, then dropped again) matches nothing.
- **`left_at IS NULL`** — a kick (FR-KICK-003), voluntary leave, or early release already resolved it.
- **`grace_expires_at <= now()`** (expiry only) — **this is what makes clock skew a non-issue.** An
  instance with a fast clock evaluates early, updates zero rows, and moves on. No other clock can
  release a slot early.
- **`lost_announced_at`** — set to `now()` when the resolving instance owns the room and will
  broadcast immediately, and left null when it does not, which is the *only* thing that marks a
  resolution as owing a deferred tail (§5.1 duty 2). `:announceInline` is `true` exactly when the
  claim of §3.3 returned `1` or `2`. Every other path that sets `left_at` — voluntary leave, kick,
  closure, account deletion on the owning instance — must stamp it too, for the same reason: an
  unstamped release is a promise that somebody will announce it.

**The rowcount is the entire idempotency story.** `1` → this caller won and owns *all* side effects.
`0` → someone else resolved it, or it is not due → do nothing. Sweep and any other actor therefore
cannot double-execute, and no deduplication table exists anywhere.

Reconnect is the mirror: `connection_count = connection_count + 1`, clearing the reservation, guarded
on `grace_reservation_id IS NOT NULL`. Rowcount `1` → `PLAYER_RECONNECTED`.

**Rowcount `0` is three-way ambiguous** — already resolved, not yet due, or superseded by a newer
reservation — and the reconnect path must not treat all three alike. It re-reads the row and branches
on actual state: released ⇒ `SLOT_RELEASED` and the late-join path (FR-REJOIN-007); a *different*
reservation outstanding ⇒ the client is racing its own newer disconnect and simply retries. The sweep
needs no such branch, since for it every `0` means "someone else won", which is a no-op either way.

### 3.3 Side effects of a won expiry

In the transaction:

1. The `UPDATE` above.
2. Insert the `player_left` row into `game_input_outbox` —
   **only if `room.active_session_id IS NOT NULL`.**
   A Lobby room has no session (§3.4), and `game_input_outbox.session_id` is `NOT NULL`
   (`data-model.md` §4.2), so an unconditional insert aborts the whole transaction on a room whose
   reservation §1.4 step 4 opened precisely because FR-DC-007 required it. The reservation would then
   never resolve and the 5-second sweep would retry it indefinitely — a stuck room and an error loop,
   from the one path that is guaranteed to run on every rolling deploy.

After commit, by the winner only:

3. Bump version; broadcast `PLAYER_LOST` with the `team_id` from `RETURNING`; set
   `lost_announced_at`.
4. Evaluate closure — **only if the room is `IN_PROGRESS`**. If no participant remains with
   `left_at IS NULL AND role = 'PLAYER'`,
   detach the session (§4) with next state `CLOSED` and `closed_reason = GRACE_EXPIRED_NO_HUMAN`
   (distinct from the participant's own `leave_reason = GRACE_EXPIRED` — one records why the room
   closed, the other why a slot was released). Because a
   participant in grace still has `left_at IS NULL`, this single predicate keeps the room alive while
   *any* human still holds a reservation — exactly FR-HDISC-003.

**The predicate has no "and not an AI" clause, and in v1 it needs none.** `room_participant` holds
humans only — an AI has no `app_user` row and the table's primary key is `(room_id, user_id)` — and
`aiPlayers` is always empty ([`../api-design/room-websocket.md`](../api-design/room-websocket.md)).
When the AI interface lands (`game-contracts.md` OQ-002) it must add both a representation *and* this
clause; the OQ is recorded as owing that pair rather than only the interface, because the closure
question — does a room of AI players survive the last human? — is decided here and not there.

**A `LOBBY` room is deliberately exempt from step 4, and the exemption is load-bearing.** Reservations
normally exist only in `IN_PROGRESS` rooms (§3.1, FR-DC-002), but §1.4 step 4 opens them in *any*
state, because FR-DC-007 forbids treating owner-instance loss as an immediate leave in a Lobby room —
without that carve-out a rolling deploy would read as every host leaving and close every Lobby room
on the platform (FR-XFER-002). Those Lobby reservations do expire, and if step 4 ran on them it would
reintroduce exactly the deletion FR-DC-007 exists to prevent — one sweep interval later instead of
immediately, and with a `closed_reason` (`GRACE_EXPIRED_NO_HUMAN`) whose requirement, FR-HDISC-003,
is explicitly scoped to In Progress. There is also no session to detach: `active_session_id` is null,
so §4 has no meaningful `sessionId` argument. An emptied Lobby room is instead collected by the
idle-Lobby duty (§5.2) under `IDLE_TIMEOUT`, which is the reason code that actually describes it.

**Step 2 carries the same exemption, for a different reason.** Step 4's is a requirements argument —
FR-HDISC-003 is scoped to In Progress. Step 2's is a schema constraint: there is no `session_id` to
write. Both exemptions have the same trigger (`active_session_id IS NULL`) and must be kept together;
the two were separated once and the result was a transaction that could never commit.

**Ownership here is decided by running the claim (§1.2), not by consulting a local set** — the same
test `detachSession` step 0 uses, and specifying it matters because the two plausible readings settle
this scenario minutes apart. On result `1` or `2` the acting instance owns the room and runs steps 1–4
itself; on result `0` the room has a live owner elsewhere, so it performs steps 1–2 only, leaves
`lost_announced_at` null to mark the resolution *unannounced*, and the owning instance executes
**steps 3 and 4 together** on its next tick. The claim is what collapses the common case: a player
early-releasing (FR-EXPIRY-004) from a room whose owner has already died adopts it on the spot and
closes it immediately, instead of waiting out a reconciliation interval for someone else to notice.

**Both steps, not just the announcement.** Step 4 is the closure evaluation, and deferring the
broadcast while dropping the evaluation produces a permanent stuck room by an entirely ordinary
route: the last human of an In Progress room holds a reservation, joins another room via a REST call
that lands on a non-owning instance, FR-EXPIRY-004 fires there, `left_at` is set — and no actor ever
asks whether the room still has a human. The room stays In Progress forever with a live session
pinning guest-execution resources. That is exactly the stuck-room class this design exists to
remove, so the deferred tail is defined as the *whole* post-commit sequence.

### 3.4 Reporting remaining time

`ROOM_STATE.graceRemainingSeconds` is **derived, never stored**:

```
ceil(greatest(0, extract(epoch from grace_expires_at - now())))
```

`disconnectedPlayers` includes only rows with `grace_expires_at > now()`, so a due-but-unswept
reservation is never advertised as live, and the value is clamped to a minimum of 1 — reporting `0`
would render as expired for a slot that is still reserved. Because it derives from a persisted
absolute timestamp, it stays correct across restart and ownership change.

**Consequence worth stating:** between a deadline elapsing and the sweep resolving it (at most one
sweep interval) a player appears in neither the connected set nor `disconnectedPlayers`. This is
deliberate — advertising a countdown that has already run out is worse — and clients should render
such a player as present but unavailable rather than inventing a zero timer.

---

## 4. Detaching a session

One method, five callers: host leave with no humans left; grace expiry with no human connected; **the
normal end of a game**; retry-limit permanent failure; and the reconciliation sweep. The next room
state is `CLOSED` for closure paths and `LOBBY` for game end.

**The detaching actor must hold the room claim before it commits or broadcasts.** Two of the five
callers arrive on threads that own nothing: account deletion is a REST call landing on an arbitrary
instance, and guest-account cleanup (FR-JOB-001) is a scheduled job. Under ADR-0002 there is no
cross-instance fan-out, so a non-owner's `ROOM_CLOSED` reaches **nobody** — and the audience is real,
because closure evicts spectators, who are connected at that moment and are not counted by the
"no human player remains" test.

**A caller that cannot claim the room defers through the existing deferred-tail mechanism, not
through a table of its own.** It commits the durable half — the participant departures, with
`lost_announced_at` left null per §3.2 — and returns. The owning instance's next deadline-sweep tick
picks the room up under §5.1 duty 2, which broadcasts and **evaluates closure** while holding the
claim. There is no `room_closure_owed` table and no third durable work table: duty 2 already does
exactly this job for grace expiries resolved by a foreign instance, and a closure owed by an account
deletion is the same shape of debt. This makes REST- and job-initiated closure asynchronous, bounded
by one sweep interval, which is the correct trade — a spectator silently stranded in a subscription to
a dead room has nothing to repair it.

**Duty 2's closure evaluation must therefore cover the Lobby host-departure case, not only
FR-HDISC-003.** When the departed participant was `room.host_user_id`, the tail additionally applies
FR-XFER-001's transfer if another human is connected, and closes with `NO_PLAYERS_REMAINING` if none
is — in **Lobby as well as In Progress**, because `../../requirements/game-rooms.md` FR-XFER-002
scopes immediate closure to explicit departures in any state and account deletion is named there as
one. The `GRACE_EXPIRED_NO_HUMAN` path (§3.3 step 4) stays In-Progress-only and stays distinct; the
two produce different `closed_reason` values because they mean different things to a player.

```
detachSession(roomId, sessionId, reason, nextState):
  0. Claim the room (§1.2). On redirect (result 0), commit the participant departures with
     lost_announced_at NULL and return — §5.1 duty 2 on the owning instance performs the
     announcement and the closure evaluation. Never commit the room-row mutation or broadcast
     without the claim.

  TX — Postgres only. No gRPC, no Redis, no remote call of any kind.
    1. SELECT ... FROM room WHERE room_id = :roomId FOR UPDATE
    2. if room.active_session_id <> :sessionId: COMMIT; return    -- already detached, idempotent
    3. UPDATE room
          SET state = :nextState, active_session_id = NULL,
              version = :expected + 1,
              closed_at = CASE WHEN :nextState = 'CLOSED' THEN now() END,
              closed_reason = CASE WHEN :nextState = 'CLOSED' THEN :reason END
        WHERE room_id = :roomId AND version = :expected AND owner_epoch = :myEpoch;
       -- zero rows ⇒ a later tenure owns this room: abort the transaction,
       --   publish nothing, self-evict (§1.5 layer 4). Do NOT retry in place.
       release slots / clear reservations / reset readiness per the path
    4. INSERT INTO session_teardown (session_id, room_id, reason)
         VALUES (...) ON CONFLICT (session_id) DO NOTHING
    5. DELETE FROM game_input_outbox
        WHERE session_id = :sessionId AND dispatched_at IS NULL   -- required; data-model.md §4.2
    6. COMMIT

  after commit, best-effort, outside any transaction:
    7. broadcast ROOM_CLOSED (or the game-end transition) ; evict spectators
    8. terminateAndCleanup(sessionId, reason)
```

```
terminateAndCleanup(sessionId, reason):
  a. TerminateSession(sessionId, reason), deadline 2s
  b. on OK:  delete session:/routing:/queue:/seq:/delivered:/failcount:{sessionId}
             DELETE FROM session_teardown WHERE session_id = :sessionId
  c. on any error: log WARN, record attempts++ / last_error / next_attempt_at on the
     session_teardown row, and leave it for the sweep. Never throw to the caller.
     (The inline attempt is the common failure — a Game Host restart — so leaving the
     bookkeeping to §5.2 would hide the first and most frequent one.)
```

**Step 3 is a fenced, version-bumping mutation like every other write to the `room` row**, and it was
once neither. §1.5's rule is "every mutation of the `room` row", with exactly one carve-out —
resolving a reservation, which touches `room_participant` only. Closure is not that carve-out: it
writes `state`, `active_session_id`, `closed_at` and `closed_reason`.

Both halves matter and they fail differently. Without the **epoch fence**, a stale owner can close a
room under the legitimate owner — the precise scenario ADR-0008 introduced the epoch for, and worse
here than elsewhere because closure is irreversible. Without the **version bump**, clients receive a
`ROOM_CLOSED` at a version they have already applied and discard it silently
([`../api-design/room-websocket.md`](../api-design/room-websocket.md) Client Reconciliation drops
`delta.version <= localVersion`), so the room vanishes server-side while every attached client still
renders it as live.

Step 0's claim is what supplies `:myEpoch`, and the `FOR UPDATE` of step 1 is what supplies
`:expected` — closure is the one mutation that may read the version inside the transaction, because
its caller may be an instance that has just adopted the room and has no in-memory counter yet. That is
safe here and nowhere else: the epoch, not the version, is doing the fencing, and the row lock is
already held.

**The gRPC call is never inside the transaction.** The room row is taken `FOR UPDATE` by every join,
leave, reconnect and readiness path; holding it across a call to a service that can hang turns one
slow Game Host into room-wide lock contention and connection-pool exhaustion. It also buys nothing —
Postgres and the Game Host cannot commit atomically regardless. The outbox row *is* the substitute
for that atomicity.

**Broadcast after commit, before teardown.** Room membership is settled the instant the transaction
commits; making players wait on a Game Host RPC to learn their room closed couples client-visible
latency to bookkeeping they have no stake in. Never before commit — a rollback would leave clients
believing a live room was gone.

**The window between broadcast and terminate, where the session is briefly still live, needs no
machinery — but not for the obvious reason.** There is **no room-scoped authorization rule** to lean
on: game-destination authorization in [`../api-design/websocket.md`](../api-design/websocket.md) is
*session*-scoped ("the session exists and is active, not terminated, not past `game_over`"), so
closing a room rejects nothing by itself. Nor is the room empty — closure evicts spectators, who are
attached at that moment, and at game end everyone is attached in Lobby.

The window is instead safe **per caller**: on the closure paths no human player remains by
construction, so nobody is authorized to send an action; game end is covered by "not past
`game_over`" plus FR-EFF-006/007; retry-limit failure by "not terminated". On the failure path the
window is **unbounded** — it lasts until the sweep succeeds — which is why `turnbase.teardown.owed`
is alerted on (FR-ALERT-007) rather than merely logged.

---

## 5. The sweeps

### 5.1 Deadline sweep — 5s, ownership-partitioned (FR-JOB-006)

```sql
SELECT rp.* FROM room_participant rp JOIN room r USING (room_id)
 WHERE rp.grace_expires_at <= now() AND rp.left_at IS NULL
   AND r.owner_instance_id = :myInstanceId;
```

Ownership partitions the rows, so no two instances select the same one — FR-JOB-005's intent met by
partitioning rather than by a global lock, which would serialize every instance's expiry behind one
leader for no correctness gain. The winner must be the owning instance because it is the only one
that can broadcast to the room's topic.

**The partition has a cost that must be stated rather than discovered: an unowned room is swept by
nobody.** Its deadlines are frozen — correctly, since they are absolute timestamps and nothing is
lost — until §5.2 adopts it, up to one 60s reconciliation interval later. So NFR-JOB-001's
`deadline + 5s` holds only for a room with a live owner, and the crash case is bounded by NFR-JOB-002
on top of it. Widening this query to unowned rooms would not help: this instance could not broadcast
into a room it does not own, which is the whole reason the partition exists.

The tick runs four duties, **in this order**:

1. **Due expiries** — the query above, resolved per §3.2 with the side effects of §3.3.
2. **Deferred tails** — resolutions committed by a foreign instance, identified by
   `left_at IS NOT NULL AND lost_announced_at IS NULL AND leave_reason IN ('GRACE_EXPIRED',
   'EARLY_RELEASE', 'LEFT')` on a room this instance owns: bump version → broadcast `PLAYER_LOST` →
   set `lost_announced_at` → **evaluate closure**. The closure evaluation is the load-bearing half;
   omitting it strands rooms whose last human left from another instance.

   **Both halves of the predicate are required and neither is redundant.** `lost_announced_at IS NULL`
   is the primary test and is now written by every inline path (§3.2), so a resolution that was
   already announced cannot match. The `leave_reason` list is the backstop: it is the set of reasons a
   *foreign* instance can produce, and it excludes `KICKED`, `ROOM_CLOSED` and `GAME_ENDED`, which are
   only ever produced by the owner under the room lock and can never legitimately owe a tail. Without
   the backstop, one path that forgets to stamp the column resurrects the defect as a phantom
   `PLAYER_LOST` for every ordinary leave, one sweep interval late — visible to players, and easy to
   read as a reconnection bug rather than a sweep bug.

   The tail also carries the **host disposition**. If the departed participant was
   `room.host_user_id`, apply FR-XFER-001's transfer to the next human by join order when one is
   connected, and close the room with `NO_PLAYERS_REMAINING` when none is — in Lobby as well as In
   Progress. This is the path that makes account deletion (`data-model-accounts.md` §5) and guest
   cleanup work from a non-owning instance, and without it a deleted host's room keeps a
   `host_user_id` naming a released participant, which is the dangling reference `data-model.md` §1
   makes the column nullable to avoid.
3. **Elapsed migration windows** — `migration_window_expires_at <= now()` on a room this instance
   owns. Clear the column, and if the host is disconnected or released while another human is
   connected, perform the FR-HDISC-001 transfer now. **Without this duty FR-HDISC-004 has no
   mechanism at all:** §1.4 opens reservations directly and never routes through §3.1, so §3.1's
   "apply host transfer unless the migration window is open" never executes on the adoption path. A
   host who does not come back would otherwise leave the room running headless — and once their grace
   expires, `room.host_user_id` would name a released participant, the dangling reference §1 of
   `data-model.md` makes the column nullable to avoid.
4. **Outbox drain** — see below.

Ordering matters between 2 and 4: a closure in duty 2 discards that session's undelivered rows (§4
step 5), so draining first would dispatch a `player_left` for a session about to be terminated,
possibly drawing effects or a `game_over` that then race the teardown. Closing first is the cheaper
and quieter order.

**The outbox drain is deliberately *not* ownership-partitioned.** It allocates and persists each row's
`sequence` before its first dispatch (`data-model.md` §4.2), and takes rows
`FOR UPDATE SKIP LOCKED` across **all** sessions, not just those of rooms this instance owns. The
partition above exists because only the owner may broadcast to a room's topic — but a drain is a gRPC
call to the Game Host, not a STOMP publish, and needs no claim whatsoever. Partitioning it would
reintroduce a bounded form of the exact failure the outbox was built to remove: a player early-released
from a non-owning instance (FR-EXPIRY-004) while the owner then crashes would leave `player_left`
undelivered for the whole adoption window, and the game would sit on a turn that never comes
(ADR-0009). Concurrent drains are safe precisely because the `sequence` is persisted on the row.

Duties 1–3 are the **only** drivers of expiry, host transfer and deferred announcement. If a latency optimization is ever added, it must call the
identical statement in §3.2, and the integration suite must pass with that optimization disabled — the
moment it does not, the optimization has acquired logic it was never allowed to have.

### 5.2 Reconciliation — 60s, single instance (FR-JOB-007)

| Duty | Predicate | Action |
|---|---|---|
| Owed teardown | `session_teardown` row with `next_attempt_at <= now()` | `terminateAndCleanup`; on failure `attempts++`, backoff 10s doubling to a 5min cap |
| Orphaned artifacts | Redis session keys whose room is absent or `CLOSED`, key age > 10 min | delete the whole key family |
| In Progress, no session | `state = IN_PROGRESS`, session record absent, **flagged on a previous run** | fail back to **Lobby** via FR-FAIL-005: clean keys, reset readiness, notify participants (`GAME_ENDED`, `readinessReset: true`). No history entry |
| Idle Lobby | `state = LOBBY`, zero connected participants, `last_activity_at` older than the idle window | close with `IDLE_TIMEOUT` |
| Unowned room | `owner_instance_id` naming an instance with no live lease, or null with `ownerless_since` set | claim (§1.2) and adopt (§1.4), so deadlines can be enforced |

Rows are taken `FOR UPDATE SKIP LOCKED` in batches.

**Failing back to Lobby rather than closing** is deliberate: closing destroys a room people may still
be sitting in, while Lobby is recoverable and reuses a path that already exists and already has a
client story. If the room really is abandoned, the idle duty collects it later. **This duty has no
closure branch** (`IMP-GATE-55`): `detachSession`'s shared skeleton
([`flows/07-room-closure.md`](../flows/07-room-closure.md)) has exactly two non-success outcomes — a
deferred claim, retried next tick, and step 2's idempotent no-op — and neither is a reason for this
duty to close the room instead.

**No Game Host probe.** The session record is the source of truth: a host that lost local state
recovers from it, and a host with no record returns `NOT_FOUND`. If the record is absent the session
is unrecoverable by definition, so a probe would add a failure mode and no information.

### 5.3 Purge — daily (FR-JOB-009)

Delete rooms `CLOSED` longer than the retention window; participants, teams and invites cascade.
Game history is keyed by session and carries no room foreign key, so it is untouched.

### 5.4 Safety preconditions (FR-JOB-008)

Three guards, each closing a specific false positive:

1. **Reachability.** Any datastore command that errors or times out aborts the whole run with
   `aborted{reason=redis_unavailable}`. **An error is never read as an absence.** This is the exact
   line between unavailability (FR-FAIL-006's scope, handled elsewhere) and data loss.
2. **Two strikes.** A divergence must persist across two consecutive runs; the first observation is
   recorded in `room.reconcile_flagged_at` so it survives a restart, and is cleared as soon as the
   room looks healthy. **The unowned-room duty is exempt**: an absent liveness lease is not an
   inference that needs corroborating — it is the claim script's own precondition, re-evaluated
   atomically at the moment of the claim — and requiring a second run would double NFR-JOB-002 to no
   purpose. The other three repair duties are all inferences about missing state and do take the two
   strikes.
3. **Startup suppression.** No repair within 120s of instance start. A just-booted instance has not
   had the Game Host re-register and would read a legitimately recovering system as a broken one.
   The sweep still runs, detects and logs during this window — it simply does not act. This is the
   inverse of the prototype's startup-cleanup design, and the inversion is the point.
   **The unowned-room duty is exempt from this guard too**, for the same reason it is exempt from
   guard 2: adoption repairs nothing and infers nothing about Game Host state — it re-establishes an
   owner from an absent Redis lease. Suppressing it would be actively harmful in the single-replica
   MVP, where a full-stack restart is the path that actually runs: every room would be unswept for
   two minutes, blocking expiries, deferred announcements and closures, and breaching NFR-JOB-002's
   bound outright. Duties (b), (c) and (d) are inferences about missing state and do keep the guard.

Additionally, if `platform:sentinel` is absent while Redis is reachable, the datastore was reset:
repairs proceed, but are reported as **one** mass-loss event rather than one warning per room.

---

## 6. Observability

| Metric | Type | Tags | Answers |
|---|---|---|---|
| `turnbase.reconcile.candidates` | gauge | `duty` | **the stuck-room detector** — non-zero and *flat* across runs means detected but never repaired |
| `turnbase.reconcile.repairs.total` | counter | `duty`, `result` | steady state ~0; drives FR-ALERT-006 |
| `turnbase.rooms.in_progress_without_session` | gauge | — | the prototype's "stuck IN_PROGRESS" class, directly observable |
| `turnbase.grace.expiry_lag.seconds` | timer | — | `now − deadline` at repair; validates NFR-JOB-001 |
| `turnbase.teardown.owed` | gauge | — | outstanding teardown debt; drives FR-ALERT-007 |
| `turnbase.room.ownership.takeovers.total` | counter | `kind=adopt_free\|takeover\|drain_release` | distinguishes clean deploys from crash takeovers |
| `turnbase.job.aborted.total` | counter | `job`, `reason` | proves the §5.4 guards fire rather than being silently disabled |

Applied repairs log at **WARN**: a repair is always evidence of a defect elsewhere, and the level
should say so. Detections log at INFO; a mass-loss event logs ERROR once.

---

## Open Questions

- **OQ-001 — Lease numbers are chosen, not derived.** 10s TTL / 3s renew / 6s self-evict / 20s
  migration window / 5s and 60s sweep intervals are reasoned defaults with no measurement behind
  them. They should be revisited against real reconnect latencies once the stack runs; the
  relationships that must hold (self-evict < TTL, renew ≪ TTL, grace > restart interval) matter more
  than the absolute values.
- **OQ-002 — Self-eviction uses a local monotonic clock while the lease expires in Redis.** The 4s
  guard band covers skew on a single node comfortably. Before any multi-node deployment this
  assumption should be re-examined, since it is the one place a local clock still affects a
  correctness bound.
- **OQ-003 — Flapping clients.** Each disconnect starts a fresh window (FR-GRACE-006), so a
  connect/disconnect loop can hold a slot indefinitely. The WebSocket reconnect lockout in
  `../api-design/rate-limiting.md` dampens this; whether a hard cap on reservations per session is
  also needed is deferred until the behaviour is observed.
