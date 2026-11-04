# Archive — M8 Regression review remediation and MVP view completeness

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim by `IMP-M20-01`. Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M8-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M8-01 | Seeded users get their privacy settings | platform | M1-07, M3-10 | DONE |
| IMP-M8-02 | The friends list query runs on PostgreSQL | platform | M1-09 | DONE |
| IMP-M8-03 | A forfeit and a timeout are recorded | platform | M5-01, M7-06 | DONE |
| IMP-M8-04 | Rooms emptied around a game end are closed | platform | M7-05, M2-09 | DONE |
| IMP-M8-05 | Tic-Tac-Toe takes only an integer `cell` | game | M7-08 | DONE |
| IMP-M8-06 | Shell, navigation, landing and redirects | frontend | M7-11 | DONE |
| IMP-M8-07 | Login, registration and OAuth completion views | frontend | M8-06 | DONE |
| IMP-M8-08 | Catalog, game detail and create-room options | frontend | M6-06 | DONE |
| IMP-M8-09 | Rooms list and join views | frontend | M7-01, M7-07 | DONE |
| IMP-M8-10 | The game room: lobby, in-game and results | frontend | M7-03, M7-04, M8-04, M8-17 | DONE |
| IMP-M8-11 | Profile view | frontend | M8-01, M8-03, M6-03 | DONE |
| IMP-M8-12 | Friends view | frontend | M8-02, M8-14 | DONE |
| IMP-M8-13 | Account settings view | frontend | M8-01, M6-03 | DONE |
| IMP-M8-14 | Notifications bell and panel | frontend | M6-06, M5-03 | DONE |
| IMP-M8-15 | The client retries a rate-limited subscribe | frontend | M6-04 | DONE |
| IMP-M8-16 | The acceptance suite covers every view and the review's gaps | frontend | M8-01…15, M8-17, M8-18 | DONE |
| IMP-M8-17 | The room resource names the viewer's membership | platform | M2-09 | DONE |
| IMP-M8-18 | The platform pushes a persisted notification to an open stream | platform | M5-03, M8-14 | DONE |

---

## M8 — Regression review remediation and MVP view completeness

Opened 2026-10-03 from the [MVP regression review](../../reviews/2026-10-03-mvp-regression-review/INDEX.md)
(`RR-01…RR-10`). Two kinds of item: `IMP-M8-01…05` close the backend and game findings; `IMP-M8-06…14`
give **every view the MVP ships a minimal, working UI** — one item per view, the game room being
`IMP-M8-10` — and `IMP-M8-15…16` close the client-side follow-up and re-run the review as a suite.

**Why a view item exists for views that are already "done".** The first review found views missing;
the second found views that exist and return `500` (Profile, Settings, Friends) or lack a control the
requirements list (create-room options). `IMP-M6-03/04/06` and `IMP-M7-01…04` were closed against their
narrow *Done when* clauses, and none walked the `VW-*` tables row by row. The review did not audit rows
individually either, so no document says which rows fail today. Each view item therefore starts with
that walk and records its failures as a checklist in its own *Remaining* line before fixing them.

**View standard — applies to every `IMP-M8-06…14`.** "Minimal working" means:

1. For each `VW-*` row of the view and each tier the row names, the element is present or absent exactly
   as the table says; an element a tier may not use is **hidden, not disabled** (NFR-USAB-001).
2. Every action the view offers succeeds against the compose stack: no `4xx`/`5xx` except the ones the
   view means to show, and no console error or warning on load or during the flow.
3. Loading, empty and error states each render something a user can act on; none is a spinner or the
   word "Loading…" that never resolves.
4. At 400 px wide the page does not scroll horizontally, and no control overlaps another.
5. Every control is reachable by keyboard and has an accessible name.
6. Astryx components only, layout styling only — nothing the `VW-*` rows do not list. Minimal means no
   polish work, not a partial feature.
7. One Playwright spec per view in `turnbase-frontend/e2e/` that exercises the rows, as a seeded user
   and — where the view has one — a Guest and an Unauth visitor. Specs use the seeded users; at most
   one registration per run (the address limit is 5 an hour, RR-10).

---

### IMP-M8-01 — Seeded users get their privacy settings

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-07, IMP-M3-10 · **Closes:** RR-01

