# Observability — Metrics, Logs, Traces and Alerts

The wiring between the four observability containers of
[`local-environment.md`](local-environment.md) §1 and the requirements that name them.
`../../requirements/platform-operations.md` owns **what** must be observable — FR-OBS-001…005,
FR-MET-001…007, FR-TRACE-001…004, FR-ALERT-001…007, CON-003…006. This document owns **how**.

Closes review blocker **IR-04**: Prometheus, Grafana, Loki and Tempo were listed containers with
nothing between them and the requirement text, and all ten `FR-MET-*`/`FR-TRACE-*` requirements were
cited by no spec anywhere in the corpus.

`platform-operations.md` OQ-003 makes the full Grafana stack a **primary learning goal** of the
project rather than a nice-to-have, so this is scoped as complete wiring — dashboards provisioned,
alerts evaluating — not as a minimum that happens to satisfy the words.

---

## 1. The four signals

| Signal | Producer | Transport | Store | Requirements |
|---|---|---|---|---|
| **Metrics** | Micrometer in each JVM | Prometheus **scrapes** `/actuator/prometheus` on the management port | Prometheus | FR-MET-001…007, CON-003 |
| **Logs** | Logback JSON encoder → stdout | Promtail tails the container log files and **pushes** | Loki | FR-OBS-001…005, CON-004 |
| **Traces** | OpenTelemetry Java agent | OTLP/gRPC **push** to `tempo:4317` | Tempo | FR-TRACE-001…004, CON-005 |
| **Alerts** | Prometheus rule evaluation | Alertmanager | — | FR-ALERT-001…007 |
| **Dashboards** | — | Grafana queries all three | Grafana | CON-006, NFR-OBS-001 |

**Metrics are pulled and the other two are pushed**, and that asymmetry is not an accident of tooling.
A scrape target that stops responding is *itself* a signal — Prometheus records `up == 0` and can
alert on it — whereas a service that stops pushing logs is indistinguishable from a service with
nothing to say. Liveness belongs on the pull path.

---

## 2. Metrics

### Exposure

Spring Boot Actuator with the Micrometer Prometheus registry. `management.server.port` is `8081`
(`local-environment.md` §7.9), and `/actuator/prometheus` is exposed there and nowhere else.

**Prometheus scrapes the management port, never the public one.**
[`../api-design/rest-conventions.md`](../api-design/rest-conventions.md) already states the rule —
"`/actuator/prometheus` (FR-MET-007) is scraped over the cluster-internal network, never through the
ingress" — and it matters here because the same listener carries the admin API (`admin-tooling.md`
FR-ADM-001). Adding an ingress rule to make scraping convenient would publish the admin API with it.

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: platform
    metrics_path: /actuator/prometheus
    static_configs: [{ targets: ['platform:8081'] }]
  - job_name: gamehost
    metrics_path: /actuator/prometheus
    static_configs: [{ targets: ['gamehost:8081'] }]
