# Repo Strategy Design

**Date:** 2026-06-12
**Status:** Approved

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
| `turnbase-common` | Internal shared library: gRPC stubs, shared internal models | `io.turnbase:turnbase-grpc` (Maven / GitHub Packages) |
| `turnbase-sdk` | Public GDK: `TurnBaseGame` interface, effect/input types, TypeScript types | `io.turnbase:turnbase-sdk` (Maven) + npm package |
| `turnbase-platform` | Platform Monolith (Spring Boot 3.5+) | Docker image |
| `turnbase-game-host` | Game Host (GraalVM CE for JDK 21 + Truffle) | Docker image |
| `turnbase-frontend` | Platform frontend (React 19, TypeScript) | Docker image / static assets |

All repos are **private** during Phase 0. Visibility may be changed to public when the project is ready to showcase.

### Submodule policy

All five component repos are registered as git submodules in `turnbase`. Cloning with `--recurse-submodules` pulls everything. Each component repo is independently usable without the root. Submodule refs in `turnbase` are updated only after the submodule's build and tests pass.

### No shared state between repos at the git level

Repos are not wired together beyond submodule registration. Cross-repo changes require separate PRs per repo. The `gamehost.proto` file is the canonical source of truth in `turnbase/docs/specs/internal-grpc/`; `turnbase-common` copies it into its own `src/main/proto/` at build time.

## Branch Model

Applied consistently across all repos:

- `master` — always deployable / releasable; protected, no direct pushes
- `feat/<description>` — new features
- `fix/<description>` — bug fixes
- `docs/<description>` — documentation changes
- `chore/<description>` — dependency bumps, CI changes, tooling

No `develop` branch. PRs go directly from feature branches into `master`. Self-merge is fine for solo work; the PR record is the value.

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
| `turnbase-sdk` | Semantic versioning (`v1.2.3`) | Manual tag on `master`; CI publishes to Maven Central + npm |
| `turnbase-common` | Semantic versioning | Manual tag; CI publishes to GitHub Packages |
| `turnbase-platform` | Semantic versioning | Manual tag; CI builds + pushes Docker image |
| `turnbase-game-host` | Semantic versioning | Manual tag; CI builds + pushes Docker image |
| `turnbase-frontend` | Semantic versioning | Manual tag; CI builds + pushes Docker image |
| `turnbase` | No releases | Commits to `master` for docs; PRs for submodule ref bumps |

No releases in Phase 0. Tags and CI pipelines are added per repo when implementation begins.

## Alternatives Considered

**True monorepo** — rejected because the SDK needs a clean public artifact with no internal platform dependencies leaking through transitive dependencies, and independent Docker image releases are cleaner per-repo.

**Orchestrator + git submodules (original CLAUDE.md plan)** — retained in spirit, but the landing repo (`turnbase`) is the hub, not an orchestrator with pinned compatible-version snapshots. Submodule refs track `master` in Phase 0.

**Separate `turnbase-contracts` repo** — considered for the gRPC proto; folded into `turnbase-common` because the proto is only used by platform-internal services and does not need its own release lifecycle.
