## Last Session Summary

**Date:** 2026-09-06 (session 29)

**IMP-M1-04 — Credential registration and login. DONE. 15 of 61 items complete** (the registry grew
by one this session — see the gate below). `POST /api/auth/register` and `POST /api/auth/login`
(`AuthController`, new `account` package). `UsernamePolicy` runs `input-validation.md`'s
canonicalization pipeline plus ICU4J `SpoofChecker` at `MODERATELY_RESTRICTIVE` for FR-AUTH-015's
single-script rule, computes the `getSkeleton(caseFold(NFC(username)))` uniqueness key, and rejects
the `guest-` prefix on that same skeleton (FR-AUTH-013). `CredentialPolicy` validates email
(FR-AUTH-002) and password (FR-AUTH-005) shape. Registration is one transaction inserting
`app_user`/`user_auth_method`/`user_privacy_settings`; a unique-index violation is mapped to the right
409 message (username vs. email) by matching the constraint name in Postgres's own error text, keeping
the driver's exception type at `runtime` scope. Passwords are Argon2id via
`Argon2PasswordEncoder(16, 32, 1, 19456, 2)`, `input-validation.md`'s explicit cost parameters.

**New `session.SessionService`** is the public API a principal-resolving flow calls to get a session —
`data-model-accounts.md` §3's atomic displace-then-insert (FR-SESS-001/002/003), retrying (bounded) on
the unique-index race between two concurrent logins. Both registration and login call it *after* their
own transaction commits, per this repo's commit-before-publish rule. The session cookie is
`turnbase_session` (new `IMP-GATE-27`, below), `HttpOnly; Secure; SameSite=Strict; Path=/`.

**Verified end-to-end.** `UsernamePolicyTest`/`CredentialPolicyTest` (unit) prove the validation and
skeleton rules directly. `AuthControllerIT` boots the real application against Testcontainers Postgres
and drives both endpoints over real HTTP: the three rows land correctly, duplicate username/email each
produce their own 409, the reserved prefix and a mismatched password confirmation both produce 400,
login succeeds by username or by email, a wrong password and an unknown identifier produce the
identical generic 401, and a second login revokes the first session (`revoked_reason = 'DISPLACED'`)
while exactly one session stays active — the FR-SESS-003 clause itself, checked against the database.
`./mvnw verify` and `-Pintegration` both green locally; CI green on `turnbase-platform` `master`
(build, 7m59s).

**Two gates, both opened and closed this session, before any code was written for either.**
`IMP-GATE-26`: the item's *Satisfies* claimed all of `FR-AUTH-001…016`, including six OAuth
requirements, but its *Done when* clause never mentioned OAuth and its read-list didn't carry the
document naming the OAuth client secret's config key. Fixed by retitling this item *Credential
registration and login*, narrowing it to `FR-AUTH-001…006, 011, 013…015`, and adding **`IMP-M1-10`**
(Google OAuth registration and login, `READY` off this item) to own `FR-AUTH-007…012/016` and
`VW-OAUTHCOMP-001…002` — pushing the registry to **61 live items**. `IMP-GATE-27`: no document in the
corpus named the session cookie itself, only its `httpOnly`/`Secure`/`SameSite=Strict` properties, and
this item's read-list was also missing `rest-conventions.md`'s Authentication section entirely. Fixed
by naming it there — `turnbase_session`, `Path=/` — as a fixed protocol constant every future reader
(the `IMP-M2-02` STOMP handshake, the `IMP-M5-03` SSE endpoint, any auth filter) must agree on.

**Two runtime dependencies neither `input-validation.md` nor `conventions.md` named, both transitive
gaps in libraries the documents do name rather than choices made here.** `Argon2PasswordEncoder`
delegates to Bouncy Castle's Argon2 implementation at runtime — `spring-security-crypto` keeps
`bcprov-jdk18on` optional — so registration threw `NoClassDefFoundError` until it was added explicitly
(pinned `1.85.2`, `runtime` scope). ICU4J's `SpoofChecker` API shape (`failsChecks`, `getSkeleton`,
`Builder.setChecks`/`setRestrictionLevel`) had to be read from the real `78.3` jar rather than assumed.

