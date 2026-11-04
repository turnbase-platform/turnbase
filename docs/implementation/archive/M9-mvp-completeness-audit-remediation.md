# Archive — M9 MVP completeness audit remediation

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim by `IMP-M20-01`. Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M9-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M9-01 | Invite friends from the room lobby | frontend | M8-10, M8-12, M9-10 | DONE |
| IMP-M9-02 | The catalog listing honours `owner` | platform | M4-01 | DONE |
| IMP-M9-03 | Tic-Tac-Toe shows the outcome | game | M8-05 | DONE |
| IMP-M9-04 | Catalog rows keep their actions at desktop widths | frontend | M8-08 | DONE |
| IMP-M9-05 | A voluntary leave reaches the engine at once | platform | M7-06, M8-03 | DONE |
| IMP-M9-06 | Settings: Google linking and privacy labels | frontend, platform | M8-13 | DONE |
| IMP-M9-07 | Decide what a Lobby reload means | docs | — | DONE |
| IMP-M9-08 | View polish and the game-frame console warning | frontend, sdk | M8-16 | DONE |
| IMP-M9-09 | The acceptance suite covers the audit's gaps | frontend | M9-01…06, M9-08, M9-10 | DONE |
| IMP-M9-10 | A member and an invitee can open an `INVITE_ONLY` room | platform | M2-09 | DONE |
| IMP-M9-11 | Warn before a reload leaves the Lobby | frontend | M8-10, M9-07 | DONE |

---

## M9 — MVP completeness audit remediation

