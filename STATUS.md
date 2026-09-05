## Last Session Summary

**Date:** 2026-09-05 (session 25)

**IMP-M0-10 — Observability baseline, `turnbase-platform` + `turnbase-game-host`. DONE. 11 of 60
items complete.** Both services now export Prometheus metrics (`/actuator/prometheus`, management
port only), emit Logback JSON to stdout, and carry the OpenTelemetry Java agent for tracing.
`BusinessMetricsConfig` polls the four FR-MET-003 gauges from Postgres every 30 seconds — buildable
now because the tables already exist from `IMP-M0-06`, independent of the room/social features that
will eventually populate them. `CorrelationIdFilter` is the HTTP-boundary MDC entry point; a
`ClientInterceptor`/`ServerInterceptor` pair (duplicated per repo, not shared code — the wire
contract is the plain metadata key name) copies the five correlation IDs across a gRPC hop, proven
against a controlled in-process call since no live gRPC client exists in the platform yet. Prometheus
scrapes both services and evaluates three alert rules (`HighErrorRate`, `HighLatencyP95`,
`DbPoolSaturated`); Alertmanager renders its webhook receiver in or out at container start with `sed`,
since the image has no environment-variable expansion. Two of `observability.md` §5's four Grafana
dashboards are built; the other two wait on signals that don't exist yet. CI green on both repos —
`./mvnw verify -Pintegration` — and the whole thing was also verified against the real `docker compose`
stack end to end: a live HTTP request produces a trace visible in Tempo, the log line's `trace_id`
matches it, both scrape targets are `up`, all three rules evaluate, and both Alertmanager render
branches were checked directly.

### The item's own Done-when clause was wrong before any code was written

