# Default-limits scenario report, 2026-10-18

**Verdict:** With every limiter enabled the pair path ran with no unexpected error and no 5xx, and the limiters answered: 320 `RATE_LIMIT_EXCEEDED`, one per iteration, from the WebSocket action bucket (inferred from the counts) hit by a no-think client in the third game of each room; HTTP tiers never fired. Single-node, laptop result.

## 1. Run

| Field | Value |
|---|---|
| Scenario | `default-limits`, defaults (20 pairs, 3 min, constant VUs; every limiter enabled: the stock chart, no `loadtest` profile) |
| Parameters (`params.txt`) | `scenario=default-limits`, `K6_CORES=4`, `VUS=20`, `DURATION=3m` |
| Start (UTC) | 2026-10-18T20:28:04Z |
| End (UTC) | 2026-10-18T20:31:24Z |
| Duration | 3 min 20 s (`provision.js` ran earlier under the loadtest overlay, then the stock chart was installed with `install.sh --default-limits`; `setup()` of about 11 s, then 3 min of load) |
| k6 exit code | 0 (every threshold held: no unexpected error, 320 `RATE_LIMIT_EXCEEDED`, no 5xx) |
| k6 version | k6 v2.2.0 (commit/00a9a1b7f5, go1.26.5, linux/amd64) |
| k6 pinned to CPUs | the last 4 of 16 (`taskset`, `K6_CORES=4`) |
| Run directory | `loadtest/results/20261018-222801-default-limits` (git-ignored) |

## 2. Environment

| Field | Value |
|---|---|
| Docker Desktop VM CPUs | 16 |
| Docker Desktop VM memory | 16,326,520,832 bytes (15.21 GiB, `docker info`) |
| `.wslconfig` | absent (VM defaults) |
| Host load during the run | `load1` mean 4.6, max 5.5 on 16 CPUs; `vm_cpu_pct` mean 14.3, max 39; k6 mean 5%, max 12% of one core (`samples.csv`, from the scenario start on) |
| Root commit | d08aa812eed1db11723974ca3d7dfaa54b6b115a |
| `turnbase-common` | 57a102a94421c5b6122d18c1984e5a0b97f5e7bd |
| `turnbase-sdk` | ab3641d692101b829c9702f5e7a1567b45d589a4 |
| `turnbase-platform` | b287e9bcd327f74296a7e623b0fbfbfe7d5c5ca3 |
| `turnbase-game-host` | 4b07fbe6a918b628c901d6d1351b28475de2ee81 |
| `turnbase-frontend` | d5253610130a2415b440c2708e9c1359a0c4b8e8 |
| `turnbase-game-tictactoe` | c5a0d084967919924f36fa395d67bfd371778348 |
| Image IDs | platform `sha256:f0049c5cbd08...`, game-host `sha256:df839d44f5cf...`, frontend `sha256:2b6f793dd2a7...` (full IDs in `cluster.txt`) |
| Ingress path | ingress-nginx -> frontend nginx -> platform |

Chart values (`helm get values turnbase`, secrets redacted):

```yaml
USER-SUPPLIED VALUES:
admin:
  password: <redacted>
  username: admin
auth:
  jwtKeySet: <redacted>
frontend:
  image:
    pullPolicy: Never
gamehost:
  extraEnv:
  - name: JDK_JAVA_OPTIONS
    value: -XX:MaxRAMPercentage=70
  image:
    pullPolicy: Never
  replicaCount: 1
  resources:
    limits:
      cpu: "4"
      memory: 4Gi
    requests:
      cpu: "4"
      memory: 4Gi
minio:
  appAccessKey: <redacted>
  appSecretKey: <redacted>
  rootPassword: <redacted>
  rootUser: <redacted>
oauth:
  google:
    clientId: <redacted>
    clientSecret: <redacted>
observability:
  grafana:
    adminPassword: <redacted>
origins:
  gameFrontendTemplate: http://{gameId}.games.localhost
  platform: http://turnbase.localhost
platform:
  autoscaling:
    enabled: false
  extraEnv:
  - name: JDK_JAVA_OPTIONS
    value: -XX:MaxRAMPercentage=70
  image:
    pullPolicy: Never
  replicaCount: 1
  resources:
    limits:
      cpu: "4"
      memory: 3Gi
    requests:
      cpu: "4"
      memory: 3Gi
  seed:
    bundlesHostPath: /run/desktop/mnt/host/c/Users/Hubert/turnbase-seed
postgres:
  appPassword: <redacted>
  ownerPassword: <redacted>
  resources:
    limits:
      cpu: "2"
      memory: 1Gi
    requests:
      cpu: "2"
      memory: 1Gi
redis:
  password: <redacted>
  resources:
    limits:
      cpu: "1"
      memory: 512Mi
    requests:
      cpu: "1"
      memory: 512Mi
```

