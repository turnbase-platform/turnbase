# Refinement Spike — 2026-11-04

A wide pre-milestone review taken after the register reached 209 of 209 and before the repositories go
public. It asks what the next milestone of refinement should hold, read from four directions: **code,
documentation, architecture, and how well Claude can work in the codebase**, plus whether the tests
earn the CI and local time they cost. The audiences are potential employers, TurnBase game designers,
friends, and the owner as the future maintainer.

Method: measurement over every repository (sizes, test reports, CI run history and step timings,
history scans, reference checks), sampling where measurement pointed. It is a spike, not an audit:
breadth first, and every finding says how deep it went.

## Verdict

> **The base is sound and well specified; what needs work is cost, legibility and release hygiene, not
> correctness.** The corpus checker is clean, the history holds no secret pattern, only 2 of 680
> platform test methods lack an assertion, and there is no TODO/FIXME in any source tree. But CI is not
> running at all on most repositories, the platform's integration suite boots Spring once per test
> method, nothing in the organisation tells a stranger what TurnBase is or how it was built, and the
> context every Claude session loads first is partly months out of date.

## Findings

Disposition: **M20** = a refinement item (the milestone was first drafted as M19, which the immersive game room had taken); **REL** = the public-release milestone; **OWNER** = needs a
decision before it can be planned; **C** = Phase C (load and scaling), not refinement.

### A. Release readiness

| # | Finding | Evidence | Disposition |
|---|---|---|---|
| RS-01 | No `LICENSE` in any repository; the umbrella has no `README.md` although `CLAUDE.md` calls it the landing page | `ls` over all eight repositories | OWNER (licence) → REL |
| RS-02 | `turnbase-game-7wonders-duel` implements a commercial, trademarked board game in full, with its rules transcribed under `docs/rules/`; its `INFO.md` says "Skeleton" while the `README.md` says the base game is complete | `README.md`, `INFO.md`, `docs/rules/` | OWNER — release blocker |
| RS-03 | Repository metadata is stale or empty: `turnbase-platform`'s GitHub description says "Spring Boot 3.5+", no repository has topics, `turnbase-frontend/README.md` is 3 lines | `gh repo view` | REL |
| RS-04 | No secret pattern in any repository's full history (AWS, GitHub PAT, private key, Slack, Anthropic); `values-local.secrets.yaml` and `.secrets/` are gitignored. A real scanner (gitleaks) has not been run | `git log --all -p` grep | REL (gitleaks gate before the visibility flip) |
| RS-05 | Platform main code carries 195 `IMP-*` work-item references in 83 files (game-host 30, frontend 5), and commit subjects carry session numbers. Meaningful only with the umbrella open beside it | grep over `src/main` | OWNER (keep as provenance or replace with spec references) |
| RS-06 | The story an employer should read — spec-first, 20 ADRs, the `work-item`/`spec-defect` loop, measured load-test evidence, 258 agent sessions — is not told anywhere public; it lives in `CLAUDE.md`, `STATUS.md` and the registry | — | REL |

### B. CI health and cost

