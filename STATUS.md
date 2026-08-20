## Last Session Summary

**Date:** 2026-08-20 (session 13)

**A pre-implementation readiness review of the harness rather than the corpus**, and the first seven
fixes it produced. The specifications were already implementation-ready; what was missing was the
layer beneath them — the conventions every work item assumes and none of them states. Still no code.

### What the review found

The corpus says *what* to build (requirements), *how it is designed* (specs) and *what to build next*
(the registry). It said nothing about **how the code is written**: no package layout, no formatter, no
coverage tool, no test-suffix convention, no cross-repo version rule. Forty of the 59 work items land
in `turnbase-platform`, executed across many sessions by agents that each read only their own item's
read-list. Forty items with no stated layout do not produce one layout.

**The corpus's only evidence of the monolith's package root was a logger name in a JSON sample** in
`observability.md`, written to illustrate log structure rather than to decide anything. That is the
shape of the whole gap: the decisions existed nowhere, so the first item to need one would have made
it silently and the next thirty would have disagreed.

### Seven defects, all closed

| # | Defect | Fix |
|---|---|---|
| 1 | FR-CICD-002/006/007 + CON-009 + OQ-002 gated on `main`; every repo is on `master` | Corrected against ADR-0012's branch model. A workflow written from the old text never fires |
| 2 | FR-CICD-004 said integration tests use Docker Compose; `local-environment.md` §8 says Testcontainers and rejects a hand-started stack | §8 was right. The requirement now states the reason inline so it does not get re-broken |
| 3 | IMP-M3-10's repo was "external consumer of `turnbase-sdk`" — no such repo, and ADR-0012 lists five | Deferred **by decision**: `turnbase-game-<name>` is created when the item starts, with the steps recorded on the item |
| 4 | FR-CICD-003 gates on coverage; no tool named anywhere | JaCoCo, over **merged** unit + integration exec data |
| 5 | Google Java Style was a `CLAUDE.md` SHOULD with no mechanism | Spotless + `google-java-format` at `validate` |
| 6 | No package layout, and none for tests either | ADR-0014 + `conventions.md` §§1, 3 |
| 7 | No cross-repo version rule; IMP-M0-01 ended at "installs to the local Maven repository" | Exact-version pinning, a `-D` override for the local loop, and a stated release order |

### Two new documents

**[`docs/implementation/conventions.md`](docs/implementation/conventions.md)** — package layout,
formatting, tests and coverage, git, cross-repo dependencies, and the per-repo build floor. Declared
normative, and deliberately **not** repeated in read-lists: it is assumed the way `CLAUDE.md` is.
`implementation/INDEX.md` now carries the rule that makes that safe — *if you are deciding something
that should be the same across all forty platform items, the answer belongs in `conventions.md` and
its absence is a defect.* Settling it locally is what produces four conventions.

**[ADR-0014](docs/decisions/0014-modular-monolith-spring-modulith.md)** — the monolith is packaged by
feature under `io.turnbase.platform`, and **Spring Modulith fails the build** when one feature reaches
into another's internals. Adopted at skeleton time, in `IMP-M0-03`.

Three things about it worth carrying:

- **The twelve feature packages are the milestone decomposition**, lifted from the registry rather
  than invented. That is why it costs nothing: every work item already knows its package without
  anyone deciding.
- **Enforced rather than documented, because the code is written by agents reading one item at a
  time.** An agent cannot see the boundary it is about to cross. A boundary that is a build error is
  a boundary; a boundary that is a sentence in a conventions document is a preference.
- **Retrofitting was the rejected option.** After thirty items it means fixing every accumulated
  violation at once, at the point where the boundaries have already stopped being real.

### The decisions taken, and why they went the way they did

- **Spotless over Checkstyle for format.** A formatter that *rewrites* gives an agent a diff; a linter
  gives it forty complaints to hand-edit. `./mvnw spotless:apply` **before** opening a PR — a bounced
  pipeline costs one session turn to discover and another to fix. Checkstyle survives in
  `turnbase-sdk` only, for the one rule a formatter cannot check: Javadoc on every public type.
