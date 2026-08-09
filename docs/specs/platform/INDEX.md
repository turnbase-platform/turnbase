# Platform Monolith Internals

Design specifications for the internals of the Platform Monolith — the parts that are neither a wire
protocol (see [api-design/](../api-design/INDEX.md)) nor game execution (see
[game-host/](../game-host/INDEX.md)), but the durable state and lifecycle machinery underneath both.

## Scope

What the monolith must get right to survive process death: which instance owns a room, how time-based
transitions are enforced when the process holding a timer can vanish, how a game session is torn down
when a room stops needing it, and the relational schema all of that is written to.

## Files

| File | Topic |
|------|-------|
| [room-lifecycle.md](room-lifecycle.md) | Room ownership claim/adoption/drain, the owner-epoch fence and event versioning, grace-deadline enforcement, session detach, the three reconciliation sweeps, observability |
| [data-model.md](data-model.md) | Relational schema for rooms, participants, teams, room ownership, and the two durable-work tables (session teardown, game-input outbox) |

## Key Decisions

- **Room ownership is a lease-gated claim, not a lifetime assignment** ([ADR-0008](../../decisions/0008-room-ownership-lifecycle.md)). The claim script is itself the failure detector — there is no dead-instance watcher. A room may sit unowned; the first client back, or reconciliation, claims it.
- **Divergence cannot become durable in the room table.** An **owner epoch**, burned by the claim script at each change of tenure, is the fence token: a stale owner's mutation matches zero rows, publishes nothing, and self-evicts. The room *version* cannot do this job — it is room-scoped, and the legitimate owner advances through the very value a stale owner is holding, at which point the stale write would match. Reads are not fenced, so a transient wrongful takeover is bounded rather than free: it is resolved by the stale owner's next write or its next ownership re-check.
- **The room version is committed before the delta is published.** Otherwise an adopting instance re-issues versions clients have already applied, and clients discard them *silently* — worse than a gap, which is at least detected.
- **Grace deadlines are absolute timestamps in PostgreSQL, enforced by a sweep, with no in-process timer** ([ADR-0009](../../decisions/0009-grace-deadline-durability.md)). The database clock is the single time authority, which removes clock skew by construction rather than by tolerance.
- **A conditional UPDATE's rowcount is the entire idempotency story.** Expiry, reconnect, kick and early release are one statement with different guards; exactly one actor wins and owns all side effects. No deduplication table exists anywhere in the design.
- **Session teardown is a durable to-do, not an ordering** ([ADR-0010](../../decisions/0010-session-teardown-ordering.md)). The state change and the owed teardown commit together; the gRPC call happens outside the transaction and may fail freely. The prototype's leak came from destroying the reference, not from the ordering.
- **Reconciliation repairs, but only on evidence.** A datastore error is never read as an absence, divergence must persist across two runs, and no repair happens in the first two minutes after startup — a recovering system is indistinguishable from a broken one until registration completes.