```

Under Kubernetes the two `static_configs` become a `kubernetes_sd_config` on pod annotations; the
scrape path and port do not change.

### What each requirement maps to

| Requirement | Metric | Source |
|---|---|---|
| FR-MET-001 | `http_server_requests_seconds{uri,method,status}` — count, histogram, error rate | Actuator, automatic |
| FR-MET-002 | `turnbase_websocket_connections_active` | A `Gauge` bound to the STOMP session registry |
| FR-MET-003 | `turnbase_rooms_active`, `turnbase_game_sessions_active`, `turnbase_users_registered`, `turnbase_friend_requests_pending` | §2.1 |
| FR-MET-004 | `hikaricp_connections_*`, `spring_data_repository_invocations_seconds` | Actuator, automatic |
| FR-MET-005 | `turnbase_redis_operation_seconds{concern}` and `turnbase_redis_errors_total{concern}` | §2.2 |
| FR-MET-006 | `jvm_memory_used_bytes`, `jvm_gc_pause_seconds`, `jvm_threads_live_threads` | Micrometer JVM binders, automatic |
| FR-MET-007 | The endpoint above | Actuator |

Four of the seven are automatic. Three are not, and those three are the work.

### 2.1 The business gauges are polled, not incremented

FR-MET-003 says "updated periodically, not per-request", and the parenthesis is the whole design.

Each of the four is a `MultiGauge` refreshed by one scheduled query every 30 seconds — not a counter
maintained by the code paths that create and destroy rooms. Maintaining them inline would put a
metric write inside the room lock, on the hottest transaction in the platform, in exchange for
freshness nobody is looking at: these numbers are read on a dashboard a human refreshes, and a scrape
interval of 15 seconds already bounds their staleness. Worse, an incremented counter **drifts** — one
missed decrement on an error path and the active-room count is permanently wrong with no way to
notice, whereas a polled gauge is self-correcting by construction.

```
turnbase_rooms_active            SELECT count(*) FROM room WHERE state <> 'CLOSED'
turnbase_game_sessions_active    SELECT count(*) FROM room WHERE active_session_id IS NOT NULL
turnbase_users_registered        SELECT count(*) FROM app_user WHERE deleted_at IS NULL
turnbase_friend_requests_pending SELECT count(*) FROM friend_request WHERE status = 'PENDING'
```

All four are index-covered (`data-model.md` §5, `data-model-social.md`) and the refresh holds no
connection between them.

**Under more than one replica these gauges are per-instance and identical**, because each queries the
same database. Grafana must therefore aggregate with `max()` rather than `sum()` — summing them
multiplies the platform's room count by the replica count, which is the kind of dashboard error that
survives for months because the shape of the graph still looks right.

### 2.2 Redis metrics are dimensioned by concern, because one instance serves four

FR-MET-005 requires the dimension and `platform-operations.md` OQ-001 is why: a single Redis instance
holds game state, the action queue, ownership leases and rate-limit counters. An undimensioned
latency histogram over all four is unreadable — a slow bulk operation on game state hides a lease
renewal that has started to miss its deadline, and the lease is the one with a correctness bound
attached (ADR-0008).

`concern` takes exactly four values: `game_state`, `action_queue`, `ownership`, `application`. The tag
is applied at the repository layer, not derived from the key prefix at scrape time, because a key
prefix is a naming convention and a tag is a contract.

FR-MET-005 also states Redis is **not** used for WebSocket pub/sub. There is deliberately no
`concern="pubsub"` value, and its absence is the assertion: fan-out is in-process under room affinity
(ADR-0002).

### 2.3 The three metrics named by other specs

Named elsewhere in the corpus and collected here so nothing owns them only in passing:

| Metric | Named by | Alert |
|---|---|---|
| `turnbase.teardown.owed` | `room-lifecycle.md` §4 | FR-ALERT-007 |
| `turnbase.effect.address_rejected.total{kind}` | [`../api-design/websocket.md`](../api-design/websocket.md) § `GAME_EVENT` | none — WARN log only |
| Per-duty reconciliation counters | `platform-operations.md` FR-JOB-011 | FR-ALERT-006 |

---

## 3. Logs

### Format

Logback with a JSON encoder, one object per line, to **stdout** — never to a file the application
manages. FR-OBS-001 requires the format; CON-004 requires the destination; and stdout is what makes
the container the log's owner rather than the process.

```json
{
  "timestamp": "2026-08-16T10:04:11.482Z",
  "level": "INFO",
  "service": "platform",
  "logger": "io.turnbase.platform.room.RoomService",
  "thread": "http-nio-8080-exec-3",
  "message": "Room claimed",
  "requestId": "0b4c…", "userId": "a1b2…", "roomId": "9c1e…",
  "sessionId": null, "gameId": "3f2b…",
  "traceId": "4bf92f3577b34da6a3ce929d0e0e4736", "spanId": "00f067aa0ba902b7"
}
```

`service`, `timestamp`, `level` and `message` are FR-OBS-002's floor. The five correlation IDs are
FR-OBS-003's list, populated from the MDC and **omitted when absent** rather than written as empty
strings — an absent `roomId` and a blank one are different facts, and Loki's label extraction treats
them differently.

`traceId`/`spanId` are FR-TRACE-003 and are injected by the agent (§4).

### Correlation IDs enter the MDC at exactly four places

FR-OBS-003 requires propagation "to all downstream calls, including gRPC". The MDC is thread-local,
so every boundary that changes threads must re-establish it:

| Boundary | Mechanism |
|---|---|
| HTTP request | A `OncePerRequestFilter` sets `requestId` (from `X-Request-Id` if present, else generated) and `userId` from the principal |
| STOMP frame | A `ChannelInterceptor` sets `requestId` per frame plus `roomId`/`sessionId` from the destination |
| gRPC out | A `ClientInterceptor` copies the MDC into metadata; the Game Host's `ServerInterceptor` restores it |
| Scheduled job / async | Explicit — the sweeps set `roomId` per row they act on |

The fourth is the one that gets missed. A `@Scheduled` method runs on a pool thread with an empty
MDC, so every reconciliation WARN that FR-JOB-011 requires would arrive with no room identifier —
which is precisely the field that makes it actionable.

### Runtime log level, and the endpoint that grants it

FR-OBS-004 requires the level to be adjustable without a restart. `/actuator/loggers/{name}` does
this, and it is a **write** endpoint: a `POST` changes application behaviour at runtime. It is
exposed only on the management port, which is the same control that protects the admin API
(`rest-conventions.md`). Enabling it on the public listener would let anyone set the root logger to
TRACE and turn the platform into its own denial of service.

### Shipping: Promtail, not the Loki Docker driver

Both work. **Promtail is chosen**, and the reason is the bootstrap: the Loki logging driver is a
Docker *plugin* the developer must `docker plugin install` before `docker compose up` will start at
all, and a clean-machine quick start cannot assume a step outside the compose file. A failure there
is also a bad one — the stack refuses to start with an error about a logging driver, which reads as
nothing to do with observability.

Promtail is one more container reading `/var/lib/docker/containers` and pushing to Loki. It costs a
bind mount and buys a `docker compose up` that works on a machine that has never seen this project.

Under Kubernetes the same Promtail configuration runs as a DaemonSet against the node's log
directory; the pipeline stages are identical.

```yaml
# promtail-config.yaml — pipeline stages
- docker: {}                                   # unwrap the Docker envelope
- json:
    expressions: { level: level, service: service, traceId: traceId }
