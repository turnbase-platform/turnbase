# Accounts, Authentication, Sessions, Guests, Social Graph — implementation-readiness audit

**Agent:** Sonnet 5 · **Files reviewed:** 8 owned (full) + 7 supporting (full or targeted) · **Date:** 2026-08-16

## Coverage

**Read in full (owned slice):**
- `docs/requirements/user-accounts.md`
- `docs/specs/platform/data-model-accounts.md`
- `docs/requirements/social-friends.md`
- `docs/specs/platform/data-model-social.md`
- `docs/specs/deployment/secrets-and-configuration.md`
- `docs/decisions/0004-account-erasure-pseudonymization.md`
- `docs/specs/flows/01-arrival-and-account.md`
- `docs/specs/api-design/input-validation.md`

**Read in full for cross-checking (not owned, but load-bearing for my scenarios):**
- `docs/specs/api-design/websocket.md` (full — to verify FR-SESS-010's connection-close mechanism)
- `docs/decisions/0001-local-first-mvp-platform.md` (full — to resolve single-instance vs multi-pod question)
- `docs/specs/INDEX.md` lines 1–51 (citation-qualification rule)
- `docs/requirements/platform-architecture.md` FR-SESS block (grep, lines 98–105 — the colliding definitions)

**Targeted / grep-only (not owned, used only to verify a specific citation or confirm absence):**
- `docs/requirements/notifications-invitations.md` (FR-INV-*, FR-FREQ-* table rows)
- `docs/requirements/platform-views.md` (VW-PROF-*, VW-FREN-*, VW-SET-* rows — profile and friends page view tables)
- `docs/specs/api-design/rest-conventions.md` (auth endpoint table, password-related grep)
- `docs/requirements/platform-operations.md` (NFR-SCALE-001, FR-MET-005 — MVP instance count)

**Not checked:** `docs/specs/platform/data-model-catalog.md` §4 (`game_review` erasure disposition) — cited from my erasure table but owned by the rooms/catalog slice; I trust the citation exists and did not verify its content. `docs/specs/platform/data-model-notifications.md` — same, cited but not independently read.

## Summary

| # | Severity | One-line | Location |
|---|---|---|---|
| 1 | BLOCKER | Profile/friends view tables give the account owner no exception from their own privacy settings, contradicting FR-PROF-007/FR-SOC-018 | `docs/requirements/platform-views.md:294-306,319-325` |
| 2 | GAP | Plain credential login (FR-AUTH-006) is never traced end-to-end anywhere, unlike guest/register/OAuth in the same flow doc | `docs/specs/flows/01-arrival-and-account.md` (missing section) |
| 3 | GAP | FR-SESS-010's live-connection closure is asserted four times but the actual mechanism (which API locates and disconnects a specific STOMP session) is never named | `docs/requirements/user-accounts.md:56`, `docs/specs/platform/data-model-accounts.md:320-323`, `docs/specs/deployment/secrets-and-configuration.md:144-149`, `docs/specs/api-design/websocket.md:54` |
| 4 | GAP | FR-SOC-015 (outgoing pending requests + Cancel) and FR-SOC-016 (profile button 3-state machine) have no view specification anywhere | `docs/requirements/platform-views.md:310-325` |
| 5 | AMBIGUITY | Multiple cross-document `FR-SESS-00x` citations in my owned docs are unqualified despite `FR-SESS-*` colliding with `platform-architecture.md`'s unrelated Game Host definitions | `docs/specs/platform/data-model-accounts.md:167,292,296,308`, `docs/specs/deployment/secrets-and-configuration.md:112,149,165` |
| 6 | GAP | Argon2id is fixed as the algorithm but no cost parameters (memory/time/parallelism) are specified anywhere | `docs/requirements/user-accounts.md:108`, `docs/specs/api-design/input-validation.md:107-115` |
| 7 | GAP | FR-ACCT-010 (password change) has no REST route in `rest-conventions.md`, unlike every other auth endpoint | `docs/requirements/user-accounts.md:71` (no realization found) |
| 8 | DRIFT | Erasure traceability table cites `FR-INV-002` ("friends-only restriction") for room-invitation deletion — wrong requirement, right behaviour | `docs/specs/platform/data-model-accounts.md:392` |

## Findings

### F1 — BLOCKER — Owner has no documented exception from their own privacy settings

**Where:** `docs/requirements/user-accounts.md:81,84` (FR-PROF-004, FR-PROF-007), `docs/requirements/social-friends.md:61` (FR-SOC-018), `docs/requirements/platform-views.md:294-306,319-325`, `docs/specs/platform/data-model-accounts.md:333-376` (§4 `user_privacy_settings`)

**Quotes:**
> "A user always sees all sections of their own profile regardless of privacy setting or per-section visibility configuration." (user-accounts.md:84, FR-PROF-007)
> "The Friends section (both tabs) is always fully visible to the profile owner regardless of the configured visibility level." (social-friends.md:61, FR-SOC-018)
> `| ID | Element / Action | Condition | Unauth | Guest | Registered |` ... `| VW-PROF-002 | Profile section — statistics | Public profile; statistics section not hidden | Visible | Visible | Visible |` (platform-views.md:294-297)
> `| VW-PROF-003 | "Profile is private" message | Private registered profile | Visible | Visible | Visible |` (platform-views.md:301)

**Blocks:** the profile-page GET handler / view-model assembly (whatever renders `/users/:username`) and the friends-section renderer. An implementer building the visibility-resolution function described in `data-model-accounts.md` ("one resolution function over four identically-shaped values") has no rule anywhere telling it to special-case `viewer_id == profile.user_id`.

**Scenario:** A registered user sets `profile_private = true` (FR-PROF-004), then navigates to their own profile page while authenticated. `platform-views.md`'s condition column is keyed only on profile state and viewer *class* (Unauth/Guest/Registered) — there is no "Owner" column or condition branch. Read literally, "Private registered profile" satisfies VW-PROF-003's condition regardless of who the "Registered" viewer is, so the owner is shown "This profile is private" instead of their own game history, stats, friends and uploaded games — directly violating FR-PROF-007 and, for the friends section specifically, FR-SOC-018. `data-model-accounts.md` §4 documents the four-value resolution function in detail (public/hidden/friends-only) but never mentions an owner override either; the column data is there (`profile_private`, per-section enums) but nothing says the read path must compare `viewer_id` to `user_id` before consulting them.

**Suggested resolution:** `platform-views.md`'s Profile and Friends view tables should add an explicit "Owner" condition/column (or a note under the table) stating the owner bypass, citing FR-PROF-007/FR-SOC-018 by qualified ID. Alternatively, `data-model-accounts.md` §4 could state the read-path rule directly ("the resolution function returns 'visible' unconditionally when `viewer_id = user_id`, before consulting any of the four columns") since that document already owns the description of the resolution function's shape. This finding spans the accounts/social slice and the (unowned-by-me) views slice; whoever owns `platform-views.md` should also see it.

---

### F2 — GAP — No end-to-end trace of credential login

**Where:** `docs/specs/flows/01-arrival-and-account.md` (whole document — sections A–E cover arrival, guest, guest expiry, registration, OAuth; there is no login section), `docs/specs/api-design/rest-conventions.md:64`

**Quotes:**
> "Someone opens `https://turnbase.localhost:8080/` for the first time, plays as a guest, and later registers. This is the shortest journey in the platform and the one that establishes the principal every other flow assumes." (01-arrival-and-account.md:3-4)
> `| POST /api/auth/login | Revokes any existing session for the account, issues a new one (FR-SESS-002/003) |` (rest-conventions.md:64 — the entire specification of the login endpoint, one table row)

**Blocks:** the `POST /api/auth/login` controller and the credential-authentication service (username-or-email lookup, Argon2 verification, NFR-SEC-003 lockout integration).

**Scenario:** An implementer tasked with building login has: (a) the requirement text (FR-AUTH-006 — login by username or email + password), (b) one table row in `rest-conventions.md` saying it revokes-and-reissues a session, (c) the revoke-then-insert transaction pattern in `data-model-accounts.md` §3 (written primarily to explain the unique-index mechanics, not as a login walkthrough), and (d) NFR-SEC-003's lockout rule in `user-accounts.md`. Nothing traces the actual sequence: look up by username OR email (which query, case-sensitivity of the lookup vs. FR-AUTH-004's case-insensitive email uniqueness), verify password against `user_auth_method` where `method='PASSWORD'`, what happens when the account has no PASSWORD row (an OAuth-only account attempting credential login), how a failed attempt is recorded against the Tier 1 IP counter, and what the success/failure response bodies look like. Every other principal-creation path (guest, registration, OAuth) gets a full numbered step table in this exact document; login — the single most common request in the system — does not. This is derivable by assembly from multiple documents (none of it is actually undecided), so it is a GAP rather than a BLOCKER, but it is the one path in "the flow that establishes the principal every other flow assumes" that isn't walked.