**Read first:**
- `docs/reviews/2026-10-03-mvp-regression-review/INDEX.md` RR-01
- `docs/specs/platform/data-model-accounts.md` §4 (`user_privacy_settings`: "one always exists")
- `docs/specs/deployment/local-environment.md` §6, §7 (the `local` seeder)
- `docs/specs/api-design/profile-rest-api.md`

**Satisfies:** `user-accounts.md` privacy-settings requirements as listed in `profile-rest-api.md`

**Done when:** after a clean `make up`, `GET /api/users/me` and `GET /api/users/{name}` return `200` for
each of `alice`, `bob`, `carol`, `dave`, as themselves and as one another; the seeder (not a lazy read)
writes the row; a repository-level test asserts every seeded registered user has exactly one
`user_privacy_settings` row; a missing row for a live registered user is an invariant violation that
the `500` message already names — an integration test over real PostgreSQL covers both the seeded path
and a user registered through the API. If §4's "always exists" and the seeder's design disagree about
who creates the row, stop and open a gate with `spec-defect`.

---

### IMP-M8-02 — The friends list query runs on PostgreSQL

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-09 · **Closes:** RR-02

**Read first:**
- `docs/reviews/2026-10-03-mvp-regression-review/INDEX.md` RR-02
- `docs/specs/api-design/social-rest-api.md` — `GET /api/users/{username}/friends`
- `docs/specs/platform/data-model-social.md`
- `docs/specs/api-design/pagination-filtering-sorting.md`

**Satisfies:** `social-friends.md` friend-list requirements as listed in `social-rest-api.md`

**Done when:** `GET /api/users/{username}/friends` returns `200` with its page and sort order for a user
with no friends, one friend and more than one page of friends; the `ORDER BY` no longer refers to an
output alias inside an expression (`BadSqlGrammarException`, PostgreSQL error `column "friend_username"
does not exist`); the integration test runs against real PostgreSQL, not a mock, and fails on the
current query. Every other hand-written `ORDER BY`/`GROUP BY` in `JdbcClient` repositories is checked
for the same pattern and the result is recorded in the item's *Closed* line.

**Closed:** session 131 — `SocialRepository.listFriends` now sorts an outer select by `lower(friend_username), friend_id`; `SocialControllerIT` covers none/one/two-page lists on real PostgreSQL and failed on the old query with `column "friend_username" does not exist`. Every other hand-written `ORDER BY`/`GROUP BY` in `JdbcClient` repositories (admin, history, catalog, account, notification, room) was checked: they sort by table-qualified columns or bare aliases, never an alias inside an expression — no further defect.

---

### IMP-M8-03 — A forfeit and a timeout are recorded

**Repo:** `turnbase-platform` · **Depends on:** IMP-M5-01, IMP-M7-06 · **Closes:** RR-03

**Read first:**
- `docs/reviews/2026-10-03-mvp-regression-review/INDEX.md` RR-03
- `docs/requirements/game-history.md` FR-HIST-001…003
- `docs/requirements/per-game-statistics.md` FR-STATS-001
- `docs/requirements/reconnection-flow.md` FR-EXPIRY-002
- `docs/specs/flows/06-game-end-and-rematch.md`, `docs/specs/api-design/history-rest-api.md`
- `docs/implementation/registry.md` IMP-M7-06 *Done when* — its last-but-one clause

**Satisfies:** `game-history.md` FR-HIST-001…003; `per-game-statistics.md` FR-STATS-001 (forfeit)