Opened 2026-10-04 from the [MVP completeness audit](../../reviews/2026-10-04-mvp-completeness-audit/INDEX.md)
(`CA-01…CA-11`; CA-11 was fixed in the audit's own commit). M8 gave every view a minimal working UI and
the audit found the views sound, so this milestone is short:

- **Two planned functions a player still cannot reach.** Inviting friends (`IMP-M9-01`) and a
  profile's uploaded games (`IMP-M9-02`).
- **One visibly wrong result.** The reference game never names the winner (`IMP-M9-03`).
- **One action invisible at every desktop width** (`IMP-M9-04`).
- **One late dispatch** (`IMP-M9-05`).
- **The settings gaps** (`IMP-M9-06`).
- **One spec decision** (`IMP-M9-07`), and the warning it implies (`IMP-M9-11`).
- **Polish** (`IMP-M9-08`).
- **The suite that pins all of it** (`IMP-M9-09`).

**What the audit taught about Done-when clauses.** Three of the findings were already covered by an
M8 item's *Satisfies* list, yet that item reached `DONE` with the gap still open:

- CA-01 — VW-RLOBBY-005, under `IMP-M8-10`.
- CA-02 — VW-PROF-002c, under `IMP-M8-11`.
- CA-04 — VW-CAT-003, under `IMP-M8-08`.

Each slipped because the spec asserted a *heading* or a *role* rather than the *row*, or checked one
width only. The *View standard* still applies to every frontend item below. Each of them must also
assert the specific row it closes **by its visible text and its effect**, not by the presence of a
container.

---

### IMP-M9-01 — Invite friends from the room lobby

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M8-10, IMP-M8-12, IMP-M9-10 · **Closes:** CA-01

**Read first:**
- `docs/reviews/2026-10-04-mvp-completeness-audit/INDEX.md` CA-01
- `docs/requirements/platform-views.md` *Room — Lobby* (VW-RLOBBY-005 and the note under the table)
- `docs/specs/api-design/room-invitation-rest-api.md`
- `docs/specs/api-design/social-rest-api.md` — `GET /api/users/{username}/friends`
- `docs/requirements/notifications-invitations.md` (room invitation requirements)

**Satisfies:** `platform-views.md` VW-RLOBBY-005

**Done when:**
- **Who sees it.** A registered host's lobby shows *Invite friends*. A Guest host, a non-host player and
  a spectator do not see it (hidden, not disabled).
- **The picker.** It opens over the host's friends and sends the invitation for each one selected, with
  the API's documented `4xx`s rendered as messages.
- **No friends.** A host with no friends gets an empty state that says so.
- **End to end.** The invitee's open page shows the notification, and *Join* enters the room.
- **The rooms that need it.** It works for a `FRIENDS_ONLY` and an `INVITE_ONLY` room.
- **Tests.** A Playwright spec drives all of the above from the UI, and `notifications.spec.ts` no longer
  sends the invitation over REST.

**Closed:** IMP-GATE-96 (opened and closed 2026-10-04, session 150) — `room-rest-api.md` §3 gave one `visible()` predicate to both the listing and direct access, and it hides every `INVITE_ONLY` room, so its host re-entering it and an invitee pressing *Join* both got `404`. §3 now defines `reachable()` (visible, or a current participant, or holding a pending invitation) for §4 and §5 step 1. The platform follows in `IMP-M9-10`.


---

### IMP-M9-02 — The catalog listing honours `owner`

**Repo:** `turnbase-platform` · **Depends on:** IMP-M4-01 · **Closes:** CA-02

**Read first:**
- `docs/reviews/2026-10-04-mvp-completeness-audit/INDEX.md` CA-02
- `docs/specs/api-design/catalog-rest-api.md` §2, §3 (`owner`), §6
- `docs/specs/platform/data-model-catalog.md` §1
- `docs/requirements/game-catalog.md` FR-UPROF-001…004

**Satisfies:** `game-catalog.md` FR-UPROF-001, FR-UPROF-003; `platform-views.md` VW-PROF-002c

**Done when:** `GET /api/games?owner={username}` restricts to that user's games:

- **Visibility.** The filter composes with §2's visibility predicate. The owner sees their own unlisted
  and Unverified games; another caller, anonymous included, sees only listed, non-Unverified ones.
- **Unknown user.** An unknown username yields `200` with an empty `content`, not `404`.
- **Platform-authored games.** A game with a null owner matches no username.
- **Integration test over real PostgreSQL.** It covers the owner, a non-owner, an anonymous caller and an
  unknown name.
- **The profile.** A seeded user's profile shows an empty *Uploaded games* section, and the frontend's
  profile spec asserts it by content, not by heading.

---

### IMP-M9-03 — Tic-Tac-Toe shows the outcome

**Repo:** `turnbase-game-tictactoe` · **Depends on:** IMP-M8-05 · **Closes:** CA-03

**Read first:**
- `docs/reviews/2026-10-04-mvp-completeness-audit/INDEX.md` CA-03
- `docs/requirements/game-contracts.md` FR-EFF-005, FR-OUTCOME-*
- `docs/specs/gdk-api/INDEX.md` → the TypeScript client (`onGameOver`)
- `turnbase-game-tictactoe/src/main/java/io/turnbase/games/tictactoe/GameMessage.java` (`Result`)

**Satisfies:** `game-contracts.md` FR-EFF-005 (the game FE displays results)

**Done when:**
- **The handler.** `onGameOver` reads the results payload instead of discarding it.
- **What a player sees.** "You won." / "You lost." / "Draw.".
- **What a spectator sees.** "X won." / "O won." / "Draw.".
- **Forfeit and timeout.** The winner also sees the reason, e.g. "Your opponent left — you win.".
- **Tests.** Unit tests cover every case of the results reducer. The bundle is re-seeded, and the
  frontend's game spec asserts the winner's and the loser's text.

---

### IMP-M9-04 — Catalog rows keep their actions at desktop widths

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M8-08 · **Closes:** CA-04

**Read first:**
- `docs/reviews/2026-10-04-mvp-completeness-audit/INDEX.md` CA-04
- `docs/requirements/platform-views.md` *Game Catalog* (VW-CAT-001…003)
- `docs/specs/platform-frontend/design-system.md`

**Satisfies:** `platform-views.md` VW-CAT-002, VW-CAT-003

**Done when:**
- **The button fits.** At 1280, 1440 and 1920 px each row's *Create room* lies wholly inside its table
  cell and the viewport, and is clickable without scrolling.
- **Nothing is cut.** The badge shows its full label.
- **The title reads as a link.** It is styled as one.
- **Game detail.** The page's *Create room* is not stretched to the content width.
- **400 px.** The layout stays as it is today.
- **Tests.** The layout spec asserts the first three at all three widths, by bounding box rather than by
  `toBeVisible`.

---

### IMP-M9-05 — A voluntary leave reaches the engine at once

**Repo:** `turnbase-platform` · **Depends on:** IMP-M7-06, IMP-M8-03 · **Closes:** CA-05

**Read first:**
- `docs/reviews/2026-10-04-mvp-completeness-audit/INDEX.md` CA-05
- `docs/specs/platform/data-model.md` §4.2 (`game_input_outbox`, the inline attempt, stamp-on-ACK, the teardown rule)
- `docs/requirements/game-rooms.md` FR-LIFE-004
- `docs/requirements/reconnection-flow.md` FR-DC-005, FR-KICK-*
- `docs/implementation/registry.md` IMP-M3-09 *Built* (the drain)

**Satisfies:** `game-rooms.md` FR-LIFE-004; `reconnection-flow.md` FR-DC-005

**Done when:**
- **Inline dispatch.** After the transaction that writes a `player_left` row commits — an explicit leave,
  an abandonment confirmation, a kick, or an account deletion — the platform attempts the dispatch once,
  inline.
- **The sweep stays.** The deadline sweep remains the retry path.
- **Same rules as before.**
  - `dispatched_at` is stamped on ACK only.
  - The teardown discard still wins.
  - A failed inline attempt records `attempts`/`last_error` exactly as the sweep does.
- **Integration test.** It shows the engine receives the input without waiting for a sweep tick.
- **Latency.** The forfeit scenario asserts leave → `GAME_OVER` at the opponent in under 1 s.

**Built (session 158):** `GameInputOutbox` owns one row's attempt (allocate-once sequence, stamp on ACK, `attempts`/`last_error` on failure); the sweep's duty 4 and a `@TransactionalEventListener(AFTER_COMMIT)` both call it. `RoomRepository.insertPlayerLeftOutbox` publishes `PlayerLeftQueued` for leave, abandonment (incl. early release), kick and account deletion. The grace-expiry insert does **not**: duty 2 may close the room in the same tick and discard the row, so it stays on the sweep (§5.1 ordering). `InlineLeaveDispatchIT` covers delivery with no sweep and failure-then-sweep-retry on the same sequence. The 1 s bound is `resilience.spec.ts`'s forfeit test (frontend). Operational note: after `down -v`, the first Game Host session needs a ~30 s wait or `CreateSession` exceeds its 35 s deadline; platform ITs that bind :8080 fail while the compose stack is up.

---

### IMP-M9-06 — Settings: Google linking and privacy labels

**Repo:** `turnbase-frontend` (spec edit in this repository) · **Depends on:** IMP-M8-13 · **Closes:** CA-06, CA-07

**Read first:**
- `docs/reviews/2026-10-04-mvp-completeness-audit/INDEX.md` CA-06, CA-07
- `docs/specs/api-design/oauth-rest-api.md` *Hidden when the client secret is absent*, `GET /api/auth/providers`, §7a
- `docs/requirements/platform-views.md` *Account Settings* (VW-SET-004, VW-SET-006, VW-SET-006a)

**Satisfies:** `platform-views.md` VW-SET-004, VW-SET-006a

**Done when:**
- **Spec first.** `oauth-rest-api.md`'s *Hidden when* paragraph names VW-SET-004 alongside VW-LOGIN-002
  and VW-REG-002 (a `spec-defect` edit, first).
- **Hidden when unconfigured.** Settings asks `GET /api/auth/providers` and does not render *Link Google
  account* when `google` is `false`.
- **Each control is named on screen.** The four per-section visibility controls each carry a visible
  label naming the section, and keep their accessible names.
- **Tests.**
  - The settings spec asserts the link is absent on the unconfigured compose stack.
  - The same spec asserts the four labels by visible text.

---

### IMP-M9-07 — Decide what a Lobby reload means

**Repo:** `turnbase` (documentation only) · **Depends on:** — · **Closes:** CA-08

**Read first:**
- `docs/reviews/2026-10-04-mvp-completeness-audit/INDEX.md` CA-08
- `docs/requirements/reconnection-flow.md` FR-DC-001…007
- `docs/requirements/game-rooms.md` FR-XFER-001, FR-XFER-002, FR-LIFE-004
- `docs/decisions/0008-room-ownership-lifecycle.md`

**Done when:** `reconnection-flow.md` records a decision, with its rationale, on what an individual
player's socket loss in Lobby (and in the results overlay, FR-DC-004) means. Either outcome closes the
item:

- **A short Lobby grace.** Specify its length and what happens to the host role and to readiness during
  it, and open the platform and frontend work item it implies, in the register.
- **Immediate leave stays.** Write that down together with the user-facing mitigation — for example a
  `beforeunload` warning in the lobby — and open its frontend item.

`check-corpus.py` is clean.

---

### IMP-M9-08 — View polish and the game-frame console warning

**Repo:** `turnbase-frontend`, `turnbase-sdk` (if the warning is the SDK's) · **Depends on:** IMP-M8-16 · **Closes:** CA-09, CA-10

**Read first:**
- `docs/reviews/2026-10-04-mvp-completeness-audit/INDEX.md` CA-09, CA-10
- `docs/specs/platform-frontend/design-system.md`
- `docs/specs/api-design/websocket.md` § *Platform-shell* relay (the exact-origin rule)
- `turnbase-sdk/src/main/ts/client.ts` (`window.parent.postMessage`)

**Satisfies:** `platform-views.md` VW-NAV-*, VW-ROOMS-001, VW-GDET-002 (presentation only)

**Done when:**
- **Accessibility.** axe-core reports no violation on any route for any tier — `/rooms`' `heading-order`
  included.
- **The bell.** It shows its count once; the accessible name stays, but is not printed as visible text.
- **Headings.** No section repeats its heading as a visible list caption (friends, uploaded games,
  sign-in methods).
- **The toast.** A copied invite link announces once.
- **VW-GDET-002.** It is either built as a tab, or the row is amended to say *section* (`spec-defect`).
- **The console warning.** The `postMessage` origin warning is gone: its posting site is found, and the
  sender does not post when it has no parent.
- **The tripwire.** `e2e/fixtures.ts` counts console warnings as well as errors, with the existing
  allow-list mechanism.

---

### IMP-M9-09 — The acceptance suite covers the audit's gaps

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M9-01…06, IMP-M9-08, IMP-M9-10

**Read first:**
- `docs/reviews/2026-10-04-mvp-completeness-audit/INDEX.md` — *What was verified working* and *Not covered*
- `docs/implementation/registry.md` IMP-M8-16 and the M9 preamble

**Done when:** `make e2e` additionally asserts:

- **Room invitations from the UI.**
  - Invite friends → notification → *Join* (IMP-M9-01).
  - The same for a `FRIENDS_ONLY` room.
- **Uploaded games.** Empty for a seeded user (IMP-M9-02).
- **The outcome.** The winner's and the loser's results text (IMP-M9-03).
- **Desktop layout.** A layout pass at 1280 and 1920 px asserting every interactive element of every
  route lies inside the viewport (IMP-M9-04).
- **Forfeit latency.** Leave → game over in under 1 s (IMP-M9-05).
- **Settings.** The two assertions of IMP-M9-06.
- **axe-core.** A pass with zero violations over every route, tier and room state, the room states
  included.

A clean `make up` followed by the suite is green twice in a row within the documented allowance.

**Delivered (session 163):** `e2e/sweep.spec.ts` — every route of `routes.tsx` for the anonymous, guest and registered tiers, plus the Lobby (host alone, host, player, spectator), in-game and results states, each asserting every interactive element inside the viewport and its clipping ancestors at 1280 and 1920 px, and zero axe-core 4.10.3 violations (the sandboxed game frame is left out of axe). It found one more clipped control — *Show description*, 9 px past its cell at 1280 px — fixed with a min-width on the catalog's title and Actions columns. The other bullets were already pinned by `IMP-M9-01…06`'s own specs. 52 of 52, twice in a row on a clean `make up` (a cold game host wedged on its first Espresso context; restart it and wait for the first game before the run).

---

### IMP-M9-10 — A member and an invitee can open an `INVITE_ONLY` room

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-09 · **Closes:** IMP-GATE-96

No dependency on `IMP-M9-01`: that item found the defect and is itself `PARTIAL` until this one lands (a dependency the other way would be a cycle — corrected session 151).

**Read first:**
- `docs/specs/api-design/room-rest-api.md` §3 (`reachable()`), §4, §5 step 1
- `docs/specs/api-design/room-invitation-rest-api.md` §2, §4

**Done when:**
- **A member re-enters.** `POST /api/rooms/{id}/participants` by a current participant of an
  `INVITE_ONLY` room, with no `inviteCode`, is the idempotent `201` of §5 step 2, not `404`; `GET
  /api/rooms/{id}` answers `200` with `viewerRole`.
- **An invitee joins.** A caller holding a pending invitation to an `INVITE_ONLY` room reads it (`200`) and
  joins it with no `inviteCode`; the invitation is then resolved as `room-invitation-rest-api.md` §4 says.
- **Nothing else opens.** Another caller without an `inviteCode` still gets `404` on both routes, and the
  listing (FR-LIST-007) is unchanged.
- **Tests.** An integration test per bullet above.

---

### IMP-M9-11 — Warn before a reload leaves the Lobby

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M8-10, IMP-M9-07 · **Closes:** CA-08

**Read first:**
- `docs/requirements/reconnection-flow.md` FR-DC-008
- `docs/requirements/game-rooms.md` FR-JOIN-008–010

**Done when:**
- **The warning.** While the viewer is a participant (not a spectator) of a room in Lobby, or sees the
  results overlay, a `beforeunload` handler is registered: a reload or tab close prompts the browser's
  confirmation.
- **Removed on leave.** After an explicit *Leave Room*, or once the viewer is not a participant, or in
  an In Progress room, no handler is registered.
- **Tests.** A unit test per bullet; an e2e asserting the `beforeunload` dialog appears on reload in
  Lobby and not after *Leave Room*.

---
