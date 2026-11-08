## Last Session Summary

**Date:** 2026-11-08 (session 296) — **IMP-M21-11 DONE: consumers on `0.1.0`, every secret gone.**

- Platform, game-host, tictactoe and 7WD pin `0.1.0` of common/sdk through the Pages `<repository>` entries; every clone-and-install step is deleted; the games depend on the `v0.1.0` release tarball by URL and `vendor/` is gone.
- CI green in all four on `master`. `gh secret list` is empty in all eight repositories (org-level secrets not readable: 403).
- Build-time saving measured per consumer (25–43 s) and recorded in the registry row; `conventions.md` §5 rewritten to the released state.
- One `ReconciliationJobIT` flake when two builds ran in parallel locally; green alone and in CI.

## Current State

- **Phase 1; M21 (public release) open**, 12 items in `docs/implementation/registry.md` (`01`–`08`, `10`, `11` done); M0–M20 are archived.
- **CI runs again.** Latest `master` runs are green in common, sdk, game-host, platform, frontend and 7WD.
- **Known noise, not failures:** Jackson 3 deprecations (`asText()`, `isTextual()`) in about ten platform classes.
- **Owner-held:**
  - the Repos Production reply (`IMP-M21-09`, BLOCKED).

## Next Priorities

- **M21:** `12` (verified from the outside); `09` stays owner-held.
- Then M22, cloud deployment (from ADR-0021), then Phase C (`docs/specs/backlog.md` *Load-test findings*).

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
