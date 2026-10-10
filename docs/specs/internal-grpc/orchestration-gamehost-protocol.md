# Orchestration Service ↔ Game Host gRPC Protocol

The internal, service-to-service contract between the **Orchestration Service** (a
domain within the Platform Monolith) and the **Game Host** service. The wire
contract is defined in [`gamehost.proto`](gamehost.proto); this document records
the design decisions, semantics, and operational rules behind it.

This is **not** a client-facing API. Player-facing real-time traffic uses
STOMP-over-WebSocket (see [../api-design/websocket.md](../api-design/websocket.md)).

**Requirements:** `docs/requirements/platform-architecture.md` (FR-ORCH-*, FR-ROUTE-*,
FR-REG-*, FR-SESS-*, FR-CTX-*, FR-FAIL-*, FR-SCALE-*) and
`docs/requirements/game-contracts.md` (FR-IN-*, FR-RESP-*, FR-EFF-*, FR-OUTCOME-*).

---

## Topology decision

> **The channel of record is the Redis routing table + action queue. gRPC
> connections are disposable.**

Three Must-priority requirements (FR-ORCH-002, FR-ORCH-006, FR-ORCH-007) require the
Orchestration Service to run as **stateless, interchangeable replicas** behind a load
balancer where **any replica can route any input** to the correct Game Host. All
routing state lives in Redis (`sessionId → Game Host instance`, CON-011).

Three topologies were evaluated:

| Option | Shape | Verdict |
|--------|-------|---------|
| **A — dual service, unary dispatch** | Game Host serves the dispatch RPCs; Orchestration serves the registry RPCs. Any replica reads Redis and dials the target pod. | **Chosen** |
| B — single bidi stream, Game Host initiates | One long-lived stream multiplexes everything; it terminates at one replica. | Rejected |
| C — dual service, server-streaming effects | Like A, but effects stream back. | Fallback only |

**Why A.** Unary request → unary response maps 1:1 onto the game handler's
synchronous, atomic contract (one input in, one complete ordered effect list out;
game-contracts.md FR-RESP-001a/004). Dispatch is "read `sessionId → host` from Redis,
dial that pod, call, deliver, dequeue" — nothing requires *this* replica to have done
the previous step, so statelessness holds exactly as FR-ORCH-002 demands. Failure
handling is conventional gRPC: a dead host surfaces as `UNAVAILABLE`, the action stays
in the Redis queue (FR-ROUTE-003), any replica reassigns and re-dispatches.

**Why B was rejected.** A single stream terminates at one Orchestration replica, which
then "owns" the only live channel to that Game Host. That ownership *is* session
affinity at the Orchestration layer — exactly what FR-ORCH-007 forbids. An action
landing on a different replica would require a second routing table (host → owning
replica) plus replica-to-replica forwarding, reintroducing the statefulness the
requirements prohibit. B's only real advantage — the Game Host never needs to be dialed
directly — is worth little when both services are in-cluster and freely addressable.

**Why C is a fallback.** C keeps A's correct topology but streams an effect list that
the handler has *already fully computed* — paying streaming's complexity (mid-stream
error ambiguity, partial-delivery questions) for no incremental-production benefit, and
weakening the all-or-nothing atomicity that the unary response gives for free. C is
retained only as a surgical escape hatch for oversized responses (see *Message size*).

---

## Services and RPCs

### `GameHostService` — dispatch path (served by Game Host)

| RPC | Purpose | Requirements |
|-----|---------|--------------|
| `CreateSession` | Bind the session to the `(game_id, game_version)` context, run `onInit` with the roster + parameters, return initial effects. | FR-SESS-004, FR-IN-002 |
| `ProcessInput` | Process an `action` / `player_joined` / `player_left` input; return the ordered effect list. | FR-IN-003/004/005, FR-ROUTE-002 |
| `Resync` | Compose one viewer's current view of the session by invoking the game's read-only `onResync`. Mutates nothing. | FR-IN-006, FR-RESP-005 |
| `TerminateSession` | Force teardown; free local + Redis state. **Idempotent** (see below). | FR-SESS-005, FR-FAIL-005, FR-XFER-002, FR-HDISC-003 |

