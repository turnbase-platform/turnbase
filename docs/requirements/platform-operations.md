# Platform Operations Requirements

This document defines operational requirements for the TurnBase platform: service topology, availability targets, observability standards, CI/CD pipeline, data retention, and deployment model. It complements `platform-architecture.md`, which covers game execution infrastructure specifically.

## Related Documents

- `platform-architecture.md` — Game Host service, Orchestration logic, game execution infrastructure
- `game-contracts.md` — Platform ↔ game communication protocol
- `user-accounts.md` — Guest account lifetime, session management
- `notifications-invitations.md` — Notification retention policy
- `../decisions/INDEX.md` — ADR-0001 (local-first platform), ADR-0002 (WebSocket room affinity), ADR-0003 (availability target), ADR-0011 (schema migrations)
- `../specs/deployment/INDEX.md` — local environment and service topology, schema migrations, secrets and configuration
- `../specs/deployment/observability.md` — the wiring for FR-OBS-*, FR-MET-*, FR-TRACE-* and FR-ALERT-*
- `../specs/deployment/load-testing.md` — how NFR-LOAD-001…004 are measured (§7) and where the load-test runs report them

---

## Stakeholders

| Role | Description |
|------|-------------|
| Platform SRE / Ops | Monitors service health, responds to incidents, manages deployments |
| Platform Developer | Consumes CI/CD pipelines, reads structured logs, ships features |
| Third-Party Game Developer | Depends on platform API availability and stability |
| End User | Indirectly affected by availability, latency, and reliability of all platform services |

---

## Service Topology

TurnBase's backend consists of two independently deployable units:

| Service | Description |
|---------|-------------|
| **Platform Monolith** | Single deployable Spring Boot application containing all platform domain logic: user accounts, authentication, room management, game catalog, notifications, friend system, game history, leaderboards, and the WebSocket Gateway. Also contains the Orchestration logic (session routing, action queuing, effect delivery) previously described as the "Orchestration Service" in `platform-architecture.md`. |
| **Game Host** | Separate deployable service running GraalVM + Truffle. Executes sandboxed game code, manages Truffle contexts and session state. Independently scalable due to distinct runtime and resource profile. Fully specified in `platform-architecture.md`. |

The Platform Monolith communicates with the Game Host over gRPC. All other inter-domain communication is in-process within the monolith.

**Note:** Earlier requirements documents (e.g., `game-rooms.md`, `platform-architecture.md`) use the term "Orchestration Service" to describe what is now the Orchestration domain within the Platform Monolith. These references are logically equivalent; the boundary is a package/module boundary, not a process boundary.

### WebSocket Scaling — Room Affinity

The WebSocket Gateway is part of the Platform Monolith. WebSocket scaling uses **room affinity** (ADR-0002): all connections for a given room are handled by a single monolith instance, selected at connection time by routing on `roomId` at the ingress.

- Because every connection for a room lives on one instance, the Orchestration logic delivers effects and events to their recipients in-process — there is no cross-instance routing.
- Ordering and consistency for a room are guaranteed by that single owning instance.
- Redis is used for game-state persistence and crash recovery (see `platform-architecture.md`), **not** for routing WebSocket traffic between instances.

For the MVP the platform runs as a single local instance (ADR-0001), so affinity is trivially satisfied; the `roomId`-based ingress rule becomes relevant only in a future multi-instance deployment.

**Ownership is a lease-gated claim, not a permanent assignment** ([ADR-0008](../decisions/0008-room-ownership-lifecycle.md)). Each instance maintains a short-lived liveness lease; a room may be claimed by another instance only once the incumbent's lease has expired, and a room may sit unowned until a client returns or reconciliation adopts it. Two consequences are operational rather than architectural, and are requirements below: the ingress must treat the affinity hint as a *hint* and fall back to normal load balancing when the named instance is not in the ready set (FR-DEPLOY-002), and an instance must **release** its rooms on graceful shutdown rather than letting them expire (FR-DEPLOY-001). The single-instance MVP exercises this path on every restart of the local stack, so it is continuously tested rather than dormant.

---

## Functional Requirements

### Observability — Structured Logging

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-OBS-001 | Structured log format | All platform services must emit logs as structured JSON. Human-readable plain-text logs are not acceptable in production. | Must |
| FR-OBS-002 | Required log fields | Every log entry must include: timestamp (ISO 8601), severity level, service name, and a message. Entries scoped to a request, session, user, or game must include the relevant correlation IDs (see FR-OBS-003). | Must |
| FR-OBS-003 | Correlation IDs | The following IDs must be included in all log entries where applicable: `requestId` (per HTTP request or WebSocket message), `userId`, `sessionId` (game session), `roomId`, `gameId`. Correlation IDs must be propagated to all downstream calls, including gRPC calls to the Game Host. | Must |
| FR-OBS-004 | Log levels | Services must use standard severity levels: TRACE, DEBUG, INFO, WARN, ERROR. Production deployments must default to INFO. Log level must be adjustable at runtime without restart. | Must |
| FR-OBS-005 | No sensitive data in logs | Logs must never contain passwords, JWT tokens, session secrets, or personally identifiable information beyond user IDs. | Must |

