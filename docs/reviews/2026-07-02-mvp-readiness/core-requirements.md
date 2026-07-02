# Platform-Core Requirements Review — MVP Implementability (core-review agent)

Scope: the 12 platform-core requirement docs, cross-referenced against `docs/specs/api-design/`. Known/tracked gaps (bundle pipeline, test harness, frontend shell, items in `requirements-gaps.md`/STATUS.md open questions) are excluded per instructions.

## BLOCKER

### 1. Initial team instantiation at room creation is undefined
**Files:** `docs/requirements/game-rooms.md` (FR-CREATE-003, FR-TEAM-002, FR-TEAM-005), `docs/specs/api-design/room-websocket.md` (`ROOM_STATE`)
When a room is created, the host is placed in it automatically and every joiner is "auto-assigned to the team with the fewest current members" — but no document says which team instances exist at t=0 or at what configured size. If zero teams exist, the host's own auto-assignment is undefined; the choice (count.min teams at size.min vs size.max) also changes the room's advertised available-slot count (FR-LIST-001/002) and whether FR-TEAM-009 start conditions can be met without host action. Every implementation path forks here, and the room happy path cannot be built without the decision.
**Suggested resolution:** at creation, instantiate `count.min` teams per template, each at `configuredSize = size.max`. Document it in the FR-TEAM section.

### 2. Voluntary "Leave Room" during In Progress contradicts the disconnect model
**Files:** `docs/requirements/reconnection-flow.md` (Definitions "Disconnect", FR-DC-001) vs `docs/requirements/game-rooms.md` (FR-LIFE-004, FR-JOIN-007/008) and `docs/specs/api-design/room-websocket.md` (`PLAYER_LEFT` vs `PLAYER_DISCONNECTED`)
Reconnection-flow explicitly says no distinction is made between voluntary leave and network drop — implying a confirmed "Leave Room" click during a game produces a 60-second reserved slot, a pinned card, and no game-engine notification. But room-websocket.md defines `PLAYER_LEFT` for voluntary departure as a distinct event from `PLAYER_DISCONNECTED`, and FR-JOIN-007/008 let a player confirm abandonment and join another room — which collides with still holding a reserved slot in the old room (is the reservation voided? does it count as "occupying a room"?). The two documents cannot both be implemented as written.
**Suggested resolution:** confirmed explicit leave = immediate departure (emit `PLAYER_LEFT`, send `player_left` to the game BE, no grace period); connection loss = grace period. Joining or creating another room while holding a reserved slot voids the reservation (early expiry). Amend the reconnection-flow Definitions accordingly.

### 3. Host disconnect when no other human player remains (In Progress)
**Files:** `docs/requirements/game-rooms.md` (FR-XFER-001/002) vs `docs/requirements/reconnection-flow.md` (FR-HDISC-001/002)
FR-XFER-002 closes the room "immediately and permanently" when the host leaves with no other human players; FR-HDISC-001/002 say a disconnecting host gets a grace-period reserved slot and host role transfers to "the next human player by join order." When the sole human player (the host) of an in-progress game disconnects — a completely ordinary event, and the default for 1-player-vs-AI rooms — there is no player to transfer to, and the docs point in opposite directions: immediate closure (killing the session, evicting spectators, making reconnection impossible) versus a 60-second survival window.
**Suggested resolution:** in In Progress state, if the disconnecting host is the last connected human, defer host transfer and keep the room alive for the grace period; close the room (and terminate the session) only if the grace period expires. FR-XFER-002's immediate closure applies to Lobby state and explicit leaves.

## IMPORTANT

### 4. Password change has no functional requirement
**Files:** `docs/requirements/user-accounts.md` (only NFR-SEC-003 mentions it), `docs/requirements/platform-views.md` (VW-SET-003), `docs/specs/api-design/rate-limiting.md` (Tier 1)
A "Change password" form and its rate limiting are referenced, but no FR defines the flow: whether the current password is required, whether the 8-char minimum applies, whether the active session survives. Implementable only by inventing security-relevant behavior.
**Suggested resolution:** add an FR: requires current password, new password subject to FR-AUTH-005, current session remains valid (single-session model already prevents other sessions).

### 5. Logout is unspecified
**Files:** `docs/requirements/platform-views.md` (VW-NAV-012), `docs/requirements/user-accounts.md` (session management section)
"Log Out" appears only as a menu item. There is no requirement that logout invalidates the session server-side (vs just clearing the cookie), and no treatment of guest logout — a guest who logs out permanently loses the account (FR-GUEST-004: no login flow exists), which deserves at least a confirmation.
**Suggested resolution:** add FRs: `POST /api/auth/logout` invalidates the session server-side and clears the cookie; guests get a confirmation dialog warning the account cannot be recovered.

