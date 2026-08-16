## Last Session Summary

**Date:** 2026-08-16 (session 11)

**Closed all 23 implementation-readiness blockers.** The 2026-08-16 audit round is **closed** and no
work item in `docs/implementation/registry.md` is gated. Phase 1 coding can begin.

Executed as 26 tasks from
[`docs/reviews/2026-08-16-implementation-readiness/remediation-plan.md`](docs/reviews/2026-08-16-implementation-readiness/remediation-plan.md),
one commit per task, on branch `docs/blocker-remediation`. Documents only — no code exists yet.

### Three new specifications, one scope cut

| Document | Closes | Note |
|---|---|---|
| `docs/specs/api-design/room-rest-api.md` | IR-13 | Five endpoints. REST is membership only; every in-room mutation stays STOMP. Gated all of M2 |
| `docs/specs/deployment/observability.md` | IR-04 | All four signals wired end to end. Adds Promtail and Alertmanager as containers |
| `docs/specs/platform-frontend/design-system.md` | IR-23a | Tokens, CSS Modules, 17 components, accessibility baseline |
| `docs/requirements/onboarding-wizard.md` | IR-23b | **Cut from v1.** Banner + all 16 priorities read `Post-MVP` |

### The four scope decisions — taken by the user, before the plan was written

Recorded because a future reader will otherwise reopen them.

| Question | Decision |
|---|---|
| Onboarding wizard | **Cut from v1.** The only one of the four structural gaps droppable without weakening what the project demonstrates |
| Design system home | **Fold into `turnbase-frontend`** as an internal module with a lint-enforced import boundary. CON-002 amended; the five-repo table stays at five |
| AI players | **Keep the wire, defer the schema.** Declare the v1 behaviour of the existing surface |
| CI coverage gate | **Narrow FR-CICD-003 to unit + integration**, measured at PR time. Keeps a real gate |

### Two resolutions departed from the review's own suggestion

- **IR-11 needs no new table.** The review left "record the closure as owed" unresolved. The
  mechanism already existed — §5.1 duty 2's deferred tail — which broadcasts *and* evaluates closure
  under the claim. A `room_closure_owed` table would be a second durable to-do duplicating one that
  works; ADR-0010's lesson is about keying such tables correctly, not minting more.
- **IR-12 declares the v1 behaviour of the AI wire surface** rather than adding a schema
  representation or cutting FR-HOST-003: `aiPlayers` always empty, `ADD_AI_PLAYER` always
  `AI_NOT_SUPPORTED`, `capabilities.ai: true` rejected at bundle validation, the "not an AI" closure
  clause removed. The protocol shape survives for when OQ-002 resolves.

### One dependency that is invisible from the affected documents

**IR-09's fix has two halves and IR-11 depends on the first.** Making `lost_announced_at` honest —
stamped by every path that sets `left_at`, not only by grace expiry — is what lets IR-11's owed
closure ride the deferred tail. The second half, narrowing duty 2 on `leave_reason`, is a backstop
against a writer that forgets. Doing only the narrowing would have left the column meaning something
other than its name, which is how the defect arose.

### Two new findings, both open, neither blocking

- **IR-24** — NFR-SPEC-001's spectator capacity has no configuration key, though `local-environment.md`
  §7 claims to hold every tunable in the corpus. `room-rest-api.md` deliberately refers to
  `spectatorCapacity` rather than inventing a property name.
- **IR-25** — `docs/requirements/` has no `INDEX.md`, so CLAUDE.md's mandatory "start from the
  INDEX" rule is unsatisfiable across seventeen documents. Surfaced when the onboarding cut called for
  annotating an index entry that does not exist.

Both are in the review INDEX under *Found during remediation*.

### Corpus state

**553 relative links, 0 broken.** A 23-assertion grep gauntlet over every fix passes; it is in the
plan's Task 26 and is worth re-running after any edit to the affected documents.

Ten non-blocking findings from the review survive this round and are recorded in the plan's
self-review. **The two most likely to cost time** are `test-harness.md`'s claim that the Game Host
blocks filesystem and network calls, and the GDK example that violates the determinism rule stated
sixty lines above it — both are read by game developers as instructions.

## Previous Session Summary

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

---

## Next Priorities

**Phase 1 has started. Work from [`docs/implementation/INDEX.md`](docs/implementation/INDEX.md), not
from this file.** The registry holds 60 work items with read-lists, dependencies and done-when
clauses; this section only says which of them to pick up.

**No work item is gated.** All 23 readiness blockers are closed, so an item's status is whatever its
own dependencies imply. The registry's gates block records how each one closed rather than what it
blocks.

### The next session

**Start writing code, at `IMP-M0-01`.**

1. **IMP-M0-01 through IMP-M0-05** — the five repository skeletons. Mechanical, and they unblock
   everything.