**Suggested resolution:** Add a "F. Logging in" section to `01-arrival-and-account.md` mirroring the structure of section D, tracing: lookup, Tier 1 rate-limit check, password verification, the revoke/insert transaction, and the account-with-no-password-method case.

---

### F3 — GAP — FR-SESS-010's connection-close mechanism is stated four times, never named

**Where:** `docs/requirements/user-accounts.md:56` (FR-SESS-010), `docs/specs/platform/data-model-accounts.md:320-323`, `docs/specs/deployment/secrets-and-configuration.md:144-149`, `docs/specs/api-design/websocket.md:54`

**Quotes:**
> "Every path that invalidates a session ... must therefore also close that session's live connections, after emitting a frame stating the reason. Without this, a displaced session keeps receiving room events, holds a reserved slot, and can continue to act in a game it is no longer authorized for." (user-accounts.md:56, FR-SESS-010)
> "The closing of those connections is a behaviour, not a column, and is specified in `user-accounts.md` FR-SESS-010 and [`../api-design/websocket.md`]" (data-model-accounts.md:322-323)
> "The revocation path pushes a `SESSION_INVALIDATED` frame and closes, which is `user-accounts.md` FR-SESS-010 and the same mechanism FR-SESS-003's displacement uses." (secrets-and-configuration.md:147-149)
> `| /user/queue/errors | server→client | Individual user | Per-user errors: kicked from room, rejected command, session displaced by new login |` (websocket.md:54 — the only mention of displacement in the WebSocket spec itself, and it names only the destination, not the trigger mechanism)

