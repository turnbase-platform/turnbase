## Last Session Summary

**Date:** 2026-11-06 (session 277) — **`IMP-M20-16` DONE. 226 of 232 items done.**

- `scripts/recovery-test.mjs` (+ `scripts/recovery-compose.override.yml`): compose stack, three rooms (in progress and returning, in progress and abandoned, lobby), every container stopped 40 s (past grace, the 35 s dispatch deadline and the lease TTL), restarted; asserts adoption at a higher epoch, intact session record and resumed game, grace counted from adoption, `GRACE_EXPIRED_NO_HUMAN` closure with teardown, lobby surviving, one new lease. Passes for SIGTERM and `--kill`. Documented in `local-environment.md` §8.
- Finding, not a defect: stopping the Frontend before the Platform drops sockets as ordinary disconnects (reservations open, Lobby rooms close at once, FR-DC-002), so a long outage then resolves in-progress rooms. The test stops the Platform first; the caveat is in §8.
- Umbrella only: no ref bump, no CI. Corpus check clean.
- Next: `IMP-M20-17`–`21` (no open dependency), `10` and `11`, `13`.

## Current State

- **Phase 1, M20 (refinement) open**: 11 of 22 items remain. M0–M19 are closed (archived under `docs/implementation/archive/`).
- **Red / not run:** CI is refused for billing, so every item is judged locally (`spotless:apply`, `verify`, `verify -Pintegration`). Nothing else is known red.
- **Owner-held:** CI billing (or the public flip); the 7WD bootstrap secret (re-check live before reporting it); the Repos Production reply, which decides whether 7WD ships under its name.

## Next Priorities

- `10` (PARTIAL, continue from its Remaining line), `11`, `13`, `15`, `17`, `18`, `19`, `20`, `21` have no open dependency. Keep the maps current: `check-corpus.py code-maps` fails on a renamed class they name.
- After M20: M21 public release (licence, README, gitleaks, published artifacts), M22 cloud deployment (ADR-0021 from `IMP-M20-15` first), then Phase C.

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
