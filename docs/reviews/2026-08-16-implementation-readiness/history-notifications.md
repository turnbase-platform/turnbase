# Game history, per-game statistics, notifications & invitations — implementation-readiness audit

**Agent:** Sonnet 5 · **Files reviewed:** 15 in full (9 owned + 6 cross-checked) · **Date:** 2026-08-16

## Coverage

Read in full (owned slice):
- `docs/requirements/game-history.md`
- `docs/specs/platform/data-model-history.md`
- `docs/requirements/per-game-statistics.md`
- `docs/requirements/notifications-invitations.md`
- `docs/specs/platform/data-model-notifications.md`
- `docs/specs/api-design/sse-notifications.md`
- `docs/specs/api-design/pagination-filtering-sorting.md`
- `docs/decisions/0004-account-erasure-pseudonymization.md`
- `docs/specs/flows/06-game-end-and-rematch.md`

Read in full for cross-verification (not owned, but load-bearing for scenarios 3–6):
- `docs/requirements/platform-operations.md` (retention table, all `FR-JOB-*`)
- `docs/specs/platform/data-model.md` (room closure-reason table §1)
- `docs/specs/platform/data-model-social.md` (`friend_request`/`friendship`)
- `docs/requirements/game-contracts.md` (`FR-OUTCOME-*`, `FR-EFF-*`)
- `docs/specs/platform/data-model-accounts.md` §5 (erasure per-table breakdown)
- `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` (`GameOutcome` validation section)

Sampled (targeted grep, not read in full): `docs/specs/flows/07-room-closure.md` (confirmed `DELETE FROM room_invitation` step exists), `docs/specs/deployment/schema-migrations.md` §5 (confirmed `btree_gin`/`pg_trgm` baseline extensions), `docs/requirements/user-accounts.md` (`FR-ACCT-005/008/009` only).

**Not checked:** the FE-facing `platform-views.md` requirements doc (history tab / stats placement UI) beyond confirming it exists — the FR-HIST-020s/FR-STATS-01xs are self-contained enough in the requirements documents themselves that I did not chase a separate design spec for them (see "What checked out"). Datastore-outage-during-`game_over` behavior (what happens if Postgres is unreachable at the moment of recording, as opposed to a malformed outcome) was not traced — it depends on `platform-architecture.md`/`FR-FAIL-*` failure handling, which is outside this slice.

## Summary

| # | Severity | One-line | Location |
|---|---|---|---|
| 1 | BLOCKER | No scheduled job purges expired `friend_request`/`room_invitation` rows — three docs assume "the purge job" exists; `platform-operations.md`'s job list has none | `docs/requirements/platform-operations.md:140-156` |
| 2 | GAP | Offset-based pagination is mandated platform-wide, including for the notification center, a list under continuous real-time insert — page-drift under concurrent insert is nowhere addressed | `docs/specs/api-design/pagination-filtering-sorting.md:5-32` |
| 3 | DRIFT | `GameOutcome` structural-validation checklist is narrower in `game-history.md`/`data-model-history.md`/flow-06 than in the internal-grpc spec (missing placement-ranking and team-id-membership checks) | `docs/specs/internal-grpc/orchestration-gamehost-protocol.md:308-315` vs `docs/specs/platform/data-model-history.md:172-175` |
| 4 | NIT | Broken cross-reference: `FR-ALERT-006` does not exist (almost certainly meant `FR-ALERT-010`) | `docs/specs/api-design/sse-notifications.md:18` |

## Findings

### F1 — BLOCKER — No scheduled job actually purges expired `friend_request` or `room_invitation` rows

**Where:** `docs/requirements/platform-operations.md:140-156` (the full Scheduled Jobs section, `FR-JOB-001`…`FR-JOB-012`), `docs/specs/platform/data-model-social.md:152`, `docs/specs/platform/data-model-notifications.md:199`, `docs/requirements/notifications-invitations.md:66,76-77`.

**Quotes:**
> "`friend_request_expiry_idx` serves the purge job. Unlike the room sweeps it is not partial — every row in this table has a deadline" (`data-model-social.md:152`)
> "That rule closes for `FRIEND_REQUEST` only because `friend_request` carries `expires_at` **and a purge job**, so every request is guaranteed a deleter." (`data-model-notifications.md:199`)
> "An expired friend request is automatically purged with no further action." (`notifications-invitations.md:76`, FR-FREQ-005)
> "A room invitation expires after the same configurable window as notification retention (default 30 days) **and is then deleted** along with its notification." (`notifications-invitations.md:66`, FR-INV-009)

