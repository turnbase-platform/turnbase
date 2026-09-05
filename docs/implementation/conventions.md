# Code and Build Conventions

The decisions every repository shares: how code is laid out, how it is formatted, how it is tested,
and how the five repositories depend on each other. One place, so that forty work items built across
many sessions produce one codebase rather than four.

`INDEX.md` covers the conventions of the **registry** — item identifiers, statuses, gates, what a
work item carries. This document covers the conventions of the **code**.

> **This document is normative.** Where a work item's *Done when* clause and this document disagree,
> that is a defect — record it. Where this document is silent on something a work item needs, that is
> also a defect: the answer belongs here, not in the item.

---

## 1. Package layout

Per [ADR-0014](../decisions/0014-modular-monolith-spring-modulith.md), the Platform Monolith is
packaged **by feature**, and the feature list is the milestone decomposition.

| Repository | Root package |
|---|---|
| `turnbase-platform` | `io.turnbase.platform` |
| `turnbase-game-host` | `io.turnbase.gamehost` |
| `turnbase-common` | `io.turnbase.grpc` |
| `turnbase-sdk` | `io.turnbase.gdk` (fixed by [`backend-gdk-api.md`](../specs/gdk-api/backend-gdk-api.md) §2) |

The monolith's features:

```
io.turnbase.platform
├── common/          error model, pagination, validation, rate limiter
├── account/  session/  social/
├── room/     chat/     game/
├── catalog/  upload/   history/
├── notification/      admin/
```

**Inside a feature**, layer as usual — controller, service, repository, domain. **Across features**,
go through the target feature's top-level API; anything under `<feature>/internal/` is private to it.
`ApplicationModules.verify()` fails the build when that rule is broken or when two features form a
cycle (ADR-0014 §3).

**Reading a Modulith failure:** it names the *source* type, the *target* type it must not see, and
the module boundary crossed. The fix is almost never to relax the boundary. It is either (a) expose
what the caller actually needs on the target's public API, or (b) if that produces a cycle, invert it
with a Spring application event (ADR-0014 §4). Widening the module definition to make the error go
away removes the only mechanism that was going to catch the next one.

### Frontend

`turnbase-frontend` follows [`shell-architecture.md`](../specs/platform-frontend/shell-architecture.md)
for structure and [ADR-0013](../decisions/0013-astryx-design-system.md) for components. The one rule
that belongs here: `src/ui/` holds **only** what Astryx does not ship, and is expected to stay near
empty. Application code imports `@astryxdesign/core/<Component>` directly — there is no wrapper layer.

---

## 2. Formatting

