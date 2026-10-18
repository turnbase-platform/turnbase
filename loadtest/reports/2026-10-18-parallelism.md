# Parallelism scenario report, 2026-10-18

**Verdict:** Moves/s scaled roughly linearly to 8 pairs (759/s), flattened at 16 pairs (805/s), peaked at 32 (909/s) and fell to 678/s at 256; the Game Host never used more than 1.5 of its 4 cores, while the platform sat at about 3 of its 4 cores and Postgres at 1.6 to 1.8 of its 2. Steps 128 and 256 crossed the latency thresholds. Single-node, laptop result.

## 1. Run

| Field | Value |
|---|---|
| Scenario | `parallelism`, defaults (levels 1, 2, 4, 8, 16, 32, 64, 128, 256 pairs; 120 s steps, 20 s settle) |
| Parameters (`params.txt`) | `scenario=parallelism`, `K6_CORES=4`, no overrides |
| Start (UTC) | 2026-10-18T19:17:37Z |
| End (UTC) | 2026-10-18T19:35:30Z |
| Duration | 17 min 53 s (setup of about 14 s, then nine steps) |
| k6 exit code | 99 (thresholds on `tb_move_rtt{step:128}`, `tb_move_rtt{step:256}`, `tb_room_join{step:128}` crossed; the scenario does not abort on them, so all nine steps ran) |
| k6 version | k6 v2.2.0 (commit/00a9a1b7f5, go1.26.5, linux/amd64) |
| k6 pinned to CPUs | the last 4 of 16 (`taskset`, `K6_CORES=4`) |
| Run directory | `loadtest/results/20261018-211735-parallelism` (git-ignored) |

## 2. Environment

| Field | Value |
|---|---|
| Docker Desktop VM CPUs | 16 |
| Docker Desktop VM memory | 16,326,520,832 bytes (15.21 GiB, `docker info`) |
| `.wslconfig` | absent (VM defaults) |
| Host load during the run | `load1` mean 11.4, max 19.9 on 16 CPUs; `vm_cpu_pct` mean 47.4, max 68 (`samples.csv`, from the first step on) |
| Root commit | 47eb216c2b1ac9a30a9e18b7aaf3053412d7dfa2 |
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
every row passes for that step. Observed values are those of the last step that passed (64 pairs).

| Metric | Target | Observed p95 | Observed p99 | Pass |
|---|---|---|---|---|
| `tb_move_rtt` | p95 < 200 ms, p99 < 500 ms | 102 ms | 114 ms | pass at 64; fails at 128 (p95 223 ms) and 256 (p95 241 ms) |
| `tb_login`, `tb_room_create`, `tb_room_join` | p95 < 200 ms, p99 < 500 ms | `tb_room_join` 21.1 ms; `tb_room_create` 13.1 ms (`tb_login` happens in setup, not stepped) | `tb_room_join` 29.3 ms; `tb_room_create` 20.0 ms | pass at 64; `tb_room_join` fails at 128 (p99 511 ms) |
| `tb_lobby_event` | p95 < 300 ms, p99 < 600 ms | 99 ms | 111 ms | pass at every step (max p95 239 ms at 256) |
| `tb_game_start` (warm) | p95 < 1 s, p99 < 2 s (cold is recorded, not gated) | 110 ms | 124 ms | pass at every step (max p95 251 ms at 256) |
| Error rate (`tb_op_failed`) | < 1% | 0 at 64 | n/a | pass at every step (the 46 errors at 128 are 0.04% of operations) |
| Concurrent sessions | >= 500 | not attempted (this scenario peaks at 256 pairs; `sessions_active` max 210 at 256) | n/a | not attempted here; `ramp-to-break` measures it |
| Concurrent WebSockets | >= 5,000 | not attempted (512 sockets at 256 pairs) | n/a | not attempted here; `ramp-to-break` measures it |

## 4. Steps

`steps.csv`, one row per step. Moves per second is `count(tb_move_rtt) / (STEP_SECONDS - SETTLE_SECONDS)` = count / 100.
Generator-bound comes from `check-generator.sh` (k6 mean 15% to 129% of its 320% budget: no step is generator-bound).
CPU columns are the per-segment means of `snapshot.sh`; its segments start at the run launch, not at the first
step, so each is offset by the setup time of about 14 s. The first segment includes the cold JIT warm-up. No cold `tb_game_start` was sampled in this
run (every game start fell outside the 30 s cold window).