`platform-operations.md`'s Scheduled Jobs section is the corpus's single canonical list of jobs (`FR-JOB-001` guest cleanup, `FR-JOB-002` notification purge, `FR-JOB-003`…`FR-JOB-012`). I read all twelve entries in full. `FR-JOB-002` purges the `notification` table only, keyed on `created_at`, and is explicitly `notification_purge_idx`-scoped — it is partial on `friend_request_id IS NULL AND invitation_id IS NULL`, i.e. it **cannot** touch actionable notifications by design (`data-model-notifications.md:51-52`). No other `FR-JOB-*` entry mentions `friend_request` or `room_invitation` at all. `FR-JOB-007`'s five reconciliation duties are all room/session-state repairs; `FR-JOB-006` is the room deadline sweep (grace/migration windows only); `FR-JOB-012` is the upload-slot sweep.

**Blocks:** the scheduled-job implementation class(es) that would page `friend_request_expiry_idx` and `room_invitation_expiry_idx` and delete rows past `expires_at` — there is currently no requirement ID, no interval, no config key, and no owner document specifying this job. An implementer at low reasoning effort will build exactly the jobs enumerated in `platform-operations.md` and stop, because that document explicitly presents itself as the complete job list.

**Scenario:** A player sends a friend request or a room invitation to someone who neither accepts, declines, nor lets their room close. `expires_at` passes at day 30. Nothing scans `friend_request_expiry_idx` or `room_invitation_expiry_idx`. The row is never deleted. Its notification is `ON DELETE CASCADE` from the subject row (`friend_request_id`/`invitation_id` FK) — but the subject row is never deleted, so the cascade never fires, and `notification_purge_idx`'s partial predicate (subject IS NULL) permanently excludes it from the generic 30-day sweep. The notification sits in the recipient's bell forever, in direct contradiction of the design intent stated at `data-model-notifications.md:191-208` ("**this is exactly the defect this whole section exists to avoid**") — this is a recurrence of the exact "unpurgeable notification" bug last session believed it had fixed by adding `expires_at`, because adding the deadline column is necessary but not sufficient without something that acts on it.

