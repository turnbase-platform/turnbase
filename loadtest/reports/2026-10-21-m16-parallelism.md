# Parallelism scenario report, M16 re-verification, 2026-10-21

**Verdict:** Throughput peaked at 1,055 moves/s at 32 pairs (909 in Phase A) and held 998 at 128 before falling to 637 at 256; the ceiling is again 64 pairs, because at 128 pairs `tb_move_rtt` p95 reached 200 ms and `tb_room_create` and `tb_room_join` p95 and p99 crossed their targets. The platform pod sat at 2.6 to 3.0 of its 4 cores while Postgres sat at its 2-core limit and the 10-connection Hikari pool queued up to 207 requests; the Game Host never used more than 1.2 of 4 cores. No error in 97,015 games (46 `ready_timeout` in Phase A), no stall. Single-node, laptop result.

## 1. Run

| Field | Value |
|---|---|
| Scenario | `parallelism`, defaults (levels 1, 2, 4, 8, 16, 32, 64, 128, 256 pairs; 120 s steps, 20 s settle), after `USERS=3000` provisioning |
| Parameters (`params.txt`) | `scenario=parallelism`, `K6_CORES=4`, `USERS=3000` |
| Start (UTC) | 2026-10-21T19:38:47Z |
| End (UTC) | 2026-10-21T19:56:28Z |
| Duration | 17 min 41 s (setup of about 14 s, then the load) |
| k6 exit code | 99 (thresholds on `tb_move_rtt`, `tb_room_create` and `tb_room_join` at 128 and 256 pairs crossed; the scenario does not abort on them, so all nine steps ran) |
| k6 version | k6 v2.2.0 (commit/00a9a1b7f5, go1.26.5, linux/amd64) |
| k6 pinned to CPUs | the last 4 of 16 (`taskset`, `K6_CORES=4`) |
| Run directory | `loadtest/results/20261021-213845-parallelism` (git-ignored) |

## 2. Environment

| Field | Value |
|---|---|
| Docker Desktop VM CPUs | 16 |
| Docker Desktop VM memory | 16,326,524,928 bytes (15.21 GiB, `docker info`) |
| `.wslconfig` | absent (VM defaults) |
| Host load during the run | `load1` mean 17.6, max 36.1 on 16 CPUs; `vm_cpu_pct` mean 53.5, max 76; k6 mean 99% of 400% (`samples.csv`, from the first step on) |
| Root commit | c196eef90e718c28e87393a8c72b25911c83dd1d (the report is committed after it) |
| `turnbase-common` | 57a102a94421c5b6122d18c1984e5a0b97f5e7bd |
| `turnbase-sdk` | ab3641d692101b829c9702f5e7a1567b45d589a4 |
| `turnbase-platform` | 65d9d743537aa8b9f15ed445ae97fd292146cafa |
| `turnbase-game-host` | b121989520f992f632ffb0dabd336924e2fc9530 |
| `turnbase-frontend` | 9b480fe73496f946902916f6ec3084b8d9b0d2bc |
| `turnbase-game-tictactoe` | c5a0d084967919924f36fa395d67bfd371778348 |
| Image IDs | platform `sha256:9f8da253923e...`, game-host `sha256:15f70fd3ccc5...`, frontend `sha256:3663712f5b6e...` (full IDs in `cluster.txt`) |
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
    value: -XX:MaxRAMPercentage=70 -Xlog:gc*,safepoint:stdout:utctime,uptime
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
  extraArgs:
  - -c
  - shared_preload_libraries=pg_stat_statements
  - -c
  - log_checkpoints=on
  ownerPassword: <redacted>
  resources:
    limits:
      cpu: "2"
      memory: 1Gi
    requests:
      cpu: "2"
      memory: 1Gi
redis:
  extraArgs: []
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
| `tb_move_rtt` | p95 < 200 ms, p99 < 500 ms | 89 ms | 126 ms | pass at 64; p95 200 ms at 128 (fails), 274 ms at 256 |
| `tb_login`, `tb_room_create`, `tb_room_join` | p95 < 200 ms, p99 < 500 ms | `tb_room_join` 158 ms; `tb_room_create` 120 ms (`tb_login` happens in setup, not stepped) | `tb_room_join` 213 ms; `tb_room_create` 170 ms | pass at 64; fail at 128 (`tb_room_join` p95 348 ms, p99 481 ms; `tb_room_create` p95 283 ms) and 256 (`tb_room_join` p99 565 ms) |
| `tb_lobby_event` | p95 < 300 ms, p99 < 600 ms | 57 ms | 89 ms | pass at every step (max p95 194 ms, p99 267 ms at 256) |
| `tb_game_start` (warm) | p95 < 1 s, p99 < 2 s (cold is recorded, not gated) | 164 ms | 226 ms | pass at every step (max p95 467 ms, p99 588 ms at 256) |
| Error rate (`tb_op_failed`) | < 1% | 0 | n/a | pass at every step (0 errors in the run) |
| Concurrent sessions | >= 500 | not attempted (this scenario peaks at 256 pairs; `sessions_active` max 197) | n/a | not attempted here; `ramp-to-break` measures it |
| Concurrent WebSockets | >= 5,000 | not attempted (506 sockets at 256 pairs) | n/a | not attempted here; `ramp-to-break` measures it |

