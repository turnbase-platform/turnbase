# Deployment, Configuration and Schema Evolution

How TurnBase is assembled, started, configured and evolved — the layer between the design documents
and a system that actually runs.

## Scope

Service topology and the network between the components; startup order and the readiness
dependencies that make it correct; the Kubernetes and docker-compose profiles and which of them is
canonical; the complete configuration surface; where secrets come from and how they rotate; and how
the relational schema comes into existence and changes over time.

Everything here is scoped **local-first** per
[ADR-0001](../../decisions/0001-local-first-mvp-platform.md). Each document states its own production
escalation path rather than deferring the whole subject to a cloud phase that has not been scheduled.

## Files

| File | Topic |
|------|-------|
| [local-environment.md](local-environment.md) | The nine containers, ports and network; startup order and readiness; the 120-second suppression budget; Kubernetes vs. compose; seed data; **the consolidated configuration surface**; how tests get their dependencies |
| [schema-migrations.md](schema-migrations.md) | Flyway layout and naming, what a migration may contain, the baseline, CI drift and checksum checks, seeds, Flyway configuration |
| [observability.md](observability.md) | Metrics, logs, traces and alert routing: Actuator/Prometheus scrape, Logback JSON → Promtail → Loki, OTLP → Tempo, Grafana provisioning, Alertmanager rules |
| [secrets-and-configuration.md](secrets-and-configuration.md) | JWT signing keys and their rotation, database and Redis credentials, OAuth client secrets, per-environment configuration, what must never reach a log |

## Key Decisions

- **Kubernetes is canonical; compose is the quick start** ([ADR-0001](../../decisions/0001-local-first-mvp-platform.md) §2). They are not generated from one another, so the mitigation for drift is that configuration is expressed once and a CI job applies the Helm chart to a `kind` cluster — compose being the test substrate and Kubernetes the deployment substrate is exactly the drift risk.
- **The deploy is a rolling update even at one replica.** Under `Recreate` nothing overlaps, and ADR-0008's claim/adoption path — which `platform-operations.md` claims is "continuously tested rather than dormant" — would never run against a live incumbent. Rolling also makes ADR-0011's backward-compatibility rule load-bearing rather than theoretical.
- **The monolith's readiness must not depend on the Game Host.** Coupling them would let a Game Host restart drop every WebSocket on the platform, including rooms in Lobby that are not running a game at all. A Game Host outage degrades *starting a game* and nothing else.
- **Migrations are forward-only and backward-compatible with the previous application version** ([ADR-0011](../../decisions/0011-schema-migrations.md)). That rule is what makes FR-CICD-008's image rollback true rather than nominal.
- **The migration files are authoritative over the schema documents.** The documents are normative for names and for reasons; when they disagree with a migration, the migration is what the database is.
- **Redis runs `maxmemory-policy noeviction`, asserted at startup.** Any `allkeys-*` policy lets memory pressure evict a liveness lease and permit a wrongful ownership takeover with no operator action and no error ([ADR-0008](../../decisions/0008-room-ownership-lifecycle.md)).
- **The platform and games origins must remain different registrable domains** ([ADR-0007](../../decisions/0007-game-frontend-separate-domain.md)), and the monolith refuses to boot if they are not — misconfiguring this removes the isolation the CSRF argument depends on, silently.
- **Signing keys rotate without invalidating every session.** Tokens name the key that signed them, so a retired key revokes exactly the sessions it issued.
