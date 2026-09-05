# Local Environment — Topology, Startup and Configuration

How the whole system is wired together and started. Realizes
[ADR-0001](../../decisions/0001-local-first-mvp-platform.md) (local-first, Docker Desktop Kubernetes
canonical, compose as a quick-start) and `../../requirements/platform-operations.md`
FR-DEPLOY-001…003, CON-010, CON-011.

**Section 7 is the configuration surface** — every tunable named anywhere in the corpus, with its
default and environment variable, in one table. Several of those numbers were previously discoverable
only by reading prose in a spec that owns something else.

---

## 1. What runs

Eleven long-running containers plus a one-shot MinIO init job. Five are the system, six are the
observability stack that `platform-operations.md` OQ-003 puts inside the local environment because
operating it is a stated learning goal. The observability set is wired in
[`observability.md`](observability.md); this section only says what runs.

| Component | Image | In-cluster ports | Depends on |
|---|---|---|---|
| **Platform Monolith** | `turnbase/platform` | `8080` HTTP + WS + game assets, `8081` management | Postgres, Redis, MinIO |
| **Game Host** | `turnbase/game-host` | `9090` gRPC, `8081` management | Redis, MinIO, Platform Monolith (to register) |
| **PostgreSQL 16** | `postgres:16-alpine` | `5432` | — |
| **Redis 7** | `redis:7-alpine` | `6379` | — |
| **MinIO** | `minio/minio` | `9000` S3 API, `9001` console | — |
| MinIO init (`minio-init`) | `minio/mc` | — | MinIO. Runs to completion, then exits |
| Prometheus | `prom/prometheus` | `9090` | — |
| Grafana | `grafana/grafana` | `3000` | Prometheus, Loki, Tempo |
| Loki | `grafana/loki` | `3100` | — |
| Tempo | `grafana/tempo` | `4317` OTLP gRPC, `3200` HTTP | — |
| Promtail | `grafana/promtail` | — | Loki. Tails the container log directory (`observability.md` §3) |
| Alertmanager | `prom/alertmanager` | `9093` | — |

### Host port map

In Kubernetes these are Service ports and collide with nothing. On the host — whether published by
compose or forwarded from the cluster — two of them do, so the published map is not the same as the
in-cluster map:

| Host port | Reaches | Bind |
|---|---|---|
| `8080` | Platform Monolith HTTP, WebSocket, **and the games origin** | all |
| `8081` | Platform management + **admin API** | `127.0.0.1` only |
| `8082` | Game Host management | `127.0.0.1` only |
| `9090` | Game Host gRPC (debugging with `grpcurl`) | `127.0.0.1` only |
| `9091` | **Prometheus** — remapped, because `9090` is taken by the Game Host on the host network | `127.0.0.1` only |
| `3000` | Grafana | all |
| `5432`, `6379`, `9000`, `9001` | Postgres, Redis, MinIO API, MinIO console | `127.0.0.1` only |

`8081` carries the admin API as well as actuator: FR-ADM-001 requires the admin port to be "bound
exclusively to localhost" and "never exposed on the internet-facing network interface", and
`admin-tooling.md` CON-001 puts it on the Spring management port. Actuator and the admin API are
therefore the **same listener**, and it is the one that must never be publicly routable.

**`management.server.address` is unset in both profiles** — the control is never the app's own
bind address, and getting that part wrong breaks the health probes under compose in a way that
looks like a Docker networking bug rather than a configuration mistake: a published port always
forwards to the container's bridge-network interface, never to its loopback, so a listener bound to
`127.0.0.1` *inside* the container is unreachable through `-p 8081:8081` regardless of how that flag
itself is written — the container-internal bind and the host-side publish are two independent
things, and only one of them can be doing the restricting.

**How the restriction is actually achieved differs between the two profiles.** Under compose, the
app listens on all interfaces inside the container, and the host-side bind of the published port —
`127.0.0.1:8081:8081` in `docker-compose.yml`, not any Spring property — is what Docker itself
enforces: a connection arriving at the host on anything other than `127.0.0.1` is never forwarded
into the container at all. Under Kubernetes the address must stay unset for a different reason — a
kubelet probes the *pod IP*, and a listener bound to `127.0.0.1` inside the container is unreachable
from outside that network namespace, so every readiness probe would fail and the Deployment would
never become available — and the control is topological instead: no Ingress rule and no
`LoadBalancer` Service ever names port 8081, so it is reachable only from inside the cluster and by
`kubectl port-forward`.

