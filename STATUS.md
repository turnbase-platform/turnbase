## Last Session Summary

**Date:** 2026-11-05 (session 266) — **`IMP-M20-07` done: the build is honest, refs verified. 217 of 232 items done.**

- **Frontend image:** `apk upgrade --no-cache` in the runtime stage (the `nginx:1.31-alpine` base, freshly pulled, still carried `brotli-libs` 1.2.0-r1 and `curl` 8.22). `trivy image` is clean at HIGH+CRITICAL (was 1 CRITICAL + 9 HIGH). Pushed as 9197741; its CI run is green, Trivy gate included. Ref bumped.
- **Local builds at the pinned refs:** common, sdk, tictactoe, 7WD (format, lint, typecheck, 263 tests, bundle) and frontend (lint, format, build, 944 tests) green; game-host `spotless:check verify -Pintegration` green (22 ITs). Stale `target/` after an SDK change gives `NoSuchMethodError: Effects.log` in tictactoe and game-host: `clean` fixes it.
- **Platform:** CI is green at the pinned 7ba10d1 (run 2026-11-05 16:55). The local `verify -Pintegration` had 9 failures: 7 (`GameAssetControllerIT` 6, `SeedDataIT` 1) are this WSL's dead DNS (`/etc/resolv.conf` names 10.255.255.254, which times out, so Java cannot resolve `<uuid>.games.localhost`); 2 (`GuestPurgeJobIT`, `NotificationPurgeJobsIT`) pass alone and fail only inside the full run — an order dependency for `IMP-M20-09`/`12`. Not fixed here.
- A flaky frontend test failed once in four `npm test` runs (944 tests); the failing name was not captured.
- Re-checked live: `gh secret list` on 7WD is empty, so its CI stays red until the owner provisions the SDK token.

**CI per repository (last run on `master`, 2026-11-05):**

| Repository | Pinned | Last CI |
|---|---|---|
| turnbase-common | 8b6d68b | failure 2026-10-29 (log expired); local build green |
| turnbase-sdk | 7a02471 | success |
| turnbase-platform | 7ba10d1 | success |
| turnbase-game-host | 7f9734f | success |
| turnbase-frontend | 9197741 | success |
| turnbase-game-tictactoe | c5a0d08 | success (2026-10-04, no later push) |
| turnbase-game-7wonders-duel | bfddf79 | failure — missing SDK bootstrap token (owner) |

CI does run again; the umbrella has no workflow.

## Current State

- **Phase 1, M20 (refinement) open**: 15 of 22 items remain. M0–M19 are closed (archived under `docs/implementation/archive/`).
- **Red / not run:** CI is refused for billing, so every item is judged locally (`spotless:apply`, `verify`, `verify -Pintegration`). Nothing else is known red.
- **Owner-held:** CI billing (or the public flip); the 7WD bootstrap secret (re-check live before reporting it); the Repos Production reply, which decides whether 7WD ships under its name.

## Next Priorities

- `08`, `13`, `15`, `17`, `18`, `19`, `20`, `21` have no open dependency. Keep the maps current: `check-corpus.py code-maps` fails on a renamed class they name.
- After M20: M21 public release (licence, README, gitleaks, published artifacts), M22 cloud deployment (ADR-0021 from `IMP-M20-15` first), then Phase C.

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
