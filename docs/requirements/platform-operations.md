# Platform Operations Requirements

This document defines operational requirements for the TurnBase platform: service topology, availability targets, observability standards, CI/CD pipeline, data retention, and deployment model. It complements `platform-architecture.md`, which covers game execution infrastructure specifically.

## Related Documents

- `platform-architecture.md` — Game Host service, Orchestration logic, game execution infrastructure
- `game-contracts.md` — Platform ↔ game communication protocol
- `user-accounts.md` — Guest account lifetime, session management
- `notifications-invitations.md` — Notification retention policy
- `../decisions/INDEX.md` — ADR-0001 (local-first platform), ADR-0002 (WebSocket room affinity), ADR-0003 (availability target)

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
| FR-MET-005 | Redis metrics | The Platform Monolith must expose Redis operation latency and error count for both game-state pub/sub and application-level Redis usage. | Must |
| FR-MET-006 | JVM metrics | All JVM-based services must expose standard JVM metrics: heap usage, GC pause duration and frequency, thread count. Provided automatically via Micrometer JVM instrumentation. | Must |
| FR-MET-007 | Metrics endpoint | All services must expose a `/actuator/prometheus` endpoint in Prometheus exposition format, scraped by the platform's Prometheus instance. | Must |

### Observability — Distributed Tracing

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-TRACE-001 | OpenTelemetry instrumentation | All services must instrument outbound calls (HTTP, gRPC, JDBC, Redis) using the OpenTelemetry Java agent. Span creation for inbound requests is automatic via the agent. | Must |
| FR-TRACE-002 | Trace context propagation | Trace context (trace ID + span ID) must be propagated across all service boundaries: HTTP headers (W3C Trace Context standard), gRPC metadata, and Redis pub/sub messages where supported. | Must |
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

### CI/CD Pipeline

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-CICD-001 | Pipeline per submodule | Each submodule (Platform Monolith, Game Host) must have its own GitHub Actions workflow. Pipelines are independent; a change to one submodule does not trigger the other's pipeline. | Must |
| FR-CICD-002 | Pull request checks | On every pull request to `main`, the pipeline must: (1) build the project, (2) run unit tests, (3) run integration tests, (4) enforce coverage thresholds. The PR cannot be merged if any check fails. | Must |
| FR-CICD-003 | Coverage threshold | All services must maintain ≥70% line coverage across all test types combined. Coverage is measured and reported as part of the PR pipeline. A coverage drop below threshold is a failing check. | Must |
| FR-CICD-004 | Test types | The pipeline must support three test categories: **unit** (no external dependencies, mocked boundaries), **integration** (real dependencies via Docker Compose — PostgreSQL, Redis, Game Host stub where needed), and **e2e** (full stack via Docker Compose, exercising real HTTP and WebSocket flows end-to-end). | Must |
| FR-CICD-005 | E2E test scope | E2E tests exercise the deployed application stack (Platform Monolith + Game Host + PostgreSQL + Redis) via its external APIs. E2E tests do not involve a real browser; they use HTTP clients and WebSocket clients. | Must |
| FR-CICD-006 | Docker image build | On merge to `main`, the pipeline must build and push a Docker image tagged with the commit SHA to the container registry. | Must |
| FR-CICD-007 | Tag-based deployment | When a version tag matching `v*.*.*` (semver) is pushed to `main`, the pipeline must trigger a production deployment using the image built for that commit. No deployment occurs on untagged merges. | Must |
| FR-CICD-008 | Deployment rollback | The deployment pipeline must support rollback to a previously deployed version tag by re-running the deployment step with the target tag. | Should |
| FR-CICD-009 | Pipeline secrets | All credentials used by the pipeline (registry credentials, Kubernetes context, deployment keys) must be stored as GitHub Actions secrets. No secrets in source code or committed configuration. | Must |

---

