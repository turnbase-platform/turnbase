# Implementation Registry — Work Items

Conventions, status vocabulary, the milestone map and the meaning of each field live in
[INDEX.md](INDEX.md). Read that first.

Every item below carries:

- **Repo** — which submodule the work lands in.
- **Depends on** — items that must be `DONE` first.
- **Read first** — the minimum document set that fully determines the item. *An implementation agent
  should not need to read anything outside this list.* If it does, that is a defect in this registry;
  record it.
- **Satisfies** — the requirement IDs the item implements, document-qualified per the rule in
  [`../specs/INDEX.md`](../specs/INDEX.md).
- **Done when** — checkable without judgement.
- **Gate** — present only when a finding is open against the item. No item is gated today.
- **Remaining** — present only while an item is `PARTIAL` (or being continued): what its *Done when*
  clause still lacks. See INDEX.md *Partly done items*.

Paths in *Read first* are relative to the repository root. Closed milestones (M0–M21) are in [`archive/`](archive/); see [INDEX.md](INDEX.md) *Archive*.

**[`conventions.md`](conventions.md) applies to every item and is not repeated in read-lists.**
Package layout, Spotless, test suffixes, JaCoCo, branch and commit format, and cross-repo version
pinning are settled there. Items name it only where they are the item that *establishes* it.

---

## Closed milestones

Every item of these is `DONE` (or `CANCELLED`). Their sections and register rows live in [`archive/`](archive/), verbatim; a session does not read them unless an item's read-list names one.

| Milestone | Items | Archive |
|---|---|---|
| M0 — Bootstrap | 12 | [`archive/M0-bootstrap.md`](archive/M0-bootstrap.md) |
| M1 — Accounts and sessions | 11 | [`archive/M1-accounts-and-sessions.md`](archive/M1-accounts-and-sessions.md) |
| M2 — Rooms and realtime | 12 | [`archive/M2-rooms-and-realtime.md`](archive/M2-rooms-and-realtime.md) |
| M3 — Game execution | 13 | [`archive/M3-game-execution.md`](archive/M3-game-execution.md) |
| M4 — Catalog and upload | 5 | [`archive/M4-catalog-and-upload.md`](archive/M4-catalog-and-upload.md) |
| M5 — History, statistics, notifications | 4 | [`archive/M5-history-statistics-notifications.md`](archive/M5-history-statistics-notifications.md) |
| M6 — Platform frontend | 7 | [`archive/M6-platform-frontend.md`](archive/M6-platform-frontend.md) |
| M7 — MVP review remediation | 13 | [`archive/M7-mvp-review-remediation.md`](archive/M7-mvp-review-remediation.md) |
| M8 — Regression review remediation and MVP view completeness | 18 | [`archive/M8-regression-review-remediation-and-mvp-vi.md`](archive/M8-regression-review-remediation-and-mvp-vi.md) |
| M9 — MVP completeness audit remediation | 11 | [`archive/M9-mvp-completeness-audit-remediation.md`](archive/M9-mvp-completeness-audit-remediation.md) |
| M10 — E2E & security audit remediation | 24 | [`archive/M10-e2e-security-audit-remediation.md`](archive/M10-e2e-security-audit-remediation.md) |
| M11 — Spring Boot 4 migration | 8 | [`archive/M11-spring-boot-4-migration.md`](archive/M11-spring-boot-4-migration.md) |
| M12 — TurnBase visual identity | 11 | [`archive/M12-turnbase-visual-identity.md`](archive/M12-turnbase-visual-identity.md) |
| M13 — Prototype fidelity | 8 | [`archive/M13-prototype-fidelity.md`](archive/M13-prototype-fidelity.md) |
| M14 — Game start resilience | 3 | [`archive/M14-game-start-resilience.md`](archive/M14-game-start-resilience.md) |
| M15 — Load and scalability testing, Phase A | 13 | [`archive/M15-load-and-scalability-testing-phase-a.md`](archive/M15-load-and-scalability-testing-phase-a.md) |
| M16 — Pre-Phase-B fixes | 15 | [`archive/M16-pre-phase-b-fixes.md`](archive/M16-pre-phase-b-fixes.md) |
| M17 — Database capacity | 5 | [`archive/M17-database-capacity.md`](archive/M17-database-capacity.md) |
| M18 — Load testing Phase B: capacity and autoscaling | 17 | [`archive/M18-load-testing-phase-b-capacity-and-autosc.md`](archive/M18-load-testing-phase-b-capacity-and-autosc.md) |
| M19 — The immersive game room | 1 | [`archive/M19-the-immersive-game-room.md`](archive/M19-the-immersive-game-room.md) |
| M20 — Refinement | 22 | [`archive/M20-refinement.md`](archive/M20-refinement.md) |
| M21 — Public release | 12 | [`archive/M21-public-release.md`](archive/M21-public-release.md) |

