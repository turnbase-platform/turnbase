# Design Specifications

Implementation-level design decisions for the TurnBase platform. Each subdirectory covers one design domain and contains its own `INDEX.md` as an entry point.

Requirements documents live in `docs/requirements/` and link to the relevant specs here when an API or protocol design is involved.

## Subdirectories

| Directory | Topic |
|-----------|-------|
| [api-design/](api-design/INDEX.md) | REST conventions, error handling, pagination, file uploads, WebSocket, SSE, rate limiting, OpenAPI |
| [platform/](platform/INDEX.md) | Platform Monolith internals: room ownership and adoption, event versioning, grace-deadline enforcement, session teardown, reconciliation sweeps — and the complete relational data model (rooms, accounts, social, catalog, history, notifications) |
| [flows/](flows/INDEX.md) | **Start here to understand the system.** Eight end-to-end journeys traced across every component they touch, naming the actual endpoints, destinations, gRPC calls, tables and requirements at each step |
| [deployment/](deployment/INDEX.md) | Service topology, ports and startup order; Kubernetes and compose profiles; the consolidated configuration surface; schema migrations; secrets and key rotation |
| [internal-grpc/](internal-grpc/INDEX.md) | Internal service-to-service gRPC contracts (Orchestration Service ↔ Game Host) |
| [game-host/](game-host/INDEX.md) | Game Host & execution internals: Espresso topology, GDK Host + serialization boundary, isolation mechanisms, session/state model, crash recovery, effect delivery |
| [platform-frontend/](platform-frontend/INDEX.md) | The platform's own React shell: routing and auth tiers, the STOMP client, the game-iframe trust boundary and message relay, alert vs. notification rendering |
| [game-frontend/](game-frontend/INDEX.md) | Game FE serving origin, iframe sandbox & CSP, shell bootstrap document — the browser-side trust boundary between platform and game code |
| [gdk-api/](gdk-api/INDEX.md) | Public GDK API: `TurnBaseGame`, lifecycle hooks, contexts, effects, results, outcome, data model |
| [manifest/](manifest/INDEX.md) | Game manifest schema: `manifest.json` structure, JSON Schema artifact, validation rules, error model |

## Convention

Every subdirectory must have an `INDEX.md` that:
- Describes the scope of that design domain
- Lists all files with a one-line description each
- Summarises the key decisions made

### Citing a requirement

**Requirement IDs are numbered per document and collide across the corpus.** Fifty identifiers are
currently defined in more than one requirements document. `NFR-PERF-001` means nine different things;
`NFR-SEC-001` nine; `FR-SESS-003` is defined in both `platform-architecture.md` (Game Host in-memory
state) and `user-accounts.md` (login displaces the previous session) with no relationship between
them. `CON-001` through `CON-005` are defined in essentially every requirements document.

**Every cross-document citation must therefore carry a document qualifier:**

> ✅ `` `game-catalog.md` FR-GAME-009 `` · `platform-operations.md` FR-JOB-007 · `user-accounts.md` CON-004
>
> ❌ FR-GAME-009 · CON-004 · NFR-SEC-001

A bare ID is acceptable only for a requirement defined in the *same* document as the citation, or
where the ID prefix is unique corpus-wide (`FR-JOB-*`, `FR-HDISC-*`, `FR-OUTCOME-*`). When in doubt,
qualify — the cost is six characters and the failure mode is a reader following a citation to the
wrong requirement and concluding the spec is wrong.

This is a rule for new and edited text rather than a completed retrofit: the corpus predates it and
most existing bare citations resolve from context. What it prevents is the next collision being
introduced silently.
