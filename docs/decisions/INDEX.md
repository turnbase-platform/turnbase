# Architecture Decision Records

Durable record of significant, cross-cutting decisions for the TurnBase platform. Each ADR captures the context, the decision taken, its consequences, and the documents it affects. ADRs are the authoritative source once accepted; requirements and specs should link back to the relevant ADR rather than restating the rationale.

Format: one file per decision, numbered sequentially (`NNNN-slug.md`). Status is one of `Proposed`, `Accepted`, `Superseded`, `Deprecated`.

## Records

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-local-first-mvp-platform.md) | Local-first MVP platform (Docker Desktop Kubernetes) | Accepted |
| [0002](0002-websocket-room-affinity.md) | WebSocket scaling via room affinity | Accepted |
| [0003](0003-mvp-availability-target.md) | MVP availability target of 99% | Accepted |
| [0004](0004-account-erasure-pseudonymization.md) | Account erasure via history pseudonymization | Accepted |
| [0005](0005-game-sandbox-espresso-spike.md) | Game sandbox — Espresso spike gates the Game Host spec | Accepted |
| [0006](0006-game-trust-model-java-official-only.md) | Game trust model — Java backends are official-only for the MVP | Accepted |
| [0007](0007-game-frontend-separate-domain.md) | Game frontends are served from a separate registrable domain | Accepted |
| [0008](0008-room-ownership-lifecycle.md) | Room ownership is a lease-gated claim, not a lifetime assignment | Accepted |
| [0009](0009-grace-deadline-durability.md) | Grace deadlines are persisted absolute timestamps, fired by a sweep | Accepted |
| [0010](0010-session-teardown-ordering.md) | Session teardown is a durable to-do, not an ordering | Accepted |

## Provenance

ADRs 0001–0005 ratify the six "Strategic decisions needing the project owner" from the
[MVP Readiness Review 2026-07-02](../reviews/2026-07-02-mvp-readiness/INDEX.md), taken in an
owner decision session on 2026-07-10.

ADR-0006 follows from the Espresso feasibility spike run on 2026-07-10/11 (ADR-0005), which showed
in-JVM Espresso on GraalVM CE cannot isolate untrusted Java; the owner chose to scope the MVP to
official-only Java backends and defer untrusted backends (hardened-container Java, plus JS/Python
runtimes) to post-MVP.

ADR-0007 resolves review blocker GAME-B3 (2026-07-12). It is recorded as an ADR rather than left in
the spec because it **overturns the review's own suggested resolution** on a security argument, and
because it carries a real-world cost (a second registered domain in production).

ADR-0008–0010 close the room-lifecycle durability cluster (GRMP lessons F1, F2 and F3) on 2026-08-09.
They are three ADRs rather than one because they are independently revisitable — a future live
migration would replace 0008 without touching 0009 or 0010 — but they were taken together, and each
depends on the other two: the sweep of 0009 needs 0008's claim before it may broadcast, and 0010's
re-drive is a duty of the same sweep. Two of the three also fix defects that were already latent in
the specs: a rolling deploy would have deleted every Lobby room, and an adopting instance would have
re-issued event versions that clients discard silently.