Pod resources (requests equal limits; halved if the VM has fewer than 12 CPUs, say so here: not halved, the VM has 16 CPUs):

| Component | CPU | Memory |
|---|---|---|
| Platform | 4 | 3 GiB |
| Game Host | 4 | 4 GiB |
| Postgres | 2 | 1 GiB |
| Redis | 1 | 512 MiB |

## 3. Thresholds

This scenario has its own pass rule (`default-limits.js`): no unexpected error, at least one `RATE_LIMIT_EXCEEDED`, no 5xx. The `load-testing.md` §6 targets are listed
for reference, over the whole run (there are no steps and no settle window).

| Metric | Target | Observed p95 | Observed p99 | Pass |
|---|---|---|---|---|
| Unexpected errors (`tb_errors{expected:false}`) | count == 0 | n/a | n/a | pass (0) |
| `RATE_LIMIT_EXCEEDED` (`tb_errors{code:RATE_LIMIT_EXCEEDED}`) | count > 0 | n/a | n/a | pass (320) |
| 5xx (`tb_errors{code:http_5xx}`) | count == 0 | n/a | n/a | pass (0) |
| `tb_move_rtt` | p95 < 200 ms, p99 < 500 ms | 51 ms | 89 ms | pass (max 1,036 ms) |
| `tb_login`, `tb_room_create`, `tb_room_join` | p95 < 200 ms, p99 < 500 ms | `tb_room_join` 135 ms; `tb_room_create` 150 ms (`tb_login`: 40 logins in `setup()`, 73 ms) | `tb_room_join` 156 ms; `tb_room_create` 152 ms | pass (the p50s are 8 ms and 7 ms; the tails are the 20 simultaneous first iterations, not isolated) |
| `tb_lobby_event` | p95 < 300 ms, p99 < 600 ms | 36 ms | 83 ms | pass |
| `tb_game_start` | p95 < 1 s, p99 < 2 s (cold is recorded, not gated) | 57 ms | **4,951 ms** (max 4,984 ms) | the p99 is the cold start of the first games on a freshly restarted Game Host; warm and cold are not split in this scenario's summary (it defines no `cold` sub-metric), so the warm p99 is not measured here |
| Error rate (`tb_op_failed`) | < 1% | 3.5% (320 of 9,068) | n/a | all 320 are the expected `RATE_LIMIT_EXCEEDED`; unexpected errors 0 |
| Concurrent sessions | >= 500 | not attempted (peak `sessions_active` 20) | n/a | not attempted: this scenario checks the limiters |
| Concurrent WebSockets | >= 5,000 | not attempted (peak `ws_connections` 40) | n/a | not attempted: this scenario checks the limiters |

## 4. Steps

One fixed load, so one row. Moves per second is `count(tb_move_rtt) / 180 s` (4,904 / 180); there is no settle window here. Generator-bound comes from `check-generator.sh` (k6 mean 5% of its 320% budget).
CPU columns are the means of the two `snapshot.sh` segments (0 to 120 s, 120 s to the end); the first includes the cold JIT warm-up.
No cold/warm split exists for this scenario (see section 3).

| Step | Moves/s | `tb_move_rtt` p50 / p95 / p99 | `tb_game_start` warm p95 / p99 | `tb_game_start` cold p95 / p99 | Errors by code | Game Host CPU cores | Platform CPU cores | Generator-bound | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 20 pairs, 3 min | 27.2 (3.6 games/s started) | 6 / 51 / 89 ms | not split (all starts: 57 ms / 4,951 ms) | not split | `RATE_LIMIT_EXCEEDED` x320 (expected) | 1.63, 1.10 | 0.53, 0.36 | no | pass |

## 5. Result

Ceiling (pairs): 20 (not a ceiling: the scenario runs one fixed load of 20 pairs and finds none)
First to break: none
Evidence: the limiters answered under load and nothing else broke. 320 `RATE_LIMIT_EXCEEDED`, 0 unexpected errors, 0 5xx, 0 restarts, `http_req_failed` 0 of 1,320 requests. Every one of the 320 iterations ended
with exactly one `RATE_LIMIT_EXCEEDED`, in the third game of the room: 961 game starts against 641 completed games is 320 abandoned games, and 4,904 moves is about 7.6 per completed game.
That is the WebSocket action bucket (burst 10, 5/s per user, `rate-limiting.md` Tier 6) answering a client that moves with no think time: a player makes about four moves per game, so the third game begins with the bucket empty.
This is an inference from those counts; the server-side `RATE_LIMIT_EXCEEDED` frames were not read (the platform log was cleared by the reset after the run). The HTTP tiers never fired: room create and join were 320 each, all 201, and no request returned 429.
Resources were far from any limit: Game Host 0.94 of 4 cores and platform 0.31 of 4 (`kubectl top` means), Postgres 0.04 of 2, `hikari_pending` 0.

