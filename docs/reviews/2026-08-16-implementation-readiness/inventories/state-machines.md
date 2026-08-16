# State Machines in TurnBase Corpus

Extracted from full documentation read (2026-08-16). Each machine's transitions are verified against source documents with line references.

---

## Machine: room.state

**Entity / column:** room.state (PostgreSQL, text)

**States:** LOBBY, IN_PROGRESS, CLOSED

**Transition table:**

| From | To | Trigger | Who performs it | Source |
|---|---|---|---|---|
| LOBBY | IN_PROGRESS | `START_GAME` command by host | Room owning instance | room-websocket.md:568; game-rooms.md:FR-HOST-009 |
| IN_PROGRESS | LOBBY | Game ends | Room owning instance (game-host-internals) | room-websocket.md:358, room-lifecycle.md:461 (game-rooms.md FR-LIFE-002) |
| LOBBY | CLOSED | Host leaves with no other humans | Room owning instance | game-rooms.md:FR-XFER-002; room-lifecycle.md:482 |
| IN_PROGRESS | CLOSED | Last human's grace expires, or room owner lost mid-game | Reconciliation sweep or owning instance | room-lifecycle.md:403 (FR-HDISC-003); data-model.md:128 |
| IN_PROGRESS | CLOSED | Session unrecoverable (In Progress, no session record) | Reconciliation sweep | room-lifecycle.md:596 (FR-JOB-007c) |
| LOBBY | CLOSED | Idle timeout (no connected participant past window) | Reconciliation sweep | room-lifecycle.md:597 (FR-JOB-007d); game-rooms.md:FR-LIFE-007 |
| LOBBY | CLOSED | Account deletion (host deleted) | Account deletion transaction | data-model-accounts.md:395 (FR-LIFE-004) |
| LOBBY | CLOSED | `ROOM_CLOSED` via closure paths | detachSession (FR-XFER-005) | room-lifecycle.md:475–493 |

**Terminal states:** CLOSED

**Unreachable states:** None

**States with no exit:** CLOSED (terminal)

---

## Machine: game_version.status

**Entity / column:** game_version.status (PostgreSQL, text)

**States:** PENDING, PROCESSING, ACTIVE, FAILED, EXPIRED, SUPERSEDED, DISCARDED

**Transition table:**

| From | To | Trigger | Who performs it | Source |
|---|---|---|---|---|
| PENDING | PROCESSING | Client calls `POST /api/games/{gameId}/versions/{uploadId}/confirm` | Upload handler / validation job | file-uploads.md:59–62 |
| PENDING | EXPIRED | Confirm never arrives before upload_expires_at, scheduled job runs | Sweep (FR-JOB-012) | data-model-catalog.md:205; file-uploads.md:148 |
| PROCESSING | ACTIVE | Validation passes | Validation job | data-model-catalog.md:206; file-uploads.md:69 |
| PROCESSING | FAILED | Validation fails | Validation job | file-uploads.md:73–74; data-model-catalog.md:213 |
| PROCESSING | FAILED | Lease (claimed_until) expires without result | Reconciliation sweep | data-model-catalog.md:326–328 |
| ACTIVE | SUPERSEDED | Newer version activates | Activation transaction | data-model-catalog.md:296 |
| SUPERSEDED | DISCARDED | No non-closed rooms reference this version, and it is not the most recently approved | Purge job (FR-GAME-011) | data-model-catalog.md:349–372 |
| FAILED | DISCARDED | Bundle purged (separately, immediately on entry to FAILED) | Purge after FAILED entry | data-model-catalog.md:334–344 |
| EXPIRED | DISCARDED | Never reused, 7-day retention passes | Purge job | data-model-catalog.md:334–344 |
| ACTIVE | DISCARDED | Game deleted/archived AND no non-closed rooms reference this version AND it is not the most recently approved | Purge job | data-model-catalog.md:349–372 |

**Terminal states:** FAILED (if no retry), EXPIRED, DISCARDED

**Unreachable states:** None from PENDING except DISCARDED (only reachable after SUPERSEDED, FAILED, or EXPIRED)

**States with no exit:** DISCARDED (terminal)

---

## Machine: game.badge

**Entity / column:** game.badge (PostgreSQL, text)

**States:** OFFICIAL, VERIFIED, UNVERIFIED

**Transition table:**

