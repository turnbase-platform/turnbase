# Ramp to break, M16 re-verification, 2026-10-21

**Verdict:** Ceiling 80 pairs (160 sockets, 62 concurrent sessions at most): the run aborted 54 s into the 90-pair step because `tb_room_join{step:90}` crossed p95 200 ms while it was running (the partial step ends at 199.9 ms over 763 joins, so the crossing was by a hair); move, lobby and game-start latencies were still far inside their targets and 0 operations failed. Phase A stopped at 70 pairs. Neither the 500-session nor the 5,000-WebSocket target was reached. Single-node, laptop result.

## 1. Run

| Field | Value |
|---|---|
| Scenario | `ramp-to-break`, defaults (start 10 pairs, +10 per step, 120 s steps, 20 s settle, abort on a failed threshold), `MAX_PAIRS=1500`, after `USERS=3000` provisioning |
| Parameters (`params.txt`) | `scenario=ramp-to-break`, `K6_CORES=4`, `USERS=3000`, `MAX_PAIRS=1500` |
| Start (UTC) | 2026-10-21T20:01:17Z |
| End (UTC) | 2026-10-21T20:18:53Z |
| Duration | 17 min 36 s (setup of about 42 s, then the load) |
| k6 exit code | 99 (`tb_room_join{step:90}` crossed, `abortOnFail` stopped the test; a normal finish for this scenario) |
| k6 version | k6 v2.2.0 (commit/00a9a1b7f5, go1.26.5, linux/amd64) |
| k6 pinned to CPUs | the last 4 of 16 (`taskset`, `K6_CORES=4`) |
| Run directory | `loadtest/results/20261021-220115-ramp-to-break` (git-ignored) |

## 2. Environment

| Field | Value |
|---|---|
| Docker Desktop VM CPUs | 16 |
| Docker Desktop VM memory | 16,326,524,928 bytes (15.21 GiB, `docker info`) |
| `.wslconfig` | absent (VM defaults) |
| Host load during the run | `load1` mean 23.6, max 32.3 on 16 CPUs; `vm_cpu_pct` mean 64.4, max 76; k6 mean 132% of 400% (`samples.csv`, from the first step on) |
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
every row passes for that step. Observed values are those of the last step that passed (80 pairs); step 90 was aborted after 54 s, of which 34 s were measured, and its figures are in the steps table.

| Metric | Target | Observed p95 | Observed p99 | Pass |
|---|---|---|---|---|
| `tb_move_rtt` | p95 < 200 ms, p99 < 500 ms | 95 ms | 121 ms | pass at every step run (step 90: 100 / 130 ms) |
| `tb_login`, `tb_room_create`, `tb_room_join` | p95 < 200 ms, p99 < 500 ms | `tb_room_join` 181 ms; `tb_room_create` 127 ms (`tb_login` happens in setup, not stepped) | `tb_room_join` 216 ms; `tb_room_create` 169 ms | pass at 80; at 90 the abort fired on `tb_room_join` when its running p95 passed 200 ms (final partial value 199.9 / 235.5 ms, `tb_room_create` 157 / 193 ms) |
| `tb_lobby_event` | p95 < 300 ms, p99 < 600 ms | 66 ms | 90 ms | pass at every step run (step 90: 73 / 98 ms) |
| `tb_game_start` (warm) | p95 < 1 s, p99 < 2 s (cold is recorded, not gated) | 170 ms | 205 ms | pass at every step run (step 90: 183 / 226 ms) |
| Error rate (`tb_op_failed`) | < 1% | 0 | n/a | pass at every step (0 errors in the run) |
| Concurrent sessions | >= 500 | not reached: `sessions_active` max 62 at step 80, 67 at the abort | n/a | not reached |
| Concurrent WebSockets | >= 5,000 | not reached: 160 at step 80 (2 x 80), 180 open at the abort | n/a | not reached |

## 4. Steps

`steps.csv`, one row per step; the scenario declares 150 steps and only steps 10 to 90 ran, so the rest are left out. Moves per second is `count(tb_move_rtt) / (STEP_SECONDS - SETTLE_SECONDS)` = count / 100; step 90 ran 54 s and was divided by its 34 measured seconds instead (28,981 moves). CPU columns are the means of the Prometheus series over the measured part of the step. The Game Host pod was 4 minutes old when the load started and used 3.0 and 2.8 cores in steps 10 and 20 against 0.8 to 1.1 from step 30 on; that fits JIT warm-up of a new pod, which was not checked separately. The cold game start (10.4 s, the maximum of `tb_game_start`) fell into the warm-up window, so no step has a cold sample.

