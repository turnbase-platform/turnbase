## Last Session Summary

**Date:** 2026-11-07 (session 293) — **IMP-M21-08 DONE: `.github` repository created and checked.**

- Created `turnbase-platform/.github` (private, default branch `master`) with the owner's in-session confirmation; pushed `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` and `profile/README.md`; deleted the staging directory `org-github/`.
- `scripts/repo-settings.sh --apply .github` fixed two drifts (Projects on, no topic); `--check` reports no drift across all nine repositories.

## Current State

- **Phase 1; M21 (public release) open**, 12 items in `docs/implementation/registry.md` (`01`–`08` done); M0–M20 are archived.
- **CI runs again.** Latest `master` runs are green in common, sdk, game-host, platform, frontend and 7WD.
- **Known noise, not failures:** Jackson 3 deprecations (`asText()`, `isTextual()`) in about ten platform classes.
- **Owner-held:**
  - the Repos Production reply (`IMP-M21-09`, BLOCKED);
  - the flip session (`10`);
  - cutting `v0.1.0` in common and sdk.

## Next Priorities

- **M21:** the owner's flip session (`10`), `11` and `12`.
- Then M22, cloud deployment (from ADR-0021), then Phase C (`docs/specs/backlog.md` *Load-test findings*).

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