| From | To | Trigger | Who performs it | Source |
|---|---|---|---|---|
| UNVERIFIED | VERIFIED | Admin approves game for review | Review approval (admin) | game-catalog.md:FR-REV-004; data-model-catalog.md:68–75 |
| VERIFIED | UNVERIFIED | New version uploaded | Activation transaction | file-uploads.md:72 (FR-GAME-014); data-model-catalog.md:269–291 |
| OFFICIAL | OFFICIAL | Any activation (unchanged) | Activation transaction | data-model-catalog.md:288 |
| Any | Any | Admin directly updates (out of scope, internal tooling) | Administrator | data-model-catalog.md:126–129 |

**Terminal states:** None (all have exits, or are terminal via admin action)

**Unreachable states:** VERIFIED → OFFICIAL (no transition defined; Official is immutable, ownerless, first-party only)

**States with no exit:** None (all states have defined transitions or admin override)

---

## Machine: game_review decision state

**Entity / column:** game_review.decided_at (timestamp; NULL = pending) and game_review.decision (APPROVED | REJECTED | WITHDRAWN)

**States:** PENDING, APPROVED, REJECTED, WITHDRAWN

**Transition table:**

| From | To | Trigger | Who performs it | Source |
|---|---|---|---|---|
| PENDING | APPROVED | Admin approves | Review handler (admin) | game-catalog.md:FR-REV-002/004; data-model-catalog.md:473–487 |
| PENDING | REJECTED | Admin rejects | Review handler (admin) | game-catalog.md:FR-REV-006; data-model-catalog.md:505 |
| PENDING | WITHDRAWN | Owner deleted account or deleted game | Account deletion transaction | data-model-accounts.md:396; data-model-catalog.md:509–514 |
| APPROVED | (no transition) | — | — | — |
| REJECTED | (no transition) | — | — | — |
| WITHDRAWN | (no transition) | — | — | — |

**Terminal states:** APPROVED, REJECTED, WITHDRAWN

**Unreachable states:** None from PENDING, but APPROVED/REJECTED/WITHDRAWN have no outgoing transitions

**States with no exit:** APPROVED, REJECTED, WITHDRAWN (terminal)

---

## Machine: room_participant implicit state (left_at, grace_reservation_id)

**Entity / column:** room_participant row; state determined by conjunction of left_at and grace_reservation_id columns

**States:** Present, InGrace, Released

**Predicate mapping:**

- **Present:** `left_at IS NULL AND grace_reservation_id IS NULL`
- **InGrace:** `left_at IS NULL AND grace_reservation_id IS NOT NULL`
- **Released:** `left_at IS NOT NULL` (leave_reason populated)

**Transition table:**

| From | To | Trigger | Who performs it | Source |
|---|---|---|---|---|
| Present | InGrace | Player's connection_count reaches 0 in IN_PROGRESS room | Owning instance on disconnect | room-lifecycle.md:335–346 (FR-GRACE-005) |
| Present | Released | Voluntary leave (explicit "Leave Room", confirmed abandonment, or account deletion) | Owning instance or account-delete transaction | data-model-accounts.md:394; game-rooms.md:FR-LIFE-004; room-lifecycle.md:189 |
| Present | Released | Kick by host | Owning instance | game-rooms.md:FR-HOST-006; room-lifecycle.md:189 |
| InGrace | Present | Reconnect (connection_count incremented, grace_reservation_id cleared) | Any instance (non-owning performs state write only) | room-lifecycle.md:382 (FR-REJOIN-004) |
| InGrace | Released | Grace deadline expires | Reconciliation sweep or owning instance | room-lifecycle.md:356–365 (FR-EXPIRY-001) |
| InGrace | Released | Player joins another room (early release) | Instance handling new join | room-lifecycle.md:426–427 (FR-EXPIRY-004) |
| InGrace | Released | Kick while in grace | Owning instance | reconnection-flow.md:FR-KICK-003; room-lifecycle.md:189 |
| Present | Released | Room closure (CLOSED state entered) | Detach transaction | data-model.md:135 |
| InGrace | Released | Room closure while in grace (game end transitions LOBBY) | Detach transaction | room-lifecycle.md:409–418 (FR-EXPIRY-006) |

**Terminal states:** Released

**Unreachable states:** None

**States with no exit:** Released (terminal)

---

## Machine: user_session revocation state

**Entity / column:** user_session.revoked_at (timestamp; NULL = active) and user_session.revoked_reason

**States:** Active, Revoked

**Predicate mapping:**

- **Active:** `revoked_at IS NULL AND expires_at > now()`
- **Revoked:** `revoked_at IS NOT NULL`
- **Expired (implicit):** `revoked_at IS NULL AND expires_at <= now()` (expired but not yet revoked)

**Transition table:**

