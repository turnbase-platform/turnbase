## Last Session Summary

**Date:** 2026-09-04 (session 17)

**`IMP-M0-04` is `DONE` — the Game Host skeleton, two more registry gates, and five Dependabot PRs
that turned into two real `dependabot.yml` bugs.** `turnbase-game-host` now boots GraalVM CE 21.0.2
(`ghcr.io/graalvm/jdk-community:21.0.2`) with Espresso available, CI green on `master` including the
container build. **4 of 60 items complete.**

### Two gates, opened and closed before and during the build

**IMP-GATE-08** — the *Done when* clause required "the process registers with the Platform Monolith
per §3's 60-second budget," but the Platform Monolith's server side of `GameHostRegistryService` is
not implemented until `IMP-M3-05` (depends on `IMP-M3-04`, `IMP-M2-04`) — nearly all of M2 and M3's
game-host chain, none of which this item (depends only on `IMP-M0-01`) can assume. Same shape as
`IMP-GATE-03`: an item's *Done when* clause needed its own dependents to exist first. Fixed: narrowed
to a client-side `Register` call proven against an in-process stub `GameHostRegistryService`; the real
cross-repo, live-monolith check moved to `IMP-M3-05`'s own *Done when* clause.

**IMP-GATE-09** — proving that `Register` call needed an address to dial, and no document named one.
`local-environment.md` §7 claims to be the whole tunable surface and §2's diagram puts the registry
service on the monolith's `8080` listener, but §7.8 (the Game Host's own properties) had no entry for
it — the same class of gap IR-24 closed for `turnbase.room.spectator-capacity`. Fixed: §7.8 gained
`turnbase.gamehost.orchestration-address` (default `platform:8080`, following the
`<service-name>:<port>` convention every other compose dependency already uses).

### What `turnbase-game-host` now has

`9090` serves `GameHostService` (every RPC inherits the generated base class's `UNIMPLEMENTED` response
until `IMP-M3-04`); `8081` is management only — `server.port=-1` disables the main servlet container,
so unlike the monolith there is no port `8080` here at all, just Spring's separate management server.
A `RegistrationLifecycle` component attempts `Register` on a background daemon thread at startup,
retrying every 2s for the 60-second budget without blocking startup — proven with three tests against
an in-process stub `GameHostRegistryService` (succeeds first try, retries then succeeds, gives up after
the budget). A trivial Espresso (`java`) guest context is created and disposed against the running
GraalVM CE 21 JDK (`allowNativeAccess(true)` is required for Espresso to boot at all on CE, per
`espresso-spike-results.md` — not a relaxation). Espresso pinned to the exact Maven artifacts
(`org.graalvm.polyglot:polyglot`/`java-community:23.1.2`) the spike verified.

**Everything was run, not just written**: `./mvnw verify` and `-Pintegration` both green locally, the
packaged jar boots in the built Docker image and answers `/actuator/health*` (all `UP`) on `8081` while
`9090` accepts connections, the guest JDK 21 symlink (`/opt/graalvm-guest-jdk21` → the host GraalVM's
own `$JAVA_HOME`) is present in the container, and CI is green on `master` including the container
build — the bar `work-item` sets, not a local pass.

### Five Dependabot PRs, two of which were real `dependabot.yml` bugs

Opened within a minute of the first push to `master`, as expected. Three were routine bumps within
pinned majors and were applied directly (not merged — Dependabot's own `pull_request` runs still lack
the bootstrap secret): Spring Boot 3.5.7→3.5.16, `grpc-bom` 1.83.1→1.84.0, `maven-failsafe-plugin`
3.5.6→3.6.0.

**The other two exposed gaps in the `dependabot.yml` ignore rules this session's own first draft
wrote.** A GraalVM/`jdk-community` docker bump to 25.0.2 opened despite an `ignore` entry naming
`ghcr.io/graalvm/jdk-community` — Dependabot's docker `dependency-name` omits the registry host, so
the entry never matched anything; fixed to `graalvm/jdk-community`. An Espresso bump to `23.1.12.1`
opened despite an `ignore` entry — but that entry only blocked `>=24`, treating Espresso like an
ordinary dependency, when the pom's own comment says it is pinned to **the exact build the spike
verified**. Any bump, patch included, needs a deliberate re-run of `espresso-spike-results.md`'s
probes, not a version-range judgment call. Both are the kind of thing that looks correct until the
first real PR proves it isn't — worth remembering for `turnbase-frontend`'s own `dependabot.yml`
(`IMP-M0-05`), which will pin Astryx exactly for a similar reason.

### Docker image note for the next session touching this repo

