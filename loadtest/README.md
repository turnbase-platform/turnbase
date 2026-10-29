# Load and scalability tests (Phase A)

k6 scripts and shell tooling that drive real Tic-Tac-Toe player pairs (one VU = two users, two STOMP
sockets) against the Helm install on Docker Desktop Kubernetes, to find where a single-node, laptop
install breaks. Design: [`docs/specs/deployment/load-testing.md`](../docs/specs/deployment/load-testing.md);
results: [`reports/SUMMARY.md`](reports/SUMMARY.md). Every report states
that the result is a single-node, laptop ceiling.

## Prerequisites

`kubectl` (context `docker-desktop`, Kubernetes enabled, ingress-nginx on port 80), `helm`, `k6`
(v2.2.0), `jq`, `curl`, `taskset`, `openssl`, `docker`. The three images `turnbase/{platform,game-host,
frontend}:dev` built locally, and the Tic-Tac-Toe seed bundle in `turnbase-game-tictactoe/target/seed/`.

## Run procedure

1. Build the images (`docker build -t turnbase/platform:dev turnbase-platform`, likewise
   `turnbase/game-host:dev` and `turnbase/frontend:dev`; `./mvnw clean package -DskipTests` first when
   `target/` is stale; always `clean`: a second `package` over an already repackaged jar shades the Boot jar
   and leaves the guest-bridge jar without its classes, and every game start then fails).
2. `bash loadtest/preflight.sh --cluster-only`, then `bash loadtest/install.sh`.
3. `bash loadtest/preflight.sh` (must print `PREFLIGHT OK`).
4. Provision the users: `k6 run loadtest/scenarios/provision.js`. A second run reports 0 created.
5. Run a scenario: `bash loadtest/run.sh start <scenario> [VAR=value …]` returns at once with `RUN_DIR=…`;
   `bash loadtest/run.sh wait <run-dir> 280` blocks up to 280 s (exit 124 = still running, repeat).
6. Collect: `steps-table.sh`, `check-generator.sh` and `snapshot.sh` (see *Scripts*).
7. Write the report from the template under `loadtest/reports/`.
8. `bash loadtest/reset.sh`, then provision again before the next run.

## Scripts

| Script | What it does |
|---|---|
| `preflight.sh [--cluster-only]` | Checks context, node, tools, images, Helm release, pods and the public URL. Prints `PREFLIGHT FAIL: <what>` per failure, then `PREFLIGHT OK` or exit 1. Check 7 requests `$BASE_URL/api/games`; any HTTP status counts |
| `install.sh [--default-limits]` | `helm upgrade --install turnbase` with `values-local.yaml`, the secrets file and `helm/values-loadtest.yaml`. Generates a git-ignored dummy `values-local.secrets.yaml` when missing. Removes the platform and Game Host pods first (a rolling update would need a second 4-CPU platform pod, which the VM cannot schedule), then the upgrade starts them again |
| `reset.sh` | Scales frontend, platform and Game Host to zero, drops and recreates the `public` schema, `FLUSHALL`s Redis, scales back (platform first). Prometheus keeps its history. Then `RESET OK`. Users must be provisioned again |
| `scenarios/provision.js` | Creates `lt-00000`…`lt-01999` (log in, register if absent, log in again). Env `USERS` changes the count |

### Install details that differ from the plan

- The seed bundle is passed as `--set platform.seed.bundlesHostPath=…` (the chart's key). That path is
  in the Kubernetes node: under WSL 2 it must be the `/run/desktop/mnt/host/c/...` form of a Windows
  directory. `install.sh` copies the bundle to `C:\Users\<you>\turnbase-seed` and uses that, or takes
  `SEED_HOST_PATH` from the environment.
- The chart's key names were as the plan expected (`platform.autoscaling.enabled`,
  `observability.prometheus.remoteWriteReceiver`, `extraEnv`); the Postgres and Redis `resources`
  values were added to the chart by this item.
- The users table is `app_user`; after `reset.sh`, `SELECT count(*) FROM app_user WHERE username LIKE
  'lt-%'` returns 0 and Redis `DBSIZE` is 5 (the seed's: the Game Host lease and the platform's startup
  keys).

## Scenarios