**Suggested resolution:** `platform-operations.md` should own a new `FR-JOB-01x` ("Friend request and room invitation expiry") analogous to `FR-JOB-002`, deleting `friend_request` rows where `expires_at < now()` and `room_invitation` rows where `expires_at < now()` (their notifications cascade automatically per `notification_single_subject_ck`'s FK). Default interval should be stated (daily, matching `FR-JOB-002`, is the obvious choice since both share the same 30-day window). `data-model-social.md:152` and `data-model-notifications.md:199` both already assert this job exists by name — they need a real `FR-JOB-*` citation once it's added.

---

### F2 — GAP — Offset-based pagination is unaddressed for stability under concurrent insert, specifically for the notification center

**Where:** `docs/specs/api-design/pagination-filtering-sorting.md:1-32`, `docs/requirements/notifications-invitations.md:52` (FR-NOTIF-009), `docs/requirements/notifications-invitations.md:50` (FR-NOTIF-007, real-time delivery).

**Quotes:**
> "Applies to all GET endpoints that return collections: game catalog, room list, notification center, game version history, etc." (`pagination-filtering-sorting.md:3`)
> "Offset-based, 1-indexed pages. Spring Data's `Pageable`..." (`pagination-filtering-sorting.md:7`)
> "Notifications are delivered in real-time while the player is online." (`notifications-invitations.md:50`, FR-NOTIF-007)
> "The notification center list is paginated." (`notifications-invitations.md:52`, FR-NOTIF-009)

**Blocks:** the `NotificationController` list endpoint (`GET /api/notifications` paginated per FR-NOTIF-009, sorted `created_at DESC` per `notification_user_recent_idx`) — specifically, whatever `Pageable`/offset query an implementer writes directly from this spec.

**Scenario:** A user opens the notification center on page 1 (items 1–25 by `created_at DESC`). While they're reading, two new notifications arrive in real time (FR-NOTIF-007) — a live, expected occurrence, not an edge case, since this is the one list in the corpus explicitly designed around continuous real-time insertion. The user clicks "next page." With `OFFSET 25 LIMIT 25`, the two new rows at the top have pushed everything down by two positions, so page 2 now starts by re-showing the last two items the user already saw on page 1 (a visible duplicate), and by the same mechanism, if they instead click "previous page" from page 3, an item can be skipped entirely. This is the standard offset-pagination-under-insert defect, and it is not addressed anywhere: `pagination-filtering-sorting.md` prescribes plain `OFFSET`/`LIMIT` with no discussion of stability, and no cursor/keyset alternative is offered for lists (like the notification center) that the corpus itself identifies as continuously growing in real time.

This is distinct from — and not covered by — the already-known-and-deferred `game-history.md` OQ-002, which is about whether pagination is a shared UI component or API pattern, not about correctness under concurrent insert. Game history is far less exposed to this (history entries arrive only at game end, not continuously per session), but the notification center is exactly the case this failure mode targets.

**Suggested resolution:** `pagination-filtering-sorting.md` should either (a) state explicitly that offset pagination's drift under insert is accepted for MVP (a legitimate call, given CON-001 in `per-game-statistics.md`-style docs elsewhere accept similar trade-offs, but it should be a stated decision, not silence), or (b) specify a keyset/cursor scheme for `created_at`-sorted, insert-heavy lists — the notification center in particular — encoding `(created_at, notification_id)` as the cursor to resolve ties and drift together. Either resolution belongs in this document, since it is the one all list endpoints defer to.

---

### F3 — DRIFT — `GameOutcome` validation checklist is stated with different completeness in three documents

**Where:** `docs/specs/internal-grpc/orchestration-gamehost-protocol.md:308-315` vs `docs/specs/platform/data-model-history.md:172-175` vs `docs/specs/flows/06-game-end-and-rematch.md:30-33`.

**Quotes:**
> "Structurally invalid — placement out of range, `teamResults` empty, a `playerResults` entry naming a player not in the session" (`data-model-history.md:174`)
> "Structurally invalid — placement outside `[1, teamCount]`, empty `teamResults`, a `playerResults` entry naming a non-participant" (flow-06:33)
> vs. the internal-grpc spec's five-row table, which also requires: "placement coverage | placements form a valid ranking; ties are permitted **only** when `draw` is true" and "team ids | every `teamResults` team id is a team of this session" (`orchestration-gamehost-protocol.md:312,314`)

**Blocks:** the `GameOutcome` validator (wherever it lands — `orchestration-gamehost-protocol.md:302` says "Orchestration validates it before it reaches Postgres", making this an Orchestration-side validation component, not a DB constraint).

**Scenario:** An implementer who reads only `data-model-history.md` (the document my slice owns, and the one most directly about the recording transaction) or only flow-06 will implement the placement-range/non-empty/participant checks and stop — missing the placement-ranking/tie-with-draw-flag check and the team-id-membership check. A game backend emitting `teamResults` with a team UUID that isn't one of this session's `room_team` rows (a real bug class, e.g. a stale UUID from a previous session) would pass the narrower validation, fail nothing at the DB layer either (no FK — `data-model-history.md:188` "No `team_id`. ... nothing in `game-history.md` reads a team identity"), and silently write a `team_stats` blob attributed to a nonexistent team with no error logged, defeating the entire point of boundary validation.

This is DRIFT rather than a BLOCKER because the fuller, correct checklist does exist and is unambiguous — it's just not the one that lives in this slice's primary document, and nothing in `data-model-history.md` or flow-06 signals "see the grpc doc for the complete list."

**Suggested resolution:** `data-model-history.md:172-175` and flow-06's table should either reproduce the full five-row checklist or explicitly say "see `orchestration-gamehost-protocol.md` §`GameOutcome validation` for the complete check list" rather than restating a partial summary that reads as complete.

---

### F4 — NIT — Broken requirement cross-reference

**Where:** `docs/specs/api-design/sse-notifications.md:18`.

**Quote:**
> "the distinction is not cosmetic — it decides whether a message is stored, replayed, or dropped (`notifications-invitations.md` FR-ALERT-006)."

`notifications-invitations.md` has no `FR-ALERT-006` — the Alerts section only defines `FR-ALERT-001` through `FR-ALERT-005` and `FR-ALERT-010`. `FR-ALERT-010` ("Alerts are a distinct delivery class... must be distinguishable by the client without inspecting the payload... dropped if the recipient is not connected") is almost certainly the intended target — it matches the cited content exactly.

**Blocks:** nothing functionally; the two-event-class table right below the citation is fully specified in the same document. Cosmetic only.

**Suggested resolution:** Change `FR-ALERT-006` to `FR-ALERT-010` in `sse-notifications.md:18`.

---

## What checked out

- **`game_over` → history/statistics recording (scenario 1).** `game-history.md` FR-HIST-005 (stored fields), `game-contracts.md` FR-OUTCOME-001…004 (source fields), `data-model-history.md` §1–§3 (schema + transaction), and flow-06 §C (concrete SQL skeleton) all agree on exactly which columns come from where. `ON CONFLICT (session_id) DO NOTHING` correctly realizes FR-EFF-007 across process restarts, verified consistently in `data-model-history.md:50-57`, flow-06 §C/§F, and `orchestration-gamehost-protocol.md`. A guest-only session correctly writes the completion row and counter but no history rows, and this is called out three times with the same reasoning (avoids under-counting).
- **`ghe_placement_ck` fix (scenario 2) is real and lands in the right place.** Verified that the boundary-validation-before-transaction design is stated consistently in `data-model-history.md:161-186`, flow-06 §B, and — critically — actually implemented as a concrete check table in `orchestration-gamehost-protocol.md:296-324`, which is the document that owns the Orchestration↔Game Host boundary. The CHECK constraint is correctly demoted to "backstop that should never fire." A malformed single-team's outcome no longer aborts the whole session's recording (confirmed: on failure, the completion row and counter still commit; only history entries are skipped). See F3 above for the one gap in this otherwise-solid fix (checklist completeness varies by document).
- **Pseudonymization non-reversibility (scenario 3).** ADR-0004, `data-model-history.md` §4, and `data-model-accounts.md` §5 are unanimous and mutually reinforcing on the random-token construction, explicitly reject `HMAC(user_id, pepper)` for the same enumerability reason in both spec documents, and match ADR-0004's requirement verbatim. `ghe_subject_ck` correctly prevents partial-erasure states. Other participants' entries are untouched — verified `UPDATE ... WHERE user_id = :u` only, and the `(session_id, user_id)` unique index's NULL-distinctness is explicitly reasoned through for the multi-erased-player-per-session case.
- **Notification actionability vs. purge (scenario 4), modulo F1.** The subject-FK mechanism (`notification_single_subject_ck`, partial `notification_purge_idx`) is a clean, well-reasoned design and is internally consistent between `data-model-notifications.md` §1–§2 and `notifications-invitations.md` FR-FREQ-006/FR-INV-009. The *design* is sound; F1 is that its precondition (something must actually delete expired subjects) has no implementation home.
- **FR-INV-008 fix at room closure (scenario 5) — confirmed to land in the producing document, not only the rule-stating one.** `docs/specs/flows/07-room-closure.md:43` contains an explicit `DELETE FROM room_invitation WHERE room_id = :r -- FR-INV-008` step inside the shared closure transaction skeleton used by all five closure producers, and `data-model.md`'s closure-reasons table (§1) independently states the same obligation and names all five producers (`FR-XFER-002`, `FR-HDISC-003`, `FR-JOB-007c`, `FR-JOB-007d`, `FR-LIFE-004`) consistently with `data-model-notifications.md:234-239`'s citation of the same five. The fix is not confined to the notifications spec.
- **SSE reconnect / `Last-Event-ID` (scenario 6).** Delivery is correctly driven by the per-row `delivered_at IS NULL` predicate rather than a client watermark, consistently described in `sse-notifications.md` and `data-model-notifications.md` §1, with the out-of-order-commit race explicitly called out as the reason the old watermark design was replaced. Retention for undelivered notifications is the same 30-day window as everything else (FR-NOTIF-006/FR-RET-001) — no separate, conflicting retention rule exists for the undelivered case.
- **Retention period tabulation** — no disagreement found across the corpus: `FR-RET-001` notifications 30d (`platform-operations.md:173`) = `FR-NOTIF-006` = `NFR-SCALE-001`; `FR-RET-003` game history indefinite (`platform-operations.md:175`) = `data-model-history.md` §5 ("No retention or purge job") = `game-history.md` NFR-HIST-003; `FR-RET-006` closed rooms 7 days = `game-history.md` CON-004 = `data-model.md` §1 = `data-model-history.md` §1. `FR-INV-009`'s room-invitation window is explicitly and deliberately the *same* config property (`turnbase.retention.notification`) as the generic notification purge (`data-model-notifications.md:205-208`) — verified this is a stated design choice, not an accidental coincidence.
- **`ghe_user_name_trgm_idx` / `btree_gin` baseline extension** — confirmed `docs/specs/deployment/schema-migrations.md:141-146` lists both `pg_trgm` and `btree_gin` as baseline `CREATE EXTENSION` statements and names `ghe_user_name_trgm_idx` specifically as the reason `btree_gin` is needed, closing the loop from `data-model-history.md`'s claim that this is "a baseline concern rather than an additive migration."
- **FR-HIST-011…013 / FR-HIST-020/027/028/029 and FR-STATS-010/011/022/024/026/027** are not realized in a separate design spec, but are self-contained, concrete requirement statements (exact label strings, exact visibility predicates cross-referencing `user-accounts.md` FR-PROF-006) that don't require further design elaboration to implement correctly — I did not find these to be GAPs.

Overall readiness for this slice: **solid but not clear**. The core recording/erasure/reclassification design (history, statistics, pseudonymization, alert-vs-notification split) is unusually well cross-checked and several previously-flagged defects are genuinely fixed and fixed in the right place. The one BLOCKER (F1) is exactly the anti-pattern the brief warns about — a rule ("purge whose subject is gone") that depends on a deleter that no document actually specifies — and it's load-bearing for both `FR-FREQ-005` and `FR-INV-009`. I'd fix F1 before writing the `FriendRequest`/`RoomInvitation` expiry code, since without it those tables grow unboundedly and the "unpurgeable notification" bug this exact design was built to prevent recurs.