## 4. Steps

`steps.csv`, one row per step. Moves per second is `count(tb_move_rtt) / (STEP_SECONDS - SETTLE_SECONDS)` = count / 100. CPU columns are the means of the Prometheus series over the measured part of the step (`scenario.epoch + step * 120 + 20` to the end of the step; the first row also holds the cold JIT warm-up of the Game Host). The one cold game start (7.6 s, the maximum of `tb_game_start`) fell into the warm-up window of step 1, so no step has a cold sample.

| Step | Moves/s | `tb_move_rtt` p50 / p95 / p99 | `tb_game_start` warm p95 / p99 | `tb_game_start` cold p95 / p99 | Errors by code | Game Host CPU cores | Platform CPU cores | Generator-bound | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 104 | 5 / 7 / 10 ms | 15 / 19 ms | none sampled | 0 | 2.30 | 0.69 | no | pass |
| 2 | 228 | 5 / 6 / 8 ms | 13 / 15 ms | none sampled | 0 | 0.72 | 1.04 | no | pass |
| 4 | 432 | 5 / 7 / 9 ms | 14 / 17 ms | none sampled | 0 | 0.87 | 1.79 | no | pass |
| 8 | 712 | 6 / 11 / 14 ms | 20 / 25 ms | none sampled | 0 | 0.86 | 2.69 | no | pass |
| 16 | 955 | 10 / 21 / 30 ms | 38 / 51 ms | none sampled | 0 | 1.04 | 3.03 | no | pass |
| 32 | 1055 | 17 / 42 / 59 ms | 72 / 96 ms | none sampled | 0 | 1.03 | 2.94 | no | pass |
| 64 | 1017 | 39 / 89 / 126 ms | 164 / 226.32 ms | none sampled | 0 | 1.02 | 2.90 | no | pass |
| 128 | 998 | 78 / 200 / 280 ms | 349 / 472.41 ms | none sampled | 0 | 0.96 | 2.76 | no | fail |
| 256 | 637 | 139 / 274 / 359 ms | 467.15 / 588 ms | none sampled | 0 | 0.92 | 2.61 | no | fail |

Generator check (`check-generator.sh`): 1: k6 mean 15% of 320% -> ok; 2: k6 mean 32% of 320% -> ok; 3: k6 mean 62% of 320% -> ok; 4: k6 mean 106% of 320% -> ok; 5: k6 mean 139% of 320% -> ok; 6: k6 mean 141% of 320% -> ok; 7: k6 mean 142% of 320% -> ok; 8: k6 mean 137% of 320% -> ok; 9: k6 mean 126% of 320% -> ok

Resources per measured window (mean over the step after the settle):

| Step | Postgres / Redis cores (`kubectl top`, mean) | Hikari active / pending (max) | Platform threads (max) | Game Host threads (max) | HTTP p95 / p99 (mean, ms) | WebSockets (max) | Sessions (max) |
|---|---|---|---|---|---|---|---|
| 1 | 0.15 / 0.22 | 0 / 0 | 87 | 47 | 33 / 38 | 2 | 1 |
| 2 | 0.36 / 0.44 | 2 / 0 | 91 | 47 | 6 / 7 | 4 | 2 |
| 4 | 0.74 / 0.69 | 1 / 0 | 97 | 49 | 7 / 8 | 8 | 3 |
| 8 | 1.35 / 0.81 | 4 / 0 | 101 | 53 | 8 / 11 | 16 | 7 |
| 16 | 1.91 / 0.67 | 8 / 0 | 111 | 62 | 13 / 21 | 42 | 14 |
| 32 | 2.06 / 0.53 | 10 / 25 | 131 | 75 | 31 / 43 | 83 | 26 |
| 64 | 2.08 / 0.47 | 10 / 75 | 181 | 98 | 60 / 87 | 172 | 48 |
| 128 | 2.08 / 0.46 | 10 / 135 | 269 | 111 | 127 / 189 | 342 | 93 |
| 256 | 2.06 / 0.45 | 10 / 207 | 292 | 118 | 246 / 354 | 506 | 196 |

