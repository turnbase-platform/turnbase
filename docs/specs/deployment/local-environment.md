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

Twelve long-running containers plus a one-shot MinIO init job. Six are the system, six are the
observability stack that `platform-operations.md` OQ-003 puts inside the local environment because
operating it is a stated learning goal. The observability set is wired in
[`observability.md`](observability.md); this section only says what runs.

| Component | Image | In-cluster ports | Depends on |
|---|---|---|---|
| **Frontend** | `turnbase/frontend` (nginx) | `8080` — the platform origin's edge: the shell document and its static assets, and a reverse proxy to the monolith (below) | Platform Monolith |
| **Platform Monolith** | `turnbase/platform` | `8080` HTTP + WS + game assets, `8081` management | Postgres, Redis, MinIO |
| **Game Host** | `turnbase/game-host` | `9090` gRPC, `8081` management | Redis, MinIO, Platform Monolith (to register) |
| **PostgreSQL 16** | `postgres:16-alpine` | `5432` | — |
| **Redis 7** | `redis:7-alpine` | `6379` | — |
| **MinIO** | `pgsty/minio` (`IMP-GATE-73`) | `9000` S3 API, `9001` console | — |
| MinIO init (`minio-init`) | `pgsty/mc` (`IMP-GATE-73`) | — | MinIO. Runs to completion, then exits |
| Prometheus | `prom/prometheus` | `9090` | — |
| Grafana | `grafana/grafana` | `3000` | Prometheus, Loki, Tempo |
| Loki | `grafana/loki` | `3100` | — |
| Tempo | `grafana/tempo` | `4317` OTLP gRPC, `4318` OTLP HTTP, `3200` HTTP | — |
| Promtail | `grafana/promtail` | — | Loki. Tails the container log directory (`observability.md` §3) |
| Alertmanager | `prom/alertmanager` | `9093` | — |

**MinIO images come from the `pgsty` community fork, not from MinIO** (`IMP-GATE-73`). MinIO stopped
publishing to Docker Hub (`IMP-GATE-52`), and by 2026-09-26 its `quay.io/minio/*` repositories no
longer served anonymous pulls either, so upstream publishes no public image at all. `pgsty/minio` and
`pgsty/mc` rebuild the same server and client from source on the same UBI-micro base, with the same
entrypoint, `/data` layout and `MINIO_ROOT_*` variables. Every consumer — the compose file, the Helm
chart and each Testcontainers `MinIOContainer` — pins the same `RELEASE.*` tag. Testcontainers'
`MinIOContainer` accepts only the name `minio/minio`, so each Java pin declares
`.asCompatibleSubstituteFor("minio/minio")`. MinIO is a local and test dependency only — production
uses S3 ([`../api-design/file-uploads.md`](../api-design/file-uploads.md)) — so the fork never reaches a
production path.

### Host port map

In Kubernetes these are Service ports and collide with nothing. On the host — whether published by
compose or forwarded from the cluster — two of them do, so the published map is not the same as the
in-cluster map:

| Host port | Reaches | Bind |
|---|---|---|
| `8080` | **Frontend** — the platform origin (shell document, and `/api`, `/ws`, `/auth` proxied to the monolith) **and the games origin** (every other `Host`, proxied to the monolith) | all |
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
different **registrable domains** — which is the entire security property ADR-0007 buys — served on
the same port, routed by `Host` header. Nothing about the origin separation requires a second port
or a second deployment, and adding one would suggest the separation is about network topology rather
than about the browser's same-site rules.

