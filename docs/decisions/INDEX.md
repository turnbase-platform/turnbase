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

## Provenance

ADRs 0001–0005 ratify the six "Strategic decisions needing the project owner" from the
[MVP Readiness Review 2026-07-02](../reviews/2026-07-02-mvp-readiness/INDEX.md), taken in an
owner decision session on 2026-07-10.