`IMP-M0-10`'s *Done when* required proving trace propagation "across the REST → gRPC boundary" — but
neither service has one yet: `turnbase-platform` issues no outbound gRPC call and runs no gRPC
server, and the Game Host's one outbound call (`Register`) isn't triggered by an inbound REST request.
That request chain doesn't exist before `IMP-M3-05`. Same shape as `IMP-GATE-08`, closed as
**IMP-GATE-18**: the agent-and-Tempo check for a real HTTP request stayed (genuine, but HTTP-only for
now); the cross-process claim narrowed to the correlation-ID interceptor pair, proven against a
controlled call; the live, request-shaped, agent-instrumented check moved to `IMP-M3-05`, which
gained a Done-when clause for it. `IMP-M0-10`'s own *Satisfies* line was narrowed to match — five
requirements this item genuinely cannot build yet (`FR-MET-002`, `FR-MET-005`,
`FR-ALERT-003/006/007`, plus the Game Host's own `platform-architecture.md` `FR-OBS-*`) were
explicitly handed to the items that will have the signal source: `IMP-M2-02`, a new `conventions.md`
§7 convention, and `IMP-M3-09`/`IMP-M2-10`/`IMP-M3-08` respectively.

### Four more gates, found only by running the thing

**IMP-GATE-19** — `observability.md` §3's own worked JSON example showed `"sessionId": null` two
sentences after the prose next to it said correlation IDs are "omitted when absent rather than
written as empty strings." The example just contradicted its own rule. Fixed: the example now omits
the key.

**IMP-GATE-20** — `observability.md` §2.1's literal SQL for `turnbase_friend_requests_pending`
filtered on `WHERE status = 'PENDING'`, but the baseline `friend_request` table (`IMP-M0-06`, already
`DONE`) has no `status` column at all — the query would fail against the real schema. Fixed: an
unfiltered `count(*)`, plus a sentence explaining why that's correct rather than a shortcut — a
pending request's row existing *is* what "pending" means in this schema; accepting one deletes it and
inserts a `friendship` row, declining or expiring one just deletes it.

**IMP-GATE-21** — found only by actually running the compose stack and reading the resulting log
line: the OpenTelemetry Java agent's `logback-mdc` instrumentation — the mechanism `observability.md`
§3 itself credits with the injection — writes `trace_id`/`span_id` (OpenTelemetry semantic
conventions for log correlation, not a project choice), not the camelCase `traceId`/`spanId` the
doc's worked example and the Grafana derived-field regex both assumed. Fixed the doc and the two
committed config files that repeated the wrong spelling (`promtail-config.yaml`,
`datasources.yaml`) — the five project-owned correlation IDs (`requestId` etc.) were never affected.

**IMP-GATE-22** — also found only by running the stack: `tempo.yaml` (`IMP-M0-08`) left the OTLP
receivers on Tempo's own default bind, which is loopback — unreachable from another container even
though the port is published on the compose network, the same class of bug `IMP-GATE-14` already
found for the management port. Every span export failed with `Connection refused` and zero traces
ever reached Tempo until this was fixed with an explicit `endpoint: 0.0.0.0:4317`/`:4318`.

**None of the four would have been caught by reading, and none by `check-corpus.py`.** They surfaced
only because something finally exported a real span and read the log line it produced — the same
lesson `IMP-GATE-01…03` taught on the first item: a skeleton compiling against the documents is a
different test than a document being internally consistent.

### One bug fixed outside this item's scope, because it blocked verifying this item's own work

`turnbase-platform`'s Dockerfile (`IMP-M0-03`) never `chown`ed `/app` before switching to the
non-root `turnbase` user, so `JwtKeySetConfig`'s (`IMP-M0-09`) local key persistence failed with
`AccessDeniedException` on every single boot of the real image — a bug that would have blocked
*every* deployment the moment anyone actually ran the container, not something specific to
observability. Nobody had run the real Docker image end-to-end before this session; earlier
verification stopped at unit/integration tests and Helm chart validation. Fixed with a one-line
`chown` in the same `RUN` that creates the user. Not a specification defect — no document
contradicted another — just an untested path, fixed because it stood between this session and
verifying its own Done-when clause.

### Two design decisions worth remembering for the items that pick up the deferred pieces

- **The polled-gauge pattern doesn't need its feature to exist.** `turnbase_rooms_active` and
  friends are pure SQL against tables the baseline migration already created — the fact that no
  Java code populates `room` rows yet doesn't block exposing (and correctly reading zero from) the
  metric. The same reasoning is why `IMP-M3-08`'s teardown-age gauge, `IMP-M2-10`'s duty counters and
  `IMP-M3-09`'s failure-rate signal were *not* pulled forward the same way: their underlying tables
  either don't exist yet or their exact metric name isn't specified anywhere in this item's
  read-list, and inventing one would have been exactly the kind of silent decision `spec-defect`
  exists to stop.
- **A gRPC boundary needs two interceptors that never share code**, one per repo, because
  `turnbase-common`'s published stubs deliberately carry no transport or support code
  (`conventions.md` §5) — the wire contract is the plain string metadata key name, and each side
  just has to agree on the spelling.

---
## Next Priorities

**Phase 1 is under way. Work from [`docs/implementation/INDEX.md`](docs/implementation/INDEX.md), not
from this file.** The registry holds **60 live work items** (IMP-M6-07 is cancelled), each with a
read-list, dependencies, the requirement IDs it satisfies and a done-when clause; this section only
says which of them to pick up.

**Before starting any of them: no pull requests** (ADR-0012, amended 2026-09-05). Branch, build,
merge to `master`, delete the branch — all within one session. Dependabot is frozen, so nothing
arrives on its own any more; a dependency bump is now an ordinary change on an ordinary branch.

**Progress: 11 of 60 done** — `IMP-M0-01` (gRPC stubs, `turnbase-common`), `IMP-M0-02` (SDK
build-and-publish floor, `turnbase-sdk`), `IMP-M0-03` (Platform Monolith skeleton,
`turnbase-platform`), `IMP-M0-04` (Game Host skeleton, `turnbase-game-host`), `IMP-M0-05`
(Frontend skeleton, `turnbase-frontend`), `IMP-M0-06` (Flyway baseline, `turnbase-platform`),
`IMP-M0-07` (local stack compose profile, `turnbase-platform`), `IMP-M0-08` (Helm chart,
`turnbase-platform`), `IMP-M0-09` (configuration and secrets wiring, `turnbase-platform` +
`turnbase-game-host`), `IMP-M0-10` (observability baseline, `turnbase-platform` +
`turnbase-game-host`) and `IMP-M3-12` (FE GDK client, `turnbase-sdk`), all pushed and green in CI.
**No work item is gated**, and all 23 readiness blockers remain closed, so an item's status is
whatever its own dependencies imply.

**Next up: `IMP-M0-11` (CI/CD workflows, all five repos) and `IMP-M0-12` (seed data, gated on
`IMP-M4-03`, not yet `READY`)** — `M0-11` is `READY` now, depending only on `M0-01…05`.
`IMP-M0-06`'s completion already unblocked `IMP-M4-02` (manifest schema validation,
`turnbase-platform`). `IMP-M0-10` left five small obligations on later items, each recorded as a
sentence in that item's own section rather than a gate: `IMP-M2-02` exposes
`turnbase_websocket_connections_active`, `IMP-M3-09`/`IMP-M2-10`/`IMP-M3-08` wire
`GameSessionFailureRate`/`ReconciliationRepairsPersist`/`TeardownOwed`, and any item adding a new
Redis usage site tags it per `conventions.md` §7. None of these block anything — they surface when
that item's own Done-when is checked.