**Done when:** after an explicit leave during `IN_PROGRESS` **and** after grace-period expiry, the
platform writes one history entry for each registered player of the session (the leaver's *Defeat*, the
opponent's *Victory*) and counts the session in both players' statistics; the log line `Invalid game
outcome … playerResults names a non-participant` and `turnbase_history_invalid_outcome_total` stay at
zero for a legitimate forfeit — the outcome's players are validated against the **session's** player
list, not the room's current members; an integration test covers both paths and reads the history API
afterwards. `IMP-M7-06` carried this clause and was closed without it. **FR-HIST-001 says history is
written only when the engine emits `game_over`**: if a forfeit's `game_over` and FR-HIST-001's wording
disagree, stop and open a gate with `spec-defect` rather than choose.

---

### IMP-M8-04 — Rooms emptied around a game end are closed

**Repo:** `turnbase-platform` · **Depends on:** IMP-M7-05, IMP-M2-09 · **Closes:** RR-04

**Read first:**
- `docs/reviews/2026-10-03-mvp-regression-review/INDEX.md` RR-04
- `docs/requirements/game-rooms.md` FR-XFER-001…003, FR-LIFE-004, FR-LIFE-007
- `docs/requirements/reconnection-flow.md` FR-DC-002, FR-DC-005, FR-EXPIRY-001…002
- `docs/specs/platform/room-lifecycle.md`, `docs/specs/flows/05-owner-loss-and-adoption.md`, `docs/specs/flows/07-room-closure.md`
- `docs/implementation/registry.md` IMP-M7-05

**Satisfies:** `game-rooms.md` FR-XFER-002, FR-XFER-003

**Done when:** (a) when every member of a room leaves within one scheduling instant — three sockets
closing 30 ms apart after `GAME_ENDED`, or two contexts closed together — the room is closed and absent
from `GET /api/rooms`, with host transfer taking place only while a human remains; the leaves are
serialised per room, not raced; (b) a room that returns to `LOBBY` after a grace expiry whose last member
is already gone is closed in the same step; (c) the grace period for two simultaneously disconnected
players is the configured 60 s — the review measured 11 s against 61 s for one player; either the
requirements define a shorter rule for that case and the item records it, or it is fixed; (d) an
integration test reproduces `09203c03` and `fe4d83bc` and asserts no listed room has `playerCount` 0
afterwards. The 30-minute idle sweep stays as the backstop and is **not** what closes these.

**Outcome (session 133):** (a) closure now keys on "the departing player left no human behind", not "the departing user was the host" — with serialised leaves the host goes first and the last one out is an ordinary player; (b) `detachSession` to `LOBBY` resolves outstanding reservations (`FR-EXPIRY-006`) and closes the room if no human remains, `ROOM_CLOSED` instead of `GAME_ENDED`; (c) **not reproduced** — each disconnect opens its own full 60 s reservation (asserted for two simultaneous drops); the review's 11 s is consistent with the second player dropping ~49 s after the first (`HOST_TRANSFERRED` shows the second was still connected at the first drop). Known simplification: if the host was among the resolved reservations and humans remain, `host_user_id` is left on the departed host as the existing "no host" state.

---

### IMP-M8-05 — Tic-Tac-Toe takes only an integer `cell`

**Repo:** `turnbase-game-tictactoe` (and `turnbase-sdk` if the mapper lives there) · **Depends on:** IMP-M7-08 · **Closes:** RR-09

**Read first:**
- `docs/reviews/2026-10-03-mvp-regression-review/INDEX.md` RR-09
- `docs/requirements/game-contracts.md` (action payloads)
- `docs/specs/gdk-api/backend-gdk-api.md` (how an action payload reaches the game)
- `turnbase-game-tictactoe/src/main/java/.../Move.java`, `TicTacToeGame.java`

**Satisfies:** `game-contracts.md` input-validation requirements

**Done when:** `SUBMIT_ACTION` with `{cell:"4"}` is `rejected` like `{cell:null}`, `-1`, `1.5` and `99`
already are; a unit test per malformed shape; if the mapper is the SDK's, the fix is made there, the
SDK's version is bumped under `conventions.md` §5 and the game consumes it.

---

### IMP-M8-06 — Shell, navigation, landing and redirects

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M7-11 · **Closes:** RR-07 (header)

**Read first:**
- `docs/requirements/platform-views.md` — *Navigation Bar* (VW-NAV-001…012), *Landing Page* (VW-LAND-*), *Redirect & Fallback Behavior* (VW-REDIR-*), NFR-SEC-001, NFR-USAB-001…002
- `docs/specs/platform-frontend/shell-architecture.md`, `docs/specs/platform-frontend/design-system.md`
- `docs/reviews/2026-10-03-mvp-regression-review/INDEX.md` RR-07

**Satisfies:** `platform-views.md` VW-NAV-001…012, VW-LAND-001…, VW-REDIR-001…, NFR-SEC-001, NFR-USAB-001…002

**Done when:** the *View standard* holds for the nav bar, the user menu, the landing page, the 403 view,
the 404 view and every redirect row, for Unauth, Guest and Registered; the header at 400 px collapses
(menu or wrap) so that **Rooms**, **Notifications** and its count badge do not overlap, which is the
defect the review saw; the `redirect` parameter rejects an external URL; a Guest following a
Registered-only link sees the explanatory message of NFR-USAB-002.

**Closed:** session 135 — the walk found the rows already present for all three tiers (`App.test.tsx` covers them); the one defect was RR-07's header. `NavBar` now moves the links (and, signed out, the three calls to action) to a wrapping second row at ≤ 640 px. `e2e/shell.spec.ts` covers Unauth, Guest and `alice` (nav rows, user menu, 403 text, `//evil` redirect, 404, no overlap/page scroll at 400 px). The `/rooms` table's horizontal scroll is `IMP-M8-09`'s, `/games` is `IMP-M8-08`'s.

---

### IMP-M8-07 — Login, registration and OAuth completion views

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M8-06 · **Closes:** RR-10

**Read first:**
- `docs/requirements/platform-views.md` — *Login* (VW-LOGIN-*), *Register* (VW-REG-*), *OAuth Completion* (VW-OAUTHCOMP-*)
- `docs/specs/api-design/rate-limiting.md` (the `429` and `Retry-After`)
- `docs/specs/api-design/error-handling.md`, `docs/specs/api-design/input-validation.md`
- `docs/reviews/2026-10-03-mvp-regression-review/INDEX.md` RR-10

**Satisfies:** `platform-views.md` VW-LOGIN-001…, VW-REG-001…, VW-OAUTHCOMP-001…

**Done when:** the *View standard* holds for `/login`, `/register`, `/auth/complete-registration` and
the *Play as Guest* action; every server field error appears next to its field; a `429` shows the wait
from `Retry-After` ("try again in 14 minutes"), not "a moment"; the OAuth button is hidden — not
disabled — when the provider is not configured, and the completion view is exercised with the stubbed
provider if the stack has one, otherwise the item records that it cannot be and why.

---

### IMP-M8-08 — Catalog, game detail and create-room options

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M6-06 · **Closes:** RR-06

**Read first:**
- `docs/requirements/platform-views.md` — *Game Catalog* (VW-CAT-*), *Game Detail* (VW-GDET-*)
- `docs/requirements/game-rooms.md` FR-CREATE-001…004, FR-LIST-006
- `docs/specs/api-design/catalog-rest-api.md`, `docs/specs/api-design/room-rest-api.md` (`POST /api/rooms`)
- `docs/reviews/2026-10-03-mvp-regression-review/INDEX.md` RR-06

**Satisfies:** `platform-views.md` VW-CAT-001…, VW-GDET-001…; `game-rooms.md` FR-CREATE-001, FR-CREATE-002

**Done when:** the *View standard* holds for `/games` and `/games/:id`; **Create room** opens a choice of
visibility (Public, Friends Only, Invite Only) and — only when the game `supportsSpectators` — whether
spectating is allowed, then posts exactly that to `POST /api/rooms`; Friends Only is not offered to a
Guest (FR-LIST-006 / FR-GUEST-007); the e2e support no longer creates spectating rooms over REST and a
spec makes one through the dialog and enters it as a spectator.

**Closed:** session 137 — `CreateRoomButton` opens a dialog: visibility (Public default, Friends Only omitted for a Guest, Invite Only) and an *Allow spectators* switch shown only when `supportsSpectators`; `spectatingEnabled` is posted only then. The `/games` filter row now wraps, so 400 px no longer scrolls the page (RR-07). `e2e/catalog.spec.ts` covers Unauth, Guest and `alice`; `support.createRoom({spectating})` goes through the dialog, no REST.

---

### IMP-M8-09 — Rooms list and join views

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M7-01, IMP-M7-07 · **Closes:** RR-07 (rooms table)

**Read first:**
- `docs/requirements/platform-views.md` — *Active Rooms* (VW-ROOMS-001…005), *Join* (VW-JOIN-001…003)
- `docs/requirements/game-rooms.md` FR-LIST-001…007, FR-JOIN-001…007
- `docs/requirements/reconnection-flow.md` FR-REJOIN-002
- `docs/specs/api-design/room-rest-api.md`

**Satisfies:** `platform-views.md` VW-ROOMS-001…005, VW-JOIN-001…003

**Done when:** the *View standard* holds for `/rooms` and `/rooms/join/:code`; the table at 400 px
becomes a stacked list or scrolls inside its own container (the page scrolled 154 px sideways in the
review); the pinned reconnection card appears for a caller holding a grace-period slot and goes away when
it is released, shown by a spec that drops a player mid-game; Friends Only rooms are absent for a Guest;
Join and Spectate are each present only when that role is open; a full-room code and a code that
resolves to nothing each show their own reason (VW-JOIN-003). *Corrected session 138:* the clause
said invalid, expired and full each differ, but `room-rest-api.md` §3.1 returns one empty list for a
wrong, expired and closed code on purpose (no oracle, NFR-SEC-002), so the client can name only
"not valid, expired or closed" as one reason.

---

### IMP-M8-10 — The game room: lobby, in-game and results

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M7-03, IMP-M7-04, IMP-M8-04, IMP-M8-17 · **Closes:** RR-05, RR-08, RR-07 (room at 400 px)

**Read first:**
- `docs/requirements/platform-views.md` — *Room Lobby* (VW-RLOBBY-001…017), *Room In-Game* (VW-RGAME-001…008), *Room Results* (VW-RRESULT-001…005), *Join* (VW-JOIN-001…003)
- `docs/specs/platform-frontend/shell-architecture.md` §4, §5, §8
- `docs/specs/api-design/room-websocket.md`, `docs/specs/api-design/room-chat-websocket.md`
- `docs/requirements/game-rooms.md` FR-XFER-*, FR-JOIN-*, `docs/requirements/reconnection-flow.md` FR-REJOIN-*
- `docs/reviews/2026-10-03-mvp-regression-review/INDEX.md` RR-05, RR-08
- `docs/specs/api-design/room-rest-api.md` §4 (`viewerRole`)

**Satisfies:** `platform-views.md` VW-RLOBBY-001…017, VW-RGAME-001…008, VW-RRESULT-001…005

**Done when:** the *View standard* holds for `/rooms/:id` in each of its states — **lobby, in-game and
results** — and for each role: host, non-host player, spectator, and a non-member. **Known (session 138):** a full page reload
of `/rooms/:id` mid-game showed the Lobby view for the reconnecting player and left their grace-period
slot held — cover it in the *refresh rejoins from a snapshot* spec. **First step:** the
review found that opening `/rooms/:id` as a non-member enrols the visitor (as a player in a public room,
as a spectator when a room has no seat) with no prompt, while VW-JOIN-002 asks for a Player / Spectator
choice before joining; `platform-views.md` writes that for the join-by-code route only. Decide in the
spec which route may enrol (`spec-defect`), then build it: a visit that is not a deliberate join does not
take a seat. Then: *Start game* is disabled — not merely refused by the server — until the platform's
readiness rule holds, and the reason is shown; host actions (Kick, Transfer host, Start) are absent for
everyone else; a spectator sees the board, the participant panel and *Switch to player* where allowed,
and no chat box; the *Team* chat tab appears only when the game declares teams (it showed in a two-player
Tic-Tac-Toe room); the results view keeps the board and offers *Return to lobby* and *Leave*; the lobby,
the in-game view and the results view at 400 px keep the board inside the viewport and the controls
reachable; a refresh in each state rejoins from a snapshot. Specs: four contexts (host, player,
spectator, outsider) through lobby → game → results, plus a drop-and-resume and a forfeit.

**Built (session 141):** entry prompt for non-members (`viewerRole`), Start disabled with reasons, Switch gated on a free slot, team chat only when a team holds more than one player (`in-room-chat.md` FR-CHAN-002 now says so), 400 px wrapping, `e2e/room.spec.ts`. The mid-game refresh defect was the platform: `ROOM_STATE` always sent `gameFrontendUrl: null` — fixed in `turnbase-platform`. A refresh by a spectator, or in the Lobby, is a disconnect-leave (FR-DC-002/003) and returns through the prompt by design.

**Closed:** IMP-GATE-95 (opened and closed 2026-10-03, session 139) — the *First step* above. Only `/rooms/join/:code` enrols on arrival; `/rooms/:id` re-enters a member and otherwise shows the Player / Spectator prompt, enrolling on a button press (`platform-views.md` *Room — Lobby*, Entry; `shell-architecture.md` §8). The client cannot tell a member from a visitor today, so the room resource gains `viewerRole` (`room-rest-api.md` §4) — built by `IMP-M8-17`, which this item now depends on. What remains for this item is the rest of its *Done when*, starting at *Start game* disabled with a reason.

---

### IMP-M8-11 — Profile view

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M8-01, IMP-M8-03, IMP-M6-03 · **Closes:** RR-01 (UI half)

**Read first:**
- `docs/requirements/platform-views.md` — *Profile* (VW-PROF-001…), including *The owner is exempt from their own privacy settings*
- `docs/specs/api-design/profile-rest-api.md`, `docs/specs/api-design/history-rest-api.md`, `docs/specs/api-design/statistics-rest-api.md`
- `docs/requirements/game-history.md`, `docs/requirements/per-game-statistics.md`

**Satisfies:** `platform-views.md` VW-PROF-001…

**Done when:** the *View standard* holds for `/users/:username` for the owner, another registered user, a
Guest and an Unauth visitor, over a public and a private profile; the history tab shows a forfeit as
*Victory*/*Defeat* (needs `IMP-M8-03`); statistics show the totals the API returns; an error response
renders a message with a retry, never an unresolved state; the owner sees Edit Profile (VW-PROF-008).

---

### IMP-M8-12 — Friends view

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M8-02, IMP-M8-14 · **Closes:** RR-02 (UI half)

**Read first:**
- `docs/requirements/platform-views.md` — *Friends* (VW-FREN-001…)
- `docs/requirements/social-friends.md`
- `docs/specs/api-design/social-rest-api.md`, `docs/specs/api-design/notification-rest-api.md`

**Satisfies:** `platform-views.md` VW-FREN-001…

**Done when:** the *View standard* holds for `/friends` as a Registered user, and a Guest and an Unauth
visitor are sent where VW-REDIR says; the friend list, send request, incoming and outgoing requests,
accept, decline, remove and block (whichever VW-FREN rows exist) each work end to end between two
contexts, and the receiver's bell shows the request live; a failed action reports **which** action
failed, not "Could not complete that action" twice on load (the review saw two such toasts on every
visit).

---

### IMP-M8-13 — Account settings view

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M8-01, IMP-M6-03 · **Closes:** RR-01 (UI half)

**Read first:**
- `docs/requirements/platform-views.md` — *Account Settings* (VW-SET-001…)
- `docs/requirements/user-accounts.md` (username change, password change, privacy, deletion as listed)
- `docs/specs/api-design/profile-rest-api.md`, `docs/specs/api-design/input-validation.md`

**Satisfies:** `platform-views.md` VW-SET-001…

**Done when:** the *View standard* holds for `/settings`; each form (username, password, email,
privacy, delete account — whichever VW-SET rows exist) loads its current value, validates with the
server's field errors, saves, and shows a confirmation; a Guest sees the registered-only message
(NFR-USAB-002), not a blank page; Settings never sits on "Loading…" when the request fails.

---

### IMP-M8-14 — Notifications bell and panel

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M6-06, IMP-M5-03 · **Closes:** the review's *Not covered* (live friend-request notification)

**Read first:**
- `docs/requirements/platform-views.md` — *Notifications* (VW-NOTIF-001…), VW-NAV-005
- `docs/requirements/notifications-invitations.md`
- `docs/specs/api-design/notification-rest-api.md`, `docs/specs/api-design/sse-notifications.md`
- `docs/requirements/game-rooms.md` (room invitations)

**Satisfies:** `platform-views.md` VW-NOTIF-001…, VW-NAV-005

**Done when:** the *View standard* holds for the bell and its panel as Guest and Registered; every
notification type the platform emits has a rendered text, including **room invitations** with a
working *Join* action and a friend request with *Accept*/*Decline*; the badge and the open panel
re-read on every (re)open of the stream; *Mark read*, *Mark all read* and *Dismiss* persist across a
reload; an unknown type renders a generic line rather than nothing.

**Moved:** the clause "a notification created while the page is open (SSE) updates the badge without
a reload" moved to `IMP-M8-18` (session 143). The platform writes every persisted notification by
SQL and delivers it only as the catch-up on stream open (`NotificationEmitterRegistry` has
`publishAlert` and `sendCatchUpNotification`, nothing that pushes a new row), so no client can satisfy
it. The client half is built: the bell refetches on every stream event and every reopen.

---

### IMP-M8-17 — The room resource names the viewer's membership

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-09 · **Closes:** RR-05 (backend half; `IMP-GATE-95`)

**Read first:**
- `docs/specs/api-design/room-rest-api.md` §4 (`viewerRole`), §5 step 2
- `docs/requirements/platform-views.md` *Room — Lobby*, Entry
- `docs/requirements/reconnection-flow.md` FR-REJOIN-003, FR-EXPIRY-001

**Satisfies:** `platform-views.md` VW-JOIN-002 (on `/rooms/:id`)

**Done when:** `GET /api/rooms/{roomId}` carries `viewerRole`: `PLAYER` for a caller with an open player
row or a grace-period reservation, `SPECTATOR` for an open spectator row, `null` otherwise — including
a visitor to a public room and a caller who has left; the field is absent from list rows; the
OpenAPI document and the frontend's generated contract fixtures name it; an integration test asserts all
four values and that a `GET` never changes membership or bumps the room's version.

---

### IMP-M8-18 — The platform pushes a persisted notification to an open stream

**Repo:** `turnbase-platform` · **Depends on:** IMP-M5-03, IMP-M8-14 · **Closes:** the review's *Not covered* (live friend-request notification); the live clause of `IMP-M8-14`

**Read first:**
- `docs/specs/api-design/sse-notifications.md` (*Two event classes*, *Offline delivery*, *Implementation*)
- `docs/specs/platform/data-model-notifications.md` §1 (`delivered_at`, `event_seq`)
- `docs/requirements/notifications-invitations.md` FR-NOTIF-007, FR-NOTIF-008, NFR-PERF-001
- `turnbase-frontend/e2e/notifications.spec.ts` (the `reload()` calls to remove)

**Satisfies:** `notifications-invitations.md` FR-NOTIF-007, FR-NOTIF-008

**Done when:** every writer of a `notification` row (`SocialRepository`'s four friend types, the room
invitation send, the review and bundle-validation producers) causes, **after commit**, an
`event: notification` frame with `id:` = `event_seq` to every open stream of the recipient and stamps
`delivered_at`, so the catch-up on the next open does not repeat it; a recipient with no open stream is
untouched (FR-NOTIF-008); the producers do not reach into `notification`'s internals (Spring Modulith
passes); an integration test over real PostgreSQL asserts push-after-commit, no push on rollback, and
no repeat on reconnect; the `reload()` calls in the frontend's `e2e/notifications.spec.ts` are removed
and it asserts the badge for a request sent while the recipient's page stays open.

