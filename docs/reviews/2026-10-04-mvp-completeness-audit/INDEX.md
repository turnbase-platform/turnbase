# MVP Completeness Audit — 2026-10-04

A third black-box run of the local stack. It started once the `IMP-M8-01…18` batch, opened by the
[2026-10-03 regression review](../2026-10-03-mvp-regression-review/INDEX.md), had reached `DONE`. M8 set
out to give every MVP view a minimal, working UI under one *View standard* (`registry.md` M8). The run
asks:

> Does every view the MVP ships now hold to that standard, for every role that reaches it? And can a
> player get through every planned function from the UI alone, without a REST call the product does
> not make?

## Verdict

> **The MVP is functionally complete for the play loop and the account surface. Two planned features
> are still out of a player's reach, and one claimed function is quietly wrong.**
>
> Every route renders for every tier at 1280 px and at 400 px, with no unintended `4xx`/`5xx` and no
> horizontal scroll. The suite is 45 of 45. All ten findings of the regression review are closed.
> Profile, Settings and Friends work for the seeded users. A forfeit writes its history row. No ghost
> room was left after about a dozen games.
>
> What remains:
> - **A host cannot invite a friend to a room.** VW-RLOBBY-005 was never built. Room invitations exist in
>   the API and in the notification panel, but only a REST call sends one (CA-01).
> - **Every profile's *Uploaded games* lists the whole catalog.** The backend ignores the `owner` filter
>   that the profile page sends (CA-02).
> - **The reference game never says who won** (CA-03).
> - **The catalog's per-row *Create room* button is clipped off the table at desktop widths** (CA-04).
>   It works at 400 px, which is the only width the *View standard* checks.
>
> MVP status: **reached for the play loop and the account surface. Not yet for room invitations and
> uploaded games.**

## How it was run

- **Clean slate:**
  - Images rebuilt at the current heads: platform `4602925`, frontend `56ef304`, game host `21a5544`,
    tictactoe `93a152a`, sdk `d78ecb9`, common `57a102a`. Every layer came from the cache, so the
    running images already matched.
  - Then `down -v` and `make up`. Healthy in **36.7 s** from cold; the observability overlay came up
    healthy on the same `.env`.
