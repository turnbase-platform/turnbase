## Last Session Summary

**Date:** 2026-11-06 (session 279) — **`IMP-M20-18` DONE. 228 of 232 items done.**

- `OQ-6` reproduced: a JVM creates twelve Espresso contexts, the thirteenth fails (`Cannot load library: eden`), with one shared engine or the `nfi-dlmopen` backend named, closed contexts or not. Matches glibc's sixteen `dlmopen` namespaces (not proven). Before this the host stayed registered and failed every later creation with `INTERNAL`.
- Decision (recorded in `game-host-internals.md` §18 `OQ-6`): `ContextBudget` counts creations (`turnbase.gamehost.max-context-creations`, default 12); the creation past it answers `UNAVAILABLE` and retires the host: drain, deregister, exit through the wedge path, supervisor starts a fresh JVM. Pinned by `ContextBudgetTest` and `HostWedgeTest`.
- Game Host `verify -Pintegration` green locally (use `clean`: a second non-clean `verify` shaded the Boot jar and failed `GuestBridgeJarIT`). Ref bumped; corpus check clean.
- Next: `IMP-M20-19`, `20`, `21`; `22` waits on `20`.

## Current State

- **Phase 1, M20 (refinement) open**: 4 of 22 items remain. M0–M19 are closed (archived under `docs/implementation/archive/`).
- **Red / not run:** CI is refused for billing, so every item is judged locally (`spotless:apply`, `verify`, `verify -Pintegration`). Nothing else is known red.
- **Owner-held:** CI billing (or the public flip); the 7WD bootstrap secret (re-check live before reporting it); the Repos Production reply, which decides whether 7WD ships under its name.

## Next Priorities

- `19`, `20`, `21` have no open dependency; `22` follows `20`. Keep the maps current: `check-corpus.py code-maps` fails on a renamed class they name.
- After M20: M21 public release (licence, README, gitleaks, published artifacts), M22 cloud deployment (ADR-0021 from `IMP-M20-15` first), then Phase C.

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
