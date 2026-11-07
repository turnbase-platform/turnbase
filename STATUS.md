## Last Session Summary

**Date:** 2026-11-07 (session 294) — **IMP-M21-10 PARTIAL: flip runbook written; the owner's flip session remains.**

- Wrote `docs/specs/deployment/public-release.md` (registered in its INDEX): five ticked-by-date steps — gate, visibility order, `repo-settings.sh --apply --harden`, PAT removal, `v0.1.0`.
- The steps need the owner (visibility, GHCR, tags), so the item waits on that session. Nothing was flipped.

## Current State

- **Phase 1; M21 (public release) open**, 12 items in `docs/implementation/registry.md` (`01`–`08` done); M0–M20 are archived.
- **CI runs again.** Latest `master` runs are green in common, sdk, game-host, platform, frontend and 7WD.
- **Known noise, not failures:** Jackson 3 deprecations (`asText()`, `isTextual()`) in about ten platform classes.
- **Owner-held:**
  - the Repos Production reply (`IMP-M21-09`, BLOCKED);
  - the flip session (`10`);
  - cutting `v0.1.0` in common and sdk.

## Next Priorities

- **M21:** the owner's flip session (`10`, runbook ready), `11` and `12`.
- Then M22, cloud deployment (from ADR-0021), then Phase C (`docs/specs/backlog.md` *Load-test findings*).

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
