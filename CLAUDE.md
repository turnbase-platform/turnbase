# TurnBase — CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project Overview

TurnBase is a platform for hosting and playing multiplayer games online. It provides:
- User registration, profiles, and friend management
- Game room creation, invitations, and in-session chat
- Game history
- A catalog of official games and support for user-uploaded games
- A public SDK/API for third-party game developers

**Primary Goal:** Showcase software engineering capabilities with a focus on architecture, maintainability, security, and scalability. This is also an experiment in leveraging AI coding agents (Claude Code) throughout the full development lifecycle.

## Current Phase

**Phase 1 — Implementation**, under way; M21 (public release) is nearly closed: the repositories are public (Apache-2.0) and `0.1.0` of `turnbase-common` and `turnbase-sdk` is released on GitHub Pages / Releases (2026-11-07, [ADR-0022](docs/decisions/0022-distribution-on-github.md)); `turnbase-game-7wonders-duel` was made public too (2026-11-08, `IMP-M21-09`); M20 (refinement) closed the same day.
The register ([`registry.md`](docs/implementation/registry.md)) holds the open items and
[STATUS.md](STATUS.md) the progress; closed milestones are in `docs/implementation/archive/`.

Check [STATUS.md](STATUS.md) at the start of each session.

**Before writing any code**, read [docs/implementation/INDEX.md](docs/implementation/INDEX.md) and
[docs/implementation/conventions.md](docs/implementation/conventions.md) (package layout, formatting,
tests, coverage, cross-repo versions — settled once, not per item). No work item is gated by the
2026-08-16 readiness audit. A specification defect found while implementing is fixed in the
specification, not in code — use the **`spec-defect`** skill.

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Platform Monolith | Java 21, Spring Boot 4.1+ | Migrated from 3.5 by milestone M11 ([ADR-0016](docs/decisions/0016-spring-boot-4-migration.md)). Host-side JSON is Jackson 3 (`tools.jackson`); only GA Boot releases, never milestones/RCs |
| Game Host service | Java 21, Spring Boot 4.1+, GraalVM CE for JDK 21 + Truffle | Host JVM is Java 21; game code runs in Espresso (Java 21 guest). No CE build exists for JDK 23; the earlier "CE 23" label was the deprecated GraalVM product-version scheme. |
| Game backends (SDK) | Java 21 (max) | Executed in Espresso; must not use Java 22+ APIs |
| Frontend (platform) | React 19, TypeScript | Clean, responsive, modern |
| Design system | [Astryx](https://github.com/facebook/astryx) (`@astryxdesign/core`) + the TurnBase theme | Astryx is Meta's open-source design system — 150+ components, MIT, React 19+. **Pin exact versions; it is Beta.** The look is TurnBase's own — a custom theme built with `astryx theme build` and committed, Light/Dark/Auto, Figtree + Pixelify Sans self-hosted ([ADR-0017](docs/decisions/0017-turnbase-visual-identity.md), amending 0013 §4). Look components up with `npm run astryx -- component <Name>` or the `astryx` MCP server, never from a list in this repo ([ADR-0013](docs/decisions/0013-astryx-design-system.md)) |
| Game UIs | Any JS-compilable language | Sandboxed iframes |
| Infrastructure | Kubernetes | Auto-scaling by traffic and active games |
| Build (backend) | Maven | |
| Build (frontend) | Vite | Astryx ships pre-built CSS and the TurnBase theme is built ahead of time — no StyleX plugin, no PostCSS, no Babel config |
| Metrics | Micrometer → Prometheus → Grafana | Spring Boot native |
| Logs | SLF4J/Logback (JSON) → Loki → Grafana | Structured, stdout in K8s |
| Traces | OpenTelemetry → Tempo → Grafana | W3C trace context propagation |

## Repository Structure

TurnBase lives under the **[turnbase-platform](https://github.com/turnbase-platform)** GitHub organisation. Each independently deployable component has its own repository with its own GitHub Actions workflows, versioning, and deployment pipeline. All component repos are registered as git submodules here.

| Repository | Description | Published artifact |
|------------|-------------|-------------------|
| [`turnbase`](https://github.com/turnbase-platform/turnbase) | This repo — the [landing page](README.md), docs, specs, submodule refs | — |
| [`turnbase-common`](https://github.com/turnbase-platform/turnbase-common) | Internal shared library: gRPC stubs, internal models | `io.github.turnbase-platform:turnbase-grpc` (Maven) |
| [`turnbase-sdk`](https://github.com/turnbase-platform/turnbase-sdk) | Public GDK: `TurnBaseGame` interface, effect/input types, TS types | `io.github.turnbase-platform:turnbase-sdk` (Maven) + npm package |
| [`turnbase-platform`](https://github.com/turnbase-platform/turnbase-platform) | Platform Monolith (Spring Boot 4.1+) | Docker image |
| [`turnbase-game-host`](https://github.com/turnbase-platform/turnbase-game-host) | Game Host (GraalVM CE for JDK 21 + Truffle) | Docker image |
| [`turnbase-frontend`](https://github.com/turnbase-platform/turnbase-frontend) | Platform frontend (React 19, TypeScript) | Docker image / static assets |
| [`turnbase-game-tictactoe`](https://github.com/turnbase-platform/turnbase-game-tictactoe) | First official game (`IMP-M3-10`) — a **consumer** of the published SDK, not a platform component | Game bundle (`<gameId>.zip`) |
| [`turnbase-game-7wonders-duel`](https://github.com/turnbase-platform/turnbase-game-7wonders-duel) | Second official game (base game complete, React frontend; credits its original authors) — a **consumer** of the published SDK, not a platform component | Game bundle (`<gameId>.zip`) |

```
turnbase/                    # This repo (landing page: README.md, + docs)
├── CLAUDE.md
├── STATUS.md
├── docs/
│   ├── requirements/        # What the system must do — INDEX.md + 17 per-feature documents
│   ├── specs/               # How it is designed — INDEX.md + one subdirectory per design domain,
│   │                        #   each with its own INDEX.md (api-design, platform, flows,
│   │                        #   deployment, internal-grpc, game-host, gdk-api, manifest,
│   │                        #   platform-frontend, game-frontend)
│   ├── decisions/           # ADRs — one numbered file per architectural decision
│   ├── implementation/      # The build plan — INDEX.md (conventions) + registry.md (open work items) + archive/
│   └── reviews/             # Closed review rounds, reduced to their INDEX plus anything still cited
├── turnbase-common/         # git submodule
├── turnbase-sdk/            # git submodule
├── turnbase-platform/       # git submodule
├── turnbase-game-host/      # git submodule
├── turnbase-frontend/       # git submodule
├── turnbase-game-tictactoe/ # git submodule — first official game (a consumer of the SDK)
└── turnbase-game-7wonders-duel/ # git submodule — second official game (a consumer of the SDK)
```

**Dependency graph:**
```
turnbase-sdk    ← game developers (Maven / npm)
                ← turnbase-game-host (loads JARs implementing TurnBaseGame)

turnbase-common ← turnbase-platform  (gRPC client stubs)
                ← turnbase-game-host (gRPC server stubs)

turnbase-frontend — no Maven dependency (postMessage with game FEs only)
```

**Docs structure — INDEX-based navigation (mandatory):**

- `docs/requirements/` and `docs/specs/` are index-oriented. `docs/requirements/INDEX.md` lists all 17 requirement documents and the requirement-ID prefixes each one **defines**; every subdirectory under `docs/specs/` has an `INDEX.md` as its entry point.
- **Reading:** always start from the relevant `INDEX.md` when looking for information in `docs/`. Do not scan files directly — follow the index to the right file.
- **Writing:** when adding a new file or subdirectory anywhere under `docs/`, register it in the nearest `INDEX.md` (one-line entry with description) before considering the work done. When updating an existing file, check whether its `INDEX.md` entry needs to be updated too.
- Requirements documents link to related spec files via "Related API Specifications" sections; keep those links up to date when specs change.
- **Cite a requirement with the document that defines it**, never one that merely mentions it — `` `game-catalog.md` FR-GAME-009 ``. Fifty IDs collide across the corpus and twelve prefixes are defined in more than one place; `docs/requirements/INDEX.md` is the lookup. A wrong qualifier is worse than a bare ID.
- **Working files are deleted once spent, not archived.** A review's slice reports, a machine-extracted inventory, an executed plan — each stops being true the moment the corpus it describes changes, and a stale document that looks authoritative is worse than an absent one. Harvest anything still live into the corpus first, then delete. What survives a closed round is its INDEX and anything still cited.

**Submodule philosophy:** A submodule boundary is drawn where a component can be independently versioned, deployed, or replaced — not just where code is logically separate ([ADR-0012](docs/decisions/0012-repo-strategy-polyrepo-submodules.md)). Submodule refs in this repo are updated only after the submodule's build and tests pass.

## Architecture Principles

- **Game-agnostic platform core** — no game logic in platform services
- **Modular monolith** — the Platform Monolith is packaged by feature under `io.turnbase.platform`,
  and Spring Modulith fails the build when one feature reaches into another's internals
  ([ADR-0014](docs/decisions/0014-modular-monolith-spring-modulith.md))
- **Game modularity** — FE as standalone bundles (sandboxed iframes), BE as dynamically loaded JARs
- **Microservices** — independently deployable services, each in its own submodule
- **Security first** — sandboxed game code, origin validation, JWT auth, TLS everywhere
- **Horizontal scalability** — stateless services scale freely; stateful services use session affinity
- **Developer SDK** — well-defined contracts allow third parties to build compatible games

## Session Workflow

### Starting a Session

1. Read [STATUS.md](STATUS.md) — current state, last session summary, next priorities
2. Read this file — architecture, guidelines, constraints
3. Propose what to work on and confirm with the user

### During a Session

**Project skills** (in `.claude/skills/`) — these two carry the Phase 1 cadence:

- **`work-item`** — before writing any code for an `IMP-*` item. Claim it, read exactly its
  read-list, build to the *Done when* clause, and leave the register honest.
- **`spec-defect`** — the moment two documents disagree or leave you a decision. Stopping is the
  cheap option; silent reconciliation is what costs a day three milestones later.

**General:**

- Use `superpowers:brainstorming` before any creative, architectural, or design decision
- Use `superpowers:writing-plans` before multi-step implementation tasks
- Use `superpowers:systematic-debugging` when encountering bugs or unexpected behavior
- Use `superpowers:verification-before-completion` before claiming work is done
- Use `feature-dev` agents for focused implementation tasks
- **Re-check externally-gated blockers live before reporting `BLOCKED`.** A blocker like a
  human-provisioned secret (`TURNBASE_SDK_PAT`, `IMP-GATE-70`) can change state between sessions —
  or between context-compaction boundaries within one — with no signal to the agent other than the
  world having moved on. A prior session's note (or a compaction summary) that a secret/dependency/gate
  "does not exist yet" is a claim about the past, not the present. Before reporting a work item
  `BLOCKED` on something external, re-run the actual check (`gh secret list`, `gh api`, etc.) rather
  than restating what an earlier session or the conversation summary said.

### After any change under `docs/`

```bash
python3 scripts/check-corpus.py      # links · cites · sections · index · registry · items · counts · code-maps · code-refs
```

Nine structural checks, exit 1 on failure. **`cites` and `sections` are the two that have found real
defects** — mis-qualified requirement IDs and ranges naming IDs that do not exist. Run it before
committing documentation; it takes under a second and it is cheaper than the defect.

### After any change to `docs/specs/internal-grpc/gamehost.proto`

```bash
scripts/sync-proto.sh                 # refresh turnbase-common's committed copy
```

The proto is authoritative here and **committed** — not generated at build time — in
`turnbase-common/src/main/proto/turnbase/gamehost/v1/` (ADR-0012 as amended, `conventions.md` §5).
Editing the copy is a defect. `scripts/sync-proto.sh --check` fails on drift and runs in the
`pre-push` hook, because drift is otherwise silent: both repositories compile and the two services
disagree on the wire.

### Local fast-fail

```bash
git config core.hooksPath .githooks    # once per clone, this repo and each submodule
```

### Language servers

`.claude/settings.json` enables `typescript-lsp` (once per machine: `npm i -g typescript-language-server
typescript`); prefer the `LSP` tool over grep for references, implementations and call hierarchy in
`turnbase-frontend` and the games.

**`jdtls-lsp` is disabled**, tried 2026-11-07. It worked (on `PodIdentity` one call returned 32 exact
references in 9 files; diagnostics showed Jackson 3 deprecations the Maven build does not print), but on
first use it imports the Maven project into the **same `target/classes`** Maven builds into, and writes
`.project`/`.classpath`/`.settings/`: a `verify -Pintegration` running at the time lost classes mid-run
(`NoClassDefFoundError`, 34 failures). Re-enable it only with jdtls building elsewhere, for instance a
pom profile activated by `m2e.version` that sets `<directory>target-ide</directory>`.

### Branches: no PRs, and nothing outlives the session

**Do not open pull requests** ([ADR-0012](docs/decisions/0012-repo-strategy-polyrepo-submodules.md)
*Pull requests are suspended*, 2026-09-05). Branch freely — the `feat/`, `fix/`, `docs/`, `chore/`
names are unchanged — but **merge into `master` and delete the branch in the same session that
created it**, on the remote as well as locally. Prefer `--ff-only` so `master` stays linear. **Use `scripts/git-land.sh`** (`land`, `sweep`, `finish`) for the commit-merge-push-delete sequence — it is the allowlisted path, so headless runs do not strand half-landed work.

The reason is what happened without the rule: by 2026-09-05, the repositories held eight open PRs
and eleven abandoned branches, none of them awaiting anybody's review. CI runs on push to `master`,
so a direct merge is checked exactly as a PR was. If the work is not green when the session ends,
leave it unmerged and unpushed rather than parking it as a PR.

**Dependabot is frozen** in every repository for the same reason (`conventions.md` §6). The
`dependabot.yml` files stay — their `ignore` entries record why each pin is deliberate — but every
ecosystem carries `open-pull-requests-limit: 0`. Bump a dependency the ordinary way, on a branch.

### Ending a Session

1. Update STATUS.md — **replace** the "Last Session Summary" section (never append), update phase progress and next priorities
2. `python3 scripts/check-corpus.py` is clean
3. Verify all changes are committed, every branch created this session is merged and deleted, and no PR was opened
4. Update submodule refs in this repo only after the submodule's build and tests pass (an M11 item whose section says `**Build on exit:** may be red` is the one exception — ADR-0016 §4)

## End of Session Checklist

- [ ] All changes committed with meaningful messages
- [ ] Every branch created this session merged into `master` and deleted, locally and on the remote
- [ ] STATUS.md "Last Session Summary" replaced with current session content
- [ ] Next priority tasks clearly defined in STATUS.md
- [ ] Submodule refs updated only if build + tests pass

## Development Constraints

**MUST:**
- Java 21 for all backend services
- TypeScript for platform frontend
- Containerize all services with Docker
- Use WebSockets for real-time communication (no polling)

**SHOULD:**
- Google Java Style for Java — enforced by Spotless + `google-java-format` at the `validate` phase.
  **`./mvnw spotless:apply` before merging to `master`**, not after CI rejects it
- Prettier + ESLint for TypeScript/React
- Javadoc for all public SDK/API interfaces (Checkstyle enforces this in `turnbase-sdk`)
- Structured logging with correlation IDs
- >70% test coverage for critical paths — JaCoCo, over **merged** unit + integration exec data

**AVOID:**
- Game-specific logic in platform code
- Shared state between platform and game UIs (postMessage only)
- Trusting client-side validation without server-side verification
- Polling where WebSockets are appropriate
