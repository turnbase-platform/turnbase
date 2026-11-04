# Archive — M7 MVP review remediation

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim by `IMP-M20-01`. Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M7-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M7-01 | Room list and join views | frontend | M6-04 | DONE |
| IMP-M7-02 | Room lobby view | frontend | M7-01 | DONE |
| IMP-M7-03 | In-game and results views, game iframe mount | frontend | M7-02, M6-05 | DONE |
| IMP-M7-04 | Room chat panel | frontend | M7-02 | DONE |
| IMP-M7-05 | Close rooms abandoned in the Lobby | platform | M2-08 | DONE |
| IMP-M7-06 | Leaving mid-game reaches the engine | platform | M3-09 | DONE |
| IMP-M7-07 | Populate `reservedSlot` on the rooms list | platform | M2-07 | DONE |
| IMP-M7-08 | Tic-Tac-Toe rejects a malformed action | game | M3-10 | DONE |
| IMP-M7-09 | Game Host warm-up before readiness | game-host | M3-10 | DONE |
| IMP-M7-10 | Lifecycle logging for rooms, auth and sessions | platform, game-host | M3-10 | DONE |
| IMP-M7-11 | Anonymous session probe, cookie flag, scheduler bean | platform, frontend | M6-02 | DONE |
| IMP-M7-12 | Local stack first-run path | platform | M0-05 | DONE |
| IMP-M7-13 | MVP browser acceptance suite | frontend | M7-03, M7-05, M7-06 | DONE |

---

## M7 — MVP review remediation

Opened 2026-10-01 from the [MVP implementation review](../../reviews/2026-10-01-mvp-implementation-review/INDEX.md).
Each item names the finding it closes (`MR-nn`). The review's evidence is a black-box run: the
backend and Game Host passed, the frontend's room views did not exist.

---

### IMP-M7-01 — Room list and join views

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M6-04 · **Closes:** MR-01 (part)

**Read first:**
- `docs/requirements/platform-views.md` VW-ROOMS-001…005, VW-JOIN-001…003
- `docs/specs/platform-frontend/shell-architecture.md` §8
- `docs/specs/api-design/room-rest-api.md` — `GET /api/rooms`, join, `reservedSlot`
- `docs/specs/platform-frontend/design-system.md`

**Satisfies:** `platform-views.md` VW-ROOMS-001…004, VW-JOIN-001…003 (VW-ROOMS-005 needs `IMP-M7-07`)

**Done when:** `/rooms` and `/rooms/join/:code` replace their `later(...)` placeholders in
`routes.tsx`; the list renders `GET /api/rooms` with filter, sort and refresh, and Join calls
`joinRoom` (which already retries a `503`); the join page shows the Player/Spectator prompt only when
both roles are open and an error message for an invalid code, a vanished room or no available role;
a successful join navigates to `/rooms/:id`; registration lands on a working `/rooms`.

---

### IMP-M7-02 — Room lobby view

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M7-01 · **Closes:** MR-01 (part)

**Read first:**
- `docs/requirements/platform-views.md` VW-RLOBBY-001…007, VW-RLOBBY-009…017
- `docs/specs/platform-frontend/shell-architecture.md` §4, §8 (one component, three states)
- `docs/specs/api-design/room-websocket.md` in full
- `docs/requirements/reconnection-flow.md` FR-REJOIN-001…008

**Satisfies:** `platform-views.md` VW-RLOBBY-001…007, VW-RLOBBY-009…017; `reconnection-flow.md`
FR-REJOIN-001…008 (the global reconnection card)