---

### IMP-M8-15 — The client retries a rate-limited subscribe

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M6-04 · **Closes:** the follow-up recorded under `IMP-M7-13`

**Read first:**
- `docs/specs/api-design/rate-limiting.md` (Tier 6, `RATE_LIMIT_EXCEEDED` on `/user/queue/errors`)
- `docs/specs/api-design/websocket.md`, `docs/specs/api-design/room-websocket.md`
- `docs/implementation/registry.md` IMP-M7-13 *Follow-ups*

**Satisfies:** `reconnection-flow.md` FR-REJOIN-* (a join that does not silently half-complete)

**Done when:** a `SUBSCRIBE` or `REQUEST_GAME_SYNC` answered with `RATE_LIMIT_EXCEEDED` is retried after a
bounded back-off and the room or game view recovers without a reload; after the retry limit the view
shows an error with a retry button; a unit test and a Playwright spec that exhausts the bucket (three
game attaches in under 30 s for one user) end with a rendered board.

---

### IMP-M8-16 — The acceptance suite covers every view and the review's gaps

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M8-01…15, IMP-M8-17, IMP-M8-18

**Read first:**
- `docs/reviews/2026-10-03-mvp-regression-review/INDEX.md` — *What was verified working* and *Not covered*
- `docs/implementation/registry.md` IMP-M7-13 and its *Follow-ups*
- `docs/implementation/conventions.md` (test layout)

**Done when:** `npm run e2e` includes the per-view specs of `IMP-M8-06…14`, a forfeit scenario that
asserts the history row and the statistics, grace-period expiry with the 60 s figure asserted, the
`RATE_LIMIT_EXCEEDED` flood and its recovery, two simultaneous departures leaving no listed room, a
400 px pass over every route asserting no horizontal scroll, and a console-error and `5xx` tripwire
that fails any spec which saw one; the suite is wired into a documented `make` target and either a CI
job or an explicit note of why it cannot run there; a clean `make up` followed by the suite is green
**twice in a row** (the run must not exhaust the registration or guest allowance).

**Delivered (session 148):** `make e2e` in `turnbase-frontend` (checks the stack is up, then runs the suite). CI cannot run it: it needs the full compose stack (platform, game host with Espresso, Postgres, Redis, MinIO) and a ~8 min run bounded by the Tier 1/5/6 rate-limit budgets, so it is run by hand — `turnbase-frontend/CLAUDE.md` documents the allowance. Two runs fit per 24 h; a third needs a Redis flush. Verified green twice in a row on a clean `make up`.

---