**Blocks:** the session-revocation service (whatever code path runs on login-displacement, logout, account deletion, guest expiry, and key retirement) needs to locate the STOMP session(s) belonging to a given `user_id`/`session_id` from a plain HTTP request handler thread and force-close them. This is architecturally non-trivial: it is not the same thread or session as the one issuing the revocation.

**Scenario:** Player A is mid-game with an open STOMP connection. Someone (attacker or A themself) logs in from a second device, triggering FR-SESS-003 displacement. The login request is handled inside an `AuthController` — a completely different execution context from A's already-established WebSocket session. Every document that touches this (four locations above, across three files I own plus one I don't) states *that* the connection must close and *what frame* it receives, but none names *how* the login handler reaches into an unrelated, already-open STOMP session to disconnect it. Contrast this with the corpus's own standard elsewhere: `websocket.md`'s game-session protocol names exact Spring mechanisms throughout (`SimpMessageHeaderAccessor.getUser()`, `ChannelInterceptor`, `SimpMessagingTemplate.convertAndSend`, `SimpUserRegistry`-style principal resolution is implied but never spelled out here). I confirmed via `platform-operations.md` NFR-SCALE-001 ("the MVP runs a single local instance") and FR-MET-005 ("Redis is not used for WebSocket pub/sub — effect fan-out is in-process") that this is *not* a cross-pod problem for the MVP — a single JVM holds every open connection — which makes the omission smaller than it would otherwise be (no distributed coordination is needed), but the concrete question of "which bean, which method" for a same-JVM, cross-thread session lookup-and-disconnect is still never answered.