`TerminateSession` has four callers: normal `game_over` (FR-SESS-005), retry-limit
permanent failure (FR-FAIL-005), room closure — including the grace-expiry closure of
FR-HDISC-003 — and the reconciliation sweep re-driving an owed teardown. All four go
through the durable-to-do mechanism in [ADR-0010](../../decisions/0010-session-teardown-ordering.md);
none of them may treat a teardown failure as a reason to abandon the room state change.

`CreateSession` is separate from `ProcessInput` because session creation is
structurally different: it carries the `ContextKey` for context binding and triggers
**host selection** (FR-ORCH-001/004). Subsequent inputs need only the `session_id` the
host already maps to a context (FR-SESS-002).

**Roster and team-name resolution.** The Orchestration Service builds
`CreateSessionRequest.teams` from the final lobby state. Each `Team.name` is the
team's resolved lobby display name — `"{template.name} {index}"` (e.g.
`"Attacker 1"`, `"Team 2"`), where `template.name` comes from the manifest
`teamTemplates` entry and defaults to `"Team"` for a single unnamed template
(game-rooms.md FR-TEAM, FR-MANIFEST-002). Using the instance display name (with
index) rather than the bare template name keeps team names unique when a template
has `count.max > 1`. The Game Host passes this value through unchanged; the GDK
surfaces it as `Team.name()` (game-development-experience.md FR-GDK-011).

**Entry-point resolution (IMP-GATE-79).** `CreateSessionRequest.entry_point_fqcn` is the
manifest's `backend.entryPoint` FQCN (game-development-experience.md FR-MANIFEST-008), resolved by the
Orchestration Service from the same manifest read that materializes `parameters` above. The
Game Host passes it through unchanged to the guest bridge, which classloads and instantiates it
(`../game-host/game-host-internals.md` §3.3/§7.2) — nothing on the Game Host side otherwise
knows which class a given `(game_id, game_version)` context should run.

### `GameHostRegistryService` — control path (served by Orchestration)

| RPC | Purpose | Requirements |
|-----|---------|--------------|
| `Register` | Advertise dialable address + supported runtimes on startup. | FR-REG-001 |
| `Heartbeat` (bidi stream) | Refresh the Redis liveness lease; receive `drain` instructions. | FR-REG-003, FR-ORCH-005, FR-SCALE-006 |
| `ReportContexts` | Snapshot of loaded context keys for warm-host selection. | FR-REG-002, FR-ORCH-004 |
| `Deregister` | Stop routing new sessions here on graceful shutdown. | FR-REG-004 |

Every registry RPC mutates only Redis-backed state, so any replica behind the LB can
service any call — which is what lets the Game Host dial a single stable Orchestration
ClusterIP while the dispatch path addresses individual pods.

---

## Addressing the Game Host pods

The dispatch path must reach a **specific** Game Host pod (the one holding the session
in local memory, `platform-architecture.md` FR-SESS-003), not a round-robin VIP. The
document qualifier matters: `user-accounts.md` independently defines an unrelated
FR-SESS-003 (login displaces the previous session). Two complementary mechanisms:

- A **headless Kubernetes Service** (`clusterIP: None`) gives each Game Host pod stable
  DNS, and/or the pod advertises its **pod IP + port** in `RegisterRequest.address`.
- The advertised address is stored in the Redis registry and used by every replica.

The Orchestration Service **pools one gRPC channel per Game Host instance** (not
dial-per-call) to meet the <50ms routing overhead budget (NFR-PERF-003), and treats a
channel as disposable on `UNAVAILABLE`.

---

## Processing semantics

- **Sequential per session, concurrent across sessions.** Ordering is enforced by the
  Orchestration Service's Redis-backed per-session queue (FR-ROUTE-002, FR-PROC-001),
  not by the transport. The next input is dispatched only after the prior
  `ProcessResult` is received.