### 6. Username constraints missing (length, charset, case-sensitivity)
**Files:** `docs/requirements/user-accounts.md` (FR-AUTH-001/003), `docs/requirements/platform-views.md` (`/users/:username`), `docs/requirements/social-friends.md` (FR-SOC-002, FR-SOC-010)
No max/min length or permitted character set is defined, yet usernames are URL path segments, prefix-searchable, and sorted case-insensitively. Whether uniqueness is case-insensitive ("Bob" vs "bob") is undefined and affects DB collation, lookup semantics, and the reserved `guest-` prefix check.
**Suggested resolution:** e.g. 3–20 characters, `[A-Za-z0-9_-]`, uniqueness enforced case-insensitively, display preserves entered case.

### 7. OAuth login with an email already registered to a credential account
**Files:** `docs/requirements/user-accounts.md` (FR-AUTH-004, FR-AUTH-007, FR-AUTH-009/010)
First Google OAuth login creates a new account, but FR-AUTH-004 requires email uniqueness across active accounts. A user who registered with credentials using their Gmail address and later clicks "Sign in with Google" — the most common OAuth collision in practice — hits undefined behavior: auto-link (account-takeover risk, no verified email), reject, or prompt. No doc decides. Relatedly, the `/auth/complete-registration` pending-OAuth-registration token (platform-views.md) has no specified transport, lifetime, or one-time-use semantics.
**Suggested resolution:** reject at `/auth/callback` with an error alert instructing the user to log in with credentials and link Google from Account Settings (FR-AUTH-010). Specify the pending token as a short-lived (~10 min), single-use, httpOnly cookie.

### 8. Auth lockout counter has no reset/decay
**Files:** `docs/requirements/user-accounts.md` (NFR-SEC-003), `docs/specs/api-design/rate-limiting.md` (Tier 1)
Failed attempts increment a per-IP counter and each failure doubles the lockout; successful operations "do not affect it" and nothing ever resets it. Read literally, an IP's lockout grows without bound forever — shared/NAT IPs eventually locked out permanently. The Redis key TTL is exactly the value the implementer must invent.
**Suggested resolution:** counter resets after a window without failures (e.g. 15 minutes); cap maximum lockout (e.g. 1 hour).

### 9. Alert-type events are listed as persisted SSE notifications
**Files:** `docs/requirements/notifications-invitations.md` (Definitions, FR-INV-006) vs `docs/specs/api-design/sse-notifications.md` (Notification Types, Offline Delivery)
The requirements define invitation accept/decline feedback as *alerts* — "never persisted... never shown in the notification center" — and session displacement similarly isn't a center item. Yet the SSE spec lists `INVITATION_ACCEPTED`, `INVITATION_DECLINED`, and `SESSION_DISPLACED` as `notification` events, and its offline-delivery model replays everything from the persistence store. Whether these three are persisted, replayed, counted in the unread badge, or shown in the center is contradictory between the two documents.
**Suggested resolution:** introduce an ephemeral event class on the SSE stream (e.g. `event: alert`, no persistence, no `Last-Event-ID` replay) for these three types; keep `event: notification` for persisted types only.

### 10. Friend request entity vs its notification — lifecycle coupling undefined
**Files:** `docs/requirements/social-friends.md` (FR-SOC-008, FR-SOC-013–015), `docs/requirements/notifications-invitations.md` (FR-FREQ-005, FR-NOTIF-005/006)
A pending friend request is visible in the Pending tab *and* delivered as a notification with inline actions, and its 30-day expiry is defined by the *notification* retention policy. But a user may delete any notification (FR-NOTIF-005) — does that decline the request, or does the request remain pending in the tab with no notification? Conversely, does acting from the Pending tab remove/mark the notification? The data-model split (one entity or two) can't be settled from the docs.
**Suggested resolution:** the friend request is its own entity with its own 30-day expiry; the notification is a pointer. Deleting the notification leaves the request pending; accepting/declining anywhere marks the linked notification read (and disables its actions). Same pattern for room invitations.

### 11. No mechanism defined for the client to learn it holds a reserved slot
**Files:** `docs/requirements/reconnection-flow.md` (FR-REJOIN-001/002), `docs/requirements/platform-views.md` (VW-ROOMS-005), `docs/specs/api-design/sse-notifications.md`
The pinned card on `/rooms` must appear "for as long as the player holds a reserved slot" — including after a full page reload or in another tab — and the transient alert targets "any tab/device with an active session." But the room WebSocket is precisely what was lost, and the SSE catalog has no disconnect/reserved-slot event type. No REST response is specified that carries "you hold a reserved slot in room X, N seconds remaining." The feature has no data source.
**Suggested resolution:** the tab that lost the WS renders the transient alert locally; add a reserved-slot field to a session-bootstrap/rooms-list REST response (e.g. `GET /api/me` → `reservedRoom: { roomId, gameName, graceRemainingSeconds }`), fetched on `/rooms` load.