| Step | Moves/s | `tb_move_rtt` p50 / p95 / p99 | `tb_game_start` warm p95 / p99 | `tb_game_start` cold p95 / p99 | Errors by code | Game Host CPU cores | Platform CPU cores | Generator-bound | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 10 | 667 | 8 / 14 / 20 ms | 23 / 29 ms | none sampled | 0 | 3.02 | 2.37 | no | pass |
| 20 | 926 | 12 / 22 / 36 ms | 36 / 48 ms | none sampled | 0 | 2.80 | 2.82 | no | pass |
| 30 | 1067 | 15 / 30 / 38 ms | 52 / 62 ms | none sampled | 0 | 1.06 | 3.05 | no | pass |
| 40 | 1032 | 21 / 42 / 52 ms | 69 / 81 ms | none sampled | 0 | 0.98 | 2.91 | no | pass |
| 50 | 1012 | 28 / 53 / 67 ms | 88 / 106 ms | none sampled | 0 | 0.93 | 2.78 | no | pass |
| 60 | 987 | 34 / 64 / 80 ms | 106 / 138 ms | none sampled | 0 | 0.89 | 2.68 | no | pass |
| 70 | 907 | 43 / 80 / 100 ms | 143 / 174 ms | none sampled | 0 | 0.88 | 2.63 | no | pass |
| 80 | 870 | 51 / 95 / 121 ms | 170 / 205 ms | none sampled | 0 | 0.84 | 2.55 | no | pass |
| 90 (partial, 34 s) | 852 | 53 / 100 / 130 ms | 183 / 225.82 ms | none sampled | 0 | 0.80 | 2.40 | no | pass |

Generator check (`check-generator.sh`): 1: k6 mean 105% of 320% -> ok; 2: k6 mean 141% of 320% -> ok; 3: k6 mean 153% of 320% -> ok; 4: k6 mean 147% of 320% -> ok; 5: k6 mean 140% of 320% -> ok; 6: k6 mean 135% of 320% -> ok; 7: k6 mean 131% of 320% -> ok; 8: k6 mean 127% of 320% -> ok; 9: k6 mean 107% of 320% -> ok

Resources per measured window (mean over the step after the settle):

| Step | Postgres / Redis cores (`kubectl top`, mean) | Hikari active / pending (max) | Platform threads (max) | Game Host threads (max) | HTTP p95 / p99 (mean, ms) | WebSockets (max) | Sessions (max) |
|---|---|---|---|---|---|---|---|
| 10 | 1.26 / 0.62 | 5 / 0 | 103 | 64 | 26 / 35 | 20 | 10 |
| 20 | 1.65 / 0.57 | 5 / 0 | 115 | 67 | 12 / 17 | 40 | 19 |
| 30 | 2.06 / 0.55 | 10 / 29 | 123 | 76 | 23 / 34 | 60 | 27 |
| 40 | 2.08 / 0.51 | 10 / 40 | 135 | 83 | 36 / 52 | 80 | 34 |
| 50 | 2.09 / 0.48 | 10 / 49 | 147 | 96 | 49 / 73 | 100 | 37 |
| 60 | 2.08 / 0.46 | 10 / 59 | 164 | 100 | 64 / 88 | 119 | 50 |
| 70 | 2.09 / 0.45 | 10 / 81 | 176 | 95 | 85 / 114 | 160 | 54 |
| 80 | 2.09 / 0.44 | 10 / 91 | 187 | 95 | 102 / 140 | 177 | 62 |
| 90 | 2.11 / 0.43 | 10 / 89 | 191 | 112 | 113 / 169 | 180 | 63 |

## 5. Result