The property FR-ADM-001 asks for holds in both cases; the mechanism is not the same one, and neither
mechanism is the container's own bind address.

### Both origins are one listener

The platform is served at `http://turnbase.localhost:8080` and game frontends at
`http://{gameId}.games.localhost:8080`
([`../game-frontend/game-asset-serving.md`](../game-frontend/game-asset-serving.md) §3). These are
different **registrable domains** — which is the entire security property ADR-0007 buys — served by
the same process on the same port, routed by `Host` header. Nothing about the origin separation
requires a second port or a second deployment, and adding one would suggest the separation is about
network topology rather than about the browser's same-site rules.

Every `*.localhost` name resolves to loopback in Chrome and Firefox with no `/etc/hosts` entry.

---

## 2. Network

One network, flat. There is no service mesh and no internal TLS (`platform-operations.md`
Out of Scope).

```
              browser
                 │  :8080
        ┌────────▼─────────┐
        │ Platform Monolith│───gRPC :9090──▶ Game Host
        └──┬────┬─────┬────┘                 │   │   │
     :5432 │    │     │ :9000                │   │   │
     ┌─────▼─┐ ┌▼────┐ ┌▼──────┐             │   │   │
     │  PG   │ │Redis│◀┤ MinIO │◀────────────┘   │   │
     └───────┘ └──▲──┘ └───────┘   artifacts     │   │
                  └────────────── session state ─┘   │
                                                     │
        Game Host ──gRPC :8080──▶ Platform Monolith ─┘
                     Register / Heartbeat / ReportContexts
```

The gRPC seam runs in **both** directions, and that is easy to miss: the monolith is the client for
`CreateSession`/`SubmitInput`/`TerminateSession`, and the *server* for
`Register`/`Heartbeat`/`ReportContexts` ([`../game-host/game-host-internals.md`](../game-host/game-host-internals.md)
§2). The registry service is hosted on the monolith's `8080` listener alongside HTTP, so no
additional port is opened.

Redis is reached by both services. Postgres is reached by the monolith only — the Game Host has no
relational store (`platform-operations.md` CON-002), which is why it has no migrations
([`schema-migrations.md`](schema-migrations.md)).

### Redis configuration is not optional

```
maxmemory-policy noeviction
appendonly yes
```

`noeviction` is **required** by [ADR-0008](../../decisions/0008-room-ownership-lifecycle.md) and
restated in [`../platform/room-lifecycle.md`](../platform/room-lifecycle.md) §1.5. Under any
`allkeys-*` policy, memory pressure can evict a healthy instance's liveness lease, which permits a
wrongful ownership takeover with no operator action and no error anywhere — the failure that layer 4
of the fence exists to bound rather than to prevent. A default Redis image ships with `noeviction`
already, so this is a configuration that must be *preserved* rather than added, which is precisely
the kind that gets lost in a later tuning pass. It is asserted at startup: the monolith reads
`CONFIG GET maxmemory-policy` and refuses to start on any other value.

`appendonly yes` narrows ADR-0001's accepted game-state loss window from "everything since the last
RDB snapshot" to "the last second", for one line of configuration.

---

## 3. Startup order and readiness

| # | Component | Ready when | Blocks |
|---|---|---|---|
| 1 | Postgres, Redis, MinIO | `pg_isready` / `PING` / `mc ready` | everything |
| 2 | Platform Monolith | Flyway complete, Postgres pool live, Redis reachable with the right eviction policy, `platform:sentinel` written | Game Host registration; all client traffic |
| 3 | Game Host | Espresso context factory warm, Redis reachable, artifact store reachable, `Register` acknowledged by the monolith | game *sessions* only |
| 4 | Prometheus, Loki, Tempo, Grafana, Promtail, Alertmanager | own probes | nothing |

### The monolith's readiness must not depend on the Game Host

`/actuator/health/readiness` on `8081` reports Postgres, Redis and MinIO. It deliberately does
**not** report the Game Host. If it did, a Game Host restart would fail the monolith's readiness
probe, remove it from the ingress endpoint set, and drop every WebSocket connection on the
platform — including every room in Lobby, every chat channel, and every player whose game is not
even running. A Game Host outage must degrade *starting a game*, and nothing else.

The same reasoning is why the monolith starts and serves before any Game Host has registered. Room
creation, joining, readiness and chat all work; `START_GAME` fails with a specific error until a host
is available.

### The 120-second suppression window and Game Host registration

FR-JOB-008(a) suppresses reconciliation repairs for 120 seconds after instance start, and requires
that window to "exceed Game Host registration and lease expiry". The budget:

| Segment | Target | Measured against |
|---|---|---|
| Monolith container start → readiness | ≤ 30 s | JVM start + Flyway + pool warm |
| Monolith readiness → Game Host `Register` acknowledged | ≤ 60 s | Game Host JVM + Espresso context factory |
| **Total** | **≤ 90 s** | against a 120 s window — 30 s of margin |

If registration has not completed 90 seconds after monolith readiness, that is a startup failure
worth alerting on, not a slow day: it means the window will expire before the system is whole, and
the next reconciliation run will act on a system that is still assembling.

**The coupling is weaker than FR-JOB-008 implies, and that is deliberate.** `room-lifecycle.md` §5.2
resolves an In-Progress room with no session by consulting the **session record**, not by probing the
Game Host — "a host that lost local state recovers from it, and a host with no record returns
`NOT_FOUND`" — so a Game Host that has not yet registered does not, by itself, cause a false repair.
The suppression window is belt and braces over a design that already avoids the inference. It is kept
because the *other* three duties do make inferences, and because a window that is only needed in the
cases nobody predicted is the kind worth keeping.

### Shutdown

FR-DEPLOY-001 prescribes the order: fail readiness → stop claiming → flush in-flight mutations →
tell clients to reconnect → release every owned room → exit.

| Setting | Value | Why |
|---|---|---|
| `server.shutdown` | `graceful` | Spring stops accepting and drains in-flight requests |
| `spring.lifecycle.timeout-per-shutdown-phase` | `30s` | Upper bound on the drain |
| `preStop` hook | `sleep 5` | Endpoint removal propagates to the ingress *asynchronously*; without the pause, connections arrive at a pod that has already begun releasing rooms |
| `terminationGracePeriodSeconds` | `60` | Must exceed `preStop` + drain + release, with margin. If it does not, Kubernetes `SIGKILL`s mid-release and the deploy degrades to the crash path — a lease wait plus a grace-period scare for every player, which is exactly what FR-DEPLOY-001 exists to avoid |

### Deployment strategy

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }
```

Rolling rather than `Recreate`, even at one replica, and the reason is not availability. It is that
`platform-operations.md` already claims "the single-instance MVP exercises this path on every restart
of the local stack, so it is continuously tested rather than dormant" — and under `Recreate` that
claim is false. Nothing overlaps, no room is ever claimed while another instance is still releasing,
and ADR-0008's claim/adoption path runs only against an empty cluster. Under `maxSurge: 1` the
successor is live while the incumbent drains, which is the situation the design was written for.

It also makes ADR-0011's backward-compatibility rule load-bearing rather than theoretical: the new
pod runs its migrations while the old pod is still serving against the old code.

**The local ingress does no room affinity.** It is plain round-robin, which is correct: FR-DEPLOY-002
already declares the affinity hint advisory, and the receiving instance resolves ownership itself. At
one steady-state replica, round-robin is exact.

---

## 4. Kubernetes is canonical; compose is the quick start

ADR-0001 §2 settles this: the Kubernetes manifests are the supported, CI-exercised path, and compose
is a lighter inner-loop profile. They are **not** generated from one another, and the risk of that is
real — a compose file and a Helm chart drift, and the one that drifts is the one CI does not run.

Two things keep them honest:

1. **Configuration is expressed once.** Both read the same `.env`-shaped key set (§7). The Helm chart
   projects it into a `ConfigMap` and a `Secret`; compose projects it into `environment:`. Neither
   file contains a literal value that the other also contains.
2. **CI runs Kubernetes.** `platform-operations.md` FR-CICD-004/005 run integration and e2e against
   compose because a compose stack is what fits in a GitHub Actions runner; a separate workflow
   applies the Helm chart to a `kind` cluster and runs the smoke path. Compose being the *test*
   substrate and Kubernetes being the *deployment* substrate is the drift risk, and the kind job is
   the mitigation.

```
turnbase-platform/deploy/
├── compose/
│   ├── docker-compose.yml            # the four core services
│   ├── docker-compose.observability.yml
│   ├── initdb/
│   │   └── 01-roles.sql              # FR-CRED-005 two-role split
│   └── .env.example
└── helm/turnbase/
    ├── Chart.yaml
    ├── values.yaml                   # defaults = §7 defaults
    ├── values-local.yaml
    └── templates/
        ├── platform-{deployment,service,ingress,configmap,secret,hpa}.yaml
        ├── gamehost-{deployment,service,configmap}.yaml
        ├── postgres-{statefulset,service,pvc}.yaml
        ├── redis-{statefulset,service,configmap}.yaml
        ├── minio-{statefulset,service}.yaml
        └── observability/
