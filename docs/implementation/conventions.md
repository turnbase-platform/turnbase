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

**TypeScript** is Prettier + ESLint per `platform-operations.md` FR-CICD-011, with `tsc --noEmit` in
the same pipeline step. Same principle: Prettier writes, ESLint complains.

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

**No git hooks, and specifically no husky.** CI is the gate, because it is the only thing that runs
on every machine and cannot be skipped with `--no-verify`. A pre-commit hook would also start a JVM
on every agent commit, which in this project is constantly. If a local fast-fail is ever wanted, the
right form is a single `pre-push` script under `core.hooksPath` — native shell, committed, no npm
dependency added to a Maven repository.

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

---

## 6. What a repository must have

The floor, checked by `IMP-M0-01`…`M0-05` and `IMP-M0-11`:

| | Java repos | Frontend |
|---|---|---|
| Toolchain pinned | `.sdkmanrc` (`21.0.2-graalce`) | `.nvmrc` + `engines.node` |
| Wrapper committed | `./mvnw` | — |
| Format enforced | Spotless at `validate` | Prettier + ESLint in CI |
| Coverage | JaCoCo, merged, ≥70% | unit only, ≥70% |
| Build reproducible | exact dependency versions | exact pins, **no `^`** for Astryx (ADR-0013) |
| CI workflow | build → test → coverage → scan → publish | + `tsc --noEmit`, production build |
| Container | Dockerfile | Dockerfile (static bundle) |

`turnbase-common` and `turnbase-sdk` publish artifacts rather than images, so their pipelines end at
publication (FR-CICD-001).
