# ADR-0022: Distribution on GitHub only — public coordinates, Pages Maven repositories, release-asset FE GDK

- **Status:** Accepted
- **Date:** 2026-11-07
- **Deciders:** Project owner
- **Supersedes:** [ADR-0012](0012-repo-strategy-polyrepo-submodules.md) *Release Strategy* rows for `turnbase-common` and `turnbase-sdk` (GitHub Packages; Maven Central and npm deferred), and the `IMP-GATE-25` deferral
- **Executed by:** `IMP-M21-04` (this record, the documents, the coordinates); `IMP-M21-05` (release workflows); `IMP-M21-11` (consumers on `0.1.0`)

## Context

M21 makes the repositories public under Apache-2.0. Three facts decide where the artifacts go
(`registry.md` M21 findings):

- Nothing has ever been released: `turnbase-common` and `turnbase-sdk` are `0.1.0-SNAPSHOT`, every consumer's CI
  clones and installs the producer with a personal access token, and the games bundle a vendored GDK tarball (F6).
- The npm scope `@turnbase` belongs to someone else (`@turnbase/keygen`). A developer who writes a version
  instead of our URL would install that package: a dependency-confusion trap (F7). `io.turnbase` cannot be
  claimed on Maven Central either (F8).
- GitHub Packages' Maven and npm registries require a token even to read a public package. GitHub Pages and
  Release assets do not (F9).

## Decision

1. **Coordinates.** Every published jar has groupId `io.github.turnbase-platform` (artifactIds unchanged:
   `turnbase-grpc`, `turnbase-sdk`, `turnbase-serialization`, `turnbase-harness`, `turnbase-bundle-validator`).
   The FE GDK is the npm package `@turnbase-platform/gdk`. **Java package names stay `io.turnbase.*`** —
   a package is not a coordinate, and renaming them would touch every game for nothing.
   `io.github.turnbase-platform` is claimable on Maven Central through the GitHub organisation, which keeps that
   move open.
2. **Jars on GitHub Pages.** Each producer serves a Maven repository from its own Pages site:
   `https://turnbase-platform.github.io/turnbase-common/maven/` and
   `https://turnbase-platform.github.io/turnbase-sdk/maven/` (sdk, serialization, harness, bundle-validator).
   Consumers add the `<repository>` they need; a game designer needs only the sdk one. Reading needs no token.
3. **FE GDK as a release asset.** The `npm pack` tarball is attached to the `turnbase-sdk` GitHub Release of the
   tag and depended on by URL. The jars are attached to the release too.
4. **Images** stay on GHCR.
5. **Publishing mechanics.** A `v*.*.*` tag (cut by the owner) runs `publish.yml`, which deploys with
   `-DaltDeploymentRepository` into a checkout of the producer's `gh-pages` branch, pushes it and creates the
   release with the assets — with the workflow's own `GITHUB_TOKEN` (`contents: write`). **No secret.** Sources
   jars are published; there is no GPG signing (nothing validates it on Pages; Maven's checksums are written).
   `workflow_dispatch` with a `dry-run` input deploys into a workflow-local directory instead (`IMP-M21-05`).
6. **First release.** `v0.1.0` for `turnbase-common` and `turnbase-sdk`; pre-1.0 says the API may still move.

## Consequences

- Consumers pin `0.1.0` and resolve it anonymously; the bootstrap SNAPSHOT install and its PATs
  (`TURNBASE_COMMON_PAT`, `TURNBASE_SDK_PAT`, …) are deleted by `IMP-M21-11`. Until then `conventions.md` §5
  keeps describing the bootstrap that still runs.
- Pages on the free plan serves public repositories only, so no Pages deployment is exercised before the
  repositories flip (`IMP-M21-10`).
- Maven Central and npmjs remain possible later; nothing here forecloses them.
