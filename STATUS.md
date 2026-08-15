## Last Session Summary

**Date:** 2026-08-15 (session 9)

**Finished Phase 0.** The corpus is now implementation-ready: every table is defined, the services
are wired and startable, config and secrets have a home, the schema has an evolution story, and eight
end-to-end journeys trace the whole system across components. **21 new files, ~35 edited.**

### What was written

| Stage | Output |
|---|---|
| 1 — the rest of the data model | Five sibling schema docs under `docs/specs/platform/`: accounts, social, catalog, history & statistics, notifications. ~30 tables |
| 2 — schema migrations (**closes OPS-3**) | **ADR-0011** (Flyway, forward-only, backward-compatible) + `deployment/schema-migrations.md` + FR-DB-001…004, CON-012 |
| 3 — system wiring | `deployment/local-environment.md`: nine containers, ports, startup and readiness budget, K8s-vs-compose, seeds, testing, and **the consolidated configuration surface** — every tunable in the corpus in one table |
| 4 — secrets (**closes OPS-5**) | `deployment/secrets-and-configuration.md` + FR-CRED-001…005. JWT key set with graceful rotation |
| 5 — end-to-end flows | `docs/specs/flows/` — INDEX + eight journeys |
| 6 — remaining specs | `manifest/bundle-format.md` (subagent), `gdk-api/test-harness.md`, `platform-frontend/shell-architecture.md` |
| 7 — edit backlog | platform-operations, user-accounts, rest-conventions, sse-notifications, websocket, the gRPC sweep, platform-ui-library, and the ID-qualification rule |

**Stage 1 decided five files rather than one.** Each domain runs 250–400 lines in the established
voice, and the INDEX is the navigation layer the corpus already uses. `data-model.md` keeps the
shared conventions the five inherit.

### The defects — 27, found in three distinct ways

**A gate review of Stage 1 returned 4 blockers, 14 defects, 8 nits and 6 coverage gaps.** All were
accepted; the three claims I had made about defects in the *requirements* were independently
confirmed real rather than manufactured, but **two of my resolutions did not execute**:

1. **`DISCARDED` was unreachable for the version my own FR-ACCT-007 amendment had to discard.** The
   status required `SUPERSEDED`, which requires a newer version — which never arrives for a
   single-version game whose owner is gone. The amendment purged nothing in the common case.
   "Retired" is now two disjoint conditions.
2. **The erasure scatter stranded three live objects** — an open `game_review` sitting in the admin
   queue forever addressed to a developer who cannot be notified, `room_invitation` on both legs, and
   `room`/`room_participant` entirely, despite `data-model.md` already defining
   `closed_reason = 'ACCOUNT_DELETED'` with no writer. **Nothing happens by cascade on that path**,
   because a registered deletion is soft — which is exactly what made the omissions look handled.

Also from that review: a `room_invitation` with no expiry made its notification **permanently
unpurgeable** (three retention requirements silently narrowed); `ghe_placement_ck` would abort the
whole recording transaction on a malformed outcome with no possible retry; the two columns whose
entire purpose is `ON DELETE CASCADE` had no index; and my partial-index rationale contradicted what
the sibling document said correctly about NULL distinctness.

**The reviewer also caught that all five files ended in literal `</content></invoke>` tool
scaffolding.** It was eight files, not five.

**The bundle-format subagent found an MVP-blocking defect by composing two correct documents.**
`file-uploads.md` clears Verified status unconditionally at activation; `game_official_ownerless_ck`
ties `badge='OFFICIAL'` to `owner_user_id IS NULL` as an equivalence. Under ADR-0006 every MVP game is
Official — so **every official upload aborts its activation transaction, and no official game can
ever be updated.** The only path the MVP exercises. Narrowed to `VERIFIED → UNVERIFIED` only.

It also found that unpacking the whole archive under `/g/{gameId}/{version}/` **publishes the backend
JAR to anonymous callers** — `gameId` is in the hostname and the version is a public catalog column,
so the URL is derivable from a catalog page. `game-asset-serving.md` §4.2 argued the exposure was
acceptable because "a bundle is JavaScript, CSS and sprites", which stops being true the moment you
unpack all of it. Publication now filters.