| Step (pairs) | Moves/s | `tb_move_rtt` p50 / p95 / p99 | `tb_game_start` warm p95 / p99 | `tb_game_start` cold p95 / p99 | Errors by code | Game Host CPU cores | Platform CPU cores | Generator-bound | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 102 | 4 / 6 / 8 ms | 13 / 16 ms | none sampled | 0 | 1.53 | 1.03 | no | pass |
| 2 | 224 | 4 / 5 / 6 ms | 11 / 12 ms | none sampled | 0 | 0.49 | 0.84 | no | pass |
| 4 | 384 | 4 / 6 / 7 ms | 12 / 15 ms | none sampled | 0 | 1.21 | 1.39 | no | pass |
| 8 | 759 | 5 / 9 / 12 ms | 16 / 20 ms | none sampled | 0 | 1.25 | 2.55 | no | pass |
| 16 | 805 | 10 / 15 / 20 ms | 24 / 31 ms | none sampled | 0 | 1.25 | 2.88 | no | pass |
| 32 | 909 | 23 / 47 / 54 ms | 54 / 63 ms | none sampled | 0 | 0.94 | 2.76 | no | pass |
| 64 | 897 | 49 / 102 / 114 ms | 110 / 124 ms | none sampled | 0 | 0.98 | 2.95 | no | pass |
| 128 | 788 | 103 / 223 / 253 ms | 232 / 263 ms | none sampled | `ready_timeout` x46 | 0.94 | 2.76 | no | fail |
| 256 | 678 | 205 / 241 / 270 ms | 251 / 277 ms | none sampled | 0 | 0.95 | 2.95 | no | fail |

Moves/s against Game Host CPU cores per step:

| Pairs | 1 | 2 | 4 | 8 | 16 | 32 | 64 | 128 | 256 |
|---|---|---|---|---|---|---|---|---|---|
| Moves/s | 102 | 224 | 384 | 759 | 805 | 909 | 897 | 788 | 678 |
| Game Host CPU cores (of 4) | 1.53 | 0.49 | 1.21 | 1.25 | 1.25 | 0.94 | 0.98 | 0.94 | 0.95 |
| Platform CPU cores (of 4) | 1.03 | 0.84 | 1.39 | 2.55 | 2.88 | 2.76 | 2.95 | 2.76 | 2.95 |

Moves/s plateaued at 16 pairs with Game Host CPU at 1.25 of 4 cores (something serialises). It scaled roughly
linearly up to 8 pairs (about 95 moves/s per pair), gained 6% from 8 to 16 pairs and 13% more by 32, then fell.
The Game Host is not the thing that serialises: its gRPC executor threads were parked in the dump below while
the platform pod held about 3.0 cores (`kubectl top`, mean 2.6 to 3.0 cores from step 8 on).

## 5. Result

Ceiling (pairs): 64
First to break: platform threads
Evidence: from 8 pairs the platform pod sits at 2.55 to 2.95 of its 4 cores (`kubectl top` agrees: 2.6 to 3.0) while the Game Host
stays at 0.9 to 1.25 of 4; platform threads rise from 80 to 226 (step 128 on) and the throughput peak (909/s at 32 pairs) is
followed by a decline while latency grows about linearly with the number of pairs (move p95 47 ms at 32, 102 at 64, 223 at 128, 241 at 256),
which is a closed-loop queue in front of a saturated stage. Postgres is at 1.6 to 1.8 of its 2 cores from step 16 on (`kubectl top`), so it
is a co-limit: the two cannot be separated with this data. `hikari_pending` was 0 up to step 128 (mean 0.43, max 3 only in the last
segment), Redis 0.4 of 1 core, 5xx never occurred, no restarts, the generator was never bound (k6 at most 129% of 320%).
The first thresholds to fail were at 128 pairs: `tb_move_rtt` p95 223 ms (target 200) and `tb_room_join` p99 511 ms (target 500).

## 6. Server side

`snapshot.sh` output (mean / max per 120 s segment; seg N is step N of the table above, see the offset note in section 4):

