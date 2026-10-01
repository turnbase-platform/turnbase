# MVP Implementation Review — 2026-10-01

A black-box run of the local stack, driven through Playwright, to answer one question after the first
batch of work items reached `DONE`:

> Does the platform actually work end to end, and is every feature the registry calls done really
> usable?

## Verdict

> **The backend and Game Host are in good shape; the product is not yet playable in a browser.**
> A full Tic-Tac-Toe game — registration, room, join, ready, start, moves, win, history, statistics —
> works correctly over REST and STOMP, with latency in the low tens of milliseconds. **But the
> frontend has no room views** (MR-01): after registering, or after pressing *Create room*, a user lands
> on a "This view is not available yet." placeholder. Two items marked `DONE` (`IMP-M6-04`,
> `IMP-M6-05`) satisfy only their narrow *Done when* clauses, not the `VW-*` requirements in their
> *Satisfies* lines. **MVP status is therefore reached for the API and the services, not for a player.**
>
> Two behavioural defects in the backend (MR-02 ghost rooms, MR-03 mid-game leave) and one in the game
> (MR-04) should be fixed before the frontend views are built, since those views will surface them.

## How it was run

- Stack: `docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d --wait`
  (platform, game-host, frontend, Postgres, Redis, MinIO, Prometheus, Grafana, Loki, Tempo, Promtail,
  Alertmanager). Cold `up --wait` ≈ 33 s. Image heads: platform `bccb1cd`, host `2c093b9`,
  frontend `24d1999`, tictactoe `c31f536`.
- A hand-written, git-ignored `deploy/compose/.env` was needed, and stale volumes from an earlier
  password set had to be wiped (`down -v`). Environment, not product — but there is no documented
  "first run" path that produces a working `.env` (see MR-11).
- **Two (here four) isolated players:** yes — one Playwright browser, several `browser.newContext()`
  contexts. Each has its own cookie jar and storage; confirmed by distinct `turnbase_session`
  cookies and distinct user IDs. Roles: A = registered `reviewer_a`, B = guest, C = guest spectator,
  D = guest outsider (never joined).
- The room views do not exist (MR-01), so gameplay was driven by an in-page STOMP client over the real
  `/ws` endpoint, using the cookie session of each context and the protocol of
  `turnbase-game-tictactoe/scripts/e2e-roundtrip.mjs`. Registration, guest login, catalog and game
  detail were driven through the real UI.
- Latency figures use `Date.now()` on a shared clock (browser contexts share a process).

## What was verified working

| Area | Result |
|---|---|
| Catalog | Seeded Tic-Tac-Toe listed with OFFICIAL badge; detail page renders; `completedSessionCount` increments |
| Auth | Register and guest login via UI; cookie `turnbase_session` is HttpOnly, SameSite=Strict; contexts isolated |
| Room flow | create → join (201) → `TOGGLE_READY` → `READINESS_CHANGED` → `START_GAME` → `GAME_STARTED` with a `gameFrontendUrl` on the games origin |
| Game rules | X/O assigned; out-of-turn move and cell 99 rejected to the sender only; full game ends in `GAME_OVER` on both clients; room returns to LOBBY (`GAME_ENDED`, `readinessReset`) |
| History / stats | Registered player: "Victory", `totalPlayed` 1. Guest history empty — correct per `game-history.md` FR-HIST-003 |
| Spectator | Joins with `{role:'SPECTATOR'}`, receives `GAME_SYNC` (role `spectator`) and every move; `SUBMIT_ACTION` → `ROLE_NOT_ELIGIBLE` |
| Authorization | Non-host `START_GAME` → `NOT_HOST`; a 3rd player joining a full room → 422; an outsider subscribing to `/topic/room.{id}` and `/topic/game.{sid}` receives nothing, and an outsider's `SUBMIT_ACTION` has no effect |
| Reconnection | Mid-game socket drop → `PLAYER_DISCONNECTED` (`gracePeriodSeconds` 60); reconnect + `REQUEST_GAME_SYNC` returns the exact board; `PLAYER_RECONNECTED` broadcast |
| Heartbeat | Heartbeating sockets survive 25 s idle; a non-heartbeating client is closed (expected) |
| Origin / CSRF | Foreign `Origin` on a mutating REST call → 400; on the WS upgrade → 403; on `POST /api/auth/guest` → 403 |
| Surface | Shell sends a strict CSP (`default-src 'self'`, `frame-src http://*.games.localhost:8080`, `frame-ancestors 'none'`); `/actuator/*` and `/api/admin/*` are not exposed on :8080 (SPA fallback / 401); management on 8081 |
| Observability | Prometheus: `platform` and `gamehost` targets up, custom `turnbase_*` metrics present; Grafana: "JVM and Database", "Platform Overview"; Loki receives structured JSON logs with `service`/`level` labels; Tempo holds traces for both services |