**Who answers on that port (`IMP-GATE-74`).** The listener is the **Frontend** container's nginx
(`turnbase-frontend`'s image), under both compose and Kubernetes:

- `Host` equal to the host of `turnbase.platform.origin` → the **shell**: the built static bundle,
  with the SPA fallback to `index.html`, and the shell's `Content-Security-Policy` header
  ([`shell-architecture.md`](../platform-frontend/shell-architecture.md) §6) on the document
  response. Requests under `/api/` and `/ws`, and exactly `/auth/google` and `/auth/callback`, are
  proxied to the monolith, carrying `X-Forwarded-For`/`-Proto`/`-Host` and the `Upgrade` headers a
  WebSocket needs. **`/auth/complete-registration` is not proxied** — it is a shell route
  (`platform-views.md` VW-OAUTHCOMP; `oauth-rest-api.md` §4 redirects the browser to it), so a
  blanket `/auth/` prefix would send the shell's own page to the monolith to 404 (`IMP-GATE-76`).
- **Every other `Host`** (in practice `*.games.localhost`) → proxied wholesale to the monolith, which
  routes the games origin by `Host` as before. The platform host is the explicit match and the games
  hosts are the fall-through, so the wildcard is never enumerated in nginx.

Under Kubernetes the Ingress may still send the games host straight to the monolith Service; the
frontend's fall-through exists because compose has one published port and no Ingress. The monolith is
never published on `8080` when the Frontend container is — the host port map above is the single
source. Only the monolith's own listener is the security boundary for the API: nginx adds no
authorization and the monolith's `Origin`/session checks are unchanged.

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
`CreateSession`/`ProcessInput`/`TerminateSession`, and the *server* for
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

**Routing by the affinity hint (ADR-0020, from `IMP-M18-09`).** REST is plain round-robin: any instance
serves a call and returns the owner's hint. `/ws` is routed by the `instance` query parameter: the frontend
proxy forwards to the named pod through the platform's headless Service (`{release}-platform-pods`; the hint
carries the pod's dashed address, which the Service resolves) and falls back to the regular Service when that
pod is not ready, the hint is malformed or the parameter is absent (FR-DEPLOY-002; the hint stays advisory).
Compose has no headless Service, so there the hint never resolves and every upgrade goes to the one instance.
`loadtest/check-ws-affinity.mjs` checks it on the cluster.

---

## 4. Kubernetes is canonical; compose is the quick start

ADR-0001 §2 settles this: the Kubernetes manifests are the supported, CI-exercised path, and compose
is a lighter inner-loop profile. They are **not** generated from one another, and the risk of that is
real — a compose file and a Helm chart drift, and the one that drifts is the one CI does not run.

Two things keep them honest:

1. **Configuration is expressed once.** Both read the same `.env`-shaped key set (§7). The Helm chart
   projects it into a `ConfigMap` and a `Secret`; compose projects it into `environment:`. Neither
   file contains a literal value that the other also contains.
2. **No CI job applies the chart to a cluster.** `platform-operations.md` FR-CICD-004/005 run
   integration and e2e against compose because a compose stack is what fits in a GitHub Actions
   runner, and no workflow applies the Helm chart anywhere. Compose being the *test* substrate and
   Kubernetes being the *deployment* substrate is therefore a standing drift risk; rule 1 (one
   configuration source) is the only mitigation, and the load-test runs
   ([`load-testing.md`](load-testing.md)) are the first thing to exercise the chart.

```
turnbase-platform/deploy/
├── compose/
│   ├── docker-compose.yml            # the five core services
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
        ├── frontend-{deployment,service,configmap}.yaml
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

The Ingress publishes two host rules — `turnbase.localhost` to the Frontend Service and
`*.games.localhost` to the monolith Service (`IMP-GATE-74`) — with `nginx.ingress.kubernetes.io/proxy-read-timeout` raised well above the
STOMP heartbeat interval, because the default 60 s closes an idle WebSocket that the protocol
considers perfectly healthy.

---

## 5. Running it

### First run, from a cold clone (`IMP-M7-12`)

Prerequisites: Docker with Compose v2, JDK 21, Node, `make`, `zip`. From the repository root:

```bash
git clone --recurse-submodules https://github.com/turnbase-platform/turnbase && cd turnbase

# 1. The game bundles the seeder uploads (§6) — without them the catalog is empty.
#    Builds Tic-Tac-Toe and 7 Wonders Duel into target/seed-bundles/
scripts/seed-bundles.sh

# 2. The two images compose does not build (ADR-0012: the platform repo never reads a sibling path)
docker build -t turnbase/game-host:dev turnbase-game-host
docker build -t turnbase/frontend:dev  turnbase-frontend

# 3. Secrets, then the stack. `make env` copies deploy/compose/.env.example to .env if there is no
#    .env (it never overwrites one); `make check-env` fails naming every required variable that
#    is missing or empty; `make up` runs both and then `docker compose up -d --wait`.
cd turnbase-platform && make up
```

Then `http://turnbase.localhost:8080`: the catalog lists Tic-Tac-Toe, and `alice` / `password` (§6)
can sign in and start a game. `.env.example` carries dummy, local-only values for every required
variable, so no editing is needed; see
[`secrets-and-configuration.md`](secrets-and-configuration.md) §2 for why that is acceptable here.

**A changed database password needs `docker compose down -v`.** The Postgres image reads
`TURNBASE_DB_OWNER_PASSWORD` only when it first initialises the data volume, and `01-roles.sql`
sets the `turnbase_app` password at the same moment. Editing either in `.env` afterwards leaves the
volume on the old one and the monolith fails authentication. `down -v` discards the volume, so the
database is re-created and re-seeded (`make reset-db` keeps the volume and does not apply a
password change). Redis and MinIO take their passwords from the environment on every start and need
only a restart.

```bash
# quick start — core services only, no observability
docker compose -f deploy/compose/docker-compose.yml up -d

# full stack, including Grafana
docker compose -f deploy/compose/docker-compose.yml \
               -f deploy/compose/docker-compose.observability.yml up -d

# canonical path — see "Installing the chart on Docker Desktop Kubernetes" below
```

Compose serves on `http://turnbase.localhost:8080`. Grafana on `http://localhost:3000`.

### Installing the chart on Docker Desktop Kubernetes

Verified end to end on 2026-10-18 (`IMP-M15-06`; Docker Desktop Kubernetes with the `docker-desktop`
context, ingress-nginx on port 80, Helm 4.3). Run from `turnbase-platform`:

```bash
# once: ingress-nginx must be running on port 80 (`kubectl get pods -n ingress-nginx`); install it from
# its own chart if the namespace is absent.

# once: the git-ignored secrets file. Copy deploy/helm/turnbase/values-local.secrets.example.yaml to
# values-local.secrets.yaml and fill every value except oauth.* with `openssl rand -hex 16`;
# minio.appAccessKey must differ from minio.rootUser; auth.jwtKeySet is the JSON in the example's
# comment with `secret` from `openssl rand -base64 32`.

# the images, from the merged `master` (both Dockerfiles copy a jar built outside the image, so
# `./mvnw package -DskipTests` comes first when `target/` is stale)
docker build -t turnbase/platform:dev  turnbase-platform
docker build -t turnbase/game-host:dev turnbase-game-host
docker build -t turnbase/frontend:dev  turnbase-frontend

H=deploy/helm/turnbase
helm lint $H -f $H/values-local.yaml -f $H/values-local.secrets.yaml
helm upgrade --install turnbase $H -f $H/values-local.yaml -f $H/values-local.secrets.yaml \
  --set platform.seed.bundlesHostPath=<absolute path of the directory holding <gameId>.zip>
```

Then `http://turnbase.localhost` (port 80: `values-local.yaml` sets both origins without a port).

**`platform.seed.bundlesHostPath` is a path in the Kubernetes node, not in your shell.** Under WSL 2
the node cannot see the WSL file system: a Linux path fails with `hostPath type check failed: … is
not a directory` and the platform pod stays in `ContainerCreating`. Copy the bundle to a Windows
directory and pass its `/run/desktop/mnt/host/c/...` form (for `C:\Users\Me\turnbase-seed`:
`/run/desktop/mnt/host/c/Users/Me/turnbase-seed`).

**What a chart without the Game Host configuration looked like.** The Game Host pod reported
`Running`/Ready, because liveness and readiness do not depend on Redis, but its log repeated
`Redis health check failed` (the image defaults to the host name `redis`, the chart's Service is
`turnbase-redis`) and it never registered. The chart now sets the Redis and artifact-store endpoints
and a Secret holding only the Redis password and the scoped artifact pair, and advertises the pod IP
(`TURNBASE_GAMEHOST_ADVERTISED_ADDRESS` from `status.podIP`).

Checks, in order:

```bash
kubectl get pods                                  # every pod Running and ready; minio-init Completed
kubectl exec turnbase-redis-0 -- redis-cli -a <redis.password> smembers hosts    # one host id
kubectl exec turnbase-redis-0 -- redis-cli -a <redis.password> hget host:<id> address   # <pod IP>:9090
PLATFORM_HOST=turnbase.localhost PLATFORM_URL=http://turnbase.localhost node .claude/skills/run-turnbase/driver.mjs game
kubectl port-forward svc/turnbase-prometheus 19090:9090 &
curl -s localhost:19090/api/v1/targets            # jobs platform and gamehost, both "up"
curl -s 'localhost:19090/api/v1/query?query=http_server_requests_seconds_bucket'   # a non-empty result
```

The `hosts` set holds host ids; each id's `host:<id>` hash carries the `address`. Under WSL 2, Node
may fail to resolve `turnbase.localhost` (`EAI_AGAIN`) although `curl` and a browser can; preload a
`dns.lookup` that answers `127.0.0.1` for `*.localhost` (`NODE_OPTIONS="--require shim.cjs"`) rather
than editing `/etc/hosts`.

The inner loop for backend work is neither of those: run the dependencies in compose and the monolith
from the IDE against them, which is what the `local` Spring profile's defaults in §7 point at.

### The bundle bucket is created by an init step, not by the application

`turnbase.artifact-store.bucket` (§7.9) must exist before the monolith issues its first pre-signed
URL. It is created by a one-shot `minio/mc` init container that runs to completion before the
monolith starts — the `pgsty` community image, because MinIO no longer publishes one
(`IMP-GATE-73`, §1):

```yaml
minio-init:
  image: pgsty/mc
  depends_on: { minio: { condition: service_healthy } }
  entrypoint: >
    /bin/sh -c "
    mc alias set local http://minio:9000 $$MINIO_ROOT_USER $$MINIO_ROOT_PASSWORD &&
    mc mb --ignore-existing local/$$TURNBASE_ARTIFACT_STORE_BUCKET &&
    mc anonymous set none local/$$TURNBASE_ARTIFACT_STORE_BUCKET &&
    mc admin policy create local turnbase-app /policy/app-policy.json &&
    mc admin user add local $$TURNBASE_ARTIFACT_STORE_ACCESS_KEY $$TURNBASE_ARTIFACT_STORE_SECRET_KEY &&
    mc admin policy attach local turnbase-app --user $$TURNBASE_ARTIFACT_STORE_ACCESS_KEY"
```

Under Kubernetes the same commands run as a `Job` with the chart's `minio` credentials (the policy
comes from a `ConfigMap` rendered from `minio.bucket`).