```

Postgres, Redis and MinIO are `StatefulSet`s with `PersistentVolumeClaim`s so a `helm upgrade` does
not reset the database. They are in the chart rather than as chart dependencies because ADR-0001 puts
a managed database post-MVP: when that arrives, the change is deleting three templates and pointing a
connection string, not unpicking a subchart.

The Ingress publishes two host rules to the same Service — `turnbase.localhost` and
`*.games.localhost` — with `nginx.ingress.kubernetes.io/proxy-read-timeout` raised well above the
STOMP heartbeat interval, because the default 60 s closes an idle WebSocket that the protocol
considers perfectly healthy.

---

## 5. Running it

```bash
# quick start — core services only, no observability
docker compose -f deploy/compose/docker-compose.yml up -d

# full stack, including Grafana
docker compose -f deploy/compose/docker-compose.yml \
               -f deploy/compose/docker-compose.observability.yml up -d

# canonical path
helm upgrade --install turnbase deploy/helm/turnbase -f deploy/helm/turnbase/values-local.yaml
```

Then `http://turnbase.localhost:8080`. Grafana on `http://localhost:3000`.

The inner loop for backend work is neither of those: run the dependencies in compose and the monolith
from the IDE against them, which is what the `local` Spring profile's defaults in §7 point at.

### The bundle bucket is created by an init step, not by the application

`turnbase.artifact-store.bucket` (§7.9) must exist before the monolith issues its first pre-signed
URL. It is created by a one-shot `minio/mc` init container that runs to completion before the
monolith starts:

```yaml
minio-init:
  image: minio/mc
  depends_on: { minio: { condition: service_healthy } }
  entrypoint: >
    /bin/sh -c "
    mc alias set local http://minio:9000 $$MINIO_ROOT_USER $$MINIO_ROOT_PASSWORD &&
    mc mb --ignore-existing local/$$TURNBASE_ARTIFACT_STORE_BUCKET &&
    mc anonymous set none local/$$TURNBASE_ARTIFACT_STORE_BUCKET"
```

Under Kubernetes the same three commands run as a `Job` with the chart's `minio` credentials.

`--ignore-existing` makes the step idempotent, which matters because it runs on every
`docker compose up` and a second run must not fail the stack. `mc anonymous set none` is explicit
rather than relying on the default: a bundle bucket that is publicly listable exposes every
unpublished game version, and the published-assets route
([`../game-frontend/game-asset-serving.md`](../game-frontend/game-asset-serving.md) §4) serves through
the monolith precisely so the bucket never needs to be public.

**The application asserts, it does not create.** On startup the monolith checks the bucket exists and
fails with a message naming `TURNBASE_ARTIFACT_STORE_BUCKET` if it does not — the same posture
FR-CRED-005 takes on `CREATE EXTENSION` (§4 of
[`secrets-and-configuration.md`](secrets-and-configuration.md)), and for the same reason: a service
that provisions its own infrastructure needs privileges it should not hold at runtime.

---

## 6. Seed data

Seeds are applied by an `ApplicationRunner` under the `local` and `e2e` profiles only, never by a
migration ([`schema-migrations.md`](schema-migrations.md) §7). Every statement is idempotent against
fixed UUIDs, so starting the stack twice does not duplicate anything and a seed can be edited freely
without tripping a migration checksum.

| Seeded | Content |
|---|---|
| Users | `alice`, `bob`, `carol`, `dave` — password `password`; `alice`↔`bob` friends, `carol`→`alice` request pending |
| Games | The official games, `badge = 'OFFICIAL'`, `owner_user_id = NULL`, one `ACTIVE` version each with a real bundle in MinIO |
| Rooms | None. A room is cheap to create through the UI, and a seeded room in `LOBBY` would be collected by the idle sweep 30 minutes later, which reads in the logs like a defect |
| Notifications | One of each type in §3 of [`../platform/data-model-notifications.md`](../platform/data-model-notifications.md), so the center is not empty on first login |

```bash
make reset-db     # drop schema, re-migrate, re-seed
make seed         # re-run seeds only
```

**The seeder drives the real upload pipeline; it does not write rows and objects by hand.** Writing a
ZIP to MinIO and inserting an `ACTIVE` `game_version` row would skip the unpack step, so
`/g/{gameId}/{version}/` would never exist: `make seed` succeeds, the catalog lists the game,
`/play/{sessionId}` renders, and the iframe 404s on its entry point. That is precisely the "lists and
cannot start" outcome — a worse first experience than an empty catalog — arrived at by the seeder
being *convenient*.