**Suggested resolution:** A short addition to `websocket.md`'s Authentication section (or a new subsection) naming the mechanism — e.g. a `SimpUserRegistry` lookup by principal plus `disconnect()` on the located session(s), or a custom `ConcurrentHashMap<UUID, WebSocketSession>` maintained by the auth layer — resolving FR-SESS-010 the same way `websocket.md` resolves every other cross-cutting WS concern.

---

### F4 — GAP — FR-SOC-015 and FR-SOC-016 have no view specification

**Where:** `docs/requirements/social-friends.md:53-54` (FR-SOC-015, FR-SOC-016), `docs/requirements/platform-views.md:294-306` (Profile page), `docs/requirements/platform-views.md:310-325` (Friends page)

**Quotes:**
> "The Pending tab also shows all outgoing friend requests the user has sent that have not yet been accepted or declined, each with a Cancel action." (social-friends.md:53, FR-SOC-015)
> "On a registered user's public profile, the 'Send friend request' button is replaced with contextual state labels: **Friends** (with an Unfriend action), **Request sent** (with a Cancel action), or **Request received** (with Accept / Decline actions)." (social-friends.md:54, FR-SOC-016)
> `| VW-FREN-004 | Pending incoming friend requests list | Visible |` `| VW-FREN-005 | Accept / Decline friend request | Enabled |` (platform-views.md:324-325 — no outgoing-request row, no Cancel action, no tab structure at all despite FR-SOC-013 requiring two tabs)
> `| VW-PROF-006 | Add Friend button | Other registered user; not already friends | Hidden | Hidden | Enabled |` `| VW-PROF-007 | Remove Friend button | Viewing a friend's profile | Hidden | Hidden | Enabled |` (platform-views.md:304-305 — only two of the four FR-SOC-016 states are represented; "Request sent"/Cancel and "Request received"/Accept-Decline are absent)

**Blocks:** the `/friends` page component (outgoing-pending section) and the profile-page friend-request button component — both frontend, both directly reader of `platform-views.md` as their spec of record.

**Scenario:** A frontend implementer builds the Friends page from `platform-views.md`'s VW-FREN table alone (as the convention throughout the corpus directs — "views" documents are the UI spec of record). They render a friend list and an incoming-requests list, matching VW-FREN-001/004/005 exactly, and never build the outgoing-pending section or its Cancel action, because no view ID describes it. Separately, the profile page implementer renders exactly two button states (Add/Remove) from VW-PROF-006/007 and never builds "Request sent" or "Request received," because FR-SOC-016's other two states have no view row. Both are `social-friends.md` Must requirements with zero view-layer realization I can find.

**Suggested resolution:** Add view IDs to `platform-views.md`'s Friends and Profile sections for the missing states, citing `social-friends.md` FR-SOC-015/016 by qualified ID. This is outside my owned slice (`platform-views.md` belongs to whichever agent covers views/frontend) but the requirement IDs are mine, so I'm flagging it here per the task's explicit instruction to check FR-SOC-015/016 for realization anywhere in the corpus.

---

### F5 — AMBIGUITY — Unqualified cross-document `FR-SESS-*` citations, resolvable only by reading prose

