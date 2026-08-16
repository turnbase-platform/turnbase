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

**Phase 1 — Implementation** (starting). Phase 0 is complete and has been audited for
implementation-readiness.

Check [STATUS.md](STATUS.md) at the start of each session for current state, last session summary,
and next priorities.

**Before writing any code**, read [docs/implementation/INDEX.md](docs/implementation/INDEX.md) — the
work-item registry. The 2026-08-16 readiness audit's **23 blockers are all closed**
([register](docs/reviews/2026-08-16-implementation-readiness/INDEX.md)), so no work item is gated;
an item's status is whatever its own dependencies imply. If a new specification defect is found while
implementing, the fix belongs in the specification, not in code.

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Platform Monolith | Java 21, Spring Boot 3.5+ | |
| Game Host service | Java 21, GraalVM CE for JDK 21 + Truffle | Host JVM is Java 21; game code runs in Espresso (Java 21 guest). No CE build exists for JDK 23; the earlier "CE 23" label was the deprecated GraalVM product-version scheme. |
| Game backends (SDK) | Java 21 (max) | Executed in Espresso; must not use Java 22+ APIs |
| Frontend (platform) | React 19, TypeScript | Clean, responsive, modern |
| Game UIs | Any JS-compilable language | Sandboxed iframes |
| Infrastructure | Kubernetes | Auto-scaling by traffic and active games |
| Build (backend) | Maven | |
| Build (frontend) | Vite | |
| Metrics | Micrometer → Prometheus → Grafana | Spring Boot native |
| Logs | SLF4J/Logback (JSON) → Loki → Grafana | Structured, stdout in K8s |
| Traces | OpenTelemetry → Tempo → Grafana | W3C trace context propagation |

## Repository Structure

TurnBase lives under the **[turnbase-platform](https://github.com/turnbase-platform)** GitHub organisation. Each independently deployable component has its own repository with its own GitHub Actions workflows, versioning, and deployment pipeline. All component repos are registered as git submodules here.

| Repository | Description | Published artifact |
|------------|-------------|-------------------|
| [`turnbase`](https://github.com/turnbase-platform/turnbase) | This repo — landing page, docs, specs, submodule refs | — |
| [`turnbase-common`](https://github.com/turnbase-platform/turnbase-common) | Internal shared library: gRPC stubs, internal models | `io.turnbase:turnbase-grpc` (Maven) |
| [`turnbase-sdk`](https://github.com/turnbase-platform/turnbase-sdk) | Public GDK: `TurnBaseGame` interface, effect/input types, TS types | `io.turnbase:turnbase-sdk` (Maven) + npm package |
| [`turnbase-platform`](https://github.com/turnbase-platform/turnbase-platform) | Platform Monolith (Spring Boot 3.5+) | Docker image |
| [`turnbase-game-host`](https://github.com/turnbase-platform/turnbase-game-host) | Game Host (GraalVM CE for JDK 21 + Truffle) | Docker image |
| [`turnbase-frontend`](https://github.com/turnbase-platform/turnbase-frontend) | Platform frontend (React 19, TypeScript) | Docker image / static assets |

```
turnbase/                    # This repo (landing + docs)
├── CLAUDE.md
├── STATUS.md
├── docs/
│   ├── requirements/        # What the system must do (per-feature requirement documents)
│   └── specs/               # How it is designed (implementation-level design specs)
│       ├── INDEX.md         # Entry point — lists all spec subdirectories
│       ├── api-design/      # REST, WebSocket, SSE, error handling, uploads, rate limiting
│       └── internal-grpc/   # Orchestration ↔ Game Host gRPC contract
│   ├── decisions/           # ADRs — one numbered file per architectural decision
│   ├── implementation/      # Implementation registry — work items, gates, done-when clauses
│   └── reviews/             # Dated review rounds; each has its own INDEX.md
├── turnbase-common/         # git submodule
├── turnbase-sdk/            # git submodule
├── turnbase-platform/       # git submodule
├── turnbase-game-host/      # git submodule
└── turnbase-frontend/       # git submodule
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

- `docs/requirements/` and `docs/specs/` are index-oriented. Every subdirectory under `docs/specs/` has an `INDEX.md` as its entry point.
- **Reading:** always start from the relevant `INDEX.md` when looking for information in `docs/`. Do not scan files directly — follow the index to the right file.
- **Writing:** when adding a new file or subdirectory anywhere under `docs/`, register it in the nearest `INDEX.md` (one-line entry with description) before considering the work done. When updating an existing file, check whether its `INDEX.md` entry needs to be updated too.
- Requirements documents link to related spec files via "Related API Specifications" sections; keep those links up to date when specs change.

**Submodule philosophy:** A submodule boundary is drawn where a component can be independently versioned, deployed, or replaced — not just where code is logically separate. Submodule refs in this repo are updated only after the submodule's build and tests pass.

## Architecture Principles

- **Game-agnostic platform core** — no game logic in platform services
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

- Use `superpowers:brainstorming` before any creative, architectural, or design decision
- Use `superpowers:writing-plans` before multi-step implementation tasks
- Use `superpowers:systematic-debugging` when encountering bugs or unexpected behavior
- Use `superpowers:verification-before-completion` before claiming work is done
- Use `feature-dev` agents for focused implementation tasks

### Ending a Session

1. Update STATUS.md — **replace** the "Last Session Summary" section (never append), update phase progress and next priorities
2. Verify all changes are committed
3. Update submodule refs in this repo only after the submodule's build and tests pass

## End of Session Checklist

- [ ] All changes committed with meaningful messages
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
- Google Java Style for Java
- Prettier + ESLint for TypeScript/React
- Javadoc for all public SDK/API interfaces
- Structured logging with correlation IDs
- >70% test coverage for critical paths

**AVOID:**
- Game-specific logic in platform code
- Shared state between platform and game UIs (postMessage only)
- Trusting client-side validation without server-side verification
- Polling where WebSockets are appropriate