Plus: `PROCESSING` had no exit at all, and because `(game_id, version)` is unique, a validation job
that died with its pod **permanently burned that version number**; the bundle-validation `422` in
`error-handling.md` mixed a synchronous check with an async one in a response no endpoint can
produce; `FR-UPLOAD-006` was checked only at slot creation, so two open slots could walk the active
version **backwards**; and the seed path bypassed the pipeline it depends on, producing exactly the
"lists and cannot start" outcome the same paragraph said it was avoiding.

**Writing the flows found the rest.** `FR-INV-008` requires invitations deleted at room *closure*,
and the only mechanism was a foreign-key cascade that fires seven days later at purge — a correct
rule, stated once, in a document none of its five producers is written from. Same shape as last
session's worst finding. And `FR-FAIL-001` terminated the session on the *first* game failure while
`FR-FAIL-003` allows three, with nothing anywhere saying what happens to the failed input or telling
the acting player: the game appears to hang, they retry, and three clicks kill the session for
everyone with no client ever told why.

### Decisions worth carrying

1. **Erasure uses a random token, not an HMAC.** ADR-0004 requires non-reversibility; `HMAC(user_id,
   pepper)` is reversible by enumeration over a small id space given the key. Only a construction
   that discards its input qualifies.
2. **Guest exclusion is a foreign key.** `friendship` references `app_user (user_id, kind)` with a
   local `CHECK kind = 'REGISTERED'`, so FR-SOC-020 cannot be violated from any code path.
3. **Guest purge is two-phase**, because a literal 24-hour delete fails permanently on
   `room_participant`'s FK and the cascade that would "fix" it would silently remove a seated player
   from a live game. FR-RET-002 amended to state the real bound (~8 days).
4. **Project only what needs an index shape the source cannot provide.** Tags get a table; the
   capability columns do not. The one exception — `title`/`short_description` — is named, because
   FR-GAME-008 makes them owner-editable and therefore not projections of anything.
5. **A notification's subject foreign key marks actionability**, and the retention purge is indexed
   *partially on having no subject* — so it can never remove an actionable message out from under a
   live object.
6. **The deploy is a rolling update even at one replica.** Under `Recreate`, ADR-0008's claim path
   never runs against a live incumbent, and `platform-operations.md`'s claim that it is "continuously
   tested rather than dormant" would be false.
7. **The monolith's readiness must not depend on the Game Host** — coupling them lets a Game Host
   restart drop every WebSocket on the platform, including rooms not running a game at all.
8. **Static serializability at upload, the executing round trip in the harness.** NFR-UPLOAD-002
   forbids running game code at upload; an executor gated on "ADR-0006 says trusted" is GRMP-F5's
   fail-open with a different variable name. New FR-HARNESS-010 makes the harness half a requirement
   rather than an assumption.

### Process

Both lessons from last session held. The Stage-1 reviewer returned a **bare idle notification**; a
re-task with an explicit file list, explicit scenarios and an explicit "an idle notification is not a
usable answer" recovered it and produced the session's best findings. Both subagents were given owned
file lists and both complied — verified with `git status`, not assumed.

**New lesson: a constraint that turns a silent corruption into a loud failure is doing its job, and
will look like the bug.** Tightening `game_official_ownerless_ck` from an implication to an
equivalence is what surfaced the MVP-blocking badge defect. The right response was to fix the
transition, not to loosen the check.

**Verification:** every relative link in `docs/` resolves (0 broken); no dangling FR/NFR citations
across all specs, decisions and requirements; no duplicate IDs within any document; every file
registered in its nearest INDEX. Four ID collisions I introduced during the session (`FR-SEC-001…005`,
`FR-ALERT-006`, `FR-HARNESS-006`, `FR-SESS-005`) were caught by the collision audit and renumbered.

---

## Previous Session Summary

**Date:** 2026-08-09 (session 8)

