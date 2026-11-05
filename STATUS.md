## Last Session Summary

**Date:** 2026-11-05 (session 265) — **`IMP-M20-06` done: Claude tooling reviewed. 216 of 232 items done.**

- `.claude/settings.json`: 13 hand-written `git push` / `git merge` / `git pull` allows removed — no session since `scripts/git-land.sh` has used one, and `git-land.sh` runs them inside the script. Deny list and the rest unchanged; the file still parses.
- `run-turnbase` skill: two statements stale since M7 (room views "not built", MR-02/MR-03 "tracked") corrected. The other skills carry no post-archive references.
- **Language server rejected.** `jdtls-lsp` and `typescript-lsp` are enabled, but `LSP findReferences` on `GameInputDispatcher.dispatch` fails with `ENOENT: jdtls`: neither `jdtls` nor `tsserver` is on `PATH`. The same lookup by `grep -rn` took one call and under a second (one caller, three files). Installing a server is the owner's call; with one installed, retry on a rename-shaped task, where grep is weakest.

## Current State

- **Phase 1, M20 (refinement) open**: 16 of 22 items remain. M0–M19 are closed (archived under `docs/implementation/archive/`).
- **Red / not run:** CI is refused for billing, so every item is judged locally (`spotless:apply`, `verify`, `verify -Pintegration`). Nothing else is known red.
- **Owner-held:** CI billing (or the public flip); the 7WD bootstrap secret (re-check live before reporting it); the Repos Production reply, which decides whether 7WD ships under its name.

## Next Priorities

- `07`, `08`, `13`, `15`, `17`, `18`, `19`, `20`, `21` have no open dependency. Keep the maps current: `check-corpus.py code-maps` fails on a renamed class they name.
- After M20: M21 public release (licence, README, gitleaks, published artifacts), M22 cloud deployment (ADR-0021 from `IMP-M20-15` first), then Phase C.

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