**The applications never hold the root account** (`IMP-M10-21`). The last three commands create the
scoped service credential: a MinIO user whose only policy (`turnbase-app`) allows
`s3:ListBucket`/`s3:GetBucketLocation` on the bundle bucket and `s3:GetObject`/`s3:PutObject`/
`s3:DeleteObject` on its objects, and nothing on any other bucket or on the admin API. The monolith
and the Game Host receive that pair as `TURNBASE_ARTIFACT_STORE_ACCESS_KEY`/`_SECRET_KEY`; the root
pair (`MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD`) reaches only the MinIO server and this init step.
Every `mc admin` command is idempotent, so the job still runs on each `docker compose up`.
`ObjectStoreCredentialScopeTest` in `turnbase-platform` fails the build if an application setting is
pointed back at the root variables or the policy widens beyond the bucket.

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
| Games | The official games, `badge = 'OFFICIAL'`, `owner_user_id = NULL`, one `ACTIVE` version each with a real bundle in MinIO — one game per `<gameId>.zip` in `turnbase.seed.bundles-dir`, below |
| Rooms | None. A room is cheap to create through the UI, and a seeded room in `LOBBY` would be collected by the idle sweep 30 minutes later, which reads in the logs like a defect |
| Notifications | One of each type in §3 of [`../platform/data-model-notifications.md`](../platform/data-model-notifications.md) **except `ROOM_INVITATION`, `GAME_APPROVED`, `GAME_REJECTED` and `BUNDLE_VALIDATION_COMPLETE`**. `ROOM_INVITATION`'s subject is a `room_invitation` row, and `room_invitation.room_id` is a `NOT NULL` foreign key to `room`, which the row above deliberately seeds none of; manufacturing one anyway would need either a live `LOBBY` room (the exact idle-sweep outcome the row above avoids) or a `CLOSED` one carrying a still-pending invitation, a combination the running system can never produce itself — `room_invitation` rows are deleted at closure (`data-model-notifications.md` §6, FR-INV-008). `GAME_APPROVED`/`GAME_REJECTED` can only be produced by [`../api-design/admin-rest-api.md`](../api-design/admin-rest-api.md) §5.3/§5.4 deciding an open `game_review` row, and nothing in the platform ever inserts one — that row comes from FR-PRV-004 (`admin-tooling.md`, the game owner's submit-for-review action), which `admin-rest-api.md` §7 explicitly disclaims building and which no work item has yet claimed. `BUNDLE_VALIDATION_COMPLETE` goes to the *uploader* (`file-uploads.md`), and the only uploader in v1 is the admin listener — ADR-0006 makes user uploads a post-MVP path — which has no user to notify; no code path produces the type today either, so a seeded one would be state the running system cannot reach (`IMP-GATE-72`). The remaining four (`FRIEND_REQUEST`, `FRIEND_REQUEST_ACCEPTED`, `FRIEND_REQUEST_DECLINED`, `FRIEND_ADDED`) are enough for the center to not be empty on first login, and are seeded as one story: `carol`'s pending request to `alice` (`FRIEND_REQUEST`, subject = that request); `bob`'s accepted request to `alice` (`FRIEND_REQUEST_ACCEPTED` to `bob`, `FRIEND_ADDED` to `alice`); `dave`'s request to `alice`, declined (`FRIEND_REQUEST_DECLINED` to `dave`), which leaves nothing but its notification. Payloads are `{userId, username}` of the *other* party, as `social.SocialRepository` writes them; `GAME_APPROVED`/`GAME_REJECTED` seeding belongs with whichever item builds FR-PRV-004 and the review queue it feeds |

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

**The "real pipeline" rule above is about games, and only games.** Users, the friendship, the pending request and the notifications are plain idempotent SQL against fixed UUIDs (`ON CONFLICT DO NOTHING`), as the paragraph opening this section says — no feature's service is called, so none has to expose a seeding entry point (`IMP-GATE-72`). Passwords are hashed with the application's own `PasswordEncoder` bean (Argon2id, `input-validation.md` § Argon2id cost parameters), never a precomputed string, so a change to the parameters cannot leave a seeded account that cannot log in.

So the runner calls the same request-slot → PUT → confirm → validate → activate path a developer
would ([`../manifest/bundle-format.md`](../manifest/bundle-format.md)), against fixed UUIDs and with
`ON CONFLICT DO NOTHING` semantics on the game row. It is slower than inserting rows and it means
`make seed` exercises the upload pipeline on every developer machine, every day — which is the second
reason to do it this way.

**Where the bundles come from, and what "fixed UUID" means for a game** (`IMP-GATE-71`). The platform
image is a JRE and the monolith has no dependency on `turnbase-sdk`, so the seeder can neither compile
a game nor build a backend JAR; it only *uploads* bundles that already exist. They are the ZIPs in the
directory named by `turnbase.seed.bundles-dir` (§7.10), one game per file, and **the file name's stem
is the game's fixed `game_id`** — a UUID, e.g. `7c0e…-….zip`. The manifest has no identity field
(`manifest-schema.md` § Top-level fields), and `POST /admin/games` mints a random id, so the file name
is the only place a stable id can live. For each file the seeder:

1. inserts the `game` row with that id — the same row `POST /admin/games` inserts
   (`badge = 'OFFICIAL'`, `owner_user_id = NULL`, `listed = true`) — `ON CONFLICT DO NOTHING`;
2. **skips the file if the game already has an `ACTIVE` version.** A bundle whose version is higher
   than the active one is *not* applied on a later start; `make reset-db` is how a developer re-seeds
   a changed bundle. (Phase A's ordering check would `422` an equal or lower version anyway; skipping
   is what keeps a second start quiet rather than an error in the log);