### Observability — Metrics

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-MET-001 | HTTP request metrics | The Platform Monolith must expose request count, latency histogram (p50, p95, p99), and error rate per endpoint. Provided automatically via Spring Boot Actuator + Micrometer. | Must |
| FR-MET-002 | WebSocket connection metrics | The Platform Monolith must expose the count of active WebSocket connections as a metric. | Must |
| FR-MET-003 | Business metrics | The Platform Monolith must expose: active room count, active game session count, registered user count (updated periodically, not per-request), and friend request queue depth. | Should |
| FR-MET-004 | Database metrics | The Platform Monolith must expose PostgreSQL connection pool utilization, query latency histogram, and error count. | Must |
| FR-MET-005 | Redis metrics | The Platform Monolith must expose Redis operation latency and error count, dimensioned by the concerns that share the instance: **game-state persistence and the action queue**, **room ownership leases** (ADR-0008), and application-level use including rate-limit counters. Redis is **not** used for WebSocket pub/sub — effect fan-out is in-process under room affinity (ADR-0002) — so there is no pub/sub dimension to measure. Lease operations are called out separately because their latency bounds a correctness property (lease renewal against a 10-second TTL), not merely a performance one. | Must |
| FR-MET-006 | JVM metrics | All JVM-based services must expose standard JVM metrics: heap usage, GC pause duration and frequency, thread count. Provided automatically via Micrometer JVM instrumentation. | Must |
| FR-MET-007 | Metrics endpoint | All services must expose a `/actuator/prometheus` endpoint in Prometheus exposition format, scraped by the platform's Prometheus instance. | Must |

### Observability — Distributed Tracing

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-TRACE-001 | OpenTelemetry instrumentation | All services must instrument outbound calls (HTTP, gRPC, JDBC, Redis) using the OpenTelemetry Java agent. Span creation for inbound requests is automatic via the agent. | Must |
| FR-TRACE-002 | Trace context propagation | Trace context (trace ID + span ID) must be propagated across all service boundaries: HTTP headers (W3C Trace Context standard), gRPC metadata, and the STOMP frames the WebSocket gateway relays. A game action crossing client → WebSocket → Orchestration → gRPC → Game Host must be one trace. There is no Redis pub/sub to propagate through (FR-MET-005); the Redis hop that does need it is the **action queue**, where an input is enqueued by one thread and dispatched by another — without the context on the queued entry the trace breaks at exactly the point that matters. | Must |
| FR-TRACE-003 | Trace-log correlation | The trace ID and span ID must be injected into the MDC (Mapped Diagnostic Context) and included in every structured log entry, enabling navigation from a log line directly to its trace. | Must |
| FR-TRACE-004 | Trace sampling | Production deployments should use a sampling rate of 10% for routine traffic. Error spans and spans exceeding latency thresholds must always be sampled (tail-based sampling or head-based with 100% on error). | Should |

### Observability — Alerting

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-ALERT-001 | Availability alert | An alert must fire when any platform service's error rate (5xx responses) exceeds 1% over a 5-minute window. | Must |
| FR-ALERT-002 | Latency alert | An alert must fire when HTTP p95 latency for any platform service exceeds 1000ms over a 5-minute window. | Should |
| FR-ALERT-003 | Game session failure alert | An alert must fire when the game session failure rate (sessions terminated by retry limit, per `platform-architecture.md` FR-FAIL-003) exceeds 1% of active sessions in a 10-minute window. | Must |
| FR-ALERT-004 | Database saturation alert | An alert must fire when the PostgreSQL connection pool utilization exceeds 80% for more than 2 minutes. | Must |
| FR-ALERT-005 | Alert routing | Alerts must be routed to a configurable notification channel (e.g., email, Slack webhook). Alert routing configuration is external to the application. | Should |
| FR-ALERT-006 | Reconciliation repair alert | Reconciliation repairs (FR-JOB-007) indicate a defect elsewhere in the system; the steady state is zero. An alert must fire when repairs are applied on more than 3 consecutive runs, or when any room remains detected-but-unrepaired for more than 10 minutes — the latter is the signature of a room the sweep can see but cannot fix, which is the failure mode that leaves permanently stuck rooms. | Should |
| FR-ALERT-007 | Owed teardown alert | An alert must fire when any owed game-session teardown (`game-rooms.md` FR-XFER-005) remains outstanding for more than 15 minutes. A session that is never torn down pins guest-execution resources for the life of the process (`game-host-internals.md` §6.3/§7.1), so an unbounded backlog degrades the Game Host rather than merely leaving stale data. | Should |

