## Last Session Summary

**Date:** 2026-11-07 (session 284) — **M20 closed and archived; M21 (public release) planned and registered, 12 items.**

- **M21 checks:**
  - gitleaks v8.28.0 over every full history found no leaks (1,296 commits, scanned from mirror clones).
  - **Names:** `@turnbase` on npm belongs to someone else, and `io.turnbase` cannot be claimed on Maven Central.
  - **History:** 33 old PRs keep the original commits on GitHub; the personal address is on 1,283 of 1,301 commits, in metadata only.
  - **7WD** ships no artwork, and its rulebook PDFs were never committed.
- **Owner decisions:**
  - coordinates `io.github.turnbase-platform` / `@turnbase-platform/gdk`;
  - **distribution on GitHub only** (a Maven repository on GitHub Pages, the GDK as a release tarball);
  - issues only, with an org `.github` repository;
  - **history kept as it is**, with a per-repository noreply `user.email` from today (set in all eight).
- **`*.localhost` in the platform's tests** (`turnbase-platform` 53758f6): a test-scoped resolver answers loopback; `verify -Pintegration` green, integration 279.8 s (46% of the 614.5 s baseline).
- **Language servers:** `jdtls-lsp` disabled; it builds into Maven's `target/classes` and broke a concurrent `verify`.
- **7WD CI green** for the first time, once `TURNBASE_SDK_PAT` existed.

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

- **M21:** `01` (licence), `03` (gate), `04` (coordinates, ADR-0022 first), `06` (README) and `07` (story) can start at once; then `02`, `05`, `08`; then the owner's flip session (`10`), `11` and `12`.
- Then M22, cloud deployment (from ADR-0021), then Phase C (`docs/specs/backlog.md` *Load-test findings*).

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
