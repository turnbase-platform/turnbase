# Flow 01 — Arrival, Guest Account, Registration

Someone opens `https://turnbase.localhost:8080/` for the first time, plays as a guest, and later
registers. This is the shortest journey in the platform and the one that establishes the principal
every other flow assumes.

**Components:** browser, Platform Monolith, PostgreSQL, Redis.
No Game Host, no WebSocket until a room is entered.

---

## A. Unauthenticated arrival

| # | Actor | Action | Durable state |
|---|---|---|---|
| 1 | Browser | `GET /` | — |
| 2 | Monolith | No session cookie. Serves the landing page. `NFR-SEC-006` exempts `/` from authentication | — |
| 3 | Browser | Renders `VW-LAND-001…004`: description, **Login**, **Register**, **Play as Guest**. Nav shows `VW-NAV-001/002/007/008/009` only — no Active Rooms, no bell, no user menu | — |

The catalog is reachable from here without authenticating (`VW-CAT-001`, `NFR-SEC-006`), but
**Create Room is hidden** (`VW-CAT-003`, `FR-CAT-008`) — browsing is public, playing is not.

---

## B. "Play as Guest"

| # | Actor | Action | Durable state |
|---|---|---|---|
| 1 | Browser | `POST /api/auth/guest` | — |
| 2 | Monolith | **Tier 5 minting throttle** — `INCR rate:mint:guest:{ip}`, 5/hour, keyed on the /64 prefix for IPv6 (`rate-limiting.md`, `NFR-SEC-007`). Over budget → `429` and stop | Redis counter |
| 3 | Monolith | `nextval('guest_serial_seq')` → `N`; username `guest-N` | sequence advanced |
| 4 | Monolith | Compute `username_skeleton`; `INSERT INTO app_user (kind='GUEST', username, username_skeleton, guest_serial, …)` | **`app_user` row** |
| 5 | Monolith | `INSERT INTO user_session (session_id, user_id, expires_at = now() + 24h, key_id)` | **`user_session` row** |
| 6 | Monolith | Sign a JWT — `sub`, `jti = session_id`, `kid`, `exp` — and set it as an `httpOnly; Secure; SameSite=Strict` cookie (`CON-004`) | — |
| 7 | Monolith | `201`, `Location: /api/users/guest-N` | — |
| 8 | Browser | Redirects to `/rooms` (`VW-REDIR-004`) | — |

**No `user_auth_method` row is written**, and that is `FR-GUEST-004`: a guest has no authentication
method, so there is no login flow and the cookie issued here is the only key that will ever exist for
this account. Losing it loses the account.

**No `user_privacy_settings` row either.** A guest profile shows the username and nothing else
(`FR-GUEST-010`, `FR-PROF-002`), so there is nothing to configure —
[`data-model-accounts.md`](../platform/data-model-accounts.md) §4 makes "is this profile
configurable" an existence test rather than a value test.

**Step 2 counts successes, not failures**, which is the whole reason Tier 5 exists. `NFR-SEC-003`
counts only failed attempts, and guest creation always succeeds, so without a second counter one
address could mint unlimited fully-privileged principals.

### The guest's ceiling

| Can | Cannot |
|---|---|
| Browse the catalog, create and join rooms (`FR-GUEST-006`), play, chat, spectate | Have friends (`FR-GUEST-007`) — enforced by a foreign key, not a service check ([social §1](../platform/data-model-social.md)) |
| See the notifications bell (`VW-NAV-005`) | Receive any notification — every type requires friends, invitations or uploads, so the panel is always empty |
| View profiles | Upload games (`FR-GUEST-008`), accrue statistics or history (`FR-GUEST-009`, `FR-HIST-003`) |

---

## C. The 24-hour cliff

| # | When | What happens |
|---|---|---|
| 1 | `expires_at` passes | The next request's `jti` lookup finds an expired row → `401`. The browser redirects to `/login?redirect=…` (`VW-REDIR-007`) |
| 2 | Next guest-cleanup run (hourly, `FR-JOB-001`) | **Phase 1**: sessions revoked, `deleted_at`, `deletion_reason='GUEST_EXPIRED'`, `purgeable_after` set. Found via `app_user_guest_expiry_idx` |
| 3 | A later run, once nothing references the row | **Phase 2**: hard `DELETE FROM app_user` |

**Step 3 is not on a timer**, and this is the one place the arrival flow is more complicated than it
looks. `room_participant.user_id` and `room.host_user_id` are foreign keys with no cascade, and
closed rooms are retained for 7 days (`FR-RET-006`). A guest who played is still referenced, so a
literal 24-hour delete raises a foreign-key violation that recurs on every subsequent run, forever.

The cascade that would "fix" it is worse: it would let an identity-cleanup job silently remove a
seated participant from a live game. So the row waits, and `FR-RET-002` was amended to state the real
bound — *room closure + 7 days*, typically about 8 days.
[`data-model-accounts.md`](../platform/data-model-accounts.md) §1 has the full argument.

What holds unconditionally at 24 hours is **inaccessibility**, which is the property the requirement
exists to deliver.

---

## D. Registering instead

