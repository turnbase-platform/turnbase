# Implementation-Readiness Review — 2026-08-16

A full-corpus audit run to answer one question before Phase 1 begins:

> Can a competent implementer, reading only the documents that own a topic, produce the intended code
> without making a decision the corpus should have made for them?

Phase 0 was declared complete on 2026-08-15. This review qualifies that claim against the specific
demand of Phase 1 — that implementation agents running at **low reasoning effort** can execute the
corpus without re-deriving architecture.

## Verdict

**The corpus is substantially implementation-ready, but not yet at the bar its own next phase
requires.** 23 blocking findings must be closed first. They are not distributed evenly, and the
distinction matters for planning:

- **Nineteen are drift or omission in otherwise sound designs.** Two documents disagree, a fix landed
  in the hub document but was never chased into the three that copy the same contract, or a rule was
  stated without a mechanism. These are cheap — hours each, and the correct answer is usually
  recoverable from the surrounding text.
- **Four are the absence of design work altogether.** `platform-ui-library.md` (~30 requirements),
  `onboarding-wizard.md` (16 requirements), the room REST API, and observability wiring have no
  implementing specification anywhere in the corpus. These need design sessions, not edits.

The strongest parts of the corpus — the room-lifecycle concurrency model, the account erasure and
guest-purge mechanics, the upload state machine, the configuration surface — are unusually rigorous
and were repeatedly confirmed correct by agents that went looking for defects and reported finding
none. Several defects that previous sessions claimed to have fixed were independently re-verified as
genuinely fixed, in the document that produces the behaviour rather than only the one that states the
rule.

## How this review was run

Thirteen agents across three model tiers, dispatched from a shared brief
(severity ladder, evidence standard, output format) with per-slice scenario lists.

| Tier | Count | Work |
|---|---|---|
| **Haiku** | 4 | Mechanical inventories — API surface, relational schema, configuration/ops surface, state machines. Extraction and tabulation only, no judgement. |
| **Sonnet** | 6 | Domain audits — accounts, catalog/upload, history/notifications, frontend, API conventions, deployment/ops. |
| **Opus** | 2 | The two subtlest slices — rooms/realtime concurrency, and the game-execution trust boundary. |
| *(orchestrator)* | 1 | Deterministic scripted checks, verification of agent claims, consolidation. |

Four checks were run by script rather than by agent, because they are deterministic and an agent
would only add hallucination risk: link integrity, requirement-ID collision mapping,
requirement→spec citation coverage, and misqualified cross-document citations.

**Agent claims were not taken at face value.** Every blocker recorded below whose severity depends on
a factual claim was re-verified against the source text by the orchestrator. Three agent claims were
rejected on verification and are recorded under *Claims rejected* at the end.

## Files

| File | Slice | Findings |
|------|-------|----------|
| [rooms-realtime.md](rooms-realtime.md) | Room lifecycle, ownership, grace, teardown, STOMP protocol | 8 BLOCKER, 3 AMBIGUITY, 6 GAP, 3 DRIFT, 1 NIT |
| [game-execution.md](game-execution.md) | Game Host, Espresso, gRPC, GDK | 4 BLOCKER, 3 AMBIGUITY, 3 GAP, 6 DRIFT, 2 NIT |
| [frontend.md](frontend.md) | Shell, views, design system, iframe boundary | 4 BLOCKER, 1 AMBIGUITY, 1 GAP, 1 NIT |
| [deployment-ops.md](deployment-ops.md) | Local stack, migrations, config, secrets, observability | 3 BLOCKER, 5 GAP, 4 DRIFT, 1 NIT |
| [catalog-upload.md](catalog-upload.md) | Catalog, upload pipeline, bundle format, asset serving | 2 BLOCKER, 1 AMBIGUITY, 1 DRIFT |
| [accounts-auth.md](accounts-auth.md) | Accounts, auth, sessions, guests, social graph | 1 BLOCKER, 1 AMBIGUITY, 4 GAP, 1 DRIFT |
| [api-conventions.md](api-conventions.md) | REST shape, errors, validation, pagination, rate limits | 1 BLOCKER, 2 GAP, 1 DRIFT, 1 NIT |
| [history-notifications.md](history-notifications.md) | History, statistics, notifications, invitations | 1 BLOCKER, 1 GAP, 1 DRIFT, 1 NIT |
| [inventories/](inventories/) | Machine-extracted reference tables (see below) | — |
| [remediation-plan.md](remediation-plan.md) | The task-by-task plan that closes all 23 blockers, with the four scope decisions taken before execution | — |