3. otherwise drives slot → `PUT` to the slot's pre-signed URL → confirm → poll the version resource
   until `ACTIVE` or `FAILED`, in-process through `upload.VersionUploadService` with
   `arrivedViaAdminListener = true` — the seeder *is* the official deployment path (E4,
   `bundle-format.md` §1.1). `FAILED` fails the runner and prints the version's `errors`.

An unset or empty directory seeds no games and logs one `INFO` line saying so; it is not an error. The
directory is **empty until `IMP-M3-10`** ships the first official game, and that item — which is the
one that produces a real bundle — owns putting the ZIP where the seeder finds it (the compose bind
mount and the chart volume) and proving the game starts. Until then a seeded stack has users, the
friendship and its request, and notifications, but an empty catalog: the "lists and cannot start"
outcome above is avoided by listing nothing rather than something unplayable.

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
| `turnbase.auth.jwt-key-set-required` | `false` | `TURNBASE_JWT_KEY_SET_REQUIRED` | IMP-GATE-16 |
| `turnbase.accounts.rename-window` | `30d` | `TURNBASE_ACCOUNTS_RENAME_WINDOW` | FR-ACCT-002, FR-ACCT-003 |
| `turnbase.social.friend-cap` | `50` | `TURNBASE_SOCIAL_FRIEND_CAP` | FR-SOC-009, NFR-SOC-SCALE-001 |
| `turnbase.pagination.default-page-size` | `25` | `TURNBASE_PAGINATION_DEFAULT_PAGE_SIZE` | FR-CAT-004, FR-HIST-026 |
| `turnbase.pagination.max-page-size` | `100` | `TURNBASE_PAGINATION_MAX_PAGE_SIZE` | pagination-filtering-sorting.md |
| `turnbase.auth.oauth.state-ttl` | `5m` | `TURNBASE_AUTH_OAUTH_STATE_TTL` | `oauth-rest-api.md` §3 |
| `turnbase.auth.oauth.pending-registration-ttl` | `10m` | `TURNBASE_AUTH_OAUTH_PENDING_REGISTRATION_TTL` | `oauth-rest-api.md` §2 |
| `turnbase.oauth.google.authorization-endpoint` | `https://accounts.google.com/o/oauth2/v2/auth` | `TURNBASE_OAUTH_GOOGLE_AUTHORIZATION_ENDPOINT` | Google's own URL; overridden only by tests |
| `turnbase.oauth.google.token-endpoint` | `https://oauth2.googleapis.com/token` | `TURNBASE_OAUTH_GOOGLE_TOKEN_ENDPOINT` | Google's own URL; overridden only by tests |
| `turnbase.oauth.google.userinfo-endpoint` | `https://openidconnect.googleapis.com/v1/userinfo` | `TURNBASE_OAUTH_GOOGLE_USERINFO_ENDPOINT` | Google's own URL; overridden only by tests |

`session-ttl` governs both registered and guest tokens (FR-GUEST-003 defines the guest lifetime as
"the same platform-configurable value"), which is why there is one key and not two — and why
`retention.guest-account` in §7.3 must track it. They are separate keys because the retention job's
window is the thing the *purge* reads, and a future decision to keep a revoked guest row longer than
its token should not require changing the token lifetime.

`jwt-key-set-required` is the only property in this document that is not itself a tunable value —
it is a switch between the two Kubernetes/compose deployment shapes §4 puts under the identical
`local` Spring profile, since profile alone cannot tell the JWT key loader which one it is running
under. `secrets-and-configuration.md` §3.1 is the authority on what it changes.

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
*Configuration* and is not duplicated here. The keys are all under `turnbase.rate-limit.*`; the ones
that are not tier budgets:

| Property | Default | Env | Note |
|---|---|---|---|
| `turnbase.rate-limit.enabled` | `true` | `TURNBASE_RATE_LIMIT_ENABLED` | master switch; gates Tiers 1 to 6. `false` is honoured **only** under the `test`, `e2e` or `loadtest` profile; the application fails to start otherwise |
| `turnbase.rate-limit.switches.auth-lockout` | `true` | `TURNBASE_RATE_LIMIT_SWITCHES_AUTH_LOCKOUT` | Tier 1 |
| `turnbase.rate-limit.switches.api` | `true` | `TURNBASE_RATE_LIMIT_SWITCHES_API` | Tier 2 |
| `turnbase.rate-limit.switches.upload` | `true` | `TURNBASE_RATE_LIMIT_SWITCHES_UPLOAD` | Tier 3 |
| `turnbase.rate-limit.switches.public` | `true` | `TURNBASE_RATE_LIMIT_SWITCHES_PUBLIC` | Tier 4 |
| `turnbase.rate-limit.switches.guest-minting` | `true` | `TURNBASE_RATE_LIMIT_SWITCHES_GUEST_MINTING` | Tier 5, guests |
| `turnbase.rate-limit.switches.registration-minting` | `true` | `TURNBASE_RATE_LIMIT_SWITCHES_REGISTRATION_MINTING` | Tier 5, registrations |
| `turnbase.rate-limit.ws.switches.connection` | `true` | `TURNBASE_RATE_LIMIT_WS_SWITCHES_CONNECTION` | Tier 6 backstop bucket |
| `turnbase.rate-limit.ws.switches.snapshot` | `true` | `TURNBASE_RATE_LIMIT_WS_SWITCHES_SNAPSHOT` | Tier 6 |
| `turnbase.rate-limit.ws.switches.action` | `true` | `TURNBASE_RATE_LIMIT_WS_SWITCHES_ACTION` | Tier 6 |
| `turnbase.rate-limit.ws.switches.chat` | `true` | `TURNBASE_RATE_LIMIT_WS_SWITCHES_CHAT` | Tier 6 |
| `turnbase.rate-limit.ws.switches.command` | `true` | `TURNBASE_RATE_LIMIT_WS_SWITCHES_COMMAND` | Tier 6 |
| `turnbase.rate-limit.ws.switches.subscribe` | `true` | `TURNBASE_RATE_LIMIT_WS_SWITCHES_SUBSCRIBE` | Tier 6 |
| `turnbase.rate-limit.ws.switches.violation-lockout` | `true` | `TURNBASE_RATE_LIMIT_WS_SWITCHES_VIOLATION_LOCKOUT` | Tier 6 violation counting, force-close and lockout |
| `turnbase.rate-limit.ws.switches.max-connections-per-user` | `true` | `TURNBASE_RATE_LIMIT_WS_SWITCHES_MAX_CONNECTIONS_PER_USER` | Tier 6 connection cap |
| `turnbase.security.trusted-proxies` | `10.0.0.0/8,172.16.0.0/12` | `TURNBASE_SECURITY_TRUSTED_PROXIES` | Client-IP derivation. Wrong here means every IP-keyed tier keys on the ingress |