**IMP-GATE-17** (`IMP-M0-09`, opened and closed 2026-09-05) — `turnbase.gamehost.grpc.port`, shipped
in `IMP-M0-04` and already read live by `GrpcServerLifecycle`, was never added to
`local-environment.md` §7.8, contradicting §7's own "whole tunable surface" claim — the same class
of gap IR-24 closed for `turnbase.room.spectator-capacity`. Fixed: added to §7.8 with its existing
default (`9090`).

**IMP-GATE-18** (`IMP-M0-10`, opened and closed 2026-09-05) — the Done-when clause required proving
trace propagation "across the REST → gRPC boundary," but no such boundary exists yet: `platform`
issues no outbound gRPC call and runs no gRPC server, and the Game Host's one outbound call
(`Register`) isn't triggered by an inbound REST request — that request chain doesn't exist before
`IMP-M3-05`. Fixed: narrowed to proving the interceptor mechanism against a controlled gRPC call, with
the live cross-repo check moved to `IMP-M3-05`. `IMP-M0-10`'s *Satisfies* was also narrowed to what it
actually builds — `FR-MET-002`, `FR-MET-005`, `FR-ALERT-003/006/007` and the Game Host's own
`platform-architecture.md` `FR-OBS-*` are deferred to `IMP-M2-02`, a new `conventions.md` §7 rule, and
`IMP-M3-09`/`IMP-M2-10`/`IMP-M3-08` respectively, each of which now carries the corresponding clause.

**IMP-GATE-19** (`IMP-M0-10`, opened and closed 2026-09-05) — `observability.md` §3's own worked
example showed `"sessionId": null` beside prose stating correlation IDs are "omitted when absent
rather than written as empty strings." Fixed: the example now omits the key.