- **Baseline:** `make e2e` (`IMP-M8-16`'s suite), **45 of 45 green in 7.3 min**.
- **Driver:** `.claude/skills/run-turnbase/driver.mjs` scenarios `game` (×2), `drop` and `leave`. A
  `leave2` variant, kept in scratch, timed the forfeit after an explicit leave.
- **Probes:** throw-away Playwright specs, in a scratch folder of `turnbase-frontend`, deleted
  afterwards.
  - **Route tour:** 14 routes × three tiers (anonymous, guest, alice) × two widths (1280, 400 px). Each
    page recorded console errors and warnings, page errors, every `≥400` response, horizontal overflow,
    and an **axe-core 4.10.3** pass (injected with CSP bypassed in the probe's own context only).
  - **Room tour:** four contexts — host alice, player bob, spectator carol, outsider dave (400 px).
    Lobby → chat → share invite → switch roles → transfer host and back → start → mid-game reload →
    play → results → return to lobby → kick → back/forward → second tab → leave.
  - **Profile and settings edges:** private profile, hidden sections, guest profile, deleted account,
    unknown user, *Link Google account*, a username change, login `redirect`, and a keyboard Tab walk.
  - **Widths:** catalog and game detail at 1280, 1440 and 1920 px.
- **Server side:** Prometheus targets and rules, the Grafana datasource health API, Loki volume per
  container, Tempo search, and the platform/game-host `ERROR`/`WARN` lines.
- **Allowance spent:** one registration (the deleted-account probe) and no new guest; the cached guest
  cookie was reused.

## Status of the 2026-10-03 findings

| ID | Finding | Now | Evidence |
|---|---|---|---|
| RR-01 | Profile and Settings return 500 for seeded users | **Closed** | `/users/alice`, `/users/carol` and `/settings` render for each seeded user, as themselves and as one another; no `5xx` in the tour |
| RR-02 | Friends list 500 | **Closed** | `/friends` lists friends and incoming requests; no toast, no `5xx` |
| RR-03 | Forfeit writes no history | **Closed** | After `leave2`, alice's history has a *Victory* row. The opponent's *game over* arrives 3.6 s after the leave — **CA-05** |
| RR-04 | Rooms emptied around a game end never close | **Closed** | About a dozen games by driver, suite and probes, each ending with every socket closing at once: `GET /api/rooms` afterwards is empty |
| RR-05 | `/rooms/{id}` enrols the visitor silently | **Closed** | Outsider dave on `/rooms/{id}` gets the *Join as spectator* prompt (no free seat) and is not enrolled until he presses it |
| RR-06 | Create-room offers neither visibility nor spectating | **Closed** | The dialog's *Allow spectators* switch produced the room the spectator tour used |
| RR-07 | Header and tables break at 400 px | **Closed** | No route scrolls horizontally at 400 px for any tier; the header wraps cleanly |
| RR-08 | *Start game* enabled while the guest is not ready | **Closed** | Disabled, with the reason shown ("bob is not ready.", "The game needs at least 2 players; 1 joined.") |
| RR-09 | Numeric string accepted as a move | **Closed** | Covered by `IMP-M8-05`'s tests; not re-probed |
| RR-10 | Rate-limit message says "a moment" | **Closed** | Covered by the suite; not re-provoked, to keep the allowance |

## What was verified working

| Area | Result |
|---|---|
| Acceptance suite | `make e2e`: 45 of 45 green in 7.3 min on a fresh `make up` |
| Redirects and tiers | Every protected route sends an anonymous visitor to `/login?redirect=…`, and logging in lands on the original route (`/friends`). A guest is kept off registered-only routes. `/nope` is the 404 view. The Google button is hidden on login and register when the provider is unconfigured |
| Layout | No horizontal scroll on any of the 14 routes at 400 px or 1280 px, for any tier. The lobby, in-game and results views fit at 400 px; the game iframe is 352 px wide inside the viewport |
| Accessibility | axe-core: the room views (lobby host/player, in-game, results) have **no** violations. The only rule seen anywhere is `heading-order` (moderate) on `/rooms` — CA-09 |
| Room — lobby | The host sees *Start game* (disabled with reasons), *Share invite link* ("Invite link copied."), and per-row *Transfer host* / *Kick*. The player sees *Ready* and *Switch to spectator*. The spectator sees no chat box (`in-room-chat.md` FR-CHAN-004) and *Switch to player* only while a seat is free. Players, readiness and spectators update live on every client |
| Room — roles | Host transfer and transfer back both apply at once, on both clients. Kicking the spectator shows "The host removed you from this room." with a way out; the kicked user can re-enter through the prompt |
| Room — in game | Host keeps *Transfer host* and *Kick* (VW-RGAME-004/005); the spectator has the board and *Leave room* only; the outsider gets the spectator prompt |
| Room — results | The board stays mounted, with "The game is over.", *Return to lobby*, *Leave room*, and host *Kick* / *Transfer host* (VW-RRESULT-001…005). *Return to lobby* is per-client: the host returns while bob still sees the results |
| Reconnection | Mid-game reload: board back in **124 ms** with the correct marks and turn; the game completes. Browser back then forward mid-game: re-entered from a snapshot. A second tab for the same user shows the same room. `drop`: 60 s grace, resync returns the board |
| Chat | Room message from host reaches the player at once |
| Profiles | Private profile shows "This profile is private." to others and the full profile to its owner. Hidden sections disappear for others. A guest profile shows the username only (VW-PROF-004). A deleted account shows "This account no longer exists." (VW-PROF-005); an unknown user gets the 404 view |
| Settings | Username change applies (`GET /api/users/me` returns the new name). Account deletion → `204`, and the profile then reads as deleted |
| Keyboard | Tab order on `/games` runs logo → nav → notifications → account menu → search and filters → table → row link → *Show description* → *Create room*, each with a visible focus outline. Astryx text inputs show `outline: none`, but that was not examined further |
| Game | Spectator action → `ROLE_NOT_ELIGIBLE`; the outsider receives 0 frames on the room and game topics. Win on the fifth move |
| Server logs | **0 `ERROR` lines** in platform and game host over the whole run. The only `WARN`s are the two `DB: extension … already exists` lines at boot |
| Observability | Prometheus `platform` and `gamehost` targets `up`, 2 rule groups / 3 rules, no alert firing. Grafana's Loki, Prometheus and Tempo datasources all report healthy. Dashboards *Platform Overview* and *JVM and Database* are provisioned. Loki holds lines from all 12 containers; Tempo holds platform traces (STOMP `SEND`, SSE stream, SQL spans) |

## Performance (local, one machine)

| Measurement | Result |
|---|---|
| `START_GAME` → `GAME_STARTED`, warm (after the suite) | 19–23 ms |
| Move → `GAME_EVENT` at the spectator, warm | 9–14 ms |
| Mid-game page reload → board rendered | 124 ms |
| Explicit leave → `PLAYER_LEFT` at the opponent | 8 ms |
| Explicit leave → `GAME_OVER` / `GAME_ENDED` at the opponent | **≈ 3.6 s** — CA-05 |
| Cold boot to healthy (`make up`) | 36.7 s |
| Resting memory | platform 944 MiB, game host 1.17 GiB, frontend 14 MiB |
| Resting CPU | all under 0.2 % |

No concurrent-game load was run.

## Findings

Severity:
- **High** — blocks a planned user-facing function.
- **Medium** — a behavioural defect or a visibly wrong result.
- **Low** — polish, a console warning, or a spec question.

### CA-01 — A host cannot invite friends to a room — **High**

VW-RLOBBY-005 (*Invite Friends* button, host only, hidden for a Guest host) is absent from the lobby.
The host's lobby offers *Start game*, *Share invite link* and *Leave room* and nothing else.

The rest of the feature is built:
- `room-invitation-rest-api.md`'s send and decline endpoints answer.
- The `ROOM_INVITATION` notification arrives live.
- The panel offers *Join* and *Decline* (VW-NOTIF-002).

So an invitation can be **received** but never **sent** from the product. The suite's
`notifications.spec.ts` sends one by `POST /api/rooms/{id}/invitations` directly. That is also why no
spec noticed.

The consequence reaches beyond one button. `FRIENDS_ONLY` and `INVITE_ONLY` rooms (both offered by the
create dialog since `IMP-M8-08`) can be entered only through a copied invite link.

`IMP-M8-10` lists VW-RLOBBY-001…017 under *Satisfies*, and its Done-when walks roles and states, not
rows. The row was never checked.

**Recommendation:** an *Invite friends* control for a registered host. It opens a picker over the
host's friends (`GET /api/users/{me}/friends`) and sends the invitation for the selected ones. Errors
come from `room-invitation-rest-api.md`'s documented `4xx`s. The suite should drive it from the UI and
assert the badge on the invitee's open page.

### CA-02 — Every profile's *Uploaded games* lists the whole catalog — **Medium**

`profileApi.ts` calls `GET /api/games?owner={username}`, as `catalog-rest-api.md` §3 specifies. The
platform's `CatalogController` takes only `search`, `minPlayers`, `maxPlayers` and `tags`. It silently
ignores `owner` and returns the unfiltered listing.

alice, bob, carol, and a username that does not exist all "uploaded" the official Tic-Tac-Toe. The
spec requires an empty page for the unknown name.

The parameter was added to the spec by IMP-GATE-80 (session 80, recorded under `IMP-M6-03`) for the
profile view. No backend item ever took the parameter on. The frontend unit tests mock the response,
and the e2e profile spec asserts the section heading, not its contents.

**Recommendation:** implement `owner` per §3, composing with §2's visibility predicate. That means
the owner's carve-out applies, and an unknown name gives an empty `content`, not a `404`. Add an
integration test over real PostgreSQL covering owner, non-owner and unknown name. Add an e2e assertion
that a seeded user's section is empty.

### CA-03 — Tic-Tac-Toe's results screen never says who won — **Medium**

The backend sends `Effects.gameOver(outcome, GameMessage.Result.of(winner, reason))`, and the platform
writes the right history row. The game frontend's `onGameOver(() => …)` drops the results argument,
and `statusLine` prints **"Game over."** for every outcome. Neither player is told whether they won,
lost or drew. The platform's banner says only "The game is over."

`game-contracts.md` FR-EFF-005 has the game FE "display results until dismissed". The reference game
is what third-party developers copy.

**Recommendation:** have the game FE render the results payload — "You won.", "You lost.", "Draw.",
"X won." for a spectator, and the forfeit case ("bob left — you win."). Assert it in the suite.

### CA-04 — The catalog's per-row *Create room* is clipped at desktop widths — **Medium**

The *Create room* button (VW-CAT-003) is laid out entirely past the table's right edge in `/games`,
inside a cell with `overflow: hidden`:

| Viewport | Button `left`…`right` | Table `right` |
|---|---|---|
| 1280 px | 1273…1376 | 1256 |
| 1920 px | 1842…1945 | 1896 |

At every desktop width a mouse user sees **no** *Create room* on the row. The way to create a room is
through the detail page. At 1280 px the badge also truncates to "Offi…", and the title link is styled
as plain text, so nothing on the row looks clickable.

At 400 px the row stacks and works. The *View standard* checks 400 px only, and Playwright scrolls and
clicks a clipped element without complaint. The game-detail page's *Create room* stretches to the full content
width.

**Recommendation:** give the actions column an intrinsic width (or the table `overflow-x: auto` per
the responsive rule), let the badge show its full label, and style the title as a link. Make the suite's
layout pass assert that every interactive element of each route lies inside the viewport at 1280 and
1920 px as well as 400 px.

### CA-05 — An explicit leave reaches the game engine only on the next 5 s sweep — **Medium**

`game-rooms.md` FR-LIFE-004 says a confirmed departure "notifies the game engine at once", and
`data-model.md` §4.2 describes an "inline attempt at detach time" with the sweep as the re-drive. The
platform does the following:
- writes the `player_left` row to `game_input_outbox`;
- broadcasts `PLAYER_LEFT` (8 ms);
- leaves delivery to `GraceDeadlineSweepJob` duty 4, which runs every `turnbase.jobs.deadline-sweep.interval` = **5 s**.

No inline dispatch exists. The opponent sees "bob left" and then waits up to 5 s (3.6 s measured) for
the game to end. In a game that does not end on a departure, the engine acts late on every leave or
kick.

**Recommendation:** after commit, attempt the dispatch inline, as §4.2 describes. Keep the sweep as the
retry path and keep the stamp-on-ACK rule. Bound the leave → `GAME_OVER` latency in the forfeit spec
(for example, under 1 s).

### CA-06 — *Link Google account* is offered when Google is not configured, and leads to raw JSON — **Low**

Settings shows *Link Google account* (VW-SET-004) on a stack with no Google client. Pressing it
navigates the whole tab to `/auth/google?intent=link`, which renders the problem document
`{"type":"https://turnbase.io/errors/not-found",…,"detail":"Google OAuth is not configured."}` as the
page. The user has to press Back.

Login and register hide their Google button by asking `GET /api/auth/providers`. Settings does not.
`oauth-rest-api.md`'s *Hidden when the client secret is absent* paragraph names VW-LOGIN-002 and
VW-REG-002 only, so the spec gap is real too.

**Recommendation:** extend that paragraph to VW-SET-004. Settings hides the link when
`google: false`, as the login page does.

### CA-07 — The four per-section privacy controls have no visible label — **Low**

Under *Privacy*, Settings renders four `SegmentedControl`s (*Public* / *Hidden*, and *Friends only*
for friends) one under another with nothing naming them. Astryx's `label` prop is
"used as aria-label, never rendered visually". Screen readers hear "Game history visibility"; a
sighted user sees four unnamed toggles (VW-SET-006a).

**Recommendation:** put a visible label beside each control (an Astryx field/label component or text
row), keeping the accessible name. Assert the visible text in the settings spec.

### CA-08 — A page reload in the Lobby is a leave, and for the host it gives up the room — **Low** (spec question)

As `reconnection-flow.md` FR-DC-002 specifies, a dropped socket in Lobby is an immediate leave. The
same applies to results, which is the Lobby state (FR-DC-004). So:
- a reload, a browser Back, or a flaky network in the lobby removes the player;
- bob's reload put him back at the *Join a room* prompt, and his seat was gone;
- for a **host** the same reload transfers the room to the next player, or closes it if they were alone
  (`game-rooms.md` FR-XFER-002).

`IMP-M8-10` records this as by design. It is the one place where the MVP punishes an ordinary browser
action, and players reload.

**Recommendation:** decide in the spec whether a short Lobby grace (a few seconds, no reservation
semantics beyond the seat) is wanted. The owner-pod carve-out (FR-DC-007) shows the rule already needed
one exception. If the answer is no, say so in the view: warn on `beforeunload` in the lobby.

### CA-09 — View polish: heading order, duplicated labels — **Low**

- **Heading order:** axe `heading-order` (moderate) on `/rooms`, where an `h3` follows the `h1` with no
  `h2`.
- **Bell:** the notification bell prints its accessible name as visible text: "Notifications, 1 unread"
  next to a badge that already says `1`.
- **Duplicated headings:**
  - *Friends* / *Friends*
  - *Your friends* ×2
  - *Uploaded games* ×2 on the profile
  - *Sign-in methods* ×2 in settings

  A heading, plus a list whose visible caption repeats it.
- **Toast:** "Invite link copied." is rendered twice (toast and live region both visible in the
  text).
- **Statistics:** VW-GDET-002 asks for a per-game statistics *tab*; the detail page shows it as a
  section. That is acceptable, but the row should then say so.

### CA-10 — A console warning from the game iframe on every game — **Low**

On every game, the host's page logs:

> `Failed to execute 'postMessage' on 'DOMWindow': The target origin provided
> ('http://turnbase.localhost:8080') does not match the recipient window's origin
> ('http://…games.localhost:8080')`

The SDK client posts to `window.parent` with the platform origin. The recipient being the game's own
window means the frame had no parent when it posted — consistent with the iframe being detached
(*Return to lobby*, or a remount) while the SDK still sends.

It is harmless. The message is dropped, by the exact-origin rule. But the *View standard* (point 2)
allows no console warning, and the suite's tripwire counts errors only.

**Recommendation:** find the posting site. If it is the SDK, it should not post when
`window.parent === window`. Consider counting warnings in the tripwire.

### CA-11 — Eight register rows still carry a session marker after `DONE` — **Low** (fixed in this round)

`IMP-M3-04`, `M3-05`, `M4-01`, `M4-05`, `M6-02`, `M6-06`, `M7-01` and `M8-14` read `DONE (session N)`.
`implementation/INDEX.md`'s transition table drops the marker at `DONE`. Fixed in the same commit as
this report.

## Not covered

- Concurrent-game load, soak, and the 4-hour room expiry.
- Team chat and the *Write channel* switcher: no seeded game declares teams.
- AI players (VW-RLOBBY-007) and editing game parameters (VW-RLOBBY-010): Tic-Tac-Toe declares neither.
- Google OAuth sign-in and linking with a configured provider, and guest-to-registered conversion.
- User-uploaded games and the admin surface.
- Rooms list filters and sorting, and catalog search, beyond what the suite already asserts.
- Screen-reader walk-throughs. The keyboard pass covered `/games` only.
- The Tempo platform → game-host span link, and Grafana panel contents beyond provisioning.

## Run-hygiene notes

- The stack is **still running** (`make up`, observability overlay included).
  `turnbase-platform/deploy/compose/.env` is git-ignored; its Grafana password is the
  `.env.example` default.
- One account (`audit47595x`) was registered and then deleted through the API. A probe changed carol's
  privacy settings and restored them. dave was logged in by the API at the end, which ends his
  browser sessions.
- The probes lived in `turnbase-frontend/e2e-audit/` and the session scratch directory, and were
  deleted afterwards. No submodule was changed.