---

## Register

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|

No milestone is open; the next (M22, cloud deployment, from ADR-0021) is registered here when it is planned.

**244 live items.** `IMP-M21-01…12` were added 2026-11-07 for the public release: licence and licence audit, a privacy and secrets gate, public coordinates and distribution on GitHub, release workflows, the landing page and the engineering story, READMEs and settings, 7WD's decision, the flip, consumers on `0.1.0` and an outside check; see [`archive/M21-public-release.md`](archive/M21-public-release.md). `IMP-M20-01…22` were added 2026-11-04 from the refinement spike ([`../reviews/2026-11-04-refinement-spike/INDEX.md`](../reviews/2026-11-04-refinement-spike/INDEX.md)): the files a session reads first, checked code maps and references, an honest and cheaper build, code and architecture debt, manifest credits; see [`archive/M20-refinement.md`](archive/M20-refinement.md). `IMP-M19-01` (the immersive game room) was added 2026-10-27. `IMP-M18-01…17` were added 2026-10-24 by the Phase B design round ([`load-testing-phase-b.md`](../specs/deployment/load-testing-phase-b.md)): spec groundwork (`01`), capacity on one node with the cores reallocated to PostgreSQL (`02…07`), the Platform scaling out with room affinity and a two-replica minimum (`08…10`), the Game Host spreading, `OQ-5` by measurement and KEDA autoscaling (`11…13`), and the harness and runs (`14…17`); see the M18 section. `IMP-M17-01…05` were added 2026-10-22 from the M16 re-verification, in which the database was the first thing to break (`platform-operations.md` FR-DBQ-*, NFR-DBQ-*): the sweep re-read (`01`), history-independent game-path queries (`02`), an explicit pool size (`03`), the pool size measured (`04`) and the re-verification runs (`05`); see the M17 section. `IMP-M16-01…15` were added 2026-10-19 from the 18 findings of Phase A ([`load-testing.md`](../specs/deployment/load-testing.md) §13): the harness and record corrections (`01`), the Game Host wedge and boot fixes (`02…06`), the platform's room ownership, Redis keys, scans and threads (`07…10`), the subscribe race and the 300 s stall (`11`, `12`), the CPU profile (`13`) and the two re-verification runs (`14`, `15`); see the M16 section. `IMP-M15-01…13` were added 2026-10-18 by the load-testing design ([`load-testing.md`](../specs/deployment/load-testing.md)): the spec groundwork and the four fixes the chart and the platform need before anything can be measured (`01…06`), the k6 harness and its scenarios (`07…10`), and the baseline runs, split into three run items so that none outlasts a session (`11…13`); see the M15 section. `IMP-M14-01…03` were added 2026-10-17 by ADR-0018: a game start that survives a cold, restarting or wedged Game Host and shows its progress; see the M14 section. `IMP-M13-01…08` were added 2026-10-12 after the owner reviewed the running M12 build and found it did not match the approved prototype: see the M13 section. `IMP-M12-01…11` were added 2026-10-11 by [ADR-0017](../decisions/0017-turnbase-visual-identity.md): the approved prototype look replaces the stock Astryx theme across every view while the services, reducers and sockets stay as they are (see the M12 section). Before them, 137 live items. `IMP-M11-01…08` were added 2026-10-10 by [ADR-0016](../decisions/0016-spring-boot-4-migration.md), closing `IMP-GATE-97`: both Spring Boot services move to Boot 4.1.1 because two CRITICAL `spring-webmvc` CVEs have no fix on the 3.5 line. **M11 runs before M10** — every `IMP-M10-*` item depends on `IMP-M11-08` — and its items are judged locally with CI not awaited (see the M11 section). `IMP-M10-01…24` were added 2026-10-10 from the
[E2E & security audit](../reviews/2026-10-10-e2e-security-audit/INDEX.md) (`AUD-01…24`), the first
black-box run of the full stack after the build plan reached 105: two Critical cross-user breaches
(`IMP-M10-01` the ownerless-upload hole closed by `IMP-GATE-96`, `IMP-M10-02` the wildcard-subscribe
queue leak), six High (auth-control bypasses, the public-edge gRPC reachability, the chunked-body
limit, and the cold-start Game Host wedge), seven Medium and nine Low/Info hardening and polish items.
One finding (join-by-code vs. visibility) was reproduced and confirmed **as specified** — no item. `IMP-M9-01…11` were added 2026-10-04 from the [MVP completeness audit](../reviews/2026-10-04-mvp-completeness-audit/INDEX.md) (`CA-01…CA-10`): the invite-friends control and the `owner` filter the MVP still lacks, the reference game's missing outcome, the clipped catalog action, the late forfeit dispatch, the settings gaps, one spec decision, polish, and the suite that pins them. `IMP-M8-01…16` were added 2026-10-03 from the [MVP regression review](../reviews/2026-10-03-mvp-regression-review/INDEX.md): five close its backend and game findings, nine give every MVP view a minimal working UI (the game room is `IMP-M8-10`), and the last two close the client follow-up and re-run the review as a suite. `IMP-M7-01…13` were added 2026-10-01 from the [MVP implementation review](../reviews/2026-10-01-mvp-implementation-review/INDEX.md): the first four close its MR-01 (the room views `IMP-M6-04`/`05` did not build), the rest close MR-02…MR-11 and add the acceptance suite the review was run by hand. IMP-M6-07 is cancelled: IR-23 cut the onboarding wizard from v1, so
`onboarding-wizard.md`'s FR-ONB-* and NFR-ONB-* have no implementing item by design. The heading is
kept below so the number is never reused. `IMP-M3-12` was added 2026-08-22, closing IMP-GATE-05 — see
its section under M3. `IMP-M3-13` was added 2026-09-30, closing IMP-GATE-91 — see its section under M3. `IMP-M1-10` was added 2026-09-06, closing IMP-GATE-26, and `IMP-M1-11` on
2026-09-26, closing IMP-GATE-78 — see their sections under M1.

