## Last Session Summary

**Date:** 2026-10-31 (session 256) — **`IMP-M18-15` DONE.** 206 of 209 items done. Umbrella only (reports, SUMMARY); both Platform and Game Host images rebuilt first.

- **`ramp-to-break` scaled** (`loadtest/reports/2026-10-31-m18-scaled-ramp-to-break.md`): ceiling **170 pairs** against 220 single-instance, so **NFR-ASC-006 is not met**. The abort at 180 is `tb_game_start{cold:false}` p95 2.1 s on a Game Host the autoscaler had just added (cold Espresso boot; the harness tags cold by time, not by host); move, create, join and Hikari were healthy. The Game Host flapped during the ramp (out +1,398 s, in +1,622 s, out +1,678 s: the KEDA trigger is a spiky point maximum) and step 170 lost 28% of its games. The busiest Platform pod sat at its 1.5 CPU limit from step 60 at the HPA maximum of 3.
- **`spike`** (`…-m18-spike.md`, `CEILING=170`): 17 to 170 pairs in 30 s, 10 min hold: every threshold passes, third Game Host Ready 142 s after the rise (NFR-ASC-001), `CORRECTNESS: PASS`, but the Game Host scaled in again mid-hold. The Platform went to 3 replicas on the setup's login burst, so its reaction to the spike is not measured.
- Harness notes: `correctness.sh` reports `FAIL games` after an aborted `ramp-to-break` (138 interrupted games are neither completed nor abandoned); the warm-up smokes leave the Platform at 3 replicas, so wait for 2 before a run; `run.sh start` fails its preflight while a pod is Terminating.

## Next Priorities

**M18: `IMP-M18-01`…`15` are done; next `16` (failover, up-down, diurnal; use the flapping and 170-pair ceiling findings of `15`) (Track 1 is complete; `09` is first of Track 2). Next, Tracks 2 (`10`) and 3 (`11…13`) may interleave with it once `01` is done; Track 4 (`14…17`) last. The design is `docs/specs/deployment/load-testing-phase-b.md`; the milestone introduction in the registry carries the live-item rules.

- The proposed `NFR-ASC` targets are the orchestrator's; the owner may adjust them before `01` writes them down.
- Still owner-held: `game-host-internals.md` §18 `OQ-6` (twelve Espresso contexts per JVM lifetime), not reached by Phase B's single-title scenarios.

**[`docs/implementation/conventions.md`](docs/implementation/conventions.md) applies to every item and
is not repeated in read-lists** — package layout, static analysis, Spotless, test suffixes, JaCoCo,
branch and commit format, cross-repo version pinning. Assume it the way you assume `CLAUDE.md`.

**The harness is done.** Submodule `CLAUDE.md` files, the corpus checker, the status protocol, the
escalation format, the two skills and the permissions all landed in session 13, and sessions 14 and
15 proved them on real items: the `work-item` cadence held both times, `spec-defect` fired three
times on `IMP-M0-01` and twice on `IMP-M0-02`, and the `pre-push` hooks now run in two repositories.

### `turnbase-sdk` is a second worked example, narrower than `turnbase-common`

It adds two things `turnbase-common`'s pom didn't need: **Checkstyle** (bound at `validate`
alongside Spotless, public-type Javadoc only — the one repository that runs it) and an enforcer
**`bannedDependencies`** rule (`turnbase-grpc`/`turnbase-game-host` banned at every scope). Both are
mechanical answers to `turnbase-sdk/CLAUDE.md`'s two repo-specific rules, and both were verified to
actually fire against a deliberate violation before being trusted.

**`typescript` is pinned to `6.0.3`, not the latest `7.0.2`** — `typescript-eslint@8.67.0`'s peer
range is `<6.1.0`; `npm install` fails `ERESOLVE` otherwise. Not in `conventions.md` because it is a
toolchain fact rather than a project decision, but worth knowing before `IMP-M0-05`
(`turnbase-frontend`) or `IMP-M3-12` pin `typescript` again.

### The next session — `M0-04` is done; `M0-05`, `M0-06`, and `IMP-M3-12` are on the board

**`IMP-M0-04` is `DONE`.** `turnbase-common`, `turnbase-platform` and `turnbase-game-host` are now
three worked examples of the bootstrap-window mechanics (Spotless at `validate`, Error Prone +
NullAway, merged JaCoCo, the enforcer, the `.mvn/jvm.config` flags, and the `TURNBASE_COMMON_PAT`
bootstrap install — one secret per bootstrap-window consumer repo, never shared). `IMP-M0-05`
(frontend skeleton) has no such dependency and is a clean start by comparison.

Things `IMP-M0-01`/`M0-03` learned that `IMP-M0-04` met on its own first push too, all in
`conventions.md` §6:

| | |
|---|---|
| GraalVM CE | `graalvm/setup-graalvm`, **not** `actions/setup-java`, which has no `graalvm-community` distribution |
| `buf breaking` | pull requests only, against the base branch — a push has no reliable baseline |
| Dependabot | opens PRs within a minute of the first push; land `ignore` entries **with** a deliberate pin, and expect every PR to fail CI on the bootstrap secret regardless of content until `IMP-M0-11` |
| Line endings | `.gitattributes` pins `*.sh`, hooks and `mvnw` to LF, or a CRLF checkout makes git silently refuse to run a hook |
| Dependabot `ignore` dependency-name | **verify the entry actually matches** — a docker `dependency-name` never includes the registry host (`ghcr.io/…` doesn't match; the bare image name does), found the hard way by `IMP-M0-04`'s own first `dependabot.yml` |

**A dependency pinned as "the exact build a spike verified" (Espresso here; Astryx for `IMP-M0-05`)
needs an `ignore` entry with no version floor at all**, not a `>=<major>` range — a patch bump is still
a different build than the one that was verified, and only a version-range-shaped rule looks like it
covers that until the first Dependabot PR proves otherwise.

**`IMP-M3-12` (FE GDK client, `turnbase-sdk`) is now `READY`**, unblocked by `IMP-M0-02`. It's a
candidate for the same session as `M0-05`/`M0-06` if there's room: `frontend-gdk-api.md` is already
read in full for `IMP-M0-02`, and the declared types it needs (`Role`, `Player`, `Team`,
`InitContext`, the envelope) already exist in `src/main/ts/types.ts`.

**`IMP-M0-05` installs and wires Astryx** (exact pins, three CSS imports in cascade-layer order,
`<Theme>` + `<LinkProvider>`, `data-astryx-theme`, self-hosted Figtree) — a skeleton without them
renders almost-right screens that get corrected one at a time later. Its lint stack is pinned in
`conventions.md` §2, not left to `npm create vite`.

**Then, still in setup:** `IMP-M0-11` wires the CI workflows — every trigger on `master`,
Testcontainers with no compose in the PR job, and FR-CICD-010's Dependabot and Trivy as committed
configuration rather than a mention.

### Then the substantive M0 items

1. **IMP-M0-06 — the Flyway baseline.** The highest-value item in the registry. Transcribing
   `V1__baseline.sql` from the six schema documents is the first mechanical test of whether they are
   mutually consistent. The two hazards the audit named are now **fixed in the documents**:
   `data-model.md` states one auto-increment idiom (`bigint GENERATED ALWAYS AS IDENTITY`), and
   `schema-migrations.md` §5 names one circular foreign key rather than two. **Any further
   disagreement found while transcribing is a
   specification defect — fix the document, then the SQL.** Do not reconcile silently in the
   migration.

   Two schema changes from this session must land in the baseline:
   `room_participant_unannounced_idx` (IR-09) and nothing else — IR-11 deliberately added no table.

2. **IMP-M0-07 — the compose stack.** IR-01 and IR-02 are closed, so this is now buildable end to
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
same session, and the record is this file plus ADR-0014, ADR-0015 and `conventions.md`. A round that
opens and closes together does not need an INDEX to track it, and a working file describing it would
be spent on arrival.

**Nothing is open in the corpus, and nothing is open in the harness.** The next work is `IMP-M0-01`.

Two things are deferred rather than done, both deliberately:

- **The three proposed agents** (`impl-agent`, `done-when-verifier`, `spec-auditor`) wait until M0
  shows where the cadence actually hurts. Guessing their shape now costs more than waiting.
**`work-item` and `spec-defect` have now had their first real outing** and both held on `IMP-M0-01`.
`spec-defect` fired three times on one item; `work-item`'s "a green local build is not `DONE`" rule
is what kept the item at `WIP` until CI actually ran — and CI then failed in both jobs, which is the
best possible argument for the rule. Neither skill needed an edit. The one thing to watch on the next
item is whether three gates in one item makes the escalation feel routine enough to start skipping.

**Permissions are settled.** The Astryx and Playwright prefixes were corrected in session 13, and
session 14 added `git push` **without any force variant** — `--force`, `--force-with-lease`,
`--mirror`, `--delete`, `--prune`, `--tags` and `+refspec` stay denied, and a `v*.*.*` tag push stays
a human action because ADR-0012 makes it the release trigger.

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
enforced by Spring Modulith)**, **ADR-0015 (static analysis — Error Prone and NullAway, at skeleton
time)**.

**Implementation:** `docs/implementation/` — the registry Phase 1 executes from. **61 live work items
across 7 milestones** (IMP-M6-07 cancelled; `IMP-M3-12` added session 15; `IMP-M1-10` added session 29),
each carrying a
read-list, dependencies, the requirement IDs it satisfies and a done-when clause. Nothing is gated.
Plus **`conventions.md`** (new, session 13): the code and build conventions every item assumes —
package layout, Spotless, tests and coverage, git, cross-repo dependencies, and the per-repo build
floor.

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