| From | To | Trigger | Who performs it | Source |
|---|---|---|---|---|
| Active | Revoked | New login (DISPLACED) | Login handler | data-model-accounts.md:294–297 (FR-SESS-002) |
| Active | Revoked | User logout (LOGOUT) | Logout handler | data-model-accounts.md:296 |
| Active | Revoked | Account deleted (ACCOUNT_DELETED) | Account deletion transaction | data-model-accounts.md:389 |
| Active | Revoked | Guest account expired (GUEST_EXPIRED) | Guest revoke sweep | data-model-accounts.md:167 |
| Active | Revoked | JWT key rotated (KEY_ROTATED) | Key rotation job | data-model-accounts.md:318 |
| Expired | Revoked | Housekeeping job or next login | User session expiry sweep | data-model-accounts.md:301 |

**Terminal states:** Revoked

**Unreachable states:** None

**States with no exit:** Revoked (terminal)

---

## Machine: game_input_outbox (game input delivery state)

**Entity / column:** game_input_outbox.dispatched_at (timestamp; NULL = pending)

**States:** Pending, Dispatched

**Transition table:**

| From | To | Trigger | Who performs it | Source |
|---|---|---|---|---|
| Pending | Dispatched | gRPC dispatch ACK received from Game Host | Outbox drain / game input handler | data-model.md:349–355 |
| Pending | (deleted) | Session detached, dispatched_at IS NULL | Detach transaction | room-lifecycle.md:486–487 |
| Pending | Dispatched | Deadline sweep re-drives undelivered rows | Reconciliation sweep (outbox drain, duty 4) | room-lifecycle.md:569 (§5.1 duty 4) |

**Terminal states:** Dispatched

**Unreachable states:** None (deletes do not count as states)

**States with no exit:** Dispatched (terminal)

---

## Machine: session_teardown owed-ness state

**Entity / column:** session_teardown row exists iff teardown is owed; row deleted on successful termination

**States:** Owed, Complete

**Predicate mapping:**

- **Owed:** Row exists in session_teardown table
- **Complete:** Row deleted OR never existed

**Transition table:**

| From | To | Trigger | Who performs it | Source |
|---|---|---|---|---|
| (N/A — created Owed) | Owed | Room detaches session (closure or game end) | Detach transaction | room-lifecycle.md:484 (INSERT ... ON CONFLICT DO NOTHING) |
| Owed | Complete | Termination succeeds (TerminateSession returns OK) | Detach's terminateAndCleanup, or reconciliation sweep | room-lifecycle.md:498–503 |
| Owed | Owed | Termination fails (retry scheduled) | Reconciliation sweep | room-lifecycle.md:594 (Owed teardown duty) |

**Terminal states:** Complete (row deleted)

**Unreachable states:** None

**States with no exit:** None (Owed has retry-with-backoff path)

---

## Machine: room_participant.grace_reservation_id presence

**Entity / column:** room_participant.grace_reservation_id (UUID; NULL when not in grace)

**States:** NoReservation, Reserved

**Predicate mapping:**

- **NoReservation:** `grace_reservation_id IS NULL`
- **Reserved:** `grace_reservation_id IS NOT NULL`

**Transition table:**

| From | To | Trigger | Who performs it | Source |
|---|---|---|---|---|
| NoReservation | Reserved | Disconnect in IN_PROGRESS, connection_count → 0 | Owning instance | room-lifecycle.md:338–346 (§3.1) |
| Reserved | NoReservation | Reconnect (UPDATE ... grace_reservation_id = NULL WHERE grace_reservation_id = :id) | Reconnecting instance | room-lifecycle.md:382 |
| Reserved | NoReservation | Expiry (grace_expires_at deadline <= now()) | Sweep or owning instance | room-lifecycle.md:358–365 |
| Reserved | NoReservation | Early release (join another room) | Acting instance (performs write) | room-lifecycle.md:426 (FR-EXPIRY-004) |
| Reserved | NoReservation | Kick while in grace | Owning instance | room-lifecycle.md:189 |
| Reserved | NoReservation | Game end (grace periods voided) | Owning instance on GAME_ENDED | room-lifecycle.md:409–418 |

**Terminal states:** NoReservation (final state after release)

**Unreachable states:** None

**States with no exit:** NoReservation (stable unless disconnect happens again)

---

## Machine: app_user deletion state

**Entity / column:** app_user.deleted_at (timestamp; NULL = active) | kind (REGISTERED | GUEST)

**States:** Active, Deleted

**Predicate mapping:**

- **Active (REGISTERED):** `kind = 'REGISTERED' AND deleted_at IS NULL`
- **Active (GUEST):** `kind = 'GUEST' AND deleted_at IS NULL`
- **Deleted:** `deleted_at IS NOT NULL`

