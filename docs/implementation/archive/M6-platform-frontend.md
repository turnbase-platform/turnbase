# Archive — M6 Platform frontend

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim by `IMP-M20-01`. Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M6-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M6-01 | Astryx integration and the `ui/` boundary | frontend | M0-05 | DONE |
| IMP-M6-02 | Shell, routing and auth tiers | frontend, platform | M6-01 | DONE |
| IMP-M6-03 | Account and profile views | frontend | M6-02, M1-07, M1-11 | DONE |
| IMP-M6-04 | Room views and the STOMP client | frontend | M6-02, M2-08 | DONE |
| IMP-M6-05 | Game iframe host and postMessage relay | frontend | M6-04, M3-07 | DONE |
| IMP-M6-06 | Catalog and history views | frontend | M6-02, M4-01, M5-01 | DONE |
| ~~IMP-M6-07~~ | ~~Onboarding wizard~~ | frontend | — | CANCELLED |

---

## M6 — Platform frontend

**Read first:**
- `docs/decisions/0013-astryx-design-system.md` — **read this before anything else in M6.** The
  component library is Astryx, not ours
- `docs/specs/platform-frontend/design-system.md` — the Astryx integration and the composition ladder
- `docs/specs/platform-frontend/shell-architecture.md` — the application shell
- `docs/requirements/platform-views.md` — every view's contract
- `docs/requirements/platform-ui-library.md` — what the platform needs from the library
- `docs/specs/game-frontend/game-asset-serving.md`, `docs/decisions/0007-game-frontend-separate-domain.md`

**Component lookup is a tool call, not a document.** `npm run astryx -- component <Name>` or the
`astryx` MCP server. Nothing in this corpus lists Astryx's components, deliberately — a copy would be
stale within a release.

`docs/requirements/onboarding-wizard.md` is **not** in this list. IR-23 cut the wizard from v1; the
document is retained as a record of a deferred feature and implements nothing.

### IMP-M6-01 — Astryx integration and the `ui/` boundary

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M0-05