Statuses are seeded as `READY`. **No item is gated** — the 2026-08-16 audit's 23 blockers are all
closed (see *Readiness gates* at the end for what each fix changed). An item's real status is
whatever its own *Depends on* implies.

---

## Readiness gates

Populated from
[`../reviews/2026-08-16-implementation-readiness/INDEX.md`](../reviews/2026-08-16-implementation-readiness/INDEX.md).

<!-- GATES:BEGIN -->
The 2026-08-16 readiness audit returned **23 blockers. All 23 are now closed** — see
[`../reviews/2026-08-16-implementation-readiness/INDEX.md`](../reviews/2026-08-16-implementation-readiness/INDEX.md)
for the register, where each entry carries the evidence and a `**Closed:**` line naming the
resolution.

**Every work item in the register above is ungated.** Status reverts to whatever the item's own
dependencies imply. The table below is a record of what changed, not an overlay to consult before
starting work — each fix is already carried by the item it affects.

| Gate | Closed by | What changed |
|---|---|---|
| IR-01 | `local-environment.md` §1, §5, §7.9 | Bucket named `turnbase-bundles`, created by a one-shot `minio/mc` init step. The application asserts its existence and never creates it |
| IR-02 | `secrets-and-configuration.md` §1, §4; `local-environment.md` §4, §7.9 | Two roles created by `deploy/compose/initdb/01-roles.sql`. `POSTGRES_USER` is `turnbase_owner`, not `turnbase_app` — naming the app role there would silently hand it superuser |
| IR-03 | `platform-operations.md` FR-CICD-003, OQ-002 | Coverage gate narrowed to unit + integration, the two categories that run at PR time |
| IR-04 | **new** `deployment/observability.md` | Full wiring: Actuator scrape, Logback JSON → Promtail → Loki, OTLP → Tempo, Grafana provisioning, Alertmanager rules. Promtail chosen over the Loki Docker driver because a plugin install is a step a clean-machine bootstrap cannot assume |
| IR-05 | `platform-views.md` VW-PROF-002…003, VW-FREN | The owner is exempt from their own privacy settings, stated as a rule and applied to five conditions |
| IR-06 | `room-lifecycle.md` §3.3 | The outbox insert is conditional on `active_session_id IS NOT NULL`, the same trigger step 4's Lobby exemption already used |
| IR-07 | `room-lifecycle.md` §1.5 layer 3, §1.6 | Drain- and self-eviction-initiated socket closes are tagged; the disconnect handler skips them |
| IR-08 | `room-chat-websocket.md`, `room-websocket.md` | Chat carries `version: null` and never advances the counter. No second sequence: FR-MSG-006 defines a missed message as lost, not as a gap |
| IR-09 | `room-lifecycle.md` §3.2, §5.1 duty 2; `data-model.md` §2, §5 | Two halves — `lost_announced_at` is stamped by every inline path, and duty 2 is additionally narrowed on `leave_reason` as a backstop. New partial index `room_participant_unannounced_idx` |
| IR-10 | `room-lifecycle.md` §4 | `detachSession` step 3 is a fenced, version-bumping `UPDATE`. Without the fence a stale owner closes a live room; without the bump every client discards the `ROOM_CLOSED` |
| IR-11 | `room-lifecycle.md` §4, §5.1 duty 2; `data-model-accounts.md` §5 | **No new table.** Owed closure rides the existing deferred tail; duty 2 gains the host disposition. The erasure transaction writes participant departures only |
| IR-12 | `room-websocket.md`, `room-lifecycle.md` §3.3, `data-model.md` §6, `manifest-schema.md`, `game-rooms.md`, `game-contracts.md` OQ-002 | Wire kept, schema deferred, **v1 behaviour declared**: `aiPlayers` always empty, `ADD_AI_PLAYER` always `AI_NOT_SUPPORTED`, `capabilities.ai: true` rejected at validation, the "not an AI" clause removed |
| IR-13 | **new** `api-design/room-rest-api.md` | Five endpoints: create, list, get, join, leave. REST is membership only; every in-room mutation stays STOMP |
| IR-14 | `flows/02-room-to-game-start.md` step 6; `game-host-internals.md` §9.1 | `session:{id}` has exactly one writer, the Game Host. Flow 02 names the keys Orchestration does write |
| IR-15 | `game-host-internals.md` §8.1, §9.1; `orchestration-gamehost-protocol.md` | The session record gains `lastOutcome` and `lastFailure`, so a replayed burned sequence returns its own failure rather than the previous input's effects |
| IR-16 | `gamehost.proto` service and field comments; protocol doc | Forward gaps are normal and must be accepted. All three sequence cases are stated at the field, because a codegen reader never sees the prose table |
| IR-17 | `api-design/websocket.md` § `GAME_EVENT`; `game-contracts.md` NFR-SEC-002 | Every effect address is validated against the producing session's membership at fan-out. The per-user queue secures the subscription, not the address |
| IR-18 | `manifest-schema.md`, `file-uploads.md`, `flows/08-upload-to-play.md` | Phase A is a synchronous `422`; everything after `confirm` is the version resource's `FAILED` state |
| IR-19 | `api-design/input-validation.md`; `game-catalog.md` | Assigned an owner. Markdown → React elements client-side, no HTML string anywhere, so the `dangerouslySetInnerHTML` ban stands unweakened |
| IR-20 | `platform-operations.md` FR-JOB-013; `local-environment.md` §7.2; both schema docs | The expiry purge job exists and is named. It is the only mechanism that ever removes an actionable notification |
| IR-21 | `shell-architecture.md` §5; `game-asset-serving.md` §6.1 | `allow-scripts allow-same-origin`, owned by `game-asset-serving.md`. `allow-scripts` alone makes `event.origin` `"null"` and silently breaks the whole relay |
| IR-22 | `shell-architecture.md` §6 *(new section)* | The platform origin's CSP, with `frame-src` still owned by `game-asset-serving.md` §6.3. The delegation now resolves |
| IR-23 | **new** `platform-frontend/design-system.md`; `onboarding-wizard.md` | Design system specified and folded into `turnbase-frontend` (CON-002 amended); onboarding wizard **cut from v1** — IMP-M6-07 is cancelled |