**Closed the room-lifecycle durability cluster — GRMP lessons F1, F2 and F3** — with three ADRs, a
new `docs/specs/platform/` subdirectory, and edits across ten existing documents.

**First, a correction to this file.** The previous "Next Priorities" listed CORE-1/2/3 as "the last
undecided blockers." They had in fact been resolved on 2026-07-10 (commit `a541cb8`): FR-TEAM-012,
FR-DC-005/FR-EXPIRY-004, and FR-HDISC-003. What actually remained of that cluster was its
*durability* half — where a grace deadline lives, what happens when the owning pod dies, and who
tears the game session down. That is what this session did. The review INDEX had the same stale
entries and is now struck through.

**Four questions were resolved by a team of parallel expert subagents, then each answer gate-reviewed
before dependent work proceeded.** Two of the four corrected the framing they were given:

1. **Ownership is a lease-gated claim, not a lifetime assignment (ADR-0008).** `room-websocket.md`
   was self-contradictory: ownership "persists for the lifetime of the room" (line 20) versus a crash
   "assigns a new owning pod" (line 37), where the join flow assigns nothing on rejoin. **As written,
   post-crash rejoins routed to a corpse forever.** The claim script is now also the failure
   detector — no dead-pod watcher exists anywhere. Rejected eager reassignment: adopting a room with
   no clients attached computes nothing in a turn-based game.
2. **Grace deadlines are persisted absolute timestamps, swept, with no in-process timer (ADR-0009).**
   Sweep-as-primary rather than sweep-as-backstop: two mechanisms enforcing one deadline is a dual
   write and a three-way race to arbitrate on every reconnect. The Postgres clock became the single
   time authority, which removes clock skew **by construction** rather than by tolerance.
3. **Teardown is a durable to-do, not an ordering (ADR-0010).** GRMP's own fix (terminate before
   persist) solves a problem TurnBase does not have — its leak came from `DELETE`ing the reference.
   The reviewer also corrected the proposed design: the to-do must be keyed by `sessionId`, **not** a
   flag on the room, because a rematch would overwrite the previous session's owed teardown and
   reintroduce the exact bug class. Keying by session is what pulled **normal game end** into the
   fix — the most frequent detach path, tearing down with no crash-safety at all.
4. **Reconciliation is three jobs, and one duty was deleted rather than specified.** Orphaned
   participant rows get `ON DELETE CASCADE`; a job there is permanent penance for a missing
   constraint. An In-Progress room with no session **fails back to Lobby, not closed** — recoverable,
   reuses FR-FAIL-005, and the idle sweep collects it later if truly abandoned.

**Two live defects were found and fixed, both independent of the new design:**

- **A rolling deploy would have deleted every Lobby room.** FR-DC-002 makes a Lobby disconnect an
  immediate leave; FR-XFER-002 closes a room when the host has left with no humans left. Chain them
  at pod drain and every Lobby room deletes itself. Fixed by FR-DC-007's carve-out.
- **An adopting pod would have silently corrupted every client's view.** The version counter was an
  in-JVM `AtomicLong` published with no stated ordering against the DB commit, while clients
  **discard** `delta.version <= localVersion`. A pod adopting a room whose DB version lagged would
  re-issue seen versions and every client would drop them — permanent and undetected, strictly worse
  than a gap. Fixed by V1 (commit before publish); V2 (assign, never `max()`) is defence in depth,
  not a second defect — the snapshot flow already said "assign".

**One blocker was caught by gate review, in my own first draft of ADR-0008:** I claimed the room
version could serve as the ownership fence token. It cannot. The version is *room*-scoped and both
producers advance it densely from the same sequence, so a stale owner holding a fixed expected value
is eventually **reached** by the legitimate owner — at which point the stale CAS matches and commits
on top of it. Fixed by introducing an **owner epoch**, burned by the claim script at each change of
tenure. The same review found that self-eviction was triggering on the wrong event (renewal failure
rather than lease *lapse*, which a stop-the-world pause longer than the TTL slips past entirely) and
that invariant I1 was circular in its sweep leg — an unowned room is not necessarily a clientless
one, since a Redis flush unowns a room whose sockets are all still alive.

