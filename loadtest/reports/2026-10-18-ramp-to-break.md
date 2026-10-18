# Ramp-to-break scenario report, 2026-10-18

**Verdict:** Ceiling 70 pairs (140 sockets, about 55 concurrent sessions): the run aborted 67 s into the 80-pair step on `tb_room_join` (p95 311 ms, p99 474 ms over 838 joins) while move, lobby and game-start latencies were still far inside their targets; neither the 500-session nor the 5,000-WebSocket target was reached. Single-node, laptop result.

## 1. Run

| Field | Value |
|---|---|
| Scenario | `ramp-to-break`, defaults (start 10 pairs, +10 per step, 120 s steps, 20 s settle, max 1,000, abort on a failed threshold) |
| Parameters (`params.txt`) | `scenario=ramp-to-break`, `K6_CORES=4`, no overrides |
| Start (UTC) | 2026-10-18T19:49:38Z |
| End (UTC) | 2026-10-18T20:05:15Z |
| Duration | 15 min 37 s (setup 30 s, seven full steps, then 67 s of the eighth) |
| k6 exit code | 99 (`tb_room_join{step:80}` crossed, `abortOnFail` stopped the test) |
| k6 version | k6 v2.2.0 (commit/00a9a1b7f5, go1.26.5, linux/amd64) |
| k6 pinned to CPUs | the last 4 of 16 (`taskset`, `K6_CORES=4`) |
| Run directory | `loadtest/results/20261018-214936-ramp-to-break` (git-ignored) |

## 2. Environment

| Field | Value |
|---|---|
| Docker Desktop VM CPUs | 16 |
| Docker Desktop VM memory | 16,326,520,832 bytes (15.21 GiB, `docker info`) |
| `.wslconfig` | absent (VM defaults) |
| Host load during the run | `load1` mean 15.3, max 18.1 on 16 CPUs; `vm_cpu_pct` mean 59.7, max 71 (`samples.csv`, from the first step on) |
| Root commit | 4b44c0c6097ff830f2426b6efbdf01f4ab97d74d |
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
  prometheus:
    remoteWriteReceiver: true
origins:
  gameFrontendTemplate: http://{gameId}.games.localhost
  platform: http://turnbase.localhost
platform:
  autoscaling:
    enabled: false
  extraEnv:
  - name: SPRING_PROFILES_ACTIVE
    value: local,loadtest
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

Targets from `load-testing.md` §6 and §7 (`platform-operations.md` NFR-LOAD-001 to 004). A step passes when
every row passes for that step. Observed values are those of the last step that passed (70 pairs).

| Metric | Target | Observed p95 | Observed p99 | Pass |
|---|---|---|---|---|
| `tb_move_rtt` | p95 < 200 ms, p99 < 500 ms | 70 ms (81 ms at 80) | 80 ms (92 ms at 80) | pass at every step |
| `tb_login`, `tb_room_create`, `tb_room_join` | p95 < 200 ms, p99 < 500 ms | `tb_room_join` 30.5 ms, `tb_room_create` 16.5 ms (`tb_login` happens in setup, not stepped) | `tb_room_join` 40.0 ms, `tb_room_create` 24.4 ms | pass to 70; `tb_room_join` at 80: p95 311.5 ms, p99 474.4 ms: fail (p95 target 200) |
| `tb_lobby_event` | p95 < 300 ms, p99 < 600 ms | 67 ms | 77 ms | pass at every step |
| `tb_game_start` (warm) | p95 < 1 s, p99 < 2 s (cold is recorded, not gated) | 81 ms | 91 ms | pass at every step |
| Error rate (`tb_op_failed`) | < 1% | 0 in every step (10 of 1,204,000 operations over the run, all outside the measured windows) | n/a | pass |
| Concurrent sessions | >= 500 | not reached: ceiling 70 pairs = 70 sessions; `sessions_active` max 63 (step 70); limiting factor: `tb_room_join` latency with the platform pod at about 3 of 4 cores | n/a | not reached |
| Concurrent WebSockets | >= 5,000 | not reached: ceiling 70 pairs = 140 sockets (160 open at the abort); the 5,000 target needs 2,500 pairs; limiting factor as above | n/a | not reached |

