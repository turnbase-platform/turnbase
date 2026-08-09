## Last Session Summary

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

## Previous Session Summary

**Date:** 2026-07-12 (session 7)

**Wrote the abuse-control specs** (STATUS priority #6) — `rate-limiting.md` rewritten and
`input-validation.md` written new. **Closes API-1, API-2 and API-6**, plus api-design review gap 8
(client-IP derivation) and GRMP lesson F6 (per-env configurability). These were the review's
"unthrottled spam vectors" — the reason its verdict was *"not yet safe to expose on the public
internet."*

**The architectural call: WebSocket rate limiting is pod-local, not Redis-backed.** The existing doc
opened with "Bucket4j backed by Redis" and the review assumed the same. But **room affinity (ADR-0002)
pins every frame a user sends about a room to that room's pod**, so an in-JVM bucket keyed by principal
observes that user's *entire* frame stream — it is exact, not approximate. Redis would have put a
network round trip on the inbound path of every chat message and every game action to buy nothing.
Rate-limit locality follows the same affinity argument as effect fan-out. HTTP tiers stay Redis-backed:
they are IP-keyed and run *before* authentication, so any pod may serve them.

**Two places the review's suggested fix was weaker than what the specs already allowed:**

1. **`parameters` is a whitelist, not a size cap.** The review proposed capping the `CHANGE_PARAMETERS`
   object at 4 KB. But `manifest-schema.md` **already declares a typed parameter schema**
   (`key`/`type`/`default`/`min`/`max`/`options`), so unknown keys can simply be *rejected*. The
   amplification vector is gone **by construction** rather than merely bounded, and a host can no
   longer push attacker-chosen data through the platform into every room member's client.
2. **NFC does not stop impersonation.** The review proposed NFC-normalizing usernames. NFC does nothing
   about `Аlice` (Cyrillic А) vs `Alice` — they are distinct strings that render identically. Usernames
   now carry an ICU4J **confusable-skeleton uniqueness index** plus a **mixed-script restriction**
   (`MODERATELY_RESTRICTIVE`), which is where homoglyph attacks actually live. The `guest-` reserved
   prefix (FR-AUTH-013) is checked against the *skeleton* too — otherwise a Cyrillic `е` walks past it.

**Design decisions recorded:**
1. **Tier 6 buckets are sized by cost, not uniformly.** The strictest is `snapshot` (1 per 3s):
   `REQUEST_GAME_SYNC` **re-enters the guest VM** (`onResync`) under the session's single-flight lock,
   making it the most expensive frame a client can send — a flood is a self-DoS of the whole session,
   strictly worse than a chat flood. `REQUEST_ROOM_STATE` shares a destination with other member
   commands, so it is charged the cheap `command` bucket at the interceptor and the `snapshot` bucket
   *inside its handler*, where `type` is already deserialized — the same fast-fail/authoritative split
   the authorization model uses.
2. **Penalty ladder: drop → close → Redis reconnect lockout** (30s, doubling, capped 15m). Closing a
   connection mid-game starts the flooder's *own* grace period, so escalation removes persistent
   abusers from live games with no separate mechanism. The numbers compose: a first offence (30s)
   resolves inside a 60s grace period; a repeat offender's lockout outlives it and they are dropped.
   **The error emission is itself throttled** (1/bucket/second) — otherwise the abuse control becomes
   an amplifier, emitting 1 000 unicast errors/s at a client sending 1 000 frames/s.
3. **Tier 5 counts *successes*.** Tier 1 counts only failures, and guest creation *always succeeds* —
   which is precisely why it leaked past it. 5 guests + 3 registrations per IP/hour; the two counters
   coexist on the same endpoints and do not interact. (New requirement: NFR-SEC-007.)
4. **IPv6 IP-tiers key on the /64 prefix.** A routed /64 gives one attacker 2^64 addresses; keying on
   the full address makes every IP-based tier silently worthless.
5. **`enabled=false` is permitted only under the `test`/`e2e` profile** — the app fails to start
   otherwise. GRMP's hardcoded login limit blocked every test session for months (workaround: deleting
   Redis keys by hand), so the escape hatch is mandatory *and* must not be shippable.