| Scenario | What it does |
|---|---|
| `scenarios/scale-in.js` | Reconnecting pairs for the scale-in test (`IMP-M18-10`); run through `test/scale-in-midgame.sh`, which scales the Platform 3 → 2 and deletes a pod mid-game and asserts 0 games lost |
| `scenarios/smoke.js` | One pair (`lt-00000`, `lt-00001`), three games: two in one room (the second is the rematch), then one in a fresh room. Exits 0 with `tb_errors` at 0, `tb_games_completed` at 3 and both a `cold:true` and a `cold:false` `tb_game_start` sample. About 10 s. `THINK_MIN_MS=5000 THINK_MAX_MS=5000` stretches it to about 90 s of idle sockets, the heart-beat proof |
| `test/selftest.js` | `k6 run loadtest/test/selftest.js`: STOMP codec and board helpers, no cluster needed |

### The pair loop (`lib/pair.js`, `lib/stomp.js`)

Differences from the plan, found against the live stack:

- **`GAME_SYNC.view.turn` is a user id**, not a mark. The mover is the player whose `init.self.id`
  equals `turn`; `payload.next` of a `move` event is a user id too. `readView(f)` is the one function
  that knows the field names (`init.self.id`, `view.yourMark`, `view.board`, `view.turn`). The empty
  cell is `""`, read from the first board, not hard-coded.
- **Sockets live for one `pairSession`, not for the VU.** An open WebSocket and its heart-beat timer
  keep a k6 iteration from ever ending (the smoke ran to its `maxDuration` and was interrupted), so
  `pairSession` closes both sockets when it leaves the room and the next one reconnects. Each
  iteration therefore opens two sockets, which `ws_connecting` measures.
- Failures: a timeout is reported under the code of an error frame on `/user/queue/errors` when one is
  buffered, otherwise under its own code (`start_timeout`, `move_timeout`, `ws_closed`, …). `-e DEBUG=1`
  logs the first failure's message and stack.
- `tb_game_start` is tagged `cold=true` only for a pair's first game within `COLD_WINDOW_MS` of the
  scenario start. A rerun against a warm Game Host still tags it `cold:true`, because the tag is the
  harness's, not the Game Host's; the first start after `reset.sh` is the really cold one.
- **The room subscriptions are confirmed before anyone acts.** `SUBSCRIBE` carries a `receipt` header and the
  platform answers with a `RECEIPT` once the broker has registered it (`room-websocket.md` § Snapshot
  Delivery); `stomp.js` `subscribeConfirmed` waits for it. Without it the guest's first `TOGGLE_READY` could be
  broadcast before the host's subscription existed (`ready_timeout`, finding 4). A missing receipt is a
  `subscribe_timeout`.
- **Clean-room check.** The participants table is `room_participant` (`user_id`, `left_at`) and the user
  table is `app_user` (key `user_id`):
  `SELECT count(*) FROM room_participant rp JOIN app_user u ON u.user_id = rp.user_id WHERE u.username LIKE 'lt-%' AND rp.left_at IS NULL`
  returns 0 after every smoke run. The stale-membership-on-first-iteration case (a VU interrupted
  mid-room) is not exercised by the smoke; `reset.sh` covers abort paths.

## Overlay and resources

`helm/values-loadtest.yaml` fixes everything a run depends on: `SPRING_PROFILES_ACTIVE=local,loadtest`
(the throttling mechanisms are switched off, which only the `loadtest` profile permits), one platform
replica without autoscaling, one Game Host replica, `-XX:MaxRAMPercentage=70` on both JVMs, and
requests equal to limits:

| Component | CPU | Memory |
|---|---|---|
| Platform | 4 | 3 GiB |
| Game Host | 2 (one replica; 4 before Phase B) | 4 GiB |
| Postgres | 4 (2 before Phase B) | 2 GiB |
| Redis | 1 | 512 MiB |

The memory limits sum to 9.5 GiB. The Docker Desktop VM (15.21 GiB on the reference machine) also runs
k6, the frontend, ingress and the observability stack, so larger limits left pods unschedulable or
OOM-killed the node. A run item never edits the overlay; the M16 items edit it only where their sections say so, and mirror the edit in `values-default-limits.yaml` (`test/check-overlays.sh`). It also passes `postgres.extraArgs` (`-c shared_preload_libraries=pg_stat_statements -c log_checkpoints=on`); `redis.extraArgs` stays empty.
The platform JVM also logs GC and safepoints to stdout (`JDK_JAVA_OPTIONS` `-Xlog:gc*,safepoint:stdout:utctime,uptime`, `IMP-M16-12`), so `kubectl logs deploy/turnbase-platform` holds every pause with its time. If the VM has fewer than 12 CPUs, halve every
`cpu` value and record it in the report.

## Environment variables (`lib/config.js`)