### CI/CD Pipeline

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-CICD-001 | Pipeline per repository | Each independently deployable repository must have its own GitHub Actions workflow, and pipelines are independent — a change to one does not trigger another's. This covers **five** repositories, not two: `turnbase-platform`, `turnbase-game-host`, **`turnbase-frontend`**, and the two published libraries `turnbase-common` and `turnbase-sdk`. The frontend was omitted from an earlier version of this requirement while being the only artifact users load directly. The two libraries publish Maven and npm artifacts rather than images, so their pipelines end at publication rather than at FR-CICD-006's image build; everything before that — build, test, coverage, scanning — applies unchanged. | Must |
| FR-CICD-010 | Dependency and image scanning | Every repository must run automated dependency updates (Dependabot, or equivalent) and vulnerability scanning of both dependencies and built container images (Trivy, or equivalent) as part of its pipeline. A **critical** finding fails the build; lower severities are reported and do not block. The distinction matters for a solo project: a pipeline that blocks on every advisory stops being run. **The automated-update half is deliberately suspended during Phase 1 implementation** (2026-09-05): Dependabot version updates are frozen in all five repositories via `open-pull-requests-limit: 0`, for the same reason pull requests are (ADR-0012) — the update stream outran the rate at which it could be merged. The configuration is kept, not deleted, so the freeze is one setting from being lifted, and the requirement is unchanged for the delivered system. Scanning is unaffected. | Should |
| FR-CICD-011 | Frontend pipeline specifics | The frontend pipeline must additionally enforce type checking (`tsc --noEmit`), lint and format checks (ESLint, Prettier), and a production build. Coverage thresholds (FR-CICD-003) apply to unit tests only; the frontend has no integration or e2e tier of its own — end-to-end coverage of the platform is FR-CICD-005's, which uses HTTP and WebSocket clients rather than a browser. | Must |
| FR-CICD-002 | Pre-merge checks | On every push to `master`, the pipeline must: (1) build the project, (2) run unit tests, (3) run integration tests, (4) enforce coverage thresholds. A red run means the work just merged is not mergeable — [`CLAUDE.md`](../../CLAUDE.md) requires it green before the submodule ref is bumped in the parent repository, and the branch that produced it is fixed forward or left unmerged, never parked. The base branch is `master` in every repository ([ADR-0012](../decisions/0012-repo-strategy-polyrepo-submodules.md) *Branch Model*); an earlier version of this requirement said `main`, which named a branch that exists nowhere. A later version gated this on a pull request; ADR-0012 was amended 2026-09-05 to suspend pull requests project-wide, so a `pull_request`-triggered gate would never fire — every merge is now a direct, local `--ff-only` merge followed by a push, and the push is what the pipeline gates. | Must |
| FR-CICD-003 | Coverage threshold | All services must maintain ≥70% line coverage measured across **unit and integration tests** — the two categories that run pre-merge, on every push to `master` (FR-CICD-002; OQ-002 moves e2e post-merge). Coverage is measured and reported as part of that same run, and a drop below threshold is a failing check. E2E tests deliberately do **not** contribute: their coverage is not available when the gate runs, and a threshold that silently counts a number it cannot see is a threshold that will be met by accident. Post-merge e2e runs report coverage for information only and gate nothing. | Must |
| FR-CICD-004 | Test types | The pipeline must support three test categories: **unit** (no external dependencies, mocked boundaries), **integration** (real PostgreSQL, Redis and MinIO, plus a Game Host stub where needed, each started by the test run itself via **Testcontainers** — never by a stack a developer started by hand), and **e2e** (the full Docker Compose stack, exercising real HTTP and WebSocket flows end-to-end). The integration tier does **not** use Docker Compose: a test that depends on a stack somebody started separately is a test that fails on a clean machine and in CI. Compose is the e2e tier's dependency, and only there. Per-category dependencies and invocations are in [`../specs/deployment/local-environment.md`](../specs/deployment/local-environment.md) §8. | Must |
| FR-CICD-005 | E2E test scope | E2E tests exercise the deployed application stack (Platform Monolith + Game Host + PostgreSQL + Redis) via its external APIs. E2E tests do not involve a real browser; they use HTTP clients and WebSocket clients. | Must |
| FR-CICD-006 | Docker image build | On merge to `master`, the pipeline must build and push a Docker image tagged with the commit SHA to the container registry. | Must |
| FR-CICD-007 | Tag-based deployment | **Deferred to post-MVP** ([ADR-0001](../decisions/0001-local-first-mvp-platform.md) §*Decision* item 4 — cloud deployment is not built for the MVP, and item 2 names the local Docker Desktop cluster, not a tag-triggered pipeline, as the CI-exercised deploy path). As originally written: when a version tag matching `v*.*.*` (semver) is pushed to `master`, the pipeline must trigger a production deployment using the image built for that commit, and no deployment occurs on untagged merges. Nothing in the MVP corpus names a production cluster endpoint, a deployment credential, or a `values-production.yaml` for this to target — ADR-0001 deferred `FR-SCALE-*` explicitly on the same page but never propagated that deferral here, the same class of gap `IMP-GATE-06` found for CON-010 (`IMP-GATE-24`). Re-scope when a real production target is chosen post-MVP. | Must (post-MVP) |
| FR-CICD-008 | Deployment rollback | **Deferred to post-MVP**, for the same reason as FR-CICD-007 — there is no deployment for a rollback to reverse. As originally written: the deployment pipeline must support rollback to a previously deployed version tag by re-running the deployment step with the target tag. | Should (post-MVP) |
| FR-CICD-009 | Pipeline secrets | All credentials used by the pipeline (registry credentials, Kubernetes context, deployment keys) must be stored as GitHub Actions secrets. No secrets in source code or committed configuration. | Must |

---

### Secrets and Credentials

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-CRED-001 | Secrets are injected, never committed | Every credential — JWT signing key, database and Redis passwords, object-store keys, OAuth client secret, admin credentials — must reach a service as an injected environment variable sourced from a secret store appropriate to the environment (a git-ignored `.env` file locally, a Kubernetes `Secret` in-cluster, GitHub Actions secrets in CI). No credential may appear in source, in a committed configuration file, or in a container image. | Must |
| FR-CRED-002 | No working default for any secret | A missing credential must cause startup to fail with an error naming the missing key. No secret may have a fallback value that allows the service to start. | Must |
| FR-CRED-003 | Signing-key rotation without mass invalidation | The platform must be able to replace its JWT signing key without invalidating sessions signed by the previous key. Tokens must identify the key that signed them, and the platform must verify against a set containing the active key and recently retired keys. A key is fully retired only after no unexpired token can name it (FR-SESS-001), at which point any session still bound to it is revoked. | Must |
| FR-CRED-004 | Emergency rotation is a bounded, stated cost | The platform must also support immediate retirement of a compromised key, revoking every session it signed. This disconnects live WebSocket and SSE connections (FR-SESS-010) and, for players in an in-progress game, starts a grace period they are unlikely to beat by re-authenticating. This cost is accepted; it must be documented rather than discovered during an incident. | Must |
| FR-CRED-005 | Least privilege for datastore access | The application's database role must not hold superuser. Privileged operations required once at provisioning time — extension creation in particular — are performed by a separate owner role, and the application asserts their result at startup rather than performing them. | Must |