| # | Finding | Evidence | Disposition |
|---|---|---|---|
| RS-07 | **CI is not running.** The latest `master` runs of `turnbase-common`, `turnbase-sdk`, `turnbase-game-host` (and three of the last four of `turnbase-platform`) were refused by GitHub: "recent account payments have failed or your spending limit needs to be increased". Real failures: `turnbase-frontend` (Trivy image gate: CRITICAL CVE-2026-111497 in `brotli-libs`, HIGH in `curl`, base image), `turnbase-game-7wonders-duel` (no token for the SDK bootstrap checkout, every run since it was created) | `gh run list/view` | OWNER (billing) + M20 |
| RS-08 | The umbrella pins submodule commits CI never verified (`turnbase-common` 8b6d68b, `turnbase-game-host` 88173cb, `turnbase-sdk` 068174d), against `CLAUDE.md`'s own rule; `turnbase-platform` has a newer green commit (60e7489) that is not pinned | `git submodule status` vs run history | M20 |
| RS-09 | **The platform integration suite is the biggest single cost.** 44 IT classes start `TurnBaseApplication` by hand, none uses `@SpringBootTest`, so there is no test-context cache; most do it in `@BeforeEach`, i.e. one Spring boot per test method. Containers are `@Container static` per class (53 restarts of Postgres + MinIO + Redis). Failsafe 812 s of the 1,206 s `Verify` step; whole platform job 24 min | failsafe reports; `GameAssetControllerIT` 98 s for 6 tests, `NotificationControllerIT` 101 s for 13 (three SSE tests at ~30 s each) | M20 (several items, one per test family) |
| RS-10 | Benchmarks and timing tests run in the default build: `EngineSharingBenchmarkIT` 28 s, `ConcurrentBootsIT` 48 s, `GameBridgeClientEspressoTest` 62 s in the *unit* phase, `HostWedgeTest` 17 s, `LoginServiceTimingTest`, `GamePathQueryCostIT`, `ThreadBoundsIT` | surefire/failsafe reports | M20 (a `perf` tag/profile, run on demand or nightly) |
| RS-11 | Every Trivy target is scanned twice (report, then gate): about 5 of game-host's 21 minutes | step timings | M20 |
| RS-12 | Every consumer build installs `turnbase-common`/`turnbase-sdk` from source with a per-repo PAT (~45 s each, plus the secret that 7wonders lacks) | step timings, `conventions.md` §5 | REL (publish the artifacts once public) |

**Test relevance, as far as the spike went.** The heuristic pass found tests that assert things, not
empty tests (2/680 platform methods without an assertion, 0/111 in game-host), and no test reads the
specification at run time. The question it could not settle is **overlap**: the platform has 53 ITs
over 25k lines of test code, and several families (`RoomControllerIT`, `RoomCommandControllerIT`,
`WebSocketIT`, `TwoInstanceIT`) look as if they drive the same paths through the same full boot. That
needs a per-module pass mapping each IT to the requirement it protects, and is an M20 item, not a
spike result.

### C. Code and architecture

| # | Finding | Evidence | Disposition |
|---|---|---|---|
| RS-13 | `RoomRepository.java` is 3,242 lines, 12% of the platform's main code; the next largest class is 719 | `wc -l` | M20 (split by concern, behaviour unchanged) |
| RS-14 | Code cites specifications 720 times by file name and 796 times by `§`. Seven file references dangle (platform: `game-path-query-cost.md`, `lifecycle.md`, `m18-reassignment-results.md`, `2026-10-29-m18-reassignment.md`; frontend: `astryx-button.md`, `astryx-selector.md`, `astryx-text-input.md`); `§` references in code are not checked at all | reference extraction vs the corpus | M20 (extend `check-corpus.py` to submodule sources) |
| RS-15 | 33 open questions (`OQ-*`) across the specifications besides `OQ-6`; some are years of design debt in miniature (`rate-limiting.md` OQ-002 per-pod budgets now matters at 2-3 replicas) | grep over `docs/specs` | M20 (triage: close, decide, or move to one backlog) |
| RS-16 | `game-host-internals.md` §18 `OQ-6` — twelve Espresso contexts per JVM lifetime — bounds how long a Game Host can live; it is base stability, not load work | §18 | M20 (investigate and decide) |
| RS-17 | Carried from Phase B: platform threads 129 → 172 at the end of the `sustained-high` hold, unexplained; `SUMMARY.md` still calls the OpenTelemetry choice "pending" though the report records it | `SUMMARY.md`, `2026-10-24-m18-otel.md` | M20 (thread growth is locally reproducible; the line is a fix-now) |
| RS-18 | Game Host cold start and flapping (NFR-ASC-006), game loss on a Game Host SIGKILL (NFR-ASC-002/007, FR-ASC-004), standby warm-up, scale-in under a daily shape | `SUMMARY.md` *What Phase C starts from* | C |

### D. Documentation and Claude's effectiveness