- **No husky, and no git hooks at all.** CI is the gate because it is the only thing that runs on
  every machine and cannot be skipped with `--no-verify`. A pre-commit hook would also start a JVM on
  every agent commit, which here is constantly. If a local fast-fail is ever wanted, the form is a
  single `pre-push` under `core.hooksPath` — not an npm dependency added to a Maven repository.
- **No `-SNAPSHOT` in a committed pom.** It makes the build unreproducible and hides breaking proto
  changes. The local loop is a `-Dturnbase-common.version=…` override: nothing to forget to revert.

### Two traps that are now written down because they fail confusingly

- **JaCoCo wired the obvious way measures unit tests only.** FR-CICD-003 counts unit *and*
  integration, so the two executions need separate exec files merged before a single `check`. It
  fails **open** — the gate passes, reports a number, and nothing ever says it is the wrong number.
- **Naively annotated, forty integration tests start forty PostgreSQL containers** and the PR
  pipeline stops being run. Containers start once per JVM; isolation comes from truncating, not from
  a fresh container.

And one setup trap: `google-java-format` uses internal `javac` APIs, so Spotless needs `--add-exports`
in `.mvn/jvm.config` on JDK 21. The first run without them fails with an `IllegalAccessError` that
reads like a broken toolchain.

### `IMP-M0-03` is no longer a mechanical item

It now establishes the build floor for the largest repository: wrapper, Spotless, JaCoCo, the twelve
empty feature packages and the Modulith verification test. That is deliberate — each of those is
cheapest at skeleton time and close to impossible to retrofit at item forty — but the previous
framing of *"M0-01…05 are mechanical and unblock everything"* is no longer true of M0-03.

### Verification

0 broken relative links across 93 files; every requirement ID cited in the new text exists in the
document it is qualified with; every `§` reference resolves to a real heading; both new files
registered in their nearest `INDEX.md`.

### What is still open — the harness, not the corpus

The review's second half found four gaps in the **Claude Code setup**, and none of them is fixed yet:

1. **No `CLAUDE.md` in any submodule.** All five contain only `README.md`.
2. **No registry status protocol.** All 59 items are seeded `READY`; nothing says who writes
   `WIP`/`DONE` or when. This drifts within three sessions, and then the registry stops being
   trustworthy — which is the one thing it cannot afford.
3. **No escalation format.** `implementation/INDEX.md` says to record a finding "against the item's
   *Gate* field" and nowhere defines what that line looks like.
4. **Permission friction.** `Bash(mvn *)` does not match `./mvnw`, which is the invocation the specs
   actually use; `Bash(git *)` is absent, so every commit prompts; `make e2e` is unallowed.

Plus the proposed skills (`work-item`, `spec-defect`, `corpus-check`, session start/end,
`astryx-component`) and agents (`impl-agent`, `done-when-verifier`, `spec-auditor`). **None created —
proposed only.** That is the next session's work.

---

## Previous Session Summary

**Date:** 2026-08-17 (session 12)

