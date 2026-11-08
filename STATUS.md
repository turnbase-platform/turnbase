## Last Session Summary

**Date:** 2026-11-08 (session 297) — **IMP-M21-12 DONE: verified from the outside.**

- Fresh containers: anonymous `git clone --recursive` initially failed (SSH submodule URLs); fixed to https, 7WD set `update = none`.
- common, sdk, tictactoe `verify`, frontend `npm ci && build`, and a minimal game project (SDK from Pages, GDK from the tarball) all pass with no credentials.
- game-host and platform integration runs do not work inside docker-in-docker here; their proof is the green GitHub Actions `master` runs. Recorded in the registry.
- All README / `how-it-was-built.md` / org-profile URLs resolve anonymously. `CLAUDE.md` records the release.

## Current State

- **Phase 1; M21 (public release) open**, 12 items in `docs/implementation/registry.md` (all done except `09`); M0–M20 are archived.
- **CI runs again.** Latest `master` runs are green in common, sdk, game-host, platform, frontend and 7WD.
- **Known noise, not failures:** Jackson 3 deprecations (`asText()`, `isTextual()`) in about ten platform classes.
- **Owner-held:**
  - the Repos Production reply (`IMP-M21-09`, BLOCKED).

## Next Priorities

- **M21:** only `09` (owner-held) remains.
- Then M22, cloud deployment (from ADR-0021), then Phase C (`docs/specs/backlog.md` *Load-test findings*).

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
