# ADR-0020: The Platform Monolith scales horizontally, with a minimum of two replicas of each stateless tier

- **Status:** Accepted
- **Date:** 2026-10-24
- **Deciders:** Project owner
- **Amends:** [ADR-0002](0002-websocket-room-affinity.md) and [ADR-0008](0008-room-ownership-lifecycle.md) by
  reference only; neither is reversed
- **Relates to:** [ADR-0001](0001-local-first-mvp-platform.md), [ADR-0003](0003-mvp-availability-target.md),
  [ADR-0018](0018-game-start-resilience.md)
- **Executed by:** milestone **M18** in [`registry.md`](../implementation/registry.md) (`IMP-M18-01…17`);
  design in [`load-testing-phase-b.md`](../specs/deployment/load-testing-phase-b.md)

## Context

`platform-operations.md` NFR-SCALE-001 and CON-013 deferred multi-instance Platform operation to post-MVP
(ADR-0001), and the platform has run as one instance. Phase A and M16/M17 load testing measured that one
instance. On 2026-10-24 the owner set the Phase B goal: autoscaling that adapts to rising and falling load,
handled correctly and efficiently, with **redundancy and correctness ahead of a higher ceiling**. ADR-0002 and
ADR-0008 already specify the multi-instance model (room affinity, lease-gated ownership, release on shutdown);
what was deferred is running more than one replica, and the pieces around it.

## Decision

1. **The deferral is lifted for the reference node.** The Platform Monolith runs as several replicas under a
   HorizontalPodAutoscaler on CPU utilisation. PostgreSQL and Redis stay single, non-HA instances (ADR-0001,
   ADR-0003).
2. **At least two replicas of each stateless tier**, Platform and Game Host, at all times in the scaled
   deployment, so that the loss of any one costs no game. Maximum three of each on the reference node.
3. **Affinity by instance hint at the frontend proxy.** The `/ws?instance={podId}` hint the browser already
   sends is the routing key: the proxy forwards to the named pod through a headless Service and falls back to
   the regular Service when that pod is not ready (FR-DEPLOY-002). The pod named is the target, not a hash of
   the room, so ADR-0008's rejection of consistent hashing at the ingress stands.
4. **Redis pub/sub for user-scoped pushes only** (SSE alerts, session revocation). ADR-0002 rejected pub/sub
   for *room* fan-out and that stays true: room traffic is produced and served by the room's owner. User-scoped
   pushes have no owner and are low-volume; delivery stays best-effort as it is today. The per-user WebSocket
   connection cap becomes cluster-wide.
5. **Release on scale-in.** On `SIGTERM` an instance stops claiming, releases its rooms, and closes its
   sockets (FR-DEPLOY-001); the rolling-deploy path is the scale-in path.
6. **The Game Host autoscales with KEDA** on active sessions against the per-host cap and on memory, with
   `minReplicaCount` 2. Scale-in is *drain, then migrate*: no new sessions to a draining host, a bounded drain
   period, remaining sessions reassigned by the mode `game-host-internals.md` `OQ-5` selects by measurement.

## Consequences

- NFR-SCALE-001 and CON-013 are amended; `FR-ASC-*` and `NFR-ASC-*` are added to `platform-operations.md`.
- `platform-architecture.md` FR-SCALE-006 is amended and `OQ-003` is resolved.
- In-memory state in the Platform (SSE registry, connection counts, revocation) must be correct across
  instances: audited and fixed by `IMP-M18-08`.
- KEDA becomes a pinned dependency of the load-test environment.
