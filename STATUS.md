## Last Session Summary

**Date:** 2026-11-07 (session 286) — **IMP-M21-02 done: third-party licence audit.**

- Reports from committed, pinned commands, named in each README: Maven `license-maven-plugin` 2.8.0 `add-third-party` (`aggregate-add-third-party` in sdk) in common, sdk, platform, game-host and both games; `npm run licenses` (`license-checker-rseidelsohn` 5.0.1, `--onlyAllow`) in frontend, sdk and both games.
- Findings: nothing incompatible. Espresso/Polyglot are GPLv2 (with the Classpath Exception) in the game-host image only; ICU4J (Unicode-3.0), HdrHistogram (CC0), Bouncy Castle (MIT-style) recorded; `css-mediaquery` is declared `BSD` (really BSD-3-Clause), excluded by name.
- Allowed families recorded in `conventions.md` §6 *Third-party licences*.
- Frontend image copies the two fonts' OFL text to `/licenses/`; the game bundles embed no fonts, so need none.
- CI green in all seven (the frontend needed one rerun of a flaky `App.test.tsx` validation-message test).

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

- **M21:** `03` (gate), `04` (coordinates, ADR-0022 first), `06` (README) and `07` (story) can start at once; then `05`, `08`; then the owner's flip session (`10`), `11` and `12`.
- Then M22, cloud deployment (from ADR-0021), then Phase C (`docs/specs/backlog.md` *Load-test findings*).

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