| metric (mean / max) | seg 1 (0s) | seg 2 (120s) | seg 3 (240s) | seg 4 (360s) | seg 5 (480s) | seg 6 (600s) | seg 7 (720s) | seg 8 (840s) | seg 9 (960s) |
|---|---|---|---|---|---|---|---|---|---|
| gamehost_cpu_cores | 1.532 / 2.849 | 0.488 / 1.048 | 1.206 / 1.661 | 1.249 / 1.904 | 1.253 / 2.585 | 0.935 / 1.013 | 0.979 / 1.027 | 0.939 / 1.102 | 0.952 / 0.983 |
| platform_cpu_cores | 1.032 / 2.176 | 0.837 / 0.974 | 1.392 / 1.729 | 2.553 / 2.725 | 2.88 / 2.965 | 2.756 / 2.96 | 2.95 / 3.003 | 2.76 / 2.992 | 2.949 / 2.979 |
| gamehost_heap_bytes | 310315281 / 433732496 | 422462168 / 487943376 | 400544051 / 505384552 | 392443524 / 502108384 | 378563575 / 477726648 | 362770615 / 486889064 | 371795129 / 484912584 | 403339908 / 506488856 | 382256701.714 / 450564744 |
| platform_heap_bytes | 266656149 / 501878512 | 162353118 / 244009296 | 144831259 / 230147112 | 147043489 / 233868608 | 172384040 / 238995552 | 177611215 / 256301920 | 186144636 / 251570328 | 277494503 / 396872864 | 285939048 / 423041160 |
| gamehost_threads | 48 / 50 | 49.25 / 50 | 51.375 / 52 | 53.875 / 55 | 53.375 / 54 | 52.5 / 53 | 52.5 / 53 | 53.25 / 56 | 52 / 52 |
| platform_threads | 74.625 / 81 | 79.5 / 81 | 79.625 / 80 | 79.75 / 80 | 83 / 87 | 102.875 / 106 | 105.75 / 106 | 150.25 / 226 | 226 / 226 |
| gamehost_gc_seconds_per_s | 0.002 / 0.004 | 0.002 / 0.003 | 0.002 / 0.003 | 0.002 / 0.002 | 0.002 / 0.002 | 0.002 / 0.002 | 0.002 / 0.003 | 0.002 / 0.002 | 0.002 / 0.002 |
| platform_gc_seconds_per_s | 0.028 / 0.104 | 0.001 / 0.001 | 0.001 / 0.002 | 0.003 / 0.004 | 0.004 / 0.005 | 0.004 / 0.004 | 0.005 / 0.005 | 0.005 / 0.006 | 0.005 / 0.006 |
| http_p95_seconds | 0.053 / 0.111 | 0.005 / 0.005 | 0.006 / 0.007 | 0.007 / 0.008 | 0.009 / 0.01 | 0.011 / 0.013 | 0.012 / 0.012 | 0.026 / 0.062 | 0.019 / 0.022 |
| http_p99_seconds | 0.064 / 0.136 | 0.006 / 0.007 | 0.007 / 0.008 | 0.009 / 0.01 | 0.012 / 0.014 | 0.025 / 0.043 | 0.018 / 0.019 | 0.128 / 0.326 | 0.031 / 0.043 |
| http_5xx_per_s | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| http_req_per_s | 29.211 / 76.766 | 28.007 / 35.313 | 49.67 / 63.959 | 104.37 / 119.141 | 136.037 / 146.13 | 131.234 / 145.563 | 143.362 / 145.146 | 133.878 / 142.916 | 135.302 / 136.645 |
| hikari_active | 0 / 0 | 0.375 / 1 | 1 / 3 | 2.875 / 5 | 2.125 / 4 | 2.375 / 5 | 3.875 / 7 | 3.5 / 6 | 5.714 / 10 |
| hikari_pending | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0.429 / 3 |
| ws_connections | 1.5 / 2 | 3.5 / 4 | 7.25 / 8 | 15.5 / 16 | 31.25 / 32 | 56 / 64 | 125.75 / 128 | 236.25 / 444 | 511.857 / 512 |
| rooms_active | 0.75 / 1 | 1.75 / 2 | 3.5 / 4 | 6.875 / 8 | 14.375 / 16 | 29.875 / 32 | 59.25 / 64 | 112.75 / 128 | 252 / 254 |
| sessions_active | 0.5 / 1 | 1.25 / 2 | 2.375 / 3 | 4 / 5 | 8.875 / 13 | 24.375 / 28 | 47.625 / 55 | 90.875 / 104 | 202.571 / 210 |
| up | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 |


| | At start | At end |
|---|---|---|
| Redis `used_memory_human` | n/a (sampled once, after the run) | 6.51M |
| Redis `connected_clients` | n/a (sampled once, after the run) | 5 |

Pod restarts and `OOMKilled` (from `cluster.txt`): all twelve pods 0 restarts, no termination reason recorded.

Missing metrics: `http_5xx_per_s` (no 5xx request ever happened; Micrometer creates the series on first use)

Per-pod CPU from `kubectl top` (`pods.csv`, millicores, mean per segment 1 to 9): platform 819, 915, 1483, 2623, 2960, 2805, 3043, 2817, 2985;
Game Host 1409, 545, 1288, 1230, 1300, 948, 1007, 939, 973; Postgres 114, 285, 536, 1156, 1569, 1573, 1767, 1683, 1842;
Redis 73, 185, 277, 413, 439, 420, 444, 417, 436; frontend nginx 31, 75, 133, 255, 308, 297, 333, 308, 328. ingress-nginx is in another namespace and was not sampled per segment (2m at the end).

