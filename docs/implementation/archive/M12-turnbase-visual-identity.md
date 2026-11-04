# Archive — M12 TurnBase visual identity

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim by `IMP-M20-01`. Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M12-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M12-01 | The corpus describes the TurnBase visual identity | docs | — | DONE |
| IMP-M12-02 | The TurnBase theme is built, themed and switchable | frontend | M12-01 | DONE |
| IMP-M12-03 | The shared `src/ui/` presentation layer | frontend | M12-02 | DONE |
| IMP-M12-04 | Shell, landing and auth views carry the identity | frontend | M12-03 | DONE |
| IMP-M12-05 | Catalog and game detail: hook plus presentational view | frontend | M12-03 | DONE |
| IMP-M12-06 | Rooms list and join-by-code: hook plus presentational view | frontend | M12-03 | DONE |
| IMP-M12-07 | The room (lobby, chat, participants, game, result) | frontend | M12-03, M12-06 | DONE |
| IMP-M12-08 | Profile, history and statistics | frontend | M12-03 | DONE |
| IMP-M12-09 | Friends and notifications | frontend | M12-03 | DONE |
| IMP-M12-10 | Settings | frontend | M12-03 | DONE |
| IMP-M12-11 | The acceptance sweeps pass in both appearances | frontend, docs | M12-04…10 | DONE |

---

## M12 — TurnBase visual identity

Opened 2026-10-11 by [ADR-0017](../../decisions/0017-turnbase-visual-identity.md), which reverses
ADR-0013 §4: the platform takes its own look — deep-space arcade, Light / Dark / Auto, Pixelify Sans
and Figtree, fake glass — as a custom Astryx theme plus a tested `src/ui/` layer. A clickable
prototype was reviewed and approved as a private artifact on 2026-10-11; it is **evidence of the
look, not code to port** (ADR-0017 *Context*).

**How M12 differs from every other frontend milestone — read before claiming any item:**

- **Services are not touched.** `roomsApi`, `roomSocket`, `roomReducer`, `useRoomConnection`,
  `gameRelay`, `shared/api`, `AuthProvider` and `notificationStream` keep their contracts. A real
  defect found in one is a `spec-defect` or a separate fix, not a restyle side effect.
- **Hook plus presentational component per view.** The hook calls the existing modules; the component
  takes plain props and imports no API module (`design-system.md` §4).
- **Behaviour is held by the existing tests.** A view's current `*.test.tsx` must pass with its
  assertions unchanged except for markup the redesign removes; new hooks and `ui/` components are
  written test-first. Coverage stays at or above the repository threshold.
- **Follow the specification, not the prototype's sample data** (ADR-0017 §4): no presence, no
  invented endpoints, no dock.
- **Lint stays strict.** No new exemption: colours are written only in `src/theme/palette.ts`, the
  generated theme build is ignored as machine output, and spacing has none.
- **Both appearances.** Anything visual is checked in Light and Dark, at 400 px and at desktop width,
  with `prefers-reduced-motion` honoured.

### IMP-M12-01 — The corpus describes the TurnBase visual identity

**Repo:** `turnbase` (docs) · **Depends on:** —

**Read first:**
- `docs/decisions/0017-turnbase-visual-identity.md`
- `docs/decisions/0013-astryx-design-system.md`

**Satisfies:** `platform-ui-library.md` FR-TOK-001, FR-TOK-005, FR-TOK-007, FR-TOK-008, FR-THM-001

**Done when:**
- **Decided.** ADR-0017 is `Accepted`, ADR-0013 §4 is marked superseded, and `docs/decisions/INDEX.md`
  lists it.
- **Cascaded.** `platform-ui-library.md`, `design-system.md`, `shell-architecture.md`, both
  `CLAUDE.md` files and the milestone map describe the identity, the built theme, `src/theme/`, the
  `--tb-*` tokens, the palette table and the hook-plus-view split.
- **Registered.** This milestone and its items exist; `python3 scripts/check-corpus.py` is clean.

### IMP-M12-02 — The TurnBase theme is built, themed and switchable

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M12-01

**Read first:**
- `docs/decisions/0017-turnbase-visual-identity.md` (§1, §2)
- `docs/specs/platform-frontend/design-system.md` (§2, §5, §6)
- `docs/specs/platform-frontend/shell-architecture.md` (§2, §6)
- `docs/requirements/platform-ui-library.md` (FR-TOK, FR-THM, CON-004, CON-005)

**Satisfies:** `platform-ui-library.md` FR-TOK-001, FR-TOK-005, FR-TOK-007, FR-TOK-008, FR-THM-001, FR-THM-002, CON-004, CON-005