### Inventories

Working artifacts, kept because they are useful during implementation. **They are extraction, not
authority** — where an inventory disagrees with a spec, the spec wins.

| File | Contents |
|------|----------|
| [inventories/api-surface.md](inventories/api-surface.md) | REST endpoints, STOMP destinations, close codes, SSE events, gRPC RPCs, error codes |
| [inventories/schema.md](inventories/schema.md) | Every table, column, constraint, index and Redis key, with source lines |
| [inventories/config-ops.md](inventories/config-ops.md) | Config keys, secrets, containers, jobs, timing constants, rate-limit buckets, metrics |
| [inventories/state-machines.md](inventories/state-machines.md) | Ten state machines with transition tables and reachability analysis |
| [inventories/coverage.md](inventories/coverage.md) | The 161 requirements cited by no spec, grouped by owning document |

---

## Blocker register

Stable IDs. The implementation registry gates work items on these — see
[`../../implementation/registry.md`](../../implementation/registry.md) *Readiness gates*.

Each entry names **the milestone it gates**, so the fix effort can be sequenced against the build.

### Gating M0 — bootstrap

#### IR-01 — No MinIO bucket name or creation mechanism exists anywhere

**Where:** `docs/specs/deployment/local-environment.md:444`;
`docs/specs/deployment/secrets-and-configuration.md:204-213`

The object store is a listed container with credentials, a port and a console, but the corpus never
names the bucket the platform writes bundles to, and specifies no creation step. Grepping all of
`docs/` for an object-store bucket returns nothing.

**Blocks:** `docker compose up` followed by `make seed` on a clean machine — literally the first task
of the next session (IMP-M0-07, IMP-M0-12). The seeder drives the real upload pipeline, which writes
to a bucket that does not exist.

**Fix owner:** `local-environment.md` §7.9 (name + env var) and §5 (creation, via a MinIO init
container or an `mc mb` step).

---

#### IR-02 — The two-role Postgres model has no provisioning mechanism

**Where:** `docs/decisions/0011-schema-migrations.md:99-109`;
`docs/specs/deployment/secrets-and-configuration.md:21,173-191`

ADR-0011 and `platform-operations.md` FR-CRED-005 require an unprivileged `turnbase_app` role
separate from a `turnbase_owner` role that performs extension creation. No init script is named or
located, and the secrets inventory lists a single undifferentiated "PostgreSQL password".

**Blocks:** IMP-M0-07 and IMP-M0-09. The failure is silent rather than loud: a naive compose file
sets `POSTGRES_USER=turnbase_app`, which makes the application role the superuser owner and violates
FR-CRED-005 while appearing to work perfectly.

**Fix owner:** `secrets-and-configuration.md` (two credentials, two env vars) and
`local-environment.md` §5 (the init mechanism).

---

#### IR-03 — `platform-operations.md` contradicts itself on CI coverage gating

**Where:** `docs/requirements/platform-operations.md:107` (FR-CICD-003) versus `:232` (OQ-002)

FR-CICD-003 requires a PR-time coverage gate measured "across all test types combined". OQ-002 moves
e2e tests to post-merge. The PR gate therefore cannot compute the number it is required to enforce,
because part of its input does not exist at PR time. Neither statement is marked authoritative.

**Blocks:** IMP-M0-11. An implementer writing the workflow must choose, and both choices are
defensible, which is precisely the decision the corpus should have made.

**Fix owner:** `platform-operations.md` — either narrow FR-CICD-003 to unit+integration, or move the
gate post-merge.

---

#### IR-04 — Observability is unwired beyond the requirement statements

**Where:** `docs/requirements/platform-operations.md:66-97` (FR-MET-001…006, FR-TRACE-001…004,
FR-ALERT-005); `docs/specs/deployment/local-environment.md:437-449`

Prometheus, Grafana, Loki and Tempo are listed containers, but the corpus specifies no OTLP endpoint
property, no Prometheus scrape configuration, no log-shipping path to Loki under compose, no Grafana
datasource or dashboard provisioning, and no Alertmanager or alert-routing mechanism for FR-ALERT-005.
The scripted coverage check confirms it independently: **all ten `FR-MET-*` and `FR-TRACE-*`
requirements are cited by no spec anywhere in the corpus.**

**Blocks:** IMP-M0-10. This is design work, not a missing config line — see *Structural gaps*.

---

### Gating M1 — accounts

#### IR-05 — The profile owner has no exemption from their own privacy settings