- **State never crosses this wire.** The Game Host holds game state in local memory and
  persists it to Redis (CON-006, FR-STATE-003). Requests carry only inputs; responses
  carry only effects.
- **Opaque payloads are `bytes`.** Action payloads, effect payloads, and the
  `game_over` FE results are opaque to the platform (FR-STATE-001). **Lobby
  parameters are the exception:** `CreateSessionRequest.parameters` is a
  *platform-structured* UTF-8 JSON map of manifest parameter key → value, built and
  default-materialized by the Orchestration Service from the manifest declarations
  and host lobby configuration (values pass through to the game via the typed
  `GameParameters` accessors). See the `parameters` field comment in the proto and
  `../game-host/game-host-internals.md` §3.4 (review GAME-I5).
- **`game_over` is terminal.** After a `GameOverEffect` is processed, no further inputs
  are sent for the session (FR-EFF-006); only the first is honored (FR-EFF-007).

### Idempotency and exactly-once delivery

Each `ProcessInputRequest` carries a monotonic per-session `sequence`. Because a replica
can die *after* dialing but *before* dequeuing (FR-ROUTE-003), an input may be
re-dispatched. Rules:

- The Game Host applies each `sequence` **at most once**. It retains the last processed
  `(sequence → effects)` per session.
- A re-dispatched (duplicate) `sequence` returns the **originally produced effects** with
  `PROCESS_STATUS_OK` — an idempotent replay — so delivery can still complete if the
  first attempt's response was lost.
- The Orchestration Service keeps a per-session **"last delivered" watermark** in Redis
  and delivers effects for a given `sequence` to clients only once. Combined with the
  Game Host replay, this yields exactly-once *application* and at-least-once *delivery*
  with client-side dedup keyed by `sequence`.

**`TerminateSession` is idempotent — normative.** Terminating a session the host does not
hold, or has already terminated, is a **no-op success**, not an error. This is load-bearing
rather than a convenience: a lost response is indistinguishable from a real failure, so the
re-drive in [ADR-0010](../../decisions/0010-session-teardown-ordering.md) will retry
terminations that in fact succeeded. A host that answered anything but `OK` for an
already-gone session would turn a completed teardown into a permanently owed one.

**`TerminateSession` never waits on the per-session single-flight lock.** It marks the
session terminated, deletes the session record from Redis, and returns immediately; the
guest instance is disposed when the lock frees, and the in-flight invocation's result is
discarded. The Orchestration Service discards any `ProcessResult` arriving for a session it
has terminated. Termination must **not** be implemented with `Context.interrupt`, which is
context-scoped and would reach sibling sessions sharing that context
([`../game-host/game-host-internals.md`](../game-host/game-host-internals.md) §12).

**Deadline: 2 seconds**, distinct from the dispatch deadline (game timeout + overhead).
Teardown is a local dispose plus a Redis delete; it does not execute game code, which is
exactly what the no-waiting rule above guarantees.

**`player_left` may be re-delivered.** When a grace period expires, the notification is
dispatched from a durable outbox ([ADR-0009](../../decisions/0009-grace-deadline-durability.md))
rather than inline, so it is at-least-once.

The per-`sequence` replay rules above make a redelivery harmless **only if it carries the same
`sequence`** — which does not happen by default, because a sequence is normally allocated at
enqueue, so a re-drained outbox row would arrive under a fresh one and be applied a second time.
The outbox therefore allocates the sequence once, persists it on the row before the first dispatch,
and reuses it on every retry ([`../platform/data-model.md`](../platform/data-model.md) §4.2). The
exactly-once property above covers re-dispatch of an *already allocated* sequence, which is a
different event from re-drain of an outbox row; conflating the two is what makes this look safe when
it is not.