| Variable | Default | Meaning |
|---|---|---|
| `BASE_URL` | `http://turnbase.localhost` | Platform origin (HTTP, WebSocket and `Origin` header) |
| `HOST_IP` | empty | Maps the host name to an IP when `::1` does not work (see below) |
| `GAME_ID` | `2cc66e36-52e6-4144-9a10-09d09c982ce4` | The seeded Tic-Tac-Toe |
| `USER_PREFIX` / `PASSWORD` | `lt-` / `Loadtest-Passw0rd-2026` | Users `lt-00000`… |
| `THINK_MIN_MS` / `THINK_MAX_MS` | 0 / 0 (250 / 250 in `default-limits`) | Think time before each move. `default-limits` defaults both to 250 when the environment does not set them, so that a correct client never trips the WebSocket action bucket (5 per second, burst 10), which stays the product limit |
| `FRESH_ROOM_EVERY` | 5 | Games per room before the pair leaves and creates a new one |
| `STEP_SECONDS` / `SETTLE_SECONDS` | 120 / 20 | Length of a stepped scenario's step and the unmeasured settle at its start |
| `PAIRS` | 1 | `smoke.js` only: concurrent pairs, one VU each (`per-vu-iterations`, one iteration); `setup()` logs in `2 * PAIRS` users and the threshold is `tb_games_completed count >= 3 * PAIRS`. The other scenarios read their own `PAIRS` |
| `THRESHOLD_SCALE` | 1 | Multiplies every threshold (a smoke check sets 0.001) |
| `COLD_WINDOW_MS` | 30000 | A game start in the first window after a restart is tagged `cold=true` |
| `START_TIMEOUT_MS` / `STEP_TIMEOUT_MS` | 120000 / 10000 | Waits for `GAME_STARTED` and for one move's echo |
| `ERROR_BACKOFF_MS` | 1000 | Pause after a failed iteration |
| `LOGIN_PARALLEL` | 8 (2 in `default-limits`) | Batch size of the pre-login in `setup()` |
| `USERS` | 2000 | Users `provision.js` creates, and the pair cap of every scenario: `lib/pair.js` allows `floor(USERS / 2)` pairs, so a run of more than 1,000 pairs sets the same `USERS` for `provision.js` and for the scenario |

`turnbase.localhost` resolves to `::1` on the WSL host. If k6 cannot connect, set `HOST_IP=127.0.0.1`.
The WSL resolver does not answer the IPv4 query for `turnbase.localhost`, so a k6 lookup takes about 10 s. The scenarios therefore set `dns.ttl` to `inf` (`lib/config.js` `dnsOption`): k6's default of 5 minutes stalled every VU for 10 s at each expiry (`IMP-M16-12`, `reports/2026-10-21-m16-stall.md`). A new script must use `baseOptions` or set `dns: dnsOption`.
(It was not needed on the reference machine for HTTP; `provision.js` ran without it.)

## Generator and VM limits

The Docker Desktop VM is the WSL 2 VM and is shared with k6, so k6 cannot get dedicated cores from a
`.wslconfig`. k6 is pinned with `taskset` to the last 4 CPUs (the last 2 on a VM with fewer than 12);
a step where k6 uses more than about 80% of its CPU is flagged generator-bound in the report.

The `.wslconfig` recommendation is about memory only, so the VM neither starves nor swaps:

```ini
[wsl2]
memory=15GB
```

Record the file's content, or "absent (VM defaults)", in every report, together with `docker info`.

## Scripts added by IMP-M15-09