**Where:**
- `docs/specs/platform/data-model-accounts.md:167` — "FR-GUEST-003, which defers the value to FR-SESS-001"
- `docs/specs/platform/data-model-accounts.md:292` — "The partial unique index is FR-SESS-002."
- `docs/specs/platform/data-model-accounts.md:296` — "FR-SESS-003 falls out of the same statement"
- `docs/specs/platform/data-model-accounts.md:308` — "cannot satisfy FR-SESS-003, which requires an *immediate* invalidation"
- `docs/specs/deployment/secrets-and-configuration.md:112` — "token lifetime does not extend with activity (FR-SESS-001)"
- `docs/specs/deployment/secrets-and-configuration.md:149` — "the same mechanism FR-SESS-003's displacement uses"
- `docs/specs/deployment/secrets-and-configuration.md:165` — "FR-SESS-003's 'immediately invalidated' requires"

**Quotes:**
> "Requirement IDs are numbered per document and collide across the corpus... `FR-SESS-003` is defined in both `platform-architecture.md` (Game Host in-memory state) and `user-accounts.md` (login displaces the previous session) with no relationship between them. ... Every cross-document citation must therefore carry a document qualifier" (INDEX.md:33-37)
> `| FR-SESS-002 | Session-to-context binding | Each session is bound to a specific Truffle context...` (platform-architecture.md:99 — the *other* FR-SESS-002, Game Host, completely unrelated to "single active session")

**Blocks:** nothing directly — each citation above is I own and each resolves correctly to the intended `user-accounts.md` requirement *by content* (the surrounding prose quotes or paraphrases the actual `user-accounts.md` text closely enough that a careful reader cannot land on the Game Host definition). But this is exactly the case the citation rule in `INDEX.md` exists to prevent, and I was asked to specifically hunt for it in my slice.

**Scenario:** A low-reasoning-effort implementation agent reading `data-model-accounts.md:292` ("The partial unique index is FR-SESS-002") in isolation, or grepping the corpus for "FR-SESS-002" to find the authoritative definition, will find two: `user-accounts.md`'s "Single active session" and `platform-architecture.md`'s "Session-to-context binding" (Game Host, Truffle contexts). Nothing at the citation site names which document to look in. In every instance I found, the surrounding paragraph's content makes the correct document unambiguous to a careful human reader — so none of these is a BLOCKER under the brief's own criterion ("resolves to the wrong one is a BLOCKER") — but a low-effort agent that resolves citations by ID lookup rather than by reading the paragraph is exactly the failure mode this rule anticipates.

**Suggested resolution:** Qualify all seven citations with `` `user-accounts.md` `` per the existing convention already used correctly at `secrets-and-configuration.md:131` and `:148`. Cheap, mechanical fix.

---

### F6 — GAP — Argon2id cost parameters unspecified

**Where:** `docs/requirements/user-accounts.md:108` (NFR-SEC-001), `docs/specs/api-design/input-validation.md:107-115`, `docs/specs/platform/data-model-accounts.md:243-247`

**Quotes:**
> "Passwords must be hashed using Argon2 (or equivalent strong adaptive hashing algorithm) with a unique random salt per user." (user-accounts.md:108, NFR-SEC-001)
> "The platform therefore uses **Argon2id** (`Argon2PasswordEncoder`), which has no such limit." (input-validation.md:114)
> "the inline parameters are what makes a cost increase a rehash-on-next-login rather than a migration" (data-model-accounts.md:246-247)

**Blocks:** the `PasswordEncoder` bean definition (`Argon2PasswordEncoder(saltLength, hashLength, parallelism, memory, iterations)`).