| # | Actor | Action | Durable state |
|---|---|---|---|
| 1 | Browser | `POST /api/auth/register` — username, email, password ×2 | — |
| 2 | Monolith | Tier 5, 3/hour per IP (`NFR-SEC-007`) | Redis counter |
| 3 | Monolith | Validate: `FR-AUTH-002` email shape, `FR-AUTH-005` length ≥ 8, `FR-AUTH-014` charset and 3–32, `FR-AUTH-015` single script | — |
| 4 | Monolith | Compute the confusable skeleton; reject if it starts with `guest-` (`FR-AUTH-013`, checked on the **skeleton**, so a Cyrillic lookalike is caught) | — |
| 5 | Monolith | Argon2id hash (`NFR-SEC-001`) — PHC string carries salt and cost inline | — |
| 6 | Monolith | One transaction: `app_user` (`kind='REGISTERED'`, `email_source='SELF'`) + `user_auth_method` (`method='PASSWORD'`) + `user_privacy_settings` (all defaults `PUBLIC`) | **three rows** |
| 7 | Monolith | Revoke any live session for this principal, insert a new one, set the cookie | **`user_session`** |

**A duplicate is a `409`** from one of two unique indexes, and which one matters:
`app_user_skeleton_key` is **total** — it spans soft-deleted rows, because `FR-ACCT-006` reserves a
deleted user's username permanently — while `app_user_email_key` is partial on `email IS NOT NULL`,
because `FR-ACCT-005` releases the address on deletion by nulling it.

So a deleted account's username is gone forever and its email is immediately reusable. That
asymmetry is deliberate and is visible to users.

`FR-AUTH-015` requires the rejection message for a confusable collision to be **identical** to a
plain duplicate, revealing nothing about which similar account exists.

### The guest→registered gap

There is **no upgrade path**. A guest who registers gets a new `user_id`, and their guest account
continues its 24-hour countdown independently. Nothing in the requirements describes carrying
anything across, and nothing could: a guest accrues no history and no statistics
(`FR-GUEST-009`, `FR-HIST-003`), so there is nothing to carry.

`kind` is therefore immutable, which is what lets the social tables pin it in a foreign key
([accounts §1](../platform/data-model-accounts.md)).

---

## E. OAuth, and the collision nobody had specified

| # | Actor | Action |
|---|---|---|
| 1 | Browser | **Continue with Google** → Google's consent screen, `state` carrying the post-login destination |
| 2 | Google | Redirects to `/auth/callback?code=…&state=…` |
| 3 | Monolith | Verifies `state` (signed, short-lived — it is attacker-influenceable input that returns as a redirect target), exchanges the code server-side using the client secret |
| 4 | Monolith | Looks up `user_auth_method` on `(method='GOOGLE', provider_subject=sub)` |
| 5a | — | **Found** → issue a session, redirect to `state`'s destination or `/rooms` |
| 5b | — | **Not found** → redirect to `/auth/complete-registration` with a short-lived pending token (Redis, not a table — its loss costs one repeat of the round trip) |
| 6 | Browser | `VW-OAUTHCOMP-001`: username form, provider email shown read-only |
| 7 | Monolith | Creates `app_user` (`email_source='OAUTH'`) + `user_auth_method` (`GOOGLE`) + privacy settings |

**Step 4 keys on Google's `sub`, never on the email.** `sub` is stable across the user renaming their
Google account; the email is not. Keying on email would let one Google identity attach to two
TurnBase accounts after a rename, and would turn an OAuth login into an email lookup — which is the
shape of the takeover `user_auth_method_subject_key` exists to prevent.

**Step 7 can collide**, and until this session nothing said what happens. If the provider's email is
already held by an active credential account, `app_user_email_key` raises a unique violation. Three
outcomes were possible and only one is right:

| Option | Verdict |
|---|---|
| Create a second account on the same email | Forbidden by `FR-AUTH-004` |
| Silently link and sign in | **Unsafe.** Controlling `alice@example.com` at Google is not proof of owning the TurnBase account that merely *registered* that address. Google verifies its own addresses; it does not vouch for who typed one into our form |
| Challenge for the existing account, then link | Correct |

`FR-AUTH-016` now specifies the third: authenticate against the existing account, link the Google
identity as an additional method (`FR-AUTH-009`), proceed. On failure, a generic message that does
not confirm which account exists.

The schema forces the question rather than permitting a silent duplicate — the unique index makes
"decide this" the only option.

---

## Defects surfaced

| Defect | Fix |
|---|---|
| Guest purge as written fails permanently on `room_participant`'s foreign key, and would recur hourly forever | Two-phase purge; `FR-RET-002` amended to state the real bound ([accounts §1](../platform/data-model-accounts.md)) |
| Guest purge checked only one of the two hard foreign keys — `room.host_user_id` has the same shape and guests may host (`FR-GUEST-006`) | Gate covers both |
| Phase 1 had no index that could find its candidates: `purgeable_after` is NULL until phase 1 has already run | `app_user_guest_expiry_idx` |
| OAuth email collision was unspecified — the schema made it a raw unique violation with no defined behaviour | **`FR-AUTH-016`** |
| No logout requirement existed at all, and logging out a guest destroys the account irrecoverably | **`FR-SESS-011`**, with a mandatory confirmation for guests |
| `NFR-SEC-003`'s lockout doubles without bound or decay — a shared address accumulates unrelated failures for days and reaches a lockout measured in weeks, with no password reset (`CON-003`) and no mail (`CON-002`) to recover through | Cap at 15 minutes, counter resets after 1 hour idle |
| Guests are shown the notifications bell (`VW-NAV-005`) but can receive no notification of any type | Recorded as a UI observation in [notifications §5](../platform/data-model-notifications.md); not a schema change |