| Script | What it does |
|---|---|
| `run.sh start <scenario> [VAR=value …]` | Creates `results/<stamp>-<scenario>/`, writes `params.txt`, runs the preflight, captures `cluster.txt` (VM size, nodes, Helm values, image IDs, commits, `.wslconfig`, k6 version), zeroes the cumulative counters (`pg_stat_statements_reset()`, Redis `CONFIG RESETSTAT`) and sets Redis `latency-monitor-threshold` to 100 ms so that `LATENCY LATEST` records, starts the Redis sampler, keeps a Prometheus port-forward on `:9090`, then starts k6 in the background pinned with `taskset` to the last 4 CPUs (2 on a VM with fewer than 12) and with the file-descriptor limit raised to the hard limit. Prints `RUN_DIR=…` and returns |
| `run.sh wait <run-dir> [seconds=280]` | Polls for `exit-code` every 5 s; exit 0 and the code when done, 124 when the budget ran out. Exit code 99 (a threshold crossed) is a finished run, not a failure |
| `sample-generator.sh <run-dir>` | Started by `run.sh`. Every 5 s appends `epoch,k6_cpu_pct,vm_cpu_pct,load1` to `samples.csv` (k6 as a share of one core: 4 cores reach 400) and, every third sample, `epoch,pod,cpu_m,mem_mi` rows from `kubectl top pods` to `pods.csv` |
| `check-generator.sh <samples.csv> <start_epoch> <segment_seconds> <k6_cores> [settle=20]` | One line per segment: `k6 mean X% of Y% -> ok` or `-> generator-bound` (Y is 80% of the pinned cores). Pass `scenario.epoch` as the start |
| `steps-table.sh <summary.json>` | Writes `steps.csv` (`segment,metric,count,p95,p99,rate,pass`; `rate` is `tb_op_failed` only) from the step-tagged metrics of k6's `--summary-export`; `pass` is false when any threshold of that metric failed |
| `snapshot.sh <run-dir> [segment_seconds]` | Runs the plan's PromQL list over the run into `prom/`, prints a mean / max table per segment, errors by code, and appends pod restarts, `OOMKilled`, Redis `used_memory_human` / `connected_clients` and the Postgres `pg_stat_statements` top 20 (by `calls`, by `total_exec_time`; `pg_stat_statements unavailable` when the extension is missing) to `cluster.txt`. It then runs `census.sh` with the label `snapshot`. A series with no samples prints `n/a` and is listed under `Missing metrics:` (for `http_5xx_per_s` that means no 5xx request ever happened: Micrometer creates the series on first use) |
| `cpu-per-move.sh <run-dir>` | From `prom/platform_cpu_cores.json`, `prom/gamehost_cpu_cores.json` (`snapshot.sh`) and the `tb_move_rtt` count in `steps.csv` (`steps-table.sh`): moves, moves per second, mean platform and Game Host cores in `[scenario.epoch + SETTLE, scenario.epoch + STEP]` and `platform_cpu_ms_per_move` for a one-step `parallelism` run (`IMP-M16-13`). |
| `census.sh <run-dir> <label>` | Writes `census-<label>.txt`: thread counts by name prefix (digits stripped, with the total) for the platform and for the Game Host JVM, from `/proc/<pid>/task/*/comm`; the Game Host's `jcmd <pid> GC.class_histogram` top 30; Redis `DBSIZE`, `INFO keyspace`, `used_memory` and the `keys` / `scan` lines of `INFO commandstats`. A section that cannot be collected prints `<section> unavailable: <reason>`. `snapshot.sh` calls it with `snapshot`; `IMP-M16-10` and `15` use `before`, `peak` and `after` |
| `redis-sampler.sh <run-dir>` | Started by `run.sh start`. Every 30 s appends `timestamp,dbsize,used_memory` (UTC) to `redis.csv` until `exit-code` exists |
| `boot-wedge-repro.sh <cycles> <pairs> [--dry-run]` | `IMP-M16-03`. Each cycle deletes the Game Host pod, waits for a differently named pod to be Ready (300 s; a timeout is a `ready_timeout` row and the next cycle goes on), runs `run.sh start smoke PAIRS=<pairs>` so that the first real guest boot happens through the platform, saves the new pod's logs (and `--previous` when the container restarted) and counts both wedge modes in them: mode A, the supervisor's `killing it` lines, and mode B, the `BootWatchdog` line `Guest boot wedged`. Writes `results/<stamp>-boot-wedge/boot-wedge.csv` (`cycle,pairs,pod,mode_a,mode_b,smoke_exit,seconds_to_first_game`), the logs, `smoke-dirs.txt` and `summary.txt`. `<pairs>` is 1 for the baseline and 4 for contention. `--dry-run` prints one cycle's commands. About 40 s a cycle |
| `check-report.sh <report.md>` | Exit 1 while a `FILL` or a required heading is left; `REPORT COMPLETE` otherwise |
| `reports/TEMPLATE.md` | The report every run fills in (`load-testing.md` §8) |
| `helm/values-default-limits.yaml` | `values-loadtest.yaml` without the `loadtest` profile and the remote-write receiver; `install.sh --default-limits` applies it |
| `test/check-generator-selftest.sh`, `test/check-overlays.sh` | Selftests without a cluster: the generator check on a synthetic file, and the overlay equality |

A run directory holds `k6.log`, `summary.json`, `samples.csv`, `pods.csv`, `redis.csv`, `census-*.txt`, `params.txt`, `cluster.txt`,
`start.epoch` (launch), `scenario.epoch` (setup finished, read from the `TB_SETUP_DONE` log line: the first
step starts here), `end.epoch`, `exit-code`, `steps.csv` and `prom/`. There is no per-sample JSON stream: a
30-minute 1,000-pair run emits hundreds of millions of samples, so the raw output is `summary.json` plus the
Prometheus series k6 pushes by remote write (`k6_tb_*`). The `summary.json` percentiles are authoritative.

