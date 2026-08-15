# Platform Monolith Internals

Design specifications for the internals of the Platform Monolith — the parts that are neither a wire
protocol (see [api-design/](../api-design/INDEX.md)) nor game execution (see
[game-host/](../game-host/INDEX.md)), but the durable state and lifecycle machinery underneath both.

## Scope

Two things. First, what the monolith must get right to survive process death: which instance owns a
room, how time-based transitions are enforced when the process holding a timer can vanish, and how a
game session is torn down when a room stops needing it. Second, **the whole relational schema** —
every table the Platform Monolith owns, across all domains.

## Files

| File | Topic |
|------|-------|
| [room-lifecycle.md](room-lifecycle.md) | Room ownership claim/adoption/drain, the owner-epoch fence and event versioning, grace-deadline enforcement, session detach, the three reconciliation sweeps, observability |
| [data-model.md](data-model.md) | **Schema conventions** (types, naming, the database clock), and the schema for rooms, participants, teams, room ownership, and the two durable-work tables (session teardown, game-input outbox) |
| [data-model-accounts.md](data-model-accounts.md) | Users (registered and guest), authentication methods, sessions, profile privacy settings, and what account deletion actually writes |
| [data-model-social.md](data-model-social.md) | Friendships and pending friend requests, the guest-exclusion foreign key, and the friend-request/notification lifecycle coupling |
| [data-model-catalog.md](data-model-catalog.md) | Games, versions and bundles, the searchable tag projection, badges and the admin review queue |
| [data-model-history.md](data-model-history.md) | Session-completion records, per-player history entries, the per-game session counter, and erasure by random-token pseudonymization |
| [data-model-notifications.md](data-model-notifications.md) | Persisted notifications with delivery and read state, room invitations, and why alerts have no table |

**Reading order for the schema:** start at [data-model.md](data-model.md) — it carries the
conventions the other five inherit and defines the room tables the rest reference.

## Key Decisions

- **Room ownership is a lease-gated claim, not a lifetime assignment** ([ADR-0008](../../decisions/0008-room-ownership-lifecycle.md)). The claim script is itself the failure detector — there is no dead-instance watcher. A room may sit unowned; the first client back, or reconciliation, claims it.
- **Divergence cannot become durable in the room table.** An **owner epoch**, burned by the claim script at each change of tenure, is the fence token: a stale owner's mutation matches zero rows, publishes nothing, and self-evicts. The room *version* cannot do this job — it is room-scoped, and the legitimate owner advances through the very value a stale owner is holding, at which point the stale write would match. Reads are not fenced, so a transient wrongful takeover is bounded rather than free: it is resolved by the stale owner's next write or its next ownership re-check.
- **The room version is committed before the delta is published.** Otherwise an adopting instance re-issues versions clients have already applied, and clients discard them *silently* — worse than a gap, which is at least detected.
- **Grace deadlines are absolute timestamps in PostgreSQL, enforced by a sweep, with no in-process timer** ([ADR-0009](../../decisions/0009-grace-deadline-durability.md)). The database clock is the single time authority, which removes clock skew by construction rather than by tolerance.
- **A conditional UPDATE's rowcount is the entire idempotency story.** Expiry, reconnect, kick and early release are one statement with different guards; exactly one actor wins and owns all side effects. No deduplication table exists anywhere in the design.
- **Session teardown is a durable to-do, not an ordering** ([ADR-0010](../../decisions/0010-session-teardown-ordering.md)). The state change and the owed teardown commit together; the gRPC call happens outside the transaction and may fail freely. The prototype's leak came from destroying the reference, not from the ordering.
- **The manifest is the source of truth for what a game declares; the catalog stores projections of it, never copies.** A column is projected only when it needs an index shape the stored `jsonb` cannot provide — which is why tags get their own table and the capability columns do not.
- **Deletion is not one operation.** A registered account becomes a namespace tombstone, a guest is hard-deleted in two phases, a game is soft-deleted, and history is pseudonymized with a **random** token rather than a keyed hash — an HMAC over the user-id space is reversible by enumeration, which is the property ADR-0004 rules out.
- **Coupled objects are coupled by foreign key.** A notification pointing at a friend request or a room invitation cascades with it, and the generic retention purge is indexed *partially on having no subject* so it can never remove an actionable message out from under a live object.
- **Reconciliation repairs, but only on evidence.** A datastore error is never read as an absence, divergence must persist across two runs, and no repair happens in the first two minutes after startup — a recovering system is indistinguishable from a broken one until registration completes.