**Done when:**
- **A built theme.** `src/theme/turnbase.theme.ts` extends `neutralTheme` with the palette (light and
  dark), radius 8/12/18/28, shadows, fonts and component overrides; `astryx theme build` output
  (`.css`, `.js`, `.d.ts`) is committed with `__built: true`; no `<style>` is injected at runtime and
  the shell CSP is unchanged.
- **Drift and build.** `npm run build` runs the theme build first; a unit test fails when the committed
  output differs from a fresh build.
- **Own tokens and fonts.** `src/theme/palette.ts` holds every colour as a `[light, dark]` pair, built
  into the theme as `light-dark()` values (`--tb-*` additions redefine no Astryx property);
  `src/theme/tokens.css` holds the non-colour `--tb-*` tokens; Figtree and Pixelify Sans are self-hosted at exact pins and
  only the weights used; `font-src 'self'` is not widened.
- **Lint.** `no-raw-color-*` and `no-raw-spacing-css` are unchanged; the generated theme build is
  ignored by lint and Prettier, and a rule test shows a hand-written stylesheet in `src/theme/`
  still fails.
- **Appearance.** A provider holds `light | dark | system` (default `system`), persists it in
  `localStorage` behind try/catch, and drives `<Theme mode>`; a control in the shell switches it and
  is keyboard-operable and labelled.
- **Contrast.** A unit test computes the contrast of every text/background token pair in both
  appearances and fails below WCAG AA.
- **Tests.** The provider, the persistence fallback and the control are tested; existing suites stay
  green.

### IMP-M12-03 — The shared `src/ui/` presentation layer

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M12-02

**Read first:**
- `docs/decisions/0017-turnbase-visual-identity.md` (§3)
- `docs/specs/platform-frontend/design-system.md` (§3, §4, §5)
- `docs/specs/api-design/pagination-filtering-sorting.md`

**Satisfies:** `platform-ui-library.md` FR-TOK-005, FR-TOK-007, FR-COMP-003, NFR-PERF-002

**Done when:**
- **The layer.** `src/ui/index.ts` exports the pointer-effect delegation (spotlight and tilt),
  `Starfield`, `Logo`, the pixel-art and icon set, `PillTabs`, a directional pane transition, and the list-query kit: `ScrollPanel` (a border and nothing else),
  `FilterPanel`, `FilterButton`, `SortControl`, `PageBar`. There is no `Person`: Astryx `Avatar` already
  shows initials from `name` and a status dot only when given `status`, so a wrapper would only rename
  it (ADR-0017 §3); views pass `name` and never `status`.
- **Controlled and honest.** `PageBar` and `SortControl` are controlled over the API's `page`, `size`
  and `sort=field,dir`; they never slice or sort data themselves.
- **Motion budget.** Every effect is disabled under `prefers-reduced-motion`; `Starfield` is one
  canvas that pauses while the tab is hidden and is static when reduced.
- **Boundaries.** The two import rules of `design-system.md` §4 hold; each component has a CSS Module
  and a unit test written first, including keyboard operation and accessible names.

### IMP-M12-04 — Shell, landing and auth views carry the identity

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M12-03

**Read first:**
- `docs/decisions/0017-turnbase-visual-identity.md`
- `docs/specs/platform-frontend/shell-architecture.md` (§2, §3)
- `docs/requirements/platform-views.md` (landing, navigation and auth views)

**Satisfies:** `platform-ui-library.md` FR-THM-001

**Done when:**
- **Shell.** The navigation bar, landing page, login, register, OAuth completion and guest entry use
  the identity; the navigation tiers, the route guards and every existing label and role are
  unchanged; the Light / Dark / Auto control is present.
- **Split.** Each form with data logic has a hook and a presentational component; `AuthProvider` is
  untouched.
- **Tests.** The existing tests pass; new hooks have tests; the e2e selectors the markup changed are
  updated.

### IMP-M12-05 — Catalog and game detail: hook plus presentational view

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M12-03

**Read first:**
- `docs/decisions/0017-turnbase-visual-identity.md` (§3, §4)
- `docs/specs/api-design/catalog-rest-api.md`
- `docs/specs/api-design/pagination-filtering-sorting.md`
- `docs/requirements/platform-views.md` (catalog and game-detail views)

**Satisfies:** `platform-ui-library.md` FR-COMP-003

**Done when:**
- **Hook.** `useCatalog` owns the query (search, filters, sort, page) against the existing catalog
  API and returns plain data; the view renders it with the list-query kit and never filters or sorts
  a fetched page.
- **Detail and create-room.** The game detail and the create-room action carry the identity with their
  behaviour unchanged.
- **Tests.** The hook is tested with the API module faked; the view with literals; existing tests and
  the catalog e2e pass.

### IMP-M12-06 — Rooms list and join-by-code: hook plus presentational view

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M12-03

