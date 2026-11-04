# TurnBase — system overview

Where each part of the system lives. Per-service code maps (checked by
`python3 scripts/check-corpus.py code-maps`):

| Repository | Map |
|---|---|
| `turnbase-platform` | [turnbase-platform/ARCHITECTURE.md](turnbase-platform/ARCHITECTURE.md) — the Platform Monolith |
| `turnbase-game-host` | [turnbase-game-host/ARCHITECTURE.md](turnbase-game-host/ARCHITECTURE.md) — Espresso game execution |
| `turnbase-frontend` | [turnbase-frontend/ARCHITECTURE.md](turnbase-frontend/ARCHITECTURE.md) — the SPA |
| `turnbase-sdk` | [turnbase-sdk/ARCHITECTURE.md](turnbase-sdk/ARCHITECTURE.md) — the public GDK |

`turnbase-common` holds the gRPC stubs generated from `docs/specs/internal-grpc/gamehost.proto`; the
games `turnbase-game-tictactoe` and `turnbase-game-7wonders-duel` are consumers of the SDK.

## How the pieces talk

- Browser ↔ platform: REST under `/api` and STOMP over WebSocket; the cookie session authenticates both.
- Platform ↔ Game Host: gRPC (`rpc CreateSession`, `rpc ProcessInput`, `rpc Resync`, `rpc TerminateSession`; the host
  calls back `rpc Register` and `rpc Heartbeat`). Redis holds host leases and room ownership; PostgreSQL holds
  durable state; an S3-compatible store holds game bundles.
- Game frontends ↔ platform frontend: `postMessage` only, inside sandboxed iframes.

## Journeys

The eight traces in [docs/specs/flows/](docs/specs/flows/INDEX.md) follow a user action across every
component. Each service map above traces five of them through its own packages and classes: sign-in,
room create and join, a move, game upload, and Game Host failure.
