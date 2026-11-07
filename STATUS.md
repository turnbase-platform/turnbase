## Last Session Summary

**Date:** 2026-11-07 (session 289) — **IMP-M21-05 done: release workflows on GitHub.**

- `publish.yml` in `turnbase-common` and `turnbase-sdk`: a `v*.*.*` tag deploys the jars into the `gh-pages` `/maven/` tree and (sdk) creates the release with the GDK tarball and jars; `GITHUB_TOKEN` only. `workflow_dispatch` `dry-run` (default true) deploys into a runner-local directory and proves the layout with `scripts/verify-maven-layout.sh` (throwaway consumer pom, `file://` repository, empty local repo); sdk also installs the tarball.
- Ran the dry-run steps locally in both repos: layout OK. That found a latent defect — the sdk `-Prelease` Javadoc failed on a broken `{@link}` in `MockOrchestration` (fixed).
- ADR-0022 §5 states what happens on a tag. Pages and the release step are not exercised before the flip (`IMP-M21-10`).

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

- **M21:** `06` (README) and `07` (story) can start at once; then `08`; then the owner's flip session (`10`), `11` and `12`.
- Then M22, cloud deployment (from ADR-0021), then Phase C (`docs/specs/backlog.md` *Load-test findings*).

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