`ghcr.io/graalvm/jdk-community:21.0.2` is the base image (Oracle Linux 9, `$JAVA_HOME` at
`/usr/lib64/graalvm/graalvm-community-java21`), not `eclipse-temurin` — the host process itself must
run on GraalVM CE, unlike the plain-JRE `turnbase-platform` image. It has no `/usr/sbin/nologin`; the
non-root user's shell is `/bin/false` instead, which exists on every base image checked so far.

---

## Session 16 Summary

**Date:** 2026-09-04 (session 16)

**`IMP-M0-03` is `DONE` — the Platform Monolith skeleton, two more registry gates, and a real
infrastructure gap the corpus had no way to predict.** `turnbase-platform` now has Spring Boot 3.5.7
on Java 21, packaged by feature under `io.turnbase.platform` (ADR-0014), CI green on `master`
including the container build. **3 of 60 items complete.**

### Two gates, closed before and during the build

**IMP-GATE-06** — the item's own read-list cites `platform-operations.md` CON-010, which still said
integration tests use Docker Compose "within the CI runner." That directly contradicts
`platform-operations.md` FR-CICD-004, corrected 2026-08-20 to Testcontainers-only, and the same rule
restated in `conventions.md` §3. Simply missed when FR-CICD-004 was fixed. Fixed `platform-operations.md`
CON-010 to match.

**IMP-GATE-07** — the *Done when* clause required `turnbase-grpc` to "resolve at the exact pinned
version" under §5's absolute no-`SNAPSHOT` rule, but `turnbase-common` has never been tagged (tagging
is a human action) and the publish workflow that would produce a release is `IMP-M0-11`, which
**depends on** this item. Unsatisfiable as written — no release exists, and the pipeline that would
produce one hadn't been built yet. `conventions.md` §5 gained a bootstrap exception: pin the current
development version, resolve it from a local install, until the first tag exists; `IMP-M0-11` owns
both the real publish workflow and the follow-up consumer bump once it lands.

### What the gate's fix didn't anticipate: CI needs the same install, and `turnbase-common` is private

The bootstrap exception said resolve "from the local install" — true for a developer's machine, but a
GitHub-hosted runner starts with an empty one. The obvious fix — clone `turnbase-common` and install
it before building — hit a wall the corpus had no way to name in advance: `turnbase-common` is
**private**, and GitHub's default `GITHUB_TOKEN` cannot read a different private repository under
**any** organization setting, only a real credential can. First CI push failed on `git clone` with
*"could not read Username for 'https://github.com'."*

Resolved with the user: a fine-grained PAT, **read-only on Contents, scoped to `turnbase-common`
only**, stored as `TURNBASE_COMMON_PAT` in `turnbase-platform`'s secrets — narrowest credential that
does the job, revocable, and deliberately temporary (deleted the same PR that bumps the version
property once `IMP-M0-11` publishes a real release). `conventions.md` §5 now names this mechanism so
`IMP-M0-04` doesn't rediscover it. Two mechanical snags on the way: `gh secret set`'s interactive
prompt didn't survive being run through the session's `!` bridge (silently produced an empty secret,
which is why the *second* attempt also failed with `TURNBASE_COMMON_PAT: ` blank in the log) — the
`--body` flag worked where `read -s` didn't.

**Separately, the Docker build doesn't need this at all.** Rather than resolving `turnbase-grpc` a
second time inside a network-isolated build stage, the Dockerfile packages a jar `./mvnw verify`
already built in the same CI step — no in-container Maven build, so the image never needs its own
repository credential.

### Three Dependabot PRs, and a limitation worth knowing before `IMP-M0-04`

The first push opened three: a legitimate patch bump (spotless, nullaway), and two that jump a major
version this project hasn't adopted (Spring Boot 4.1.1 against the CLAUDE.md-pinned 3.5+; Java 25
against the pinned 21). All three initially showed CI failing — but not because of their content:
**Dependabot's own `pull_request`-triggered runs get no repository secrets**, so every Dependabot PR
against a bootstrap-window consumer fails the install step regardless of what it changes. Closed all
three, applied the legitimate bump directly (push-triggered CI has the secret), and added
`dependabot.yml` ignores for the two major bumps. Now in `conventions.md` §6 as the third
first-push trap, alongside the GraalVM and `buf breaking` ones `IMP-M0-01` found.

### What `turnbase-platform` now has