A `NOT_FOUND` on this path means the session record is gone. It is terminal **only while a room still
claims that session as active** (`room.active_session_id = :sessionId`); otherwise the session has
been retired from its room, the absent record is the expected result of a teardown that raced the
drain, and the outbox row is dropped. Treating it as unconditionally terminal would close a healthy
room that had already returned to Lobby after a normal game end. The test is attachment, **not**
teardown history — a completed teardown deletes its own record
([`../platform/data-model.md`](../platform/data-model.md) §4.1), so history is not a fact that
survives to be queried.

### Crash recovery

If the Game Host receives an input for a session it does not hold in local memory (e.g.
after re-dispatch to a fresh host), it loads state from Redis before invoking the handler
(`platform-architecture.md` FR-SESS-003b) — transparently, without a distinct error. A `NOT_FOUND` is returned only
when no state exists in Redis at all (a terminal condition).

### `Resync` — the read-only path

`Resync` sits outside every mechanism above, deliberately. It is the only RPC on the
dispatch path that does not advance the session:

| Property | `ProcessInput` | `Resync` |
|---|---|---|
| Allocates a `sequence` | Yes (Redis `INCR` at enqueue) | **No** |
| Enters the per-session queue | Yes | **No** |
| Writes the session record | Yes, atomically, on `OK` | **No** |
| Advances `lastAppliedSequence` | Yes | **No** |
| Advances the delivery watermark | Yes | **No** |
| Result audience | The effect's recipient set | **The requesting client only** |
| Counts toward the retry limit on failure | Yes (FR-FAIL-003) | **No** |

