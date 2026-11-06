## Last Session Summary

**Date:** 2026-11-06 (session 276) — **`IMP-M20-15` DONE. 225 of 232 items done.**

- ADR-0021 (`docs/decisions/0021-deployment-profiles.md`): two profiles, scaled Kubernetes (what M18 measured) and single instance (one Platform, one Game Host, may scale to zero; compose is its local form). Instance addressing (`?instance=` to the Platform; the advertised address to a Game Host) is a contract, the headless Service one implementation. One provider per deployment. Amends ADR-0020 §2.
- `platform-operations.md`: every `FR-ASC-001…005` and `NFR-ASC-001…007` row states its profile (both: FR-ASC-002, -004, NFR-ASC-002; the rest scaled). Registered in `decisions/INDEX.md`. Docs only; no code, no CI, no ref bump.
- Corpus check clean.
- Next: `IMP-M20-16` (now unblocked), or `10` (PARTIAL), `11`, `13`, `17`–`21`.

## Current State

- **Phase 1, M20 (refinement) open**: 12 of 22 items remain (`10` partly done). M0–M19 are closed (archived under `docs/implementation/archive/`).
- **Red / not run:** CI is refused for billing, so every item is judged locally (`spotless:apply`, `verify`, `verify -Pintegration`). Nothing else is known red.
- **Owner-held:** CI billing (or the public flip); the 7WD bootstrap secret (re-check live before reporting it); the Repos Production reply, which decides whether 7WD ships under its name.

## Next Priorities

- `10` (PARTIAL, continue from its Remaining line), `11`, `13`, `15`, `17`, `18`, `19`, `20`, `21` have no open dependency. Keep the maps current: `check-corpus.py code-maps` fails on a renamed class they name.
- After M20: M21 public release (licence, README, gitleaks, published artifacts), M22 cloud deployment (ADR-0021 from `IMP-M20-15` first), then Phase C.

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
