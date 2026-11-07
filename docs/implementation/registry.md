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

Paths in *Read first* are relative to the repository root. Closed milestones (M0–M20) are in [`archive/`](archive/); see [INDEX.md](INDEX.md) *Archive*.

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

---

## Register

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M21-01 | Apache-2.0 in every repository | all | — | DONE |
| IMP-M21-02 | Third-party licence audit | common, sdk, platform, game-host, frontend, tictactoe, 7WD | M21-01 | DONE |
| IMP-M21-03 | Pre-flip privacy and secrets gate | all | — | READY |
| IMP-M21-04 | Coordinates and distribution, spec first | docs, then all with a pom or GDK dependency | — | READY |
| IMP-M21-05 | Release workflows on GitHub | common, sdk | M21-01, M21-04 | READY |
| IMP-M21-06 | The umbrella README | docs | M21-01 | READY |
| IMP-M21-07 | How it was built | docs | — | READY |
| IMP-M21-08 | Component READMEs, community files and repository settings | all, `.github` | M21-06 | READY |
| IMP-M21-09 | 7WD release decision | 7WD, docs | publisher's reply | BLOCKED |
| IMP-M21-10 | The flip | all, org | M21-01…08 | READY |
| IMP-M21-11 | Consumers on `0.1.0`, every secret gone | platform, game-host, tictactoe, 7WD | M21-10 | READY |
| IMP-M21-12 | Verified from the outside | all public | M21-11 | READY |

**244 live items.** `IMP-M21-01…12` were added 2026-11-07 for the public release: licence and licence audit, a privacy and secrets gate, public coordinates and distribution on GitHub, release workflows, the landing page and the engineering story, READMEs and settings, 7WD's decision, the flip, consumers on `0.1.0` and an outside check; see the M21 section. `IMP-M20-01…22` were added 2026-11-04 from the refinement spike ([`../reviews/2026-11-04-refinement-spike/INDEX.md`](../reviews/2026-11-04-refinement-spike/INDEX.md)): the files a session reads first, checked code maps and references, an honest and cheaper build, code and architecture debt, manifest credits; see [`archive/M20-refinement.md`](archive/M20-refinement.md). `IMP-M19-01` (the immersive game room) was added 2026-10-27. `IMP-M18-01…17` were added 2026-10-24 by the Phase B design round ([`load-testing-phase-b.md`](../specs/deployment/load-testing-phase-b.md)): spec groundwork (`01`), capacity on one node with the cores reallocated to PostgreSQL (`02…07`), the Platform scaling out with room affinity and a two-replica minimum (`08…10`), the Game Host spreading, `OQ-5` by measurement and KEDA autoscaling (`11…13`), and the harness and runs (`14…17`); see the M18 section. `IMP-M17-01…05` were added 2026-10-22 from the M16 re-verification, in which the database was the first thing to break (`platform-operations.md` FR-DBQ-*, NFR-DBQ-*): the sweep re-read (`01`), history-independent game-path queries (`02`), an explicit pool size (`03`), the pool size measured (`04`) and the re-verification runs (`05`); see the M17 section. `IMP-M16-01…15` were added 2026-10-19 from the 18 findings of Phase A ([`load-testing.md`](../specs/deployment/load-testing.md) §13): the harness and record corrections (`01`), the Game Host wedge and boot fixes (`02…06`), the platform's room ownership, Redis keys, scans and threads (`07…10`), the subscribe race and the 300 s stall (`11`, `12`), the CPU profile (`13`) and the two re-verification runs (`14`, `15`); see the M16 section. `IMP-M15-01…13` were added 2026-10-18 by the load-testing design ([`load-testing.md`](../specs/deployment/load-testing.md)): the spec groundwork and the four fixes the chart and the platform need before anything can be measured (`01…06`), the k6 harness and its scenarios (`07…10`), and the baseline runs, split into three run items so that none outlasts a session (`11…13`); see the M15 section. `IMP-M14-01…03` were added 2026-10-17 by ADR-0018: a game start that survives a cold, restarting or wedged Game Host and shows its progress; see the M14 section. `IMP-M13-01…08` were added 2026-10-12 after the owner reviewed the running M12 build and found it did not match the approved prototype: see the M13 section. `IMP-M12-01…11` were added 2026-10-11 by [ADR-0017](../decisions/0017-turnbase-visual-identity.md): the approved prototype look replaces the stock Astryx theme across every view while the services, reducers and sockets stay as they are (see the M12 section). Before them, 137 live items. `IMP-M11-01…08` were added 2026-10-10 by [ADR-0016](../decisions/0016-spring-boot-4-migration.md), closing `IMP-GATE-97`: both Spring Boot services move to Boot 4.1.1 because two CRITICAL `spring-webmvc` CVEs have no fix on the 3.5 line. **M11 runs before M10** — every `IMP-M10-*` item depends on `IMP-M11-08` — and its items are judged locally with CI not awaited (see the M11 section). `IMP-M10-01…24` were added 2026-10-10 from the
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