Ceiling (pairs): 80
First to break: DB pool
Evidence: `tb_room_join` is the only metric that crossed, and it grows steadily with the pair count (p95 15, 25, 44, 67, 88, 110, 149, 181 and 200 ms from 10 to 90 pairs) while moves, lobby events and game starts stay far inside their targets. From 30 pairs the 10-connection Hikari pool is fully busy (`hikari_active` max 10 of 10) and requests queue behind it: `hikari_pending` max 29 at 30 pairs, 49 at 50, 81 at 70 and 91 at 80 (0 throughout in Phase A), while Postgres sits at its 2-core limit (2.06 to 2.11 cores from 30 pairs on, `kubectl top`) and the platform at 2.4 to 3.1 of 4 cores. Game Host 0.8 to 1.1 of 4 cores from step 30, Redis 0.4 to 0.6 of 1, no restart, no 5xx, no generator-bound step (k6 105% to 153% of 320%).

Capacity statements:

- 500 concurrent sessions: **not reached.** Ceiling 80 pairs = 80 sessions (`sessions_active` max 62 at step 80, 67 at the abort); limiting factor `tb_room_join` latency behind the database pool.
- 5,000 WebSockets: **not reached; ceiling in sockets: 160** (2 x 80; 180 open when the run aborted). The ceiling is below 1,000 pairs, so the idle-socket run was not made (protocol, `IMP-M15-11` step 3); limiting factor as above. The remaining 4,840 sockets were not attempted.

`Ceiling (pairs)` is one integer: the last step all of whose thresholds passed and that is not
generator-bound, or `<n> (not reached)` when no step failed. `First to break` is exactly one of:
`Game Host CPU`, `Espresso contention`, `DB pool`, `Redis`, `platform threads`, `ingress / frontend nginx`,
`k6 itself`, `memory (OOM)`, `none`. A report for `start-rate` writes `Ceiling (games/s): <n>` instead.

## 6. Server side

Output of `snapshot.sh` (mean / max per segment; segment N starts N x 120 s after the launch, so each is offset by the setup time):

| metric (mean / max) | seg 1 (0s) | seg 2 (120s) | seg 3 (240s) | seg 4 (360s) | seg 5 (480s) | seg 6 (600s) | seg 7 (720s) | seg 8 (840s) | seg 9 (960s) |
|---|---|---|---|---|---|---|---|---|---|
| gamehost_cpu_cores | 2.678 / 3.792 | 2.817 / 3.001 | 1.202 / 1.822 | 0.996 / 1.039 | 0.936 / 0.96 | 0.901 / 0.943 | 0.881 / 0.908 | 0.848 / 0.873 | 0.814 / 0.837 |
| platform_cpu_cores | 2.716 / 3.766 | 2.765 / 2.939 | 3.056 / 3.109 | 2.936 / 3.013 | 2.793 / 2.857 | 2.706 / 2.808 | 2.644 / 2.713 | 2.569 / 2.628 | 2.448 / 2.512 |
| gamehost_heap_bytes | 222913277 / 297940400 | 300849356 / 402864640 | 292396889 / 377180712 | 312754940 / 397652144 | 284636365 / 339002992 | 296451011 / 372915528 | 285804763 / 401938680 | 260922062 / 371619256 | 292137616 / 382921312 |
| platform_heap_bytes | 221866615 / 289406976 | 186412029 / 248774224 | 186970894 / 268383472 | 215221477 / 279059848 | 206582743 / 269452720 | 171395517 / 240079248 | 199700096 / 260465984 | 258539781 / 300614016 | 265346916 / 312641024 |
| gamehost_threads | 58 / 64 | 64.125 / 67 | 72.625 / 76 | 81.125 / 83 | 90.75 / 96 | 96.125 / 100 | 93.375 / 95 | 94.125 / 95 | 112 / 112 |
| platform_threads | 91.625 / 103 | 111.5 / 115 | 121.125 / 123 | 132.375 / 135 | 145.25 / 147 | 158.25 / 164 | 169 / 176 | 182.875 / 187 | 190.5 / 191 |
| gamehost_gc_seconds_per_s | 0.006 / 0.011 | 0.004 / 0.004 | 0.004 / 0.004 | 0.004 / 0.005 | 0.004 / 0.004 | 0.004 / 0.004 | 0.003 / 0.004 | 0.004 / 0.004 | 0.003 / 0.004 |
| platform_gc_seconds_per_s | 0.024 / 0.058 | 0.005 / 0.006 | 0.006 / 0.006 | 0.006 / 0.006 | 0.006 / 0.006 | 0.006 / 0.007 | 0.006 / 0.007 | 0.006 / 0.007 | 0.006 / 0.006 |
| http_p95_seconds | 0.041 / 0.107 | 0.011 / 0.013 | 0.021 / 0.027 | 0.034 / 0.039 | 0.047 / 0.053 | 0.062 / 0.068 | 0.082 / 0.088 | 0.1 / 0.106 | 0.112 / 0.114 |
| http_p99_seconds | 0.052 / 0.121 | 0.016 / 0.018 | 0.031 / 0.038 | 0.049 / 0.055 | 0.07 / 0.076 | 0.086 / 0.094 | 0.111 / 0.12 | 0.138 / 0.151 | 0.166 / 0.169 |
| http_5xx_per_s | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| http_req_per_s | 84.021 / 111.339 | 132.864 / 144.992 | 164.067 / 173.831 | 163.163 / 168.423 | 160.961 / 164.262 | 157.167 / 160.456 | 148.773 / 157.155 | 139.776 / 142.021 | 138.289 / 142.683 |
| hikari_active | 1.75 / 5 | 4 / 7 | 7.125 / 10 | 9.75 / 10 | 9.875 / 10 | 10 / 10 | 10 / 10 | 10 / 10 | 10 / 10 |
| hikari_pending | 0 / 0 | 0 / 0 | 9.5 / 29 | 25.625 / 40 | 30.5 / 49 | 50.5 / 59 | 62.375 / 81 | 81.375 / 91 | 87.25 / 89 |
| ws_connections | 15 / 20 | 37.375 / 40 | 56.25 / 60 | 76.625 / 80 | 99 / 100 | 118.375 / 120 | 141.375 / 160 | 160.75 / 177 | 179 / 180 |
| rooms_active | 6.125 / 10 | 16.25 / 20 | 27.5 / 30 | 36.625 / 40 | 46.375 / 48 | 56.875 / 60 | 68.125 / 70 | 78.25 / 80 | 88 / 89 |
| sessions_active | 5.375 / 10 | 12.5 / 19 | 22.5 / 27 | 30.625 / 34 | 34.5 / 37 | 45.625 / 50 | 50.75 / 54 | 60 / 62 | 65 / 67 |
| up | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 |

