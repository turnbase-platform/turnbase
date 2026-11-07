## Last Session Summary

**Date:** 2026-11-07 (session 291) — **IMP-M21-07 done: how it was built.**

- `docs/how-it-was-built.md`: spec-first layers, the agent workflow and guard-rails, the eight review rounds, evidence (load test, test cost, coverage rule, CVE gate) and what went wrong (PR suspension, stale `BLOCKED`, jdtls, CI refused, readiness blockers), with commit SHAs.
- `scripts/project-stats.sh` (new): commits, latest session, items, ADRs, requirement and spec counts, tests per repository from a checkout, no build. Output pasted into the page with its date; the page links the script. Run on this recursive clone, 7WD included.
- New `docs/INDEX.md` (the page had no INDEX above it); README links the page.
- Test counts are static counts of annotations, not run results; coverage is cited as the enforced rule, not a figure.

## Current State

- **Phase 1; M21 (public release) open**, 12 items in `docs/implementation/registry.md` (`01`–`07` done); M0–M20 are archived.
- **CI runs again.** Latest `master` runs are green in common, sdk, game-host, platform, frontend and 7WD.
- **Known noise, not failures:** Jackson 3 deprecations (`asText()`, `isTextual()`) in about ten platform classes.
- **Owner-held:**
  - the Repos Production reply (`IMP-M21-09`, BLOCKED);
  - creating the `.github` repository (`08`);
  - the flip session (`10`);
  - cutting `v0.1.0` in common and sdk.

## Next Priorities

- **M21:** `08`; then the owner's flip session (`10`), `11` and `12`.
- Then M22, cloud deployment (from ADR-0021), then Phase C (`docs/specs/backlog.md` *Load-test findings*).

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
