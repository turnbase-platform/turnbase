## Last Session Summary

**Date:** 2026-11-06 (session 281) — **`IMP-M20-20` DONE. 230 of 232 items done.**

- All 33 `OQ-*` in `docs/specs` now have a disposition in the new [`docs/specs/backlog.md`](docs/specs/backlog.md) (registered in `docs/specs/INDEX.md`): 4 closed (frontend-gdk OQ-001, game-host OQ-5 and OQ-6, local-environment OQ-001 measured by `IMP-M20-17`), 4 owner decisions with options and a recommendation (catalog OQ-001 and OQ-003, fullscreen, local Postgres backup), 25 backlog with a trigger each.
- The owner decisions are not taken: they wait for the owner. Umbrella-only; no ref bump; corpus check clean.
- Next: `IMP-M20-21`, then `22` (its dependency `20` is done).

## Current State

- **Phase 1, M20 (refinement) open**: 2 of 22 items remain. M0–M19 are closed (archived under `docs/implementation/archive/`).
- **Red / not run:** CI is refused for billing, so every item is judged locally (`spotless:apply`, `verify`, `verify -Pintegration`). Nothing else is known red.
- **Owner-held:** CI billing (or the public flip); the 7WD bootstrap secret (re-check live before reporting it); the Repos Production reply, which decides whether 7WD ships under its name.

## Next Priorities

- `21` and `22` have no open dependency. Keep the maps current: `check-corpus.py code-maps` fails on a renamed class they name.
- After M20: M21 public release (licence, README, gitleaks, published artifacts), M22 cloud deployment (ADR-0021 from `IMP-M20-15` first), then Phase C.

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
