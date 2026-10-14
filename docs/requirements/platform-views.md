# Platform Views & Navigation Requirements

## Stakeholders

| Role | Description |
|------|-------------|
| Unauthenticated Visitor | No session token; limited to public views |
| Guest User | Valid guest session token; can participate in games, view profiles |
| Registered User | Valid registered session token; full platform access |
| Platform (System) | Enforces access rules, redirects, and error responses |

---

## Auth Tier Reference

| Tier | Condition |
|------|-----------|
| **Unauth** | No valid session token present |
| **Guest** | Valid session token for a guest account |
| **Registered** | Valid session token for a registered account |

---

## Navigation Bar

The navigation bar is present on every view.

The bar is a floating glass bar (`IMP-M13-02`). Landing (`/`), Login (`/login`) and Registration
(`/register`) are *bare* pages: each leads with its own way into the catalog or the account, so the
bar carries no Game Catalog link there (VW-NAV-002).

### Nav Components

| ID | Component | Unauth | Guest | Registered |
|----|-----------|--------|-------|------------|
| VW-NAV-001 | Logo / brand mark — links to Landing (`/`) | Visible | Visible | Visible |
| VW-NAV-002 | Game Catalog link — absent on the bare pages `/`, `/login` and `/register` | Visible | Visible | Visible |
| VW-NAV-003 | Active Rooms link | Hidden | Visible | Visible |
| VW-NAV-004 | Friends link | Hidden | Hidden | Visible |
| VW-NAV-005 | Notifications bell | Hidden | Visible | Visible |
| VW-NAV-006 | User menu (username + dropdown) | Hidden | Visible | Visible |
| VW-NAV-007 | Login button | Visible | Hidden | Hidden |
| VW-NAV-008 | Register button | Visible | Hidden | Hidden |
| VW-NAV-009 | Play as Guest button | Visible | Hidden | Hidden |

### User Menu Dropdown (VW-NAV-006)

| ID | Item | Guest | Registered |
|----|------|-------|------------|
| VW-NAV-010 | View My Profile | Visible | Visible |
| VW-NAV-011 | Account Settings | Hidden | Visible |
| VW-NAV-012 | Log Out | Visible | Visible |

---

## Views

### Landing Page (`/`)

| Attribute | Value |
|-----------|-------|
| Auth required | No |
| Available to | Unauth, Guest, Registered |

| ID | Element / Action | Unauth | Guest | Registered |
|----|-----------------|--------|-------|------------|
| VW-LAND-001 | Platform description and feature overview | Visible | Visible | Visible |
| VW-LAND-002 | Login button | Visible | Hidden | Hidden |
| VW-LAND-003 | Register button | Visible | Hidden | Hidden |
| VW-LAND-004 | Play as Guest button | Visible | Hidden | Hidden |

No onboarding CTA is present. `onboarding-wizard.md` FR-ONB-004 requires one; that document is
**Post-MVP** (IR-23) and the row is deliberately absent rather than missing.

---

### Login Page (`/login`)

| Attribute | Value |
|-----------|-------|
| Auth required | No |
| Available to | Unauth |
| Redirect — Guest | → Active Rooms (`/rooms`) |
| Redirect — Registered | → Active Rooms (`/rooms`) |

| ID | Element / Action | Unauth |
|----|-----------------|--------|
| VW-LOGIN-001 | Credential login form (username or email + password) | Visible |
| VW-LOGIN-002 | Google OAuth login button | Visible |
| VW-LOGIN-003 | Link to Registration page | Visible |
| VW-LOGIN-004 | `redirect` query parameter support — on successful login, redirects to the path specified; falls back to `/rooms` if absent or invalid | Enforced |

---

### Registration Page (`/register`)

| Attribute | Value |
|-----------|-------|
| Auth required | No |
| Available to | Unauth |
| Redirect — Guest | → Active Rooms (`/rooms`) |
| Redirect — Registered | → Active Rooms (`/rooms`) |

| ID | Element / Action | Unauth |
|----|-----------------|--------|
| VW-REG-001 | Credential registration form (username, email, password, confirm password) | Visible |
| VW-REG-002 | Google OAuth registration button | Visible |
| VW-REG-003 | Link to Login page | Visible |

---

### OAuth Callback (`/auth/callback`)

