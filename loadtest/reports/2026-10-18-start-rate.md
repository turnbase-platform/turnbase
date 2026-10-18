# Start-rate scenario report, 2026-10-18

**Verdict:** No step failed a threshold at 1 to 32 games/s (warm `game_start` p95 at most 34.9 ms, p99 at most 43 ms; NFR-LOAD-001 holds with a factor of about 25), but the 32 games/s step lost 146 iterations and had 54 `ready_timeout` in a 15 s stall at its start, so the highest clean rate is 16 games/s; no resource was near its limit, so the rate at which `game_start` degrades was not reached. Single-node, laptop result.

## 1. Run

| Field | Value |
|---|---|
| Scenario | `start-rate`, defaults (arrival rates 1, 2, 4, 8, 16, 32 games/s; 120 s steps, 20 s settle; 400 VU cap) |
| Parameters (`params.txt`) | `scenario=start-rate`, `K6_CORES=4`, no overrides |
| Start (UTC) | 2026-10-18T20:11:15Z |
| End (UTC) | 2026-10-18T20:23:27Z |
| Duration | 12 min 12 s (setup of about 16 s, then six steps; k6 stopped 12 s after the last step) |
| k6 exit code | 0 (every threshold held; the scenario does not abort on them) |
| k6 version | k6 v2.2.0 (commit/00a9a1b7f5, go1.26.5, linux/amd64) |
| k6 pinned to CPUs | the last 4 of 16 (`taskset`, `K6_CORES=4`) |
| Run directory | `loadtest/results/20261018-221113-start-rate` (git-ignored) |

## 2. Environment

| Field | Value |
|---|---|
| Docker Desktop VM CPUs | 16 |
| Docker Desktop VM memory | 16,326,520,832 bytes (15.21 GiB, `docker info`) |
| `.wslconfig` | absent (VM defaults) |
| Host load during the run | `load1` mean 4.7, max 8.4 on 16 CPUs; `vm_cpu_pct` mean 15.3, max 42; k6 mean 15%, max 75% of one core (`samples.csv`, from the first step on) |
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
every row passes for that step. Observed values are those of the last step that passed (32 games/s; its thresholds held, but see section 5 for why it is not the ceiling).

| Metric | Target | Observed p95 | Observed p99 | Pass |
|---|---|---|---|---|
| `tb_move_rtt` | p95 < 200 ms, p99 < 500 ms | 5 ms | 7 ms | pass at every step (worst step: 4 games/s, p95 29 ms, p99 37 ms) |
| `tb_login`, `tb_room_create`, `tb_room_join` | p95 < 200 ms, p99 < 500 ms | `tb_room_join` 9.9 ms; `tb_room_create` 7.7 ms (`tb_login`: 815 logins in `setup()`, not stepped, p95 68 ms) | `tb_room_join` 11.8 ms; `tb_room_create` 9.5 ms | pass at every step (worst: `tb_room_join` at 4 games/s, p95 67 ms, p99 98 ms) |
| `tb_lobby_event` | p95 < 300 ms, p99 < 600 ms | 3 ms | 4 ms | pass at every step (worst: 20 / 29 ms at 4 games/s) |
| `tb_game_start` (warm) | p95 < 1 s, p99 < 2 s (cold is recorded, not gated) | 12 ms | 14 ms | pass at every step (worst: 4 games/s, p95 34.9 ms, p99 43 ms) |
| Error rate (`tb_op_failed`) | < 1% | 0.12% (54 of 41,953) | n/a | pass at every step (the 54 `ready_timeout` are all in the 32 games/s step) |
| Concurrent sessions | >= 500 | not attempted (peak `sessions_active` 2 in the snapshot, sampled every 15 s: the open model keeps few games open at once) | n/a | not attempted here; `ramp-to-break` measures it |
| Concurrent WebSockets | >= 5,000 | not attempted (peak `ws_connections` 10) | n/a | not attempted here; `ramp-to-break` measures it |

## 4. Steps

`steps.csv`, one row per step. Moves per second is `count(tb_move_rtt) / (STEP_SECONDS - SETTLE_SECONDS)` = count / 100;
games per second likewise from `tb_games_completed`. Generator-bound comes from `check-generator.sh` (k6 mean 2% to 47% of its 320% budget: no step is generator-bound).
CPU columns are the per-segment means of `snapshot.sh`; its segments start at the run launch, not at the first step, so each is offset by the setup time of about 16 s.
The first segment includes the cold JIT warm-up.