**Every Java repository uses [Spotless](https://github.com/diffplug/spotless) with
`google-java-format`.** `CLAUDE.md` already requires Google Java Style; `google-java-format` *is* that
style, executable, with nothing to configure and therefore nothing to drift between repositories.

Spotless steps, in every Java repo, identical:

| Step | |
|---|---|
| `googleJavaFormat` | The formatter. Version pinned in the parent-less `pom.xml` of each repo |
| `removeUnusedImports` | |
| `importOrder` | Empty configuration — google-java-format's own order |
| `trimTrailingWhitespace`, `endWithNewline` | |

**Binding:** `spotless:check` runs at the **`validate`** phase — before compilation, failing in
seconds rather than after the test suite. `./mvnw verify` therefore enforces it, and CI inherits it
with no extra workflow step.

**The fix is `./mvnw spotless:apply`.** This matters more than it looks: a formatter that *rewrites*
gives an agent a diff, where a linter gives it forty complaints to hand-edit. Run `spotless:apply`
**before merging to `master`**, not after CI rejects it — a bounced pipeline costs a full session turn
to discover and another to fix, and with PRs suspended (§4) the bounce lands on `master` itself.

**Setup trap.** `google-java-format` uses internal `javac` APIs, so on JDK 16+ Spotless needs
`--add-exports` flags for `jdk.compiler` in `.mvn/jvm.config`. Without them the very first
`spotless:check` fails with an `IllegalAccessError` that looks like a broken toolchain rather than a
missing flag. The file is committed per repo; the flags are in Spotless's own documentation for the
`googleJavaFormat` step.

**Checkstyle is used in `turnbase-sdk` only**, configured for one thing: Javadoc on every public
type. That is a `CLAUDE.md` SHOULD and an `IMP-M0-02` *Done when* clause, and it is the one rule a
formatter cannot check. Adding Checkstyle to the other repositories buys duplicated format rules and
an argument.

### Static analysis

Per [ADR-0015](../decisions/0015-static-analysis-error-prone-nullaway.md), every Java repository runs:

| Tool | Configuration | Fails the build on |
|---|---|---|
| **Error Prone** | compiler plugin; default `ERROR` patterns stay at `ERROR` | its own bug patterns |
| **NullAway** | Error Prone plugin; JSpecify `@NullMarked` at package level | a dereference it cannot prove safe |

Formatting checks the shape of the code; these are the only things in the build that look for
**defects**. Nullness in particular is load-bearing in this data model — `left_at` /
`lost_announced_at` drive the deferred-tail partial index, and `owner_user_id`'s nullness is tied to
`badge='OFFICIAL'` by a check constraint — so it is worth having the compiler enforce what the schema
already means.

**Two configuration traps**, both of which fail in ways that read like a broken toolchain:

- Error Prone needs three compiler arguments — `-XDcompilePolicy=simple`,
  `--should-stop=ifError=FLOW` and, **on JDK 21, `-XDaddTypeAnnotationsToSymbol=true`** — plus
  `--add-exports` flags for `jdk.compiler`, which are the same family of setup as
  google-java-format's and go in the same `.mvn/jvm.config`. Error Prone refuses to start without the
  third and says so in one line that reads like a corrupt install; it cost `IMP-M0-01` a build cycle
  to find, which is the only reason it is named here.
- A pom **comment** cannot quote any of those flags: XML forbids a double hyphen inside a comment,
  and the parse error points at the comment rather than at what is wrong with it. Describe the flags
  in prose; the `<compilerArgs>` elements themselves are fine.
- **Generated code and Spring injection points must be excluded from NullAway's scope.** gRPC stubs
  are generated and will not be annotated. Noise on code nobody wrote is the fastest route to
  somebody muting the tool.

**A check that fires is fixed, or suppressed at the site with a reason.** `@SuppressWarnings("Name")`
plus a comment is fine. Lowering a check's severity build-wide is not: it is one decision, invisible
afterwards, that turns off a class of finding for the whole project.

### TypeScript

Prettier + ESLint + `tsc --noEmit`, per `platform-operations.md` FR-CICD-011. Same principle as Java:
**Prettier writes, ESLint complains.**

The ruleset, pinned here so it is not decided by whoever runs `npm create vite` first:

- ESLint **flat config** (`eslint.config.js`).
- `typescript-eslint` **strict** + `stylistic` configs, type-aware.
- `eslint-plugin-react-hooks` — the rules-of-hooks check is the one that catches real bugs.
- `eslint-config-prettier` last, so ESLint stops having opinions about formatting.

`tsconfig.json` runs `strict: true`. It is the TypeScript half of the same argument NullAway makes
for Java, and it is equally impossible to adopt later.

---

## 3. Tests

Three categories, defined by `platform-operations.md` FR-CICD-004 and given their dependencies by
[`local-environment.md`](../specs/deployment/local-environment.md) §8.

| Category | Suffix | Plugin | Dependencies | Invocation |
|---|---|---|---|---|
| Unit | `*Test` | surefire | none — mocked boundaries | `./mvnw test` |
| Integration | `*IT` | failsafe, bound to `verify` under `-Pintegration` | real Postgres, Redis, MinIO via **Testcontainers** | `./mvnw verify -Pintegration` |
| E2E | — | — | the full compose stack | `make e2e` |

Tests live **beside the code they test**, in the same package-by-feature tree, under
`src/test/java`. There is no parallel `it/` source root: an integration test for rooms is
`io.turnbase.platform.room.RoomJoinIT`, next to `RoomJoinTest`.

**Integration tests never use Docker Compose.** FR-CICD-004 said they did until 2026-08-20; §8 was
right and the requirement was corrected. A test that depends on a stack someone started by hand
passes locally and fails on every clean machine and in CI. Compose is the e2e tier's dependency and
only there — and where a scripted compose fixture is genuinely needed for e2e, it belongs in the
`make e2e` target, not in a test's `@BeforeAll`.

**The container-reuse trap.** Naively annotated, forty integration tests start forty PostgreSQL
containers and the pipeline stops being run. Start containers **once per JVM** — a static
singleton initialised in an abstract base class, or Testcontainers' reuse flag — and let Spring Boot's
`@ServiceConnection` bind them. Isolation between tests comes from truncating or rolling back, not
from a fresh container.

**Integration tests run migrations**, because Testcontainers hands Flyway an empty database. Every
integration run is therefore also a migration test — the check of
[`schema-migrations.md`](../specs/deployment/schema-migrations.md) §6 as a side effect of ordinary
work rather than a job somebody has to remember.

Two more traps that §8 names and are repeated here because they are found by failing tests, not by
reading:

- A test of grace expiry must **override** `grace-period` and `deadline-sweep.interval`, not wait
  them out. Sleeping 65 seconds in a suite is not a test.
- A test of reconciliation must clear `reconcile.startup-suppression` (120s), or every repair
  assertion fails with no repair and no error — the sweep detects, logs, and deliberately does
  nothing (`room-lifecycle.md` §5.4).

### Coverage

**JaCoCo**, threshold **≥70% line**, per `platform-operations.md` FR-CICD-003.

The requirement measures coverage across **unit and integration together**, which is the part that is
easy to get wrong. Each tier writes its own exec file; `jacoco:merge` combines them; a single
`jacoco:check` runs against the merged data. Wire it the obvious way — one execution, bound to
`test` — and the gate silently measures unit tests only. That is precisely the "threshold met by
accident" failure FR-CICD-003 warns about, and it fails *open*, so nothing ever reports it.

E2E contributes nothing to the gate by design (FR-CICD-003; `platform-operations.md` OQ-002 resolved).

---

## 4. Git

Branch model, commit format and release triggers are
[ADR-0012](../decisions/0012-repo-strategy-polyrepo-submodules.md). The parts most often got wrong:

- **The base branch is `master`, in every repository.** Not `main`. Workflow triggers, branch
  protection and the `v*.*.*` tag rules all name `master`.
- Branches are `feat/`, `fix/`, `docs/`, `chore/` + description.
- Commits are [Conventional Commits](https://www.conventionalcommits.org/): `<type>(<scope>): <subject>`,
  subject ≤72 chars, imperative, no trailing period.
- **Cross-repo changes are separate branches per repo.** There is no atomic multi-repo commit; §5 is
  how the versions stay coherent.
- **Do not open pull requests** (ADR-0012 *Pull requests are suspended*, 2026-09-05). Branch, build,
  merge to `master` and delete the branch **within the same session**. Prefer `--ff-only`, so
  `master` stays linear. CI runs on push, so a direct merge is checked exactly as a PR was.

### Git hooks — `pre-push`, native, no husky

**CI is the gate.** It is the only thing that runs on every machine and the only thing that cannot be
skipped with `--no-verify`. Nothing below changes that; a hook is a fast-fail, never a substitute.

The local fast-fail is **one `pre-push` script per repository**, enabled with:

```bash
git config core.hooksPath .githooks
```

Committed, native shell, no dependency added. Each repo's runs what its CI runs first and cheapest —
`./mvnw spotless:check` and the compile (Error Prone and NullAway fail there), or
`npm run lint && npm run typecheck` in the frontend.

**Why `pre-push` and not `pre-commit`.** Commits in this project are constant — an agent makes many
per work item — and a pre-commit hook pays a JVM start on every one of them, which is how hooks come
to be bypassed. Pushes are rare: roughly one per work item, at the moment the work becomes visible to
CI and to anyone else. That is where the check belongs.

There is a second reason specific to how this project is worked. **The agent cannot push** — `git
push` is denied in `.claude/settings.json`, so pushing is always a human action. A `pre-push` hook
therefore catches what an agent left broken at the exact moment a person is about to publish it,
which is the most useful possible placement and costs nothing in the inner loop.

**Not husky.** In the three Java repositories it means adding a `package.json` to a Maven project to
get git hooks, which is a dependency and a toolchain for something `core.hooksPath` does natively. In
the frontend husky would be idiomatic and cheap — but one repository doing it differently is worse
than five doing it the same way, and `lint-staged`'s advantage (only touching staged files) is an
optimisation for a pre-commit hook we are not writing.

**The hook is a convenience, so it is allowed to be bypassed.** `--no-verify` when you know the
push is a WIP branch is fine. What is not fine is a green push whose CI then fails on formatting,
because that round trip costs a full turn to discover and another to fix.

---

## 5. Cross-repository dependencies

`turnbase-common` publishes `io.turnbase:turnbase-grpc`, consumed by both `turnbase-platform` and
`turnbase-game-host`. `turnbase-sdk` publishes `io.turnbase:turnbase-sdk`, consumed by
`turnbase-game-host` and by game developers.

**Consumers pin an exact released version**, through a property:

```xml
<properties>
  <turnbase-common.version>0.1.0</turnbase-common.version>
</properties>
```

**No `-SNAPSHOT` in a committed pom.** A SNAPSHOT dependency makes the build unreproducible — the
same commit compiles differently on Tuesday — and it hides breaking proto changes until they land
somewhere inconvenient.

**Bootstrap exception, before the first tag exists.** This rule assumes a release to pin against.
`turnbase-common` and `turnbase-sdk` publish only on a manual `v*.*.*` tag (§5 below,
[ADR-0012](../decisions/0012-repo-strategy-polyrepo-submodules.md) Release Strategy), and cutting that
tag is a human action — nothing in this project pushes one. The publish workflow itself is
`IMP-M0-11`, which **depends on** `IMP-M0-03`/`M0-04`. So the very first consumer skeletons cannot
pin a release: none exists, and the pipeline that would produce one has not been built yet.

Until `turnbase-common`'s first `v*.*.*` tag is cut, `IMP-M0-03` and `IMP-M0-04` pin
`<turnbase-common.version>` to its **current development version** (`0.1.0-SNAPSHOT` today), resolved
from the artifact `./mvnw install` puts in the local Maven repository — the same install step
`IMP-M0-01` already runs, not a new mechanism. This checks exactly what a consumer skeleton can check
at this point in the build order: the generated Java compiles and links against a real build of the
stubs. It does not check resolution from GitHub Packages, because nothing publishes there yet — that
half moves to `IMP-M0-11`, which stands up the publish workflow and is the item with something to
resolve it from.

**The follow-up is ordinary, not special-cased.** The first time `turnbase-common` is tagged and
`IMP-M0-11`'s workflow publishes it, `turnbase-platform` and `turnbase-game-host` each get a small
change bumping `<turnbase-common.version>` from the SNAPSHOT to the released version — the same "consumer
bump is where the compile break surfaces" step the *Promoting a change* paragraph below already
describes for every later release. The first release is not exempt from that step; it is only exempt,
until it exists, from needing one.

**CI needs the same install, since a runner starts with an empty local repository.**
`turnbase-platform`'s and `turnbase-game-host`'s workflows check out `turnbase-common` alongside
themselves and run `./mvnw install -DskipTests` in it before building, for as long as
`<turnbase-common.version>` is a bootstrap SNAPSHOT. This is the one point where a consumer's CI reads
outside its own repository, and it is deliberately temporary: the step is deleted, not adapted, in the
same change that bumps the version property to a real release, because from that point resolution is
an ordinary dependency fetch from GitHub Packages.

**`turnbase-common` is private (ADR-0012), so the checkout needs a credential — GitHub's default
`GITHUB_TOKEN` cannot read a different private repository under any organization setting.** The
credential is a **fine-grained personal access token, read-only on Contents, scoped to
`turnbase-common` only**, stored as the `TURNBASE_COMMON_PAT` secret in each bootstrap-window consumer
repo (`turnbase-platform` today; `turnbase-game-host` when `IMP-M0-04` reaches this same step). Not a
classic PAT (unscopable to one repo) and not the pusher's own account token (far broader than this
one clone needs). Provisioning the token is a human action — creating it means signing in to GitHub —
the same category as cutting a release tag. Deleted alongside the bootstrap install step once the
first real release lands, for the same reason: at that point resolution is an ordinary authenticated
fetch from GitHub Packages using the workflow's own token, not a second repository's source.

**The local loop**, when a proto change must be tried against a consumer before it is released:

```bash
cd turnbase-common && ./mvnw install                       # to the local repository
cd ../turnbase-platform && ./mvnw verify -Dturnbase-common.version=0.2.0-SNAPSHOT
```

A command-line override, not a profile and not an edit. Nothing to forget to revert.

**Promoting a change** is the two-step sequence ADR-0012 already implies, now with an order:
`turnbase-common` merges and tags → CI publishes → each consumer bumps the property in its own repo.
The consumer bump is where the compile break surfaces, which is the right place for it.

**The proto is copied, not shared.** `gamehost.proto` is authoritative in
[`../specs/internal-grpc/`](../specs/internal-grpc/); `turnbase-common` holds a **committed copy** at
the canonical buf-module path derived from the proto package (`turnbase.gamehost.v1`):

```
turnbase-common/src/main/proto/turnbase/gamehost/v1/gamehost.proto
```

`PACKAGE_DIRECTORY_MATCH` therefore holds and `turnbase-common`'s `buf.yaml` needs no lint exception.
The authoritative file stays flat in the spec tree beside its design doc, and *that* is the one
waiver. Copying the flat layout across would mean disabling a standard lint rule in the repository
that actually publishes the artifact, which is where it is worth having.

**Committed, not generated at build time** (ADR-0012, amended by IMP-GATE-02). `turnbase-common` must
build from a standalone clone — its CI checks out the submodule alone, not the superproject — so
nothing in its build may read a path outside the repository.

**Editing the copy is a defect.** The change belongs in the spec directory, and the copy is refreshed
from it in the parent, which is the only checkout holding both files:

```bash
scripts/sync-proto.sh            # refresh the copy from the authoritative file
scripts/sync-proto.sh --check    # fail if they differ; runs in the parent's pre-push hook
```

The guard is mechanical because the failure is not: two identical-looking protos diverge, both
repositories still compile, and the two services disagree on the wire.

**Generated Java lands under the repository root package**, `io.turnbase.grpc`, with the proto's own
package as the tail — `io.turnbase.grpc.gamehost.v1` (IMP-GATE-01). Keeping the version segment is
not decoration: a future `turnbase.gamehost.v2` has to generate into a package that can coexist with
v1 on one classpath, because both consumers will run them side by side through a migration.

---

## 6. What a repository must have

The floor, checked by `IMP-M0-01`…`M0-05` and `IMP-M0-11`:

| | Java repos | Frontend |
|---|---|---|
| Toolchain pinned | `.sdkmanrc` (`21.0.2-graalce`) | `.nvmrc` + `engines.node` |
| Wrapper committed | `./mvnw` | — |
| Format enforced | Spotless at `validate` | Prettier |
| Static analysis | Error Prone + NullAway (ADR-0015) | ESLint flat config, `typescript-eslint` strict |
| Strictness | `@NullMarked` at package level | `tsconfig` `strict: true` |
| Coverage | JaCoCo, merged, ≥70% | unit only, ≥70% |
| Build reproducible | exact dependency versions | exact pins, **no `^`** for Astryx (ADR-0013) |
| Supply chain | `dependabot.yml` (**frozen**, see below) + Trivy; **critical fails, lower reports** (FR-CICD-010) | same |
| Local fast-fail | `.githooks/pre-push` + `core.hooksPath` | same |
| CI workflow | build → test → coverage → scan → publish | + `tsc --noEmit`, production build |
| Container | Dockerfile | Dockerfile (static bundle) |

`turnbase-common` and `turnbase-sdk` publish artifacts rather than images, so their pipelines end at
publication (FR-CICD-001).

### Two things CI gets wrong on a repository's first push

Both cost `IMP-M0-01` a red pipeline, and neither reproduces locally.

- **GraalVM CE is set up by `graalvm/setup-graalvm`, not `actions/setup-java`.** The latter has no
  `graalvm-community` distribution and fails with *"No supported distribution was found for input
  graalvm-community"*. Use the same `21.0.2-graalce` the `.sdkmanrc` pins, so CI and a developer's
  shell run the same JDK rather than two that merely agree today.
- **`buf breaking` needs a baseline that exists.** It runs on every push in `turnbase-common`,
  against `.git#ref=HEAD~1` — which requires `fetch-depth: 0`, since a shallow checkout has no
  previous commit to compare with. This was gated to pull requests only until 2026-09-05, because on
  the commit that first adds a `.proto` the baseline is a tree with no protos and the error
  (`Module "path: "." had no .proto files`) names the module rather than the missing baseline. That
  window closed once the proto was on `master`, and under §4's suspended-PR workflow a PR-only gate
  would never fire at all. `buf lint` is cheap and always has an answer, so it runs on everything.

### Dependabot is frozen

**Version updates are off in all five repositories** (2026-09-05), via `open-pull-requests-limit: 0`
on every ecosystem — GitHub's documented switch for disabling them. Dependabot security updates were
already off in repository settings, so nothing opens a PR now. The trigger was volume: bumps arrived
weekly across five repositories and were merged at nothing like that rate, leaving a backlog of open
PRs and orphaned branches that cost more attention than the updates returned. Under §4 there is no
mechanism to merge them anyway — a bot's PR is a PR.

**The `dependabot.yml` files are kept, not deleted, and this is the point.** Their `ignore` entries
are the project's record of *why* five pins are deliberate — the protobuf-maven-plugin 5.x config
rewrite, the `typescript-eslint` peer range that caps TypeScript below 6.1, Astryx's Beta
codemod-only upgrades, jsdom's Node engine floor, the Espresso artifacts tied to a spike result.
That reasoning outlives the freeze; deleting the files would discard it and leave five pins looking
like neglect. **Keep landing new `ignore` entries in the same change as the pin they protect**, for
the same reason.

Re-enabling is restoring the limits, nothing else. Bumping a dependency while frozen is an ordinary
change on an ordinary branch.

**One trap survives the freeze, for whenever it lifts:** during the §5 bootstrap window, Dependabot's
own PRs structurally cannot pass CI. GitHub does not give a `pull_request`-triggered run opened by
Dependabot access to repository secrets — including `TURNBASE_COMMON_PAT` — even though an ordinary
push-triggered run on the same repository gets it, so every such PR against `turnbase-platform` or
`turnbase-game-host` fails on the bootstrap install step regardless of what it changes. It reads like
the dependency bump broke something when it did not. Apply anything legitimate by editing the pinned
version directly and pushing; do not wait for the check to go green.