**Also fixed, found while writing:** `TerminateSession` idempotency existed only in the
implementation spec, not the contract, though the whole re-drive depends on it; `NOT_FOUND` was
unscoped, so a retried teardown read as a hard failure; there was no termination reason for
`game_over`; `TERMINATION_REASON_HOST_ENDED` had no producing requirement anywhere (reserved); six
Redis session keys had no TTL.

### Final review round — 18 further defects, three of them correctness holes

A full-corpus review followed the gate reviews: my own pass, a scenario-walk (`cohesion-final`, three
end-to-end failure traces across all three ADRs), and a citation-semantics audit (`xref-final`, ~90
cross-document references checked against the cited text rather than for mere existence).

**The most important finding was a bug in a fix from earlier the same session.** I had made `NOT_FOUND`
on the game-input drain "terminal only if no teardown was ever recorded" — but `terminateAndCleanup`
**deletes** the `session_teardown` row on success, so the history that rule reads is erased by the very
event it is trying to detect. It produced the exact failure it was written to prevent: a re-driven
teardown succeeds, deletes its row, and a surviving outbox row then reads as "session lost" and fails a
**healthy live rematch** back to Lobby. Replaced with a test of the durable fact —
`room.active_session_id = :sessionId` — which needs no schema addition and stays correct after purge.

**Two more correctness holes:**

- **The adoption write was itself unfenced.** The claim script is atomic, so no two tenures share an
  epoch — but nothing orders their *Postgres* writes. A claimant that stalled after claiming could
  stamp a lower `owner_epoch` over a later tenure's, making every one of the legitimate owner's fenced
  mutations match zero rows: it self-evicts and drops all its clients, while the stale adoption puts
  its *connected* players into grace windows. Fixed with `WHERE owner_epoch < :myEpoch`.
- **FR-HDISC-004 had no mechanism on its only path.** Adoption "started" a migration window that
  nothing ever ended: `§3.1`'s host-transfer line sits on the individual-disconnect path, which
  adoption never routes through. A host who did not return left the room **permanently headless**.
  Fixed with a persisted `migration_window_expires_at` and a sweep duty that closes it.

**Also fixed:** the outbox drain was ownership-partitioned though it is a gRPC call needing no
ownership, so an unowned room's `player_left` went undelivered and the game sat "on a turn that never
comes" — ADR-0009's own words for the failure the outbox exists to remove; NFR-JOB-002 required
re-ownership in <30s from a sweep running every 60s (retargeted to <90s, with the adopt duty exempted
from both FR-JOB-008 guards, which would otherwise have blocked adoption for 120s after every
restart); grace expiry in a **Lobby** room would have re-deleted the rooms FR-DC-007 exists to save;
`ownerless_since` had no writer anywhere; `room-websocket.md` contradicted `room-lifecycle.md` on both
where `ROOM_UNAVAILABLE_RETRY` may appear and the internal retry duration; `dispatched_at` was
undefined as attempt-vs-ACK while the teardown discard is scoped on it; and `§4`'s "benign window"
still carried a justification ADR-0010 had already disproven. New: `EARLY_RELEASE` leave reason,
`room_active_session_idx`, and a host-role rule added to FR-HDISC-003 for the state the schema was
designed for but no requirement covered.

**A note on process.** Two lessons, both worth carrying forward:

1. **Subagents dispatched as read-only reviewers edited files anyway.** Competent and on-brief, but
   uncoordinated: it collided with edits in flight and introduced three inconsistencies (the
   `ROOM_CLOSED` reason set, how `RECONNECT_REQUIRED` is delivered, pod-vs-instance naming), all
   reconciled. Grant edit rights explicitly with an owned file list, or verify read-only compliance
   rather than assuming it.
2. **A fix can read correctly and still depend on a fact the design deletes.** Both the `NOT_FOUND`
   rule and the migration window were self-consistent prose whose supporting state had no writer, or
   an eraser. When a rule tests history, ask what deletes that history. Reviewing the *diff* would not
   have caught either; walking the scenario end-to-end did.