## M21 — Public release

Opened 2026-11-07 from the refinement spike
([`../reviews/2026-11-04-refinement-spike/INDEX.md`](../reviews/2026-11-04-refinement-spike/INDEX.md),
`RS-01`, `03`, `04`, `06`, `12`) and the checks of the same day, approved by the owner the same day. It makes
the repositories public in a state the four audiences — potential employers, game designers, friends, the
owner — can use without asking anyone anything: an employer can verify every claim from the repositories, a
game designer adds the SDK with no token or account, and anyone can clone and build any repository with no
credentials. Cloud deployment is M22 (ADR-0021).

Items cite the findings (`F*`) and decisions (`D*`) below by number.

### M21 findings (2026-11-07)

| # | Finding | Evidence |
|---|---------|----------|
| F1 | All 8 repositories are PRIVATE; the org (free plan) has no profile, description or blog; no repository has topics; `turnbase-platform`'s description still says "Spring Boot 3.5+"; Issues and Projects on everywhere, Wiki off | `gh repo view`, `gh api orgs/turnbase-platform` |
| F2 | No `LICENSE`, `CONTRIBUTING` or `SECURITY` file anywhere; the umbrella has no `README.md`; `turnbase-frontend/README.md` is 3 lines, `turnbase-game-tictactoe`'s 19 | `ls` |
| F3 | **gitleaks v8.28.0 over every full history: no leaks** — 692 umbrella commits, 604 across the submodules (scanned from mirror clones; a scan through a submodule worktree reads 0 commits and is not evidence) | `zricethezav/gitleaks:v8.28.0 git` |
| F4 | 1,283 of 1,301 commits (all eight histories, today's included — it was the configured `user.email`) carry the owner's personal e-mail address as author/committer; only ~10 web-UI commits use the noreply address. The address appears **only in commit metadata** — in no file content, in no commit message | `git log --all --format='%ae'`, `git log -S`, `git grep` |
| F5 | **33 pull requests** (common 7, sdk 6, platform 6, game-host 6, frontend 8) keep their original commits reachable through `refs/pull/*`, which cannot be deleted; GitHub also serves force-pushed-away commits by SHA. A rewrite plus force-push would not remove the address from GitHub; only fresh repositories would, and the owner declined them (D8). No issues and no releases exist anywhere | `gh pr list --state all` |
| F6 | **No release has ever been cut.** `turnbase-common` and `turnbase-sdk` are `0.1.0-SNAPSHOT`, untagged; every consumer pins the SNAPSHOT, and its CI clones and installs the producer with a PAT — `TURNBASE_COMMON_PAT`, `TURNBASE_SDK_PAT` (platform, game-host, both games), plus `TURNBASE_GAME_HOST_PAT` and `TURNBASE_FRONTEND_PAT` for platform's e2e sibling checkouts. The games bundle `vendor/turnbase-gdk-0.1.0.tgz` | poms, workflows, `conventions.md` §5 |
| F7 | **The npm scope `@turnbase` belongs to someone else** (`@turnbase/keygen`, "Keygen tool for the TurnBase API", 2023). Keeping the GDK's name `@turnbase/gdk` is a dependency-confusion trap: a developer writing a version instead of our URL installs the other owner's package. `@turnbase-platform` is free | `registry.npmjs.org/-/org/turnbase/package` |
| F8 | `io.turnbase` cannot be claimed on Maven Central (the domain belongs to someone else); `io.github.turnbase-platform` is claimable through the GitHub org — kept open for a later move to Central | `search.maven.org`, DNS |
| F9 | GitHub Packages' Maven and npm registries **require a token even to read a public package**. GitHub Pages and GitHub Release assets do not — but **Pages on the free plan serves public repositories only** | GitHub docs |
| F10 | A GitHub organisation named `TurnBase` exists (empty, 2025): the name is used elsewhere. Not a blocker for a portfolio project; recorded so it is not a surprise | `gh api orgs/TurnBase` |
| F11 | 7WD ships no artwork (no image file in its history); its rules corpus is a restatement, and the rulebook PDFs are git-ignored and were never committed; the "reference implementation" its docs cite is the owner's own `game-room-management-platform`. Only the name and card names are Repos Production's. The platform names 7WD in one file (`deploy/compose/docker-compose.yml`) | `git log --all --name-only`, `git grep` |
| F12 | Fonts arrive as npm dependencies (`@fontsource/*`, SIL OFL 1.1); Astryx is MIT; the game-host image carries GraalVM CE / Espresso (GPLv2 with the Classpath Exception, UPL). No dependency licence report exists | `package.json`, poms |
| F13 | Workflows are safe to expose: `pull_request` runs never push images, no `pull_request_target`, no self-hosted runner. `.claude/settings.json` carries an absolute `/home/hmazur/proj/turnbase` sandbox path; `.claude/settings.local.json` is ignored only by the owner's global gitignore | workflow `grep`, `git check-ignore -v` |

### M21 goals

**Goals**
1. Apache-2.0 in every repository, declared in every build file; third-party licences known and compatible.
2. Every published artifact on GitHub, anonymously resolvable; consumers on a released version; no PAT and
   no repository secret left anywhere.
3. A landing page and an honest engineering story an employer can check against the repositories.
4. Every commit from 2026-11-07 on uses the noreply address; a repeatable pre-flip gate; a hardened public
   configuration.
5. 7WD released under its name only if the publisher's answer allows it.

**Non-goals:** a live instance or demo URL (M22); a documentation website (GitHub renders the corpus);
Maven Central or npmjs (possible later — F8 keeps the door open); versioned image releases of
platform/game-host/frontend (M22 decides what deploys); the Jackson 3 deprecation clean-up and the
load-test findings (Phase C); new features.

**Anti-goals** (a failure even if every box is ticked): anything secret or private going public (the
existing history's e-mail address excepted, D8); a README claim the repositories do not back; shipping 7WD's name against the
publisher's wishes; a red `master`
left behind after the flip session.

### M21 decisions

Marked **(owner)** where the owner decided, **(my call)** where the designer chose and a builder may revisit with a reason.

- **D1 Licence (owner).** Apache-2.0 for all eight. For 7WD it covers the code only.
- **D2 No per-file licence headers (my call).** Apache-2.0 does not require them; one `LICENSE` per
  repository plus the build-file declaration. No `NOTICE` file except 7WD's (D9).
- **D3 Coordinates (owner).** groupId `io.github.turnbase-platform` for every published jar; the GDK's
  npm name `@turnbase-platform/gdk`. Java package names stay `io.turnbase.*`.
- **D4 Distribution on GitHub only (owner).**
  - Jars: a Maven repository on each producer's own GitHub Pages site — `turnbase-common` at
    `https://turnbase-platform.github.io/turnbase-common/maven/`, `turnbase-sdk` (sdk, serialization,
    harness) at `https://turnbase-platform.github.io/turnbase-sdk/maven/` (the `/maven/` path is my call, to
    leave the site root free). Consumers add the `<repository>` they need; a game designer needs only the
    sdk one.
  - FE GDK: the `npm pack` tarball attached to the `turnbase-sdk` GitHub Release of the tag, depended on by
    URL. The jars are attached to the release too.
  - Images: GHCR, as today.
  - A new ADR (**ADR-0022**, distribution on GitHub) records this and supersedes ADR-0012's *Release
    Strategy* rows for common and sdk, and the IMP-GATE-25 deferral (`IMP-M21-04`).
- **D5 Publishing mechanics (my call).** The tag workflow deploys with
  `-DaltDeploymentRepository` into a checkout of the producer's `gh-pages` branch and pushes it, and
  creates the GitHub Release with the assets — all with the workflow's own `GITHUB_TOKEN`
  (`contents: write`); **no secret**. Sources jars are published (IDE navigation); no GPG signing (nothing
  validates it on Pages; Maven's checksums are written). Optional for the owner: claim the free npm org
  `turnbase-platform` so nobody else can (F7).
- **D6 First release (my call).** `v0.1.0` for `turnbase-common` and `turnbase-sdk`; pre-1.0 says the API may
  still move. Tags are cut by the owner (ADR-0012).
- **D7 Secrets and privacy gate (my call).** The gitleaks CLI in a container as a CI job in every
  repository (not `gitleaks-action`, which needs a licence key for organisation repositories), and
  `scripts/preflip-check.sh` over every full history before the flip. GitHub secret scanning and push
  protection on at the flip (free for public repositories).
- **D8 History kept as it is (owner).** The existing commits keep the personal address (F4): metadata
  cannot be changed in place, and the owner declined rewritten histories in fresh repositories. From
  2026-11-07 every repository's local `git config user.email` is
  `62445143+JayHubPL@users.noreply.github.com` (owner: per repository, not global — done), and the gate
  checks that no later commit uses another address.
- **D9 7WD (my call, overridable).** 7WD waits for the publisher's reply; everything else flips without it.
  It stays private. Meanwhile the umbrella README lists it as
  "pending" and `.gitmodules` still names it (a recursive clone then fails on that one submodule — the README
  says so). On permission: a `NOTICE` and a README/`INFO.md` line stating it is an unofficial
  implementation, not affiliated with or endorsed by Repos Production, whose name it is. On refusal: it stays
  private, and the umbrella drops its submodule entry and mentions; a renamed release would be a new design.
- **D10 The story from the repositories (my call).** Every number in the story is generated by a script from
  the repositories, or cited to the file that holds it.
- **D11 Contributions (owner).** Issues and security reports welcome; pull requests not accepted for now.
  Community files in an org-level `.github` repository, so all repositories inherit them, with
  `profile/README.md` as the organisation's landing page pointing at the umbrella.
- **D12 Settings as code (my call).** Every repository setting M21 relies on (eight repositories, a dozen
  settings each) is applied by an idempotent script, `scripts/repo-settings.sh`, not by hand, so it can be
  checked for drift.

### M21 order

```
01 licence ── 02 audit ───────────────────────┐
04 coordinates ── 05 release workflows ───────┤
03 gate ──────────────────────────────────────┤
06 README ── 08 READMEs, .github, settings ───┼── 10 the flip ── 11 consumers ── 12 outside
07 story ─────────────────────────────────────┘   (owner session)
09 7WD (BLOCKED on the publisher) ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄ own flip later
```

01, 03, 04, 06 and 07 can start at once. The only owner-held work before the flip session is the
`.github` repository (M21-08) and the publisher's reply (M21-09); the flip session itself (M21-10) is the
owner's main step, followed by cutting two tags.

### IMP-M21-01 — Apache-2.0 in every repository

**Repo:** all eight · **Depends on:** —

**Read first:** D1, D2; ADR-0012.

**Settled:** D1, D2. The canonical Apache-2.0 text, identical in every repository; the copyright line
`Copyright 2026 Hubert Mazur` where the appendix places it.

**Done when:**
- `LICENSE` at the root of all eight; every `pom.xml` has `<licenses>` with the Apache-2.0 name and URL;
  every `package.json` has `"license": "Apache-2.0"`; GitHub detects the licence in each repository.
- Every touched repository's build passes.
- `check-corpus.py` clean; merged and pushed.

### IMP-M21-02 — Third-party licence audit

**Repo:** all except `turnbase` · **Depends on:** M21-01

**Read first:** F12; each repository's `pom.xml` / `package.json` / `Dockerfile`; `conventions.md` §6.

**Settled:** the audit covers what each repository **distributes**: its jars, bundle or image (base image
included). An incompatibility — a copyleft licence without a linking exception in something we distribute —
is a stop-and-ask, not a swap made in passing.

**Done when:**
- A report per repository from a committed, pinned command (Maven: `license-maven-plugin`
  `aggregate-add-third-party`; npm: a pinned licence checker over production dependencies — the tool is the
  builder's), named in the repository's README.
- The allowed licence families are recorded in `conventions.md` (new subsection: Apache-2.0, MIT, BSD, ISC,
  OFL-1.1, EPL-2.0, UPL, GPLv2+CPE runtime-only in the game-host image; anything else asks).
- The frontend image and the game bundles carry the fonts' OFL text.
- `check-corpus.py` clean; merged and pushed.

### IMP-M21-03 — Pre-flip privacy and secrets gate

**Repo:** all eight · **Depends on:** —

**Read first:** F3, F4, F13; D7, D8.

**Settled:** D7. `scripts/preflip-check.sh` mirror-clones every repository into a temporary directory, runs
gitleaks over each full history, and fails on any author or committer e-mail on a commit dated
2026-11-07 or later that is not a `users.noreply.github.com` address, on any tracked file naming the owner's absolute home path or the
personal address, and on a commits-scanned count of zero (F3).

**Done when:**
- The script exists and exits non-zero on each failure kind (shown by a test against a throwaway repository
  with one planted finding of each kind).
- A `secrets` job runs gitleaks on push in every repository's `build.yml`, pinned to an exact image version.
- `.claude/settings.json`'s absolute sandbox path is replaced by one that works from any clone, or removed
  if the sandbox cannot take a relative path; `.claude/settings.local.json` is in the umbrella's
  `.gitignore`.
- The script passes on all eight.
- `check-corpus.py` clean; merged and pushed.

### IMP-M21-04 — Coordinates and distribution, spec first

**Repo:** `turnbase` (ADR, specs), then every repository with a pom or a GDK dependency · **Depends on:** —

**Read first:** F6–F9; ADR-0012 *Release Strategy*; `game-development-experience.md` CON-003, FR-FEGDK-007;
`conventions.md` §5; `backend-gdk-api.md` §2; `frontend-gdk-api.md`; `test-harness.md`.

**Settled:** D3, D4. ADR-0022 is written first, then the documents, then the code.

**Done when:**
- ADR-0022 exists (registered in `docs/decisions/` navigation); ADR-0012's rows for common and sdk point at
  it; CON-003 and FR-FEGDK-007 name the real coordinates and distribution; `conventions.md` §5 describes the
  target (Pages repositories, release-asset tarball) beside the bootstrap that still runs; no document in
  the corpus names `io.turnbase:` or `@turnbase/gdk` as a coordinate (archives excepted).
- Every pom's `groupId` and every GDK `package.json` name, dependency and import use the new coordinates;
  every build passes (the games still on `vendor/` until M21-11).
- `check-corpus.py` clean; merged and pushed.

### IMP-M21-05 — Release workflows on GitHub

**Repo:** `turnbase-common`, `turnbase-sdk` · **Depends on:** M21-01, M21-04

**Read first:** both `publish.yml`; D4–D6; `conventions.md` §5.

**Settled:** D4–D6. The workflow runs on a `v*.*.*` tag and on `workflow_dispatch` with a `dry-run` input.
The harness jar is published (it is for game designers).

**Done when:**
- `publish.yml` in both deploys to the producer's `gh-pages` `/maven/` tree and (sdk) creates the release
  with the GDK tarball and the jars, using `GITHUB_TOKEN` only.
- A dry run deploys into a workflow-local directory instead and proves the layout: a throwaway consumer pom
  resolves every artifact from that directory as a `file://` repository, and `npm install` of the tarball
  works. Pages itself is not exercised before the flip (F9) — M21-10 does that.
- ADR-0012 / ADR-0022 state what now happens on a tag.
- `check-corpus.py` clean; merged and pushed.

### IMP-M21-06 — The umbrella README

**Repo:** `turnbase` · **Depends on:** M21-01; screenshots need the local stack

**Read first:** `CLAUDE.md` (overview, tech stack, repository map); `docs/specs/INDEX.md`; ADR titles; the
`run-turnbase` skill; RS-06.

**Settled:** written for the four audiences in that order: what TurnBase is in two sentences; screenshots
(catalog, game room, a game in play; light and dark) captured from the local stack with Playwright and
committed under `docs/assets/` (each under 300 KB, registered in an INDEX); a Mermaid architecture diagram;
the repository map; a five-minute quickstart (the compose stack); *Write a game* (the GDK spec, the
coordinates of D4, `turnbase-game-tictactoe` as the template); status and roadmap (M22, Phase C); licence;
credits and 7WD's state per D9; issues welcome per D11. No claim without a link to where it is shown.

**Done when:**
- `README.md` renders on GitHub, diagram included; every relative link resolves (`check-corpus.py links`
  covers it, or is extended to).
- The quickstart was followed from a clean clone and works as written.
- `CLAUDE.md` links the README where it calls the umbrella the landing page.
- `check-corpus.py` clean; merged and pushed.

### IMP-M21-07 — How it was built

**Repo:** `turnbase` · **Depends on:** —

**Read first:** RS-06; `STATUS.md`; `docs/implementation/INDEX.md`, `registry.md`; `CLAUDE.md` *Session
Workflow*; the `work-item` and `spec-defect` skills; `docs/reviews/INDEX.md`; the ADR index; the load-test
summary; the `scripts/test-cost.sh` baseline.

**Settled:** D10. `docs/how-it-was-built.md`, registered and linked from the README: spec-first
(requirements → specs → ADRs → items); the agent workflow and its guard-rails (skills, `check-corpus.py`,
`git-land.sh`, hooks); the review rounds; the evidence (load test, test cost, coverage); and what went wrong
and what changed because of it (the PR suspension, the BLOCKED misuse, the jdtls incident, the readiness
gates). Numbers from `scripts/project-stats.sh` (new: commits, sessions, items, ADRs, requirement and spec
counts, tests per repository), with the date they were generated. Commit SHAs may be cited (histories are kept, D8).

**Done when:**
- Every number is produced by the script or cites the file it comes from; every claim links to evidence.
- The script runs on a clean recursive clone.
- `check-corpus.py` clean; merged and pushed.

### IMP-M21-08 — Component READMEs, community files and repository settings

**Repo:** all eight; `.github` (new) · **Depends on:** M21-06 (links back to it)

**Read first:** F1, F2; each repository's README and `ARCHITECTURE.md`; D11, D12.

**Settled:** every submodule README has one shape — what it is and where it fits (link to the umbrella),
build, run/test, layout (link to `ARCHITECTURE.md`), licence; the frontend's and tictactoe's are rewritten,
the rest brought to the shape. `CONTRIBUTING.md` (D11), `SECURITY.md` (private vulnerability reporting as
the channel), `CODE_OF_CONDUCT.md` and `profile/README.md` in the `.github` repository.
`scripts/repo-settings.sh` (D12) applies, idempotently: description (platform: Spring Boot 4.1), topics,
homepage (the umbrella), Projects and Wiki off, Issues on, and the hardening of M21-10 that the API can set.

**Owner-held:** creating the `.github` repository (the agent may with in-session confirmation).

**Done when:**
- Every README has the shape; the `.github` files exist (pushed to the repository, which stays private
  until the flip).
- `scripts/repo-settings.sh --check` reports no drift on the current repositories.
- `check-corpus.py` clean; merged and pushed.

### IMP-M21-09 — 7WD release decision

**Repo:** `turnbase-game-7wonders-duel`, `turnbase` · **Depends on:** the publisher's reply

**Read first:** F11; D9; 7WD's `README.md`, `INFO.md`, `manifest.json`.

**Gate:** Repos Production's answer to the owner (owner-held).

**Settled:** D9.

**Done when:** on permission, the `NOTICE` and the README/`INFO.md` disclaimer exist and the repository goes
through M21-10's flip steps; on refusal, the umbrella no longer names the submodule and `deploy/compose` no
longer seeds it, and the repository stays private. Either way the decision and its date are in the spike
INDEX.
- `check-corpus.py` clean; merged and pushed.

### IMP-M21-10 — The flip

**Repo:** all, org settings · **Depends on:** M21-01–08 (M21-09 may follow on its own)

**Read first:** D4–D9, D12; the outputs of M21-03, M21-05 and M21-08.

**Settled:** a runbook, `docs/specs/deployment/public-release.md` (registered in its INDEX), prepared by the
agent and executed in one owner session; the agent runs the API steps the owner confirms in-session.
Nothing lands in any repository from step 2 until step 4.

1. `scripts/preflip-check.sh` passes; `scripts/repo-settings.sh --check` reports no drift.
2. **Owner:** flip `turnbase-sdk`, `turnbase-common`, `turnbase-game-tictactoe`, `turnbase-game-host`,
   `turnbase-platform`, `turnbase-frontend`, `.github`, then the umbrella last (its links never point at a
   private repository); 7WD per M21-09.
3. Hardening, per public repository: secret scanning and push protection; private vulnerability reporting;
   Dependabot **alerts** on, security updates off (the freeze, `conventions.md` §6); CodeQL default setup
   for Java and JavaScript/TypeScript; a ruleset on `master` blocking force pushes and deletion (no required
   PRs — CLAUDE.md's direct-merge rule stands); Actions' default `GITHUB_TOKEN` read-only and fork-PR
   workflows needing approval; Pages enabled on `gh-pages` for common and sdk. **Owner:** GHCR packages set public (web UI only).
4. The bootstrap clone steps drop their PAT (the producers are public), so every consumer's CI is green
   before anything else lands.
5. **Owner:** cut `v0.1.0` in `turnbase-common` and `turnbase-sdk`; both publish; the artifacts resolve from
   Pages anonymously.

**Done when:** every step is ticked in the runbook with its date and the `gh api` read that confirms it;
`gh repo view` reports PUBLIC for each flipped repository; CI is green on every `master`.
- `check-corpus.py` clean; merged and pushed.

### IMP-M21-11 — Consumers on `0.1.0`, every secret gone

**Repo:** `turnbase-platform`, `turnbase-game-host`, `turnbase-game-tictactoe`,
`turnbase-game-7wonders-duel` · **Depends on:** M21-10 step 5

**Read first:** `conventions.md` §5 *Bootstrap exception*; each consumer's `build.yml`; ADR-0022.

**Settled:** `conventions.md` §5's own follow-up — version properties to `0.1.0`, the `<repository>` entries
of D4, and the clone-and-install steps deleted in the same change; the games depend on the release tarball
URL and `vendor/` is deleted; platform's sibling checkouts take no token.

**Done when:**
- No committed pom pins a SNAPSHOT of common or sdk; no workflow clones either; no workflow references any
  secret other than `GITHUB_TOKEN`, and no repository has any secret left (`gh secret list` empty).
- CI green in all four; the build-time saving per consumer is measured against RS-12's ~45 s and recorded
  in the registry row.
- `conventions.md` §5 describes the released state; the bootstrap paragraphs shrink to a dated note.
- `check-corpus.py` clean; merged and pushed.

### IMP-M21-12 — Verified from the outside

**Repo:** all public ones · **Depends on:** M21-11

**Read first:** the runbook; ADR-0022.

**Settled:** "outside" means a fresh container with no GitHub credentials, no `~/.m2`, no npm login.

**Done when:**
- In the clean container: `git clone --recursive` of the umbrella succeeds (7WD excepted per D9);
  `./mvnw verify` passes for common, sdk, game-host, platform and tictactoe, and `npm ci && npm run build`
  for the frontend; a new minimal game project resolving the SDK from Pages and the GDK from the release
  tarball compiles.
- Every link in the README, `how-it-was-built.md` and the org profile resolves from an anonymous browser.
- `STATUS.md` and `CLAUDE.md` record the release.
- `check-corpus.py` clean; merged and pushed.

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