## 4. Steps

`steps.csv`, one row per step reached. Moves per second is `count(tb_move_rtt) / (STEP_SECONDS - SETTLE_SECONDS)` = count / 100;
for the aborted step 80 only 47 s were measured, so its count is divided by 47 and includes the ramp-up from 70 pairs.
Generator-bound comes from `check-generator.sh` (k6 mean 96% to 136% of its 320% budget: no step is generator-bound).
CPU columns are the per-segment means of `snapshot.sh`; its segments start at the run launch, so each is offset by the setup time of about 30 s.
The first segment includes the cold JIT warm-up (hence the Game Host 2.47 at step 10). No cold `tb_game_start` was sampled (every game start fell outside the 30 s cold window).

| Step (pairs) | Moves/s | `tb_move_rtt` p50 / p95 / p99 | `tb_game_start` warm p95 / p99 | `tb_game_start` cold p95 / p99 | Errors by code | Game Host CPU cores | Platform CPU cores | Generator-bound | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 10 | 794 | 6 / 9 / 13 ms | 17 / 22 ms | none sampled | 0 | 2.47 | 2.90 | no | pass |
| 20 | 931 | 12 / 17 / 21 ms | 25 / 30 ms | none sampled | 0 | 1.85 | 2.96 | no | pass |
| 30 | 841 | 20 / 26 / 30 ms | 34 / 39 ms | none sampled | 0 | 0.99 | 2.85 | no | pass |
| 40 | 909 | 28 / 36 / 42 ms | 44 / 51 ms | none sampled | 0 | 1.01 | 2.98 | no | pass |
| 50 | 812 | 36 / 46 / 54 ms | 55 / 65 ms | none sampled | 0 | 0.99 | 2.96 | no | pass |
| 60 | 873 | 44 / 58 / 69 ms | 69 / 81 ms | none sampled | 0 | 0.91 | 2.78 | no | pass |
| 70 | 856 | 54 / 70 / 80 ms | 81 / 91 ms | none sampled | 0 | 0.97 | 2.95 | no | pass |
| 80 | 664 | 61 / 81 / 92 ms | 94 / 107 ms | none sampled | 0 | 0.93 | 2.88 | no | fail |

Per-step `tb_room_join` (p95 / p99, ms): 10: 12.0 / 16.0, 20: 14.0 / 17.9, 30: 20.7 / 51.7, 40: 18.5 / 26.0, 50: 29.3 / 199.1, 60: 32.4 / 51.7, 70: 30.5 / 40.0, 80: 311.5 / 474.4 (p50 18.2, max 535 ms, 838 samples).

## 5. Result

Ceiling (pairs): 70
First to break: platform threads
Evidence: the abort came from one metric: `tb_room_join{step:80}` p95 311.5 ms (target 200) on 838 samples over about 47 s; its p50 was 18.2 ms,
so a tail of roughly 40 slow joins, up to 535 ms, tripped it. Everything else was inside its target at that step (move p95 81 ms,
lobby 79 ms, game start 94 ms). Room join writes to Postgres, which ran at 1.85 of its 2 cores in that step (`kubectl top`, 1.5 to 1.85 from step 20 on),
next to a platform pod at 2.9 of 4 cores that has been at about 3 cores since 20 pairs (the clients do not think, so the platform is saturated
at every step; latency rose steadily, move p95 9 ms at 10 pairs to 81 ms at 80). `hikari_pending` was 0 except one segment (step 60: mean 1.1, max 9), and the connection pool is not shown to be the limit.
Game Host 0.9 to 1.0 of 4 cores from step 30, Redis 0.4 of 1, no 5xx, no restarts, generator never bound. The Postgres core limit and the platform core limit cannot be separated with this data,
and the single-metric abort at the start of a step may be a transient: the ceiling is the protocol's (last fully passing step), not proof that 80 pairs cannot be served.

Capacity statements:

- 500 concurrent sessions: **not reached.** Ceiling 70 pairs = 70 sessions (`sessions_active` max 63 at step 70, 58 at 80); limiting factor `tb_room_join` latency (platform and Postgres CPU).
- 5,000 WebSockets: **not reached; ceiling in sockets: 140** (2 x 70; 160 open when the run aborted). The ceiling is below 1,000 pairs, so the idle-socket run was not made (protocol, `IMP-M15-11` step 3); limiting factor as above. The remaining 4,860 sockets were not attempted.

## 6. Server side

`snapshot.sh` output (mean / max per 120 s segment; seg N is step 10 x N, see the offset note in section 4):

| metric (mean / max) | seg 1 (0s) | seg 2 (120s) | seg 3 (240s) | seg 4 (360s) | seg 5 (480s) | seg 6 (600s) | seg 7 (720s) | seg 8 (840s) |
|---|---|---|---|---|---|---|---|---|
| gamehost_cpu_cores | 2.467 / 3.951 | 1.849 / 2.936 | 0.992 / 1.146 | 1.013 / 1.077 | 0.987 / 0.995 | 0.91 / 0.985 | 0.969 / 0.987 | 0.934 / 0.964 |
| platform_cpu_cores | 2.905 / 3.947 | 2.96 / 3.089 | 2.847 / 3.095 | 2.983 / 3.007 | 2.959 / 2.993 | 2.777 / 2.947 | 2.946 / 2.985 | 2.881 / 2.937 |
| gamehost_heap_bytes | 336996463 / 519194496 | 401485532 / 519818328 | 409188539 / 529539096 | 366835630 / 500284648 | 407760854 / 523135896 | 354233907 / 461120112 | 381480515 / 506670960 | 455267003.2 / 534921976 |
| platform_heap_bytes | 200372086 / 299829552 | 179152243 / 251189008 | 207676744 / 264462384 | 215254575 / 233307392 | 180435553 / 230592360 | 209639554 / 269531568 | 198846920 / 289609408 | 196321929.6 / 286515256 |
| gamehost_threads | 53.125 / 56 | 53.375 / 55 | 52.625 / 53 | 52.375 / 53 | 52.25 / 53 | 52.25 / 53 | 52 / 52 | 52 / 52 |
| platform_threads | 80.5 / 84 | 83.75 / 84 | 96.375 / 108 | 108 / 108 | 108.5 / 109 | 133.125 / 137 | 137.5 / 138 | 137 / 137 |
| gamehost_gc_seconds_per_s | 0.005 / 0.011 | 0.003 / 0.004 | 0.002 / 0.002 | 0.002 / 0.003 | 0.002 / 0.002 | 0.002 / 0.002 | 0.002 / 0.002 | 0.002 / 0.002 |
| platform_gc_seconds_per_s | 0.021 / 0.075 | 0.005 / 0.005 | 0.004 / 0.005 | 0.004 / 0.004 | 0.004 / 0.004 | 0.004 / 0.005 | 0.005 / 0.005 | 0.005 / 0.005 |
| http_p95_seconds | 0.039 / 0.109 | 0.008 / 0.009 | 0.01 / 0.013 | 0.011 / 0.011 | 0.012 / 0.013 | 0.022 / 0.034 | 0.016 / 0.018 | 0.019 / 0.02 |
| http_p99_seconds | 0.053 / 0.135 | 0.011 / 0.012 | 0.019 / 0.028 | 0.015 / 0.017 | 0.019 / 0.021 | 0.055 / 0.103 | 0.026 / 0.029 | 0.031 / 0.033 |
| http_5xx_per_s | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| http_req_per_s | 93.705 / 128.444 | 141.007 / 148.674 | 134.23 / 147.253 | 144.518 / 146.627 | 141.625 / 143.326 | 127.009 / 138.222 | 137.096 / 140.107 | 132.774 / 133.473 |
| hikari_active | 2.125 / 3 | 3.125 / 6 | 2.25 / 5 | 2.625 / 5 | 3.875 / 5 | 4.625 / 10 | 3.625 / 7 | 2.6 / 5 |
| hikari_pending | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 1.125 / 9 | 0 / 0 | 0 / 0 |
| ws_connections | 17.5 / 20 | 37.5 / 40 | 50 / 60 | 77.25 / 80 | 97.25 / 100 | 104.75 / 120 | 137.25 / 140 | 156 / 160 |
| rooms_active | 6.5 / 10 | 16.5 / 20 | 25.75 / 30 | 34.5 / 38 | 45.625 / 50 | 53.5 / 60 | 65 / 69 | 73.4 / 78 |
| sessions_active | 4.5 / 8 | 11.375 / 16 | 20.375 / 25 | 27 / 34 | 32.75 / 34 | 30.875 / 49 | 54.125 / 63 | 55.2 / 58 |
| up | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 |