A mechanism acts only when the master switch **and** its own switch are both `true`. With the master
switch or any switch off, the application starts only when the `test`, `e2e` or `loadtest` profile is
active; `local` alone does not permit it, and the refusal message names every disabled switch by
property name.

**The `loadtest` profile** (`load-testing.md` §4 A1a) turns every switch off except
`turnbase.rate-limit.ws.switches.max-connections-per-user` and leaves the master switch on. It is never
activated by default; the load-test Helm overlay sets `SPRING_PROFILES_ACTIVE=local,loadtest`.

### 7.7 Origins

| Property | Default (local) | Env |
|---|---|---|
| `turnbase.platform.origin` | `http://turnbase.localhost:8080` | `TURNBASE_PLATFORM_ORIGIN` |
| `turnbase.game-frontend.origin-template` | `http://{gameId}.games.localhost:8080` | `TURNBASE_GAME_FRONTEND_ORIGIN_TEMPLATE` |

The Frontend container reads both (same names, one source in compose/Helm), plus
`TURNBASE_FRONTEND_UPSTREAM` (default `platform:8080`), the monolith address nginx proxies to. It
consumes them at container start — nginx's official image renders `/etc/nginx/templates/*.template`
with `envsubst` — never at build time, for the reason `game-asset-serving.md` §3.1 gives: the same
image must serve every environment. `frame-src` is *derived* from the template in
`game-asset-serving.md` §6.3, not restated.

These two must remain different **registrable domains** (ADR-0007). Setting the games template to a
subdomain of the platform origin silently removes the isolation that
`rest-conventions.md`'s CSRF argument depends on, and nothing will fail — which is why the monolith
asserts the difference at startup and refuses to boot if it does not hold.

### 7.8 Game Host

| Property | Default | Env | Source |
|---|---|---|---|
| `turnbase.gamehost.grpc.port` | `9090` | `TURNBASE_GAMEHOST_GRPC_PORT` | IMP-GATE-17 |
| `turnbase.gamehost.handler-timeout` | `30s` | `TURNBASE_GAMEHOST_HANDLER_TIMEOUT` | FR-CTX-008 |
| `turnbase.gamehost.boot-timeout` | `20s` | `TURNBASE_GAMEHOST_BOOT_TIMEOUT` | longest a guest-JVM boot (warm-up or a new context) may run before the host declares itself wedged, deregisters and exits with code 70; `0` disables. `game-host-internals.md` §11, [ADR-0018](../../decisions/0018-game-start-resilience.md). Compose runs the service with `restart: unless-stopped` so the exit is followed by a fresh boot. The image's `docker/supervise.sh` entrypoint additionally kills, and respawns in place, a JVM that stops answering `/actuator/health/liveness` (`TURNBASE_SUPERVISOR_GRACE` 45 s, `TURNBASE_SUPERVISOR_FAILURES` 4, `TURNBASE_SUPERVISOR_PIDFILE` `/tmp/jvm.pid`, `TURNBASE_SUPERVISOR_MARKER` `/tmp/turnbase-wedged`, `TURNBASE_SUPERVISOR_MAX_DEATHS` 5, `TURNBASE_SUPERVISOR_WINDOW` 600 s) |
| `turnbase.gamehost.max-concurrent-boots` | `2` | `TURNBASE_GAMEHOST_MAX_CONCURRENT_BOOTS` | most guest-JVM boots that run at once; further boots queue, fairly, and their `boot-timeout` starts when they get a permit, not when they queue (at least `1`). `game-host-internals.md` §6.1 |
| `turnbase.gamehost.warmup-enabled` | `false` | `TURNBASE_GAMEHOST_WARMUP_ENABLED` | runs the throwaway warm-up session before `Register`. Off by default: with it on, 27.5 % of cold starts wedged on their first real guest boot (5 % with it off). `game-host-internals.md` §11 *Boot-wedge measurement* |
| `turnbase.gamehost.wedge-marker` | `/tmp/turnbase-wedged` | `TURNBASE_GAMEHOST_WEDGE_MARKER` | file `HostWedge` writes on a wedged guest boot; `docker/supervise.sh` watches the same path (`TURNBASE_SUPERVISOR_MARKER`) and SIGKILLs and respawns the JVM at once. `game-host-internals.md` §11, [ADR-0018](../../decisions/0018-game-start-resilience.md) |
| `turnbase.gamehost.interrupt-escalation-grace` | `5s` | `TURNBASE_GAMEHOST_INTERRUPT_ESCALATION_GRACE` | game-host-internals §15 |
| `turnbase.gamehost.drain-period` | `30s` | `TURNBASE_GAMEHOST_DRAIN_PERIOD` | `IMP-M18-13`: after `SIGTERM` the host announces `draining` on its next heartbeat and keeps serving its sessions for up to this long (less when it holds none), then deregisters; the gRPC server stops after. Must fit in the pod's `terminationGracePeriodSeconds` (90 s) with the gRPC server's own wait |
| `turnbase.gamehost.max-context-creations` | `12` | `TURNBASE_GAMEHOST_MAX_CONTEXT_CREATIONS` | `IMP-M20-18`: how many Espresso contexts one JVM can create in its lifetime (a glibc limit, measured at twelve). The creation past it answers `UNAVAILABLE` and the host drains, exits and is restarted by the supervisor. The warm-up context counts. `game-host-internals.md` §18 `OQ-6` |
| `turnbase.gamehost.context-idle-eviction` | `5m` | `TURNBASE_GAMEHOST_CONTEXT_IDLE_EVICTION` | FR-CTX-009 |
| `turnbase.gamehost.memory-pressure-threshold` | `80%` | `TURNBASE_GAMEHOST_MEMORY_PRESSURE_THRESHOLD` | FR-CTX-010 |
| `turnbase.gamehost.redis-unavailable-window` | `60s` | `TURNBASE_GAMEHOST_REDIS_UNAVAILABLE_WINDOW` | game-host-internals §9.4 |
| `turnbase.gamehost.retry-limit` | `3` | `TURNBASE_GAMEHOST_RETRY_LIMIT` | FR-FAIL-003 |
| `turnbase.gamehost.grpc.max-message-size` | `32MB` | `TURNBASE_GAMEHOST_GRPC_MAX_MESSAGE_SIZE` | protocol doc |
| `turnbase.gamehost.guest-java-home` | `/opt/graalvm-guest-jdk21` | `TURNBASE_GAMEHOST_GUEST_JAVA_HOME` | game-host-internals §15 |
| `turnbase.gamehost.advertised-address` | *(absent)* | `TURNBASE_GAMEHOST_ADVERTISED_ADDRESS` | what `RegisterRequest.address` carries. Four-step resolution: a value containing `:` verbatim; otherwise the value plus `:` and `grpc.port`; blank or absent, the local host name plus the port; `localhost:` plus the port if the host name does not resolve. The chart sets it from the pod IP. An IPv6 literal must be bracketed with its port (`[fd00::1]:9090`); a bare one is unsupported. `orchestration-gamehost-protocol.md` *Addressing the Game Host pods* |
| `turnbase.gamehost.orchestration-address` | `platform:8080` | `TURNBASE_GAMEHOST_ORCHESTRATION_ADDRESS` | IMP-GATE-09 |
| `turnbase.gamehost.sdk-jar-path` | `/opt/turnbase/guest-bridge.jar` | `TURNBASE_GAMEHOST_SDK_JAR_PATH` | game-host-internals §4.2 |
| `turnbase.gamehost.artifact-cache-dir` | `/var/lib/turnbase/game-host/artifact-cache` | `TURNBASE_GAMEHOST_ARTIFACT_CACHE_DIR` | FR-LOAD-003 |
| `turnbase.gamehost.artifact-cache-size-limit` | `512MB` | `TURNBASE_GAMEHOST_ARTIFACT_CACHE_SIZE_LIMIT` | FR-LOAD-004 |

