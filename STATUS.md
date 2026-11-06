## Last Session Summary

**Date:** 2026-11-06 (session 282) — **`IMP-M20-21` DONE. 231 of 232 items done.**

- Optional manifest `credits` (`designers` required; `artists`, `publisher`, `year`): spec, `manifest.schema.json` and the SDK copy/validator agree and reject a malformed one; `GET /api/games/{id}` returns it (read from the active version's manifest, no migration); Game Detail shows a Credits card (VW-GDET-004, not on the Catalog card).
- 7WD's manifest, README and INFO carry the credits; INFO no longer says "skeleton". Verified in the rebuilt compose stack: 7WD returns its credits, Tic-Tac-Toe `null`.
- Local `verify -Pintegration` in the platform: `GameAssetControllerIT` and `SeedDataIT` fail on `*.localhost` subdomain resolution in this WSL, identically on unchanged `master`; `ReconciliationJobIT` is timing-flaky (failed once under load, passed twice alone).
- Next: `IMP-M20-22`.

## Current State

- **Phase 1, M20 (refinement) open**: 1 of 22 items remains. M0–M19 are closed (archived under `docs/implementation/archive/`).
- **Red / not run:** CI is refused for billing, so every item is judged locally (`spotless:apply`, `verify`, `verify -Pintegration`). Nothing else is known red.
- **Owner-held:** CI billing (or the public flip); the 7WD bootstrap secret (re-check live before reporting it); the Repos Production reply, which decides whether 7WD ships under its name.

## Next Priorities

- `22` has no open dependency. Keep the maps current: `check-corpus.py code-maps` fails on a renamed class they name.
- After M20: M21 public release (licence, README, gitleaks, published artifacts), M22 cloud deployment (ADR-0021 from `IMP-M20-15` first), then Phase C.

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