Twelve empty feature packages under `io.turnbase.platform`, `spring-modulith-starter-core`, and
`ApplicationModules.verify()` green (passes trivially — no code exists to violate a boundary yet, but
the first violation now fails a build). `8080` HTTP, `8081` management with its bind address driven by
`MANAGEMENT_SERVER_ADDRESS` — **verified live**, not just configured: loopback-only when the compose
value is set, all-interfaces when unset, matching `local-environment.md` §1 exactly. Health,
readiness and liveness all respond and report nothing about the Game Host. A `GameHostServiceGrpc`
blocking-stub test proves `turnbase-grpc` resolves and compiles here, not just in a throwaway
consumer. Merged JaCoCo at 70%, non-vacuous this time — a real `TurnBaseApplicationTest` boots the app
through its own `main` on ephemeral ports for 100% coverage of the one hand-written class.

**Everything was run, not just written**: `./mvnw verify` and `-Pintegration` both green locally,
the packaged jar boots and answers `/actuator/health`, the Docker image builds and its container
answers the same endpoints, and CI is green on `master` including the container-build step — the bar
`work-item` sets, not a local pass.

---

## Session 15 Summary

**Date:** 2026-08-22 (session 15)

**`IMP-M0-02` is `DONE` — the SDK's build-and-publish floor, and two more registry defects found
before any code existed.** `turnbase-sdk` now has `io.turnbase:turnbase-sdk` (Maven) and
`@turnbase/gdk` (npm) building, testing and publishing locally, both green in CI on the first
push. **2 of 60 items complete.**

### Two gates, opened and closed before writing code

Reading `IMP-M0-02`'s own three-document read-list found the item could not be built as written —
same shape as `IMP-M0-01`'s three gates, this time caught before any code rather than during it:

| Gate | The contradiction | Fix |
|---|---|---|
| **IMP-GATE-04** | Read-list was `backend-gdk-api.md` §1–3, claiming `FR-GDK-001`; but §3's `TurnBaseGame` references ten types defined in §4/§7 and its default method calls `PlayerJoinedResult.of(state)` — the §1–3 surface cannot compile without all of §§3–8, which is `IMP-M3-01`'s own *Done when* | `IMP-M0-02` narrowed to build-and-publish floor only; the Java type surface stays `IMP-M3-01`'s |
| **IMP-GATE-05** | `FR-FEGDK-001…009` (`TurnBaseClient`) was claimed only by `IMP-M6-05`, which implements the platform shell's half of the boundary, not the client — no item in `turnbase-sdk`, the repo that publishes `@turnbase/gdk`, owned it | New `IMP-M3-12 — FE GDK client`, in `turnbase-sdk`, depends on `IMP-M0-02`. `IMP-M6-05`'s *Satisfies* corrected |

Registry is now **60 live items**. Both gates closed in the same session they opened, per
`spec-defect`'s "still write both" guidance — the record of *why* is the durable part even when
open and close land together.

### What `turnbase-sdk` now has

