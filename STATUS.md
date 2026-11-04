## Last Session Summary

**Date:** 2026-11-04 (session 262) — **`IMP-M20-03` done: `CLAUDE.md` trimmed, counts checked. 213 of 232 items done.** Umbrella only.

- *Current Phase* is now three lines linking the register; per-milestone history and the work-item counts left `CLAUDE.md`. Restated "five repositories" wording removed.
- New `counts` check in `scripts/check-corpus.py` (7th): numbers `CLAUDE.md` states for requirement documents, work items, repositories and submodules must equal the disk; verified to fail on a planted wrong count.
- Auto-memory (outside the repo, not checkable): `MEMORY.md` + `project_turnbase_overview.md` — a pointer only, deferring to `CLAUDE.md`/`STATUS.md`; no contradicting claim.

## Current State

- **Phase 1, M20 (refinement) open**: 19 of 22 items remain. M0–M19 are closed (archived under `docs/implementation/archive/`).
- **Red / not run:** CI is refused for billing, so every item is judged locally (`spotless:apply`, `verify`, `verify -Pintegration`). Nothing else is known red.
- **Owner-held:** CI billing (or the public flip); the 7WD bootstrap secret (re-check live before reporting it); the Repos Production reply, which decides whether 7WD ships under its name.

## Next Priorities

- `IMP-M20-03` (`CLAUDE.md` trim) is now unblocked; `04`, `05`, `07`, `08`, `13`, `15`, `17`, `18`, `19`, `20`, `21` have no open dependency; `06` is unblocked.
- After M20: M21 public release (licence, README, gitleaks, published artifacts), M22 cloud deployment (ADR-0021 from `IMP-M20-15` first), then Phase C.

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