**Read first:**
- `docs/decisions/0017-turnbase-visual-identity.md` (§3, §4)
- `docs/specs/api-design/room-rest-api.md`
- `docs/specs/api-design/pagination-filtering-sorting.md`
- `docs/requirements/platform-views.md` (rooms views)

**Satisfies:** `platform-ui-library.md` FR-COMP-003

**Done when:**
- **Hook.** `useRooms` owns load state, paging, sort and the status filter with the current defaults
  and sort fields; `RoomsPage` becomes presentational. The join-by-code flow is split the same way.
- **Layout.** A one-line header, a query row of equal-height controls and an internally scrolling
  list in a plain bordered container, as approved in the prototype.
- **No invented data.** An "Invites" column exists only if a real source already carries it.
- **Tests.** As `IMP-M12-05`.

### IMP-M12-07 — The room (lobby, chat, participants, game, result)

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M12-03, IMP-M12-06

**Read first:**
- `docs/decisions/0017-turnbase-visual-identity.md`
- `docs/specs/platform-frontend/shell-architecture.md` (§4, §5)
- `docs/requirements/platform-views.md` (room views)

**Satisfies:** `platform-ui-library.md` FR-COMP-003

**Done when:**
- **Presentation only.** `RoomPage`, `RoomLobby`, `RoomGame`, `ChatPanel`, `ParticipantPanel`,
  `InviteFriendsButton` and `GameFrame` carry the identity; `useRoomConnection`, `roomReducer`,
  `roomSocket` and `gameRelay` are unmodified, and the iframe sandbox, the attach order and the
  `postMessage` checks are exactly as specified.
- **Split.** Any data logic still in these components moves into hooks.
- **Tests.** Existing tests and the room e2e pass; the reconnect and version-gap behaviour is not
  re-implemented.

### IMP-M12-08 — Profile, history and statistics

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M12-03

**Read first:**
- `docs/decisions/0017-turnbase-visual-identity.md`
- `docs/specs/api-design/profile-rest-api.md`
- `docs/specs/api-design/history-rest-api.md`
- `docs/requirements/platform-views.md` (profile views)

**Satisfies:** `platform-ui-library.md` FR-COMP-003

**Done when:**
- **Hooks.** The profile, its history list (paged, server-side) and its statistics each have a hook;
  the views are presentational and use the identity. No presence indicator is shown.
- **Tests.** As `IMP-M12-05`.

### IMP-M12-09 — Friends and notifications

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M12-03

**Read first:**
- `docs/decisions/0017-turnbase-visual-identity.md` (§4)
- `docs/specs/api-design/social-rest-api.md`
- `docs/specs/api-design/notification-rest-api.md`
- `docs/specs/api-design/sse-notifications.md`

**Satisfies:** `platform-ui-library.md` FR-COMP-003

**Done when:**
- **Friends.** One list plus Requests (no Online / In a game / Offline groups); add, accept, decline,
  remove and invite keep their behaviour, with a hook and a presentational view.
- **Notifications.** The bell and panel carry the identity; `notificationStream` is unmodified.
- **Tests.** As `IMP-M12-05`.

### IMP-M12-10 — Settings

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M12-03

**Read first:**
- `docs/decisions/0017-turnbase-visual-identity.md`
- `docs/specs/api-design/profile-rest-api.md`
- `docs/requirements/platform-views.md` (settings view)

**Satisfies:** `platform-ui-library.md` FR-THM-001

**Done when:**
- **Split.** The 600-line settings page is divided into a section per tab, each a hook plus a
  presentational component, with every existing action (profile, email change, password, privacy,
  deletion with re-authentication) unchanged.
- **Appearance.** The Appearance section exposes Light / Dark / Auto, the cursor-effects switch and
  the Reduced-motion setting, persisted locally and never sent to the server.
- **Tests.** As `IMP-M12-05`.

### IMP-M12-11 — The acceptance sweeps pass in both appearances

**Repo:** `turnbase-frontend`, `turnbase` · **Depends on:** IMP-M12-04, IMP-M12-05, IMP-M12-06, IMP-M12-07, IMP-M12-08, IMP-M12-09, IMP-M12-10

**Read first:**
- `docs/decisions/0017-turnbase-visual-identity.md` (*Consequences*)
- `docs/specs/platform-frontend/design-system.md` (§6)

**Satisfies:** `platform-ui-library.md` FR-THM-001, NFR-PERF-002

**Done when:**
- **Suites.** `make e2e` and the axe sweep pass in Light and in Dark; the 400 px and desktop layout
  checks pass; the console tripwire stays clean.
- **Reduced motion.** With `prefers-reduced-motion` the starfield is static and no pointer effect runs.
- **Docs.** Anything the build contradicted in `design-system.md` or ADR-0017 is corrected; STATUS and
  both `CLAUDE.md` files name M12 as closed.