| | At start | At end |
|---|---|---|
| Redis `used_memory_human` | n/a (sampled once, after the run) | 7.18M |
| Redis `connected_clients` | n/a (sampled once, after the run) | 5 |

Pod restarts and `OOMKilled` (from `cluster.txt`): all twelve pods 0 restarts, no termination reason recorded.

Missing metrics: `http_5xx_per_s` (no 5xx request ever happened; Micrometer creates the series on first use)

Per-pod CPU from `kubectl top` (`pods.csv`, millicores, mean per segment 1 to 8): platform 2655, 2988, 2830, 3007, 2984, 2741, 2972, 2899;
Game Host 2461, 1680, 967, 1023, 999, 898, 981, 951; Postgres 876, 1498, 1508, 1704, 1760, 1650, 1841, 1854;
Redis 281, 433, 419, 447, 444, 413, 437, 429; frontend nginx 185, 305, 297, 323, 322, 291, 319, 308. ingress-nginx (another namespace) was at 2m after the run.

## 7. Errors by code

| Code | Expected | Count |
|---|---|---|
| `ready_timeout` | no | 10 (none in a measured step window: the step-tagged counters are all 0, so they fell in a settle window) |

## 8. Findings

- **The ramp stopped at 80 pairs on a room-join tail, not on a sustained break.** `tb_room_join{step:80}` p95 311.5 ms, p99 474.4 ms, max 535 ms over 838 joins, with p50 18.2 ms; move p95 was 81 ms. Suspected cause: Postgres at 1.85 of 2 cores (92%) and the platform at 2.9 of 4, so a burst of joins queues. Not checked: Postgres statistics, a platform thread dump, whether the tail is a periodic stall (the step-50 p99 was 199 ms, against 26 ms at step 40 and 52 ms at step 60), and a rerun of 80 pairs alone.
- **Capacity on this machine is far below the targets.** 70 pairs = 70 concurrent sessions and 140 WebSockets at the ceiling, against 500 and 5,000. Zero-think-time clients keep the platform at about 3 of 4 cores from 20 pairs on, so the number is a ceiling for that traffic shape, not for human players. Not checked: a run with realistic think times.
- **The platform pod uses about 3.0 of its 4 cores at every step from 20 pairs** and never the fourth. Not checked: CPU throttling counters (`container_cpu_cfs_throttled_*`), which would show a quota effect.
- **Platform thread count grows with load** (80 at step 10, 108 at 40, 133 to 138 from 60 to 80); no 5xx, no pool exhaustion (`hikari_pending` max 9 once, at step 60).
- **10 `ready_timeout` errors** outside the measured windows (during settle). Same shape as the error recorded in the `parallelism` report (46 at 128 pairs). Not checked: which rooms, and the cause (the README's `SUBSCRIBE_SETTLE_MS` race or a late broadcast).
- No restart, no `OOMKilled`, no 5xx, no generator-bound step.

## 9. Constants

- This is a single-node, laptop ceiling: Docker Desktop Kubernetes on one WSL2 VM shared with the load generator. It is the ceiling of this machine, not of the platform.
- Latency is measured per request from a closed-loop client at the configured think time, so coordinated omission applies: when the system slows, the client issues fewer requests and the percentiles understate the delay a constant-rate client would see. `start-rate` is open-loop.
- One step is generator-bound when the k6 process averages more than 80% of its pinned cores after the settle window; such a step never counts as the platform's breaking point.
- The first `SETTLE_SECONDS` of every step are excluded from that step's thresholds.
- A crossed threshold aborts the run no earlier than 30 s after the test start (`delayAbortEval` counts from the test start, not from the step), so a step's first samples after its settle window can trip a one-sample percentile.
