# MVP Regression Review — 2026-10-03

A second black-box run of the local stack, after the `IMP-M7-01…13` batch that the
[2026-10-01 review](../2026-10-01-mvp-implementation-review/INDEX.md) produced reached `DONE`. It asks two
questions:

> Did that batch close what it said it closed? And what does a player or an operator meet that neither
> the batch nor its acceptance suite looks at?

## Verdict

> **The game is now playable in a browser, and nearly every defect of the first review is closed. But
> three of the four account pages a registered player reaches from the header are broken for the seeded
> users, and a forfeit leaves no trace in history.** Registration, catalog, room list, lobby, chat,
> spectating, Tic-Tac-Toe to a win, mid-game drop and resume, and a mid-game leave all work through the
> UI, and `npm run e2e` is 5 of 5. **Profile (`/users/{name}`), Settings and the Friends list return
> `500`** (RR-01, RR-02) — none of them is in the acceptance suite, by choice. A player who forfeits or
> times out is not recorded in history or statistics for either side (RR-03). Rooms that empty around the
> end of a game are still never closed (RR-04, the part of MR-02 that `IMP-M7-05` did not reach).
>
> MVP status is **reached for the play loop; not yet for the account surface.**

## How it was run

- **Clean slate:** all images rebuilt at the current heads (platform `c790d92`, frontend `49bfed3`, host
  `21a5544`, tictactoe `cd385af`), `down -v`, the hand-written `.env` deleted, then **`make up` alone** —
  the first-run path `IMP-M7-12` added. Healthy in **31 s** from cold with the `.env` copied from
  `.env.example`; the observability overlay then came up healthy on the same `.env`.
- **Four players, four cookie jars:** the same split as before — alice and bob play, carol spectates, dave
  is the outsider — as separate Playwright `browser.newContext()` contexts (UI) and as independent
  cookie jars in the STOMP driver (`.claude/skills/run-turnbase/driver.mjs`). Registered accounts were
  created through the UI until the 5-per-hour address limit answered `429`, then the seeded users were
  used.
- **Tiers:** the existing suite (`npm run e2e`) as a baseline; the driver scenarios `game`, `drop`,
  `leave`; then throw-away Playwright probes and STOMP scripts for what the suite leaves out
  (lobby/in-game/spectator views, chat, friends and notifications, 400 px layout, malformed actions,
  flood, forfeit history, visibility). The probes were deleted afterwards; nothing was added to a
  repository.
- Seeded sessions are single-device: a second `login` for the same user ends the first
  (`401 … logged in from another device`). Concurrent runs of the driver and a browser as the same seeded
  user therefore break each other — environment, not a defect.

## Status of the 2026-10-01 findings

| ID | Finding | Now | Evidence |
|---|---|---|---|
| MR-01 | Room views are placeholders | **Closed** | Create → lobby → join → ready → start → play → results, all in the browser; `GameFrame` loads `…games.localhost:8080/play/{sessionId}` with `sandbox="allow-scripts allow-same-origin"` as `game-asset-serving.md` §6.1 requires |
| MR-02 | Rooms abandoned in Lobby never close | **Partly closed** | A host who leaves, and two members closing at once, close the room. Rooms emptied around a game end do not — **RR-04** |
| MR-03 | Leaving mid-game neither forfeits nor ends | **Closed for the game, open for the record** | Opponent gets "The game is over." and *Return to lobby*; no history row — **RR-03** |
| MR-04 | Missing `cell` is cell 0 | **Closed, with one residue** | `{}`, `null`, `-1`, `1.5`, `99` are `rejected`; a string `"4"` is still a move — **RR-09** |
| MR-05 | Cold game start 6.5 s | **Improved, not gone** | First `START_GAME` after a clean boot 3 828 ms (was 6 465); warm 20–44 ms |
| MR-06 | Sparse application logging | **Closed** | Loki carries `Room created`, `Room event event=… roomVersion=…`, `Room socket connected/disconnected`, `WebSocket connected/disconnected`, each with `roomId`/`userId` |
| MR-07 | Console 401 on anonymous load | **Closed** | `GET /api/auth/session` → `200 {"authenticated":false}`; no console error on `/`, `/games`, `/login`, `/register` |
| MR-08 | Two `TaskScheduler` beans WARN | **Closed** | The only WARN lines on a fresh boot are the two `DB: extension …` lines |
| MR-09 | Games origin 404 at `/` | **Closed as a question** | `/` is still `404` by design; the URL the platform hands out, `/play/{sessionId}`, mounts the game in the frame |
| MR-10 | `Secure` on plain-HTTP localhost | **Closed** | `turnbase_session=…; HttpOnly; SameSite=Strict` — no `Secure` |
| MR-11 | No first-run path | **Closed** | `make up` from a clone with no `.env` → healthy stack, seeded game listed |