## 6. Server side

`snapshot.sh` output (mean / max per 120 s segment; seg 1 is the first 120 s after the scenario start, seg 2 the remaining 69 s):

| metric (mean / max) | seg 1 (0s) | seg 2 (120s) |
|---|---|---|
| gamehost_cpu_cores | 1.627 / 2.018 | 1.096 / 1.269 |
| platform_cpu_cores | 0.527 / 1.123 | 0.356 / 0.494 |
| gamehost_heap_bytes | 310677730 / 473208512 | 378676828.8 / 480598416 |
| platform_heap_bytes | 201910190 / 313677920 | 186537368 / 264173608 |
| gamehost_threads | 53.125 / 56 | 53.6 / 54 |
| platform_threads | 121.875 / 132 | 131.2 / 132 |
| gamehost_gc_seconds_per_s | 0.002 / 0.004 | 0.001 / 0.002 |
| platform_gc_seconds_per_s | 0.001 / 0.001 | 0 / 0 |
| http_p95_seconds | 0.07 / 0.138 | 0.024 / 0.026 |
| http_p99_seconds | 0.099 / 0.153 | 0.032 / 0.038 |
| http_5xx_per_s | n/a | n/a |
| http_req_per_s | 6.13 / 10.936 | 10.919 / 10.967 |
| hikari_active | 0.125 / 1 | 0 / 0 |
| hikari_pending | 0 / 0 | 0 / 0 |
| ws_connections | 31.75 / 40 | 36.8 / 40 |
| rooms_active | 17.5 / 20 | 20 / 20 |
| sessions_active | 12.5 / 20 | 20 / 20 |
| up | 1 / 1 | 1 / 1 |

Per-pod CPU from `kubectl top` (`pods.csv`, millicores, mean over the run): platform 307, Game Host 936, Postgres 43 (max 102).

| | At start | At end |
|---|---|---|
| Redis `used_memory_human` | n/a (sampled once, after the run) | 1.80M |
| Redis `connected_clients` | n/a (sampled once, after the run) | 5 |

Pod restarts and `OOMKilled` (from `cluster.txt`): all thirteen pods 0 restarts (the list includes the finished `minio-init` job), no termination reason recorded.

Missing metrics: `http_5xx_per_s` (no 5xx request ever happened; Micrometer creates the series on first use)

## 7. Errors by code

| Code | Expected | Count |
|---|---|---|
| `RATE_LIMIT_EXCEEDED` | yes | 320 |

## 8. Findings

- **The limiters work under load, and the only one that fired is the per-user WebSocket action bucket.** One `RATE_LIMIT_EXCEEDED` per iteration, in its third game; no HTTP 429. The load shape (no think time, 5 games per room by default) is what trips it: the default-limits result says the *stock* limits let a no-think pair play about two games in a burst, which is not evidence about human play. Not checked: the server-side frame, and which of the two players hit the bucket.
- **A pair that hits the limit loses its game and backs off.** 320 games started and never finished; the pair retries after the harness error backoff, so the rest of the run is the same iteration repeated (about 1.6 iterations/s over 20 pairs).
- **The stock chart's HTTP tiers were not exercised.** 1,320 requests over 189 s (7 per second) are far below the API tier (100 per 10 s per user) and the public tier (200 per minute per IP is global for this client, see `load-testing.md` §3.2, and 40 logins in `setup()` are inside it). A test of those tiers is not part of this item.
- **The first games on a cold Game Host take about 5 s** (`tb_game_start` max 4,984 ms), as in `start-rate`.
- No restart, no `OOMKilled`, no 5xx, generator never bound.

## 9. Constants

- This is a single-node, laptop ceiling: Docker Desktop Kubernetes on one WSL2 VM shared with the load generator. It is the ceiling of this machine, not of the platform.
- Latency is measured per request from a closed-loop client at the configured think time, so coordinated omission applies: when the system slows, the client issues fewer requests and the percentiles understate the delay a constant-rate client would see. `start-rate` is open-loop.
- One step is generator-bound when the k6 process averages more than 80% of its pinned cores after the settle window; such a step never counts as the platform's breaking point.
- The first `SETTLE_SECONDS` of every step are excluded from that step's thresholds.
- A crossed threshold aborts the run no earlier than 30 s after the test start (`delayAbortEval` counts from the test start, not from the step), so a step's first samples after its settle window can trip a one-sample percentile.