## 5. Result

Ceiling (pairs): 64
First to break: DB pool
Evidence: from 16 pairs on the 10-connection Hikari pool is fully active (10 of 10) and requests queue behind it: `hikari_pending` maximum 27 at 16, 61 at 32, 131 at 64, 199 at 128 and 207 at 256 (0 up to 128 pairs in Phase A), while Postgres uses 1.91 to 2.08 of its 2 cores (`kubectl top`, at its limit) and the platform 2.6 to 3.0 of 4. Throughput therefore stops growing at 16 pairs (955 moves/s) and peaks at 32 (1,055); latency grows with the pair count (move p95 21 ms at 16, 42 at 32, 89 at 64, 200 at 128, 274 at 256; `tb_room_join` p95 32, 73, 158, 348, 451 ms). The first thresholds to fail are at 128 pairs: `tb_move_rtt` p95 200 ms (target below 200) and `tb_room_create` / `tb_room_join` p95 283 / 348 ms. The Game Host stays at 0.7 to 1.2 of 4 cores, Redis at 0.4 to 0.8 of 1, no restart, no 5xx, no generator-bound step (k6 at most 142% of 320%).

`Ceiling (pairs)` is one integer: the last step all of whose thresholds passed and that is not
generator-bound, or `<n> (not reached)` when no step failed. `First to break` is exactly one of:
`Game Host CPU`, `Espresso contention`, `DB pool`, `Redis`, `platform threads`, `ingress / frontend nginx`,
`k6 itself`, `memory (OOM)`, `none`. A report for `start-rate` writes `Ceiling (games/s): <n>` instead.

## 6. Server side

Output of `snapshot.sh` (mean / max per segment; segment N starts N x 120 s after the launch, so each is offset by the setup time):

| metric (mean / max) | seg 1 (0s) | seg 2 (120s) | seg 3 (240s) | seg 4 (360s) | seg 5 (480s) | seg 6 (600s) | seg 7 (720s) | seg 8 (840s) | seg 9 (960s) |
|---|---|---|---|---|---|---|---|---|---|
| gamehost_cpu_cores | 1.73 / 2.681 | 1.08 / 2.206 | 0.862 / 1.727 | 0.823 / 0.91 | 1.014 / 1.063 | 1.136 / 1.769 | 1.028 / 1.095 | 0.969 / 0.999 | 0.923 / 0.945 |
| platform_cpu_cores | 1.106 / 3.168 | 0.954 / 1.058 | 1.674 / 1.852 | 2.566 / 2.742 | 2.994 / 3.094 | 2.953 / 3.002 | 2.903 / 2.985 | 2.783 / 2.851 | 2.622 / 2.663 |
| gamehost_heap_bytes | 182499642 / 269231952 | 212673608 / 255913712 | 221602838 / 278495032 | 182994437 / 243819576 | 195561079 / 246910576 | 230553247 / 283200200 | 205436186 / 272381056 | 241989284 / 287407440 | 223195334.667 / 283354976 |
| platform_heap_bytes | 308709648 / 791674880 | 183002026 / 257391992 | 138295099 / 244507592 | 210296385 / 257075040 | 173093749 / 241378800 | 195227142 / 247440752 | 220336230 / 269201696 | 278063211 / 365564952 | 313265192 / 364896288 |
| gamehost_threads | 44.25 / 47 | 46.875 / 47 | 47.75 / 49 | 51 / 53 | 59 / 62 | 74.375 / 76 | 94.875 / 98 | 108.625 / 111 | 116 / 118 |
| platform_threads | 77.625 / 87 | 89.625 / 91 | 95.125 / 97 | 99.75 / 101 | 108.125 / 111 | 125.125 / 131 | 165.75 / 181 | 239 / 269 | 292 / 292 |
| gamehost_gc_seconds_per_s | 0.003 / 0.006 | 0.002 / 0.003 | 0.001 / 0.002 | 0.002 / 0.003 | 0.004 / 0.005 | 0.006 / 0.006 | 0.006 / 0.006 | 0.006 / 0.007 | 0.006 / 0.007 |
| platform_gc_seconds_per_s | 0.025 / 0.089 | 0.001 / 0.001 | 0.002 / 0.002 | 0.003 / 0.004 | 0.004 / 0.005 | 0.006 / 0.006 | 0.007 / 0.008 | 0.007 / 0.008 | 0.006 / 0.006 |
| http_p95_seconds | 0.052 / 0.109 | 0.006 / 0.006 | 0.007 / 0.007 | 0.008 / 0.009 | 0.012 / 0.014 | 0.028 / 0.033 | 0.057 / 0.063 | 0.119 / 0.132 | 0.235 / 0.251 |
| http_p99_seconds | 0.057 / 0.115 | 0.007 / 0.008 | 0.008 / 0.009 | 0.01 / 0.012 | 0.019 / 0.022 | 0.041 / 0.047 | 0.083 / 0.089 | 0.178 / 0.2 | 0.347 / 0.356 |
| http_5xx_per_s | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| http_req_per_s | 33.909 / 92.591 | 28.93 / 35.584 | 55.971 / 66.154 | 96.772 / 110.462 | 138.939 / 152.71 | 162.924 / 171.106 | 165.263 / 175.428 | 161.84 / 167.109 | 149.743 / 156.555 |
| hikari_active | 0 / 0 | 0.75 / 2 | 1 / 2 | 2.25 / 4 | 3.75 / 8 | 8.875 / 10 | 9.125 / 10 | 10 / 10 | 10 / 10 |
| hikari_pending | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 10.25 / 27 | 38.75 / 75 | 119 / 135 | 194.167 / 207 |
| ws_connections | 1.5 / 2 | 3.75 / 4 | 7.5 / 8 | 15.25 / 16 | 31.5 / 42 | 65.625 / 83 | 131.625 / 172 | 263.125 / 342 | 499.333 / 506 |
| rooms_active | 0.75 / 1 | 1.625 / 2 | 3.75 / 4 | 7.5 / 8 | 15 / 16 | 32 / 32 | 62.25 / 64 | 122.5 / 124 | 247.167 / 251 |
| sessions_active | 0.25 / 1 | 1.25 / 2 | 2.75 / 3 | 6.25 / 7 | 12.25 / 14 | 23.5 / 26 | 46.5 / 48 | 89.5 / 93 | 187.167 / 197 |
| up | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 |