### Two resolutions that departed from the review's own suggestion

Recorded here because a future reader will otherwise reopen them.

- **IR-11 uses the existing deferred-tail mechanism rather than a new owed-closure table.** §5.1 duty
  2 already performs exactly this job for grace expiries resolved by a foreign instance, and a
  closure owed by an account deletion is the same shape of debt. ADR-0010's lesson is about keying
  such tables correctly, not about minting more of them.
- **IR-12 declares the v1 behaviour of the AI wire surface** rather than adding a schema
  representation or cutting `FR-HOST-003`. The protocol shape survives for when the AI interface
  lands; the implementer gets an unambiguous instruction today.

**IR-09's fix has two halves and Task 11 depended on the first** — that dependency is not visible
from either document, which is why it is written down here.
<!-- GATES:END -->

### Raised during remediation — both closed

| ID | What | Resolution |
|---|---|---|
| ~~IR-24~~ | ~~`game-rooms.md` NFR-SPEC-001 requires spectator capacity to be configurable, and no property name is assigned~~ | **Closed.** `turnbase.room.spectator-capacity`, default `8`, in `local-environment.md` §7.1 and named at all four call sites |
| ~~IR-25~~ | ~~`docs/requirements/` has no `INDEX.md`~~ | **Closed.** [`../requirements/INDEX.md`](../requirements/INDEX.md) lists all seventeen documents and the requirement prefixes each one *defines* — use it to resolve a qualifier before citing one |

**No review finding is open anywhere in the corpus**, and since ADR-0013 no `OQ-*` in
`platform-ui-library.md` is open either — three were dropped rather than answered, because Astryx had
already made the visual decisions they were asking the platform to make.

**On the *Satisfies* qualifiers above.** Each names the document that **defines** the requirement, not
one that merely cites it. The two are easy to confuse: `game-history.md` discusses `FR-RET-003` at
length, but `platform-operations.md` defines it. Nineteen citations in this corpus had it the wrong
way round and were corrected; `../requirements/INDEX.md` is the lookup that prevents the next one.