**Where:** `docs/requirements/platform-views.md:294-306,319-325`; contradicts
`user-accounts.md` FR-PROF-007 and `social-friends.md` FR-SOC-018

`platform-views.md`'s profile and friends view tables state visibility rules with no owner carve-out.
Read literally — which is how a low-effort implementer reads them — a user who sets their own profile
to private sees *their own profile* rendered as "private" instead of their own content. Neither
`platform-views.md` nor `data-model-accounts.md`'s privacy-resolution schema states the bypass
anywhere.

**Blocks:** IMP-M1-07 and IMP-M6-03. Cheap to fix — a documentation addition, not a redesign — but it
must be fixed before anyone builds profile visibility, because the wrong behaviour is the
straightforward literal reading.

---

### Gating M2 — rooms and realtime

The largest concentration of blockers in the corpus, in its most subtle machinery. All eight were
found by the Opus auditor walking failure scenarios end to end; the two marked **verified** were
additionally re-confirmed against source by the orchestrator.

#### IR-06 — Grace expiry in a Lobby room aborts permanently on a `NOT NULL` violation *(verified)*

**Where:** `docs/specs/platform/room-lifecycle.md:392-395` (§3.3) and `:396-418`;
`docs/specs/platform/data-model.md:315`

§3.3's in-transaction side effects are: (1) the `UPDATE`, (2) "Insert the `player_left` row into
`game_input_outbox`" — **unconditionally**. `game_input_outbox.session_id` is `NOT NULL`. A Lobby
room has `active_session_id = NULL`, which §3.4 states explicitly ("There is also no session to
detach: `active_session_id` is null").

Step 4 (closure evaluation) carries a carefully reasoned Lobby exemption. **Step 2 does not.**

**Failure:** a player disconnects from a Lobby room; §1.4 step 4 opens a reservation in *any* state
(required by FR-DC-007); the reservation comes due; the expiry transaction attempts the outbox insert
with a null `session_id`; the constraint aborts the whole transaction; the reservation is never
resolved; the sweep retries it every 5 seconds forever. The room is stuck and the sweep logs an error
loop.

**Fix owner:** `room-lifecycle.md` §3.3 — make step 2 conditional on `active_session_id IS NOT NULL`.

---

#### IR-07 — Graceful drain re-triggers the exact cascade FR-DC-007 exists to prevent

**Where:** `docs/specs/platform/room-lifecycle.md:236-240`, `:170-174`;
`docs/specs/flows/04-disconnect-and-return.md:16-18`

Self-eviction and graceful drain close client sockets. Closing a socket fires the ordinary disconnect
handler, and in a Lobby room `reconnection-flow.md` FR-DC-002 makes a disconnect an immediate leave.
Chained with FR-XFER-002 (close a room whose host has left with no humans remaining), a rolling
deploy deletes Lobby rooms — the precise failure FR-DC-007's carve-out was written to stop, arriving
by a path the carve-out does not cover.

**Fix owner:** `room-lifecycle.md` §2 — the drain path must suppress the disconnect handler, or mark
the disconnect as instance-initiated.

---

#### IR-08 — Chat consumes the room version but reaches only a subset of subscribers

**Where:** `docs/specs/api-design/room-chat-websocket.md:29-31`;
`docs/specs/api-design/room-websocket.md:726`

Chat messages advance the room `version`, but team-channel messages are delivered to a *subset* of
`/topic/room.{roomId}` subscribers. Clients gap-detect on `version`. Every spectator and every
off-team player therefore observes a permanent version gap and requests a snapshot.

**Failure:** one team chat message in a room with spectators produces a resync storm — and the
storm's cost is `websocket.md` OQ-001's known hotspot, reached here by an ordinary action rather than
an adversarial one.

**Fix owner:** `room-chat-websocket.md` — chat must either not consume the room version, or ride a
separate sequence.

---

#### IR-09 — Deadline-sweep duty 2 matches every released participant

**Where:** `docs/specs/platform/room-lifecycle.md:557-560`; `docs/specs/platform/data-model.md:218-224`

Duty 2's predicate as written matches *any* participant row in the released state, not only those
released by grace expiry. Voluntary leaves, host kicks and room closures all match.

**Failure:** every ordinary leave draws a phantom `PLAYER_LOST` broadcast and a spurious closure
evaluation, one sweep interval after the real event that already handled it.

**Fix owner:** `room-lifecycle.md` §5.1 — narrow the predicate on `leave_reason`, and add the index
noted in the slice file (finding 15: the only participant index is partial on the *opposite*
predicate).

---

#### IR-10 — `detachSession` mutates the room row with no version bump and no epoch fence

**Where:** `docs/specs/platform/room-lifecycle.md:477-492` versus `:176-194` (§1.5)

§1.5 states that **every** mutation of the `room` row carries the epoch fence and bumps the version.
§4's `detachSession` transaction does neither.

**Failure:** this is the ADR-0008 defect class the epoch was introduced to close. A stale owner can
detach a session under the legitimate owner, and clients never see a version bump for a state change
they must observe.

**Fix owner:** `room-lifecycle.md` §4.

---

#### IR-11 — "Record the closure as owed" names no table, and another document says it is synchronous

**Where:** `docs/specs/platform/room-lifecycle.md:468`, `:475-476`;
`docs/specs/platform/data-model-accounts.md:395,422`

The account-deletion closure path says the closure is "recorded as owed" but names no table, no
column and no sweep duty that consumes it. `data-model-accounts.md` describes the same closure as
synchronous. Both cannot be built.

**Fix owner:** `room-lifecycle.md` §4 and `data-model-accounts.md` §5 must agree. Note the ADR-0010
lesson: if it is a durable to-do, it must be keyed by session, and the rule that reads it must not
test state that its own success deletes.

---

#### IR-12 — AI players are load-bearing in the protocol and absent from the schema

**Where:** `docs/specs/api-design/room-websocket.md:151-158,566`;
`docs/specs/platform/room-lifecycle.md:403-405`; `docs/specs/platform/data-model.md:158-178`

`ROOM_STATE` carries AI participants on the wire, and the closure predicate turns on "not an AI"
(§3.3 step 4, quoted in IR-06's context). `room_participant` has no column distinguishing an AI from
a human.

**Failure:** the closure predicate cannot be written. It is also the predicate that decides whether a
room full of AI players closes when the last human leaves.

**Note:** `game-contracts.md` OQ-002 defers the *AI/bot player interface* to a future spec. That
deferral is legitimate; what is not legitimate is that two shipped mechanisms already depend on a
representation the deferral was assumed to postpone. **This OQ is mislabelled as non-blocking.**

**Fix owner:** `data-model.md` §3 — either add the discriminator, or remove AI from the wire protocol
and the closure predicate for the MVP.

---

#### IR-13 — No REST specification exists for the room API *(verified)*

**Where:** absent from `docs/specs/api-design/` entirely. `POST /api/rooms` appears only in
`docs/specs/flows/02-room-to-game-start.md:15` (a narrative step) and as a query-string example in
`docs/specs/api-design/pagination-filtering-sorting.md:44`.

`rest-conventions.md` tabulates the auth endpoints and gives authorization rules for
`/api/rooms/{id}` at line 94 — but no document anywhere defines the room endpoints' paths, methods,
request bodies, response bodies or status codes.

**Corroborated independently by the coverage script:** all of FR-CREATE-001/002/004,
FR-HOST-001/002/008, FR-JOIN-001…005/009/010/011 and FR-LIST-002…007 are cited by no spec.

**Blocks:** IMP-M2-01, and by dependency the whole of M2. This is the entry point for every join,
create and rejoin scenario in the corpus. See *Structural gaps*.

---

### Gating M3 — game execution

#### IR-14 — `session:{id}` has two claimed writers, disarming `CreateSession`'s idempotency guard

**Where:** `docs/specs/flows/02-room-to-game-start.md:115`;
`docs/specs/game-host/game-host-internals.md:647`; `docs/requirements/platform-architecture.md:130`

Orchestration pre-writes the session key; the Game Host's `CreateSession` treats the key's existence
as its idempotency guard.

**Failure:** the guard fires on the first call, so `onInit` never runs. The game starts with no
initial state and no initial effects.

**Fix owner:** `game-host-internals.md` §9 and flow 02 must agree on a single writer.

---

#### IR-15 — The two owning documents disagree on whether `lastAppliedSequence` advances on a failed input

**Where:** `docs/specs/internal-grpc/orchestration-gamehost-protocol.md:271`;
`docs/specs/game-host/game-host-internals.md:404-412`, `:358-362`

The protocol document says the sequence is burned and `lastAppliedSequence` advances, so a redelivery
replays the same failure. The internals document's session record has nowhere to store a failure.

**Failure:** the replay path returns `OK` carrying the *previous* input's effects — a silent wrong
answer rather than a visible error.

---

#### IR-16 — Proto and prose disagree on out-of-order sequence handling

**Where:** `docs/specs/internal-grpc/gamehost.proto:39-40` versus
`docs/specs/internal-grpc/orchestration-gamehost-protocol.md:270`

The proto comment instructs the Game Host to "reject out-of-order/duplicate sequences defensively".
The prose makes forward sequence gaps a normal consequence of failure handling.

**Why this is a blocker rather than drift:** codegen follows the proto and humans follow the prose,
so the two readings land in different files of the same service. A defensive implementer following
the proto freezes every session after its first failed action.

---

#### IR-17 — No server-side check that a game-addressed `player_id` belongs to the session *(verified)*

**Where:** `docs/specs/api-design/websocket.md:255`, `:263`;
`docs/requirements/game-contracts.md:169` (NFR-SEC-002, Must)

`websocket.md:263` argues NFR-SEC-002 is "mechanically true rather than aspirational" because
`send_to_player` rides a per-user queue a client cannot subscribe to on another's behalf. That
argument secures the **subscription**. It does not secure the **address**: nothing validates that
`SendToPlayerEffect.player_id`, which is chosen by game code, identifies a participant of the session
that produced it.

**Failure:** game code returns a `player_id` for a user in another room, and Spring delivers it to
that user's queue. Under ADR-0006 the MVP's games are first-party, so this is not currently
exploitable — which is exactly the problem. It is a **fail-open gated on the trust model**, of the
class GRMP lesson F5 names, and the document asserts the property is mechanical.

**Fix owner:** `websocket.md` §5 — require session-membership validation of every effect address at
fan-out, and soften the NFR-SEC-002 claim to name the check that makes it true.

---

### Gating M4 — catalog and upload

#### IR-18 — The async-validation error contract never propagated to three documents

**Where:** `docs/specs/manifest/manifest-schema.md:192-215`;
`docs/specs/api-design/file-uploads.md:154-156`;
`docs/specs/flows/08-upload-to-play.md:47-49,55-56`

`error-handling.md` and `bundle-format.md` §3.4 fixed this: manifest validation needs the bundle
bytes, so it can only run after `confirm` has already returned `202`, and failures surface as the
version resource's `FAILED` state via `GET .../versions/{uploadId}` — never as a `422`.

Three documents still describe a synchronous `422`, including **`manifest-schema.md`, the document
that owns manifest validation**. `file-uploads.md:156` contradicts its own error table three lines
above. Flow 08 asserts both `202` and a synchronous `422` for the same request.

**Found independently by two agents** (api-conventions F1, catalog-upload F1), which is why it is
recorded once here.

**Sharpest detail:** `manifest/INDEX.md`'s own key-decisions list states the *correct* model. Following
the corpus's own "read the INDEX first" rule does not save an implementer, because the document the
index points at is wrong in its body.

---

#### IR-19 — Info-document Markdown sanitization has no implementation spec

**Where:** `docs/requirements/game-catalog.md:48` (FR-GDET-004);
`docs/specs/api-design/input-validation.md:182-195`; `docs/specs/manifest/bundle-format.md:494`

FR-GDET-004 requires the game detail page to render a developer-supplied Markdown info document. No
library, no server-versus-client split and no allow-list is named anywhere.
`input-validation.md:182-195` compounds it by asserting the game-log renderer is "the only surface
where the platform renders anything other than plain text", which is not true.

**Why it is a real security finding:** unlike game frontends, this surface renders on the **trusted
platform origin**, which carries the session cookie. It is also the one XSS sink whose content comes
from an uploaded artifact. `input-validation.md`'s platform-wide ESLint ban on
`dangerouslySetInnerHTML` rules out the naive implementation, so an implementer has no sanctioned
path at all.

**Fix owner:** unowned — it falls between `game-catalog.md`'s requirement, `bundle-format.md`'s data
flow and `input-validation.md`'s security rules, and no document's scope section claims it. Assign it.

---

### Gating M5 — history and notifications

#### IR-20 — No job purges expired friend requests or room invitations

**Where:** `docs/specs/platform/data-model-social.md:152`;
`docs/specs/platform/data-model-notifications.md:199`; `docs/requirements/platform-operations.md:140-156`

Two schema documents assert that "the purge job" deletes expired `friend_request` and
`room_invitation` rows, and the notification design depends on it: the `notification_purge_idx`
partial index deliberately excludes actionable notifications from the generic sweep, on the
understanding that deleting the subject cascades the notification away.

`platform-operations.md`'s scheduled-job list is FR-JOB-001…012 and contains no such job. Nothing
scans `friend_request_expiry_idx` or `room_invitation_expiry_idx`.

**Failure:** an invitation nobody acts on is never deleted, so its notification is never purged. This
is a **regression of the exact bug session 9 believed it had fixed** — adding an `expires_at` column
made expiry *expressible*, but no writer or sweeper acts on it.

**Fix owner:** `platform-operations.md` — add the job. This is the "a rule whose supporting state has
no actor" pattern the last two sessions kept hitting.

---

### Gating M6 — frontend

#### IR-21 — The game iframe `sandbox` attribute is directly contradicted

**Where:** `docs/specs/platform-frontend/shell-architecture.md:142` versus
`docs/specs/game-frontend/game-asset-serving.md:232`

`shell-architecture.md` specifies `allow-scripts` only, with a stated rationale for why
`allow-same-origin` would be dangerous. `game-asset-serving.md` specifies
`allow-scripts allow-same-origin`, with a stated rationale for why it is safe given the separate
registrable domain (ADR-0007). Both claim to own the value; neither acknowledges the other.

**Failure if `shell-architecture.md`'s version ships:** the frame gets an opaque origin. Game engines
lose `localStorage` and `IndexedDB`, and — the part that makes this a blocker rather than a
preference — `event.origin` becomes the string `"null"`, so the shell's own origin check drops every
message the game sends. The relay fails silently and completely.

**Fix owner:** ADR-0007 governs; `game-asset-serving.md`'s reasoning is the one consistent with it.
Make one document authoritative and have the other cite it.

---

#### IR-22 — The platform shell's Content-Security-Policy is specified nowhere

**Where:** `docs/specs/game-frontend/game-asset-serving.md:265-274`;
`docs/specs/platform-frontend/shell-architecture.md` (no CSP content anywhere)

`game-asset-serving.md` §6.3 requires the shell to pin `frame-src` and explicitly delegates the rest
of the shell's CSP to the frontend shell specification. That specification has no CSP section.

**Blocks:** IMP-M6-02. The delegation target does not exist, so the platform origin — the one holding
the session cookie — ships with no specified policy.

---

#### IR-23 — Two entire requirement documents have no implementing specification

**Where:** `docs/requirements/platform-ui-library.md` (~30 requirements);
`docs/requirements/onboarding-wizard.md` (16 requirements)

See *Structural gaps* below. Recorded as one blocker because the remedy is one decision: schedule the
design work, or cut the scope from v1.

---

## Structural gaps

Four of the blockers above are not defects to correct but **design work that was never done**. They
are called out separately because they cannot be fixed by editing, and because together they are the
main threat to the stated Phase 1 premise that implementation agents need no architecture sessions.

| Gap | Scale | Evidence |
|---|---|---|
| **Design system** (IR-23) | ~30 requirements, 24 uncited | No spec in `docs/specs/` covers tokens, CSS strategy, or component architecture. Only FR-COMP-010 is cited anywhere. Compounding: `platform-ui-library.md` CON-002 requires it to live in its own submodule, and `CLAUDE.md`'s five-repo component table has no such repo. |
| **Onboarding wizard** (IR-23) | 16 requirements, all 16 uncited | The entire document is referenced by nothing else in the corpus — no mount point, no trigger wiring, and no CTA row in `platform-views.md`'s own landing-page element table despite FR-ONB-004 requiring one. |
| **Room REST API** (IR-13) | ~21 requirements uncited | The entry point to all of M2. |
| **Observability** (IR-04) | 10 requirements, all uncited | Metrics, tracing, log shipping and alert routing exist as requirement statements and container images with nothing between them. |

**Recommendation:** these are four short design sessions, not one long one, and three of them
(design system, onboarding, observability) are independent of the backend critical path. The room
REST API is not — it gates M2 and should be done first.

**Scope alternative worth considering:** `onboarding-wizard.md` is the only one of the four that could
simply be cut from v1 without weakening the demonstration the project exists to make. It is 16
requirements of first-run polish on a platform whose v1 audience is the author.

---

## Non-blocking findings

62 findings below blocker severity are recorded in the per-slice files: 8 AMBIGUITY, 22 GAP, 20 DRIFT,
7 NIT (plus the 23 blockers above; two agents reported the same manifest defect, counted once).

The ones most likely to cost an implementer time, with slice file for detail:

- **`FR-SESS-*` collides across two requirement documents** with unrelated meanings — account sessions
  in `user-accounts.md`, Game Host in-memory state in `platform-architecture.md`. IDs 001–004 collide.
  Seven citations in `data-model-accounts.md` and `secrets-and-configuration.md` are unqualified; all
  seven were checked individually and resolve correctly by context, so this is an ambiguity rather
  than a defect — but it is the highest-traffic collision in the corpus. (`accounts-auth.md` F5)
- **Argon2id is pinned as the algorithm with no cost parameters** anywhere. (`accounts-auth.md` F6)
- **Profile privacy has no REST endpoint** despite dedicated UI, DB columns and a `PATCH` worked
  example in `rest-conventions.md` that names the operation without naming the route.
  (`api-conventions.md` F2)
- **`FR-ACCT-010` (password change) has no route**, unlike every other auth endpoint.
  (`accounts-auth.md` F7)
- **No consolidated WebSocket error-code registry.** `room-websocket.md` has a good 21-row table;
  game-session codes `ACTION_TOO_LARGE` and `ACTION_REJECTED` exist only as prose in `websocket.md`;
  `error-handling.md` never mentions WebSocket errors. (`api-conventions.md` F4)
- **Offset pagination is mandated for the notification centre**, a list under continuous real-time
  insert, with no discussion of page drift. (`history-notifications.md` F2)
- **Inconsistent `bigserial` versus `GENERATED ALWAYS AS IDENTITY`** across three sibling schema
  documents with no stated convention — a transcription hazard for IMP-M0-06.
  (`deployment-ops.md` F10)
- **`schema-migrations.md` mislabels `room_participant.team_id → room_team` as circular** when by its
  own stated table order it is not. Only `game`/`game_version` actually is.
  (`deployment-ops.md` F9)
- **The GDK's flagship example violates the determinism rule stated 60 lines above it.** This is the
  code a game developer copies. (`game-execution.md` F15)
- **`test-harness.md` tells developers the Game Host blocks filesystem and network calls** — the exact
  claim the Espresso spike disproved. (`game-execution.md` F11)

---

## Corrections applied during this review

Four mechanical corrections were made directly, being unambiguous and verified:

| Fix | Detail |
|---|---|
| **14 files** stripped of `</content>` / `</invoke>` tool scaffolding | Session 9 reported fixing this and cleaned only the five data-model files. The whole of `docs/specs/flows/` (all 8 files), both deployment documents, `platform-frontend/` (2), and `gdk-api/test-harness.md` still carried it. |
| `shell-architecture.md:210` | `notifications-invitations.md` FR-ALERT-006 → **FR-ALERT-010** |
| `sse-notifications.md:18` | `notifications-invitations.md` FR-ALERT-006 → **FR-ALERT-010** |
| `bundle-format.md:598` | `platform-operations.md` FR-SEC-002 → **FR-CRED-002** |

The FR-ALERT-006 citations were the worst class of citation defect in the corpus: **document-qualified
and confidently wrong.** `FR-ALERT-006` does exist — in `platform-operations.md`, as a reconciliation
repair alert — so a reader following the qualifier lands on a real requirement about something else.
Both sites meant FR-ALERT-010 (alerts as a distinct delivery class). A bare ID would have been safer.

`bundle-format.md` cited the right document but the wrong ID; the "missing configuration must fail
startup" rule is FR-CRED-002, and FR-SEC-002 (`platform-architecture.md`) is about outbound network
egress.

**One correction was deliberately not made.** `data-model-accounts.md:392` cites `FR-INV-002`
(friends-only restriction) for room-invitation deletion on erasure, which is certainly wrong, but the
intended target is not certain — FR-INV-001 establishes that invitations exist, while the deletion
duty itself is FR-ACCT-005. Recorded rather than guessed.

---

## What checked out

Stated with evidence, because a readiness review that only lists defects misrepresents the corpus.

**Scripted, whole-corpus:**
- **481 relative markdown links resolve. Zero broken.**
- **Zero dangling `FR`/`NFR`/`CON` citations** — every ID cited anywhere is defined somewhere.
- **Only 4 misqualified citations** across the whole corpus, of which 3 were real and are now fixed.
- **Configuration surface is consistent**: no config key has different defaults in different files, no
  timing constant appears with two values, all six job intervals agree between
  `local-environment.md` §7.2 and `platform-operations.md`, and all seven secrets have a stated
  rotation story.
- **No orphaned tables**: every `REFERENCES` target is defined, and every erasure-cascade target in
  `data-model-accounts.md` §5 exists.
- **No unreachable enum values**: every status value in every CHECK constraint has at least one
  documented writer, across ten state machines.

**Confirmed by agents that went looking for defects:**
- The **account erasure scatter** — session 9's target defect — is genuinely fixed. All five objects
  in the scenario (hosted room, pending friend request, game history, open review, invitation on both
  legs) have explicit dispositions.
- **Erasure non-reversibility** is consistent across ADR-0004, `data-model-history.md` and
  `data-model-accounts.md`, with HMAC explicitly rejected in two places for the same correct reason.
- **The two-phase guest purge** is fully specified, and "a seated guest cannot be hard-deleted" is
  structurally guaranteed rather than merely asserted.
- **FR-INV-008's fix landed in the document that produces the closure** (`flows/07:43` has the actual
  `DELETE`), not only in the document that states the rule — the failure mode session 9 called out.
- **JWT key rotation** is self-contained and consistent.
- **The `ghe_placement_ck` fix is real**: boundary validation before the transaction, CHECK as backstop.
- **The upload pipeline's core** — state machine, crash-recovery lease, FR-JOB-012, the official-game
  badge transition, advisory-versus-authoritative version ordering — is coherent across every document
  that touches it. `manifest.schema.json` and `manifest-schema.md` agree with no drift.
- **The postMessage trust boundary agrees message-for-message** across `shell-architecture.md`,
  `game-asset-serving.md` §6.2 and `frontend-gdk-api.md` §8 — origin, source and shape checks all
  match. (The `sandbox` attribute, IR-21, is the one exception.)
- **Migration discipline** (ADR-0011) and **readiness independence** (the monolith must not depend on
  the Game Host) are both implementable exactly as written.
- **Every deferred `OQ-*` in the catalog slice was individually assessed** and correctly deferred —
  they gate the community-upload path, which ADR-0006 makes unreachable in the MVP. The one
  mislabelled deferral found anywhere is `game-contracts.md` OQ-002 (see IR-12).

---

## Claims rejected on verification

Recorded so they are not re-raised.

| Claim | Verdict |
|---|---|
| `room-websocket.md:326` cites `FR-JOB-007d`, which is defined nowhere *(scripted check)* | **Rejected.** `FR-JOB-007` defines duties (a)–(e) and the corpus refers to them as `FR-JOB-007a…e` in 8 places consistently. Not a dangling citation — but the sub-duty convention is never declared, which is worth one sentence in `docs/specs/INDEX.md`. |
| `sse-notifications.md` cites a nonexistent `FR-ALERT-006` *(`history-notifications.md` NIT)* | **Partially rejected.** The ID exists, in `platform-operations.md`. The defect is real but is a misqualification, not a dangling reference — a more dangerous failure than reported. Fixed. |
| Four FK columns have no index *(`inventories/schema.md` §5a)* | **Partially rejected.** `room.game_id` is covered by `room_open_game_idx (game_id, game_version) WHERE state <> 'CLOSED'`. `room.host_user_id` genuinely has none and is touched by account deletion — that one stands. |
| `FR-GDK-*`, `FR-FEGDK-*`, `FR-HARNESS-*` are each defined in two documents *(scripted check)* | **Rejected.** The second "definition" is a traceability matrix in the implementing spec — a feature of the corpus, not a collision. The heuristic over-counted; the true multi-document count is far below the raw 252. |

---

## Recommended fix order

Sequenced so that nothing blocks the build for longer than it must.

1. **IR-01, IR-02** — one short session. Unblocks `docker compose up`, the literal first task.
2. **IR-13 (room REST API)** — a design session. Gates all of M2, the longest milestone.
3. **IR-06 … IR-12** — the seven remaining M2 correctness fixes. All are edits to
   `room-lifecycle.md` and its neighbours, and are best done as one pass by someone holding the whole
   ownership model in their head.
4. **IR-18** — propagate the async error contract to the three stale documents. Mechanical.
5. **IR-03, IR-05, IR-20** — three independent single-document fixes.
6. **IR-14 … IR-17** — the M3 execution-boundary fixes. Not urgent until M3, but IR-17 should be
   scheduled deliberately rather than left as a trust-model fail-open.
7. **IR-19, IR-21, IR-22** — before any frontend work starts.
8. **IR-04, IR-23** — the three remaining design sessions (observability, design system, onboarding),
   or an explicit scope cut. Independent of the backend critical path; do not let them block it.

**Do not start implementation of a milestone whose gates are open.** The registry
([`../../implementation/registry.md`](../../implementation/registry.md)) encodes these gates per work
item so an implementation agent hits the block before writing code rather than after.