## What was verified working

| Area | Result |
|---|---|
| Acceptance suite | `npm run e2e`: 5 of 5 green in 60 s against the freshly built stack |
| Catalog and detail | Seeded Tic-Tac-Toe with OFFICIAL badge, *Create room* works from the detail page |
| Auth | UI registration and log-in; anonymous visitors to `/rooms` and `/friends` are sent to `/login`; `/nope` is a 404 view; 6th registration from one address → `429` with `Retry-After` |
| Room lobby | Host sees *Transfer host*, *Kick*, *Start game*, *Share invite link*, *Leave room*; guest sees *Ready*; players, readiness and spectators update live on every client |
| Room visibility | `FRIENDS_ONLY` and `INVITE_ONLY` rooms are absent from an outsider's list and answer `404` on `GET`; the UI shows "This room is closed, or you cannot enter it." |
| Chat | Room message from A reaches B in the same second; `<b>hi</b> & <img onerror=…>` renders as literal text; chat survives the game start and the opponent's leave; spectators have no chat box (as `in-room-chat.md` specifies) |
| Spectator | Sees players and the game frame, cannot act (`ROLE_NOT_ELIGIBLE`), *Switch to player* offered in the lobby |
| Game | X/O, alternate turns, win on the fifth move, "The game is over." on both players, return to lobby; 5 moves 20–28 ms warm |
| Server-side guards | `START_GAME` with an unready guest → `START_CONDITIONS_NOT_MET`; non-participant `SUBMIT_ACTION` ignored; outsider receives 0 frames on the room and game topics |
| Reconnection | `drop`: `PLAYER_DISCONNECTED` with a 60 s grace, resync returns the board. **Grace expiry observed for the first time:** one player's socket closed mid-game → `PLAYER_LOST reason=GRACE_PERIOD_EXPIRED` at the opponent after **61.0 s**, as specified. (A second, two-player abandonment expired after 11 s — see RR-04) |
| Flood | 60 `REQUEST_GAME_SYNC` in one burst → one `RATE_LIMIT_EXCEEDED`, then `RATE_LIMIT_ABUSE` and the socket is closed `1002` |
| Notifications | Bell shows the unread count (`1`, `2`) from the seeded rows, the panel lists them with *Mark read / Dismiss / Mark all read* |
| Observability | Prometheus `platform` and `gamehost` up; `turnbase_rooms_active`, `turnbase_game_sessions_active`, `turnbase_websocket_connections_active`, `turnbase_history_invalid_outcome_total` (new) present; `HighErrorRate` went `pending` during the run — the 500s below did it; Loki returns the lifecycle lines; Tempo holds platform traces |

## Performance (local, one machine)

| Measurement | Result |
|---|---|
| `START_GAME` → `GAME_STARTED`, **cold** (first session after boot) | **3 828 ms** (was 6 465) |
| `START_GAME` → `GAME_STARTED`, warm | 20–44 ms |
| Move → `GAME_EVENT` at the spectator, warm | 20–28 ms (first moves after a cold start 85 and 279 ms) |
| Resting memory | platform 1.01 GiB, game host 1.10 GiB, frontend 15 MiB (was 849 MiB / 881 MiB / 17 MiB) |
| Resting CPU | platform 2.7 %, others under 1 % |

No concurrent-game load was run.

## Findings

Severity: **High** blocks a user-facing surface; **Medium** is a behavioural defect or a real risk;
**Low** is polish or a spec question. Findings that are already recorded as follow-ups in the registry are
marked *known*.

### RR-01 — Profile and Settings return 500 for every seeded user — **High**