| | At start | At end of the run (last sample) | After the run (snapshot) |
|---|---|---|---|
| Redis `used_memory` / keys | 1.10 MiB / 5 | 2.19 MiB / 2132 (peak 2132 keys, 2.19 MiB) | 1.60M / 6 |
| Redis `connected_clients` | n/a (sampled once, after the run) | n/a | 5 |

Pod restarts and `OOMKilled` (from `cluster.txt`): platform, Game Host and frontend 0 restarts; Postgres, Redis and the observability pods show 3 to 4 restarts, all from before this run (last one about 3 h before it started); no `OOMKilled`.

Missing metrics: http_5xx_per_s (no 5xx request ever happened; Micrometer creates the series on first use)

Platform thread census at the end of the run (`census-snapshot.txt`, taken after the last step): 305 threads, of which 210 `http-nio` workers (Tomcat is waiting on the saturated pool), 16 + 16 STOMP channel threads and 5 Lettuce loops. Game Host: 108 threads, of which 53 `grpc-default-executor` (idle). Redis held 2,132 keys at the end of the load and 6 (`DBSIZE`) after the snapshot, so the per-room keys of finding 13 are released.

Postgres `pg_stat_statements` (reset at the start of the run), by total execution time: the occupancy query over `room_team` / `room_participant` 97,015 calls, 2.84 ms mean, 275.5 s in total; the team lookup `select t.team_id ... left join (... count(*) as occupied ...)` 38,806 calls, 2.79 ms mean, 108.2 s; `select room_id, grace_reservation_id ... from room_participant where user_id = $1 and left_at is null` 38,806 calls, 2.49 ms mean, 96.6 s (no row returned); the participant joins of the room (933,930 calls each, 0.04 to 0.08 ms) 115 s together. By calls, the participant lookup runs 9.6 times per completed game (933,930 / 97,015).

## 7. Errors by code

| Code | Expected | Count |
|---|---|---|
| none | n/a | 0 |

## 8. Findings

