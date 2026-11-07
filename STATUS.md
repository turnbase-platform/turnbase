## Last Session Summary

**Date:** 2026-11-07 (session 285) — **IMP-M21-01 done: Apache-2.0 in every repository.**

- Canonical Apache-2.0 text (`Copyright 2026 Hubert Mazur` in the appendix) as `LICENSE` in all eight repositories.
- `<licenses>` in the root `pom.xml` of common, sdk (children inherit), platform, game-host, tictactoe and 7WD; `"license": "Apache-2.0"` in the four `package.json` files.
- Spotless reformatted the inserted pom block in common, platform and game-host; every `verify` green, and CI green in all seven submodules; GitHub detects Apache-2.0 in each.
- 7WD's licence covers the code only (D1); its `NOTICE` belongs to `IMP-M21-09`.

## Current State

- **Phase 1; M21 (public release) open**, 12 items in `docs/implementation/registry.md`; M0–M20 are archived.
- **CI runs again.** Latest `master` runs are green in common, sdk, game-host, platform, frontend and 7WD.
- **Known noise, not failures:** Jackson 3 deprecations (`asText()`, `isTextual()`) in about ten platform classes.
- **Owner-held:**
  - the Repos Production reply (`IMP-M21-09`, BLOCKED);
  - creating the `.github` repository (`08`);
  - the flip session (`10`);
  - cutting `v0.1.0` in common and sdk.

## Next Priorities

- **M21:** `03` (gate), `04` (coordinates, ADR-0022 first), `06` (README) and `07` (story) can start at once; then `02`, `05`, `08` (`02` is unblocked now); then the owner's flip session (`10`), `11` and `12`.
- Then M22, cloud deployment (from ADR-0021), then Phase C (`docs/specs/backlog.md` *Load-test findings*).

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