---

### Database Schema Management

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-DB-001 | Managed schema migrations | The Platform Monolith's PostgreSQL schema must be created and evolved exclusively by versioned migration scripts applied by a migration tool ([ADR-0011](../decisions/0011-schema-migrations.md): Flyway). No schema object may be created by application auto-DDL, by a library's own bootstrap, or by hand. A database whose migration history does not match the deployed application's expected version must cause startup to fail rather than be adopted. | Must |
| FR-DB-002 | Forward-only migrations | Migrations are never reversed. A defective migration is corrected by a subsequent migration. An already-applied migration file is immutable; editing one must be detected as a checksum failure at startup and in CI. | Must |
| FR-DB-003 | Backward-compatible migrations | Every migration must leave a schema against which the **previous** application version still runs correctly. A rolling deploy runs both versions simultaneously (FR-DEPLOY-001), and FR-CICD-008's rollback re-deploys the previous image against the newer schema. Destructive changes — dropping or renaming a column or table, narrowing a type, or adding a constraint the previous version would violate — must be split across at least two releases (expand, then contract). | Must |
| FR-DB-004 | Migration observability and bounds | Migration application must be logged as a structured event with the version applied and elapsed time, and the migration session must run under a lock timeout so that a migration blocked behind a long-running query fails the deploy rather than blocking every reader of the affected table. Migration time counts against the deploy bound in FR-DEPLOY-003. | Must |

---

### Database Query Efficiency and Connection Pool

Added 2026-10-22 from the M16 re-verification (`../../loadtest/reports/SUMMARY.md`, *M16*), in which the
database connection pool and PostgreSQL were the first thing to break in every capacity scenario. Built
by milestone M17.

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-DBQ-001 | Query cost independent of retained history | Every statement run on the game path (room create, room join, the open-room listing, lobby and ready commands, game start, game action) and by every duty of the deadline sweep (FR-JOB-006; the reconciliation sweep of FR-JOB-007 is not included) must cost time bounded by the room or user it concerns, not by the number of closed rooms, departed participants or retained history rows. Verified on a database seeded with at least 100,000 retained closed-room participants: no such statement's plan is a sequential scan of `room`, `room_team` or `room_participant`, and the rows each statement examines in those tables (actual rows plus rows removed by a filter) exceed those on an empty-history database by no more than 10. | Must |
| FR-DBQ-002 | Room-scoped team occupancy | The number of active players per team is computed only from the participants of the room in question. | Must |
| FR-DBQ-003 | Live participation lookup by user | Finding a user's live room participation reads only that user's participant rows that have not been left, not other users' rows nor that user's departed history. | Must |
| FR-DBQ-004 | Sweep duties make progress | A sweep duty (FR-JOB-006) that selects a room must, within the same run, either complete its action on that room or stop selecting it until the room's state changes. A room the instance cannot mutate (a closed room, no ownership, a lock timeout) must not be selected and re-read on every interval without end; the exclusion is made in the selecting statement, not by discarding rows after the select. The first suspected case is the elapsed migration window (OQ-005). | Must |
| FR-DBQ-005 | Explicit connection-pool size | The Platform Monolith's database connection-pool maximum size is set explicitly in configuration, never left to the library default, and is overridable per deployment environment without a code change. | Must |
| FR-DBQ-006 | Pool size grounded in measurement | The default pool size is chosen from load-test runs on the reference node (`../specs/deployment/load-testing.md`), on the build that already satisfies FR-DBQ-001…004. The runs start from the conventional rule (PostgreSQL cores × 2 + 1) and try at least two larger values. The candidate with the highest ceiling (the last step meeting every NFR-LOAD-001…004 threshold, as `load-testing.md` defines it) wins; among candidates with that ceiling, any whose peak moves/s is within 5% of the best counts as tied, and the smallest tied value is chosen. The candidates, their results and the reason for the choice are recorded in `../specs/deployment/local-environment.md` §7.9. | Must |
| FR-DBQ-007 | PostgreSQL server tuning (conditional) | If NFR-DBQ-001 still fails with PostgreSQL as the first thing to break once FR-DBQ-001…006 hold, the chart's PostgreSQL server settings (memory and connection limits) are tuned and the values recorded with their rationale in `../specs/deployment/local-environment.md`. | Could |

