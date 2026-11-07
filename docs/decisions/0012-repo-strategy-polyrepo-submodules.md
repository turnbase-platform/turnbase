# ADR-0012: Repository strategy — polyrepo under an organisation, with submodules

- **Status:** Accepted
- **Date:** 2026-06-12
- **Deciders:** Project owner
- **Source:** Taken at project inception, before the ADR directory existed. Filed as an ADR on
  2026-08-16 because it is a cross-cutting decision that `CLAUDE.md` compresses to a single line
  (*"a submodule boundary is drawn where a component can be independently versioned, deployed, or
  replaced"*), and that line is the conclusion without the argument.

## Context

TurnBase is a portfolio project consisting of six independently deployable components. This document records the GitHub repository strategy decided at project inception.

## Decision

**Polyrepo under a GitHub Organisation, with git submodules in the landing repo.**

### Organisation

All repos live under the `turnbase-platform` GitHub organisation (`github.com/turnbase-platform`).

### Repos

| Repo | Role | Published artifact |
|------|------|--------------------|
| `turnbase` | Landing repo: docs, specs, submodule refs | — |
| `turnbase-common` | Internal shared library: gRPC stubs, shared internal models | `io.github.turnbase-platform:turnbase-grpc` (Maven, GitHub Pages — ADR-0022) |
| `turnbase-sdk` | Public GDK: `TurnBaseGame` interface, effect/input types, TypeScript types | `io.github.turnbase-platform:turnbase-sdk` (Maven) + npm package |
| `turnbase-platform` | Platform Monolith (Spring Boot 4.1+ — [ADR-0016](0016-spring-boot-4-migration.md)) | Docker image |
| `turnbase-game-host` | Game Host (GraalVM CE for JDK 21 + Truffle) | Docker image |
| `turnbase-frontend` | Platform frontend (React 19, TypeScript) | Docker image / static assets |
| `turnbase-game-tictactoe` | First official game — a **consumer** of the published GDK, not a platform component (`IMP-M3-10`; ADR-0006) | Game bundle (`<gameId>.zip`, `bundle-format.md` §2) |
| `turnbase-game-7wonders-duel` | Second official game (skeleton) — a **consumer** of the published GDK, with a React frontend; not a platform component (ADR-0006) | Game bundle (`<gameId>.zip`, `bundle-format.md` §2) |

All repos are **private** during Phase 0. Visibility may be changed to public when the project is ready to showcase.

### Submodule policy

All five component repos, and the first official game (a consumer, not a component), are registered as git submodules in `turnbase`. Cloning with `--recurse-submodules` pulls everything. Each component repo is independently usable without the root. Submodule refs in `turnbase` are updated only after the submodule's build and tests pass.

### No shared state between repos at the git level

Repos are not wired together beyond submodule registration. Cross-repo changes require a separate change per repo. The `gamehost.proto` file is the canonical source of truth in `turnbase/docs/specs/internal-grpc/`; `turnbase-common` holds a **committed copy** at `src/main/proto/turnbase/gamehost/v1/gamehost.proto`.

**Amended 2026-08-20 (IMP-GATE-02).** This clause originally read *"copies it into its own
`src/main/proto/` at build time"*, which contradicts the submodule policy above: a build step reading
`../docs/` cannot run in a standalone clone, and `turnbase-common`'s own CI clones `turnbase-common`
rather than the superproject. The copy is therefore a **tracked file**, not a build artifact —
`turnbase-common` builds from its own tree with no path outside the repository, and the
independence clause holds.

Synchronisation is a **parent-repo** concern, because that is the only checkout where both files
exist:

- `scripts/sync-proto.sh` refreshes the copy from the authoritative file.
- `scripts/sync-proto.sh --check` fails if they differ, and runs in the parent's `pre-push` hook.

Drift is the whole risk this arrangement carries — two identical-looking protos that diverge while
both sides still compile — so the guard is mechanical rather than a rule in a document.

## Branch Model

Applied consistently across all repos:

- `master` — always deployable / releasable. **Not branch-protected**, and direct pushes are
  allowed: GitHub does not offer branch protection on private repositories outside a paid plan, and
  a rule the platform cannot enforce is one that reads as a guarantee while being an honour system.
  The discipline is the branch model below, not a server-side block *(amended 2026-08-20 — the clause
  previously read "protected, no direct pushes", which contradicted this ADR's own "self-merge is
  fine for solo work")*
- `feat/<description>` — new features
- `fix/<description>` — bug fixes
- `docs/<description>` — documentation changes
- `chore/<description>` — dependency bumps, CI changes, tooling

No `develop` branch. Branches merge directly into `master`.

### Pull requests are suspended *(amended 2026-09-05)*

**Do not open pull requests.** A branch is still the normal way to do a piece of work, but it is
**merged into `master` and deleted within the session that created it** — not left open across
sessions, and not turned into a PR.

This reverses the clause that stood here until 2026-09-05: *"PRs go directly from feature branches
into `master`. Self-merge is fine for solo work; the PR record is the value."* The record turned out
not to be worth its cost. On a solo project with no second reviewer, a self-merged PR adds no review
that the branch did not already have, and in practice they were not being merged at all: by
2026-09-05 there were eight open PRs and eleven abandoned branches across five repositories, none of
them awaiting anybody's opinion. The residue — stale branches, open PRs, merge commits from
long-diverged work — cost more attention than the record ever returned.

What this does and does not change:

- **A branch per change stays.** The naming above is unchanged, and so is the reason for it: the
  work is isolated until it is green.
- **The merge happens in the same session.** A branch that outlives its session is the failure mode
  being removed; if the work is not finished, it stays unmerged and unpushed, not parked as a PR.
- **Delete the branch on merge**, locally and on the remote. Prefer a fast-forward merge, so the
  history of `master` stays linear and no merge commit records a branch that no longer exists.
- **CI still runs.** Every repository's workflow triggers on `push` to `master` as well as
  `pull_request`, so a direct merge is checked exactly as a PR was. The one check that was
  PR-only — `buf breaking` in `turnbase-common` — now runs on push against the previous commit,
  because a contract check that never fires is worse than none.
- **The `pull_request` triggers stay in the workflows.** They cost nothing while unused and are what
  makes resuming PRs a decision rather than a rebuild.

This is a working-practice suspension for the remainder of Phase 1 implementation, reversible by
amending this section. `platform-operations.md` FR-CICD-002 still specifies what a pull-request
pipeline must do, and still holds — the pipeline retains that capability; what changed is that
nothing is currently exercising it.

## Commit Conventions

[Conventional Commits](https://www.conventionalcommits.org/) across all repos:

```
<type>(<scope>): <subject>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
Breaking changes: append `!` — e.g. `feat(grpc)!: rename CreateSession fields`
Subject: ≤ 72 chars, imperative mood, no trailing period.

## Release Strategy

| Repo | Versioning | Trigger |
|------|-----------|---------|
| `turnbase-sdk` | Semantic versioning (`v1.2.3`) | Manual tag on `master`; CI publishes the Maven artifacts and the FE GDK tarball to GitHub — see [ADR-0022](0022-distribution-on-github.md), which supersedes the earlier GitHub Packages / deferral wording (`IMP-GATE-25`). |
| `turnbase-common` | Semantic versioning | Manual tag `v*.*.*`; CI publishes to the repository's GitHub Pages Maven tree (ADR-0022 §5 lists the steps; `IMP-M21-05`) |
| `turnbase-platform` | Semantic versioning | Manual tag; CI builds + pushes Docker image |
| `turnbase-game-host` | Semantic versioning | Manual tag; CI builds + pushes Docker image |
| `turnbase-frontend` | Semantic versioning | Manual tag; CI builds + pushes Docker image |
| `turnbase` | No releases | Commits to `master` for docs and for submodule ref bumps |

No releases in Phase 0. Tags and CI pipelines are added per repo when implementation begins.

## Alternatives Considered

**True monorepo** — rejected because the SDK needs a clean public artifact with no internal platform dependencies leaking through transitive dependencies, and independent Docker image releases are cleaner per-repo.

**Orchestrator + git submodules (original CLAUDE.md plan)** — retained in spirit, but the landing repo (`turnbase`) is the hub, not an orchestrator with pinned compatible-version snapshots. Submodule refs track `master` in Phase 0.

**Separate `turnbase-contracts` repo** — considered for the gRPC proto; folded into `turnbase-common` because the proto is only used by platform-internal services and does not need its own release lifecycle.