## Performance (local, one machine, 2 players + 1 spectator)

| Measurement | Result |
|---|---|
| Move → `GAME_EVENT` at all three clients | 13–16 ms |
| `REQUEST_GAME_SYNC` round trip | 12–19 ms |
| `START_GAME` → `GAME_STARTED`, **warm** | 24 ms |
| `START_GAME` → `GAME_STARTED`, **cold** (first session after boot) | **6 465 ms** (MR-05) |
| Resting memory | platform 849 MiB, game host 881 MiB, frontend 17 MiB |
| Resting CPU | all < 3 % |

No concurrent-load test was run; the figures above are single-game latency only.

## Findings

Severity: **High** blocks the MVP's purpose; **Medium** is a behavioural defect or a real risk;
**Low** is polish or documentation.

### MR-01 — Room views are placeholders; a player cannot play in the browser — **High**

`turnbase-frontend/src/app/routes.tsx:45-47` mounts `/rooms`, `/rooms/join/:code` and `/rooms/:id` as
`later(...)` placeholders. `GameFrame` and the postMessage relay exist in `features/game` but no page
mounts them; `features/rooms` holds the socket, reducer and hook but no pages. Registration lands on
`/rooms` (placeholder), *Create room* lands on `/rooms/{id}` (placeholder).

`IMP-M6-04` records this itself ("not built by this item … tracked in `STATUS.md`") but the registry
status is `DONE`, so nothing in `registry.md` owns the views: `VW-ROOMS`, `VW-JOIN`, `VW-RLOBBY`,
`VW-RGAME`, `VW-RRESULT` (`platform-views.md`) and `in-room-chat.md` FR-CHAN / FR-SWITCH are
unsatisfied with no open work item. `IMP-M6-05`'s iframe host is likewise unreachable.

**Recommendation:** add work items for the five views (and chat) and mark the *Satisfies* gap in the
registry; consider reopening `IMP-M6-04`/`05`. Until then the MVP claim is API-only.

### MR-02 — Rooms abandoned in Lobby are never closed — **Medium**

