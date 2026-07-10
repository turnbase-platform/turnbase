# Design Specifications

Implementation-level design decisions for the TurnBase platform. Each subdirectory covers one design domain and contains its own `INDEX.md` as an entry point.

Requirements documents live in `docs/requirements/` and link to the relevant specs here when an API or protocol design is involved.

## Subdirectories

| Directory | Topic |
|-----------|-------|
| [api-design/](api-design/INDEX.md) | REST conventions, error handling, pagination, file uploads, WebSocket, SSE, rate limiting, OpenAPI |
| [internal-grpc/](internal-grpc/INDEX.md) | Internal service-to-service gRPC contracts (Orchestration Service ↔ Game Host) |
| [game-host/](game-host/INDEX.md) | Game Host & execution internals: Espresso topology, GDK Host + serialization boundary, isolation mechanisms, session/state model, crash recovery, effect delivery |
| [gdk-api/](gdk-api/INDEX.md) | Public GDK API: `TurnBaseGame`, lifecycle hooks, contexts, effects, results, outcome, data model |
| [manifest/](manifest/INDEX.md) | Game manifest schema: `manifest.json` structure, JSON Schema artifact, validation rules, error model |

## Convention

Every subdirectory must have an `INDEX.md` that:
- Describes the scope of that design domain
- Lists all files with a one-line description each
- Summarises the key decisions made