**Adopted [Astryx](https://github.com/facebook/astryx) as the platform's design system**
([ADR-0013](docs/decisions/0013-astryx-design-system.md)) — Meta's open-source library, MIT, 150+
components, React 19+ — superseding `design-system.md`'s in-house seventeen written one day earlier.
Also scanned the local toolchain: **no installs needed.** Node v22.20.0, `.sdkmanrc` pinning
`21.0.2-graalce`, Maven 3.9.11, Docker 29.1.2, **Helm v4** (not 3 — `IMP-M0-08` is written against v4
conventions). `.nvmrc` and `.mcp.json` (the `astryx` docs server) landed with it.

**The substantive change was the aesthetic, not the library.** `theme-neutral` is muted and minimal
where `platform-ui-library.md` had described neon on near-black with frosted glass: FR-TOK-007
withdrawn, FR-TOK-001 loses the neon palette, FR-TOK-005 the frosted glass, and NFR-PERF-002's
`backdrop-filter` clause with it. All five `OQ-*` in `platform-ui-library.md` closed — three
*dropped*, because each asked the platform to decide something Astryx has already decided.

Four rules keep it from drifting, all in `design-system.md`: **exact version pins, no `^`** (Astryx is
Beta at 0.4.3); the **compose → swizzle → write ladder**, stopping at the first rung that works, because
a swizzle is a fork with a nice name; **no wrapper layer** — application code imports
`@astryxdesign/core/Button` directly; and **nothing in this corpus lists Astryx's components** —
lookup is `npm run astryx -- component <Name>` or the MCP server, because a copy is stale within a
release.

**The one trap worth repeating:** `<LinkProvider component={Link}>` must be mounted in the shell.
Without it every Astryx `Link` emits a plain `<a href>` and triggers a full page reload — dropping the
STOMP connection, the room subscription and all in-memory session state. It surfaces as a navigation
bug three milestones from where it was introduced.

---

## Earlier Sessions

**2026-08-16 (session 11) — the corpus became implementation-ready.** Closed all 23
implementation-readiness blockers; completed the registry so that **all 59 live items carry Repo,
Depends on, Read first, Satisfies and Done when** (an audit had found 19 with no body at all); wrote
`docs/requirements/INDEX.md`; named `turnbase.room.spectator-capacity`; then harvested the ten
surviving non-blocking findings and **pruned `docs/` from 30 229 lines to 22 715** by deleting spent
working files — five machine-extracted inventories, the executed remediation plan, thirteen slice and
domain reports.

Four things from it that still bear on Phase 1:

- **A stale inventory is worse than no inventory** — it is exactly the kind of file an agent greps
  into and believes. That, rather than size, is why they went. Working files are deleted once spent,
  not archived.
- **Cite a requirement with the document that *defines* it.** Twelve prefixes genuinely collide;
  checking citations strictly against definitions found **19 mis-qualified** ones. A wrong qualifier
  is worse than a bare ID, and `docs/requirements/INDEX.md` is the lookup.
- **`Gate:` now appears only when something is open**, so its absence means what it says.
- Two mechanical checks are worth reconstructing after any documentation change: every relative link
  resolves, and every requirement citation exists in the document it is qualified with. They are the
  two that found real defects. (Session 13 ran both; both clean.)

**2026-08-15 (session 9) — Phase 0 finished.** 21 new files, ~35 edited: the rest of the data model
(five schema documents, ~30 tables), schema migrations (ADR-0011 + Flyway), system wiring and the
consolidated configuration surface, secrets and JWT key rotation, and eight end-to-end journeys under
`docs/specs/flows/`.

**27 defects, found three distinct ways**, and the pattern is the lesson: the worst were found by
*composing two individually correct documents*. `file-uploads.md` cleared Verified status
unconditionally at activation while `game_official_ownerless_ck` tied `badge='OFFICIAL'` to a null
owner as an equivalence — so **every official upload would abort its activation transaction, and no
official game could ever be updated.** The only path the MVP exercises. Also: unpacking the whole
bundle under a derivable URL **published the backend JAR to anonymous callers**; `PROCESSING` had no
exit, so a validation job that died with its pod permanently burned that version number.

Two process lessons that held: **a constraint that turns silent corruption into a loud failure is
doing its job and will look like the bug** — tightening the badge check is what surfaced the defect,
and the right response was to fix the transition, not loosen the check. And a subagent returning a
bare idle notification is recovered by re-tasking with an explicit file list, explicit scenarios and
an explicit *"an idle notification is not a usable answer"*.

---

## Next Priorities

**Phase 1 has started. Work from [`docs/implementation/INDEX.md`](docs/implementation/INDEX.md), not
from this file.** The registry holds **59 live work items** (IMP-M6-07 is cancelled), each with a
read-list, dependencies, the requirement IDs it satisfies and a done-when clause; this section only
says which of them to pick up.

**No work item is gated.** All 23 readiness blockers are closed, so an item's status is whatever its
own dependencies imply. The registry's gates block records how each one closed rather than what it
blocks, and a `Gate:` line now appears on an item only when one is actually open.

**[`docs/implementation/conventions.md`](docs/implementation/conventions.md) applies to every item and
is not repeated in read-lists** — package layout, Spotless, test suffixes, JaCoCo, branch and commit
format, cross-repo version pinning. Assume it the way you assume `CLAUDE.md`.

### The next session

**Finish the Claude Code setup before writing code.** The corpus is ready; the harness is not, and
every one of the four gaps below gets more expensive once forty items are in flight:

1. **A `CLAUDE.md` per submodule** — all five currently hold only a `README.md`.
2. **A registry status protocol.** 59 items are seeded `READY` and nothing says who writes
   `WIP`/`DONE` or when. Left alone this drifts within three sessions, and a registry nobody trusts
   is worse than no registry.
3. **An escalation format** — `implementation/INDEX.md` says to record a finding "against the item's
   *Gate* field" without defining the line.
4. **Permissions** — `Bash(mvn *)` does not match `./mvnw`; `Bash(git *)` is absent so every commit
   prompts; `make e2e` is unallowed.

Then the skills and agents proposed in session 13: `work-item`, `spec-defect` and `corpus-check`
first; the agents deferred until M0 shows where the cadence actually hurts.

### Then start writing code, at `IMP-M0-01`

1. **IMP-M0-01 through IMP-M0-05** — the five repository skeletons. Four are mechanical and they
   unblock everything. Two carry real content:

   - **`IMP-M0-03` is no longer mechanical.** It establishes the build floor for the repository that
     holds forty of the 59 items: `./mvnw`, Spotless (with the `--add-exports` flags in
     `.mvn/jvm.config`), JaCoCo over merged exec data, the twelve feature packages of
     [ADR-0014](docs/decisions/0014-modular-monolith-spring-modulith.md) §1, and the
     `ApplicationModules.verify()` test. **Root package `io.turnbase.platform`, packaged by feature**
     — getting it wrong is a rename across forty items later.
   - **`IMP-M0-05` installs and wires Astryx** (exact pins, three CSS imports in cascade-layer order,
     `<Theme>` + `<LinkProvider>`, `data-astryx-theme`, self-hosted Figtree) — a skeleton without them
     renders almost-right screens that get corrected one at a time later.
2. **IMP-M0-06 — the Flyway baseline.** The highest-value item in the registry. Transcribing
   `V1__baseline.sql` from the six schema documents is the first mechanical test of whether they are
   mutually consistent. The two hazards the audit named are now **fixed in the documents**:
   `data-model.md` states one auto-increment idiom (`bigint GENERATED ALWAYS AS IDENTITY`), and
   `schema-migrations.md` §5 names one circular foreign key rather than two. **Any further
   disagreement found while transcribing is a
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
- **M6's component library is Astryx, not ours** ([ADR-0013](docs/decisions/0013-astryx-design-system.md)).
  Read that ADR before anything else in M6. `IMP-M6-01` is an integration item — install is already
  done by `IMP-M0-05`, so what remains is the `ui/` boundary and the compose→swizzle→write ladder.
  **Component lookup is a tool call** (`npm run astryx -- component <Name>` or the `astryx` MCP
  server); nothing in this corpus lists them.

- **Every trigger, tag rule and branch protection names `master`**, in every repo. FR-CICD-002/006/007
  said `main` until session 13 and were corrected; a workflow written from the old text never fires.
- **Integration tests are Testcontainers, never compose** (`local-environment.md` §8). Compose belongs
  to the post-merge e2e job alone. The PR job needs a Docker daemon and nothing else.

### Spec hygiene

- **The ID-qualification retrofit** remains outstanding. `docs/specs/INDEX.md` states the rule and it
  holds for new text; the corpus predates it. The highest-traffic collision is `FR-SESS-001…004`,
  defined in both `user-accounts.md` (account sessions) and `platform-architecture.md` (Game Host
  in-memory state); all seven citations resolve correctly by context, so this is a hazard rather than
  a defect. A **wrong** qualifier is worse than a bare ID.
- The `FR-JOB-007a…e` sub-duty convention is declared in `docs/specs/INDEX.md`, and
  `data-model-accounts.md:392`'s wrong FR-INV-002 citation is corrected (session 11).
- **`docs/requirements/INDEX.md` now exists** (IR-25 closed) and carries the twelve genuinely
  colliding prefixes. Use it to resolve a qualifier before writing one — the qualifier names the
  document that **defines** the requirement, never one that merely cites it.
- **`turnbase.room.spectator-capacity`** (IR-24 closed) is in `local-environment.md` §7.1, whose
  title is now *Room lifecycle, capacity and deadlines*. §7 is again true when it claims to hold every
  tunable in the corpus — keep it that way: a property named at a call site and never registered there
  is invisible to the next configuration audit.
- The ten non-blocking findings worth acting on were harvested into the corpus in Part 5 and the
  slice files deleted; the review INDEX records each with where its fix landed. The remaining ~52 were
  NITs and low-value GAPs, and re-deriving one from a fresh audit is cheaper than carrying 3 184 lines
  of stale report against the chance that one mattered.

### Review action plan

`docs/reviews/2026-07-02-mvp-readiness/INDEX.md` — fully worked, **closed**.

`docs/reviews/2026-08-16-implementation-readiness/INDEX.md` — **closed.** 23 of 23 blockers resolved;
each entry carries a `**Closed:**` line. The two follow-on findings raised during remediation (IR-24,
IR-25) are closed too.

**2026-08-20 readiness review (session 13)** — no review directory: seven defects, all closed in the
same session, and the record is this file plus ADR-0014 and `conventions.md`. A round that opens and
closes together does not need an INDEX to track it, and a working file describing it would be spent
on arrival.

**Nothing in the corpus is open.** What is open is the harness — the four gaps under *The next
session*.

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
Flyway, forward-only, backward-compatible), ADR-0012 (polyrepo under an organisation, with
submodules), ADR-0013 (Astryx supersedes the in-house design system), **ADR-0014 (modular monolith,
enforced by Spring Modulith)**.

**Implementation:** `docs/implementation/` — the registry Phase 1 executes from. **59 live work items
across 7 milestones** (IMP-M6-07 cancelled), each carrying a read-list, dependencies, the requirement
IDs it satisfies and a done-when clause. Nothing is gated. Plus **`conventions.md`** (new, session
13): the code and build conventions every item assumes — package layout, Spotless, tests and
coverage, git, cross-repo dependencies, and the per-repo build floor.

**Reviews:** `docs/reviews/` — two closed rounds, reduced to their INDEXes plus
`espresso-spike-results.md`. `2026-08-16-implementation-readiness/INDEX.md` carries all 23 blockers
with evidence and a `Closed:` line each, the ten harvested non-blocking findings, and IR-24/IR-25.
Working files (slice reports, inventories, the remediation plan) were deleted once spent — they had
become pre-remediation snapshots of a corpus that no longer matched them.

**Coverage caveat — now largely closed.** Of the four areas that had requirements but no implementing
specification, three were written this session: the design system
(`platform-frontend/design-system.md`), the room REST API (`api-design/room-rest-api.md`) and
observability (`deployment/observability.md`). The fourth, the onboarding wizard, was **cut from v1**
rather than specified. The table above lists requirement coverage, not design coverage.

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
