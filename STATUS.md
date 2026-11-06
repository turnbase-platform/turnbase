## Last Session Summary

**Date:** 2026-11-06 (session 280) — **`IMP-M20-19` DONE. 229 of 232 items done.**

- The 129 to 172 platform-thread jump of `sustained-high` is a pool growing to its bound, not a leak: from the run's Prometheus history, 45 threads started in the one 20 s sample where live threads rose 43, only `timed-waiting` threads grew, every named executor stayed at its bound, so it is Tomcat's worker pool (max 200). The same sample has a 2.43 s maximum request time (0.27 s around it); the extras left within 60 s of the load going (172 to 64). The stall itself was not found.
- A 23-minute rerun (119 pairs, 3 pods, per-pod `/proc` census) did not reproduce it: Tomcat workers 62 to 70 per pod, no step. Recorded as the `**M20:**` line on `load-testing.md` §13 finding 17. No code change, no ref bump; corpus check clean.
- Next: `IMP-M20-20`, `21`; `22` waits on `20`.

## Current State

- **Phase 1, M20 (refinement) open**: 3 of 22 items remain. M0–M19 are closed (archived under `docs/implementation/archive/`).
- **Red / not run:** CI is refused for billing, so every item is judged locally (`spotless:apply`, `verify`, `verify -Pintegration`). Nothing else is known red.
- **Owner-held:** CI billing (or the public flip); the 7WD bootstrap secret (re-check live before reporting it); the Repos Production reply, which decides whether 7WD ships under its name.

## Next Priorities

- `20`, `21` have no open dependency; `22` follows `20`. Keep the maps current: `check-corpus.py code-maps` fails on a renamed class they name.
- After M20: M21 public release (licence, README, gitleaks, published artifacts), M22 cloud deployment (ADR-0021 from `IMP-M20-15` first), then Phase C.

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