6. **The game log is the platform's only non-plain-text render surface**, and its content is composed
   by *game code* — the one place "React escapes by default" does not save us. Markdown renderer runs
   with raw HTML disabled, no links, no autolinking. Accepted residual: a username containing Markdown
   metacharacters can corrupt log *formatting* (cosmetic, never markup).
7. **BCrypt silently truncates at 72 bytes**, so a 128-char Unicode password loses entropy without a
   word. Argon2id (already NFR-SEC-001) is now load-bearing, not merely preferred.

**Files changed:**
- `docs/specs/api-design/rate-limiting.md` — **rewritten**: two enforcement domains, client-IP
  derivation, Tier 5 (minting), Tier 6 (WebSocket), penalty ladder, configuration
- `docs/specs/api-design/input-validation.md` — **new**: pipeline, canonicalization, field catalogue,
  size limits, `CHANGE_PARAMETERS` whitelist, output encoding
- `docs/requirements/user-accounts.md` — FR-AUTH-014/015 (username charset, impersonation safety),
  NFR-SEC-007 (minting throttle); FR-AUTH-003/013 amended to run on the skeleton
- `docs/specs/api-design/websocket.md` — the two "unthrottled / known gap" hedges replaced with the
  real budgets; OQ-001 narrowed to the legitimate mass-reconnect case
- `docs/specs/api-design/room-websocket.md` — 6 new error codes (parameters, validation, rate limit)
- `docs/specs/api-design/room-chat-websocket.md`, `rest-conventions.md` (413), `INDEX.md`
- `docs/requirements/game-rooms.md`, `in-room-chat.md` — spec links
- `docs/reviews/2026-07-02-mvp-readiness/INDEX.md`, `STATUS.md`

---

## Next Priorities

Continue the review's action plan (`docs/reviews/2026-07-02-mvp-readiness/INDEX.md`).

**Blocker status: all 15 of the review's blockers are now closed or decided.** The game-execution
chain (GAME-B1/B2/B3), the API abuse surface (API-1/API-2), and the room-lifecycle contradictions
(CORE-1/2/3) are fully closed; API-3 and OPS-1…6 are *decided* (ADR-0001…0006) with doc edits
outstanding. The room-lifecycle **durability** work (ADR-0008/0009/0010) closed GRMP lessons F1, F2
and F3 — a second pass over the same area, prompted by a self-contradiction found in
`room-websocket.md`, not a reopening of CORE-1/2/3.

**What remains is no longer blocker work: it is the deployment/ops specs (item 9), the existing-doc
edit backlog (item 8), and the previously planned build-out queue (item 10).**

1. **Owner decisions** — ✅ done (ADR-0001…0005, 2026-07-10).
2. **Espresso feasibility spike** (ADR-0005) — ✅ done (2026-07-11) → **ADR-0006** (official-only Java).
3. **Game Host internals spec** — ✅ done (session 4). Closed GAME-I1/I2, GAME-B2, exec-half of B1.
4. **Game-session WebSocket spec** — ✅ done (session 5). Closed **GAME-B1**, **I4**, **I6**.
5. **Game FE serving origin / sandbox / CSP** — ✅ done (session 6). Closed **GAME-B3**, **API-5**.
6. **WS abuse controls + input validation** — ✅ done (2026-07-12, session 7). `rate-limiting.md`
   (rewritten) + `input-validation.md` (new). Closed **API-1**, **API-2**, **API-6**, review gap 8,
   GRMP-F6.
