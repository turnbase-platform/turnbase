## Last Session Summary

**Date:** 2026-11-04 (session 263) — **`IMP-M20-04` done: a checked `ARCHITECTURE.md` per service. 214 of 232 items done.**

- `ARCHITECTURE.md` in `turnbase-platform`, `turnbase-game-host`, `turnbase-frontend`, `turnbase-sdk`: packages/modules with one line each, and the five flows (sign-in, room create/join, a move, upload, Game Host failure) traced through classes. The umbrella `ARCHITECTURE.md` is the system overview linking them and `docs/specs/flows/`.
- New `code-maps` check in `scripts/check-corpus.py` (8th): every package, class, component, method and path named in a map must resolve; `scripts/test-code-maps.py` plants four renames and asserts each fails.
- Docs-only in the submodules; CI on each pushed `master` was watched green before the refs were bumped.

## Current State

- **Phase 1, M20 (refinement) open**: 18 of 22 items remain. M0–M19 are closed (archived under `docs/implementation/archive/`).
- **Red / not run:** CI is refused for billing, so every item is judged locally (`spotless:apply`, `verify`, `verify -Pintegration`). Nothing else is known red.
- **Owner-held:** CI billing (or the public flip); the 7WD bootstrap secret (re-check live before reporting it); the Repos Production reply, which decides whether 7WD ships under its name.

## Next Priorities

- `05`, `07`, `08`, `13`, `15`, `17`, `18`, `19`, `20`, `21` have no open dependency; `06` is unblocked. Keep the maps current: `check-corpus.py code-maps` fails on a renamed class they name.
- After M20: M21 public release (licence, README, gitleaks, published artifacts), M22 cloud deployment (ADR-0021 from `IMP-M20-15` first), then Phase C.

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
