## Last Session Summary

**Date:** 2026-11-07 (session 287) — **IMP-M21-03 done: pre-flip privacy and secrets gate.**

- `scripts/preflip-check.sh` mirror-clones all eight repositories and fails on a gitleaks finding (pinned `v8.28.0` container), zero commits scanned, a non-noreply e-mail on a commit after the switch, or a tracked file naming the home path or personal address. `scripts/test-preflip-check.sh` plants one of each kind; it passes. The script passes on all eight.
- **Boundary is a moment, not a day:** two umbrella and one platform commit of the morning of 2026-11-07 still carry the personal address (before the noreply setting), so the default `--since` is `2026-11-07T14:00:00+01:00` (D8, F4).
- A `secrets` job (gitleaks, full history) is in every repository's `build.yml`; CI green in all seven (frontend needed one rerun of the flaky `App.test.tsx` validation tests).
- `.claude/settings.json` no longer names an absolute sandbox path (the default already allows writes under the project); `.claude/settings.local.json` is in `.gitignore`. Two docs that quoted the home path were reworded.

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

- **M21:** `04` (coordinates, ADR-0022 first), `06` (README) and `07` (story) can start at once; then `05`, `08`; then the owner's flip session (`10`), `11` and `12`.
- Then M22, cloud deployment (from ADR-0021), then Phase C (`docs/specs/backlog.md` *Load-test findings*).

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