**Done when:** `/rooms/:id` mounts the room component on `useRoomConnection`; the lobby shows the
player list with readiness, the read-only parameters panel, Toggle Readiness for non-host players,
Start for the host only (enabled by the platform's own readiness rule, not recomputed), invite code,
and the host's Kick and Transfer Host; a refresh of the page rejoins the room from a `ROOM_STATE`
snapshot; a dropped socket shows the reconnection card and resyncs without a stale-delta replay.

---

### IMP-M7-03 — In-game and results views, game iframe mount

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M7-02, IMP-M6-05 · **Closes:** MR-01 (part), MR-09

**Read first:**
- `docs/requirements/platform-views.md` VW-RGAME-001…005, VW-RRESULT-001…005
- `docs/specs/game-frontend/game-asset-serving.md` §6, §7
- `docs/specs/platform-frontend/shell-architecture.md` §5
- `docs/specs/api-design/websocket.md` § *Platform-shell relay contract*

**Satisfies:** `platform-views.md` VW-RGAME-001…005, VW-RRESULT-001…005

**Done when:** on `GAME_STARTED` the room view mounts the existing `GameFrame` at the payload's
`gameFrontendUrl`, and the shell relays the game stream both ways with origin validation; the game
frontend actually loads from `http://{gameId}.games.<host>` (the review saw `404 problem+json` at `/`,
MR-09 — either the path the platform hands out resolves or the asset route is fixed); the participant
status panel, Leave, and the host's Kick and Transfer Host are present; on `GAME_OVER` the results
view keeps the iframe and offers Return to Lobby and Leave; two browser contexts can play Tic-Tac-Toe
to a win through the UI alone.

---

### IMP-M7-04 — Room chat panel

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M7-02 · **Closes:** MR-01 (part)

**Read first:**
- `docs/requirements/in-room-chat.md` FR-CHAN-001…004, FR-SWITCH-001…002
- `docs/requirements/platform-views.md` VW-RGAME-006…008
- `docs/specs/api-design/room-chat-websocket.md`

**Satisfies:** `in-room-chat.md` FR-CHAN-001…004, FR-SWITCH-001…002; `platform-views.md` VW-RGAME-006…008

**Done when:** players see a unified room log and a team tab only when the game declares teams; the
write-channel switcher is shown only to players with both channels; chat frames carry `version: null`
and never touch the room's `localVersion` (IR-08); spectators have no chat panel and a spectator's
send is refused by the server, not merely hidden; the chat log is client-held only (FR-CHAN-003).

---

### IMP-M7-05 — Close rooms abandoned in the Lobby

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-08 · **Closes:** MR-02

**Read first:**
- `docs/requirements/game-rooms.md` FR-XFER-001…003, FR-LIFE-004, FR-LIFE-007
- `docs/specs/platform/room-lifecycle.md`
- `docs/specs/flows/05-owner-loss-and-adoption.md`, `docs/specs/flows/07-room-closure.md`
- `docs/reviews/2026-10-01-mvp-implementation-review/INDEX.md` MR-02

**Satisfies:** `game-rooms.md` FR-XFER-002, FR-XFER-003

**Done when:** a Lobby room whose last human loses their socket, or leaves implicitly by creating or
joining another room, is closed at once and disappears from `GET /api/rooms` and from
`GET /api/rooms/{id}` (404), exactly as an explicit `DELETE …/participants/me` already does; when other
humans remain, host transfer happens instead (FR-XFER-001); an integration test reproduces the
review's three paths (socket loss, implicit release, explicit leave) and asserts no listed room has
`playerCount` 0. The 30-minute idle sweep is unchanged and remains the backstop.


**Follow-up (2026-10-03):** the review found rooms emptied by concurrent leaves, or around a game end, still listed — `IMP-M8-04`.
---

### IMP-M7-06 — Leaving mid-game reaches the engine

**Repo:** `turnbase-platform` · **Depends on:** IMP-M3-09 · **Closes:** MR-03

**Read first:**
- `docs/requirements/game-rooms.md` FR-LIFE-004
- `docs/requirements/reconnection-flow.md` FR-EXPIRY-002 and § *Game engine response set*
- `docs/requirements/per-game-statistics.md` FR-STATS-001
- `docs/specs/flows/04-disconnect-and-return.md`, `docs/specs/flows/06-game-end-and-rematch.md`
- `docs/specs/gdk-api/backend-gdk-api.md` — the "player lost" event and the response set
- `docs/reviews/2026-10-01-mvp-implementation-review/INDEX.md` MR-03

**Satisfies:** `reconnection-flow.md` FR-EXPIRY-002; `per-game-statistics.md` FR-STATS-001 (forfeit)

**Done when:** an explicit `DELETE /api/rooms/{id}/participants/me` by a player during `IN_PROGRESS`
delivers the same "player lost" event to the engine that grace-period expiry does; for Tic-Tac-Toe the
opponent receives `GAME_OVER` (forfeit) and the room returns to LOBBY with a `GAME_ENDED`; a forfeit
session is counted in statistics and written to history; a spectator leaving changes nothing in the
session. If the requirements do not say what an explicit leave must do, stop and open a gate with
`spec-defect` — do not choose. An integration test reproduces the review's run (leave with a socket
open, game not stuck).