Game Host thread dump at the plateau step, taken in a separate re-run of that step only (`LEVELS=16 STEP_SECONDS=240`,
run directory `loadtest/results/20261018-214127-parallelism`, dump 70 s and 90 s into the step; `jcmd 7`, because the JVM is PID 7 behind `supervise.sh`
and the plan's `jcmd 1` fails with "target process 1 doesn't respond"): 66 threads in total, 8 `grpc-default-executor-*` all
`TIMED_WAITING (parking)` on the `SynchronousQueue` that idle pool threads wait on, in both dumps (one of eight `RUNNABLE` in the first); no thread blocked on a monitor.
Highest CPU time of the whole process: `lettuce-nioEventLoop-4-2` 72.8 s and `grpc-default-worker-ELG-3-3` 66.5 s; the busiest executor thread 23.1 s. One executor thread:

```
"grpc-default-executor-1" #77 daemon prio=5 cpu=21773.60ms elapsed=461.78s
   java.lang.Thread.State: TIMED_WAITING (parking)
	at jdk.internal.misc.Unsafe.park(java.base@21.0.2/Native Method)
	at java.util.concurrent.locks.LockSupport.parkNanos(java.base@21.0.2/LockSupport.java:410)
	at java.util.concurrent.LinkedTransferQueue$DualNode.await(java.base@21.0.2/LinkedTransferQueue.java:452)
	at java.util.concurrent.SynchronousQueue$Transferer.xferLifo(java.base@21.0.2/SynchronousQueue.java:194)
	at java.util.concurrent.SynchronousQueue.xfer(java.base@21.0.2/SynchronousQueue.java:233)
	at java.util.concurrent.SynchronousQueue.poll(java.base@21.0.2/SynchronousQueue.java:336)
	at java.util.concurrent.ThreadPoolExecutor.getTask(java.base@21.0.2/ThreadPoolExecutor.java:1069)
```

During that re-run `kubectl top` showed the Game Host at 1000m and the platform at 3066m.

## 7. Errors by code

| Code | Expected | Count |
|---|---|---|
| `ready_timeout` | no | 46 (all in the 128-pair step) |

## 8. Findings

- **Throughput plateaus at 16 pairs and declines past 32.** 805 moves/s at 16, 909 at 32, 678 at 256 (a 25% drop from the peak) with the Game Host at 0.94 to 1.25 of 4 cores. The Game Host is not the limit: its dump shows idle gRPC executors. Suspected cause: the platform pod at about 3 of 4 cores (and Postgres at 1.6 to 1.8 of 2), which also carries the STOMP broker, HTTP and the game-event fan-out. Not checked: CPU throttling counters of the platform pod (which would explain why it does not use the fourth core), a platform thread dump, Postgres query statistics.
- **The 200 ms move target fails at 128 pairs (256 sockets).** `tb_move_rtt` p95 223 ms, p99 253 ms; at 256 pairs p95 241 ms. `tb_room_join` p99 511 ms (target 500) at 128 pairs, also the only step where it exceeds its p99 target. Latency grows about linearly with the pair count from 16 pairs on, which is queueing behind the saturated stage.
- **46 `ready_timeout` errors, all in the 128-pair step** (0.04% of 124,729 operations, under the 1% error threshold). A player waited the full timeout for the ready broadcast. The README's `SUBSCRIBE_SETTLE_MS` note describes a similar race at low load; whether this is that race or a late broadcast under load was not determined. Not checked: which room, and whether the broadcast was sent late or lost.
- **Platform threads grow from 80 to 226** (step 64: 106, step 128: mean 150, max 226; step 256: 226 flat), with `hikari_pending` mean 0.43 (max 3) only in the last segment. Hikari active connections peaked at 10, so the pool is unlikely to be the limit.
- **Harness defect in the run protocol: `jcmd 1` does not work in the Game Host image.** PID 1 is `supervise.sh` and the JVM is PID 7. Not fixed in the plan (the plan is a working file); the dump above used PID 7. `IMP-M15-12` and `13` should use `jcmd 7`.
- No restart, no `OOMKilled`, no 5xx, no generator-bound step.

## 9. Constants

- This is a single-node, laptop ceiling: Docker Desktop Kubernetes on one WSL2 VM shared with the load generator. It is the ceiling of this machine, not of the platform.
- Latency is measured per request from a closed-loop client at the configured think time, so coordinated omission applies: when the system slows, the client issues fewer requests and the percentiles understate the delay a constant-rate client would see. `start-rate` is open-loop.
- One step is generator-bound when the k6 process averages more than 80% of its pinned cores after the settle window; such a step never counts as the platform's breaking point.
- The first `SETTLE_SECONDS` of every step are excluded from that step's thresholds.
- A crossed threshold aborts the run no earlier than 30 s after the test start (`delayAbortEval` counts from the test start, not from the step), so a step's first samples after its settle window can trip a one-sample percentile.