| | At start | At end of the run (last sample) | After the run (snapshot) |
|---|---|---|---|
| Redis `used_memory` / keys | 1.07 MiB / 5 | 1.86 MiB / 699 (peak 761 keys, 1.82 MiB) | 1.77M / 674 |
| Redis `connected_clients` | n/a (sampled once, after the run) | n/a | 5 |

Pod restarts and `OOMKilled` (from `cluster.txt`): platform, Game Host and frontend 0 restarts; Postgres, Redis and the observability pods show 3 to 4 restarts, all from before this run; no `OOMKilled`.

Missing metrics: http_5xx_per_s (no 5xx request ever happened; Micrometer creates the series on first use)

Redis held 674 keys at the snapshot (699 at the last sample, peak 761): the abort stops k6 with 89 rooms still open and the keys of those rooms are still there, about 7.6 per room. Whether they expire was not checked in this run; the `parallelism` run, which finishes its games, left 6.

Platform thread census at the end of the run (`census-snapshot.txt`): 191 threads, of which 180 `http-nio` workers, 16 + 16 STOMP channel threads and 5 Lettuce loops. Game Host 112 threads (95 at the previous segment).

Postgres `pg_stat_statements` over the run (about 122,400 games including the warm-up window), by total execution time: the team occupancy query 122,459 calls, 3.68 ms mean, 450.7 s in total; `select t.team_id ... occupied` 49,062 calls, 3.69 ms, 180.8 s; `select room_id, grace_reservation_id ... where user_id = $1 and left_at is null` 49,063 calls, 3.31 ms, 162.4 s (no row returned); the room lookup with game version 24,531 calls, 5.17 ms, 126.8 s. By calls, the two participant listings run 9.6 times per game (1,179,342 each). Postgres time on these four statements is about 920 s over the 1,000 s of the load.

## 7. Errors by code

| Code | Expected | Count |
|---|---|---|
| none | n/a | 0 |

## 8. Findings