**IMP-GATE-20** (`IMP-M0-10`, opened and closed 2026-09-05) — `observability.md` §2.1's SQL for
`turnbase_friend_requests_pending` filtered on a `status` column `friend_request` does not have
(`IMP-M0-06`'s baseline). Fixed: an unfiltered `count(*)` — a pending request's row existing is what
"pending" means in this schema; accepting or declining one deletes the row.

**IMP-GATE-21** (`IMP-M0-10`, opened and closed 2026-09-05) — found by actually running the stack:
`observability.md`'s JSON log example and Grafana derived-field regex used camelCase
`traceId`/`spanId`, but the OpenTelemetry Java agent's `logback-mdc` instrumentation — the mechanism
the doc itself credits — writes `trace_id`/`span_id` (OTel semantic conventions, not configurable).
Fixed: doc, `promtail-config.yaml` and `datasources.yaml` all changed to `trace_id`/`span_id`.

**IMP-GATE-22** (`IMP-M0-10`, opened and closed 2026-09-05) — also found by running the stack:
`tempo.yaml` (`IMP-M0-08`) left the OTLP receivers on Tempo's default loopback bind, so every span
export failed with `Connection refused` and zero traces ever reached Tempo — same bind-address trap
class as `IMP-GATE-14`. Fixed: explicit `endpoint: 0.0.0.0:4317`/`:4318`.

**IMP-GATE-16** (`IMP-M0-09`, opened and closed 2026-09-05) — `secrets-and-configuration.md`'s
`local`/`test,e2e`/`Kubernetes` split for the JWT key set cannot be implemented by Spring profile
alone: `local-environment.md` §4 runs the canonical Kubernetes chart under the identical
`spring.profiles.active=local` compose uses, but the two rows need opposite behaviour — generate and
persist to a file under compose (one instance), fail if absent under Kubernetes (the chart's own HPA
can run more than one replica). Fixed: a new non-secret switch, `turnbase.auth.jwt-key-set-required`
(`local-environment.md` §7.4, default `false`), set to `true` only by the Helm chart's ConfigMap;
`secrets-and-configuration.md` §3.1 now states this is the actual mechanism and profile is not.

**IMP-GATE-15** (`IMP-M0-09`, opened and closed 2026-09-05) — the *Done when* clause requires a
Kubernetes Secret path for every secret, including the JWT key set, but
`secrets-and-configuration.md` §3.1 named none: it said only "Supplied; startup fails if absent," and
§7 deliberately excludes secrets by design, so there was nowhere else it could be named either.
Fixed: §3.1 now names `TURNBASE_JWT_KEY_SET` (`turnbase.auth.jwt-key-set`), one JSON-valued
environment variable carrying the whole key set in §3.2's own shape.

**IMP-GATE-14** (`IMP-M0-07`, opened and closed 2026-09-05) — `local-environment.md` §1 said
compose achieves the loopback-only management port by setting `management.server.address =
127.0.0.1` *inside* the container, with the published port doing the rest — but a Docker published
port always forwards to the container's bridge interface, never its loopback, so a listener bound
that way is unreachable through its own published port regardless of the host-side bind. Proven
live: the container refused every host connection with the address set, and answered normally with
it unset. `IMP-M0-03`/`IMP-M0-04`'s "verified live" claims never exercised a real Docker
port-publish round trip. Fixed: §1 and §7.9 now say the app listens on all interfaces in both
profiles; compose's restriction is the published port's own host-side bind. No application code
changed (`MANAGEMENT_SERVER_ADDRESS` already defaults to unset); only stale comments and
`docker-compose.yml` were corrected.

**IMP-GATE-13** (`IMP-M0-07`, opened and closed 2026-09-05) — ADR-0011 §6 requires the Postgres
init script to create `pg_trgm` and `btree_gin` as superuser (the baseline migration's own
`CREATE EXTENSION IF NOT EXISTS` for both then succeeds as a no-op), but
`secrets-and-configuration.md` §4's actual `01-roles.sql` content created only `pgcrypto`. Running
the real compose stack — the first thing to migrate as the actual unprivileged `turnbase_app` role
rather than a Testcontainers superuser — failed outright with `permission denied to create
extension "pg_trgm"`. Fixed: §4's script (and `deploy/compose/initdb/01-roles.sql`) now creates all
three extensions; the baseline migration file needed no change, verified.

**IMP-GATE-12** (`IMP-M0-07`/`IMP-M0-08`, opened and closed 2026-09-05) — both items' `Repo` field
said "this repo" (the root `turnbase` landing repo), but `local-environment.md` §4 roots the whole
deploy tree — compose files, Helm chart — at `turnbase-platform/deploy/…`, and ADR-0012 describes
`turnbase` itself as holding only docs, specs and submodule refs, no deploy artifacts. Fixed: both
items' `Repo` corrected to `turnbase-platform`, matching the spec and the ADR.

**IMP-GATE-11** (`IMP-M0-06`, opened and closed 2026-09-05) — `schema-migrations.md` §5 names
`shedlock` as a baseline table but no document supplied its columns. Fixed: §5 now states the DDL,
which is ShedLock's own fixed schema, not a TurnBase design choice.

**IMP-GATE-10** (`IMP-M0-06`, opened and closed 2026-09-05) — the *Done when* clause named the
baseline file `V1__baseline.sql`, contradicting ADR-0011 §5 and `schema-migrations.md` §§1–2, which
mandate timestamp-based naming and both already name the real file `V202608091200__baseline.sql`.
Fixed: the registry entry (the one document that had it wrong) now names
`V202608091200__baseline.sql` throughout.

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