---
## Next Priorities

**Phase 1 is under way. Work from [`docs/implementation/INDEX.md`](docs/implementation/INDEX.md), not
from this file.** The registry holds **61 live work items** (IMP-M6-07 is cancelled), each with a
read-list, dependencies, the requirement IDs it satisfies and a done-when clause; this section only
says which of them to pick up.

**IMP-GATE-26** (`IMP-M1-04`, opened and closed 2026-09-06, session 29) — the item's *Satisfies*
claimed the full `FR-AUTH-001…016` range, including six OAuth-only requirements
(`FR-AUTH-007…012, 016`) and `VW-OAUTHCOMP-001…002`, but its *Done when* clause never mentioned OAuth
and its read-list didn't even carry the document naming the OAuth client secret's config key.
Fixed: `IMP-M1-04` retitled *Credential registration and login* and narrowed to `FR-AUTH-001…006, 011,
013…015`; the OAuth round trip (consent redirect, code exchange, signed `state`, the FR-AUTH-016
email-collision challenge-and-link path) is new item **`IMP-M1-10`**, `READY` off `IMP-M1-04`, which
is now `DONE` (see *Last Session Summary*).

**IMP-GATE-28** (`IMP-M1-06`, opened and closed 2026-09-08, session 30) — `IMP-M1-06`'s *Satisfies*
claimed `FR-SESS-010` in full, but its actual duty (closing a session's live WebSocket/SSE connections
on revocation) needs a connection registry that doesn't exist yet — `IMP-M2-02` and `IMP-M5-03` are
both still `READY`, and `IMP-M5-03` didn't claim `FR-SESS-010` at all despite SSE being one of the two
connection types the requirement names. Fixed: `IMP-M1-06` narrowed to `FR-SESS-001…004, FR-SESS-011`
plus publishing a `SessionRevokedEvent`; `IMP-M2-02` and `IMP-M5-03` each gained the corresponding
close-on-revocation `Done when` clause (`IMP-M5-03` also gained `FR-SESS-010` in *Satisfies* and
`IMP-M1-06` as a dependency, for the event type).

**IMP-GATE-27** (`IMP-M1-04`, opened and closed 2026-09-06, session 29) — no document in the corpus
named the session cookie itself, only its `httpOnly`/`Secure`/`SameSite=Strict` properties
(`user-accounts.md` CON-004); `rest-conventions.md`'s Authentication section, the natural home, was
also missing from `IMP-M1-04`'s read-list. Fixed: `rest-conventions.md` now names it —
`turnbase_session`, `Path=/` — as a fixed constant every server-side reader (the future STOMP
handshake, SSE endpoint, and any authenticated-route filter) must agree on; read-list corrected.

**Before starting any of them: no pull requests** (ADR-0012, amended 2026-09-05). Branch, build,
merge to `master`, delete the branch — all within one session. Dependabot is frozen, so nothing
arrives on its own any more; a dependency bump is now an ordinary change on an ordinary branch.

**Progress: 15 of 61 done** — `IMP-M0-01` (gRPC stubs, `turnbase-common`), `IMP-M0-02` (SDK
build-and-publish floor, `turnbase-sdk`), `IMP-M0-03` (Platform Monolith skeleton,
`turnbase-platform`), `IMP-M0-04` (Game Host skeleton, `turnbase-game-host`), `IMP-M0-05`
(Frontend skeleton, `turnbase-frontend`), `IMP-M0-06` (Flyway baseline, `turnbase-platform`),
`IMP-M0-07` (local stack compose profile, `turnbase-platform`), `IMP-M0-08` (Helm chart,
`turnbase-platform`), `IMP-M0-09` (configuration and secrets wiring, `turnbase-platform` +
`turnbase-game-host`), `IMP-M0-10` (observability baseline, `turnbase-platform` +
`turnbase-game-host`), `IMP-M0-11` (CI/CD workflows, all five repos), `IMP-M3-12` (FE GDK
client, `turnbase-sdk`), `IMP-M1-01` (error model, REST conventions, validation harness,
`turnbase-platform`), `IMP-M1-03` (JWT key set, issuance, rotation, `turnbase-platform`) and
`IMP-M1-04` (credential registration and login, `turnbase-platform`), all pushed and green in CI.
**No work item is gated**, and all 23 readiness blockers remain closed, so an item's status is
whatever its own dependencies imply.

