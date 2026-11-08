## Last Session Summary

**Date:** 2026-11-08 (session 298) — **IMP-M21-09 DONE: 7WD published.**

- Owner decided to publish without the publisher's reply (no original art). 7WD got a `NOTICE` and an unofficial-implementation disclaimer in README/`INFO.md`; CI green.
- `preflip-check.sh` passed; repo flipped PUBLIC and hardened (`repo-settings.sh --check --harden`: no drift).
- Umbrella: `update = none` removed from `.gitmodules`, README and runbook updated, decision recorded in the spike INDEX. Ref bumped.

## Current State

- **Phase 1; M21 (public release) complete**, all 12 items done; M0–M20 are archived.
- **CI runs again.** Latest `master` runs are green in common, sdk, game-host, platform, frontend and 7WD.
- **Known noise, not failures:** Jackson 3 deprecations (`asText()`, `isTextual()`) in about ten platform classes.

## Next Priorities

- **M21** is closed (archive it). Next: M22, cloud deployment (from ADR-0021), then Phase C (`docs/specs/backlog.md` *Load-test findings*).

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