### Scheduled Jobs

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-JOB-001 | Guest account cleanup | A scheduled job permanently deletes guest accounts whose session token has expired, consistent with `user-accounts.md` FR-GUEST-005. Default interval: every 1 hour. The interval is configurable at the platform level. | Must |
| FR-JOB-002 | Notification purge | A scheduled job permanently deletes notifications older than the configured retention window (default: 30 days), consistent with `notifications-invitations.md` FR-NOTIF-006. Default interval: once per day. The interval is configurable at the platform level. | Must |
| FR-JOB-003 | Job failure handling | If a scheduled job fails, the failure must be logged as an ERROR with the job name and failure reason. The job is retried on its next scheduled interval; no immediate retry is performed. | Must |
| FR-JOB-004 | Job observability | Each scheduled job execution must emit a structured log event on start and completion, including the count of records processed and elapsed time. Last-run timestamp and execution count must be exposed as metrics. | Should |
| FR-JOB-005 | Single-instance execution | In a horizontally scaled deployment, each scheduled job must execute on exactly one monolith instance per interval. This is enforced via a distributed lock (e.g. ShedLock backed by the platform's PostgreSQL or Redis instance). **Exception:** a job whose work is partitioned by room ownership (FR-JOB-006) satisfies this requirement by partitioning rather than by locking — each room is owned by exactly one instance, so no two instances can process the same row. A global lock would instead serialize every instance's work behind one leader for no correctness gain. | Must |
| FR-JOB-006 | Room deadline sweep | A scheduled job enforces the time-based room transitions defined in `reconnection-flow.md` from **persisted absolute deadline timestamps**: grace-period expiry (FR-EXPIRY-001/002) and the deferred closure of a last-connected-human host disconnect (FR-HDISC-003). This sweep is the **primary** enforcement mechanism — deadlines are not held in in-process timers, so enforcement survives restart and instance failover ([ADR-0009](../decisions/0009-grace-deadline-durability.md)). Each transition is applied as a conditional update guarded on the reservation still being outstanding, so a concurrent reconnect and the sweep can never both take effect (FR-EXPIRY-005). The job processes only rooms owned by its own instance and must hold that ownership before mutating room state or emitting events ([ADR-0008](../decisions/0008-room-ownership-lifecycle.md)); rooms with no live owner are handled by FR-JOB-007. The same job closes elapsed migration windows (`reconnection-flow.md` FR-HDISC-004) and performs the host transfer they defer, which is otherwise unreachable on the adoption path. It also drains the durable game-input notifications of FR-EXPIRY-005, and **that duty alone is not ownership-partitioned**: delivering a notification to the Game Host is not an event broadcast and needs no room ownership, so partitioning it would leave a player's departure undelivered for as long as their room sat unowned. Default interval: every 5 seconds; configurable. | Must |
| FR-JOB-007 | Room and session reconciliation | A scheduled job reconciles room records against live game-session state and repairs divergence. Duties: (a) re-drive owed session teardowns (`game-rooms.md` FR-XFER-005) until the Game Host confirms them; (b) delete orphaned session artifacts whose room no longer exists or is closed, when older than 10 minutes; (c) resolve In Progress rooms whose session state is gone by **failing them back to Lobby** via the graceful session-failure path (`platform-architecture.md` FR-FAIL-005) — the room is **not** closed and no game-history entry is created (`game-history.md` CON-001); (d) close Lobby rooms with zero connected participants whose last activity is older than the configured idle window (default 30 minutes), per `game-rooms.md` FR-LIFE-007; (e) adopt rooms whose owning instance is no longer live, so their deadlines can be enforced (ADR-0008). Default interval: every 60 seconds; interval and idle window configurable. Executes on exactly one instance per interval per FR-JOB-005. | Must |
| FR-JOB-008 | Reconciliation safety preconditions | FR-JOB-007 must distinguish **state loss** from **datastore unavailability** (`platform-architecture.md` FR-FAIL-006). A datastore command that errors or times out aborts the entire run without performing any repair — an error is never evidence of absence; only a successful negative existence check is. Additionally: (a) no repair is performed within a configurable startup window (default 120 seconds after instance start, which must exceed Game Host registration and lease expiry), because a recovering system is indistinguishable from a broken one until registration completes; (b) a divergence must be observed on two consecutive runs before it is repaired, and the first observation is recorded durably so it survives restart; **guards (a) and (b) both exempt the room-adoption duty (FR-JOB-007e)**, which repairs nothing and infers nothing about Game Host state — it re-establishes an owner from an absent liveness lease, a precondition the claim re-checks atomically — and subjecting it to either guard would breach NFR-JOB-002 and leave every room unswept for the startup window after a restart; (c) if the platform's sentinel key is absent while the datastore is reachable, the datastore has been reset — repairs proceed, but are reported as a single mass-loss event rather than one warning per room. | Must |
| FR-JOB-009 | Closed room purge | A scheduled job permanently deletes room records that have been Closed longer than the configured retention window (default: 7 days), cascading to participant, team, and invite records. Game history entries are independent of room records and are never affected (FR-RET-006). Default interval: once per day. | Should |
| FR-JOB-012 | Upload slot and validation sweep | A scheduled job reclaims game-version upload slots that cannot complete. Two duties: (a) an upload slot still `PENDING` past its expiry is moved to `EXPIRED` and its storage object, if any, deleted; (b) a version stuck in `PROCESSING` past its validation lease is moved to `FAILED` with a synthetic error entry. Duty (b) is not optional bookkeeping: `(game_id, version)` is unique, so a row stranded in `PROCESSING` by an instance that died **permanently burns that version number** for the game — the developer can never retry it. Bundle objects for `FAILED` and `EXPIRED` versions are deleted at the same time. Default interval: every 15 minutes; configurable. Executes on exactly one instance per interval per FR-JOB-005. | Must |
| FR-JOB-010 | Repair idempotency | Every sweep repair must be expressed as a conditional state transition whose guard is the precondition that justified it. A repair whose guard no longer holds is a no-op, not an error. Re-running any sweep against an already-consistent system must produce zero repairs and zero side effects. | Must |
| FR-JOB-013 | Expired request and invitation purge | A scheduled job permanently deletes `friend_request` and `room_invitation` rows whose `expires_at` has passed, scanning `friend_request_expiry_idx` and `room_invitation_expiry_idx` (`../specs/platform/data-model-social.md`, `../specs/platform/data-model-notifications.md`). Deleting the subject row cascades its actionable notification away, which is **the only mechanism that ever removes one**: `notification_purge_idx` is partial and deliberately excludes actionable notifications from FR-JOB-002's generic sweep, so without this job an invitation nobody acts on is retained forever and so is its notification. Default interval: once per hour; configurable. Executes on exactly one instance per interval per FR-JOB-005. | Must |
| FR-JOB-011 | Reconciliation observability | Beyond FR-JOB-004, each sweep must expose per-duty counts of candidates detected, repairs applied, and repairs skipped by guard, as metrics dimensioned by duty. Every applied repair must emit a WARN log carrying the room identifier, session identifier, duty, detection age, and action taken — a repair is always evidence of a defect elsewhere, and the log level must say so. Every aborted run must record its abort reason. A room repeatedly detected but never repaired must be identifiable from metrics alone. | Must |

---

### Deployment and Shutdown

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-DEPLOY-001 | Graceful shutdown drains room ownership | On shutdown an instance must, in order: fail its readiness probe so the ingress stops sending it traffic; refuse to claim ownership of any further room; complete and flush in-flight room mutations; instruct attached clients to reconnect; **release ownership of every room it owns**; and only then exit. The container termination grace period must be long enough for this sequence to complete. Releasing rather than expiring ownership is what makes a deploy fast: the next instance claims a free room immediately instead of waiting out the previous owner's liveness lease. | Must |
| FR-DEPLOY-002 | Affinity hint is advisory at the ingress | The room-affinity routing hint must be treated as a hint. When the instance it names is absent from the ready endpoint set, the ingress must fall back to normal load balancing rather than failing the request; the receiving instance then resolves ownership itself. Without this, every request for a room whose owner has died is routed to a dead instance. | Must |
| FR-DEPLOY-003 | Deploy duration bound | A full rolling deploy must complete within the bound in `reconnection-flow.md` NFR-CONF-003. The binding quantity is the **cumulative** time a single room spends unreachable or unclaimable across the whole deploy, not the interval between individual restarts: a player who never manages to reconnect has one absolute deadline running through every outage, and forfeits when it elapses. A graceful drain (FR-DEPLOY-001) normally opens no grace windows at all, so this constrains the ungraceful path — drain timeouts, OOM kills — and the reconnect latency clients actually experience. | Must |

---

### Data Retention

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-RET-001 | Notifications | Notifications are retained for 30 days from creation, consistent with `notifications-invitations.md` FR-NOTIF-006. After 30 days, notifications are purged automatically. | Must |
| FR-RET-002 | Guest accounts | A guest account becomes **inaccessible** 24 hours after creation — its sessions are revoked and it is marked deleted — consistent with `user-accounts.md` FR-GUEST-003/005. The account **row** is hard-deleted once nothing references it: `room_participant` and `room.host_user_id` are foreign keys with no cascade (deliberately — see [`../specs/platform/data-model-accounts.md`](../specs/platform/data-model-accounts.md) §1), and room records are retained for 7 days after closure (FR-RET-006). The row therefore survives its token by *room closure + the closed-room retention window*, typically about 8 days and longer for a room that runs for days. Deleting the row on a fixed 24-hour schedule is not possible without either violating a foreign key or letting an identity deletion silently remove a seated participant from a live game. | Must |
| FR-RET-003 | Game history | Completed game session records are retained indefinitely. No automated purge. | Must |
| FR-RET-004 | In-room chat | Chat messages are not persisted. They exist only in the WebSocket connections of connected clients during the session. No retention policy applies. | Must |
| FR-RET-005 | Game artifacts | Game artifacts (JARs, frontend bundles) uploaded by developers are retained indefinitely while the game is listed. Artifacts for delisted games are subject to manual cleanup; no automated purge is required. | Should |
| FR-RET-006 | Closed rooms | Closed room records, and the participant, team and invite records belonging to them, are retained for 7 days and then purged automatically (FR-JOB-009). A closed room's only residual value is post-incident debugging; the durable record of what was played is the game history, which is retained independently (FR-RET-003) and must therefore not depend on the room record's continued existence. | Should |

---

## Non-Functional Requirements

| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-AVAIL-001 | Availability | MVP availability target for all platform services (Platform Monolith, Game Host), measured as percentage of time the service successfully handles requests. **99% is what the architecture can actually deliver, and the number is chosen rather than aspirational**: a single-node local cluster with a single non-HA PostgreSQL and a single non-HA Redis has no redundancy anywhere, so any one of them restarting is full downtime, and 99% permits about 7 hours a month. Committing to 99.9% would require HA for both datastores, at least two nodes, a staging environment and someone on call (ADR-0003) — none of which the MVP has, and the first two of which ADR-0001 explicitly defers. Stating 99.9% anyway would make every incident a breach of a target nobody could have met. | 99% uptime (MVP); 99.9% aspiration | Must |
| NFR-PERF-001 | Performance | HTTP API p95 response latency for non-game-session endpoints (user, catalog, rooms, social) | < 200ms p95 | Should |
| NFR-PERF-002 | Performance | WebSocket effect delivery latency from Orchestration logic to client (Platform Monolith internal path, excluding Game Host processing) | < 50ms p95 | Should |
| NFR-PERF-003 | Performance | Platform Monolith must support concurrent WebSocket connections without degrading HTTP API latency | 5,000 concurrent connections | Should |
| NFR-SCALE-001 | Scalability | The Platform Monolith is designed to scale horizontally behind a load balancer using WebSocket **room affinity** (route by `roomId`; ADR-0002) rather than cross-instance pub/sub. Multi-instance horizontal scaling, HPA, connection draining, and cold-start budgets (`FR-SCALE-*`) are **deferred to post-MVP** (ADR-0001); the MVP runs a single local instance. | ≥2 instances without data races | Post-MVP |
| NFR-OBS-001 | Observability | All production incidents must be diagnosable using logs, metrics, and traces without requiring access to the live production environment. | Full post-incident observability | Must |
| NFR-LOAD-001 | Performance | Warm game start, `START_GAME` to `GAME_STARTED`, measured under load (`load-testing.md` §7). A cold start (first start after a Game Host boot) is recorded, not gated. | p95 < 1 s, p99 < 2 s | Should |
| NFR-LOAD-002 | Performance | Game action round trip (`move_rtt`: an action sent to the resulting state update received), measured under load (`load-testing.md` §7). | p99 < 500 ms | Should |
| NFR-LOAD-003 | Performance | Non-game HTTP endpoints under load (`load-testing.md` §7). Complements NFR-PERF-001, which is the p95 target at the design load. | p99 < 500 ms | Should |
| NFR-LOAD-004 | Performance | Lobby event delivery, the command to the broadcast received by a participant, under load (`load-testing.md` §7). | p99 < 600 ms | Should |
| NFR-JOB-001 | Correctness | Grace expiry and deferred closure take effect no later than their persisted deadline plus one sweep interval (FR-JOB-006), **for a room that has a live owner**. FR-JOB-006 is partitioned by ownership, so a room whose owner was lost is not swept at all until it is adopted; that case is bounded by NFR-JOB-002 instead, and the two bounds add. Mirrors `reconnection-flow.md` NFR-PERF-003. | deadline + 5s p99 | Must |
| NFR-JOB-002 | Recoverability | A room whose owning instance is lost becomes owned again — by a returning client (immediately, on the claim its rejoin performs) or by reconciliation (FR-JOB-007) — within this bound, after which its deadlines are enforced normally. The bound is set by FR-JOB-007's interval, since a room nobody returns to has no other path to an owner: it must therefore exceed one full interval, and the adopt duty (FR-JOB-007e) is **exempt from the two-observation rule of FR-JOB-008(b)** — an absent liveness lease is not a divergence to be corroborated, and requiring a second run would double this bound. | < 90s (one FR-JOB-007 interval + margin) | Must |
| NFR-DBQ-001 | Scalability | In the `parallelism`, `ramp-to-break` and `soak` scenarios on the reference single node (`../specs/deployment/load-testing.md`), each run on a freshly reset stack, the database is not the first thing to break. (M16 broke on the DB pool in `parallelism` and `ramp-to-break`; `soak` reported `none` and must stay so.) | The *First to break* line of each of the three reports names neither `DB pool` nor `PostgreSQL` (the vocabulary of `load-testing.md` §8) | Must |
| NFR-DBQ-002 | Performance | HTTP latency stays stable at constant load across the `soak` hold (`load-testing.md` §13 finding 15). | HTTP p99 drift < 25% over the 30-minute hold | Must |
| NFR-DBQ-003 | Performance | No regression against the M16 re-verification (`../../loadtest/reports/SUMMARY.md`, *M16*). | `ramp-to-break` ceiling ≥ 80 pairs; `parallelism` ceiling ≥ 64 pairs and peak moves/s no more than 5% below 1,055 | Must |
| NFR-DBQ-004 | Performance | Game-path statement time does not grow with retained history (FR-DBQ-001). | Mean execution time of each FR-DBQ-001 statement with ≥ 100,000 retained closed-room participants is within 25% (or 0.5 ms, whichever is larger) of the same statement on an empty-history database | Should |

---

## Constraints

| ID | Description |
|----|-------------|
| CON-001 | Backend services use Java 21 with Spring Boot 4.1+ (ADR-0016; only GA releases). |
| CON-002 | The Platform Monolith uses PostgreSQL as its primary relational database and Redis for live game-state persistence / crash recovery and application-level caching. Redis is **not** used for WebSocket routing (room affinity — ADR-0002). |
| CON-003 | Metrics are instrumented via Micrometer (Spring Boot native) and exposed in Prometheus format. |
| CON-004 | Logs are structured JSON, emitted to stdout, collected by Kubernetes and forwarded to Grafana Loki. |
| CON-005 | Distributed tracing uses the OpenTelemetry Java agent. Trace data is exported to Grafana Tempo. |
| CON-006 | Dashboards and alerting use Grafana, consuming Prometheus (metrics), Loki (logs), and Tempo (traces) as data sources. |
| CON-007 | CI/CD pipelines use GitHub Actions, one workflow per submodule. |
| CON-008 | Docker images are built and pushed to a container registry as part of the CI pipeline. |
| CON-009 | Deployments are tag-based (semver tags on `master`). No automatic deployment on untagged merges. |
| CON-010 | E2E tests use Docker Compose to spin up the full stack locally within the CI runner. Integration tests use Testcontainers to start real service dependencies (PostgreSQL, Redis, MinIO) per test run, never a stack started separately (FR-CICD-004). |
| CON-011 | For the MVP, infrastructure runs on **local Docker Desktop Kubernetes** (WSL2), with docker-compose as a supported quick-start profile (ADR-0001). Cloud Kubernetes is a post-MVP aspiration; provider not selected. |
| CON-012 | Schema migrations use **Flyway** with plain SQL migrations, run at application startup ([ADR-0011](../decisions/0011-schema-migrations.md)). Migration files live in the `turnbase-platform` submodule and are authoritative over the schema documents in `docs/specs/platform/`. The Game Host has no relational database and therefore no migrations. |
| CON-013 | One Platform Monolith instance (NFR-SCALE-001 unchanged). FR-DBQ-* and NFR-DBQ-* are measured on the `load-testing.md` reference node with its pinned PostgreSQL resources (2 CPU, 1 GiB). |
| CON-014 | Behaviour when the connection pool is exhausted is unchanged: a request waits for a connection as it does today. Fail-fast or `503` shedding is not introduced by FR-DBQ-*. |
| CON-015 | Schema changes made for FR-DBQ-* (indexes and similar) follow FR-DB-001…004: forward-only, backward-compatible with the previous application version, and bounded; an index on an existing table is built per `../specs/deployment/schema-migrations.md` § `CREATE INDEX CONCURRENTLY`. |
| CON-016 | Retention is unchanged: FR-RET-006 keeps closed rooms for 7 days. FR-DBQ-001 makes that retention free for the game path rather than shortening it. |

---

## Out of Scope

- Kubernetes cluster provisioning, infrastructure-as-code, and network topology
- Service mesh, ingress controller configuration, and TLS termination details
- Container registry selection and image signing
- Cloud deployment for the MVP — AWS/EKS, Terraform, ALB/ACM/Route53, and Kubernetes provider selection are deferred to post-MVP (ADR-0001)
- Game execution infrastructure observability (defined in `platform-architecture.md`)
- Admin tooling and moderation (separate gap — not yet specified)
- Multi-region deployment and geo-redundancy
- Cost monitoring and resource budgeting — **the MVP's infrastructure cost is zero.** Everything runs on hardware the developer already owns (ADR-0001), so there is nothing to monitor and no budget to enforce. The two costs that do exist are a domain registration and, when a cloud phase begins, a second registrable domain for game frontends (ADR-0007). This entry is kept rather than deleted because "cost monitoring is out of scope" reads as an omission, and it is a consequence of the deployment decision
- **Write batching for the database.** The M16 `pg_stat_statements` recon found no hot write path: a game action writes nothing to PostgreSQL, and a room join or a game completion writes about five rows per *game*. Batching them would not move the ceiling FR-DBQ-* addresses.
- Fail-fast or `503` load shedding on connection-pool exhaustion (CON-014).
- A separate connection pool for background jobs; revisited only if a run after FR-DBQ-004 shows jobs competing with requests for connections.
- A connection budget across replicas, a connection proxy (PgBouncer) and multi-instance deployment (Phase B, `../specs/deployment/load-testing.md` §9).
- Query-result caching (a per-room cache is a Phase B design topic).

---

## Open Questions

- **OQ-001** — **Resolved:** A single Redis instance is used for all platform concerns: game-state persistence and crash recovery, the action queue, room ownership leases and epochs (ADR-0008), and application-level counters including rate limiting. It is **not** used for WebSocket routing or fan-out — those are in-process under room affinity (ADR-0002). Consistent with `platform-architecture.md` CON-011. One consequence is operational rather than architectural and is not optional: because a `maxmemory` eviction of an ownership lease permits a wrongful room takeover with no error anywhere, the instance must run `maxmemory-policy noeviction`, asserted at monolith startup (`../specs/deployment/local-environment.md` §2). If that ever has to be relaxed, the escalation is a dedicated logical database for ownership keys, not a policy change.
- **OQ-002** — **Resolved:** Unit and integration tests run pre-merge, gating every push to `master`
  (FR-CICD-002). E2E tests run post-merge, triggered by that same push. This keeps the pre-merge
  feedback loop fast while ensuring E2E coverage is always current on `master` before a tag-based
  deployment can succeed. FR-CICD-003's threshold is scoped to the two categories that run pre-merge
  as a direct consequence. (Originally written against a pull-request-gated flow; ADR-0012's
  2026-09-05 amendment suspending pull requests replaced "PR" with "push to `master`" throughout —
  the gating shape is otherwise unchanged.)
- **OQ-003** — **Resolved:** The full Grafana stack (Prometheus, Loki, Tempo, Grafana) is included in the local Docker Compose setup. This is a primary learning goal of the project. Exact Docker Compose configuration is deferred to the deployment setup documentation.
- **OQ-004** — `NFR-AVAIL-001` states two targets. This document sets 99% for the MVP (99.9% as an aspiration), with the reasoning that a single-node cluster with non-HA PostgreSQL and Redis cannot deliver more. `platform-architecture.md` lists the same ID at 99.9% for Game Host availability for the primary runtime type. The two rows are not changed here: the owner decides which number is the requirement and whether the second row is a different requirement that needs its own ID. Found by `IMP-M15-02` (2026-10-18).
- **OQ-005** — Does the elapsed-migration-window sweep re-process rooms without end? The M16 CPU profile (`../../loadtest/reports/2026-10-21-m16-cpu.md` §3) counted three statements at about 1.26 calls per game action (`select host_user_id from room`, `select connection_count > 0 from room_participant`, `select user_id from room_participant … connection_count > 0`), but the game-action path issues none of them. Their only caller on that schedule is `GraceDeadlineSweepJob.closeMigrationWindow` (FR-JOB-006, every 5 s), which reads them before clearing the window *inside* `RoomEventExecutor.execute` and swallows `RoomUnavailableRetryException`; a room this instance cannot mutate would keep its window and be re-read every interval. The likeliest such room is a **closed** one: `RoomOwnershipService.onRoomClosed` drops the in-memory epoch but leaves `owner_instance_id` and `migration_window_expires_at` set, and closure (`detachSession`) does not clear the window, so a room that closes inside its window would be selected every 5 s until its purge (FR-RET-006, 7 days). Its host has no live connection, which fits the three statements' equal counts. `RoomOwnershipService.release` dropping `owned` without clearing the owner is a second candidate. Unconfirmed: to be reproduced, counting calls per tick against the rooms with `migration_window_expires_at <= now()`, closed rooms included. FR-DBQ-004 stands either way. Found 2026-10-22.
