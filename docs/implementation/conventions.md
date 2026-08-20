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
**before opening a PR**, not after CI rejects it — a bounced pipeline costs a full session turn to
discover and another to fix.

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

- Error Prone needs `-XDcompilePolicy=simple` and `--should-stop=ifError=FLOW`, plus `--add-exports`
  flags for `jdk.compiler` — the same family of setup as google-java-format's, and they go in the
  same `.mvn/jvm.config`.
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
containers and the PR pipeline stops being run. Start containers **once per JVM** — a static
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
- **Cross-repo changes are separate PRs per repo.** There is no atomic multi-repo commit; §5 is how
  the versions stay coherent.

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

**The local loop**, when a proto change must be tried against a consumer before it is released:

```bash
cd turnbase-common && ./mvnw install                       # to the local repository
cd ../turnbase-platform && ./mvnw verify -Dturnbase-common.version=0.2.0-SNAPSHOT
```

A command-line override, not a profile and not an edit. Nothing to forget to revert.

**Promoting a change** is the two-PR sequence ADR-0012 already implies, now with an order:
`turnbase-common` merges and tags → CI publishes → each consumer bumps the property in its own PR.
The consumer bump is where the compile break surfaces, which is the right place for it.

**The proto is copied, not shared.** `gamehost.proto` is authoritative in
[`../specs/internal-grpc/`](../specs/internal-grpc/); `turnbase-common` copies it into
`src/main/proto/` at build time (ADR-0012). Editing the copy is a defect — the change belongs in this
repository's spec directory, and the copy is refreshed from it.

**The copy takes the canonical buf-module path**, derived from the proto package
(`turnbase.gamehost.v1`):

```
turnbase-common/src/main/proto/turnbase/gamehost/v1/gamehost.proto
```

so `PACKAGE_DIRECTORY_MATCH` holds and `turnbase-common`'s `buf.yaml` needs no lint exception. The
authoritative file stays flat in the spec tree beside its design doc, and *that* is the one waiver.
Copying the flat layout across would mean disabling a standard lint rule in the repository that
actually publishes the artifact, which is where it is worth having.

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
| Supply chain | `dependabot.yml` + Trivy; **critical fails, lower reports** (FR-CICD-010) | same |
| Local fast-fail | `.githooks/pre-push` + `core.hooksPath` | same |
| CI workflow | build → test → coverage → scan → publish | + `tsc --noEmit`, production build |
| Container | Dockerfile | Dockerfile (static bundle) |

`turnbase-common` and `turnbase-sdk` publish artifacts rather than images, so their pipelines end at
publication (FR-CICD-001).