| Attribute | Value |
|-----------|-------|
| Auth required | No |
| Available to | Unauth |
| Purpose | Processes the redirect from Google after OAuth authorization. Not a user-facing view — exchanges the authorization code for a session token and redirects immediately. The original redirect destination is preserved via the OAuth `state` parameter. |
| Redirect — existing account | → Active Rooms (`/rooms`) or the path preserved in `state` |
| Redirect — new account (no username yet) | → `/auth/complete-registration` |
| Redirect — error | → `/login` with an error alert indicating the failure reason |

---

### OAuth Registration Completion (`/auth/complete-registration`)

| Attribute | Value |
|-----------|-------|
| Auth required | No (session not yet established) |
| Available to | Users arriving from `/auth/callback` with a valid pending OAuth registration token; direct access without that token redirects to `/login` |
| Redirect — direct access without pending registration | → `/login` |
| Redirect — success | → Active Rooms (`/rooms`) |

| ID | Element / Action | Unauth |
|----|-----------------|--------|
| VW-OAUTHCOMP-001 | Username input form | Visible; the provider-supplied email is shown read-only for reference |
| VW-OAUTHCOMP-002 | Submit button | Creates the account, sets the session cookie, redirects to `/rooms` |

---

### Active Rooms (`/rooms`)

| Attribute | Value |
|-----------|-------|
| Auth required | Yes |
| Available to | Guest, Registered |
| Redirect — Unauth | → `/login?redirect=/rooms` |
| Post-login default | This is the default destination after login or guest account creation |

Room list behavior, filtering, pagination, and visibility rules are specified in game-rooms.md.

| ID | Element / Action | Guest | Registered |
|----|-----------------|-------|------------|
| VW-ROOMS-001 | Room list | Visible | Visible |
| VW-ROOMS-002 | Filter and sort controls | Visible | Visible |
| VW-ROOMS-003 | Refresh button | Visible | Visible |
| VW-ROOMS-004 | Join room action | Enabled | Enabled |
| VW-ROOMS-005 | Reconnection pinned card | Visible when the player holds a grace-period reserved slot in an in-progress room; shows the room name and a Rejoin button; removed automatically when the slot is released; per `reconnection-flow.md` FR-REJOIN-002 | Visible | Visible |

Note: "Friends Only" rooms are not listed for Guest users (they cannot have friends, per FR-LIST-006 and FR-GUEST-007).

---

### Game Catalog (`/games`)

| Attribute | Value |
|-----------|-------|
| Auth required | No |
| Available to | Unauth, Guest, Registered |

| ID | Element / Action | Unauth | Guest | Registered |
|----|-----------------|--------|-------|------------|
| VW-CAT-001 | Searchable and filterable game list | Visible | Visible | Visible |
| VW-CAT-002 | Link to Game Detail page per game | Visible | Visible | Visible |
| VW-CAT-003 | Create Room button per game entry | Hidden | Visible | Visible |

---

### Game Detail (`/games/:id`)

| Attribute | Value |
|-----------|-------|
| Auth required | No |
| Available to | Unauth, Guest, Registered |