The heartbeat interval and lease TTL are **not** configured on the Game Host: they are handed to it
in `RegisterResponse`, so the monolith owns both sides of the liveness contract and they cannot be
set inconsistently.

**`turnbase.gamehost.orchestration-address` is where the Game Host dials `GameHostRegistryService`**
for `Register`/`Heartbeat`/`ReportContexts`/`Deregister` (§2's `gRPC :8080` edge — the registry service
shares the monolith's HTTP listener rather than opening a second port). The default follows §2's
`<service-name>:<port>` convention for every other compose dependency (`postgres:5432`, `redis:6379`,
`minio:9000`); under Kubernetes it resolves to the Platform Monolith's Service DNS name instead. No
TLS, per §2's "one network, flat."

**Platform side — the Orchestration Service** (`IMP-GATE-87`). These are the monolith's own properties;
the Game Host does not read them.

| Property | Default | Env | Source |
|---|---|---|---|
| `turnbase.orchestration.heartbeat-interval` | `5s` | `TURNBASE_ORCHESTRATION_HEARTBEAT_INTERVAL` | `RegisterResponse.heartbeat_interval_seconds` |
| `turnbase.orchestration.lease-ttl` | `15s` | `TURNBASE_ORCHESTRATION_LEASE_TTL` | `RegisterResponse.lease_ttl_seconds`; three intervals, under NFR-REL-002's 30 s |
| `turnbase.orchestration.host-wait` | `40s` | `TURNBASE_ORCHESTRATION_HOST_WAIT` | how long each `CreateSession` attempt of a start waits for a Game Host to register, polling every 500 ms; covers a cold stack and a host being restarted after a wedge. `0` fails at once ([ADR-0018](../../decisions/0018-game-start-resilience.md)) |
| `turnbase.orchestration.quarantine-ttl` | `60s` | `TURNBASE_ORCHESTRATION_QUARANTINE_TTL` | how long a host that timed out a `CreateSession` is skipped by host selection, whichever way its lease stands |
| `turnbase.orchestration.dispatch-deadline` | `35s` | `TURNBASE_ORCHESTRATION_DISPATCH_DEADLINE` | deadline on `CreateSession`/`ProcessInput`/`Resync`; must exceed `turnbase.gamehost.handler-timeout` (30s) by the transport overhead (`orchestration-gamehost-protocol.md` *Error model*) |

`TerminateSession`'s deadline is not configurable: it is a fixed 2 s
(`orchestration-gamehost-protocol.md` *Processing semantics*), because it executes no game code.

### 7.9 Infrastructure

**Phase B budget (ADR-0020, `load-testing-phase-b.md` §3.1, §4.4; applied by `IMP-M18-02` onwards).** In the
load-test overlays PostgreSQL moves to 4 CPU / 2 GiB and the Game Host to 2 CPU in total (two replicas of 1 CPU
at the minimum; 1.5 CPU each since `IMP-M18-13`, below). At the replica maxima, all at `requests == limits`: PostgreSQL 4 + Redis 1 + Game Host 3 × 1 +
Platform 3 × 1.5 = 12.5 CPU, plus k6 pinned to 3 cores = 15.5 of the node's 16. PostgreSQL's `max_connections`
covers `platform.maxReplicas × poolMaxSize` (3 × 10) plus migrations and operators. `IMP-M18-02` applied the
PostgreSQL and Game Host figures (one Game Host replica of 2 CPU until `IMP-M18-13`) and rescaled
`postgres.settings` below.

**Game Host autoscaling and the budget as built (`IMP-M18-13`, session 253).** KEDA (chart pinned in `loadtest/install.sh`) owns the Game Host's replicas through a `ScaledObject` (`gamehost.autoscaling`): two triggers over the Platform's gauges in Prometheus, `max(turnbase_gamehost_sessions_utilization)` against 0.7 and `max(turnbase_gamehost_memory_max_percent)` against 85, `minReplicaCount` 2, `maxReplicaCount` 3, scale-out one pod per 60 s with no stabilisation, scale-in one pod per 120 s after 180 s. The sessions gauge is active sessions of non-draining hosts over hosts × the cap, so a load only scales the fleet once it holds more than 0.7 × 100 × hosts concurrent sessions: 170 and 185 pairs of `gamehost-scale.sh` sat at 0.65 to 0.77 and did not always cross (no third pod within 400 s in two runs), 200 pairs crossed within 70 s. The 1-CPU Game Host tripped the 20 s `BootWatchdog` when the third replica booted under load (`load-testing.md` finding 8), so the §4.4 fallback applies: **Game Host 1.5 CPU / 2 GiB**. A Platform at 3 × 1.5 CPU and a Game Host at 3 × 1.5 CPU are 4.5 + 4.5 + PostgreSQL 4 + Redis 1 = 14 CPU of requests, plus k6's 3 pinned cores = 17 of the node's 16: the two maxima are reached by different loads (CPU for the Platform, sessions for the Game Host) and the requests alone fit. Memory did not: at 2 GiB a replica, three Platform pods and three Game Hosts plus PostgreSQL (2 GiB), Redis and the system pods are 15.4 GiB of requests against 15.1 GiB allocatable, and the third Game Host stayed `Pending` (`Insufficient memory`) for minutes while the Platform's third pod held the memory: seen in the run that timed out at 241 s (`FailedScheduling` in the pod's events), and probably the 210 s wait of the first run too (no events were kept then). The Platform is therefore **1.5 CPU / 1536 Mi** (it used 750 Mi at rest; heap is 70 % of the limit). A host whose lease lapses without a deregistration (a pod removed hard) leaves its `host:` entry behind but is excluded from every gauge (`HostRegistry.loads()` checks the lease; `GameHostRegistryServerIT` asserts it).

