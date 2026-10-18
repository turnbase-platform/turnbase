# Load and scalability tests (Phase A)

k6 scripts and shell tooling that drive real Tic-Tac-Toe player pairs (one VU = two users, two STOMP
sockets) against the Helm install on Docker Desktop Kubernetes, to find where a single-node, laptop
install breaks. Design: [`docs/specs/deployment/load-testing.md`](../docs/specs/deployment/load-testing.md);
test definition and run protocol: `docs/implementation/m15-test-definition-plan.md`. Every report states
that the result is a single-node, laptop ceiling.

## Prerequisites

`kubectl` (context `docker-desktop`, Kubernetes enabled, ingress-nginx on port 80), `helm`, `k6`
(v2.2.0), `jq`, `curl`, `taskset`, `openssl`, `docker`. The three images `turnbase/{platform,game-host,
frontend}:dev` built locally, and the Tic-Tac-Toe seed bundle in `turnbase-game-tictactoe/target/seed/`.

## Run procedure

1. Build the images (`docker build -t turnbase/platform:dev turnbase-platform`, likewise
   `turnbase/game-host:dev` and `turnbase/frontend:dev`; `./mvnw package -DskipTests` first when
   `target/` is stale).
2. `bash loadtest/preflight.sh --cluster-only`, then `bash loadtest/install.sh`.
3. `bash loadtest/preflight.sh` (must print `PREFLIGHT OK`).
4. Provision the users: `k6 run loadtest/scenarios/provision.js`. A second run reports 0 created.
5. Run a scenario: `loadtest/run.sh start <scenario>` (background) and `loadtest/run.sh wait`
   (added by IMP-M15-09).
6. `loadtest/snapshot.sh` collects Prometheus and cluster state (IMP-M15-09).
7. Write the report from the template under `loadtest/reports/`.
8. `bash loadtest/reset.sh`, then provision again before the next run.

## Scripts

| Script | What it does |
|---|---|
| `preflight.sh [--cluster-only]` | Checks context, node, tools, images, Helm release, pods and the public URL. Prints `PREFLIGHT FAIL: <what>` per failure, then `PREFLIGHT OK` or exit 1. Check 7 requests `$BASE_URL/api/games`; any HTTP status counts |
| `install.sh [--default-limits]` | `helm upgrade --install turnbase` with `values-local.yaml`, the secrets file and `helm/values-loadtest.yaml`. Generates a git-ignored dummy `values-local.secrets.yaml` when missing. Never restarts pods |
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
| Game Host | 4 | 4 GiB |
| Postgres | 2 | 1 GiB |
| Redis | 1 | 512 MiB |

The memory limits sum to 8.5 GiB. The Docker Desktop VM (15.21 GiB on the reference machine) also runs
k6, the frontend, ingress and the observability stack, so larger limits left pods unschedulable or
OOM-killed the node. A run item never edits the overlay. If the VM has fewer than 12 CPUs, halve every
`cpu` value and record it in the report.

## Environment variables (`lib/config.js`)

| Variable | Default | Meaning |
|---|---|---|
| `BASE_URL` | `http://turnbase.localhost` | Platform origin (HTTP, WebSocket and `Origin` header) |
| `HOST_IP` | empty | Maps the host name to an IP when `::1` does not work (see below) |
| `GAME_ID` | `2cc66e36-52e6-4144-9a10-09d09c982ce4` | The seeded Tic-Tac-Toe |
| `USER_PREFIX` / `PASSWORD` | `lt-` / `Loadtest-Passw0rd-2026` | Users `lt-00000`… |
| `THINK_MIN_MS` / `THINK_MAX_MS` | 0 / 0 | Think time before each move |
| `FRESH_ROOM_EVERY` | 5 | Games per room before the pair leaves and creates a new one |
| `STEP_SECONDS` / `SETTLE_SECONDS` | 120 / 20 | Length of a stepped scenario's step and the unmeasured settle at its start |
| `THRESHOLD_SCALE` | 1 | Multiplies every threshold (a smoke check sets 0.001) |
| `COLD_WINDOW_MS` | 30000 | A game start in the first window after a restart is tagged `cold=true` |
| `START_TIMEOUT_MS` / `STEP_TIMEOUT_MS` | 120000 / 10000 | Waits for `GAME_STARTED` and for one move's echo |
| `ERROR_BACKOFF_MS` | 1000 | Pause after a failed iteration |
| `LOGIN_PARALLEL` | 8 | Batch size of the pre-login in `setup()` |
| `USERS` | 2000 | `provision.js` only |

`turnbase.localhost` resolves to `::1` on the WSL host. If k6 cannot connect, set `HOST_IP=127.0.0.1`.
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

## Scripts added by Task 9

(Filled in by `IMP-M15-09`: `run.sh`, `snapshot.sh`, `check-generator.sh`, the stepper and thresholds.)