3. Reviewers repeatedly returned bare idle notifications instead of findings. Re-tasking with a
   **self-contained brief** — explicit files, explicit scenarios, explicit "an idle notification is
   not a usable answer" — recovered both, and produced the session's best findings.

**Files:** new — `docs/decisions/0008/0009/0010`, `docs/specs/platform/{INDEX,room-lifecycle,data-model}.md`.
Edited — `game-rooms.md`, `reconnection-flow.md`, `platform-operations.md`, `platform-architecture.md`,
`game-history.md`, `room-websocket.md`, `websocket.md`, `game-host-internals.md`,
`orchestration-gamehost-protocol.md`, `gamehost.proto`, both INDEXes, review INDEX + `grmp-lessons.md`.

**Verification:** every relative markdown link in `docs/` resolves; no dangling FR/NFR/CON citations;
no duplicate IDs within any document.

---

## Next Priorities

**Phase 0 is complete.** All 15 review blockers are closed, OPS-3 and OPS-5 are closed, the existing-doc
edit backlog is worked, and the corpus answers every question the session-9 goal set: what every table
looks like, how the services are wired and started, how config and secrets reach them, how the schema
evolves, and how each primary journey flows end to end.

**The next session should start implementing**, not specifying. Suggested order, which follows the
dependency graph rather than the document order:

1. **Bootstrap the repositories and the local stack.** `turnbase-platform` skeleton, the compose file
   and Helm chart of `deployment/local-environment.md`, and the Flyway baseline transcribed from the
   six schema documents. Finishing here means `docker compose up` gives a running, migrated, seeded
   database — and the baseline is the first real test of whether the schema is self-consistent.
2. **Accounts and sessions**, end to end: registration, login, guest minting, the session table and
   the JWT key set. It is the shortest vertical slice that exercises REST, Postgres, Redis and the
   rate limiter, and everything else needs a principal.
3. **Rooms and the WebSocket**, up to `START_GAME`. The room-lifecycle machinery — claim, epoch fence,
   version ordering, the sweeps — is the most thoroughly specified and the most subtle; building it
   before the catalog means the hard part is behind the easy part.
4. **The Game Host and one official game.** ADR-0006 makes the MVP official-only, so the first game is
   also the proof the GDK contract works.
5. **Catalog, history, notifications, social** — the CRUD tail, in whatever order is convenient.

### Spec work that remains, and none of it blocks implementation

- **`FR-SESS-005` is defined twice** (`platform-architecture.md` = Game Host state discard;
  `user-accounts.md` did not define it, which is why the new session-invalidation requirement took
  FR-SESS-010). The corpus-wide qualification rule is now stated in `docs/specs/INDEX.md`, but it is a
  rule for new text, not a completed retrofit: **50 identifiers are still defined in more than one
  requirements document** (`NFR-PERF-001` nine times, `CON-001` in seventeen). A mechanical pass to
  qualify existing bare citations is worth one session and has no deadline.
- **Open questions raised this session**, all deferred rather than dropped:
  - `data-model-catalog.md` OQ-001 — a rejected re-review leaves a community game stuck with an
    `ACTIVE` version an operator refused and no rollback in the status machine. Dormant under ADR-0006;
    must be resolved before community uploads open.
  - `data-model-catalog.md` OQ-003 — FR-REV-001's pending-review state has no owner-facing
    representation, so a second submission fails as a raw unique violation.
  - `local-environment.md` OQ-001 — the startup budget is a target, not a measurement, and
    `FR-JOB-008`'s 120-second window depends on it.
  - `local-environment.md` OQ-002 — **no backup or restore story for the local Postgres volume.** For
    a seedable local MVP this is arguably right, but it is undecided rather than decided, and the first
    genuinely valuable data the platform holds is game history, which FR-RET-003 retains indefinitely
    and nothing protects.
  - `bundle-format.md` OQ-1…5 — notably the deny-list-versus-`frontend.root` question (which ties to
    `game-asset-serving.md` OQ-003) and the unmeasured NFR-UPLOAD-001 30-second validation budget.