- **Finding 1 persists, at a higher level.** Moves/s 955 at 16 pairs, 1,055 at 32, 1,017 at 64, 998 at 128 and 637 at 256 (909 at 32 and 678 at 256 in Phase A), so the peak is 16% higher and the decline at 256 pairs is steeper (40% below the peak). Moves/s no longer scales between 16 and 128 pairs while the Game Host uses 0.7 to 1.2 of 4 cores. What binds is the database: Postgres at 2.06 of 2 cores and 10 of 10 pool connections busy from 16 pairs, with `hikari_pending` up to 207. Not checked: the Postgres CPU split between the statements listed above, a larger pool, the throttling counters of the Postgres pod.
- **Finding 2 persists at the same pair count.** `tb_move_rtt` p95 is 200 ms at 128 pairs (223 ms in Phase A) and 274 ms at 256 (241); p99 280 and 359 ms (253, 270). The target fails at 128 pairs as before, by the smallest possible margin this time. HTTP operations got slower while moves got faster: `tb_room_join` p95 is 158 ms at 64 pairs (21 ms in Phase A) and 348 ms at 128 (the target of 200 ms is crossed at 128 pairs as before), `tb_room_create` p95 120 ms at 64 (13 ms). The pool queue (finding 1) sits in front of every HTTP request, while a move uses the connection for less time.
- **Finding 4 is resolved in this run.** 0 errors of any code in 97,015 games and 739,900 moves, including the 128-pair step where Phase A had 46 `ready_timeout`.
- **Finding 10 is resolved here.** `ws_connecting` maximum 600 ms over 38,806 connects (10.0 s in Phase A) and no `http_req_duration` outlier above 67 ms.
- **Platform threads rise to 292** (88 at 1 pair, 159 at 32, 229 at 64, 292 at 128 and 256; 226 at most in Phase A), almost all of it Tomcat workers waiting for a connection (210 `http-nio` workers in the census). The M16-10 bounds hold for the STOMP channels (16 + 16) and gRPC, but the worker pool is not bounded by the pool size. Game Host threads rise from 44 to 118 (56 in Phase A), 53 of them idle `grpc-default-executor` threads, and stay there after the load. Not checked: whether the Game Host figure is the executor's cached pool growing with the number of concurrent calls.
- No restart, no `OOMKilled`, no 5xx, no generator-bound step. 

## 9. Phase A vs M16

| Pairs | 1 | 2 | 4 | 8 | 16 | 32 | 64 | 128 | 256 |
|---|---|---|---|---|---|---|---|---|---|
| Moves/s, Phase A | 102 | 224 | 384 | 759 | 805 | 909 | 897 | 788 | 678 |
| Moves/s, M16 | 104 | 228 | 432 | 712 | 955 | 1,055 | 1,017 | 998 | 637 |
| `tb_move_rtt` p95 ms, Phase A | 6 | 5 | 6 | 9 | 15 | 47 | 102 | 223 | 241 |
| `tb_move_rtt` p95 ms, M16 | 7 | 6 | 7 | 11 | 21 | 42 | 89 | 200 | 274 |
| `tb_room_join` p95 ms, Phase A | n/a | n/a | n/a | n/a | n/a | n/a | 21 | n/a (p99 511) | n/a |
| `tb_room_join` p95 ms, M16 | 9 | 8 | 10 | 15 | 32 | 73 | 158 | 348 | 451 |
| Platform cores at the step, M16 | 0.67 | 1.03 | 1.79 | 2.69 | 3.02 | 2.94 | 2.89 | 2.75 | 2.61 |

| | Phase A | M16 |
|---|---|---|
| Ceiling (pairs) | 64 | 64 |
| Peak moves/s | 909 (32 pairs) | 1,055 (32 pairs) |
| Errors | 46 `ready_timeout` | 0 |
| Platform threads, maximum | 226 | 292 |
| Game Host threads, maximum | 56 | 118 |
| `hikari_pending`, maximum | 3 | 207 |
| Postgres cores at 64 pairs (`kubectl top`) | 1.77 | 2.08 |
| Redis keys after the run | 36,047 after `up-down` | 6 |

Phase A rows come from `2026-10-18-parallelism.md`; its per-step platform cores were means over segments offset by the setup time, so they are not repeated here.

## 10. Constants

- This is a single-node, laptop ceiling: Docker Desktop Kubernetes on one WSL2 VM shared with the load generator. It is the ceiling of this machine, not of the platform.
- Latency is measured per request from a closed-loop client at the configured think time, so coordinated omission applies: when the system slows, the client issues fewer requests and the percentiles understate the delay a constant-rate client would see. `start-rate` is open-loop.
- One step is generator-bound when the k6 process averages more than 80% of its pinned cores after the settle window; such a step never counts as the platform's breaking point.
- The first `SETTLE_SECONDS` of every step are excluded from that step's thresholds.
- A crossed threshold aborts the run no earlier than 30 s after the test start (`delayAbortEval` counts from the test start, not from the step), so a step's first samples after its settle window can trip a one-sample percentile.
