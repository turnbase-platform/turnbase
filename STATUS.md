## Last Session Summary

**Date:** 2026-11-06 (session 278) — **`IMP-M20-17` DONE. 227 of 232 items done.**

- Time-to-ready measured in the compose stack with `scripts/startup-time.sh` (median of five): Platform 9.6 s, Game Host 8.6 s. Tried dynamic CDS (8.4 s, −13 %), `TieredStopAtLevel=1` (10.1 s), SerialGC (9.5 s), lazy initialisation (8.9 s). All rejected, reasons in `local-environment.md` §8 *Startup time*: the CDS archive never survives a replaced pod, needs a diagnostic flag beside the OTel agent, and its shutdown dump trips the Game Host supervisor.
- No image or service change; umbrella only, no ref bump, no CI. Corpus check clean.
- Next: `IMP-M20-18`–`21` (no open dependency), `10`, `11`, `13` are closed already; `22` waits on `20`.

## Current State

- **Phase 1, M20 (refinement) open**: 5 of 22 items remain. M0–M19 are closed (archived under `docs/implementation/archive/`).
- **Red / not run:** CI is refused for billing, so every item is judged locally (`spotless:apply`, `verify`, `verify -Pintegration`). Nothing else is known red.
- **Owner-held:** CI billing (or the public flip); the 7WD bootstrap secret (re-check live before reporting it); the Repos Production reply, which decides whether 7WD ships under its name.

## Next Priorities

- `18`, `19`, `20`, `21` have no open dependency; `22` follows `20`. Keep the maps current: `check-corpus.py code-maps` fails on a renamed class they name.
- After M20: M21 public release (licence, README, gitleaks, published artifacts), M22 cloud deployment (ADR-0021 from `IMP-M20-15` first), then Phase C.

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