- labels: { level, service }                   # labels only — see below
```

**`traceId` is parsed but not made a label.** Loki labels are an index and a high-cardinality label
set is the standard way to make Loki slow; `traceId` is unique per request. It stays in the log line,
where a Grafana derived field turns it into a link to Tempo (§5).

---

## 4. Traces

### The agent, not manual instrumentation

FR-TRACE-001 names the OpenTelemetry Java agent. It attaches with `-javaagent:` and instruments
Spring MVC, gRPC, JDBC and Lettuce with no code change:

```
JAVA_TOOL_OPTIONS=-javaagent:/opt/opentelemetry-javaagent.jar
OTEL_SERVICE_NAME=platform
OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1
```

`management.otlp.tracing.endpoint` (`local-environment.md` §7.9) carries the same value for Spring's
own Micrometer Tracing bridge; the two must agree, and the agent's variable is the one that decides
where spans actually go.

### Propagation, and the two hops the agent does not cover

FR-TRACE-002 requires one trace across client → WebSocket → Orchestration → gRPC → Game Host. W3C
`traceparent` is the format throughout. The agent handles HTTP and gRPC automatically. Two hops need
explicit work:

- **The STOMP frame.** A WebSocket connection is one long-lived HTTP upgrade; every frame inside it
  is a separate logical request the agent knows nothing about. The `ChannelInterceptor` of §3 also
  reads a `traceparent` STOMP header and starts a span per inbound frame. Without this every action
  in a game session collapses into the span of the *handshake*, which is the trace nobody wants: one
  span, hours long, containing everything.
- **The Redis action queue.** An input is enqueued by one thread and dequeued by another, possibly on
  another instance. The `traceparent` travels **in the queued payload** and the dequeuing side starts
  a child span from it. This is the boundary FR-TRACE-002 names by exception — "there is no Redis
  pub/sub to propagate through" — and the queue is the thing that remains.

### Sampling is head-based at 10%, and FR-TRACE-004 is only partly met

FR-TRACE-004 asks for 10% of routine traffic **and** always-sample on error or high latency. Those
two are in tension: whether a trace is an error is known at its *end*, and a head-based sampler
decides at its start.

The MVP takes `parentbased_traceidratio` at `0.1`
(`management.tracing.sampling.probability`, `local-environment.md` §7.9) and **does not** implement
the always-on-error half. Tail-based sampling requires the OpenTelemetry Collector with a
`tail_sampling` processor — a fifth observability container buffering every span until its trace
completes, which is a real memory budget for a laptop.

**Stated as a gap rather than silently satisfied**, because "10% sampling" and "10% plus every error"
are different systems and only the first is built. The mitigation is that errors are never *only* in
traces: every 5xx is a log line with its `traceId`, and FR-ALERT-001 fires on the metric. The
escalation is the Collector, and nothing here forecloses it — the agent already exports OTLP, so it
is a change of endpoint.

---

## 5. Grafana provisioning

Provisioned from files in the repository, never configured by hand in the UI. A dashboard that exists
only in Grafana's SQLite volume is lost the first time somebody runs `docker compose down -v`, and
the loss is silent.

```
deploy/compose/grafana/
├── datasources/datasources.yaml
└── dashboards/
    ├── dashboards.yaml              # the provider: scan this directory
    ├── platform-overview.json       # FR-MET-001/002/003
    ├── jvm-and-database.json        # FR-MET-004/006
    ├── redis-by-concern.json        # FR-MET-005
    └── room-lifecycle.json          # FR-JOB-011 duty counters, teardown backlog
