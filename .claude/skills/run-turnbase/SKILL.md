---
name: run-turnbase
description: Start, run, drive, test or tear down the TurnBase local stack (docker compose on :8080) and play Tic-Tac-Toe through it with several independent players. Use for "run the platform", "start the stack", "play a game", "simulate two players", "check latency", "reproduce the MVP review".
---

# Run TurnBase locally

Paths are relative to the repository root. The stack is the compose project in
`turnbase-platform/deploy/compose/` (platform, game host, frontend, Postgres, Redis, MinIO, plus the
observability stack). Everything is reached through **http://turnbase.localhost:8080**. Management
endpoints are on loopback only: platform `8081`, game host `8082`. The driver is
`.claude/skills/run-turnbase/driver.mjs`.

## Prerequisites

Docker with compose v2, Node 22, and the game's `node_modules` (the driver borrows its `ws`):
`turnbase-game-tictactoe/node_modules/ws` must exist. The images
`turnbase/platform:dev`, `turnbase/game-host:dev`, `turnbase/frontend:dev` must be built; a
`target/seed-bundles/<gameId>.zip` (Tic-Tac-Toe and 7 Wonders Duel, from `scripts/seed-bundles.sh`) is what gets seeded.

## 1. Secrets (once)

`deploy/compose/.env` is git-ignored and nothing in the repo provides an example (review finding
MR-11). Dummy values are fine:

```bash
cat > turnbase-platform/deploy/compose/.env <<'ENV'
TURNBASE_DB_OWNER_PASSWORD=rev-owner-pw
TURNBASE_DB_APP_PASSWORD=rev-app-pw
TURNBASE_REDIS_PASSWORD=rev-redis-pw
MINIO_ROOT_USER=rev-minio
MINIO_ROOT_PASSWORD=rev-minio-pw1
TURNBASE_ADMIN_USERNAME=rev-admin
TURNBASE_ADMIN_PASSWORD=rev-admin-pw
GF_SECURITY_ADMIN_PASSWORD=rev-grafana
ENV
```

## 2. Start and stop

```bash
cd turnbase-platform/deploy/compose
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d --wait --wait-timeout 300
docker compose -f docker-compose.yml -f docker-compose.observability.yml down -v   # stop; -v wipes data
```

Cold `up --wait` takes about 30 s and ends with every container `Healthy`. Drop the observability file
for a smaller stack. The `local` profile seeds users `alice`, `bob`, `carol`, `dave` (password
`password`) and the Tic-Tac-Toe game.

## 3. Drive it (agent path)

```bash
node .claude/skills/run-turnbase/driver.mjs game    # full game, spectator and outsider checks
node .claude/skills/run-turnbase/driver.mjs drop    # mid-game socket drop, reconnect, resync
node .claude/skills/run-turnbase/driver.mjs leave   # mid-game explicit leave
```

Each run logs in four independent cookie jars (alice and bob play, carol spectates, dave never joins),
speaks real STOMP over `/ws`, and prints one JSON line. Observed output of `game`:

```
{"scenario":"game","warmOrColdStartMs":21,"marks":{"a":"X","b":"O","c":""},"spectatorAction":"ROLE_NOT_ELIGIBLE","moveLatencyMs":[22,14,20,17,21],"outsiderFrames":0}
```

It exits non-zero if a spectator action is not refused or the outsider receives any frame. The first
`warmOrColdStartMs` after a boot is the cold figure (6.5 s was seen in the review); run `game` twice to
get the warm one. The seeded e2e script is a second opinion:
`cd turnbase-game-tictactoe && node scripts/e2e-roundtrip.mjs` (alice/bob, ends `PASS`).

For the UI, the browser is `http://turnbase.localhost:8080`. Two players that do not share a session
need separate Playwright **browser contexts** (`browser.newContext()`), each with its own cookie jar.
The room views are not built yet (`IMP-M7-01…03`), so past registering, "Play as Guest" and the game
detail page there is nothing to click; use the driver for gameplay.

## Gotchas

- **Guest creation is limited to 5 per IP per hour** (`POST /api/auth/guest` → `429`,
  `Retry-After` about 700 s). That is why the driver logs in the seeded users instead of creating guests.
- **A STOMP client must send heartbeats.** The server negotiates `10000,10000` and closes a silent
  socket with `Session closed` (1002). The driver sends `\n` every 4 s.
- **Outsiders get silence, not an error.** Subscribing to a room or game topic you do not belong to
  yields no frames and no `ERROR`; test for absence of messages.
- **Timestamps:** compare client latencies with `Date.now()`. `performance.now()` has a per-page origin,
  so values from two Playwright pages cannot be subtracted.
- **The WebSocket needs an `Origin` header** matching the platform host; a foreign one is `403`.
- **A room left empty in the Lobby is not closed** (MR-02) and stays listed; leaving mid-game leaves the
  room `IN_PROGRESS` (MR-03). Both are tracked as `IMP-M7-05` and `IMP-M7-06`.

## Troubleshooting

- Platform container exits 1, `password authentication failed` → the Postgres volume was created with
  different passwords. `down -v` and start again.
- `FAIL: guest …: 429` → see the guest limit above.