`GET /api/users/me` and `GET /api/users/{name}` (authenticated) answer `500`. The profile page shows
"Could not load this profile. Please try again."; **Settings sits on "Loading…" for ever**. The platform
log names the cause: `user_privacy_settings row missing for a live registered user — data-model-accounts.md
§4 states one always exists` (`ProfileService.requireNonNull`) and
`EmptyResultDataAccessException … ProfileRepository.findPrivacySettings`. The `local` seeder inserts the
four users without that row (`select count(*) from user_privacy_settings` → 1, for the one user registered
through the UI). Viewing *another* seeded user's profile fails the same way, so the fault is on the target
row, not the viewer. An anonymous `GET /api/users/alice` succeeds, which is why the suite's profile
assertion (`/users/{registered}` after a game) never notices.

**Recommendation:** the seeder must write the row (or the service must create it on demand — then
§4's "always exists" is wrong). Also decide whether a missing row should be a `500` at all. Add profile
and settings to the acceptance suite for a seeded user. The 500 trips the `HighErrorRate` alert on a
local stack.

### RR-02 — The Friends list returns 500; the page never leaves "Loading…" — **High** (*known*)

`GET /api/users/{name}/friends` → `500`: `BadSqlGrammarException` on
`… order by lower(friend_username) asc` — PostgreSQL rejects an *output-column alias* inside an
expression in `ORDER BY` (`ERROR: column "friend_username" does not exist`). The query is the only one
that sorts that way. In the UI the *Incoming requests* section renders but **"Your friends" stays on
"Loading…"** and two "Could not complete that action. Please try again." toasts appear on every visit.
Accept/Decline could not be exercised end to end for the same reason (the page re-fetches the list).
Recorded under `IMP-M7-13`'s follow-ups but with no work item; the cause is now confirmed.

**Recommendation:** order by `lower(case when f.user_id_low = ? … end)` or wrap the select in a subquery.
Test it against a real PostgreSQL — the unit tier cannot see it.

### RR-03 — A forfeit or a grace-period timeout writes no history and no statistics — **Medium**

After `DELETE …/participants/me` mid-game, **and** after `GRACE_PERIOD_EXPIRED`, the platform logs
`Invalid game outcome, no history entries written sessionId=… : playerResults names a non-participant`
(five times during this run) and increments `turnbase_history_invalid_outcome_total`. The leaver has
already been removed from the room, so the engine's outcome names someone the history service no longer
treats as a participant. Result: the winner by forfeit has **no *Victory* row and no count**
(`totalPlayed` unchanged), the leaver has no *Defeat*. `per-game-statistics.md` FR-STATS-001 counts a
forfeit as a completed session. The `IMP-M7-13` forfeit test deliberately does not assert the row.

**Recommendation:** resolve participants for the outcome against the session's player list, not the
room's current members; add the history row to the forfeit scenario.

### RR-04 — Rooms that empty around a game end are still never closed — **Medium**

Two rooms stayed `LOBBY`, `playerCount 0`, `canJoin: true` and listed for at least 12 minutes (the 30-minute
idle sweep was not awaited):

1. **`09203c03`** — driver `game`: after `GAME_ENDED` all three sockets closed within 30 ms →
   `PLAYER_LEFT` ×3, **no `HOST_TRANSFERRED`, no close**. Repeating the scenario three more times closed
   cleanly each time, so this is a race between concurrent leaves.
2. **`fe4d83bc`** — both players' sockets dropped mid-game → `HOST_TRANSFERRED`, then
   `PLAYER_LOST … GRACE_PERIOD_EXPIRED` and `GAME_ENDED` only **11 s** after the disconnect, not the 60 s
   a single drop took (61.0 s, measured separately). The room returned to `LOBBY` with a member who
   was long gone and then with none. Why the grace was shorter when both players were gone is unexplained.

`IMP-M7-05` covers a host leaving and the last human leaving one at a time; neither concurrent leaves nor
the post-game window are covered. The public list (the first screen after logging in) fills with
unjoinable-in-practice rooms again — two of its three rows during the run were ghosts.

### RR-05 — Opening `/rooms/{id}` joins the visitor, silently — **Low** (spec question)

A logged-in outsider who follows a link to a *public* room is enrolled as a **player** on page load
("dave — Not ready" appeared in the host's lobby); to a room that allows spectators and has no free
seat, as a **spectator**. No prompt precedes it. `platform-views.md` VW-JOIN-002 asks for a Player /
Spectator choice "before joining when both roles are available", but that is written for the join-by-code
route; `/rooms/:id` is not specified to join anyone. A prefetch, a link preview or a mistaken click takes
a seat. For a `FRIENDS_ONLY` room the view correctly refuses. Decide in the spec which route may enrol.

### RR-06 — The create-room view offers neither visibility nor spectating — **Medium** (*known*)

*Create room* posts `{gameId, visibility: PUBLIC}`. A player cannot create a Friends-only or Invite-only
room, and **cannot create a room that allows spectators**, so the spectator experience (and VW-ROOMS's
*Spectate* button) is unreachable from the product — the suite makes such rooms over REST.
`game-rooms.md` FR-CREATE-001/002 are listed under `IMP-M6-04` and `IMP-M7-01` *Satisfies*; neither
builds the choice, and no work item owns it.

### RR-07 — Header and tables break at 400 px — **Low**

At 400 px (a phone) the header collides: the **Rooms** and **Notifications** labels print over each other
and the count badge overlaps *Friends*. `/rooms` scrolls the page horizontally by 154 px (the table's
*Actions* column is clipped) and `/games` by **376 px**. Profile, Friends, Settings, the lobby and the
in-game view were within the viewport. `platform-views.md` asks for a usable phone layout; the
acceptance suite lists 400 px as not covered.

### RR-08 — *Start game* is enabled while the guest is not ready — **Low**

The server refuses it (`START_CONDITIONS_NOT_MET`), so nothing breaks; the button should be disabled, or
the refusal shown. What the player *sees* after pressing it was not checked.

### RR-09 — Tic-Tac-Toe accepts a numeric string as a move — **Low**

`SUBMIT_ACTION {cell:"4"}` is a legal move on cell 4; `{}`, `{cell:null}`, `-1`, `1.5`, `99` and an
object with an extra field are all `rejected`. Jackson's default coercion in `Move`; the reference game
is what third parties copy. Disable `ALLOW_COERCION_OF_SCALARS` in the SDK's mapper or document the
behaviour.

### RR-10 — The registration limit tells the user "a moment" and means 13 minutes — **Low**

The sixth `POST /api/auth/register` from one address in an hour returns `429` with `Retry-After: 806`; the
form shows "Too many attempts. Please wait a moment and try again." The header is there to be read.
Related for developers: the acceptance suite registers a user per run, so a handful of runs (or any
manual exploration) exhausts the hour's allowance.

## Not covered

- Idle sweep of the two ghost rooms (30 minutes; not awaited) and the 4-hour room expiry.
- Accept/Decline of a friend request end to end, friend request *send* from the profile page, and the
  `FRIEND_REQUEST` notification arriving live (blocked by RR-01/RR-02; the bell was verified on seeded
  rows only).
- The client not retrying a rate-limited `SUBSCRIBE` / `REQUEST_GAME_SYNC` — *known*, recorded under
  `IMP-M7-13`; not provoked from the UI here. The server side of the flood behaves as specified.
- Public/OAuth sign-in, guest conversion, user-uploaded games and the admin surface; the in-room team
  chat tab (*Team* is shown in a two-player room with no teams).
- Accessibility audit; concurrent-game load and soak; Grafana dashboard contents (the compose Grafana
  password differs from the one in the review's `.env`, so the API was not queried); the Tempo
  platform → game-host span link.
- The Google OAuth button's availability probe and the guest limit (5 per hour per address — the guest
  path was not run at all, to keep the allowance for registration).

## Run-hygiene notes

- The stack is **still running** (`docker compose … up -d`, `.env` from `.env.example`, no volumes
  kept from the earlier run). `turnbase-platform/deploy/compose/.env` is git-ignored.
- Images `turnbase/{platform,game-host,frontend}:dev` were rebuilt from the current submodule heads.
- All probes were throw-away files in the session's scratch directory; `e2e/probe.spec.ts` was created in
  `turnbase-frontend` for the run and deleted. No repository was changed.
