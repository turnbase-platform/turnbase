## Last Session Summary

**Date:** 2026-11-04 (session 261) — **`IMP-M20-02` done: `STATUS.md` reset to the present. 212 of 232 items done.** Umbrella only.

- The file was 260 lines of M0-era text; it is now this page. Lessons worth keeping went to `conventions.md` §6 (Dependabot `ignore` rules, line endings); the rest was already in `conventions.md`/submodule `CLAUDE.md` or is spent. The commit body lists each.
- The per-document coverage table and the open-questions table were dropped: `docs/requirements/INDEX.md`, `docs/specs/INDEX.md` and each document's own *Open questions* are the authority (`IMP-M20-20` triages them).

## Current State

- **Phase 1, M20 (refinement) open**: 20 of 22 items remain. M0–M19 are closed (archived under `docs/implementation/archive/`).
- **Red / not run:** CI is refused for billing, so every item is judged locally (`spotless:apply`, `verify`, `verify -Pintegration`). Nothing else is known red.
- **Owner-held:** CI billing (or the public flip); the 7WD bootstrap secret (re-check live before reporting it); the Repos Production reply, which decides whether 7WD ships under its name.

## Next Priorities

- `IMP-M20-03` (`CLAUDE.md` trim) is now unblocked; `04`, `05`, `07`, `08`, `13`, `15`, `17`, `18`, `19`, `20`, `21` have no open dependency; `06` is unblocked.
- After M20: M21 public release (licence, README, gitleaks, published artifacts), M22 cloud deployment (ADR-0021 from `IMP-M20-15` first), then Phase C.

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
