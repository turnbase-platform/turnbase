## Last Session Summary

**Date:** 2026-11-07 (session 288) — **IMP-M21-04 done: coordinates and distribution, spec first.**

- **ADR-0022** (distribution on GitHub only) written first and registered; ADR-0012's release rows for common and sdk point at it; `CON-003` and `FR-FEGDK-007` name the real coordinates; `conventions.md` §5 states the target (Pages Maven repositories, release-asset tarball) above the bootstrap that still runs.
- **Code:** every pom's `groupId` and cross-references are `io.github.turnbase-platform`; the GDK is `@turnbase-platform/gdk` (package, imports, harness import map, both games). The games' `vendor/` tarballs were repacked from the renamed sdk. Java package names stay `io.turnbase.*`.
- Builds green locally in all six touched repositories (sdk with `-Pintegration`); no document outside the register and archives names the old coordinates.

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

- **M21:** `06` (README) and `07` (story) can start at once; then `05` (workflows), `08`; then the owner's flip session (`10`), `11` and `12`.
- Then M22, cloud deployment (from ADR-0021), then Phase C (`docs/specs/backlog.md` *Load-test findings*).

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
