## Last Session Summary

**Date:** 2026-11-08 (session 299) — **M21 verified, closed and archived.**

- Live verification: all 9 repositories PUBLIC, Apache-2.0 detected, `preflip-check.sh` PASS, no Actions secret anywhere, both `0.1.0` `maven-metadata.xml` and the GDK tarball 200 anonymously, GHCR images pullable anonymously, 16 public links checked. Clean `maven:3.9-eclipse-temurin-21` container: `git clone --recursive` (7WD included), `./mvnw verify` for tictactoe and 7WD, a minimal project on the Pages SDK, `npm i` of the tarball, all green.
- **Defect found and fixed:** CodeQL was never set up; `repo-settings.sh` matched `not-configured` with `grep -q configured`. Now `grep -qx`; applied, `configured` in all nine repositories; three high alerts dismissed as false positives / test code, with reasons (`IMP-M21-10` close-out).
- Dev-tooling advisories cleared in frontend, sdk, tictactoe, 7WD (production audit was already clean): patched vite/vitest/esbuild/ws, lock refresh, `overrides.minimatch` 11.0.1. Left: sdk esbuild 0.27.7 (tsup 8.5.1 pins `^0.27`; low, Windows dev server only).
- `.github` repository got its `LICENSE`. M21 moved to `docs/implementation/archive/M21-public-release.md`.

## Current State

- **Phase 1; no milestone open.** M0–M21 are archived (244 items, all done). The repositories are public and `0.1.0` of common and sdk is released.
- **CI green** on every `master`; CodeQL default setup runs in all nine repositories.
- **Known noise, not failures:** Jackson 3 deprecations (`asText()`, `isTextual()`) in about ten platform classes; the 7WD checkout here has `core.autocrlf=true`, so its local `npm run format:check` reports CRLF (the index is LF; CI does not run it).

## Next Priorities

- **Plan M22, cloud deployment** (from ADR-0021), the way M21 was planned: a design pass, then registered items. Then Phase C (`docs/specs/backlog.md` *Load-test findings*).
- Optional: tsup 9 in sdk (clears the last esbuild advisory); a Repos Production reply, if one comes, is recorded against `IMP-M21-09`.

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