```

```yaml
# datasources.yaml
apiVersion: 1
datasources:
  - { name: Prometheus, type: prometheus, uid: prom, url: http://prometheus:9090, isDefault: true }
  - { name: Loki, type: loki, uid: loki, url: http://loki:3100,
      jsonData: { derivedFields: [ { name: TraceID, matcherRegex: '"traceId":"(\w+)"',
                                     url: '$${__value.raw}', datasourceUid: tempo } ] } }
  - { name: Tempo, type: tempo, uid: tempo, url: http://tempo:3200 }
```

**The derived field is the payoff for the whole design.** It turns the `traceId` in a log line into a
link to that trace in Tempo — one click from "this request failed" to "here is where it spent its
time". FR-TRACE-003 exists to make this possible and it is the single most useful thing in the stack;
without the derived field the MDC injection is data nobody can traverse.

The Grafana admin password is `GF_SECURITY_ADMIN_PASSWORD`, already inventoried in
[`secrets-and-configuration.md`](secrets-and-configuration.md) §1. Anonymous access is **off** even
locally: Grafana is bound to all interfaces on port 3000 (`local-environment.md` §1) so that a phone
on the same network can reach it, and an unauthenticated Grafana reachable from a LAN exposes every
log line the platform emits.

---

## 6. Alert routing

Rules in Prometheus, notification in Alertmanager — a tenth long-running container.

| Rule | Expression sketch | For | Requirement |
|---|---|---|---|
| `HighErrorRate` | 5xx rate / total rate > 0.01 | 5m | FR-ALERT-001 |
| `HighLatencyP95` | `histogram_quantile(0.95, http_server_requests_seconds_bucket)` > 1 | 5m | FR-ALERT-002 |
| `GameSessionFailureRate` | retry-limit terminations / active sessions > 0.01 | 10m | FR-ALERT-003 |
| `DbPoolSaturated` | `hikaricp_connections_active / hikaricp_connections_max` > 0.8 | 2m | FR-ALERT-004 |
| `ReconciliationRepairsPersist` | repairs applied on > 3 consecutive runs, **or** a room detected-but-unrepaired > 10m | — | FR-ALERT-006 |
| `TeardownOwed` | `turnbase_teardown_owed_age_seconds` > 900 | — | FR-ALERT-007 |

`DbPoolSaturated` fires at 16 of 20 connections (`local-environment.md` §7.9), which is worth knowing
before tuning either number.

`ReconciliationRepairsPersist` has two disjuncts and the second is the important one:
a room the sweep can *see* and cannot *fix* is the failure mode FR-JOB-008's two-strike rule can
otherwise hide forever, because a repair that never applies never increments the repair counter.

### When no webhook is configured

FR-ALERT-005 requires a configurable channel. `TURNBASE_ALERT_WEBHOOK_URL` is **absent by default**
and Alertmanager's receiver is empty when it is unset — the same posture the OAuth client secret
takes (`secrets-and-configuration.md` §1): a local-first project must not require registering with a
third party before the stack will run.

**Rules still evaluate and still fire into Alertmanager when no receiver is configured.** They are
visible in Alertmanager's UI and in Grafana; what is missing is only the delivery. This is stated
because "alerts are configured" and "alerts reach a human" are different claims, and FR-ALERT-005 is
the second one. A developer running locally has the first; a deployment that wants the second sets
one environment variable.

---

## 7. What the local stack does not do

- **No long-term storage.** Prometheus retains 15 days, Loki and Tempo use filesystem storage on a
  local volume. Production is object storage and a retention policy; nothing here forecloses it.
- **No high availability.** One replica of each. The observability stack going down must never take
  the platform with it, which is why every exporter is fire-and-forget and no readiness probe
  consults Prometheus.
- **No tail-based sampling.** §4.
- **No log-based metrics.** Deriving a counter from a Loki query is slower and less reliable than a
  Micrometer counter, and the temptation only arises when someone forgot to add the metric.
- **No profiling (Pyroscope) and no synthetic monitoring.** Neither is named by a requirement.

---

## 8. Requirements traceability

| Requirement | Realized by |
|---|---|
| FR-OBS-001, CON-004 | §3 — Logback JSON to stdout |
| FR-OBS-002 | §3 — the required-field set |
| FR-OBS-003 | §3 — the four MDC boundaries |
| FR-OBS-004 | §3 — `/actuator/loggers` on the management port |
| FR-OBS-005 | `secrets-and-configuration.md` §6, which this document does not restate |
| FR-MET-001, FR-MET-004, FR-MET-006 | §2 — Actuator and Micrometer binders |
| FR-MET-002 | §2 — the STOMP session-registry gauge |
| FR-MET-003 | §2.1 — polled business gauges |
| FR-MET-005 | §2.2 — the `concern` dimension |
| FR-MET-007, CON-003 | §2 — `/actuator/prometheus` and the scrape config |
| FR-TRACE-001, CON-005 | §4 — the OpenTelemetry Java agent |
| FR-TRACE-002 | §4 — W3C propagation plus the STOMP and Redis-queue hops |
| FR-TRACE-003 | §3 log fields, §5 the Grafana derived field |
| FR-TRACE-004 | §4 — **partially**: head-based 10%; always-on-error is a stated gap |
| FR-ALERT-001…004 | §6 rule table |
| FR-ALERT-005 | §6 — configurable webhook, absent by default |
| FR-ALERT-006 | §6 `ReconciliationRepairsPersist` |
| FR-ALERT-007 | §6 `TeardownOwed`; the metric is `room-lifecycle.md` §4's |
| CON-006 | §5 — Grafana over all three stores |
| NFR-OBS-001 | §5 — the log→trace link is what makes post-incident diagnosis possible without live access |