| ID | Element / Action | Unauth | Guest | Registered |
|----|-----------------|--------|-------|------------|
| VW-GDET-001 | Game description and metadata | Visible | Visible | Visible |
| VW-GDET-002 | Per-game statistics section (a section of the detail page, not a tab — it is the page's only panel) | Visible | Visible | Visible |
| VW-GDET-003 | Create Room button | Hidden | Visible | Visible |

Note: The content and structure of per-game statistics is specified in per-game-statistics.md.

---

### Room — Lobby (`/rooms/:id`, state: Lobby)

| Attribute | Value |
|-----------|-------|
| Auth required | Yes |
| Available to | Guest, Registered |
| Redirect — Unauth | → `/login?redirect=/rooms/:id` |

Room lifecycle, readiness rules, and host management behavior are specified in game-rooms.md. This section defines which UI elements are visible and enabled per role and auth tier.

**Entry — which route may enrol (`IMP-GATE-95`).** Opening `/rooms/:id` never takes a seat. A caller who
already holds one (`viewerRole` in `room-rest-api.md` §4) re-enters it: the idempotent join, which is
also how a refresh or a stored link resumes (FR-REJOIN-003, 004). A caller who holds none sees the
VW-JOIN-002 prompt — *Join as player* and/or *Join as spectator*, each only when the room's `canJoin` /
`canSpectate` allow it — and is enrolled only by pressing one; with neither available, the VW-JOIN-003
error. This holds whether the visitor arrived by the Rooms list, a pasted URL, a notification or a link
preview. `/rooms/join/:code` keeps its own rule below: a valid code is itself the deliberate act, and it
prompts only when both roles are available.

| ID | Element / Action | Role condition | Guest | Registered |
|----|-----------------|----------------|-------|------------|
| VW-RLOBBY-001 | Player list with readiness indicators | All participants | Visible | Visible |
| VW-RLOBBY-002 | Game parameters panel (read-only) | All participants | Visible | Visible |
| VW-RLOBBY-003 | Toggle Readiness button | Non-host players only | Enabled | Enabled |
| VW-RLOBBY-004 | Leave Room button | All participants | Enabled | Enabled |
| VW-RLOBBY-005 | Invite Friends button | Host only | Hidden | Enabled |
| VW-RLOBBY-006 | Share Invite Link button | Host only | Enabled | Enabled |
| VW-RLOBBY-007 | Add AI Player button | Host only, if game supports AI | Enabled | Enabled |
| ~~VW-RLOBBY-008~~ | *(removed)* | — | — | — |
| VW-RLOBBY-009 | Kick Player button | Host only | Enabled | Enabled |
| VW-RLOBBY-014 | Transfer Host button (per player) | Host only | Enabled | Enabled |
| VW-RLOBBY-010 | Edit Game Parameters controls | Host only, if game exposes parameters | Enabled | Enabled |
| VW-RLOBBY-011 | Start Game button | Host only; enabled when all start conditions met (FR-TEAM-009) | Enabled | Enabled |
| VW-RLOBBY-012 | Switch to Spectator button | Non-host players; if room supports spectating and spectator slot available | Enabled | Enabled |
| VW-RLOBBY-013 | Switch to Player button | Spectators; if player slot available | Enabled | Enabled |
| VW-RLOBBY-015 | Chat panel (unified message view) | Players only; spectators excluded per `in-room-chat.md` FR-CHAN-004 | Visible | Visible |
| VW-RLOBBY-016 | Team channel tab | Players with a team assignment; only when the game declares team support | Visible | Visible |
| VW-RLOBBY-017 | Write channel switcher | Players with access to both room and team channels | Enabled | Enabled |

Note: Chat behavior, channel rules, and message format are fully specified in `in-room-chat.md`.

Note: VW-RLOBBY-005 (Invite Friends) is hidden for Guest hosts because guests cannot have friends. All other host actions are available regardless of auth tier. The host never sees a Toggle Readiness button — Start Game serves as their implicit readiness confirmation.

---

### Room — In Progress (`/rooms/:id`, state: In Progress)

| Attribute | Value |
|-----------|-------|
| Auth required | Yes |
| Available to | Guest, Registered |
| Redirect — Unauth | → `/login?redirect=/rooms/:id` |

| ID | Element / Action | Role condition | Guest | Registered |
|----|-----------------|----------------|-------|------------|
| VW-RGAME-001 | Game sandbox (iframe) | Player or Spectator | Visible | Visible |
| VW-RGAME-002 | Participant status panel | All participants | Visible | Visible |
| VW-RGAME-003 | Leave Room button | All participants | Enabled | Enabled |
| VW-RGAME-004 | Kick Player button | Host only | Enabled | Enabled |
| VW-RGAME-005 | Transfer Host button (per player) | Host only | Enabled | Enabled |
| VW-RGAME-006 | Chat panel (unified message view) | Players only; spectators excluded per `in-room-chat.md` FR-CHAN-004 | Visible | Visible |
| VW-RGAME-007 | Team channel tab | Players with a team assignment; only when the game declares team support | Visible | Visible |
| VW-RGAME-008 | Write channel switcher | Players with access to both room and team channels | Enabled | Enabled |

Note: Chat behavior, channel rules, and message format are fully specified in `in-room-chat.md`.

---

### Room — Post-Game Results (`/rooms/:id`, room state: Lobby)

> This is not a distinct server-side room state. When a game ends the room is already in **Lobby** state (game-rooms.md FR-LIFE-001, FR-LIFE-002). The game iframe remains rendered and displays results; the platform overlays a dismiss control. Once the player dismisses the game UI, the standard Lobby view (above) is shown. See game-rooms.md FR-LIFE-003.

| Attribute | Value |
|-----------|-------|
| Auth required | Yes |
| Available to | Guest, Registered |
| Redirect — Unauth | → `/login?redirect=/rooms/:id` |

| ID | Element / Action | Role condition | Guest | Registered |
|----|-----------------|----------------|-------|------------|
| VW-RRESULT-001 | Game iframe (showing results) | All participants | Visible | Visible |
| VW-RRESULT-002 | Return to Lobby button (dismisses game iframe, reveals lobby view) | All participants | Enabled | Enabled |
| VW-RRESULT-003 | Leave Room button | All participants | Enabled | Enabled |
| VW-RRESULT-004 | Kick Player button | Host only | Enabled | Enabled |
| VW-RRESULT-005 | Transfer Host button (per player) | Host only | Enabled | Enabled |

---

### Room Join via Invite Link (`/rooms/join/:code`)

| Attribute | Value |
|-----------|-------|
| Auth required | Yes |
| Available to | Guest, Registered |
| Redirect — Unauth | → `/login?redirect=/rooms/join/:code` |
| Purpose | Validates the invite code and routes the player into the room. Not a persistent view — resolves immediately to the room or an error state. |

| ID | Element / Action | Guest | Registered |
|----|-----------------|-------|------------|
| VW-JOIN-001 | Automatic redirect to room (`/rooms/:id`) | On valid code with an available role; all joining rules from `game-rooms.md` FR-JOIN-003–FR-JOIN-006 apply | Enabled | Enabled |
| VW-JOIN-002 | Player / Spectator choice prompt | Shown before joining when both roles are simultaneously available; on `/rooms/:id` a non-member is also prompted when only one role is available (see *Room — Lobby*, Entry) | Enabled | Enabled |
| VW-JOIN-003 | Error message | Shown when the code is invalid, the room no longer exists, or no role is available; includes the specific reason | Visible | Visible |

---

### User Profile (`/users/:username`)

| Attribute | Value |
|-----------|-------|
| Auth required | No |
| Available to | Unauth, Guest, Registered |

Profile content depends on the account type and privacy settings of the viewed user (see user-accounts.md).

**The owner is exempt from their own privacy settings.** Every visibility condition in the table below
is evaluated against the *viewer*, and when the viewer is the profile's owner it resolves to visible
regardless of the setting. A private profile is private to other people; it is not a way to hide your
own statistics from yourself, and VW-PROF-008's Edit Profile link would otherwise appear beside a
"Profile is private" message on the owner's own page. This restates `user-accounts.md` FR-PROF-007
and `social-friends.md` FR-SOC-018 at the point of use, because the tables read as complete without
it.

| ID | Element / Action | Condition | Unauth | Guest | Registered |
|----|-----------------|-----------|--------|-------|------------|
| VW-PROF-001 | Username | Always | Visible | Visible | Visible |
| VW-PROF-002 | Profile section — statistics | Viewer is the owner, or (public profile and statistics section not hidden) | Visible | Visible | Visible |
| VW-PROF-002a | Profile section — game history tab | Viewer is the owner, or (public profile and game history section not hidden) | Visible | Visible | Visible |
| VW-PROF-002b | Profile section — friends list | Viewer is the owner, or (public profile and friends section not hidden) | Visible | Visible | Visible |
| VW-PROF-002c | Profile section — uploaded games | Viewer is the owner, or (public profile and uploaded games section not hidden) | Visible | Visible | Visible |
| VW-PROF-003 | "Profile is private" message | Private registered profile, viewed by someone other than the owner | Visible | Visible | Visible |
| VW-PROF-004 | Empty profile (username only) | Guest profile | Visible | Visible | Visible |
| VW-PROF-005 | "Account no longer exists" message | Deleted account profile | Visible | Visible | Visible |
| VW-PROF-006 | Add Friend button | Other registered user; not already friends | Hidden | Hidden | Enabled |
| VW-PROF-007 | Remove Friend button | Viewing a friend's profile | Hidden | Hidden | Enabled |
| VW-PROF-008 | Edit Profile / Settings link | Viewing own profile (registered) | N/A | N/A | Enabled |

---

### Friends (`/friends`)

| Attribute | Value |
|-----------|-------|
| Auth required | Yes (Registered only) |
| Available to | Registered |
| Redirect — Unauth | → `/login?redirect=/friends` |
| Response — Guest | 403; platform displays "this feature requires a registered account" |

| ID | Element / Action | Registered |
|----|-----------------|------------|
| VW-FREN-001 | Friend list | Visible |
| VW-FREN-002 | View friend's profile link | Enabled |
| VW-FREN-003 | Remove Friend action | Enabled |
| VW-FREN-004 | Pending incoming friend requests list | Visible |
| VW-FREN-005 | Accept / Decline friend request | Enabled |

The owner exemption above applies here too: `social-friends.md` FR-SOC-018 hides a friends list from
others, never from its owner. `/friends` is a self-scoped route — there is no viewer who is not the
owner — so the exemption is trivially satisfied, and it is stated so that a future "view a friend's
friends" feature does not inherit the wrong default.

---

### Account Settings (`/settings`)

| Attribute | Value |
|-----------|-------|
| Auth required | Yes (Registered only) |
| Available to | Registered |
| Redirect — Unauth | → `/login?redirect=/settings` |
| Response — Guest | 403; platform displays "this feature requires a registered account" |

| ID | Element / Action | Condition | Registered |
|----|-----------------|-----------|------------|
| VW-SET-001 | Update username form | — | Enabled |
| VW-SET-002 | Update email form | Email not bound to an OAuth provider | Enabled |
| VW-SET-003 | Change password form | Credential auth method linked | Enabled |
| VW-SET-004 | Add authentication method | — | Enabled |
| VW-SET-005 | Remove authentication method | More than one auth method linked | Enabled |
| VW-SET-006 | Profile privacy toggle (public / private) | — | Enabled |
| VW-SET-006a | Per-section visibility toggles (history, stats, friends, uploaded games) | Public profile only; hidden when profile is private | Enabled |
| VW-SET-007 | Delete Account action | — | Enabled |

---

### Notifications Panel (global overlay)

| Attribute | Value |
|-----------|-------|
| Auth required | Yes |
| Available to | Guest, Registered |
| Access | Via nav bar bell icon (VW-NAV-005) |

| ID | Element / Action | Guest | Registered |
|----|-----------------|-------|------------|
| VW-NOTIF-001 | Notification list (platform events, errors, status feedback) | Visible | Visible |
| VW-NOTIF-002 | Room invite notification with Accept / Decline | Hidden | Visible |
| VW-NOTIF-003 | Friend request notification with Accept / Decline | Hidden | Visible |
| VW-NOTIF-004 | Dismiss / mark as read | Visible | Visible |

Note: Full notification types, delivery rules, and real-time behavior will be specified in a dedicated notifications document.

---

## Redirect & Fallback Behavior

| ID | Scenario | Behavior |
|----|----------|---------|
| VW-REDIR-001 | Guest or Registered user visits `/login` or `/register` | Redirect to `/rooms` |
| VW-REDIR-002 | Unauthenticated user visits any auth-required view | Redirect to `/login?redirect=<original-path>` |
| VW-REDIR-003 | Guest user visits a Registered-only view (`/friends`, `/settings`) | 403 response; platform displays "this feature requires a registered account" |
| VW-REDIR-004 | Successful login or guest creation (no `redirect` param) | Redirect to `/rooms` |
| VW-REDIR-005 | Successful login with a valid `redirect` param | Redirect to the path in `redirect`; must be a valid internal platform path |
| VW-REDIR-006 | Successful login with an invalid or external `redirect` param | Redirect to `/rooms` (open redirect prevention) |
| VW-REDIR-007 | Request without a valid session token to a non-exempt endpoint | 401 response; frontend redirects to `/login?redirect=<original-path>` |

---

## Non-Functional Requirements

| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-SEC-001 | Security | The `redirect` parameter must be validated as an internal platform path before use. External URLs must be rejected and discarded. | 100% of redirect uses | Must |
| NFR-USAB-001 | Usability | UI elements inaccessible to the current auth tier must be hidden entirely, not merely disabled. | 100% of gated elements | Must |
| NFR-USAB-002 | Usability | When a Guest user attempts to access a Registered-only feature, the platform displays a clear message explaining that a registered account is required. | — | Must |

---

## Constraints

| ID | Description |
|----|-------------|
| CON-001 | Frontend must be implemented in React 19 with TypeScript. |
| CON-002 | All view-level access enforcement is backed by server-side token validation — client-side hiding is supplemental only. |

---

## Out of Scope

- In-room chat (separate document)
- Notification types, delivery rules, and real-time push behavior (separate document)
- Per-game statistics content (specified in per-game-statistics.md)
- Game SDK developer portal or admin interface
- Responsive layout breakpoints and mobile-specific design (implementation detail)