Modelled on `turnbase-common`'s pom rather than re-derived: enforcer (JDK 21, plus a
**`bannedDependencies`** rule new to this repo — `turnbase-grpc` and `turnbase-game-host` banned
at every scope, verified to actually fire, mechanizing the rule `turnbase-sdk/CLAUDE.md` already
stated), Spotless, **Checkstyle** (the one repository that runs it, public-type Javadoc only,
verified to actually fire), Error Prone + NullAway (`AnnotatedPackages=io.turnbase.gdk` — no
generated code here to exclude), merged JaCoCo at 70% (vacuous today, same documented shape as
`turnbase-common`'s). `io.turnbase.gdk.GameState` plus all five `@NullMarked` packages
`backend-gdk-api.md` §2 fixes — four empty, because the layout is part of the published surface
and a later rename would be a breaking change.

npm side: `tsup` building ESM + CJS + bundled `.d.ts` from `src/main/ts/` (kept under Maven's
`src/main/<lang>` shape rather than a conventional npm `src/`, so the two toolchains share one
tree), the **declared** FE GDK types from `frontend-gdk-api.md` §5/§6/§9/§10 — `Role`, `Player`,
`Team`, `InitContext`, the `Window.__TURNBASE__` bootstrap global, the inbound/outbound message
envelope. Zero runtime dependencies, asserted by a test rather than assumed. No `TurnBaseGame`, no
`TurnBaseClient` — both deliberately absent, and `CLAUDE.md` now says so, so `IMP-M3-01` and
`IMP-M3-12` don't read as something broken.

### The one build trap this item hit

**`npm install` failed `ERESOLVE`** on the latest `typescript` (7.0.2): `typescript-eslint@8.67.0`
peers on `<6.1.0`. Not a spec defect — a toolchain-compatibility fact no document could have
stated — pinned to `6.0.3`, with the `dependabot.yml` `ignore` entry landing in the same commit as
the pin (`conventions.md` §6's rule, now exercised by a second repository). Separately, `tsup`'s
`.d.ts` bundling step tripped TS's new `baseUrl`-deprecation error even though this `tsconfig.json`
sets no `baseUrl`; `"ignoreDeprecations": "6.0"` silenced it. Neither reproduced by reading a spec —
both were found by running the build.

### CI green on both jobs, first push — unlike `IMP-M0-01`

Neither of `IMP-M0-01`'s two first-push failures applied here: no proto means no `buf` job, and
`conventions.md` §6 already carried the `graalvm/setup-graalvm` fix into this workflow from the
start. Both Dependabot PRs opened on the first push (`actions/setup-node` 6→7, `@eslint/js`
9.39.1→10.0.1) were legitimate and merged directly — neither touched a protected pin, unlike
`turnbase-common`'s five.

### Process note

**The provided-scope consumer probe and the two enforcement rules (Checkstyle, banned
dependencies) were each demonstrated against a deliberate violation**, not just asserted to exist
— the same discipline session 13 applied to `check-corpus.py`. All three fired correctly, then were
reverted.

---

## Session 14 Summary

**Date:** 2026-08-20 (session 14)

**The first code in the project, and three specification defects found by trying to write it.**
`IMP-M0-01` is **`DONE`** — the gRPC stubs are built, tested, pushed, and green in CI, and
`turnbase-common` now carries the full build floor of `conventions.md` §6. **1 of 59 items complete.**

The session also settled how this project is actually worked: the agent can now push (without any
force variant), so it sees its own hooks and its own pipeline fail. ADR-0012 lost a branch-protection
rule that never existed.

### The headline is not the code

Phase 0 produced a corpus that had been audited twice. The first item to actually compile something
against it hit **three contradictions in its own three-document read-list**, none of which any of the
five corpus checks could have found:

| Gate | The contradiction | Where the fix landed |
|---|---|---|
| **01** | `gamehost.proto` declared `java_package = "com.turnbase.gamehost.grpc.v1"`; `conventions.md` §1, ADR-0014 §1 and the item's own *Done when* all say `io.turnbase.grpc`. `com.turnbase` occurred **exactly once** in the entire corpus | the proto, now `io.turnbase.grpc.gamehost.v1`; rule stated in `conventions.md` §5 |
| **02** | ADR-0012 said the proto is copied into `src/main/proto/` **at build time**, and — eight lines earlier — that each repo is **independently usable without the root**. Both cannot hold | ADR-0012 amended: the copy is **committed**; drift guarded by `scripts/sync-proto.sh --check` |
| **03** | The *Done when* clause required resolution from `turnbase-platform` and `turnbase-game-host`, but `IMP-M0-04` **depends on** `IMP-M0-01` — the clause needed its own dependents | clause split: the local half stayed, the cross-repo half moved to `IMP-M0-03`/`IMP-M0-04` |

**GATE-02 is the one worth remembering.** It was not a typo or a stale sentence: two individually
correct statements combined into an impossible requirement, and resolving it silently would have
picked a repository layout by accident. The first symptom would have been `turnbase-common`'s CI
failing on the day it was first pushed, long after the choice was made and with nothing recording
that a choice existed.

That is exactly the failure `spec-defect` was written to prevent, and this is its first real
outing — three for three on an item budgeted as "close to mechanical".

### What `turnbase-common` now has

`./mvnw verify` runs Spotless → Error Prone + NullAway → protoc codegen → 15 tests → merged JaCoCo.
Enforcer fails a wrong JDK at `validate` rather than deep inside codegen. `buf lint` is clean with
**no** exception, because the committed copy sits at the canonical `turnbase/gamehost/v1/` path — the
lint waiver stays scoped to the spec tree, where the file is flat for readability beside its design
doc. Dependabot, a `pre-push` hook, and a workflow running `verify` plus `buf lint`/`breaking`.

**The surface test parses the `.proto` instead of hard-coding what it expects.** A hard-coded list
asserts that codegen produced what the test author typed, and stays green when someone adds a service
to the contract and forgets everything downstream. It also pins the thing GATE-01 could have broken
silently: the **wire** name is still `turnbase.gamehost.v1.*` regardless of the Java package, and
since both peers regenerate from the same file, nothing else would have noticed.

### Three build traps, none of which said what they were

- **Error Prone on JDK 21 additionally needs `-XDaddTypeAnnotationsToSymbol=true`**, beyond the
  `compilePolicy` and `should-stop` flags `conventions.md` §2 already named. Now in §2.
- **`protobuf-maven-plugin` 5.x rewrote its configuration surface.** Pinned to 4.1.3, with a
  Dependabot `ignore` entry so the pin is not mistaken for neglect.
- **XML comments cannot contain a double hyphen**, so no pom comment can quote a compiler flag.

And one that would have bitten later: the parent checks out the proto as CRLF while the submodule
pins it to LF, so `sync-proto.sh --check` would have reported drift on **every line of an identical
file** after a fresh clone — a false alarm on the one check whose value is that a real difference is
never dismissed as noise. Both ends pinned, and the comparison made line-ending agnostic anyway.

### CI failed both jobs on the first push, and neither failure reproduced locally

This is the part worth carrying, because the other three Java repos will meet the first one:

- **`actions/setup-java` has no `graalvm-community` distribution.** GraalVM CE is set up by
  `graalvm/setup-graalvm`. The error names the distribution, so it reads as a typo rather than as the
  wrong action entirely.
- **`buf breaking` had no baseline.** On a push it compared against `HEAD~1` — which, on the commit
  that *introduces* the proto, is a tree with no protos. `Module "path: "." had no .proto files`
  names the module, not the absent baseline. It now runs on pull requests only, against the base
  branch; `buf lint` still runs on everything because it always has an answer.

Both are recorded in `conventions.md` §6.

**Dependabot opened five PRs within a minute of the first push**, one of them reverting the
deliberate `protobuf-maven-plugin` pin. The rest were right and were applied directly — `checkout`
and `upload-artifact` to v7, the Maven wrapper to 3.9.16 — then all five were closed as superseded.
The rule that came out of it, now in `conventions.md` §6: **an `ignore` entry ships in the same
change as the pin it protects**, carrying the reason.

### Two process decisions

**The agent pushes now, without any force variant.** `--force`, `--force-with-lease`, `--mirror`,
`--delete`, `--prune`, `--tags` and `+refspec` are denied; tag pushes stay a human action because
ADR-0012 makes a `v*.*.*` tag the release trigger. This closed a real gap rather than a theoretical
one — the `pre-push` hooks existed for a session without ever having been seen to run. They now fire
on every push and are visible in the transcript. The alternative, moving them to `pre-commit`, was
rejected: it would have taxed all nine commits of this session to run a check that mattered on four
pushes, and a commit is *allowed* to be broken — the `work-item` skill mandates a claim commit before
any code exists.

**ADR-0012's "`master` — protected, no direct pushes" is removed.** GitHub does not offer branch
protection on private repositories outside a paid plan, so the clause described a setting that never
existed, read as a guarantee, and contradicted the same ADR's "self-merge is fine for solo work".
Feature branches and PRs remain the normal path; the document now describes what the platform
enforces.

### One thing left deliberately imperfect, and written down rather than hidden

**The coverage gate in `turnbase-common` is inert.** It measures the hand-written remainder, which is
empty, so JaCoCo logs "All coverage checks have been met" over a bundle of **zero classes** — the
same fail-open shape `conventions.md` §3 warns about. That is a true statement about a codegen-only
module, and the alternatives were worse: lowering the threshold, or including generated stubs and
setting the gate to whatever codegen happens to emit. It becomes load-bearing with no build change on
the first class under `io.turnbase.grpc.internal`, which is why that package exists now carrying
`@NullMarked`. Recorded in the pom, the README and the registry — three places a reader would look.

---

## Session 13 Summary

**Date:** 2026-08-20 (session 13)

**A readiness review of the harness rather than the corpus, and everything it produced.** The
specifications were already implementation-ready; what was missing was the layer beneath them — the
conventions every work item assumes, and the Claude Code setup that executes them. Two ADRs, two new
documents, a checker, two skills, five submodule instruction files. Still no code.

### What the review found

The corpus says *what* to build (requirements), *how it is designed* (specs) and *what to build next*
(the registry). It said nothing about **how the code is written**: no package layout, no formatter,
no static analysis, no coverage tool, no test-suffix convention, no cross-repo version rule.

**The corpus's only evidence of the monolith's package root was a logger name in a JSON sample** in
`observability.md`, written to illustrate log structure rather than to decide anything. That is the
shape of the whole gap: the decisions existed nowhere, so the first item to need one would have made
it silently and the next thirty would have disagreed.

### Seven defects, all closed

| # | Defect | Fix |
|---|---|---|
| 1 | FR-CICD-002/006/007 + CON-009 + OQ-002 gated on `main`; every repo is on `master` | Corrected against ADR-0012. A workflow written from the old text never fires |
| 2 | FR-CICD-004 said integration tests use Docker Compose; `local-environment.md` §8 says Testcontainers and rejects a hand-started stack | §8 was right; the requirement now carries the reason inline |
| 3 | IMP-M3-10's repo did not exist and ADR-0012 lists five | Deferred **by decision**: `turnbase-game-<name>` is created when the item starts |
| 4 | FR-CICD-003 gates on coverage; no tool named anywhere | JaCoCo, over **merged** unit + integration exec data |
| 5 | Google Java Style was a `CLAUDE.md` SHOULD with no mechanism | Spotless + `google-java-format` at `validate` |
| 6 | No package layout, and none for tests | ADR-0014 + `conventions.md` §§1, 3 |
| 7 | No cross-repo version rule | Exact pins, a `-D` override for the local loop, a stated release order |

### Two ADRs, and they share one argument

**[ADR-0014](docs/decisions/0014-modular-monolith-spring-modulith.md)** — the monolith is packaged by
feature under `io.turnbase.platform`, and **Spring Modulith fails the build** when one feature reaches
into another's internals. The twelve feature packages are the registry's own milestone decomposition,
lifted rather than invented, so every work item already knows its package.

**[ADR-0015](docs/decisions/0015-static-analysis-error-prone-nullaway.md)** — **Error Prone +
NullAway**, JSpecify `@NullMarked` at package level, in every Java repository. Formatting checks the
*shape* of code; nothing in the build was looking for **defects**. Nullness is load-bearing in this
data model specifically: `left_at` / `lost_announced_at` drive the deferred-tail partial index, and
`owner_user_id`'s nullness is tied to `badge='OFFICIAL'` by a check constraint. Rejected SpotBugs and
PMD (noise), and ArchUnit (Modulith already owns that invariant).

**Both were taken before any code existed, for the same reason: a build-time check is cheap at
skeleton time and prohibitive at work item forty**, where the retrofit arrives as one unreviewable
change and gets downgraded to a warning — which is the same as not having it. There is no later point
at which either decision is available on the same terms. That argument is why they are ADRs and
Spotless, JaCoCo and the test suffixes are not.

### `docs/implementation/conventions.md` — new, and normative

Package layout, formatting, static analysis, tests and coverage, git, cross-repo dependencies, and
the per-repo build floor. Deliberately **not** repeated in read-lists: it is assumed the way
`CLAUDE.md` is. `implementation/INDEX.md` carries the rule that makes that safe — *if you are
deciding something that should be the same across all forty platform items, the answer belongs in
`conventions.md` and its absence is a defect.* Settling it locally is what produces four conventions.

### The harness layer

**Five submodule `CLAUDE.md` files**, additive to the root one, each carrying only what is repo-local.
The bias was toward traps that surface far from their cause: the management port differing between
compose and Kubernetes, `<LinkProvider>` presenting as a navigation bug three milestones downstream,
the proto copy that diverges invisibly because both sides still compile, the CE-23 image that does
not exist. `turnbase-game-host/README.md` still advertised GraalVM CE 23; corrected.

**`scripts/check-corpus.py`** — five checks, exit 1 on failure: `links`, `cites`, `sections`,
`index`, `registry`. It is a script rather than a skill because it is mechanical, and what is
enforceable by validation should be automated. **Verified against deliberate defects rather than
assumed**, and the registry check confirmed non-vacuous (60 rows, 60 sections, 59 `READY` + 1
`CANCELLED`).

It found two real citation defects on its first run — one of them written three commits earlier in
the same session (`registry.md` qualifying FR-CICD-004 with `local-environment.md`), the other
`bundle-format.md` qualifying CON-006 with a document that does not define it, where CON-006 exists
in six documents with unrelated meanings.

**Registry status protocol** — status lives in the register table and nowhere else; whoever works the
item writes the transition in the same commit as the work, not from memory at session end. Two
invariants are now machine-checked: every ID has both a row and a section, and `BLOCKED` holds if and
only if a `Gate:` line exists. **Escalation format** — the `Gate:` line, the specification fix and the
`STATUS.md` entry happen together or none of them count.

**Two project skills** in `.claude/skills/`: **`work-item`** (the cadence — claim, read exactly the
read-list, build to the *Done when*, verify green, bump the ref) and **`spec-defect`** (the
escalation, whose argument is that stopping is the *cheap* option). Written with skill-creator's
guidance; **not stress-tested against subagents** — the owner's call, reasonable for a solo project,
and their real test is the first M0 items.

### Decisions worth carrying

- **Spotless over Checkstyle for format.** A formatter that rewrites gives an agent a diff; a linter
  gives it forty complaints to hand-edit. `spotless:apply` **before** the PR — a bounced pipeline
  costs one turn to discover and another to fix. Checkstyle survives in `turnbase-sdk` only, for the
  one rule a formatter cannot check.
- **Git hooks: `pre-push`, native, via `core.hooksPath`. Not husky, not pre-commit.** Commits here
  are constant and a pre-commit hook pays a JVM start on each; pushes are roughly one per work item.
  And **the agent cannot push** — `git push` is denied — so a `pre-push` hook catches what an agent
  left broken at the moment a human is about to publish it. husky would mean adding `package.json` to
  three Maven repos, and one repo differing is worse than five matching.
- **No `-SNAPSHOT` in a committed pom.** It makes builds unreproducible and hides breaking proto
  changes. The local loop is a `-D` override with nothing to forget to revert.
- **A check that fires is fixed or suppressed at the site with a reason.** Lowering severity
  build-wide is one invisible decision that turns off a class of finding forever.

### Three traps now written down because they fail confusingly

- **JaCoCo wired the obvious way measures unit tests only** — and it fails *open*, reporting a number
  nobody can tell is wrong. FR-CICD-003 counts unit *and* integration, so two exec files must be
  merged before a single `check`.
- **Naively annotated, forty integration tests start forty PostgreSQL containers** and the PR
  pipeline stops being run. Containers start once per JVM; isolation comes from truncating.
- **`google-java-format` and Error Prone both need `.mvn/jvm.config` flags** (`--add-exports`,
  `-XDcompilePolicy=simple`, `--should-stop=ifError=FLOW`). The first failure reads like a broken
  toolchain rather than a missing flag.

### `IMP-M0-03` is no longer a mechanical item

It now establishes the build floor for the repository holding forty of the 59 work items: wrapper,
Spotless, Error Prone + NullAway, JaCoCo, the twelve empty feature packages, the Modulith
verification test, and the `pre-push` hook. Deliberate — every one of those is cheapest at skeleton
time — but the old framing of *"M0-01…05 are mechanical and unblock everything"* is no longer true
of it.

### Verification

`python3 scripts/check-corpus.py` clean across all five checks. Both new ADRs registered in
`decisions/INDEX.md`; `conventions.md` registered in `implementation/INDEX.md`.

### Permissions

Applied by the owner, and bare `Bash(mvn *)` deliberately dropped so only `./mvnw` is frictionless —
which is what `conventions.md` §6 requires. **Two gaps remain:** `mcp__playwright__*` does not match
the actual tool names (`mcp__plugin_playwright_playwright__*`), and **`mcp__astryx__*` is not
allowlisted at all**, so every Astryx component lookup will prompt — and ADR-0013 makes that lookup a
tool call by design.

---

## Session 12 Summary

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

**Phase 1 is under way. Work from [`docs/implementation/INDEX.md`](docs/implementation/INDEX.md), not
from this file.** The registry holds **60 live work items** (IMP-M6-07 is cancelled), each with a
read-list, dependencies, the requirement IDs it satisfies and a done-when clause; this section only
says which of them to pick up.

**Progress: 4 of 60 done** — `IMP-M0-01` (gRPC stubs, `turnbase-common`), `IMP-M0-02` (SDK
build-and-publish floor, `turnbase-sdk`), `IMP-M0-03` (Platform Monolith skeleton,
`turnbase-platform`) and `IMP-M0-04` (Game Host skeleton, `turnbase-game-host`), all pushed and green
in CI. **No work item is gated**, and all 23 readiness blockers remain closed, so an item's status is
whatever its own dependencies imply.

**`IMP-M0-05` (frontend skeleton) has no bootstrap-window dependency on `turnbase-common`** — it is a
clean start, unlike the last three M0 items. **`IMP-M0-06` (Flyway baseline)** is the other open
candidate and the highest-value item in the registry: it depends only on `IMP-M0-03`, which is done.

**IMP-GATE-09** (`IMP-M0-04`, opened and closed 2026-09-04) — no document names the address the Game
Host dials to reach the Platform Monolith's `GameHostRegistryService`, which `local-environment.md`
§2 places on the monolith's `8080` HTTP listener rather than a dedicated port. Fixed: §7.8 gained
`turnbase.gamehost.orchestration-address` (default `platform:8080`).

**IMP-GATE-08** (`IMP-M0-04`, opened and closed 2026-09-04) — the *Done when* clause required "the
process registers with the Platform Monolith per §3's 60-second budget," but the platform's server
side of `GameHostRegistryService` is not implemented until `IMP-M3-05` (depends on `IMP-M3-04`,
`IMP-M2-04`), far downstream of `IMP-M0-04` (depends only on `IMP-M0-01`). Same shape as
`IMP-GATE-03`. Fixed: `IMP-M0-04`'s clause narrowed to a `Register` client call proven against an
in-process stub registry service; the real cross-repo, 60-second-budget check is now `IMP-M3-05`'s own
*Done when* clause.

**IMP-GATE-07** (`IMP-M0-03`, opened and closed 2026-09-02, `DONE` 2026-09-04) — `IMP-M0-03`/`M0-04`'s
*Done when* required the `turnbase-grpc` client/server stubs to resolve "at the exact pinned
`<turnbase-common.version>`" against `conventions.md` §5's absolute "no `-SNAPSHOT` in a committed
pom" — but `turnbase-common` has never been tagged (a human action) and the publish workflow that
would produce a release is `IMP-M0-11`, which depends on `M0-03`/`M0-04`. Unsatisfiable as written.
Fixed: `conventions.md` §5 gained a bootstrap exception — pin the current development version,
resolved from the local install, until the first tag exists; `IMP-M0-11` owns both standing up the
publish workflow and the follow-up PRs that bump consumers to the real release once it's tagged. The
fix's first draft still missed how CI itself gets that install — see the session 16 summary above for
the private-repo credential problem that turned up executing it.

**IMP-GATE-06** (`IMP-M0-03`, opened and closed 2026-09-02) — `platform-operations.md` CON-010 still
said integration tests use Docker Compose, contradicting FR-CICD-004 in the same document (corrected
2026-08-20 to Testcontainers-only) and the same rule restated in `conventions.md` §3. Simply missed
when FR-CICD-004 was fixed. Fixed `platform-operations.md` CON-010 to state the Testcontainers/compose
split correctly.

Seven gates have now been opened *and closed* across the first three items — three on `IMP-M0-01`,
two on `IMP-M0-02`, two on `IMP-M0-03` — which is the number worth planning around: **a skeleton item
costs roughly one spec defect per document in its read-list.** Budget for that rather than treating a
gate as a delay.

**IMP-GATE-05** (`IMP-M0-02`, closed 2026-08-22) — `game-development-experience.md`
FR-FEGDK-001…009 (the `TurnBaseClient` class itself) was claimed only by `IMP-M6-05`, which
implements the platform shell's half of the postMessage boundary, not the client — no item in
`turnbase-sdk`, the repo that publishes `@turnbase/gdk`, owned it. Fixed by adding
**`IMP-M3-12` — FE GDK client**, depends on `IMP-M0-02`, and correcting `IMP-M6-05`'s *Satisfies*.

**IMP-GATE-04** (`IMP-M0-02`, closed 2026-08-22) — the read-list named `backend-gdk-api.md` §1–3
and claimed `FR-GDK-001`, but §3's `TurnBaseGame` cannot compile without all of §§3–8 — verbatim
`IMP-M3-01`'s own *Done when*. Fixed by narrowing `IMP-M0-02` to the build-and-publish floor; the
Java type surface stays `IMP-M3-01`'s.

**IMP-GATE-03** — the clause "resolves from both `turnbase-platform` and `turnbase-game-host`"
required the item's own dependents to exist first (`IMP-M0-04` depends on `IMP-M0-01`). The half that
is checkable at the source — install, then compile and run a consumer against the client stub *and*
the server base class — stayed; the cross-repo half moved onto `IMP-M0-03` and `IMP-M0-04`, which
have a consumer to check it with.

**IMP-GATE-02** — ADR-0012 said `turnbase-common` copies `gamehost.proto` into `src/main/proto/` *at
build time*, and also said each component repo is *independently usable without the root*. Two
sections apart, and they cannot both hold: a Maven step reading `../docs/` fails in a standalone
clone, which is exactly what that repo's CI checks out. ADR-0012 is amended — the copy is a
**committed file**, and the drift guard is `scripts/sync-proto.sh --check` in the parent's `pre-push`
hook, because drift here is silent (both repos compile; the two services disagree on the wire).

**IMP-GATE-01** — `gamehost.proto` declared `java_package = "com.turnbase.gamehost.grpc.v1"` against the
`io.turnbase.grpc` root that `conventions.md` §1 and ADR-0014 §1 both give `turnbase-common`. The
proto now declares `io.turnbase.grpc.gamehost.v1`, and `conventions.md` §5 states the rule — package
tail and canonical buf-module path — so the next generated artifact does not re-decide it.

**None of the three was findable by reading**, and none would have been caught by
`check-corpus.py`. They surfaced only because something finally had to compile against the documents.
That is the argument for doing the skeletons before anything subtle depends on them.

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

**Implementation:** `docs/implementation/` — the registry Phase 1 executes from. **60 live work items
across 7 milestones** (IMP-M6-07 cancelled; `IMP-M3-12` added session 15), each carrying a
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