So the runner calls the same request-slot → PUT → confirm → validate → activate path a developer
would ([`../manifest/bundle-format.md`](../manifest/bundle-format.md)), against fixed UUIDs and with
`ON CONFLICT DO NOTHING` semantics on the game row. It is slower than inserting rows and it means
`make seed` exercises the upload pipeline on every developer machine, every day — which is the second
reason to do it this way.

---

## 7. Configuration surface

**Binding rule.** Every property below is a Spring `@ConfigurationProperties` key. The environment
variable is the key uppercased with `.` and `-` replaced by `_` — `turnbase.room.grace-period` →
`TURNBASE_ROOM_GRACE_PERIOD`. The column is given explicitly anyway, because the rule is only obvious
once you already know it.

Durations use ISO-8601 or Spring's shorthand (`60s`, `30m`, `7d`). Sizes use `KB`/`MB`.

### 7.1 Room lifecycle, capacity and deadlines

| Property | Default | Env | Source |
|---|---|---|---|
| `turnbase.room.grace-period` | `60s` | `TURNBASE_ROOM_GRACE_PERIOD` | FR-GRACE-002 |
| `turnbase.room.migration-window` | `20s` | `TURNBASE_ROOM_MIGRATION_WINDOW` | FR-HDISC-004, room-lifecycle §1.4 |
| `turnbase.room.idle-window` | `30m` | `TURNBASE_ROOM_IDLE_WINDOW` | FR-JOB-007d |
| `turnbase.room.spectator-capacity` | `8` | `TURNBASE_ROOM_SPECTATOR_CAPACITY` | `game-rooms.md` NFR-SPEC-001 |
| `turnbase.room.lease.ttl` | `10s` | `TURNBASE_ROOM_LEASE_TTL` | room-lifecycle §1.1 |
| `turnbase.room.lease.renew-interval` | `3s` | `TURNBASE_ROOM_LEASE_RENEW_INTERVAL` | room-lifecycle §1.1 |
| `turnbase.room.lease.self-evict-after` | `6s` | `TURNBASE_ROOM_LEASE_SELF_EVICT_AFTER` | room-lifecycle §1.5 layer 3 |

**`spectator-capacity` is a platform limit, and deliberately the only capacity in this table.**
NFR-SPEC-001 says hosts have no control over it, so it is not a room column and not a create-request
field; a host chooses *whether* a room allows spectating (`spectatingEnabled`) and the platform
chooses how many. It is not per-game either — a game's manifest declares whether it supports
spectating at all, not a headcount, because the cost being bounded here is the platform's fan-out
rather than anything the game does.

The value is read at every capacity check
([`../api-design/room-rest-api.md`](../api-design/room-rest-api.md) §3, §5) and is echoed on the wire
as `spectatorCapacity` in the room resource and in `ROOM_STATE`. **The wire field is the resolved
value, not a stored one** — lowering the property does not evict anybody, so a room can sit above
capacity until spectators leave. That is the intended behaviour: the alternative is disconnecting
people mid-game to satisfy a config change.

The three lease values are a **set**, not three independent knobs. `renew-interval ≪ ttl` (so a single
missed renewal is survivable) and `self-evict-after < ttl` with a guard band (so an instance stops
acting before its lease can have lapsed) are the relationships that must hold; `room-lifecycle.md`
OQ-001 records that the absolute values are reasoned rather than measured. Changing one without the
others is how this design breaks.

### 7.2 Scheduled jobs

| Property | Default | Env | Source |
|---|---|---|---|
| `turnbase.jobs.deadline-sweep.interval` | `5s` | `TURNBASE_JOBS_DEADLINE_SWEEP_INTERVAL` | FR-JOB-006 |
| `turnbase.jobs.reconcile.interval` | `60s` | `TURNBASE_JOBS_RECONCILE_INTERVAL` | FR-JOB-007 |
| `turnbase.jobs.reconcile.startup-suppression` | `120s` | `TURNBASE_JOBS_RECONCILE_STARTUP_SUPPRESSION` | FR-JOB-008a |
| `turnbase.jobs.reconcile.orphan-age` | `10m` | `TURNBASE_JOBS_RECONCILE_ORPHAN_AGE` | FR-JOB-007b |
| `turnbase.jobs.guest-cleanup.interval` | `1h` | `TURNBASE_JOBS_GUEST_CLEANUP_INTERVAL` | FR-JOB-001, FR-GUEST-005 |
| `turnbase.jobs.notification-purge.interval` | `24h` | `TURNBASE_JOBS_NOTIFICATION_PURGE_INTERVAL` | FR-JOB-002 |
| `turnbase.jobs.expiry-purge.interval` | `1h` | `TURNBASE_JOBS_EXPIRY_PURGE_INTERVAL` | FR-JOB-013 |
| `turnbase.jobs.room-purge.interval` | `24h` | `TURNBASE_JOBS_ROOM_PURGE_INTERVAL` | FR-JOB-009 |
| `turnbase.jobs.upload-slot-cleanup.interval` | `15m` | `TURNBASE_JOBS_UPLOAD_SLOT_CLEANUP_INTERVAL` | FR-JOB-012 |
| `turnbase.uploads.validation-lease` | `10m` | `TURNBASE_UPLOADS_VALIDATION_LEASE` | FR-JOB-012(b) |