| # | Finding | Evidence | Disposition |
|---|---|---|---|
| RS-19 | **Claude's auto-memory for this project is wrong**: Java 25, React 18, "Phase 0 — requirements", "prioritise spec work until the user signals readiness". Loaded into every session ahead of `CLAUDE.md` | `~/.claude/projects/…/memory/` | fix now |
| RS-20 | `STATUS.md` is 260 lines; after the first ~25, it is August guidance ("the next session — M0-04 is done", M0-06 Flyway hazards). The durable lessons in it belong in `conventions.md` or a submodule `CLAUDE.md` | read | M20 |
| RS-21 | `CLAUDE.md` *Current Phase* is one ~900-character sentence of milestone history, loaded every session; it should state the present in three lines and link the registry | read | M20 |
| RS-22 | `registry.md` is 9,026 lines, ~95% of it closed milestones. An agent working an item reads its section, but every search and every "what is open" question pays for the whole history | `wc -l` | OWNER (split per milestone, closed ones collapsed) |
| RS-23 | **There is no code map.** The submodule `CLAUDE.md` files say what the rules and traps are, not where things live; the move path (frontend → STOMP → platform → gRPC → Game Host → Espresso) has to be re-derived by grep each session. One `ARCHITECTURE.md` per service, flows mapped to classes, serves Claude and a human reader equally | read | M20 |
| RS-24 | Tooling: `.claude/settings.json` is a 15 KB permission list; no language server is configured although the harness supports one; the test-cost measurement this spike did by hand is not a script | read | M20 (`scripts/test-cost.sh`; LSP evaluated) |

## Questions for the owner

1. **`turnbase-game-7wonders-duel`** (RS-02): keep it private and out of the public organisation, or
   rework it into an original game with its own name and rules?
2. **Licence** (RS-01): one licence for all, or a permissive one for the SDK and games and another for
   the platform?
3. **Provenance in code** (RS-05): keep `IMP-*` references and session numbers as visible evidence of
   the agent workflow, or replace them with specification references?
4. **CI billing** (RS-07): restore it now, or wait for the public flip (public repositories run free)?
   Until one happens, M20 items can only be verified locally.
5. **Registry** (RS-22): split per milestone?

## Owner's answers (2026-11-04)

- **Open source, all repositories.** A game that implements an existing one must credit its original
  authors. RS-02 becomes an attribution item: *7 Wonders Duel* — designed by Antoine Bauza and Bruno
  Cathala, art by Miguel Coimbra, published by Repos Production, 2015 — credited in the game's
  `README.md`, `INFO.md` and manifest, and the `INFO.md`/`README.md` status contradiction fixed. The
  repository holds no original art and no rulebook PDF (checked); `docs/rules/` paraphrases the
  rulebooks. The owner will write to Repos Production for permission. Attribution credits the authors
  but does not license the name or the rules text, so the reply decides whether the game ships under
  this name.
- **The registry and the Claude-critical files** (`CLAUDE.md`, `STATUS.md`, memory, skills): most of
  the content is archived so that a session does not read it. RS-19 to RS-22 are in M20.
- **`IMP-*` references in code** stay, as provenance (RS-05 closed, no item).
- **Credits go in the manifest** and the platform shows them (M20-21).
- **7WD decision** (RS-02, 2026-11-08): the owner decided to publish `turnbase-game-7wonders-duel` without a reply
  from Repos Production, because it uses no original art. `NOTICE` and an unofficial-implementation disclaimer
  were added; the repository is public (`IMP-M21-09`). The name and rules text are not licensed by this.
- **Licence** (RS-01, answered 2026-11-07): **Apache-2.0 for every repository**, games and SDK included.
  For `turnbase-game-7wonders-duel` it covers the code only; the game's name and rules stay Repos
  Production's.
- **Release** means a proper cloud CI/CD setup (AWS or another provider), not only flipping visibility.
  It needs its own spec and ADR.

## Proposed shape

- **M20 — Refinement** (M19 is the immersive game room): RS-07 (the code half), 08, 09, 10, 11, 13, 14, 15, 16, 17, 20, 21, 23, 24, and
  the IT-overlap pass. Each item small, verified locally: a test count unchanged, a measured time, a
  checker clean, a grep empty.
- **M21 — Public release**: RS-01, 03, 04, 06, 12, and the visibility flip.
- **M22 — Deployment**, then **Phase C** (RS-18).

Fixed during the spike: none — this round only measures. RS-19 (the auto-memory) was corrected when M20
was registered; the `SUMMARY.md` line is `IMP-M20-22`.

**Registered 2026-11-04** as `IMP-M20-01…22` in [`registry.md`](../../implementation/registry.md); the
design document the owner approved was deleted once its items were registered, its content now in the
M20 section.