**Follow-up (2026-10-03):** the clause "a forfeit session is … written to history" was not met: the history service rejects the outcome (`playerResults names a non-participant`) — `IMP-M8-03`.
---

### IMP-M7-07 — Populate `reservedSlot` on the rooms list

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-07 · **Closes:** the deferral recorded in `IMP-M6-04`

**Read first:**
- `docs/specs/api-design/room-rest-api.md` §3 (the `reservedSlot` field)
- `docs/requirements/reconnection-flow.md` FR-REJOIN-002
- `docs/requirements/platform-views.md` VW-ROOMS-005

**Satisfies:** `platform-views.md` VW-ROOMS-005 (backend half), `reconnection-flow.md` FR-REJOIN-002

**Done when:** `GET /api/rooms` returns `reservedSlot` populated for a caller who holds a live
grace-period reservation and `null` otherwise, unaffected by filters; `IMP-M7-01`'s list shows the
pinned reconnection card from it.

---

### IMP-M7-08 — Tic-Tac-Toe rejects a malformed action

**Repo:** `turnbase-game-tictactoe` · **Depends on:** IMP-M3-10 · **Closes:** MR-04

**Read first:**
- `turnbase-game-tictactoe/src/main/java/io/turnbase/games/tictactoe/Move.java`, `TicTacToeGame.java`
- `docs/specs/gdk-api/backend-gdk-api.md` — the action-rejection contract

**Done when:** `Move.cell` is nullable (`Integer`) and an action with no `cell`, a non-integer `cell`
or an unparsable payload yields a rejection (`That cell is not available.` or a dedicated message)
to the sender only, with no state change and no turn consumed; a unit test covers `{}`, `null`,
`"x"` and a valid move; the game remains a model for third-party authors.

---

### IMP-M7-09 — Game Host warm-up before readiness

**Repo:** `turnbase-game-host` · **Depends on:** IMP-M3-10 · **Closes:** MR-05

**Read first:**
- `docs/specs/game-host/game-host-internals.md`
- `docs/decisions/0005-game-sandbox-espresso-spike.md` (startup NFRs deferred post-MVP) — what is and is not owed
- `docs/specs/deployment/observability.md`

**Done when:** before the Game Host reports readiness it runs a synthetic session against an
embedded trivial game so the first real `START_GAME` no longer pays the Truffle warm-up; the measured
cold `START_GAME → GAME_STARTED` on a freshly booted stack is recorded in the item's section and is
within the same order as warm (target < 1 s; if not reachable, record the figure and the reason);
the synthetic session never appears in history, statistics or the active-session gauge.

**Measured (session 123, compose stack, GraalVM CE 21.0.2):** cold `START_GAME → GAME_STARTED` fell from
6 465 ms (review, MR-05) to **4 163 ms**; warm is 39 ms. The < 1 s target is **not reached**: the remaining
cost is the per-context Espresso boot (a guest JVM per context, ~13 s on the unit-test classpath), which a
throwaway context cannot pre-pay and a shared `Engine` did not reduce. Closing it needs a pre-booted pool of
game contexts, which is a post-MVP design (ADR-0005 defers the startup NFRs). The warm-up context is outside
`GameContextManager`/Redis, so it is invisible to history, statistics and the `active_sessions` signal.

---

### IMP-M7-10 — Lifecycle logging for rooms, auth and sessions

**Repo:** `turnbase-platform`, `turnbase-game-host` · **Depends on:** IMP-M3-10 · **Closes:** MR-06

**Read first:**
- `docs/specs/deployment/observability.md` (logging section)
- `docs/specs/api-design/websocket.md` (connect, disconnect)

**Done when:** structured INFO lines with `roomId`, `userId` (and `sessionId` where one exists) are
emitted for: registration, login and guest creation, room create / join / leave / close (with the
close reason), game start and end (with outcome), socket connect / disconnect and the grace-period
open / expiry / reconnect; the Game Host logs context create / release and `Deregister`; no credential,
session token or chat text is logged; a reviewer can reconstruct the review's game from Loki alone.