`deadline-sweep.interval` is the second term of NFR-JOB-001 (`deadline + one interval`), and
`reconcile.interval` sets NFR-JOB-002's 90-second bound. Raising either raises a stated correctness
bound; they are not performance knobs.

### 7.3 Retention

| Property | Default | Env | Source |
|---|---|---|---|
| `turnbase.retention.closed-room` | `7d` | `TURNBASE_RETENTION_CLOSED_ROOM` | FR-RET-006 |
| `turnbase.retention.notification` | `30d` | `TURNBASE_RETENTION_NOTIFICATION` | FR-RET-001, FR-NOTIF-006 |
| `turnbase.retention.friend-request` | `30d` | `TURNBASE_RETENTION_FRIEND_REQUEST` | FR-FREQ-005 |
| `turnbase.retention.guest-account` | `24h` | `TURNBASE_RETENTION_GUEST_ACCOUNT` | FR-RET-002 |

Game history has no entry here. FR-RET-003 retains it indefinitely; it is the one table with no purge
([`../platform/data-model-history.md`](../platform/data-model-history.md) §5).

### 7.4 Accounts and social

| Property | Default | Env | Source |
|---|---|---|---|
| `turnbase.auth.session-ttl` | `24h` | `TURNBASE_AUTH_SESSION_TTL` | FR-SESS-001, FR-GUEST-003 |
| `turnbase.accounts.rename-window` | `30d` | `TURNBASE_ACCOUNTS_RENAME_WINDOW` | FR-ACCT-002, FR-ACCT-003 |
| `turnbase.social.friend-cap` | `50` | `TURNBASE_SOCIAL_FRIEND_CAP` | FR-SOC-009, NFR-SOC-SCALE-001 |
| `turnbase.pagination.default-page-size` | `25` | `TURNBASE_PAGINATION_DEFAULT_PAGE_SIZE` | FR-CAT-004, FR-HIST-026 |
| `turnbase.pagination.max-page-size` | `100` | `TURNBASE_PAGINATION_MAX_PAGE_SIZE` | pagination-filtering-sorting.md |

`session-ttl` governs both registered and guest tokens (FR-GUEST-003 defines the guest lifetime as
"the same platform-configurable value"), which is why there is one key and not two — and why
`retention.guest-account` in §7.3 must track it. They are separate keys because the retention job's
window is the thing the *purge* reads, and a future decision to keep a revoked guest row longer than
its token should not require changing the token lifetime.

### 7.5 Uploads and request limits

| Property | Default | Env | Source |
|---|---|---|---|
| `turnbase.uploads.max-bundle-size` | `256MB` | `TURNBASE_UPLOADS_MAX_BUNDLE_SIZE` | FR-BUNDLE-006 |
| `turnbase.uploads.slot-ttl` | `1h` | `TURNBASE_UPLOADS_SLOT_TTL` | file-uploads.md step 1 |
| `turnbase.http.max-body-size` | `64KB` | `TURNBASE_HTTP_MAX_BODY_SIZE` | input-validation.md; 413 in rest-conventions.md |

`max-body-size` and `max-bundle-size` differ by four orders of magnitude and do not conflict: the
bundle never passes through the monolith. It is PUT directly to object storage against a pre-signed
URL, which is the reason the small cap can be small.

### 7.6 Rate limiting

The full tier table is in [`../api-design/rate-limiting.md`](../api-design/rate-limiting.md) §
*Configuration* and is not duplicated here. The keys are all under `turnbase.rate-limit.*`; the two
that are not tier budgets:

| Property | Default | Env | Note |
|---|---|---|---|
| `turnbase.rate-limit.enabled` | `true` | `TURNBASE_RATE_LIMIT_ENABLED` | `false` is honoured **only** under the `test` or `e2e` profile; the application fails to start otherwise |
| `turnbase.security.trusted-proxies` | `10.0.0.0/8,172.16.0.0/12` | `TURNBASE_SECURITY_TRUSTED_PROXIES` | Client-IP derivation. Wrong here means every IP-keyed tier keys on the ingress |

### 7.7 Origins

| Property | Default (local) | Env |
|---|---|---|
| `turnbase.platform.origin` | `http://turnbase.localhost:8080` | `TURNBASE_PLATFORM_ORIGIN` |
| `turnbase.game-frontend.origin-template` | `http://{gameId}.games.localhost:8080` | `TURNBASE_GAME_FRONTEND_ORIGIN_TEMPLATE` |

These two must remain different **registrable domains** (ADR-0007). Setting the games template to a
subdomain of the platform origin silently removes the isolation that
`rest-conventions.md`'s CSRF argument depends on, and nothing will fail — which is why the monolith
asserts the difference at startup and refuses to boot if it does not hold.

### 7.8 Game Host

| Property | Default | Env | Source |
|---|---|---|---|
| `turnbase.gamehost.handler-timeout` | `30s` | `TURNBASE_GAMEHOST_HANDLER_TIMEOUT` | FR-CTX-008 |
| `turnbase.gamehost.interrupt-escalation-grace` | `5s` | `TURNBASE_GAMEHOST_INTERRUPT_ESCALATION_GRACE` | game-host-internals §15 |
| `turnbase.gamehost.context-idle-eviction` | `5m` | `TURNBASE_GAMEHOST_CONTEXT_IDLE_EVICTION` | FR-CTX-009 |
| `turnbase.gamehost.memory-pressure-threshold` | `80%` | `TURNBASE_GAMEHOST_MEMORY_PRESSURE_THRESHOLD` | FR-CTX-010 |
| `turnbase.gamehost.redis-unavailable-window` | `60s` | `TURNBASE_GAMEHOST_REDIS_UNAVAILABLE_WINDOW` | game-host-internals §9.4 |
| `turnbase.gamehost.retry-limit` | `3` | `TURNBASE_GAMEHOST_RETRY_LIMIT` | FR-FAIL-003 |
| `turnbase.gamehost.grpc.max-message-size` | `32MB` | `TURNBASE_GAMEHOST_GRPC_MAX_MESSAGE_SIZE` | protocol doc |
| `turnbase.gamehost.guest-java-home` | `/opt/graalvm-guest-jdk21` | `TURNBASE_GAMEHOST_GUEST_JAVA_HOME` | game-host-internals §15 |
| `turnbase.gamehost.orchestration-address` | `platform:8080` | `TURNBASE_GAMEHOST_ORCHESTRATION_ADDRESS` | IMP-GATE-09 |

The heartbeat interval and lease TTL are **not** configured on the Game Host: they are handed to it
in `RegisterResponse`, so the monolith owns both sides of the liveness contract and they cannot be
set inconsistently.