**Next up in M1**: `IMP-M1-05` (guest minting and purge), `IMP-M1-06` (session lifecycle and
displacement), `IMP-M1-07` (profiles and privacy settings) and `IMP-M1-10` (Google OAuth) are all
`READY` off `IMP-M1-04`. `IMP-M1-02` (rate limiter) remains independently `READY` off `IMP-M1-01`.
`IMP-M1-06` is the one that actually closes the loop `IMP-M1-04` opened — FR-SESS-004's 401 shape for
a displaced request, FR-SESS-010's live-connection close, and FR-SESS-011 logout are still unbuilt;
`IMP-M1-04` only proved the displacement write itself, at the database, per its own narrowed
Done-when.

**IMP-GATE-25** (`IMP-M0-11`, opened and closed 2026-09-05) — `game-development-experience.md`
CON-003 and ADR-0012's Release Strategy commit `turnbase-sdk` to Maven Central + npm, but no document
names a license for it, and Maven Central's publish validation rejects a POM with no `<licenses>`.
Raised to the project owner (a real decision, not a CI mechanic), who deferred it. Fixed: both
documents now say the Maven Central/npm publish is deferred until a license is chosen. Only the Maven
half gets an interim home (GitHub Packages, same as `turnbase-common`) — GitHub Packages' npm registry
requires a scope matching the `turnbase-platform` org, which `@turnbase/gdk` (FR-FEGDK-007) cannot
satisfy, so the npm package stays unpublished by any registry until the public one is available.

**IMP-GATE-24** (`IMP-M0-11`, opened and closed 2026-09-05) — FR-CICD-007/008 require a tag-triggered
production deployment and rollback, but ADR-0001 defers all cloud/production deployment to post-MVP
and names the local Docker Desktop cluster as the only CI-exercised deploy path — no production target
exists for a workflow to reach. Fixed: FR-CICD-007/008 marked deferred to post-MVP in
`platform-operations.md`; ADR-0001's *Affected documents* updated to record it. `IMP-M0-11`'s own
*Satisfies*/*Done when* narrowed to match — FR-CICD-006 (image push to a registry) stands.

**IMP-GATE-23** (`IMP-M0-11`, opened and closed 2026-09-05) — `platform-operations.md` FR-CICD-002/003
and OQ-002's resolution gated the pipeline on a **pull request** ("the PR cannot be merged...", "PR
feedback loops"), but ADR-0012 (amended 2026-09-05) suspends pull requests project-wide, so a
`pull_request` trigger would never fire. Fixed: FR-CICD-002 retitled *Pre-merge checks* and reworded
to gate on push to `master`; FR-CICD-003 and OQ-002 updated to match. No workflow code changed — the
five repos' `build.yml` files already run on push.

**`IMP-M0-11` is now DONE.** `IMP-M0-12` (seed data) stays not-`READY` — it depends on `IMP-M4-03`,
which has not been picked up. **M0 is otherwise finished, and `IMP-M1-01`/`IMP-M1-03` are now DONE
too.** Next up in M1 (accounts and sessions — see *Then, in dependency order* below): `IMP-M1-04`
(credential registration and login — narrowed from *Registration and login* by IMP-GATE-26; OAuth is
now the separate `IMP-M1-10`), `READY` off both `IMP-M1-01` and `IMP-M1-03`, is the natural next pick —
it is the first item to actually create an `app_user`/`user_session` row through an endpoint rather
than a test fixture. `IMP-M1-02` (rate limiter, Tiers 1–5), `READY` off `IMP-M1-01`, remains
independently pickable if `IMP-M1-04` is deferred. `IMP-M0-10` left five small
obligations on later items, each recorded as a sentence in that item's own section rather than a
gate: `IMP-M2-02` exposes `turnbase_websocket_connections_active`,
`IMP-M3-09`/`IMP-M2-10`/`IMP-M3-08` wire
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
