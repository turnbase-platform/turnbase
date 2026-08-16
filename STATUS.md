## Last Session Summary

**Date:** 2026-08-16 (session 10)

**Audited the whole corpus for implementation-readiness and built the registry Phase 1 executes
from.** No new specification was written. The session asked one question — *can an implementation
agent running at low reasoning effort build this without re-deriving architecture?* — and answered it
with evidence.

**Verdict: substantially ready, but not at the bar Phase 1 requires. 23 blockers.** Nineteen are
drift or omission in sound designs and are cheap. Four are the absence of design work altogether.

### How it was run

Thirteen agents, three model tiers, one shared brief (severity ladder, evidence standard, output
format) plus per-slice scenario lists.

| Tier | N | Work |
|---|---|---|
| Haiku | 4 | Mechanical inventories — API surface, schema, config/ops, state machines |
| Sonnet | 6 | Domain audits — accounts, catalog, history, frontend, API conventions, deployment |
| Opus | 2 | Rooms/realtime concurrency, and the game-execution trust boundary |

Four checks were **scripted rather than delegated**, because they are deterministic and an agent adds
only hallucination risk: link integrity, ID-collision mapping, requirement→spec coverage, and
misqualified citations. That was the right call twice over — the coverage script independently
corroborated the room-REST-API blocker, and the citation script found a defect class no agent was
looking for.

### The 23 blockers

Full register with quotes, failure scenarios and fix owners:
`docs/reviews/2026-08-16-implementation-readiness/INDEX.md`. Distribution: **M2 rooms 8, M3 execution
4, M6 frontend 4, M0 bootstrap 4, M4 catalog 2, M1 1** (IR-05), **M5 1** (IR-20).

The ones that matter most:

1. **A Lobby grace expiry aborts permanently on a `NOT NULL` violation** (IR-06). §3.3's in-transaction
   side effects insert a `player_left` outbox row *unconditionally*; `game_input_outbox.session_id` is
   `NOT NULL`; a Lobby room's `active_session_id` is null — which the same section says out loud four
   paragraphs later. Step 4 carries a carefully reasoned Lobby exemption. **Step 2 does not.** The
   reservation never resolves and the sweep retries it every 5 seconds forever.
2. **No REST specification exists for the room API** (IR-13). `POST /api/rooms` appears in a flow
   narrative and a pagination example. Nowhere are the room endpoints' paths, bodies or status codes
   defined. It is the entry point to every join, create and rejoin scenario, and it gates all of M2.
3. **NFR-SEC-002 fails open on the trust model** (IR-17). `websocket.md` argues the property is
   "mechanically true rather than aspirational" because a client cannot subscribe to another's
   `/user/queue`. That secures the *subscription*. Nothing validates the *address* — that a
   game-chosen `SendToPlayerEffect.player_id` belongs to the session that produced it. Not exploitable
   under ADR-0006, which is precisely the GRMP-F5 shape.
4. **No job purges expired friend requests or room invitations** (IR-20). Two schema documents assert
   "the purge job" exists and the notification partial-index design depends on it. FR-JOB-001…012
   contains no such job. **This is a regression of the bug session 9 believed it had fixed** — adding
   `expires_at` made expiry expressible; nothing acts on it.
5. **The game iframe `sandbox` attribute is contradicted between its two owning documents** (IR-21),
   with opposite security rationales and no cross-reference. If `shell-architecture.md`'s version
   ships, `event.origin` becomes `"null"` and the shell's own origin check silently drops every
   message the game sends.
6. **AI players are load-bearing on the wire and in the closure predicate, and absent from the
   schema** (IR-12). `game-contracts.md` OQ-002 defers the AI interface — legitimately — but two
   shipped mechanisms already depend on the representation it postponed. **The one mislabelled
   deferral found anywhere in the corpus.**

### Four structural gaps — design work, not edits

Not fixable by editing: **the design system** (`platform-ui-library.md`, ~30 requirements, 24 cited by
no spec), **the onboarding wizard** (all 16 requirements, the entire document referenced by nothing
else in the corpus), **the room REST API**, and **observability** (all ten `FR-MET-*`/`FR-TRACE-*`
uncited; four container images with nothing between them and the requirement text).

Three of the four are off the backend critical path. The room REST API is not. And onboarding is the
only one that could simply be cut from v1 without weakening what the project exists to demonstrate.

### What checked out — stated because a defect list misrepresents this corpus

**481 relative links resolve, zero broken. Zero dangling FR/NFR/CON citations. Only 4 misqualified
citations corpus-wide.** No config key has two defaults; no timing constant has two values; all six
job intervals agree across two documents; all seven secrets have a rotation story; every
`REFERENCES` target exists; across ten state machines, every CHECK enum value has a documented writer.

Agents sent to find defects confirmed instead: the **erasure scatter** is genuinely fixed on all five
objects; **erasure non-reversibility** is consistent across three documents with HMAC rejected twice
for the right reason; the **two-phase guest purge** is structurally guaranteed, not merely asserted;
**FR-INV-008's fix landed in the document that produces the closure**, not only the one stating the
rule; the **upload pipeline core** is coherent everywhere it is touched and `manifest.schema.json`
matches its prose exactly; the **postMessage trust boundary agrees message-for-message** across three
documents. The M2 blockers cluster in the *edges* — expiry, closure, chat, sweeps — while the
ownership and versioning core is clean.

### Fixes applied

**14 files still carried `</content>`/`</invoke>` tool scaffolding.** Session 9 reported this fixed
and had cleaned only the five data-model files; all eight flow documents, both deployment documents,
both `platform-frontend/` files and `test-harness.md` still had it.