### Scheduled Jobs

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-JOB-001 | Guest account cleanup | A scheduled job permanently deletes guest accounts whose session token has expired, consistent with `user-accounts.md` FR-GUEST-005. Default interval: every 1 hour. The interval is configurable at the platform level. | Must |
| FR-JOB-002 | Notification purge | A scheduled job permanently deletes notifications older than the configured retention window (default: 30 days), consistent with `notifications-invitations.md` FR-NOTIF-006. Default interval: once per day. The interval is configurable at the platform level. | Must |
| FR-JOB-003 | Job failure handling | If a scheduled job fails, the failure must be logged as an ERROR with the job name and failure reason. The job is retried on its next scheduled interval; no immediate retry is performed. | Must |
| FR-JOB-004 | Job observability | Each scheduled job execution must emit a structured log event on start and completion, including the count of records processed and elapsed time. Last-run timestamp and execution count must be exposed as metrics. | Should |
| FR-JOB-005 | Single-instance execution | In a horizontally scaled deployment, each scheduled job must execute on exactly one monolith instance per interval. This is enforced via a distributed lock (e.g. ShedLock backed by the platform's PostgreSQL or Redis instance). | Must |

---

### Data Retention

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-RET-001 | Notifications | Notifications are retained for 30 days from creation, consistent with `notifications-invitations.md` NFR-RET-001. After 30 days, notifications are purged automatically. | Must |
| FR-RET-002 | Guest accounts | Guest accounts and their associated sessions are purged 24 hours after creation, consistent with `user-accounts.md`. | Must |
| FR-RET-003 | Game history | Completed game session records are retained indefinitely. No automated purge. | Must |
| FR-RET-004 | In-room chat | Chat messages are not persisted. They exist only in the WebSocket connections of connected clients during the session. No retention policy applies. | Must |
| FR-RET-005 | Game artifacts | Game artifacts (JARs, frontend bundles) uploaded by developers are retained indefinitely while the game is listed. Artifacts for delisted games are subject to manual cleanup; no automated purge is required. | Should |

---

## Non-Functional Requirements

| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-AVAIL-001 | Availability | MVP availability target for all platform services (Platform Monolith, Game Host), measured as percentage of time the service successfully handles requests. 99.9% is a post-MVP aspiration requiring cloud HA, staging, and on-call (ADR-0003). | 99% uptime (MVP); 99.9% aspiration | Must |
| NFR-PERF-001 | Performance | HTTP API p95 response latency for non-game-session endpoints (user, catalog, rooms, social) | < 200ms p95 | Should |
| NFR-PERF-002 | Performance | WebSocket effect delivery latency from Orchestration logic to client (Platform Monolith internal path, excluding Game Host processing) | < 50ms p95 | Should |
| NFR-PERF-003 | Performance | Platform Monolith must support concurrent WebSocket connections without degrading HTTP API latency | 5,000 concurrent connections | Should |
| NFR-SCALE-001 | Scalability | The Platform Monolith is designed to scale horizontally behind a load balancer using WebSocket **room affinity** (route by `roomId`; ADR-0002) rather than cross-instance pub/sub. Multi-instance horizontal scaling, HPA, connection draining, and cold-start budgets (`FR-SCALE-*`) are **deferred to post-MVP** (ADR-0001); the MVP runs a single local instance. | ≥2 instances without data races | Post-MVP |
| NFR-OBS-001 | Observability | All production incidents must be diagnosable using logs, metrics, and traces without requiring access to the live production environment. | Full post-incident observability | Must |

---

## Constraints

| ID | Description |
|----|-------------|
| CON-001 | Backend services use Java 21 with Spring Boot 3.5+. |
| CON-002 | The Platform Monolith uses PostgreSQL as its primary relational database and Redis for live game-state persistence / crash recovery and application-level caching. Redis is **not** used for WebSocket routing (room affinity — ADR-0002). |
| CON-003 | Metrics are instrumented via Micrometer (Spring Boot native) and exposed in Prometheus format. |
| CON-004 | Logs are structured JSON, emitted to stdout, collected by Kubernetes and forwarded to Grafana Loki. |
| CON-005 | Distributed tracing uses the OpenTelemetry Java agent. Trace data is exported to Grafana Tempo. |
| CON-006 | Dashboards and alerting use Grafana, consuming Prometheus (metrics), Loki (logs), and Tempo (traces) as data sources. |
| CON-007 | CI/CD pipelines use GitHub Actions, one workflow per submodule. |
| CON-008 | Docker images are built and pushed to a container registry as part of the CI pipeline. |
| CON-009 | Deployments are tag-based (semver tags on `main`). No automatic deployment on untagged merges. |
| CON-010 | Integration and E2E tests use Docker Compose to spin up real service dependencies (PostgreSQL, Redis) locally within the CI runner. |
| CON-011 | For the MVP, infrastructure runs on **local Docker Desktop Kubernetes** (WSL2), with docker-compose as a supported quick-start profile (ADR-0001). Cloud Kubernetes is a post-MVP aspiration; provider not selected. |

---

## Out of Scope

- Kubernetes cluster provisioning, infrastructure-as-code, and network topology
- Service mesh, ingress controller configuration, and TLS termination details
- Container registry selection and image signing
- Cloud deployment for the MVP — AWS/EKS, Terraform, ALB/ACM/Route53, and Kubernetes provider selection are deferred to post-MVP (ADR-0001)
- Game execution infrastructure observability (defined in `platform-architecture.md`)
- Admin tooling and moderation (separate gap — not yet specified)
- Multi-region deployment and geo-redundancy
- Cost monitoring and resource budgeting

---

## Open Questions

- **OQ-001** — **Resolved:** A single Redis instance is used for all platform concerns (game-state persistence, action queue, session routing, WebSocket pub/sub). This is consistent with `platform-architecture.md` CON-011. Separate instances can be introduced later if independent scaling or failure isolation becomes necessary.
- **OQ-002** — **Resolved:** Unit and integration tests run in the PR pipeline and block merge. E2E tests run post-merge on `main` (triggered by the same merge commit, not blocking the PR). This keeps PR feedback loops fast while ensuring E2E coverage is always current on `main` before a tag-based deployment can succeed.
- **OQ-003** — **Resolved:** The full Grafana stack (Prometheus, Loki, Tempo, Grafana) is included in the local Docker Compose setup. This is a primary learning goal of the project. Exact Docker Compose configuration is deferred to the deployment setup documentation.