7. **Room-lifecycle contradictions (CORE-1/2/3)** — ✅ done (2026-07-10, commit `a541cb8`, before
   items 2–6 above). Initial team instantiation (new FR-TEAM-012), voluntary leave vs. disconnect (new
   FR-DC-005, FR-EXPIRY-004), and last-connected-human host disconnect (new FR-HDISC-003) are all
   resolved in `game-rooms.md` and `reconnection-flow.md`. This item previously sat here marked "next"
   after the resolution had already shipped — the review's own action-plan checklist below inherited
   the same staleness and has been corrected alongside it.
8. **Room-lifecycle durability (GRMP-F1/F2/F3)** — ✅ done (2026-08-09, session 8). ADR-0008
   (ownership as a lease-gated claim), ADR-0009 (persisted deadlines, sweep-only), ADR-0010
   (teardown as a durable to-do); new `docs/specs/platform/` with `room-lifecycle.md` and the
   corpus's first `data-model.md`; FR-JOB-006…011. Fixed two latent defects: a rolling deploy would
   have deleted every Lobby room, and an adopting pod would have re-issued event versions that
   clients discard silently. A final full-corpus review closed a further 18 defects — including an
   unfenced adoption write, FR-HDISC-004 having no mechanism at all, and a `NOT_FOUND` rule whose
   supporting state the design itself deletes.
9. **Existing-doc edit checklist, remainder:** `platform-operations.md` (~~reconciliation sweep
   GRMP-F1~~ done; **replace the Redis-pub/sub scaling text with room affinity — the API-3 doc
   edit**; Dependabot/Trivy + frontend in FR-CICD-001), `rest-conventions.md` (authz/IDOR ownership model,
   actuator on a separate management port, logout endpoint, idempotency), `user-accounts.md` (password
   change FR, logout FR, OAuth email-collision rule, lockout decay), notifications/SSE event classes,
   `platform-ui-library.md` (Tabs/Select/Switch/Badge; Avatar contradiction), gRPC proto sweep
   (GAME-I3 failed-action drop semantics, `GameOutcome` validation).
   **Also: requirement IDs are numbered per-document, so the same ID string means different things
   in different files.** A corpus audit found `FR-SESS-003` defined twice with unrelated meanings
   (`platform-architecture.md` = Game Host in-memory state; `user-accounts.md` = login displaces
   previous session), cited unqualified in specs — now qualified at those call sites. `NFR-PERF-001`
   is defined 8 times, `NFR-SEC-001` and others similarly. It works today only because most
   citations carry disambiguating context. Worth one pass to require a document qualifier on every
   cross-document ID citation, before the corpus grows another collision.
10. **New specs (rescoped local-first) — the top of the queue now:** local deployment &
   infrastructure (Docker Desktop K8s + compose per ADR-0001), data-operations (Postgres/Redis local,
   accepted game-state loss window — OPS-4; note `data-model.md` now exists and the schema for rooms
   belongs to it, so this spec covers migrations/backups rather than restating tables), secrets &
   config (OPS-5).
11. **Then** the previously planned queue: game bundle format + upload pipeline (must unpack into the
    `/g/{gameId}/{version}/` layout `game-asset-serving.md` §4.1 serves; `gdkApiVersion` check
    GAME-I7), test harness, platform-frontend shell spec (must honor the `websocket.md` relay contract
    and the iframe embedding contract in `game-asset-serving.md` §6).

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

**Specs:** `docs/specs/` — api-design, internal-grpc, game-host, game-frontend, gdk-api, manifest, and
**platform** (new: room lifecycle, ownership, sweeps, relational data model).

**Decisions:** `docs/decisions/` — ADR-0001 (local-first platform), ADR-0002 (WS room affinity),
ADR-0003 (availability), ADR-0004 (erasure pseudonymization), ADR-0005 (sandbox / Espresso spike),
ADR-0006 (game trust model — official-only Java for MVP), ADR-0007 (game FEs on a separate
registrable domain), ADR-0008 (room ownership as a lease-gated claim), ADR-0009 (grace deadlines
persisted and swept), ADR-0010 (session teardown as a durable to-do).

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
