# ADR-0001: Local-first MVP platform (Docker Desktop Kubernetes)

- **Status:** Accepted
- **Date:** 2026-07-10
- **Deciders:** Project owner
- **Source:** MVP Readiness Review 2026-07-02 — blockers OPS-1/2/6, strategic decisions #1 and #2, and #6 (partial)

## Context

The review flagged that the cloud provider and Kubernetes flavor were "TBD" (OPS-1), that
there was no infrastructure-as-code (OPS-2), and that ingress/TLS/DNS were undefined for a
WebSocket-centric product (OPS-6). It also surfaced a hard conflict: gVisor is a stated *Must*,
but gVisor collides with EKS (requires custom node AMIs) and is unavailable for local WSL2
development (`runsc` is not supported there — a GRMP lesson). Separately, the GRMP prototype
never escaped docker-compose in 15 months.

The owner's direction is to focus the MVP on **local development, testing, and demo** using the
tooling already on hand: **WSL2 + Docker Desktop with its bundled single-node Kubernetes engine**.

## Decision

1. **The MVP runs locally only.** No cloud provider is provisioned for the MVP. The execution
   target is Docker Desktop's bundled Kubernetes on WSL2.
2. **Canonical deploy path = Kubernetes.** Kubernetes manifests / Helm charts targeting the
   local single-node cluster are the supported, CI-exercised deployment path — Kubernetes is a
   stated project goal and stays exercised. **docker-compose** is maintained as a lighter
   quick-start profile for fast inner-loop work.
3. **gVisor is out of scope for the MVP.** `runsc` is unavailable on Docker Desktop/WSL2, so the
   gVisor *Must* is re-scoped to **production-only, post-cloud hardening**. MVP sandbox isolation
   relies on Truffle/guest-context isolation (or process isolation — see ADR-0005) plus pod
   isolation.
4. **Cloud deployment is deferred to post-MVP.** AWS/EKS + Terraform + ECR + ALB/ACM/Route53
   remain the documented aspiration but are not built for the MVP. The planned
   "Deployment & infrastructure spec" is rescoped to the local profile now; the cloud target is
   captured as a forward-looking appendix, not an MVP deliverable.
5. **Cloud-scaling requirements deferred (strategic #6).** `FR-SCALE-*` (HPA, connection
   draining, cold-start budgets) move to post-MVP. The MVP bar is **single-node local
   correctness**, not elastic scale.

## Consequences

- **Positive:** zero cloud cost, fast iteration, no custom-AMI/gVisor yak-shaving, and a
  realistic scope for a solo build. Kubernetes remains part of the everyday workflow.
- **Negative / deferred:** no real horizontal-scaling or HA validation until a post-MVP cloud
  phase; the availability target is set accordingly (ADR-0003).
- **Redis (OPS-4):** for the MVP, Redis is a single local instance with no HA. Because Redis is
  the crash-recovery layer for live game state, the accepted game-state loss window must be
  documented in the data-operations spec; this is acceptable for a local MVP.
- The gVisor *Must* in the requirements must be annotated as production-only.

## Affected documents

- `docs/requirements/platform-operations.md` — deployment model → local Docker Desktop K8s +
  compose; `FR-SCALE-*` → post-MVP; `FR-CICD-007`/`FR-CICD-008` (tag-triggered production deployment
  and rollback) → post-MVP, closing `IMP-GATE-24` — no production target exists for the MVP for
  either to act on; availability (see ADR-0003).
- `docs/requirements/platform-architecture.md` — gVisor Must → production-only; sandbox story
  (see ADR-0005).
- Future **deployment & infrastructure spec** — rescoped to the local profile; cloud as appendix.
- Future **data-operations spec** — single-node Redis + accepted loss window (OPS-4).
- Review INDEX — resolves OPS-1/2/6 for MVP scope, strategic #1/#2, partial #6.
