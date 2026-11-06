# ADR-0021: Two deployment profiles — scaled Kubernetes and single instance

- **Status:** Accepted
- **Date:** 2026-11-06
- **Deciders:** Project owner
- **Amends:** [ADR-0020](0020-platform-horizontal-scaling.md) §2 (the two-replica minimum binds one profile, not every deployment)
- **Relates to:** [ADR-0001](0001-local-first-mvp-platform.md), [ADR-0002](0002-websocket-room-affinity.md),
  [ADR-0008](0008-room-ownership-lifecycle.md)
- **Executed by:** `IMP-M20-15` (this record); `IMP-M20-16` (recovery from a full stop) builds on it

## Context

ADR-0020 states "at least two replicas of each stateless tier, at all times". That is the right rule for what
M18 measured, and the wrong one for a small deployment: a hobbyist or a demo wants one Platform, one Game
Host, and the freedom to let them sleep. The local compose stack is already that shape. Without a name for it,
every `FR-ASC-*` / `NFR-ASC-*` row reads as binding the compose stack too, and the requirement set contradicts
the thing the quick start runs.

## Decision

1. **Two profiles.**
   - **Scaled Kubernetes** — what M18 measured: a two-replica minimum of Platform and Game Host, the
     HorizontalPodAutoscaler on the Platform, KEDA on the Game Host, the headless Service for instance
     addressing. ADR-0020 §1–6 describe it and stand unchanged for it.
   - **Single instance** — one Platform and one Game Host. Either may scale to zero when idle, and may be
     restarted without a second replica to cover; the cost is that a restart interrupts games, which room
     recovery (ADR-0008) and `IMP-M20-16` bound. The docker compose stack is its local form.
2. **The instance-addressing contract is stated as a contract**, not as a Kubernetes mechanism:
   - *Browser to Platform.* A WebSocket upgrade carrying `?instance={podId}` reaches the Platform instance
     that `podId` names when that instance is ready, otherwise any ready instance (FR-DEPLOY-002). The hint is
     advisory and names only an instance of this deployment.
   - *Platform to Game Host.* The Platform reaches the specific Game Host that holds a session, by the
     address that host advertised at registration (`orchestration-gamehost-protocol.md`).
   - The **headless Service** (nginx resolving `a-b-c-d.{headless}`; pod IPs advertised) is *one
     implementation*, used by the scaled profile. In the single-instance profile there is one instance and the
     contract holds trivially.
3. **One provider per deployment**, not one per component (owner). A deployment is entirely on one
   orchestration provider; mixing (for example a Kubernetes Platform and a compose Game Host) is out of scope.
4. **Requirements bind a profile.** Each `FR-ASC-*` and `NFR-ASC-*` row in `platform-operations.md` names the
   profile it binds. Behaviour that is correctness (release on removal, correctness through scaling, the
   addressing contract) binds both; replica counts, autoscaling, scale-out/in timings, ceilings and failover
   bind the scaled profile only.

## Consequences

- `platform-operations.md` rows `FR-ASC-001…005` and `NFR-ASC-001…007` each carry a **Profile** statement.
- Scale-to-zero (`FR-SCALE-002`, cold-start budget `FR-SCALE-007`) is available in the single-instance profile
  only and stays deferred as a *requirement* (ADR-0001); this ADR defines where it would apply.
- Nothing in the scaled profile changes, and no code changes with this record.