- **`admin-tooling.md` OQ-001/OQ-002** (resubmission after rejection; delisting a Verified game
  post-approval) are now load-bearing for `data-model-catalog.md` OQ-001 rather than merely deferred.

### Review action plan

`docs/reviews/2026-07-02-mvp-readiness/INDEX.md` is fully worked. Every blocker, every strategic
decision, and every item on the existing-doc checklist is closed or explicitly deferred with a named
open question.

---

## Coverage Summary

| Document | Coverage |
|----------|----------|
| `user-accounts.md` | Registration, auth, sessions, account management, profiles, guests, per-section privacy settings, block-requests toggle |
| `game-rooms.md` | Room list, creation, joining, host management, teams, readiness, lifecycle, mid-game join assignment |
| `game-catalog.md` | Catalog listing, game detail, game management, profile games tab |
| `notifications-invitations.md` | Alerts, notification center, invitations, friend request notifications |
| `reconnection-flow.md` | Disconnect detection, grace period, re-entry, kick mechanics |
| `in-room-chat.md` | Room/team channels, messaging, delivery model, late-join team chat access |
| `per-game-statistics.md` | Session counting, game detail stats, profile stats |
| `platform-views.md` | All views, navigation, redirects, auth tier gating |
| `game-development-experience.md` | GDK, game packaging, upload pipeline, local dev workflow |
| `game-contracts.md` | Platform ↔ game BE/FE protocol, effect types, structured outcome, postMessage API |
| `platform-architecture.md` | Game execution infrastructure, Game Host, Orchestration Service, sandboxing, scaling |
| `game-history.md` | Per-session history recording, win condition labels, profile history tab, privacy, deletion pseudonymization |
| `social-friends.md` | Friendship model, request lifecycle, friend cap, discovery, visibility, guest exclusion, block-requests toggle |
| `platform-operations.md` | Service topology (monolith), availability, observability stack, CI/CD pipeline, data retention |
| `onboarding-wizard.md` | First-time wizard overlay, pane structure, localStorage suppression, landing page re-entry |
| `admin-tooling.md` | Internal admin API, game badge model (Official/Verified/Unverified), review queue, private game behaviour |

**Specs:** `docs/specs/` — **flows** (new: eight end-to-end journeys — start here), **deployment**
(new: local environment and the configuration surface, schema migrations, secrets and key rotation),
**platform-frontend** (new: the React shell and the iframe trust boundary), platform (room lifecycle
plus the **complete relational data model** across six documents), api-design, internal-grpc,
game-host, game-frontend, gdk-api (now including the **test harness**), manifest (now including the
**bundle format and upload pipeline**).

**Decisions:** `docs/decisions/` — ADR-0001 (local-first platform), ADR-0002 (WS room affinity),
ADR-0003 (availability), ADR-0004 (erasure pseudonymization), ADR-0005 (sandbox / Espresso spike),
ADR-0006 (game trust model — official-only Java for MVP), ADR-0007 (game FEs on a separate
registrable domain), ADR-0008 (room ownership as a lease-gated claim), ADR-0009 (grace deadlines
persisted and swept), ADR-0010 (session teardown as a durable to-do), ADR-0011 (schema migrations —
Flyway, forward-only, backward-compatible).

---

## Open Questions Remaining in Existing Docs