**Per-host session cap (`IMP-M18-11`).** `turnbase.orchestration.max-sessions-per-host` (`TURNBASE_ORCHESTRATION_MAX_SESSIONS_PER_HOST`, FR-SCALE-005) defaults to **100**. Sizing: in the `m18-baseline` report one Game Host of 2 CPU carried 165 to 170 sessions at the abort using about 1.2 of its 2 cores, so a Phase B replica of 1 CPU is sized at about 100, which leaves headroom for the guest start burst. A host at the cap is skipped by selection (`game-host-internals.md` §11); the cap is read from the `activeSessions` the host last heartbeated, so it is approximate between heartbeats.

**Warm hosts (`IMP-M18-13`).** `turnbase.orchestration.warm-hosts` (`TURNBASE_ORCHESTRATION_WARM_HOSTS`) defaults to **2**: while fewer hosts than this hold a game's context, a new session goes to a cold host below its cap, so the second replica is warmed by a real start and a drain or failover does not meet a cold boot.

**Platform autoscaling (`IMP-M18-10`).** Both overlays render the HPA (`platform.autoscaling`): CPU utilisation
target 40 % of the 1.5-CPU request, `minReplicas` 2, `maxReplicas` 3, scale-out at one pod per 30 s with no
stabilisation, scale-in at one pod per 60 s after a 120 s stabilisation window. Each replica has 1.5 CPU and
2 GiB at `requests == limits`, so the Platform at its maximum is 3 × 1.5 = 4.5 CPU and 6 GiB. With the Game Host
still at one replica of 2 CPU / 4 GiB (until `IMP-M18-13`), the requests total 4 (PostgreSQL) + 1 (Redis) +
2 (Game Host) + 4.5 (Platform) = 11.5 CPU and 2 + 0.5 + 4 + 6 = 12.5 GiB of memory, inside the node's 16 CPU and
15 GiB; with the Game Host at three replicas of 1 CPU the CPU total is the 12.5 above. `max_connections` stays 50
(3 × 10 pool connections plus operators). With an HPA the Deployment omits `replicas` (the HPA owns it), so
`loadtest/install.sh`, which stops the application pods before an overlay switch, deletes the HPA first and
starts one Platform pod afterwards for the HPA to take to its minimum. `loadtest/run.sh` still pins k6 to four
cores; the three cores of the budget are `IMP-M18-14`'s to apply.

**Scale-in drain (`IMP-M18-10`).** On `SIGTERM` (Spring's `ContextClosedEvent`, after the 5 s `preStop` pause
and readiness off) `room.RoomDrain` refuses every claim of a room the instance does not own, then for each
owned room takes the room lock (an in-flight mutation finishes), sends `RECONNECT_REQUIRED` to its sockets
(tagged instance-initiated, so no disconnect is processed) and releases it, and last deletes the liveness key
and stops its renewal. The next claimant takes the free branch with no lease wait and logs `adopted room`.
`loadtest/test/scale-in-midgame.sh` checks it on the cluster. A REST call for a room that another instance owns
answers `503 ROOM_UNAVAILABLE_RETRY` (the claim finds a live owner), so at two or more replicas a client retries
it and the round-robin finds the owner; the k6 pairs of `scenarios/scale-in.js` do the same.

