# Archive — M21 Public release

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim when M21 closed (2026-11-08). Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M21-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M21-01 | Apache-2.0 in every repository | all | — | DONE |
| IMP-M21-02 | Third-party licence audit | common, sdk, platform, game-host, frontend, tictactoe, 7WD | M21-01 | DONE |
| IMP-M21-03 | Pre-flip privacy and secrets gate | all | — | DONE |
| IMP-M21-04 | Coordinates and distribution, spec first | docs, then all with a pom or GDK dependency | — | DONE |
| IMP-M21-05 | Release workflows on GitHub | common, sdk | M21-01, M21-04 | DONE |
| IMP-M21-06 | The umbrella README | docs | M21-01 | DONE |
| IMP-M21-07 | How it was built | docs | — | DONE |
| IMP-M21-08 | Component READMEs, community files and repository settings | all, `.github` | M21-06 | DONE |
| IMP-M21-09 | 7WD release decision | 7WD, docs | owner's decision | DONE |
| IMP-M21-10 | The flip | all, org | M21-01…08 | DONE |
| IMP-M21-11 | Consumers on `0.1.0`, every secret gone | platform, game-host, tictactoe, 7WD | M21-10 | DONE |
| IMP-M21-12 | Verified from the outside | all public | M21-11 | DONE |

---

## M21 — Public release

Opened 2026-11-07 from the refinement spike
([`../reviews/2026-11-04-refinement-spike/INDEX.md`](../../reviews/2026-11-04-refinement-spike/INDEX.md),
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
| F13 | Workflows are safe to expose: `pull_request` runs never push images, no `pull_request_target`, no self-hosted runner. `.claude/settings.json` carries an absolute home-directory sandbox path; `.claude/settings.local.json` is ignored only by the owner's global gitignore | workflow `grep`, `git check-ignore -v` |

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

**Decided:** 2026-11-08 — the owner decided to publish without the publisher's reply, on the ground that the
repository uses no original art (owner-held decision, not overridden).

**Settled:** D9.

**Result (2026-11-08, session 298):** 7WD `NOTICE`, README and `INFO.md` disclaimer landed (`3236c6f`, CI green); `preflip-check.sh`
passed; flipped PUBLIC; `repo-settings.sh --apply --harden` then `--check --harden` reports no drift; `.gitmodules` `update = none`
removed, README no longer warns of a failing recursive clone.

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

**Close-out (2026-11-08, M21 verification):** CodeQL had **not** been set up anywhere. `repo-settings.sh`
tested the state with `grep -q configured`, which `not-configured` also matches, so `--check` reported no
drift and `--apply` skipped it. Fixed (`grep -qx`; a failed apply now prints `FAIL`), applied: default setup
`configured` in all nine repositories, first analyses green. Three high alerts, all dismissed with reasons:
platform `java/xss` in `GamePlayController` (false positive: the source is a bound `UUID`; the rest is
escaped), frontend `js/insecure-randomness` in `e2e/support.ts` and `js/incomplete-sanitization` in
`nginx.test.ts` (test code, no untrusted input). `npm audit` found dev-tooling advisories (vite, vitest,
esbuild, ws, undici, zod, source-map-js, brace-expansion, minimatch) in frontend, sdk, tictactoe and 7WD;
`npm audit --omit=dev` was already clean in all four. Cleared by bumps to the first patched releases and
`overrides.minimatch` `11.0.1` (eslint's `^10` has no fix); left: sdk's esbuild `0.27.7`, held by tsup
`8.5.1` (`^0.27`), whose advisory (GHSA-g7r4-m6w7-qqqr, low) is the Windows dev server tsup never runs.
`.github` got its `LICENSE` (it was created after `IMP-M21-01`).

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

**Measured (2026-11-08, session 296):** the bootstrap steps the previous green `master` run spent, now gone — platform
33 s (`build`; the `e2e` job repeated it, about 33 s more), game-host 33 s, tictactoe 25 s, 7WD 43 s. That is the
clone-plus-install time of RS-12's ~45 s estimate less the fetch from Pages, which is inside the Maven step. `gh secret list`
is empty in all eight repositories; no org-level secret was readable (403, not an org admin), so none was checked.

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


**Measured (2026-11-08, session 297):** fresh `maven:3.9-eclipse-temurin-21` containers, no credentials, no `~/.m2`, no npm login.
`git clone --recursive` first **failed**: `.gitmodules` used `git@github.com:` URLs (host-key failure) — fixed to `https://`,
and `turnbase-game-7wonders-duel` carries `update = none` so the private repository (D9) is skipped (`9bedaff`); the clone
then succeeded. `./mvnw verify` passed for common, sdk and tictactoe; `npm ci && npm run build` for the frontend; a minimal
project (pom with the sdk Pages `<repository>`, a class implementing `TurnBaseGame`) compiled and `npm i` of the
GDK release tarball installed. **Deviation:** game-host and platform need GraalVM CE and Docker (Testcontainers), which a
plain container does not give: game-host's Espresso tests passed on `ghcr.io/graalvm/jdk-community:21`, but its
`-Pintegration` run hung inside docker-in-docker and was killed; platform's ITs failed to reach Ryuk there. Their
clean-runner proof is the GitHub Actions `build` on `master` (public repository, no secret exists): success for both
(game-host `5386eed`, platform `37bc984`). Links: every absolute URL in README, `how-it-was-built.md` and the org profile
returns 200 anonymously except the bare Maven repository root (`…/turnbase-sdk/maven/`, 404 by nature: poms under it are 200).