| Document | Open Question |
|----------|---------------|
| `reconnection-flow.md` | Game engine response set after "player lost" event — deferred to Game SDK contracts |
| `game-history.md` | OQ-002: Pagination reuse — shared UI component vs. API pattern deferred to implementation |
| `game-contracts.md` | OQ-001: Log color annotation syntax — deferred to GDK spec |
| `game-contracts.md` | OQ-002: AI/bot player interface — deferred to future spec |
| `game-contracts.md` | OQ-003: Platform-managed timer system — deferred to future spec |
| `websocket.md` | OQ-001: Resync cost under a *legitimate* mass reconnect (N resyncs serialize behind one session lock) — cache the per-viewer view against `lastAppliedSequence` if it becomes a hotspot. The adversarial case is now closed by the Tier 6 `snapshot` bucket |
| `websocket.md` | OQ-002: A game whose `onResync` returns an empty spectator view leaves spectators blank until the next `broadcast` — the test harness should warn |
| `admin-tooling.md` | OQ-001: Can a developer resubmit a rejected game, or is rejection terminal? |
| `admin-tooling.md` | OQ-002: Can an operator delist a Verified or Official game post-approval? |
| `game-asset-serving.md` | OQ-001: Fullscreen — `allow=""` grants no Permissions-Policy features; whether to add `allow="fullscreen"` is a shell-spec UX call |
| `game-asset-serving.md` | OQ-002: Private-bundle exposure — bundle assets are unauthenticated; a signed-token variant is additive if genuinely private third-party bundles become a requirement post-MVP |
| `game-asset-serving.md` | OQ-003: Manifest-declared stylesheets — CSS must currently be imported from JS; deferred to the bundle spec |
| `rate-limiting.md` | OQ-001: Shared-IP (CGNAT/campus NAT) guest throttling — accepted for a local-first MVP; escalation path is raise limit → add entropy to the key → proof-of-work |
| `rate-limiting.md` | OQ-002: Tier 6 budgets are per-pod, so a user connected to two pods gets 2× — accepted (these are abuse controls, not fairness quotas); revisit only if concurrent multi-room membership lands |
| `input-validation.md` | OQ-001: No emoji or symbols in usernames — the clean fix, if users push back, is a separate free-form display name alongside a strict username (post-MVP model change) |
| `input-validation.md` | OQ-002: ASCII-only email rejects IDN/EAI addresses — revisit if a real user is blocked; there is no mail system in the MVP to normalize against (no verification email is sent) |
| `room-lifecycle.md` | OQ-001: Lease/window numbers (10s TTL, 3s renew, 6s self-evict, 20s migration window, 5s/60s sweeps) are reasoned defaults with no measurement behind them; the relationships that must hold matter more than the values |
| `room-lifecycle.md` | OQ-002: Self-eviction uses a local monotonic clock while the lease expires in Redis — the 4s guard band covers single-node skew, but this is the one place a local clock still affects a correctness bound; re-examine before multi-node |
| `room-lifecycle.md` | OQ-003: Flapping clients — each disconnect starts a fresh window, so a connect/disconnect loop can hold a slot indefinitely; the Tier 6 reconnect lockout dampens it, but whether a hard cap per session is needed is deferred until observed |
| `data-model-catalog.md` | OQ-001: A rejected re-review leaves a community game with an `ACTIVE` version an operator refused, its previously approved version `SUPERSEDED` and unreactivatable, and no rollback in the status machine. §5.1 preserves the artifact; nothing says how to recover the state. Dormant under ADR-0006 |
| `data-model-catalog.md` | OQ-002: `game_review.decided_by` identifies a shared static credential, not a person (`admin-tooling.md` CON-002) — adequate for one operator, not as an audit trail beyond that |
| `data-model-catalog.md` | OQ-003: FR-REV-001's pending-review state has no owner-facing representation, so a second submission fails as a raw unique violation rather than a domain error |
| `local-environment.md` | OQ-001: The startup budget (≤30s to readiness, ≤60s to Game Host registration) is a target, not a measurement, and FR-JOB-008's 120-second suppression window depends on it |
| `local-environment.md` | OQ-002: **No backup, restore or disaster-recovery story for the local Postgres volume.** Undecided rather than decided; the first genuinely valuable data the platform holds is game history, retained indefinitely by FR-RET-003 and protected by nothing |
| `bundle-format.md` | OQ-1…5: publication deny list vs. a manifest `frontend.root` allow list (ties to `game-asset-serving.md` OQ-003); no integrity digest on published objects; the harness cannot check `gdkApiVersion` offline; NFR-UPLOAD-001's 30s validation budget is unmeasured; a version orphaned by a GDK-range move has no user-facing representation |