**Closed:** IMP-GATE-68 (opened and closed 2026-09-22) — this item's own Done-when clause 4 requires
`no-raw-color` and `no-raw-spacing` ESLint rules "with no path allow-list," but `design-system.md`
(the item's own read-list, in full) never defined what either rule checks — the pre-Astryx version of
that document did (a table: hex/`rgb()`/`hsl()`/`oklch()` literals in `.css`/`.tsx` for the first,
`px`/`rem` on `padding`/`margin`/`gap`/`inset` for the second, plus a now-obsolete `tokens.css`
allow-list for the first only), but the ADR-0013 rewrite dropped the table entirely without replacing
it, and §9's traceability table mapped the whole `FR-TOK-001…008` range to "Astryx" — wrong for
`FR-TOK-008` specifically, which is about raw values in *our* code, not Astryx's token supply, and is
exactly what the pre-rewrite table enforced. Fixed in `design-system.md`: §5 gained an *Enforcement
(FR-TOK-008)* subsection carrying the two rules forward with no allow-list (dropping the pre-Astryx
`no-raw-font-size`, since typography is now fully Astryx-owned and this item's own Done-when never
names it); §9's traceability table splits `FR-TOK-001…007` (Astryx) from `FR-TOK-008` (ours, §5).
`python3 scripts/check-corpus.py` clean.

**Read first:**
- `docs/decisions/0013-astryx-design-system.md` — why the library is Astryx
- `docs/specs/platform-frontend/design-system.md` **in full** — §2 setup, §3 the composition ladder,
  §4 where our code lives, §5 styling our own code, §6 what remains ours, §7 the CLI
- `docs/requirements/platform-ui-library.md` **in full** — what the platform needs from the library

**Satisfies:** `platform-ui-library.md` FR-TOK-001…006, FR-TOK-008, FR-COMP-001…014,
FR-LYT-001…003, FR-THM-001…002, NFR-DX-001…004, NFR-PERF-001…002, NFR-VER-001

**This item is an integration, not a construction.** IMP-M0-05 already installed and wired Astryx;
what remains is the boundary around our own code and the rules that keep it from drifting.

**Done when:**

1. `src/ui/` exists with `index.ts` as its only legal import path, and **both**
   `no-restricted-imports` rules are in force: deep imports out, and imports from `features/` *into*
   `ui/` out. The second direction matters more — a shared component that reaches into application
   code is a screen with a generic name and it breaks on its second use.
2. `src/ui/` is **empty or near-empty**, and that is the correct end state. Application code imports
   `Button` from `@astryxdesign/core/Button` directly. A pass-through wrapper for every Astryx
   component re-creates the maintenance burden ADR-0013 exists to remove, and puts a stale prop
   signature between the developer and the real documentation.
3. **No parallel token scale exists.** No `--tb-*` custom property is defined anywhere. Every value
   comes from Astryx's `--spacing-*`, `--color-*`, `--radius-*`, `--shadow-*`.
4. `no-raw-color` and `no-raw-spacing` lint rules are enabled with **no path allow-list** — there is
   no token definition file to exempt any more (FR-TOK-008).
5. Any component in `src/ui/` uses CSS Modules and consumes Astryx tokens; `className` overrides on
   Astryx components **append, never substitute**.
6. Every swizzled component (`astryx swizzle`) carries a comment naming what could not be done
   through props. A swizzle is a fork: it stops receiving upstream fixes, including accessibility
   ones, and `astryx upgrade` cannot codemod it.
7. Contrast meets WCAG AA on body text with no exceptions (§6). `theme-neutral` clears this, so the
   check is on anything we compose or swizzle.

**Climb the ladder in order: compose → swizzle → write** (§3). The failure mode this item exists to
prevent is an agent writing a `Button` because it did not think to run
`npm run astryx -- component --list` first.

**`npm run astryx -- init` writes an Astryx component index into `CLAUDE.md`.** Useful — it is how a
low-effort agent discovers components instead of guessing. Run it deliberately and review the diff;
do not let it land unread in a hand-written file.

---

### IMP-M6-02 — Shell, routing and auth tiers

**Repo:** `turnbase-frontend` (the shell, and the nginx template that serves it) and
`turnbase-platform` (the compose service and Helm templates that put the Frontend container on the
platform origin — `IMP-GATE-74`; and the one-field principal change of `IMP-GATE-75`). Branch per
repo; `turnbase-frontend` first, since the platform change pins its image. · **Depends on:** IMP-M6-01

**Closed:** IMP-GATE-75 (opened and closed 2026-09-26, session 75, found writing the tier gate) —
§3's three tiers need to tell a Guest from a Registered user, and `GET /api/auth/session` ("returns
the current principal") was the only source, but no document said what the principal contains and the
shipped `PrincipalResponse` was `{userId, username}` — no tier. The alternatives were parsing the
`guest-` username prefix or an extra `GET /api/users/{username}` per page load. Fixed:
`rest-conventions.md` § Authentication defines the principal body as `{userId, username, kind}`
(`REGISTERED` | `GUEST`, the `app_user.kind` literals) for `register`, `login`, `guest`, `session` and
`complete-registration`; `oauth-rest-api.md` §6 cites it. The platform's `PrincipalResponse` gains
`kind` as part of this item. The same section now also names the `login`/`register` request bodies,
which no document gave and which the shell's forms must match.

**Closed:** IMP-GATE-76 (opened and closed 2026-09-26, session 75, found designing the nginx template
and the login page) — two defects. (1) `local-environment.md` §1 (as `IMP-GATE-74` fixed it) proxied
the whole `/auth/` prefix to the monolith, but `/auth/complete-registration` is a *shell* route that
`oauth-rest-api.md` §4 redirects the browser to; the prefix would send it to the monolith and 404.
Fixed: only `/auth/google` and `/auth/callback` are proxied. (2) `VW-LOGIN-002`/`VW-REG-002` hide the
Google button when the secret is absent, but no document gave the frontend any way to know — a
browser cannot probe a `302`-or-`404` across a navigation. Fixed: `GET /api/auth/providers` →
`{ "google": bool }` (`oauth-rest-api.md` §1/§3), exempted in `user-accounts.md` NFR-SEC-006, Tier 4
in `rate-limiting.md`. The platform half (endpoint, interceptor exemption, rate-limit path) is this
item's.

**Closed:** IMP-GATE-74 (opened and closed 2026-09-26, session 74, found reading this item's
*Done when*) — the item says "the CSP is emitted by the platform origin", but no document said what
serves the shell document at that origin. `local-environment.md` §1 had the monolith answering
`turnbase.localhost:8080` and no Frontend container at all — neither compose nor the Helm chart
deployed `turnbase-frontend`'s image, whose `nginx.conf` already anticipated SPA fallback for this
item. And `frame-src`, which `game-asset-serving.md` §6.3 "owns", was given there only as a literal
local value, though the value is deployment configuration (`turnbase.game-frontend.origin-template`)
that a static bundle cannot know. Fixed: `local-environment.md` §1/§4/§7.7 make the Frontend
container the listener on the platform origin (shell + CSP + reverse proxy to the monolith; every
other `Host` falls through to the monolith); `game-asset-serving.md` §6.3 defines `frame-src` as
derived at container start from the origin template (`{gameId}` → `*`); `shell-architecture.md` §6
names nginx as the emitter and stops restating the directive. The wiring is this item's, below.

**Read first:**
- `docs/specs/platform-frontend/shell-architecture.md` §§1–3 (structure, auth tiers, routing),
  §6 (Content-Security-Policy), §7 (notifications and alerts), §10
- `docs/specs/deployment/local-environment.md` §1 (*Both origins are one listener*), §4, §7.7 — who
  serves the shell, and the two env vars it reads
- `docs/specs/game-frontend/game-asset-serving.md` §6.3 — the one place `frame-src` is specified
- `docs/specs/api-design/rest-conventions.md` § Authentication — `login`, `guest`, `logout`,
  `session` and the `turnbase_session` cookie the tier check rests on
- `docs/specs/api-design/oauth-rest-api.md` — `/auth/google`, `/auth/callback`, and the three
  `/api/auth/oauth/*` endpoints `/auth/complete-registration` calls (VW-OAUTHCOMP)
- `docs/requirements/platform-views.md` VW-NAV-001…012, VW-REDIR-001…007, VW-LAND-001…004,
  VW-LOGIN-001…004, VW-REG-001…003, VW-OAUTHCOMP-001…002
- `docs/requirements/user-accounts.md` FR-SESS-001…004, FR-SESS-010…011
- `docs/specs/api-design/sse-notifications.md`
- `docs/specs/platform-frontend/design-system.md` §2 — the two providers the shell owns
- `docs/specs/api-design/notification-rest-api.md` — `GET /api/notifications/unread-count`, the
  badge the shell refreshes on each pushed notification
- `docs/specs/api-design/error-handling.md` — the `application/problem+json` shape `apiFetch` parses
- `docs/specs/platform/data-model-accounts.md` §1 — `app_user.kind`, the value `IMP-GATE-75` exposes

**Satisfies:** `platform-views.md` VW-NAV-001…012, VW-REDIR-001…007, VW-LAND-001…004,
VW-LOGIN-001…004, VW-REG-001…003, VW-OAUTHCOMP-001…002, NFR-USAB-001…002

**Done when:** (`IMP-GATE-75`) every response carrying the principal — `register`, `login`, `guest`,
`session`, `complete-registration` — includes `kind`, and `GET /api/auth/providers` answers
`{ "google": bool }` unauthenticated, each asserted in `turnbase-platform`; the shell takes its tier
from `kind` and renders the Google buttons only when `google` is `true`; §3's three auth tiers gate every route, and a route's tier is declared with the route
rather than checked inside the view; §6's CSP is emitted by the platform origin **without restating
`frame-src`**, which `game-asset-serving.md` §6.3 owns — two documents specifying one directive is how
they drift; a mid-session 401 follows the VW-REDIR rules rather than blanking the view; the SSE
stream reconnects with backoff and does not duplicate alerts on reconnect. **And (`IMP-GATE-74`)** a
`docker compose up` serves the shell at `http://turnbase.localhost:8080` from the Frontend
container — `/api`, `/ws` (including the upgrade), `/auth/google` and `/auth/callback` reach the monolith through it
(`/auth/complete-registration` is served by the shell — `IMP-GATE-76`), and a
`Host: x.games.localhost` request reaches the monolith's games origin unchanged; the served CSP's
`frame-src` equals `game-asset-serving.md` §6.3's derivation for the configured template, and a
test proves it for both a per-game and a constant (shared-origin) template; the Helm chart gains the
`frontend-*` templates and its Ingress sends `turnbase.localhost` to the Frontend Service.

**Done 2026-09-26 (session 75).** `turnbase-frontend` `9bc005d`, `turnbase-platform` `cdbc78e`, both CI
green. Frontend: `react-router` 8.4.0, `appRoutes` table declaring each route's access kind, `RouteGuard`
(gated elements are removed, never disabled), `safeRedirect`, `AuthProvider` with a 401 listener,
login/register/OAuth-completion pages, the SSE stream (reopens only when the browser gives up —
`readyState` CLOSED — with backoff and jitter, dedupes on `notificationId`), and nginx rendered at
container start with `frame-src` derived from the origin template (`src/deploy/nginx.test.ts` proves
per-game, constant, multi-occurrence and default templates). Platform: `kind` on all five principal
responses, `GET /api/auth/providers` (public, Tier 4), a compose `frontend` service that owns host port
`8080`, Helm `frontend-*` templates with one `origins` values source for both configmaps, e2e smoke
retargeted. Verified against the real stack (compose with the Redis workaround below): shell + SPA
fallback + CSP served for `turnbase.localhost`, `/api` and `/ws` (101 upgrade) proxied,
`/auth/complete-registration` served by the shell, `x.games.localhost` reaching the monolith.
**Not done in this item, on purpose:** the notification centre, the OAuth link-challenge form and every
placeholder page belong to later M6 items.

**The shell mounts `<LinkProvider component={Link}>` inside `<Theme>`, once** (`design-system.md`
§2). Skipping it is the expensive mistake in M6: every Astryx `Link`, and every component that
renders one internally, falls back to a plain `<a href>` and triggers a **full page reload** —
dropping the STOMP connection, the room subscription and all in-memory session state. It fails as a
navigation bug three milestones from where it was introduced.

---

### IMP-M6-03 — Account and profile views

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M6-02, IMP-M1-07, IMP-M1-11

**Closed:** IMP-GATE-78 (opened and closed 2026-09-26, session 77) — see `IMP-M1-11`. Settings had no
read route and no auth-method routes; the platform half is now its own item and this one waits on it.
The read-list also lacked `social-rest-api.md` (the Friends views' whole API) and the two `rest-conventions.md`
/ `oauth-rest-api.md` sections above. **Still open, not gated:** the profile page's statistics and game
history tabs need `IMP-M5-01`/`M5-02`'s REST surface, which is not `DONE`; build those tabs against
whatever those items publish, or leave them for the item that does.

**Closed:** IMP-GATE-80 (opened and closed 2026-09-27, session 80) — this item's own *Done when*
requires VW-PROF-002…003 to render for the owner, and VW-PROF-002c ("Profile section — uploaded
games") is in that range, but no document gave the uploaded-games section anything to call:
`catalog-rest-api.md`'s `GET /api/games` had no owner/author filter, its own "what is deliberately
absent" section never named the gap, and `game-catalog.md` FR-UPROF-001…004 (the requirement that
actually specifies this section's behaviour — not `user-accounts.md` FR-PROF-001, which only names
"uploaded games" as one of five profile contents) had no realizing API at all. Fixed: `catalog-rest-api.md`
`GET /api/games` gained an `owner` query parameter that composes with the existing §2 visibility
predicate — the owner-viewing-own-profile case already falls out of that predicate's owner carve-out,
a non-owner viewer sees only that user's listed games, an unknown username yields an empty page rather
than `404` (§3, §6, §7 updated); `game-catalog.md`'s `catalog-rest-api.md` cross-reference updated to
match. FR-UPROF-002's per-game management actions (edit, delist/publish, delete) remain unrealized —
no mutation route exists yet, same pre-existing gap `catalog-rest-api.md` §6 already disclaimed for
FR-GAME-001…013 — so this item's owner view renders the list but not those actions. The read-list below
gained `game-catalog.md` FR-UPROF-001…004, which it should have named from the start.

**Closed:** IMP-GATE-82 (opened and closed 2026-09-27, session 82) — this item's own *Done when* clause
requires rendering every case of `GET /api/users/{username}` (owner, guest, soft-deleted, private
non-owner, `relationshipState`), and `social-rest-api.md` §9, `catalog-rest-api.md` §3 and
`history-rest-api.md` all treat that endpoint as an established contract they extend or reference, but
no `docs/specs/api-design/*.md` document ever specified it — only `IMP-M1-07`'s own (already-`DONE`)
registry prose and unshaped prose requirements in `user-accounts.md` described the response, so this
item had no wire contract to build its views against. Same shape as `IMP-GATE-31/33/35/37/78/80/81`.
Fixed: new `docs/specs/api-design/profile-rest-api.md`, transcribed from the shipped
`account.ProfileResponse`/`ProfileService.view` (`IMP-M1-07`, session 32) rather than inventing a
divergent shape — registered in `api-design/INDEX.md` and cross-referenced from `user-accounts.md`.
This item's read-list below now cites it in place of the prose it was reading around.

**Closed:** IMP-GATE-83 (opened and closed 2026-09-27, session 83) — the Account Settings password
form this item builds (VW-SET-003) posts to `POST /api/users/me/password`, and `rest-conventions.md`'s
own entry for that route names only "the current password and the new one" — FR-ACCT-010's "supplying
their current password and the new password twice" gives a field *count*, not the three field names a
client actually has to send. Every sibling route on that same table is exact (`login`'s
`usernameOrEmail`/`password`, the auth-methods `password`/`confirmPassword` body), so this was the one
gap left in that section. Fixed: `rest-conventions.md`'s password-change row now names the body,
transcribed from the shipped `account.ChangePasswordRequest` (`IMP-M1-08`) rather than inventing field
names that might diverge from it — `{ "currentPassword", "newPassword", "confirmNewPassword" }`.

**Read first:**
- `docs/requirements/platform-views.md` VW-PROF-001…008, VW-SET-001…007, VW-FREN-001…005
- `docs/specs/api-design/profile-rest-api.md` — the `GET /api/users/{username}` envelope every case
  below renders from (`IMP-GATE-82`)
- `docs/specs/api-design/rest-conventions.md` § Authentication — the `/api/users/me` routes and *The
  account representation*: everything Account Settings reads and writes (`IMP-GATE-78`)
- `docs/specs/api-design/oauth-rest-api.md` §7a — the three-request Google link the Add
  authentication method action drives
- `docs/specs/api-design/social-rest-api.md` — the friend list, requests and `relationshipState` the
  Friends and profile views call
- `docs/specs/api-design/catalog-rest-api.md` §3's `owner` filter — the uploaded-games profile section
  (`IMP-GATE-80`)
- `docs/requirements/user-accounts.md` FR-PROF-001…008, FR-ACCT-002…004, FR-ACCT-009…010
- `docs/requirements/game-catalog.md` FR-UPROF-001…004 — the uploaded-games section's actual behaviour
- `docs/requirements/social-friends.md` FR-SOC-001…021
- `docs/specs/platform-frontend/design-system.md` §4 (the component inventory these views compose)

**Satisfies:** `platform-views.md` VW-PROF-001…008, VW-SET-001…007, VW-FREN-001…005;
`user-accounts.md` FR-PROF-001…008, FR-ACCT-002…004, FR-ACCT-009…010; `game-catalog.md`
FR-UPROF-001, FR-UPROF-003…004; `social-friends.md` FR-SOC-001…021

**Done when:** **the owner sees their own profile in full regardless of every privacy setting they
have set** — private profile, hidden sections and hidden friend list all render for them (IR-05,
FR-PROF-007, VW-PROF-002…003, VW-FREN); a guest profile shows the username and nothing else
(FR-GUEST-010); a soft-deleted user's profile shows the FR-ACCT-009 placeholder; deletion is a
confirmed, explicit action (FR-ACCT-004).

**Done (session 84):** Profile, Friends and Settings pages built and wired at `/users/:username`,
`/friends`, `/settings`; all four *Done when* cases covered by `ProfilePage.test.tsx` and
`SettingsPage.test.tsx`. Also built, beyond the *Done when* clause but within *Satisfies*: friend
request send/accept/decline/remove (`FriendsPage.tsx`), password change and add-password
(`FR-ACCT-010`/`IMP-GATE-83`), auth-method add (Google link, `oauth-rest-api.md` §7a) and remove, and
the four privacy-visibility toggles. **Deliberately deferred:** the profile page's statistics and
game-history tabs render nothing yet — `IMP-M5-01`/`M5-02` are not `DONE` and have no REST surface to
build against, per the still-open note left on `IMP-GATE-78` above; build those tabs when either item
ships. The `GET /api/users?search=` endpoint (`social-rest-api.md`) was not built into any view — no
`VW-*` requirement in this item's *Done when*/*Satisfies* calls for a username-search UI.

**The view is not the access control.** Every rule above is already enforced by IMP-M1-07 server-side;
implementing it here as well is a rendering concern, and implementing it *only* here is a
vulnerability.

---

### IMP-M6-04 — Room views and the STOMP client

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M6-02, IMP-M2-08

**Read first:**
- `docs/specs/platform-frontend/shell-architecture.md` §4 (the WebSocket client) and §8 (the room
  view's one-component-three-states shape and the global reconnection card)
- `docs/specs/api-design/websocket.md` — the base connection this protocol extends: `/ws`, the
  cookie-only `CONNECT` auth with no separate token, and the shared envelope
- `docs/specs/api-design/room-websocket.md` **in full**, and `room-chat-websocket.md`
- `docs/specs/api-design/room-rest-api.md` — the affinity hint and the `503` contract
- `docs/requirements/platform-views.md` VW-ROOMS-001…005, VW-JOIN-001…003, VW-RLOBBY-001…007, VW-RLOBBY-009…017,
  VW-RGAME-001…008, VW-RRESULT-001…005
- `docs/requirements/reconnection-flow.md` FR-REJOIN-001…008

**Satisfies:** `platform-views.md` VW-ROOMS-001…005, VW-JOIN-001…003, VW-RLOBBY-001…007, VW-RLOBBY-009…017,
VW-RGAME-001…008, VW-RRESULT-001…005; `game-rooms.md` NFR-PERF-001…002; `in-room-chat.md`
FR-CHAN-001…004, FR-SWITCH-001…002

**Done when:** the client holds a `localVersion` and **discards any delta with
`version <= localVersion`**; resync is snapshot-then-deltas with no merge path; chat frames carry
`version: null` and are excluded from that comparison entirely (IR-08) — comparing them against
`localVersion` discards every chat message after the first room event; the
`X-TurnBase-Room-Instance` hint is honoured when opening the socket; a `503` with `Retry-After` from
a join is retried after the stated delay rather than surfaced as a failure, because it means "not
here yet", not "no".

**Done 2026-09-27 (session 85).** `turnbase-frontend`: `roomSocket.ts` (STOMP client —
`localVersion` assigned, never merged, from `ROOM_STATE`; `reconcileVersion`'s apply/discard/resync
table; a resync discards every delta until the next snapshot rather than reconciling against a
stale version; chat's `/topic/room.{roomId}.chat` and `.team.{teamId}` subscriptions never touch
`reconcileVersion`; `brokerUrl` honours `?instance={hint}`), `roomsApi.ts` (`joinRoom` retries a
`503`+`retryAfterMs` transparently), `roomReducer.ts` and `useRoomConnection.ts` (the event-to-state
reducer and the React hook wiring the two together). 36 unit tests, all *Done when* clauses asserted
directly. `npm run format && lint && typecheck && test && build` green locally and in CI
(`36323893623`). The room list/join/lobby/game/results views (VW-ROOMS/VW-JOIN/VW-RLOBBY/VW-RGAME/
VW-RRESULT, `in-room-chat.md` FR-CHAN/FR-SWITCH) are not built by this item — `registry.md`
INDEX.md's own instruction is to build exactly the *Done when* clause, which names none of them, and
IMP-GATE-84's closing note already established the precedent of deferring a *Satisfies* entry the
backend or a later item has to finish first. Tracked in `STATUS.md` *Next Priorities* as the
remaining work before those requirement IDs are actually satisfied.

**Closed:** IMP-GATE-85 — this item's own *Done when* requires the `X-TurnBase-Room-Instance` hint
to be "honoured when opening the socket", but no document named a mechanism a browser's native
`WebSocket` (which cannot set arbitrary handshake headers) can actually use to carry it, and
`room-websocket.md` §*Routing on join*'s own illustrative "cookie or header" aside never resolved to
one either. Opened and closed 2026-09-27: `room-websocket.md` now names the concrete mechanism — the
client appends the hint as `/ws?instance={podId}`, consumed by an ingress configured for it and
ignored otherwise (`local-environment.md` §3's round-robin ingress, correctly per FR-DEPLOY-002).

**Closed:** IMP-GATE-84 — `shell-architecture.md` §8 requires the `/rooms` reconnection pinned card
(VW-ROOMS-005, FR-REJOIN-002) to be "driven by a field on the rooms list response", but
`room-rest-api.md` §3's `GET /api/rooms` response had no field naming the caller's own held
grace-period reservation, and `reconnection-flow.md` never named the wire mechanism either. Opened
and closed 2026-09-27: added a top-level `reservedSlot` field to the `GET /api/rooms` envelope in
`room-rest-api.md` §3 (sibling to `content`/`pagination`, unaffected by filters, `null` when the
caller holds no live reservation). The backend (`IMP-M2-01`, `IMP-M2-07`, both `DONE`) does not yet
populate it — VW-ROOMS-005 is deferred within this item pending that backend follow-up (tracked
below, not in this item's *Done when*).

---

### IMP-M6-05 — Game iframe host and postMessage relay

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M6-04, IMP-M3-07

**Read first:**
- `docs/specs/platform-frontend/shell-architecture.md` §5 (the trust boundary), §6
- `docs/specs/game-frontend/game-asset-serving.md` §6 (the iframe), §7 (session integration),
  §8, §9
- `docs/specs/gdk-api/frontend-gdk-api.md` §8 (origin validation), §9 (the bootstrap contract),
  §10 (the inbound envelope)
- `docs/decisions/0007-game-frontend-separate-domain.md`
- `docs/specs/api-design/websocket.md` § *Catch-up: the sync flow*, § *Platform-shell relay contract*,
  § *Client→server command catalogue* — the STOMP half of the relay (added session 109; the list
  named no document for the game stream the relay translates)

**Satisfies:** `game-contracts.md` FR-FE-001…006, NFR-SEC-001…004; `platform-views.md`
VW-RGAME-001…008

**Note:** `FR-FEGDK-001…009` (the `TurnBaseClient` library itself) moved to `IMP-M3-12` in
`turnbase-sdk` when IMP-GATE-05 closed 2026-08-22 — this item implements the platform shell's half
of the postMessage boundary, not the client.

**Done when:** the shell validates `event.origin` against the game origin on every inbound message;
the iframe carries the sandbox attributes and CSP of `game-asset-serving.md`; no state is shared with
the game frontend other than by `postMessage` (`CLAUDE.md` AVOID).

**The sandbox is `allow-scripts allow-same-origin`, and dropping the second token breaks everything
silently** (IR-21). With `allow-scripts` alone the iframe gets an opaque origin, every
`event.origin` reads the string `"null"`, and the origin check either fails permanently or gets
"fixed" by comparing against `"null"` — which accepts messages from any sandboxed frame. The
separation ADR-0007 buys comes from the **registrable domain**, not from withholding
`allow-same-origin`.

---

### IMP-M6-06 — Catalog and history views

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M6-02, IMP-M4-01, IMP-M5-01

**Closed:** IMP-GATE-81 (opened and closed 2026-09-27, session 81) — this item's own *Satisfies*
claimed `game-history.md` FR-HIST-020…030 (the History tab: cards, search, pagination, empty state,
visibility), but no REST endpoint existed to render it against, this item's *Depends on* never named
`IMP-M5-01` (the platform item that owns `game_history_entry`), and its own *Done when* never tested
any of the range — same shape as `IMP-GATE-80`. Fixed: see `IMP-M5-01`'s closed gate for the new
`history-rest-api.md`. This item's *Depends on* gained `IMP-M5-01`; its read-list gained the new
document; its *Done when* gained the clauses below.

**Read first:**
- `docs/requirements/platform-views.md` VW-CAT-001…003, VW-GDET-001…003, VW-NOTIF-001…004
- `docs/requirements/game-catalog.md` FR-CAT-001…010, FR-GDET-001…009
- `docs/requirements/game-history.md` FR-HIST-020…030
- `docs/specs/api-design/history-rest-api.md` (`IMP-GATE-81`) — the History tab's data source
- `docs/specs/api-design/input-validation.md` § *Output encoding* — the owner of the Markdown rule
- `docs/specs/api-design/pagination-filtering-sorting.md`
- `docs/specs/api-design/notification-rest-api.md` — the notifications panel (VW-NOTIF); added
  session 107, the list named no document for a range the item claims

**Satisfies:** `platform-views.md` VW-CAT-001…003, VW-GDET-001…003, VW-NOTIF-001…004;
`game-catalog.md` FR-CAT-001…010, FR-GDET-001…009; `game-history.md` FR-HIST-020…030

**Closed:** IMP-GATE-92 (opened and closed 2026-09-30, session 108) — no document stated the payload of `FRIEND_REQUEST` or how its Accept/Decline reaches a request id; `notification-rest-api.md` §2 now has a *Payload shapes* table and the resolution rule.

**Done when:** game descriptions are parsed from Markdown into **React elements**, client-side, with
no intermediate HTML string anywhere in the path (IR-19); `dangerouslySetInnerHTML` appears nowhere
in the repository and a lint rule enforces its absence — the ban is only worth having if nothing can
quietly re-introduce it; catalog paging uses the shared contract from IMP-M1-01 rather than a
bespoke one; the History tab renders `history-rest-api.md`'s `content` array as cards
(`gameName`/`gameLinkable`/`outcomeLabel`/`completedAt`), each expandable to its `playerStats`/
`teamStats` sections when present and collapsed otherwise (FR-HIST-021…022); an empty `content` array
renders FR-HIST-027's placeholder, not a blank tab; the search input and pagination controls drive
`history-rest-api.md`'s `search`/`page`/`size` query parameters rather than filtering a client-held
page; the notifications panel opens from the bell, lists `notification-rest-api.md`'s `content` without
marking anything read on open, offers Accept / Decline on `ROOM_INVITATION` (join / decline the room invitation)
and `FRIEND_REQUEST` (accept / delete the request, its id resolved from `GET /api/friend-requests`) rows, and
drives mark-read, mark-all-read and dismiss through the PATCH / POST / DELETE endpoints (VW-NOTIF-001…004).

---

### ~~IMP-M6-07 — Onboarding wizard~~ · CANCELLED

**Cancelled by IR-23.** The onboarding wizard is cut from v1.
`docs/requirements/onboarding-wizard.md` is retained as the record of a deferred feature; its
FR-ONB-001…013 and NFR-ONB-001…003 have no implementing item and are not expected to.

The identifier is retired and will not be reused. If the wizard returns, it gets a new number.

---