**Cold start.** The `tb_game_start` summary in `summary.json` keeps only `cold:false` per step. The cold series (a pair's first game within 30 s of the scenario start, on a Game Host restarted by `reset.sh`) is in Prometheus (`k6_tb_game_start_*{cold="true"}`): in the warm-up window p50 22 ms, p95 4.16 s, p99 4.79 s, max 4.95 s; the cold-tagged starts that fell into the first step are p95 21 ms, max 21 ms (the sample count is not exposed). So the first start on a cold Game Host takes about 5 s, and later cold-tagged starts are already as fast as warm ones. Cold is recorded, not gated.

| Step (games/s) | Games/s completed | Moves/s | `tb_move_rtt` p50 / p95 / p99 | `tb_game_start` warm p95 / p99 | `tb_game_start` cold p95 / p99 | Errors by code | Game Host CPU cores | Platform CPU cores | Generator-bound | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1.01 | 7.9 | 6 / 8 / 10 ms | 16 / 18 ms | see above | 0 | 1.20 | 0.52 | no | pass |
| 2 | 2.02 | 15.4 | 5 / 5 / 6 ms | 13 / 15 ms | see above | 0 | 0.31 | 0.19 | no | pass |
| 4 | 4.04 | 31.0 | 4 / 29 / 37 ms | 34.9 / 43 ms | see above | 0 | 0.26 | 0.27 | no | pass (a stall at about 60 s into the step, see section 8) |
| 8 | 8.10 | 61.2 | 4 / 5 / 6 ms | 11 / 13 ms | see above | 0 | 0.09 | 0.41 | no | pass |
| 16 | 16.21 | 123.3 | 4 / 5 / 6 ms | 11 / 13 ms | see above | 0 | 0.16 | 0.76 | no | pass |
| 32 | 30.74 | 234.7 | 4 / 5 / 7 ms | 12 / 14 ms | see above | `ready_timeout` x54 | 0.27 | 1.39 | no | pass on thresholds; **146 dropped iterations** and 54 errors (a stall in its first seconds) |

`dropped_iterations` is not step-tagged. Prometheus (`k6_dropped_iterations_total`) shows all 146 between 605 s and 615 s after the scenario start, that is the first 15 s of the 32 games/s step: the counter was 0 before and flat after. The 4 games/s step has none.

## 5. Result

Ceiling (games/s): 16
First to break: none
Evidence: no resource was near its limit at any step. At 32 games/s the platform pod used 1.39 of 4 cores (`kubectl top`: 1.44), the Game Host 0.27 of 4 (0.28), Postgres 0.64 of 2, Redis 0.24 of 1, `hikari_pending` 0, no 5xx, no restart, k6 at 47% of its 320% budget. `game_start` stayed at p95 12 ms (p99 14 ms) from 8 games/s on and never degraded before `move_rtt` did (neither degraded). The highest passing rate is 16 games/s by the rule that the step must also show no `dropped_iterations`: the 32 games/s step passed every threshold but lost 146 iterations and had 54 `ready_timeout` in a stall that starts as the rate doubles from 16 to 32. A second stall of the same kind (a 10 s WebSocket connect, a 10.5 s iteration) hit the 4 games/s step at about 300 s without any dropped iteration. Nothing in the CPU, pool or thread numbers explains either stall (platform threads step from 81 to 123 in the first and to 232 in the second); the cause is not determined. The scenario's top rate is 32 games/s, so **the rate at which `game_start` degrades was not reached**: the true ceiling is above 31 games/s completed (about 235 moves/s) and `parallelism` carried 909 moves/s closed-loop, about 116 games/s at 7.8 moves per game.

## 6. Server side

`snapshot.sh` output (mean / max per 120 s segment; seg N is step N of the table above, offset by the setup time):

| metric (mean / max) | seg 1 (0s) | seg 2 (120s) | seg 3 (240s) | seg 4 (360s) | seg 5 (480s) | seg 6 (600s) |
|---|---|---|---|---|---|---|
| gamehost_cpu_cores | 1.196 / 2.417 | 0.31 / 1.044 | 0.263 / 0.982 | 0.093 / 0.113 | 0.159 / 0.185 | 0.271 / 0.399 |
| platform_cpu_cores | 0.524 / 1.942 | 0.192 / 0.204 | 0.265 / 0.362 | 0.408 / 0.474 | 0.755 / 0.869 | 1.388 / 1.699 |
| gamehost_heap_bytes | 272352222 / 458739296 | 344425312 / 427262816 | 346840040 / 485983072 | 379830344 / 493796752 | 374830911 / 469297968 | 390989242 / 513179968 |
| platform_heap_bytes | 243260661 / 324583688 | 207357551 / 277449040 | 143986709 / 194180248 | 192241740 / 269148344 | 186062327 / 256710624 | 273844327 / 378756224 |
| gamehost_threads | 51.25 / 55 | 48.125 / 49 | 49.375 / 52 | 47.625 / 50 | 47 / 47 | 49.125 / 51 |
| platform_threads | 77.75 / 81 | 80.875 / 81 | 97.25 / 123 | 121.375 / 123 | 120.625 / 122 | 203.5 / 232 |
| gamehost_gc_seconds_per_s | 0.001 / 0.003 | 0 / 0.001 | 0.001 / 0.001 | 0.001 / 0.001 | 0.001 / 0.001 | 0.001 / 0.002 |
| platform_gc_seconds_per_s | 0.017 / 0.073 | 0 / 0 | 0 / 0 | 0 / 0 | 0.001 / 0.001 | 0.002 / 0.002 |
| http_p95_seconds | 0.045 / 0.107 | 0.006 / 0.006 | 0.01 / 0.019 | 0.005 / 0.005 | 0.005 / 0.006 | 0.014 / 0.051 |
| http_p99_seconds | 0.054 / 0.112 | 0.008 / 0.009 | 0.03 / 0.071 | 0.006 / 0.006 | 0.007 / 0.007 | 0.086 / 0.235 |
| http_5xx_per_s | n/a | n/a | n/a | n/a | n/a | n/a |
| http_req_per_s | 24.091 / 75.962 | 10.275 / 12.317 | 20.405 / 25.384 | 40.51 / 48.617 | 80.797 / 96.989 | 154.329 / 197.706 |
| hikari_active | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0.5 / 1 | 1.125 / 4 |
| hikari_pending | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| ws_connections | 0 / 0 | 0 / 0 | 1.5 / 2 | 2 / 2 | 3.75 / 4 | 7 / 10 |
| rooms_active | 0 / 0 | 0 / 0 | 0.5 / 1 | 1 / 1 | 1.5 / 2 | 17 / 58 |
| sessions_active | 0 / 0 | 0 / 0 | 0.25 / 1 | 0.25 / 1 | 0.25 / 1 | 1 / 2 |
| up | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 |

Per-pod CPU from `kubectl top` (`pods.csv`, millicores, mean per step, aligned to the scenario start): platform 325, 156, 258, 437, 810, 1441; Game Host 1135, 215, 237, 98, 170, 282; Postgres 32, 41, 78, 147, 303, 638; Redis 13, 24, 42, 81, 151, 241.

| | At start | At end |
|---|---|---|
| Redis `used_memory_human` | n/a (sampled once, after the run) | 3.59M |
| Redis `connected_clients` | n/a (sampled once, after the run) | 5 |

Pod restarts and `OOMKilled` (from `cluster.txt`): all twelve pods 0 restarts, no termination reason recorded.

Missing metrics: `http_5xx_per_s` (no 5xx request ever happened; Micrometer creates the series on first use)

## 7. Errors by code

| Code | Expected | Count |
|---|---|---|
| `ready_timeout` | no | 54 (all in the 32 games/s step) |

## 8. Findings

- **The 32 games/s step lost 146 iterations and had 54 `ready_timeout` to a stall at its start, with the machine idle.** `dropped_iterations` 146, all between 605 s and 615 s after the scenario start; `k6_vus` jumped from 4 to 152 and back to 4 by 625 s; `tb_ws_connecting` max 10.7 s, `iteration_duration` max 21.5 s. At the same time the platform pod used 1.4 of 4 cores and the Game Host 0.27 of 4. Suspected cause: a pause on the platform or ingress side that the arrival-rate VUs queue behind (platform threads went from 123 to 232). Not checked: JVM safepoint or GC logs, ingress and frontend nginx access logs, the Tomcat accept queue; whether the pause recurs without load.
- **A smaller stall of the same shape at about 300 s (in the 4 games/s step).** `tb_ws_connecting` max 10.0 s (the harness's WebSocket connect timeout), `iteration_duration` max 10.5 s, move p95 29 ms and room-join p95 67 ms in that step against 5 to 12 ms in all others; no dropped iteration; platform threads 81 to 123. The two stalls are about 300 s apart (300 s and 605 s after the scenario start). A 10 s WebSocket connect also appeared at 300 s to 310 s of the `contexts` run, and `ramp-to-break` raised the same question. Not checked: whether the interval is exact, any periodic job on the platform or the ingress.
- **`game_start` is not the first thing to degrade in this sweep: nothing degrades.** Warm p95 11 to 16 ms and p99 13 to 18 ms at every rate from 1 to 32 games/s except the stalled 4 games/s step (34.9 / 43 ms); NFR-LOAD-001 (p95 < 1 s, p99 < 2 s) holds with a factor of about 25 to 100. The sweep's top rate (32/s) is below the point where it would.
- **Cold start is about 5 s once, on a freshly restarted Game Host.** First-ever game start in the run: 4.95 s; the cold-tagged starts after it are 21 ms.
- No restart, no `OOMKilled`, no 5xx, no generator-bound step.
- `contexts` was built by `IMP-M15-10`, so no "not run" line is owed; its report is `2026-10-18-contexts.md`.

## 9. Constants

- This is a single-node, laptop ceiling: Docker Desktop Kubernetes on one WSL2 VM shared with the load generator. It is the ceiling of this machine, not of the platform.
- Latency is measured per request from a closed-loop client at the configured think time, so coordinated omission applies: when the system slows, the client issues fewer requests and the percentiles understate the delay a constant-rate client would see. `start-rate` is open-loop.
- One step is generator-bound when the k6 process averages more than 80% of its pinned cores after the settle window; such a step never counts as the platform's breaking point.
- The first `SETTLE_SECONDS` of every step are excluded from that step's thresholds.
- A crossed threshold aborts the run no earlier than 30 s after the test start (`delayAbortEval` counts from the test start, not from the step), so a step's first samples after its settle window can trip a one-sample percentile.