When the host, as the last human, loses the socket in LOBBY — or creates a second room while in a
first — the first room stays `LOBBY` with `playerCount` 0, `hostUserId` pointing at the departed user,
and is listed by `GET /api/rooms` with `canJoin: true`. `game-rooms.md` FR-XFER-002 ("closes
immediately and permanently when the host leaves and no humans remain") and the Lobby-disconnect rule
FR-DC-002 (immediate leave) are not met. Only an explicit `DELETE …/participants/me` closes the room;
the 30-minute idle sweep (FR-LIFE-007 / FR-JOB-007d) is the only safety net. Three such rooms existed
during the run. Public listing therefore fills with unjoinable-in-practice rooms.

### MR-03 — A player leaving mid-game neither forfeits nor ends the game — **Medium**

After `DELETE /api/rooms/{id}/participants/me` by player B mid-game, A received `PLAYER_LEFT` only. The
room stayed `IN_PROGRESS` with `playerCount` 1, no `GAME_OVER`/`GAME_ENDED` followed, and the
session stays open for the remaining player. `per-game-statistics.md` FR-STATS-001 counts a forfeit as a
completed session and `reconnection-flow.md` FR-EXPIRY-002 sends a "player lost" event to the engine,
so the platform has a path for this; an explicit leave does not appear to take it. The remaining player
is stuck in a game that cannot finish. (Grace-period expiry for a dropped socket was **not** observed —
the 60 s window was not run to completion; see *Not covered*.)

### MR-04 — Tic-Tac-Toe accepts a move with no `cell` as cell 0 — **Low**

`Move(int cell)` coerces a missing field to `0` (`Move.java`), and `TicTacToeGame.java:61` only
rejects out-of-range or occupied cells (:68). `SUBMIT_ACTION` with `{}` is a legal move on cell 0.
Reference game, so third-party authors will copy it: use `Integer` and reject `null`.

### MR-05 — Cold game start takes 6.5 s — **Medium**

First `START_GAME` after boot took 6 465 ms (warm: 24 ms), consistent with Espresso/Truffle context
warm-up. The 3 s / 5 s startup figures are deferred post-MVP (ADR-0005), but the first player on a fresh
pod sees the delay and the host does not pre-warm. Consider a synthetic warm-up game on startup and
before readiness (`/actuator/health/readiness`).

### MR-06 — Sparse application logging — **Low**

Loki carries structured JSON with `trace_id`, but the only application-level INFO line seen across
register, room create, join, start, leave, disconnect and game end was `Session created
sessionId=… instanceId=…` (`GameSessionService`). Everything else is framework noise. Operations
reading Loki cannot reconstruct a room's story (who joined, who left, why a room closed). Add INFO lines
for the room and auth lifecycle with `roomId`/`userId` fields.

### MR-07 — Console 401 on every anonymous page load — **Low**

`GET /api/auth/session` returns 401 for an anonymous visitor and the browser logs it as a console
error on every page load. Return 200 with `{authenticated:false}` or handle silently. Password inputs
also lack `autocomplete` attributes (Chrome DevTools verbose).

### MR-08 — Startup WARN: more than one `TaskScheduler` bean — **Low**

The platform logs it on every boot. Harmless today; name the intended scheduler (or mark one `@Primary`)
before something injects the wrong one.

### MR-09 — Games origin returns 404 problem+json at `/` — **Low**

`http://{gameId}.games.localhost:8080/` returns `404 application/problem+json` rather than the game
frontend index; the shell's own `gameFrontendUrl` path was not exercised in a browser (no room view to
mount the iframe; MR-01). Confirm the URL the platform hands out resolves, once the iframe host is
mounted.

### MR-10 — `Secure` cookie flag set on plain-HTTP localhost — **Low**

`turnbase_session` carries `Secure` over `http://turnbase.localhost:8080`. Chrome treats `localhost`
as secure so the run worked; other browsers (Safari, older Firefox) will drop the cookie. Make the flag
profile-driven for the local stack.

### MR-11 — No documented first-run path for the local stack — **Low**

`deploy/compose/` needs eight secrets in a `.env` that exists nowhere in the repository's docs as a
working example, and a `down -v` after any password change. A `.env.example` plus a
`make up` that fails fast with the list of missing variables would remove the trial and error.

## Not covered

- Game frontend loaded inside the sandboxed iframe, `postMessage` relay, and CSP on the games origin
  (blocked by MR-01 / MR-09).
- Grace-period **expiry** (60 s) and the resulting engine "player lost" decision.
- STOMP flood / `RATE_LIMIT_EXCEEDED`.
- Friends, notifications bell, profile and settings pages; 400 px responsive layout; accessibility audit.
- Concurrent-game load and soak testing; Grafana dashboard contents beyond their existence.
- Tempo trace continuity from the platform into Game Host for a single action (traces for both services
  exist; the cross-service span link was not inspected).

## Run-hygiene notes

- `turnbase-platform/deploy/compose/.env` was created for this run (git-ignored, dummy secrets) and the
  compose volumes were wiped once. The stack is still running.