| Property | Default | Env |
|---|---|---|
| `spring.datasource.url` | `jdbc:postgresql://postgres:5432/turnbase` | `SPRING_DATASOURCE_URL` |
| `spring.datasource.username` | `turnbase_app` | `SPRING_DATASOURCE_USERNAME` |
| `spring.datasource.hikari.maximum-pool-size` | `10` — explicit in `application.yml`, never Hikari's library default; `FR-DBQ-006` governs the value; chosen by measurement (`IMP-M17-04`, [report](../../../loadtest/reports/2026-10-23-m17-pool-sizing.md)): `parallelism` at 5, 10 and 20 connections, ceiling 64 pairs for all three, peak 1,452, 1,755 and 1,714 moves/s, so 20 ties 10 within 5% and the smallest tied pool, 10, stays; chart value `platform.db.poolMaxSize` | `SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE` |
| `spring.data.redis.host` | `redis` | `SPRING_DATA_REDIS_HOST` |
| `spring.data.redis.port` | `6379` | `SPRING_DATA_REDIS_PORT` |
| `spring.data.redis.password` | **no default** — secret, `secrets-and-configuration.md` § Redis (`TURNBASE_REDIS_PASSWORD`) | `SPRING_DATA_REDIS_PASSWORD` |
| `turnbase.artifact-store.endpoint` | `http://minio:9000` | `TURNBASE_ARTIFACT_STORE_ENDPOINT` |
| `turnbase.artifact-store.bucket` | `turnbase-bundles` | `TURNBASE_ARTIFACT_STORE_BUCKET` |
| `turnbase.artifact-store.access-key` / `secret-key` | **no default** — the scoped service credential, never the MinIO root pair (§5, `secrets-and-configuration.md` § MinIO / S3) | `TURNBASE_ARTIFACT_STORE_ACCESS_KEY` / `TURNBASE_ARTIFACT_STORE_SECRET_KEY` |
| `management.server.port` | `8081` | `MANAGEMENT_SERVER_PORT` |
| `management.server.address` | **unset**, both profiles (§1 — compose restricts by publishing the port to `127.0.0.1` on the host, not by the app's own bind address) | `MANAGEMENT_SERVER_ADDRESS` |
| `logging.level.root` | `INFO` | `LOGGING_LEVEL_ROOT` |
| `management.otlp.tracing.endpoint` | `http://tempo:4318/v1/traces` (OTLP/HTTP — Micrometer's exporter cannot speak gRPC, so it must not be pointed at `4317`) | `MANAGEMENT_OTLP_TRACING_ENDPOINT` |
| `management.tracing.sampling.probability` | `0.1` | `MANAGEMENT_TRACING_SAMPLING_PROBABILITY` |
| `spring.profiles.active` | `local` | `SPRING_PROFILES_ACTIVE` |

**Redis is addressed by `host` + `port`, never by `spring.data.redis.url` (`IMP-GATE-77`).** Spring Boot's `url`
property takes precedence over `host`, `port`, `username` **and `password`**: with a `url` set, the
credential comes from the URL's userinfo or is absent, and `SPRING_DATA_REDIS_PASSWORD` is silently
ignored — Redis then answers `NOAUTH` and the service exits during startup. No committed configuration
sets `url`. (Integration tests may pass `--spring.data.redis.url` for a password-less Testcontainers
instance; that is the one legitimate use.) The datasource pair is different — `spring.datasource.url`
is JDBC and carries no credential, so it and `spring.datasource.password` compose.

Pool size 10 against FR-ALERT-004's 80 % saturation alert means the alert fires at 8 concurrent
checkouts. The deadline sweep runs every 5 seconds and the reconcile sweep every 60; neither holds a
connection between rows.

**PostgreSQL server settings (`FR-DBQ-007`).** The chart's `postgres.settings` renders `-c name=value`
arguments for the Phase B 4 CPU / 2 GiB (`IMP-M18-02`; the 2 CPU / 1 GiB values of M17 are in the git history):

| Setting | Value | Reason |
|---|---|---|
| `shared_buffers` | `512MB` | 25% of the memory limit |
| `effective_cache_size` | `1GB` | half of the memory limit |
| `max_connections` | `50` | `platform.maxReplicas × poolMaxSize` (3 × 10) plus migrations and operators; the image default of 100 reserves memory for connections nobody opens |
| `max_wal_size` / `checkpoint_completion_target` | `2GB` / `0.9` | fewer, smoother checkpoints under a write-heavy game path |
| `random_page_cost` | `1.1` | the volume is an SSD |
| `max_worker_processes`, `max_parallel_workers` | `4`, `4` | the core count |
| `max_parallel_workers_per_gather`, `max_parallel_maintenance_workers` | `2`, `2` | half the cores, so one query cannot take them all |

`synchronous_commit` stays on: the game path does not trade durability for speed. M17 history: the settings were
applied after `IMP-M17-05`'s `parallelism` and `ramp-to-break` runs named `PostgreSQL` as the first to break
([reports](../../../loadtest/reports/2026-10-24-m17-ramp-to-break.md)); the limit then was the 2-core CPU, which
settings do not add. With the 4 cores of `IMP-M18-02` the baseline ([report](../../../loadtest/reports/2026-10-24-m18-baseline.md))
reaches 128 pairs in `parallelism` and 220 in `ramp-to-break`, with PostgreSQL at 2.1 to 2.4 of 4 cores.

Credentials are **not** in this table. They are in
[`secrets-and-configuration.md`](secrets-and-configuration.md).

### 7.10 Seed data

| Property | Default | Env | Source |
|---|---|---|---|
| `turnbase.seed.bundles-dir` | *(unset)* | `TURNBASE_SEED_BUNDLES_DIR` | §6 — read only under the `local` and `e2e` profiles |

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

**E2E runs with the master rate-limit switch off.** The master switch or any per-mechanism switch may
be off only under the `test`, `e2e` or `loadtest` profile, and the application refuses to start
otherwise (§7.6). E2E is a place the escape hatch is legitimate, and it is profile-gated for exactly
that reason
([`../api-design/rate-limiting.md`](../api-design/rate-limiting.md)): the GRMP prototype's hardcoded
login limit blocked every test session for months, and the workaround was deleting Redis keys by
hand.

Two things the sweep intervals do to tests, worth knowing before writing one:

- A test of grace expiry must either wait out `grace-period + deadline-sweep.interval` or override
  both. Overriding is right; sleeping 65 seconds in a test suite is not.
- A test of reconciliation must clear `reconcile.startup-suppression`, which is 120 seconds and will
  otherwise make every repair assertion fail with no repair and no error — the sweep detects, logs,
  and deliberately does nothing (`room-lifecycle.md` §5.4).

### Recovery from a full stop (`IMP-M20-16`)

`node scripts/recovery-test.mjs [--kill]` is the repeatable test of the single-instance profile
([ADR-0021](../../decisions/0021-deployment-profiles.md)). It starts the compose stack with
`scripts/recovery-compose.override.yml` (grace 30 s, migration window 5 s, deadline sweep 2 s, reconcile
interval 10 s), builds three rooms, stops **every** container for 40 s, which is longer than the grace period,
the 35 s dispatch deadline and the 10 s lease TTL, starts them again, and asserts:

| Room | Before the stop | After the start |
|---|---|---|
| `G` | in progress, two moves played, both players connected | adopted at a higher epoch; the session record is intact (same board, `onInit` not re-run); nobody released; both players return, the game resumes and finishes |
| `A` | in progress, both players connected | nobody returns: closed `GRACE_EXPIRED_NO_HUMAN` once grace, counted from adoption, elapses; `session:`/`queue:` keys torn down; `room:A:pod` deleted |
| `L` | lobby, host connected | still `LOBBY`, not closed `GRACE_EXPIRED_NO_HUMAN` even after the host's grace elapsed (FR-DC-007) |

It also asserts that exactly one liveness lease exists afterwards, a new incarnation, that `room:G:pod` names it,
and that the Game Host registers again. `--kill` replaces `SIGTERM` with `SIGKILL` (the crash path). Both
variants pass. Prerequisites are those of the `run-turnbase` skill (the three `:dev` images, seed bundles,
`turnbase-game-tictactoe/node_modules/ws`); it uses one guest account, so it can run five times an hour per IP.

**The order of the stop matters, and the test stops the Platform first.** The Platform's drain tags the sockets it
closes, so nothing opens a reservation before the stop and the deadlines start at adoption
(room-lifecycle.md §1.4 step 4, §1.6). When the Frontend stops first (the order `docker compose stop` takes), the
proxy drops every socket while the Platform is alive; those are ordinary disconnects, which open a 30 s
reservation in each in-progress room and close each Lobby room at once (FR-DC-002). A 40 s outage then
resolves every in-progress room after the restart. That follows the specification as written, so it is a
property of the stop order and not a defect, but it means "restart the stack" and "restart the stack gracefully"
differ for the players in it: stop the Platform first when games are running.

---

### Startup time (`IMP-M20-17`)

`scripts/startup-time.sh <platform|gamehost> [runs]` stops one compose service, starts it and polls
`/actuator/health` until it answers 200; the figure is container start to ready. Median of five, same
jars, 2026-11-06, with other containers on the machine:

| Variant | Platform | Verdict |
|---|---|---|
| Baseline (Game Host: 8.6 s) | 9.6 s | — |
| Dynamic CDS (`-XX:+AutoCreateSharedArchive`) | 8.4 s (−13 %) | **Rejected** |
| `-XX:TieredStopAtLevel=1` | 10.1 s | Rejected: slower, and caps peak throughput |
| `-XX:+UseSerialGC` | 9.5 s | Rejected: no gain, changes the collector |
| `spring.main.lazy-initialization=true` | 8.9 s | Rejected: moves wiring failures from boot to first request |

CDS is rejected for both services. The archive is written at JVM exit into the container's own
filesystem, so a Kubernetes pod, which is replaced and never restarted, never reuses it: the gain exists
only where containers are restarted in place. Running it beside the OpenTelemetry agent needs
`-XX:+UnlockDiagnosticVMOptions -XX:+AllowArchivingWithJavaAgent`, and without that flag the JVM exits 1 and
the container crash-loops. On the Game Host the dump at shutdown ran past the supervisor's four silent
probes, which SIGKILLed the JVM mid-dump (exit 137) and never produced the archive; the Truffle classes
dominate its start in any case. A build-time archive would avoid both problems but needs a training run that
boots the application, which needs PostgreSQL and Redis inside `docker build`; not worth a 1 s gain. Revisit
if the platform start is ever on a request path (scale-to-zero).

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