**Process ids inside the pods.** The platform JVM is PID 1 and its image has no `jcmd` (only `java`, `jfr`,
`jrunscript`, `jwebserver`, `keytool`, `rmiregistry`), so platform threads come from `/proc` alone. In the Game
Host image PID 1 and PID 8 are `supervise.sh` and the JVM is the process whose `/proc/<pid>/comm` is `java`
(PID 7 observed; `/tmp/jvm.pid` once `IMP-M16-02` writes it). `jcmd` exists there at `/usr/bin/jcmd`, but `kill`
only as a shell builtin, so `jcmd 1` fails and `jcmd <jvm pid>` works.

### Scenarios (minimum size: each runs for at most two minutes)

| Scenario | Shape | Minimum parameters |
|---|---|---|
| `parallelism` | `ramping-vus`, steps of 1, 2, 4 … 256 pairs, thresholds only create the per-step sub-metrics | `STEP_SECONDS=20 SETTLE_SECONDS=5 LEVELS=1,2` |
| `ramp-to-break` | `ramping-vus`, +`STEP_PAIRS` per step, every threshold aborts (exit 99) | `STEP_SECONDS=20 SETTLE_SECONDS=5 START_PAIRS=2 STEP_PAIRS=2 MAX_PAIRS=6` |
| `start-rate` | `ramping-arrival-rate`, 1 … 32 games/s, one game per iteration | `STEP_SECONDS=20 SETTLE_SECONDS=5 RATES=1,2` |
| `soak` | `ramping-vus` to `PAIRS`, hold, down in half the ramp time; `PAIRS` required | `PAIRS=2 HOLD_MINUTES=1 RAMP_SECONDS=10` |
| `up-down` | up, hold, down (`RAMP_MINUTES`, `HOLD_MINUTES`), then `IDLE_MINUTES` of nothing (a sleeping VU; k6 drops a trailing zero-VU stage); `PAIRS` required | `PAIRS=2 RAMP_MINUTES=0.25 HOLD_MINUTES=0.25` |
| `default-limits` | `constant-vus` with every limiter on, think time 250 ms by default; `RATE_LIMIT_EXCEEDED` is expected, anything else is not | `VUS=4 DURATION=60s` after `install.sh --default-limits` |
| `contexts` | `constant-vus`, `PAIRS` (50) for `DURATION` (5m); pair `i` plays `CONTEXT_IDS[i % n]`, so the Game Host holds one Espresso context per id. Needs the copies below; no thresholds abort | `PAIRS=4 DURATION=60s CONTEXT_IDS=<four ids>` |

`THRESHOLD_SCALE=0.001` makes every threshold impossible: `ramp-to-break` then aborts within about 30 s and
exits 99. Samples carry `step:<tag>` (the first `SETTLE_SECONDS` of a step are `step:warmup`) and thresholds
select one step each, because k6 thresholds are global and a cumulative percentile would make "the ceiling"
meaningless. A crossed threshold ends the run no earlier than 30 s after the test start (`delayAbortEval`
counts from the start, not from the step), so a step's first post-settle samples can trip a one-sample
percentile.

`default-limits` flow: reset, `install.sh`, provision, `install.sh --default-limits`, preflight, run, then
`install.sh` and preflight again. The DB survives the upgrade.

### `contexts`: the bundle copies

`lib/bundles.sh <count>` writes `<count>` copies of the seed bundle to `results/contexts-bundles/`, each named
`<fresh UUID>.zip` (the stem is the game id), with the manifest `title` suffixed ` <k>` and `version` `1.0.<k>`,
and prints the ids comma separated. Route used: the seeder directory (the official path, `bundle-format.md` §1.1;
the platform accepted all four copies and logged `Seeded official game <id> version 1.0.<k>`). Copy the zips into
the seed directory (`C:\Users\<you>\turnbase-seed`), `bash loadtest/reset.sh` (the seeder runs on the platform's
start), provision, run the scenario, then **delete the copies and reset again**: they would otherwise be in the
catalog of every later run.

Proof of spread, from the minimum run (`PAIRS=4 DURATION=60s`, exit 0, `tb_errors` 0, 2,105 games in 60 s):

```bash
kubectl logs deploy/turnbase-gamehost | grep 'Game context created'
```

printed four lines, one per copy, from `GameContextManager`: `gameId=4a2ba2df-… gameVersion=1.0.3`,
`gameId=e858badf-… gameVersion=1.0.1`, `gameId=2725900a-… gameVersion=1.0.2`, `gameId=6eef12b7-… gameVersion=1.0.4`.
(The Redis session keys are not the proof; the Game Host's own context log is.)