### 12. UI library component set can't build the specified views
**Files:** `docs/requirements/platform-ui-library.md` (FR-COMP-001–010) vs `docs/requirements/platform-views.md`, `docs/requirements/social-friends.md` (FR-SOC-013, FR-SOC-017), `docs/requirements/game-catalog.md` (FR-CAT-010)
The views require: Tabs (profile History/Friends/Uploaded-games tabs, game-detail stats tab, Friends/Pending tabs), a Select/Dropdown (user menu, three-level friends visibility setting), Toggle/Checkbox (privacy and per-section visibility toggles, spectating option), and a Badge (Official/Verified, room status). None are in the component list, while token-only ESLint enforcement (FR-TOK-008, NFR-DX-004) makes ad-hoc one-off components exactly what the library exists to prevent. Separately, FR-COMP-006 Avatar (user image + online/offline indicator) contradicts user-accounts.md (avatars out of scope) and social-friends.md (presence out of scope). (Distinct from the tracked OQ-001–004, which cover exact token values only.)
**Suggested resolution:** add Tabs, Select, Switch/Checkbox, and Badge to the Must component set; reduce Avatar to initials-only or drop it for MVP.

## MINOR

**13. Session token mechanism (JWT vs opaque) unstated** — `user-accounts.md` FR-SESS-001–004; CLAUDE.md says "JWT auth." Single active session, displacement, and a displacement-specific error message all require server-side session state, which plain JWTs don't give you. Resolution: declare opaque server-side sessions (Postgres or Redis).

**14. Effect of session invalidation on live WS/SSE connections** — `websocket.md` validates the token only on STOMP CONNECT; whether displacement (FR-SESS-003) or logout closes already-open WebSocket/SSE connections is unspecified (a displaced user's game WS would otherwise stay live). Resolution: invalidation closes the user's WS and SSE; the WS close then drives the normal disconnect flow.

**15. "Room name" does not exist** — `platform-views.md` VW-ROOMS-005 says the pinned card shows "the room name"; `reconnection-flow.md` FR-REJOIN-002 says "room identifier"; rooms have no name attribute anywhere. Resolution: card shows game name + host username.

**16. Catalog version-column sort semantics** — `game-catalog.md` FR-CAT-007 allows sorting by version; lexicographic sort misorders `1.10.0` vs `1.9.0`. Resolution: store segments as integers or a zero-padded sortable column.

**17. "Active player count" definition** — `game-catalog.md` FR-GDET-005: "players currently in active rooms" — Lobby included? Spectators? AI? Resolution: human players in Lobby + In Progress rooms, excluding spectators and AI.

**18. Guest notification bell has nothing to show** — `platform-views.md` VW-NAV-005/VW-NOTIF-001 give guests the bell, but no type in `sse-notifications.md` can target a guest (no friends, no invites, no uploads, no re-login to displace). Resolution: hide the bell for guests, or explicitly accept the permanent empty state.

**19. Disconnect detection latency unspecified** — `reconnection-flow.md` FR-DC-001 hinges on WS loss, but no STOMP heartbeat interval is specified anywhere; half-open connections could take minutes to register, silently extending the effective grace period. Resolution: specify heartbeats (e.g. 10s/10s) in `websocket.md`.

**20. Account deletion while in a room / in-progress game** — `user-accounts.md` FR-ACCT-004: `/settings` is reachable mid-game; deletion's effect on the room/session is unspecified. Resolution: treat as an explicit leave (per gap #2's resolution) before purging.

**21. Missing input maxima** — password has no upper length bound (Argon2 CPU-DoS via megabyte passwords); email/search inputs likewise. Resolution: password ≤ 128 chars, email ≤ 254, general string caps in validation.

---

## Overall Verdict

This domain is close to implementable and well above typical Phase-0 quality — privacy matrices, guest semantics, the room WS protocol, chat, pagination, and the error taxonomy are specified to a level where an engineer needs to invent very little. The absence of a per-endpoint REST catalog is acceptable given the conventions plus code-first OpenAPI, with one exception: the OAuth completion handshake should be pinned down alongside gap #7. However, the room-lifecycle core has three genuine decision points (initial teams, voluntary-leave-vs-disconnect, last-human-host disconnect) where documents either say nothing or contradict each other, and those sit directly on the create-room → play → finish happy path — they must be resolved before implementation starts, not during it. The IMPORTANT items are each one-paragraph decisions (password change, logout, username rules, OAuth collision, lockout decay, alert-vs-notification split, friend-request/notification coupling, reserved-slot discovery, UI component set); resolving them is roughly a day of spec work. With those ~12 decisions written down, I'd consider the platform-core docs sufficient to build and ship the MVP without further invention.