---

### IMP-M7-11 — Anonymous session probe, cookie flag, scheduler bean

**Repo:** `turnbase-platform`, `turnbase-frontend` · **Depends on:** IMP-M6-02 · **Closes:** MR-07, MR-08, MR-10

**Read first:**
- `docs/specs/api-design/rest-conventions.md`, `docs/specs/platform/` auth and session specs
- `docs/specs/deployment/secrets-and-configuration.md`
- `docs/reviews/2026-10-01-mvp-implementation-review/INDEX.md` MR-07, MR-08, MR-10

**Done when:** an anonymous load of any page produces no console error (the session probe answers
without a 401, or the 401 is the documented contract and the client handles it silently — record
which in the spec); `turnbase_session` is `Secure` only when the configuration says the deployment is
HTTPS, so the local HTTP stack works in browsers that do not treat `localhost` as secure;
the "more than one TaskScheduler bean" WARN no longer appears at start-up (the intended scheduler is
named or `@Primary`); password inputs carry `autocomplete` attributes.

---

### IMP-M7-12 — Local stack first-run path

**Repo:** `turnbase-platform` · **Depends on:** IMP-M0-05 · **Closes:** MR-11

**Read first:**
- `docs/specs/deployment/local-environment.md`, `docs/specs/deployment/secrets-and-configuration.md`
- `turnbase-platform/deploy/compose/`

**Done when:** `deploy/compose/.env.example` lists every required variable with a dummy value; a `make`
target (or a documented command) copies it when no `.env` exists and fails fast naming any missing
variable; `local-environment.md` states that a changed database password needs `down -v`; a cold clone
reaches a healthy stack and a listed Tic-Tac-Toe following only that document.

**Closed:** IMP-GATE-94 (opened and closed 2026-10-03, session 126) — `secrets-and-configuration.md` §2 said `.env.example` holds no values while this clause requires dummy ones; §2 now says every required variable carries a labelled local-only dummy, and that `make env`/`check-env` exist.

---

### IMP-M7-13 — MVP browser acceptance suite

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M7-03, IMP-M7-05, IMP-M7-06

**Read first:**
- `docs/reviews/2026-10-01-mvp-implementation-review/INDEX.md` — the scenarios run by hand
- `turnbase-game-tictactoe/scripts/e2e-roundtrip.mjs`
- `docs/implementation/conventions.md` (test layout)

**Done when:** a Playwright suite runs against the compose stack with **separate browser contexts**
for each player and covers, through the UI where a view exists: register and guest login; create,
join, ready, start; a full Tic-Tac-Toe game to a win; history and statistics for the registered
player; spectator can watch and cannot act; an outsider receives nothing from the room and game
topics; a mid-game socket drop and resume; a leave mid-game ending in a forfeit; a Lobby abandoned
by its host disappearing from the list; a foreign `Origin` refused on REST and on the WebSocket upgrade.
The review's *Not covered* list (grace-period expiry, rate-limit flood, friends / notifications /
profile pages, 400 px layout, concurrent games) is either covered here or recorded as an explicit
follow-up. The suite is wired into CI or a documented `make` target.

**Follow-ups (recorded, not owed by this item):** the suite is `npm run e2e`, run by hand against the compose stack (`make reset-db` between runs; documented in `turnbase-frontend/CLAUDE.md`) — no CI job, it needs the full stack. Not covered, by choice: grace-period expiry, rate-limit flood, friends / notifications / profile pages, 400 px layout, concurrent games; the create-room view exposes neither visibility nor spectating (FR-CREATE-001/002), so the suite makes spectating rooms over REST. The forfeit scenario asserts the opponent is told and can return to the lobby but not the history row — whether a leave-forfeit emits `game_over` (FR-HIST) is unsettled. Found while running it: `GET /api/users/{username}/friends` throws `BadSqlGrammarException` (500) in the platform log. The client did not retry a `SUBSCRIBE`/`REQUEST_GAME_SYNC` dropped by Tier 6, so a game started on an empty bucket rendered no board (closed by `IMP-M8-15`).


**Follow-up (2026-10-03):** the uncovered areas and the known defects above are owned by `IMP-M8-01…16`; the suite is extended by `IMP-M8-16`.
---
