## Last Session Summary

**Date:** 2026-11-07 (session 290) — **IMP-M21-06 done: the umbrella README.**

- `README.md`: two-sentence pitch, five screenshots (`docs/assets/`, WebP under 40 KB each, registered in `docs/assets/INDEX.md`), a Mermaid architecture diagram, the repository map, a quickstart, *Write a game* with the ADR-0022 coordinates, status and roadmap, licence, 7WD's pending state (D9) and contributions (D11).
- Followed the quickstart from a fresh SSH clone in `/tmp`: stack healthy, `:8080` returns 200, catalog seeded. The spec's §5 first-run omits the `install` of common and sdk and the `package` of the platform and game-host jars; the README has them (spec text not touched).
- `check-corpus.py` now also checks `README.md`; `CLAUDE.md` links it as the landing page.
- Room screenshot is light only (the dark one would have needed a second room).
- The README does not link the story document until `IMP-M21-07` lands it.

## Current State

- **Phase 1; M21 (public release) open**, 12 items in `docs/implementation/registry.md` (`01`–`06` done); M0–M20 are archived.
- **CI runs again.** Latest `master` runs are green in common, sdk, game-host, platform, frontend and 7WD.
- **Known noise, not failures:** Jackson 3 deprecations (`asText()`, `isTextual()`) in about ten platform classes.
- **Owner-held:**
  - the Repos Production reply (`IMP-M21-09`, BLOCKED);
  - creating the `.github` repository (`08`);
  - the flip session (`10`);
  - cutting `v0.1.0` in common and sdk.

## Next Priorities

- **M21:** `07` (story; link it from the README when done), then `08`; then the owner's flip session (`10`), `11` and `12`.
- Then M22, cloud deployment (from ADR-0021), then Phase C (`docs/specs/backlog.md` *Load-test findings*).

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