**Scenario:** The algorithm is pinned unambiguously (Argon2id, via Spring's `Argon2PasswordEncoder`), and the corpus is explicit that cost parameters are expected to change over time (the "rehash-on-next-login" remark presupposes a specific starting cost that later increases). But no document states starting values for memory cost, iteration count, or parallelism. An implementer will use whatever Spring's no-arg/factory-method default happens to be (Spring Security 6's `Argon2PasswordEncoder.defaultsForSpringSecurity_v5_8()` — memory 1<<16 KB, iterations 2, parallelism 1 — or, if they call the plain constructor, meaningfully weaker defaults). This does not produce incorrect *behavior* (login/verification still works), so it is not a BLOCKER, but it is the one place the brief explicitly asked me to check ("is the algorithm and its parameters actually specified, or assumed?") and the parameters are assumed.

**Suggested resolution:** State a concrete starting Argon2id parameter set (e.g., OWASP's current recommendation) in `input-validation.md` or `user-accounts.md` NFR-SEC-001, alongside the existing algorithm choice.

---

### F7 — GAP — FR-ACCT-010 (password change) has no REST route

**Where:** `docs/requirements/user-accounts.md:71` (FR-ACCT-010), `docs/specs/api-design/rest-conventions.md` (grepped in full for "password" — zero matches)

**Quotes:**
> "A user with a credential auth method may change their password from account settings by supplying their current password and the new password twice." (user-accounts.md:71, FR-ACCT-010)
> `| /api/users/me/** | Implicit — the principal *is* the resource. No user id is ever accepted in the path for a self-scoped operation | — |` (rest-conventions.md:91 — the only thing that could be read as covering it, and it is a generic convention statement, not a route)

**Blocks:** the password-change controller (method, path, request/response DTOs).

**Scenario:** Every other write-heavy auth operation (login, guest, logout) has an explicit row in `rest-conventions.md`'s endpoint table with its exact path and a one-line description of its session-management side effect. Password change — arguably the single highest-value target for an attacker with a stolen session — has no such row anywhere. `FR-ACCT-010`'s own text is otherwise very complete (verify-current-password rationale, hashing, session semantics, lockout interaction), so the *behavior* is fully specified; only the transport binding (verb + path) is missing. An implementer will infer something plausible from the `/api/users/me/**` convention (e.g. `PATCH /api/users/me/password` or `POST /api/users/me/password`), and picking the "wrong" one produces no functional defect, only an unreviewable inconsistency with whatever the rest of the API settled on. AMBIGUITY-adjacent, but reported as GAP because nothing pins the choice down at all.

**Suggested resolution:** Add a row to `rest-conventions.md`'s auth/account endpoint table for password change, citing FR-ACCT-010.

---

### F8 — DRIFT — Erasure traceability table cites the wrong FR-INV requirement

**Where:** `docs/specs/platform/data-model-accounts.md:392`, `docs/requirements/notifications-invitations.md:58-59`

**Quotes:**
> `| room_invitation | all rows deleted, **both** as inviter and as invitee | FR-ACCT-005 (amended), FR-INV-002 |` (data-model-accounts.md:392)
> `| FR-INV-002 | Friends-only restriction | Platform invitations may only be sent to players who are friends with the host. |` (notifications-invitations.md:59 — the actual, unrelated content of the cited ID)

**Blocks:** nothing — the operation described in the row itself ("all rows deleted, both as inviter and as invitee") is correct and matches `FR-ACCT-005`'s own prose in `user-accounts.md:67` ("all room invitations the user sent or received (notifications-invitations.md FR-INV-001)"), which correctly cites FR-INV-001 instead. The citation error is confined to this one traceability-table cell.

**Scenario:** An implementer or reviewer who follows the `FR-INV-002` link from this table row to verify the deletion behavior against its source requirement finds "Friends-only restriction" — a requirement about *sending* invitations, not erasure — and either wastes time reconciling the mismatch or (worse, for a low-effort agent) concludes the erasure behavior is unsourced and invents its own. The correct reading is recoverable from `FR-ACCT-005`'s own text one document over, which is why this is DRIFT and not a BLOCKER.

**Suggested resolution:** Change the citation to `FR-ACCT-005 (amended), FR-INV-001` (or drop the FR-INV reference entirely, since FR-ACCT-005 already carries it correctly).

---

## What checked out

- **Registration → uniqueness → error surface.** `FR-AUTH-003/004` (username/email uniqueness) are both database constraints (`app_user_skeleton_key` total unique index; `app_user_email_key` partial on `email IS NOT NULL`), not application-only checks. The 409 conflict path is traced explicitly in `01-arrival-and-account.md` §D with the asymmetry (soft-deleted username reserved forever vs. released email) called out and consistent with `FR-ACCT-005/006`.
- **Guest → registered has no upgrade path, and the corpus is consistent about it everywhere it's mentioned** (flow §D, `data-model-accounts.md` §1's "`kind` is immutable" note, the FK design pinning `kind='REGISTERED'` in the social tables). No document implies otherwise.
- **Guest two-phase purge.** Trigger, query, and effect are fully specified for both phases (`data-model-accounts.md` §1 table), consistently cross-referenced from `01-arrival-and-account.md` §C, and the "guest seated in a live room cannot be hard-deleted" property is guaranteed structurally (both `room_participant.user_id` and `room.host_user_id` gate phase 2, with the corpus explicitly noting the second FK was a defect fixed in an earlier session). `FR-RET-002`'s amendment ("room closure + 7 days, not literally 24h") is stated candidly rather than glossed over.
- **JWT key rotation.** `secrets-and-configuration.md` §3 is fully self-contained and consistent with `data-model-accounts.md` §3's `key_id`/`revoked_reason='KEY_ROTATED'` columns: key set structure, promote/wait/retire steps, the emergency-rotation shortcut, and the claims shape (`sub`/`jti`/`kid`/`iat`/`exp`, deliberately excluding username/role) are all concretely specified. `user_session.key_id` gives verification exactly what it needs to accept `active` or any `retired` key without a mass logout.
- **Account erasure scatter (the scenario 4 checklist).** `data-model-accounts.md` §5 gives every object in the scenario an explicit disposition: hosted room (closed if last human, else host transfer — FR-XFER-002/FR-LIFE-004), pending friend request (deleted both directions — FR-SOC-012), game history (pseudonymized via a fresh random token, explicitly *not* HMAC-derived, with the reversibility argument spelled out — ADR-0004), open game review (withdrawn, third decision value, not deleted), and room invitation on both legs (deleted, with the reasoning for why *both* legs matter). The "nothing happens by cascade" framing is checked against the actual FK cascade list, and the four items the document says were "missing from the first draft" are all present now — the erasure-scatter defect mentioned in the task appears genuinely fixed, modulo the F8 citation slip.
- **OAuth email collision.** `FR-AUTH-016` gives one clear answer (challenge-then-link) among three considered options, consistently narrated in both `user-accounts.md` and `01-arrival-and-account.md` §E, backed by the `app_user_email_key` unique index that forces the case to be handled rather than silently admitted.
- **Social graph schema.** Guest exclusion from friendship is a foreign-key constraint, not a service check (`data-model-social.md` §1); the friend cap is correctly *not* a DB constraint given its configurability requirement (NFR-SOC-SCALE-001) and its asymmetric enforcement (blocks sending, not receiving) is faithfully reflected; reverse-request auto-accept (FR-SOC-004) is implemented as opposite-row detection with no second row ever written; the friend-request/notification coupling (FR-FREQ-006) is a single documented mechanism, not two independently-timed objects.

## Requirement-ID audit results (task-specified checks)

- **FR-ACCT-010, FR-PROF-001, FR-PROF-004:** behavior specified in `user-accounts.md`; realized in schema (`data-model-accounts.md` §4) or inferable from generic conventions (`FR-ACCT-010`'s route — see F7). Not blocking.
- **FR-PROF-007:** genuinely unrealized anywhere — see F1 (BLOCKER).
- **FR-SOC-007:** realized (compressed citation `FR-SOC-005/007/008` in `data-model-social.md:211` — my initial grep for the literal string "FR-SOC-007" missed this because the traceability table compresses adjacent IDs; re-verified by reading the table directly). Not a gap.
- **FR-SOC-015, FR-SOC-016:** genuinely unrealized in any view spec — see F4 (GAP).
- **FR-SOC-018:** genuinely unrealized — folded into F1 (BLOCKER) alongside FR-PROF-007, same underlying defect (no owner-bypass anywhere in the privacy/visibility model).