- **Finding 3 (`tb_room_join` is the first threshold to fail) persists, with a higher ceiling.** The abort moves from step 80 to step 90 and the ceiling from 70 to 80 pairs, and the crossing is smaller: p95 about 200 ms at 90 pairs against 311 ms at 80 in Phase A. The cause named in Phase A (Postgres or platform CPU, not separable) is now separable in part: the pool is saturated (`hikari_active` 10 of 10, `hikari_pending` up to 91, none in Phase A) while Postgres is at its 2-core limit. Not checked: which of the two (CPU or connection count) is the bottleneck when the other is raised.
- **Finding 1 shows up here too.** Moves/s peaks at 1,067 at 30 pairs (931 at 20 in Phase A), then falls to 870 at 80 (664 partial in Phase A) while the Game Host uses 0.8 to 1.1 cores of 4.
- **Pool queue is new since Phase A.** `hikari_pending` was 0 in Phase A for the whole run except one segment; it is 29 to 91 here from 30 pairs. The per-game statement counts above (about 9.6 participant listings and 5 team occupancy queries per game) are the load; whether M16-07/08/09 (room ownership, reconciliation) added statements per move or per join was not measured.
- **Finding 4 is resolved in this run.** 0 errors of any code in 122,383 games and 934,387 moves.
- **Finding 10 is resolved here.** `ws_connecting` max 160 ms and `http_req_duration` max 314 ms (10.0 s in Phase A); no stall.
- **The abort comes from a transient.** `abortOnFail` evaluates the running percentile, and at step 90 the final p95 is 199.9 ms, under the target. The ceiling follows the protocol (last step that fully passed), so 80 pairs is a lower bound, as it was in Phase A.
- Platform threads 191 at the abort (137 in Phase A at 80 pairs), 180 of them Tomcat workers; Game Host threads 112 (52 in Phase A). No restart, no `OOMKilled`, no 5xx, no generator-bound step.

## 9. Phase A vs M16

| Step (pairs) | 10 | 20 | 30 | 40 | 50 | 60 | 70 | 80 | 90 |
|---|---|---|---|---|---|---|---|---|---|
| Moves/s, Phase A | 794 | 931 | 841 | 909 | 812 | 873 | 856 | 664 (aborted) | n/a |
| Moves/s, M16 | 667 | 926 | 1,067 | 1,032 | 1,012 | 987 | 907 | 870 | 852 (aborted, 34 s) |
| `tb_move_rtt` p95 ms, Phase A | 9 | 17 | 26 | 36 | 46 | 58 | 70 | 81 | n/a |
| `tb_move_rtt` p95 ms, M16 | 14 | 22 | 30 | 42 | 53 | 64 | 80 | 95 | 100 |
| `tb_room_join` p95 ms, M16 | 15 | 25 | 44 | 67 | 88 | 110 | 149 | 181 | 200 |
| `hikari_pending` max, M16 | 0 | 0 | 29 | 40 | 49 | 59 | 81 | 91 | 89 |

| | Phase A | M16 |
|---|---|---|
| Ceiling (pairs) | 70 | 80 |
| First to break | platform threads | DB pool |
| Aborted on | `tb_room_join{step:80}` p95 311 ms | `tb_room_join{step:90}` p95 crossed 200 ms (199.9 ms at the end) |
| Concurrent sessions at the ceiling | 58 to 63 | 62 to 67 |
| Platform threads, max | 138 | 191 |
| Game Host threads, max | 56 | 112 |
| `hikari_pending`, max | 9 | 91 |
| Errors | 0 | 0 |

Phase A rows come from `2026-10-18-ramp-to-break.md`; its step 80 is the aborted step and its `hikari_pending` maximum is the one segment (step 60) the report names.

## 10. Constants

- This is a single-node, laptop ceiling: Docker Desktop Kubernetes on one WSL2 VM shared with the load generator. It is the ceiling of this machine, not of the platform.
- Latency is measured per request from a closed-loop client at the configured think time, so coordinated omission applies: when the system slows, the client issues fewer requests and the percentiles understate the delay a constant-rate client would see. `start-rate` is open-loop.
- One step is generator-bound when the k6 process averages more than 80% of its pinned cores after the settle window; such a step never counts as the platform's breaking point.
- The first `SETTLE_SECONDS` of every step are excluded from that step's thresholds.
- A crossed threshold aborts the run no earlier than 30 s after the test start (`delayAbortEval` counts from the test start, not from the step), so a step's first samples after its settle window can trip a one-sample percentile.
