# ADR-0003: MVP availability target of 99%

- **Status:** Accepted
- **Date:** 2026-07-10
- **Deciders:** Project owner
- **Source:** MVP Readiness Review 2026-07-02 — strategic decision #4

## Context

`platform-operations.md` sets a 99.9% availability *Must*. Achieving 99.9% (~43 min downtime/mo)
requires redundancy, a staging environment, and on-call — none of which are realistic for a
solo-run, local-first MVP (ADR-0001), which has no HA at all.

## Decision

- The **MVP enforceable SLO is 99%** (~7.2 h/mo of allowed downtime).
- **99.9% is documented as an aspiration** for a future cloud/HA deployment, not an MVP *Must*.

## Consequences

- **Positive:** an honest, achievable target for a single-node local deployment; relaxes the
  implied redundancy/staging/on-call demands to post-MVP.
- **Negative:** the platform is explicitly not making strong uptime guarantees during the MVP;
  the 99.9% target is revisited when cloud deployment and HA land.

## Affected documents

- `docs/requirements/platform-operations.md` — availability FR: 99% MVP *Must*, 99.9% aspiration.
- Review INDEX — resolves strategic #4.