What it *does* share with `ProcessInput` is the **per-session single-flight lock**: the
Game Host serves a `Resync` while no handler is running for that session, so the view is
composed against a consistent, fully-applied state and can be truthfully stamped with the
`as_of_sequence` it reflects. That stamp is what makes client catch-up race-free — see
[`../api-design/websocket.md`](../api-design/websocket.md#game-session-protocol),
"Catch-up: the sync flow".

Because a resync mutates nothing, it needs no idempotency machinery: a duplicate or
re-dispatched `Resync` is simply re-executed. A failed `Resync` (`PROCESS_STATUS_FAILED`)
fails only the attaching client, which is surfaced to that client as a `RESYNC_FAILED`
error; the session continues unaffected (FR-RESP-005).

---

## Error model

Two tiers, kept strictly separate:

**Transport / infrastructure failures → native gRPC status codes.**

| Code | Meaning | Orchestration action |
|------|---------|----------------------|
| `UNAVAILABLE` | Host unreachable / crashed | Reassign session to another host, re-dispatch from queue (FR-ORCH-005, FR-FAIL-002) |
| `DEADLINE_EXCEEDED` | Call exceeded the deadline (set to the game timeout + overhead) | Treat as a processing failure; apply retry-limit semantics |
| `RESOURCE_EXHAUSTED` | Message exceeded the configured size ceiling | Fail the session (oversized effect/state) |
| `NOT_FOUND` | Session unknown and no Redis state. **Scoped to `ProcessInput` and `Resync` only** — `TerminateSession` returns `OK` for an unknown session (idempotency, above), so a retried teardown is never read as a hard failure | Permanently fail the session |
| `FAILED_PRECONDITION` | Context could not be loaded for the session | Fail the session |

**Game-level failures → in-band `ProcessResult`.** When the game *code* fails (threw,
timed out within the context, produced malformed output, exceeded the state size limit,
crashed the context, or failed to load), the host returns `PROCESS_STATUS_FAILED` with a
typed `GameFailure`. The Orchestration Service counts failures per session and, after the
retry limit (FR-FAIL-003), calls `TerminateSession` with `TERMINATION_REASON_RETRY_LIMIT`
and notifies participants (FR-FAIL-001/005).

This separation matters: transport codes are *retryable/reroutable infrastructure*
signals, while `GameFailure` is a *deterministic game-code* signal that re-dispatching
will not fix.

### What happens to the input that failed (GAME-I3)

"Counts failures and terminates after the limit" leaves the more common case — a failure *below* the
limit — unspecified, and there are four separate questions in it. All four are answered here because
getting any of them wrong produces a game that looks frozen.

| Question | Answer |
|---|---|
| Is the input re-dispatched? | **No.** A `GameFailure` is deterministic; replaying it reproduces it, and three retries of one bad action would exhaust the limit from a single click |
| Is the `sequence` consumed? | **Yes.** It is burned. The game stream is deliberately sparse (`../api-design/websocket.md`) and a hole carries no information, so no client notices. The proto's `ProcessInputRequest.sequence` comment states all three cases, because a codegen reader never sees this table |
| Does `lastAppliedSequence` advance? | **Yes**, to the failed input's sequence. A redelivery of the same sequence must be a replay returning the same failure, not a second invocation of a handler that has already run and thrown. The Game Host records the outcome alongside the sequence (`../game-host/game-host-internals.md` §8.1 `lastOutcome`/`lastFailure`) so the replay returns the same failure rather than the previous input's effects |
| Is anybody told? | **Yes** — and this is the part that was missing. The acting player receives a unicast `ACTION_REJECTED` on `/user/queue/errors`, carrying the `GameFailure` kind but **not** its message |

**The failure detail is not forwarded to the client.** A `GameFailure` message is a stack trace or an
exception string from game code, and game code is untrusted (ADR-0006 makes the MVP's Java
first-party, but the contract is written for the general case). Forwarding it leaks internals and
hands an attacker a channel to place arbitrary text in another user's client. The player is told their
action was rejected; the detail goes to the log, correlated by `session_id`.

Without the notification, the failure is invisible: the player clicks, no effect is fanned out
because the handler threw, and the game appears to hang. They retry — which is a *fresh* input with a
*fresh* sequence, so it fails again and consumes a second of the three allowed. Three clicks and the
session is dead with no explanation to anyone.

**The counter is over *consecutive* failures and resets on any success** (`FR-FAIL-003`, which says
consecutive). One bad action in a two-hour game must not accumulate toward a limit alongside two
unrelated ones an hour later. It is held in `failcount:{sessionId}` in Redis, which is why that key
is deleted by `terminateAndCleanup`.

**Re-dispatch is the *other* path, and it also counts.** FR-FAIL-003's "across container restarts or
re-dispatches" refers to `UNAVAILABLE` and crash recovery (FR-FAIL-002/004), where the input *is*
re-dispatched from the Redis queue because the failure was infrastructural. Those attempts count
toward the same limit, so a session that cannot survive being resumed also terminates — but by a
different route, and one that a retry can legitimately fix.

### `GameOutcome` validation

A `GameOverEffect` carries the structured outcome the platform writes to history and statistics
(`game-contracts.md` FR-OUTCOME-001…004). It is game-supplied, and FR-OUTCOME-001 bounds nothing
beyond "a placement (integer, 1-based finishing position)".

**Orchestration validates it before it reaches Postgres**, and the reason is that the database cannot
be the thing that rejects it. `game_history_entry` has `CHECK (placement >= 1 AND placement <= team_count)`;
a violation aborts the whole recording transaction, and `game_over` is terminal (FR-EFF-006), so
there is no retry that can succeed. A single out-of-range integer would erase a completed session
from history *and* from per-game statistics.

| Check | Rule |
|---|---|
| `teamResults` non-empty | at least one team |
| `placement` | `1 ≤ placement ≤ len(teamResults)` for every entry |
| placement coverage | placements form a valid ranking; ties are permitted **only** when `draw` is true (FR-OUTCOME-003) |
| `playerResults` player ids | every id is a participant of this session |
| team ids | every `teamResults` team id is a team of this session |
| stat maps | present or absent; contents **not** inspected (FR-OUTCOME-004, `game-history.md` CON-003) |

On failure the platform records the session as **completed** — the engine reported completion, which
is all `per-game-statistics.md` FR-STATS-001 asks — increments the per-game counter, writes **no**
history entries, and logs ERROR with the session, game and version. Statistics stay correct; only the
malformed per-player history is lost. See
[`../platform/data-model-history.md`](../platform/data-model-history.md) §2.

This is deliberately *not* a `GameFailure`: the game completed successfully and its FE results
payload is still delivered. Only the platform-facing outcome was unusable.

---

## Message size

Individual effect and state payloads may reach 10 MB (`game-contracts.md` NFR-SIZE-001/002), and a response
carries an ordered *list* of effects — so the gRPC default ~4 MB inbound limit will be
exceeded. Mitigation:

1. **Default:** raise `maxInbound/OutboundMessageSize` on both peers to a deliberate
   ceiling (≈16–32 MB), sized for a realistic multi-effect response with headroom and
   bounded to protect per-call memory across the 500-session target (NFR-SCALE-001).
2. **Escape hatch:** if a response can legitimately exceed the ceiling, server-stream
   **only** the `ProcessInput`/`CreateSession` response leg (Option C, applied
   surgically) and have the Orchestration Service buffer the full stream before delivery
   to preserve all-or-nothing atomicity (FR-RESP-004). Do not adopt streaming wholesale.

---

## Security and observability

- **The registry's access control is unreachability from the public listener** (IMP-M10-06).
  `GameHostRegistryService` shares the monolith's HTTP listener (`local-environment.md` §7.8) and
  carries no credential of its own, so anything that can reach the path can `Register` a host. The
  boundary is enforced at the public edge: the Frontend's nginx answers `404` for
  `/turnbase.gamehost.v1.*` on both of its servers (platform host and the games-origin fall-through)
  and never proxies it. Game Hosts dial `orchestration-address` over the internal network instead.
  Any new public ingress must keep that prefix unrouted.
- **mTLS** on both directions. The Game Host exposes an inbound gRPC server port for the
  dispatch path; a Kubernetes NetworkPolicy restricts inbound to the Orchestration
  Service only, mirroring FR-SEC-002's egress scoping.
- **W3C trace context** propagates via gRPC metadata (OpenTelemetry interceptors), not in
  message bodies. Each unary dispatch is one span, aligning with FR-OBS-004/009 and the
  <50ms routing-overhead budget.
- The `session_id` is the correlation ID on all dispatch-path logs/metrics; `instance_id`
  and `ContextKey` correlate control-path and context-lifecycle events (FR-OBS-008).

---

## Open points (deferred, non-blocking)

- **Stat value typing.** `GameOutcome` stat maps use `map<string, string>`; the GDK
  stringifies arbitrary game-defined stat values. Revisit with `google.protobuf.Value`
  only if typed numeric aggregation in history/stats is later required (FR-OUTCOME-004
  currently treats stats as opaque).
- ~~**Proto home.** This contract currently lives in `docs/` during the
  requirements/spec phase. When the Game Host and Platform Monolith submodules are
  created, the canonical `gamehost.proto` should move to a shared, versioned location
  (its own proto module or a `buf` workspace) consumed by both build pipelines.~~
  **Resolved by [ADR-0012](../../decisions/0012-repo-strategy-polyrepo-submodules.md):** no shared
  workspace. `gamehost.proto` stays authoritative here and `turnbase-common` holds a **committed
  copy** at `src/main/proto/turnbase/gamehost/v1/`, kept in sync by `scripts/sync-proto.sh` (checked
  by `scripts/sync-proto.sh --check` in the parent's `pre-push` hook) rather than generated at build
  time — a build step reading `../docs/` cannot run in a standalone `turnbase-common` clone
  (ADR-0012's 2026-08-20 amendment, `IMP-GATE-02`). `turnbase-common` publishes the stubs as
  `io.turnbase:turnbase-grpc` from its own committed copy — which is what both pipelines consume, so
  neither needs the proto itself. Editing the copy is a defect; the change belongs here
  ([`conventions.md`](../../implementation/conventions.md) §5).