Three citation fixes. Two sites cited `notifications-invitations.md FR-ALERT-006` — **document-qualified
and confidently wrong.** `FR-ALERT-006` exists, in `platform-operations.md`, as an unrelated
reconciliation alert, so the qualifier delivers a reader to a real requirement about something else.
Both meant FR-ALERT-010. A bare ID would have been safer than a wrong one. The third cited
`platform-operations.md FR-SEC-002` for a fail-startup rule that is FR-CRED-002.

One correction was **deliberately not made**: `data-model-accounts.md:392` cites FR-INV-002 for
invitation deletion on erasure, which is wrong, but the intended target is genuinely unclear. Recorded
rather than guessed.

### The registry

`docs/implementation/` — **60 work items across 7 milestones**, each carrying repo, dependencies, a
**Read first** list that should be sufficient on its own, the requirement IDs it satisfies, and a
*Done when* clause checkable without judgement. Every blocker is wired in as a **gate** against the
items it blocks, so an agent hits the block before writing code rather than after.

The invariants sessions 8 and 9 paid for are written into the items that need them — epoch fence not
room version, teardown keyed by session, commit-before-publish, two-phase guest purge, random-token
erasure, publication filtering — so an implementer meets each one at the point of use instead of
having to read this file.

### Process

**Both Opus agents — the two largest slices — returned bare idle notifications**, the failure mode
STATUS.md has now flagged three sessions running. It cost nothing here only because the brief
required findings to be written to a file first; both had produced 70 KB and 68 KB of good work. **The
mitigation is the file, not the reply.** Keep briefs file-first.

**Verify agent claims.** Four were checked and three did not survive: a "dangling `FR-JOB-007d`" is a
sub-duty convention used consistently in eight places; the `FR-GDK`/`FR-FEGDK`/`FR-HARNESS`
"duplicate definitions" are traceability matrices in the implementing specs — a feature, not a
collision; one of four "unindexed FK columns" is covered by a partial index. Reported as found, they
would have generated three phantom fix tasks.

**Two agents independently found the same manifest defect** (IR-18), which is the strongest evidence
in the round. The sharpest detail is theirs: `manifest/INDEX.md` states the *correct* async model, so
following the corpus's own "read the INDEX first" rule does not save you — the document it points at
is wrong in its body.

---

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

### The next session

**Close the M0 gates, then build the bootstrap.** Specifically:

1. **IR-01 and IR-02** — one short specification session. The MinIO bucket has no name and no
   creation step, and the two-role Postgres model has no provisioning mechanism. Both block
   `docker compose up` on a clean machine, which everything else is eventually tested against. IR-02's
   failure is silent rather than loud: a naive compose file makes the application role the superuser
   and violates FR-CRED-005 while appearing to work.
2. **IMP-M0-01 through IMP-M0-06** — all five repository skeletons plus the Flyway baseline. These
   are `READY` now and do not wait on the gates above.

**IMP-M0-06 is the highest-value item in the registry.** Transcribing `V1__baseline.sql` from the six
schema documents is the first mechanical test of whether they are mutually consistent, and the audit
already named two hazards to expect: the `bigserial` versus `GENERATED ALWAYS AS IDENTITY` split
across three sibling documents, and `schema-migrations.md`'s claim that
`room_participant.team_id → room_team` is one of "the two circular foreign keys" when by its own
stated table order it is not. Any further disagreement found while transcribing is a **specification**
defect — fix the document, then the SQL. Do not reconcile silently in the migration.

### Then, in order

3. **IR-13 — design the room REST API.** A design session. It gates all of M2, the longest milestone,
   and nothing else in the corpus can substitute for it.
4. **IR-06 … IR-12 — the seven remaining M2 correctness fixes**, as one pass. They are all edits to
   `room-lifecycle.md` and its neighbours and are best done by someone holding the whole ownership
   model in their head at once.
5. **IR-18** — propagate the async upload error contract to the three stale documents. Mechanical.
6. **IR-03, IR-05, IR-20** — three independent single-document fixes.
7. **IR-14 … IR-17** — the M3 execution-boundary fixes, before M3 starts. IR-17 should be scheduled
   deliberately rather than left standing as a trust-model fail-open.
8. **IR-19, IR-21, IR-22** — before any frontend work begins.
9. **IR-04 and IR-23** — the three remaining design sessions: observability, the design system, and
   onboarding. Independent of the backend critical path; **do not let them block it.** Onboarding is
   a legitimate v1 scope cut if the schedule needs one.

### Spec hygiene that still has no deadline

- **The ID-qualification retrofit.** `docs/specs/INDEX.md` states the rule and it holds for new text.
  The corpus predates it. The highest-traffic collision is `FR-SESS-001…004`, defined in both
  `user-accounts.md` (account sessions) and `platform-architecture.md` (Game Host in-memory state);
  seven citations were individually checked this session and all resolve correctly by context, so this
  is a hazard rather than a defect. Note that a **wrong** qualifier is worse than a bare ID — that is
  what the FR-ALERT-006 fixes were.
- **The `FR-JOB-007a…e` sub-duty convention** is used consistently in eight places and declared
  nowhere. One sentence in `docs/specs/INDEX.md`.
- **`data-model-accounts.md:392`** cites FR-INV-002 for invitation deletion on erasure. Wrong; correct
  target unclear. Left for whoever owns that document.
- The 62 non-blocking findings are in the per-slice files under
  `docs/reviews/2026-08-16-implementation-readiness/`, with the ten most likely to cost an implementer
  time called out in that directory's INDEX.

### Review action plan

`docs/reviews/2026-07-02-mvp-readiness/INDEX.md` — fully worked, closed.

`docs/reviews/2026-08-16-implementation-readiness/INDEX.md` — **open.** 23 blockers, none closed.
Gates are wired into the registry per work item.

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