2. **IMP-M0-06 — the Flyway baseline.** The highest-value item in the registry. Transcribing
   `V1__baseline.sql` from the six schema documents is the first mechanical test of whether they are
   mutually consistent, and the audit already named two hazards to expect: the `bigserial` versus
   `GENERATED ALWAYS AS IDENTITY` split across three sibling documents, and `schema-migrations.md`'s
   claim that `room_participant.team_id → room_team` is one of "the two circular foreign keys" when by
   its own stated table order it is not. **Any further disagreement found while transcribing is a
   specification defect — fix the document, then the SQL.** Do not reconcile silently in the
   migration.

   Two schema changes from this session must land in the baseline:
   `room_participant_unannounced_idx` (IR-09) and nothing else — IR-11 deliberately added no table.

3. **IMP-M0-07 — the compose stack.** IR-01 and IR-02 are closed, so this is now buildable end to
   end: the `minio-init` container, `deploy/compose/initdb/01-roles.sql`, and `POSTGRES_USER` set to
   `turnbase_owner`. Getting the last one wrong is the silent FR-CRED-005 violation.

### Then, in dependency order

M1 accounts → M2 rooms (the longest milestone, and now fully specified) → M3 execution → M4 catalog →
M5 history → M6 frontend. The registry has the per-item ordering.

Three things worth knowing before the milestone that needs them:

- **M2's specifications are clean but subtle.** The ownership and versioning core was confirmed
  correct by the audit; the blockers clustered in the edges — expiry, closure, chat, sweeps — and all
  of those are now fixed. Read ADR-0008/0009/0010 before touching `room-lifecycle.md`'s mechanisms,
  and remember that **the epoch is the fence token, not the version**.
- **M3's trust boundary now requires an address check** (IR-17) that did not exist when the registry
  was written: every effect address is validated against the producing session's membership at
  fan-out.
- **M6 inherits three fresh documents** — the design system, the CSP section, and the info-document
  renderer. None existed when the M6 items were drafted.

### Spec hygiene

- **The ID-qualification retrofit** remains outstanding. `docs/specs/INDEX.md` states the rule and it
  holds for new text; the corpus predates it. The highest-traffic collision is `FR-SESS-001…004`,
  defined in both `user-accounts.md` (account sessions) and `platform-architecture.md` (Game Host
  in-memory state); all seven citations resolve correctly by context, so this is a hazard rather than
  a defect. A **wrong** qualifier is worse than a bare ID.
- **Done this session:** the `FR-JOB-007a…e` sub-duty convention is declared in `docs/specs/INDEX.md`,
  and `data-model-accounts.md:392`'s wrong FR-INV-002 citation is corrected.
- **New and open:** `docs/requirements/` has no `INDEX.md` (IR-25), and NFR-SPEC-001's spectator
  capacity has no configuration key (IR-24).
- The 62 non-blocking findings are in the per-slice files under
  `docs/reviews/2026-08-16-implementation-readiness/`, with the ten most likely to cost an implementer
  time called out in that directory's INDEX.

### Review action plan

`docs/reviews/2026-07-02-mvp-readiness/INDEX.md` — fully worked, **closed**.

`docs/reviews/2026-08-16-implementation-readiness/INDEX.md` — **closed.** 23 of 23 blockers resolved;
each entry carries a `**Closed:**` line. Two follow-on findings (IR-24, IR-25) are open and
non-blocking.

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

**Implementation:** `docs/implementation/` — the registry Phase 1 executes from. 60 work items across
7 milestones, each with a read-list, dependencies, requirements satisfied, a done-when clause, and the
readiness gates that block it.

**Reviews:** `docs/reviews/` — `2026-07-02-mvp-readiness` (closed) and
`2026-08-16-implementation-readiness` (**open**: 23 blockers, 62 lesser findings, eight per-slice
files plus five machine-extracted inventories covering the API surface, the schema, the configuration
surface, ten state machines, and requirement→spec coverage).

**Coverage caveat.** Four areas have requirements but **no implementing specification**: the design
system (`platform-ui-library.md`), the onboarding wizard (`onboarding-wizard.md`), the room REST API,
and observability (`FR-MET-*`, `FR-TRACE-*`). The table above lists requirement coverage, not design
coverage, and for these four the difference is the whole design.

---

## Open Questions Remaining in Existing Docs

| Document | Open Question |
|----------|---------------|
| `reconnection-flow.md` | Game engine response set after "player lost" event — deferred to Game SDK contracts |
| `game-history.md` | OQ-002: Pagination reuse — shared UI component vs. API pattern deferred to implementation |
| `game-contracts.md` | OQ-001: Log color annotation syntax — deferred to GDK spec |
| `game-contracts.md` | OQ-002: AI/bot player interface — deferred to future spec. **Mislabelled: this now blocks M2 (IR-12).** `ROOM_STATE` carries AI participants on the wire and the room-closure predicate turns on "not an AI", but `room_participant` has no discriminator — so the closure predicate cannot be written. Either add the column or remove AI from the protocol for the MVP |
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