**`turnbase.gamehost.orchestration-address` is where the Game Host dials `GameHostRegistryService`**
for `Register`/`Heartbeat`/`ReportContexts`/`Deregister` (§2's `gRPC :8080` edge — the registry service
shares the monolith's HTTP listener rather than opening a second port). The default follows §2's
`<service-name>:<port>` convention for every other compose dependency (`postgres:5432`, `redis:6379`,
`minio:9000`); under Kubernetes it resolves to the Platform Monolith's Service DNS name instead. No
TLS, per §2's "one network, flat."

### 7.9 Infrastructure

| Property | Default | Env |
|---|---|---|
| `spring.datasource.url` | `jdbc:postgresql://postgres:5432/turnbase` | `SPRING_DATASOURCE_URL` |
| `spring.datasource.username` | `turnbase_app` | `SPRING_DATASOURCE_USERNAME` |
| `spring.datasource.hikari.maximum-pool-size` | `20` | `SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE` |
| `spring.data.redis.url` | `redis://redis:6379` | `SPRING_DATA_REDIS_URL` |
| `turnbase.artifact-store.endpoint` | `http://minio:9000` | `TURNBASE_ARTIFACT_STORE_ENDPOINT` |
| `turnbase.artifact-store.bucket` | `turnbase-bundles` | `TURNBASE_ARTIFACT_STORE_BUCKET` |
| `management.server.port` | `8081` | `MANAGEMENT_SERVER_PORT` |
| `management.server.address` | **unset**, both profiles (§1 — compose restricts by publishing the port to `127.0.0.1` on the host, not by the app's own bind address) | `MANAGEMENT_SERVER_ADDRESS` |
| `logging.level.root` | `INFO` | `LOGGING_LEVEL_ROOT` |
| `management.otlp.tracing.endpoint` | `http://tempo:4317` | `MANAGEMENT_OTLP_TRACING_ENDPOINT` |
| `management.tracing.sampling.probability` | `0.1` | `MANAGEMENT_TRACING_SAMPLING_PROBABILITY` |
| `spring.profiles.active` | `local` | `SPRING_PROFILES_ACTIVE` |

Pool size 20 against FR-ALERT-004's 80 % saturation alert means the alert fires at 16 concurrent
checkouts. The deadline sweep runs every 5 seconds and the reconcile sweep every 60; neither holds a
connection between rows.

Credentials are **not** in this table. They are in
[`secrets-and-configuration.md`](secrets-and-configuration.md).

---

## 8. Testing

`platform-operations.md` FR-CICD-004 defines three categories. Where each one gets its dependencies:

| Category | Dependencies | How |
|---|---|---|
| **Unit** | none | Mocked boundaries. No Postgres, no Redis, no Spring context where avoidable |
| **Integration** | real Postgres, Redis, MinIO | Testcontainers with `@ServiceConnection`. Not the compose stack — a test that needs a stack somebody started by hand is a test that fails on a clean machine |
| **E2E** | full stack | The compose stack, exercised over real HTTP and WebSocket clients. No browser (FR-CICD-005) |

```bash
./mvnw test                       # unit
./mvnw verify -Pintegration       # Testcontainers
make e2e                          # compose up, run, compose down
```

**Integration tests run migrations.** Testcontainers starts an empty Postgres and Flyway builds the
schema, which means every integration test run is a migration test — the check of
[`schema-migrations.md`](schema-migrations.md) §6 as a side effect of ordinary work rather than as a
job somebody has to remember.

**E2E runs with `turnbase.rate-limit.enabled=false`.** This is the one place the escape hatch is
legitimate, and it is profile-gated for exactly that reason
([`../api-design/rate-limiting.md`](../api-design/rate-limiting.md)): the GRMP prototype's hardcoded
login limit blocked every test session for months, and the workaround was deleting Redis keys by
hand.

Two things the sweep intervals do to tests, worth knowing before writing one:

- A test of grace expiry must either wait out `grace-period + deadline-sweep.interval` or override
  both. Overriding is right; sleeping 65 seconds in a test suite is not.
- A test of reconciliation must clear `reconcile.startup-suppression`, which is 120 seconds and will
  otherwise make every repair assertion fail with no repair and no error — the sweep detects, logs,
  and deliberately does nothing (`room-lifecycle.md` §5.4).

---

## 9. What is deliberately absent

- **No service mesh, no internal TLS, no mTLS between monolith and Game Host.** Out of scope in
  `platform-operations.md`; the two run in one cluster on one network.
- **No HPA.** `FR-SCALE-*` is post-MVP (ADR-0001 §5). The chart has a template for it, disabled.
- **No cloud manifests.** ADR-0001 §4. The Helm chart's values are the seam: a cloud deployment
  changes `values-*.yaml`, not templates.
- **No gVisor / `runsc` runtime class.** ADR-0001 §3 — unavailable on Docker Desktop/WSL2, re-scoped
  to production-only hardening.
- **No separate Redis instances per concern.** `platform-operations.md` OQ-001 resolved this: one
  instance for game state, leases, rate limits and caching. ADR-0008's note about "a dedicated logical
  database for ownership keys" is the escalation if `noeviction` ever has to be relaxed.
- **No backup or restore procedure.** Postgres is a PVC on a laptop. This is a genuine gap rather than
  a decision, and is OQ-002 below.

---

## 10. Open questions

- **OQ-001** — The startup budget in §3 is a target, not a measurement. Nothing has been built, so
  "≤ 30 s to readiness" is a guess about a Spring Boot application with Flyway and a connection pool.
  It should be replaced with a measured value and a CI assertion once the stack runs, because
  FR-JOB-008's window depends on it.
- **OQ-002** — There is no backup, restore or disaster-recovery story for the local Postgres volume.
  For a local MVP whose data is seedable this is arguably correct, but it is undecided rather than
  decided: nothing states whether losing the volume is acceptable. The first genuinely valuable data
  the platform holds is game history, which FR-RET-003 retains indefinitely and nothing protects.