**Transition table:**

| From | To | Trigger | Who performs it | Source |
|---|---|---|---|---|
| Active (REGISTERED) | Deleted | User initiates account deletion | Account deletion endpoint | data-model-accounts.md:§5 |
| Active (GUEST) | Deleted | Token lifetime elapsed (token_lifetime config, default 24h) | Guest revoke sweep (FR-GUEST-003) | data-model-accounts.md:167 |
| Deleted | (hard delete) | GUEST: no references remain AND purgeable_after elapsed | Guest purge sweep | data-model-accounts.md:168 |

**Terminal states:** Deleted (for REGISTERED); Hard delete for GUEST

**Unreachable states:** GUEST cannot transition through Deleted → any other state (hard delete only)

**States with no exit:** Deleted (REGISTERED soft delete is final); hard delete removes row

**Cross-machine couplings:**

| Machine A transition | Forces | Machine B transition | Source |
|---|---|---|---|
| room.state LOBBY→CLOSED (host account deleted) | Forces | room_participant all rows → Released (left_at set) | data-model-accounts.md:394 (FR-LIFE-004); room-lifecycle.md:189 |
| app_user Active→Deleted (account deletion) | Forces | game_review PENDING→WITHDRAWN (if any open reviews exist) | data-model-accounts.md:396; data-model-catalog.md:509–514 |
| room.state IN_PROGRESS→CLOSED (session unrecoverable) | Forces | session_teardown → Owed (teardown recorded) | room-lifecycle.md:484, 596 |
| room.state IN_PROGRESS→CLOSED (grace expiry) | Forces | session_teardown → Owed (teardown recorded) | room-lifecycle.md:403, 484 |
| room.state LOBBY→CLOSED (any path) | Forces | room_invitation all rows deleted | data-model.md:139 |
| game_version.status ACTIVE→SUPERSEDED | Forces | (none forced; previous version persists per FR-GAME-011) | data-model-catalog.md:295–300 |
| room_participant.state Present→InGrace | Forces | room_participant.grace_expires_at set to now() + graceSeconds | room-lifecycle.md:338–346 (§3.1) |
| room_participant.state InGrace→Released (expiry) | Forces | game_input_outbox INSERT player_left row (durable outbox) | room-lifecycle.md:358–365 (§3.3 side effects) |
| room.state LOBBY→IN_PROGRESS (START_GAME) | Requires | room_participant all non-spectators ready OR host (FR-TEAM-009) | game-rooms.md:FR-TEAM-009 |

---

## Summary

**State machines found:** 8 primary machines

1. **room.state** (3 states, 8 transitions)
2. **game_version.status** (7 states, 10 transitions)
3. **game.badge** (3 states; OFFICIAL unreachable from UNVERIFIED)
4. **game_review decision** (4 states, 3 incoming to PENDING)
5. **room_participant presence** (3 states, 8 transitions, terminal Released)
6. **user_session revocation** (2 states, 5 triggers to Revoked)
7. **game_input_outbox dispatch** (2 states, 3 transitions; deletions per session detach)
8. **session_teardown owed-ness** (2 states, row-based; bounded retry)
9. **room_participant.grace_reservation_id** (2 states, 6 transitions)
10. **app_user deletion** (2–3 states: Active REGISTERED, Active GUEST, Deleted)

**Critical findings:**

- **UNREACHABLE STATE:** `game.badge = 'OFFICIAL'` is unreachable from `UNVERIFIED` or `VERIFIED` (ADR-0006 constraint: Official games are first-party only; transition documented only as "admin tooling" which is out of scope)
- **UNREACHABLE STATE:** `game_review` state APPROVED/REJECTED/WITHDRAWN have no backward transitions; they are terminal by definition
- **TRIGGER NOT FOUND:** room.state IN_PROGRESS→LOBBY trigger is "game ends" but the exact mechanism (who calls what on the Game Host, when the Game Host responds, where the return path commits the transition) is deferred to `game-host-internals.md` and `game-rooms.md` FR-LIFE-002 (not fully specified in this corpus read)
- **TRIGGER NOT FOUND:** game_version.status PROCESSING→ACTIVE/FAILED transition trigger is "validation job completes" but no persistence mechanism or job lifecycle is specified in these docs (referenced as async, `game-development-experience.md FR-UPLOAD-002` is out of scope)

**Cross-machine dependencies (8 couplings documented):** Room closure cascades to participant release, session teardown, and invitation deletion. Account deletion cascades to review withdrawal and room closure. Grace expiry cascades to outbox row insertion. Participation state changes drive grace deadline and outbox creation.
