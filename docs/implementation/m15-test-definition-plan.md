# M15 Test Definition and Run Plan

> **Working file, deleted once spent** (CLAUDE.md, *Working files are deleted once spent*). It carries
> `IMP-M15-07…10` (the k6 harness, its scenarios and the report template) and the run protocol for
> `IMP-M15-11…13` (the Phase A measurements). The registry's *Done when* clauses stay authoritative;
> this file only orders the steps and fixes the decisions the registry leaves open. Steps use
> checkbox (`- [ ]`) syntax. Every decision below is **fixed**: where it reads "is", do not re-open it.

**Goal:** a committed k6 harness (`loadtest/`) that drives real Tic-Tac-Toe player pairs through room
creation, game start and play against the Helm install on Docker Desktop Kubernetes, plus the
protocol by which unattended sessions run it and commit reports saying where the system breaks.

**Architecture:** one VU is one player pair (users `lt-{2i}` and `lt-{2i+1}`, one STOMP socket each).
A small STOMP 1.2 client over `k6/websockets` (Task 8), a pair game loop (Task 8), nine scenarios on
top of it (Tasks 9 and 10), and shell scripts for install, reset, preflight, run, sampling and
snapshotting (Tasks 7 and 9). Pass or fail is evaluated **per step** by tagging every sample with the
step it was taken in and generating one threshold set per step.

**Tech Stack:** k6 v2.2.0 (`k6/websockets`, `k6/http`, `k6/execution`), bash, jq, curl, taskset, Helm 3,
kubectl, Docker Desktop Kubernetes (WSL2). No npm dependency, no remote k6 import (jslib.k6.io is not
used).

**Spec:** [`docs/specs/deployment/load-testing.md`](../specs/deployment/load-testing.md) §3.5, §3.6,
§4 (A1, A2, A3), §5, §6, §8, §12, §13.

**Depends on:** `IMP-M15-06` (the chart runs the Game Host, `extraEnv`, `remoteWriteReceiver`, the
`loadtest` profile). Dependency graph of the later items: `IMP-M15-12` depends on 10 and 11, `IMP-M15-13` on 11 and 12.

---

## Global Constraints

- **Repository.** Everything lands in the umbrella repository under `loadtest/`. The single exception is
  Task 7, Step 3: the chart gains `postgres.resources` and `redis.resources` in `turnbase-platform`
  (the chart has no such values today; `grep -n resources` over the Postgres and Redis StatefulSets
  returns nothing). That is a separate branch in `turnbase-platform`, merged `--ff-only`, pushed, and its
  ref bumped in the umbrella. Task 7 corrects the `Repo` field of `IMP-M15-07` in `registry.md` to say so.
- **Measurement items touch no product code.** No file under `turnbase-platform/`, `turnbase-game-host/`,
  `turnbase-frontend/`, `turnbase-sdk/` or `turnbase-common/` changes in Tasks 8 to 10 or in any run item.
- **Branches.** One branch per task in the umbrella, `feat/m15-07-loadtest-scaffold`,
  `feat/m15-08-k6-client`, `feat/m15-09-scenarios`, `feat/m15-10-contexts`; merged `--ff-only` into
  `master` and deleted, locally and on the remote, in the same session. No pull requests (ADR-0012).
  Run items use `docs/m15-<n>-runs`. Commits are Conventional Commits (`conventions.md` §4):
  `feat(loadtest): …` for harness, `docs(loadtest): …` for reports.
- **No CI exists for the umbrella** (`work-item` skill, *Umbrella-only items*). `DONE` means the *Done
  when* clause holds, `python3 scripts/check-corpus.py` prints `clean` and `master` is pushed. Do not
  `gh run watch`. The one chart commit in `turnbase-platform` follows the session's CI policy paragraph.
- **Scripts.** `bash`, `set -euo pipefail`, no external tool beyond `kubectl helm k6 jq curl taskset awk
  openssl`. Every script starts with a comment saying what it does and its arguments. `bash -n` passes.
- **Long commands.** A foreground Bash call is capped at ten minutes and the loop's stall watchdog
  kills a session after fifteen minutes without output. **Every k6 run expected to last more than eight
  minutes is started with `loadtest/run.sh start` (background) and polled with `loadtest/run.sh wait`
  (blocks at most 280 s).** Emit a `LOOP_PHASE: testing <scenario> <elapsed>` line after every poll. A
  `wait` that returns 124 means "still running": poll again. Never end the turn to "check back".
- **Secrets.** `turnbase-platform/deploy/helm/turnbase/values-local.secrets.yaml` is git-ignored. If it
  is missing, `loadtest/install.sh` generates it with random dummy values (Task 7, Step 5). That is not
  a blocker. A cluster that is not running **is** an external blocker (see *Blocked* below).
- **Blocked.** Report `LOOP_STATUS: BLOCKED` only after re-running the failing check live
  (`kubectl get nodes`, `docker info`) and it still fails. Name the command. A missing image is built,
  not a blocker (`docker build -t turnbase/<name>:dev .` in the component directory).
- **Spec first.** If two documents disagree, stop and use the `spec-defect` skill. Known deviations
  this plan already settled are listed under *Settled deviations*; do not re-file them.
- **Style.** No emoji. Names `tb_` prefixed for k6 metrics. Comments say why, not what.

### Verified environment (2026-10-18)

| Fact | Value | Consequence |
|---|---|---|
| k6 | v2.2.0, go1.26.5, `/usr/bin/k6` | `k6/websockets` is WHATWG-style: `new WebSocket(url, null, {headers})`, `addEventListener`, text frames, global `setTimeout`/`setInterval`; the iteration waits for the event loop. `http.asyncRequest` exists and must be used inside the pair loop (a synchronous request blocks the VU's event loop and inflates STOMP timestamps) |
| Docker Desktop VM | 16 CPUs, 15.21 GiB (`docker info`), one node `docker-desktop`, Kubernetes v1.34.1, metrics-server present (`kubectl top` works) | The VM **is** the WSL2 VM, shared with k6. Record `docker info` in every report |
| `.wslconfig` | absent | Record "absent (VM defaults)" or the file's content |
| Ingress | ingress-nginx on port 80; platform host `turnbase.localhost`; path is ingress-nginx, then the frontend nginx, then the platform | Both proxies are in the measured path. A limit there is a finding ("ingress / frontend nginx") |
| `turnbase.localhost` | resolves to `::1` on the WSL host | If `k6` cannot connect, set `HOST_IP=127.0.0.1` (Task 7, `config.js`) |
| Tools | `jq curl taskset awk python3` present, `CLK_TCK=100` | |
| Images | `turnbase/{platform,game-host,frontend}:dev` exist | |
| Seed bundle | `turnbase-game-tictactoe/target/seed/2cc66e36-52e6-4144-9a10-09d09c982ce4.zip`; the manifest carries **no** `gameId` (it is the bundle's file name / the URL) | Matters for Task 10 |
| Username / password policy | username 3 to 32 of letters, digits, `_`, `-`, not starting `guest-`; password 8 to 128 characters, no composition rules | `lt-00000` and the default `PASSWORD` are valid |
| Protocol | `.claude/skills/run-turnbase/driver.mjs` | The only source for destinations and event names; port it, do not re-derive it |

### Settled deviations (found while planning; the owner has been told)

1. **Chart change for Postgres and Redis resources** (Global Constraints above).
2. **Memory.** The fixed limits (platform 3Gi, Game Host 4Gi, Postgres 1Gi, Redis 512Mi) sum to 8.5 GiB
   on a 15.21 GiB VM that also runs k6, the frontend, ingress and the observability stack; larger limits
   left pods unschedulable or OOM-killed the node. The values stay, and a run item never lowers or raises
   them ad hoc: a pod that is `Pending` for insufficient memory is `BLOCKED` (see R1). Every report records pod restarts and `OOMKilled`
   (`kubectl get pods -o jsonpath` in the snapshot step) and an OOM kill is a finding, not a harness bug.
3. **Heap.** The JVMs default to 25% of the container limit as heap. `values-loadtest.yaml` sets
   `JDK_JAVA_OPTIONS=-XX:MaxRAMPercentage=70` on both services. `JAVA_TOOL_OPTIONS` is **not** used: the
   Dockerfiles use it for the OpenTelemetry agent.
4. **`.wslconfig` cannot give k6 dedicated cores** (the VM is shared). k6 is pinned with `taskset` to the
   last 4 CPUs (the last 2 if the VM has fewer than 12) and the README says so. The `.wslconfig` note in the
   README is a memory recommendation only.
5. **`tb_op_failed`** (a k6 `Rate`, 1 per failed operation, 0 per successful one) is added so that the
   error-rate threshold "tb_errors / attempted operations < 1%" is expressible; a Counter alone cannot.
6. **`tb_active_games`** (Gauge) cannot be aggregated across VUs by k6: it holds the last value any VU
   wrote. Reports take concurrent games from the platform's `turnbase_game_sessions_active`.
7. **`start-rate`** uses `ramping-arrival-rate` (a `constant-arrival-rate` cannot step).
8. **`default-limits` keeps the resources.** It is redeployed from `loadtest/helm/values-default-limits.yaml`,
   which equals `values-loadtest.yaml` minus the `SPRING_PROFILES_ACTIVE` entry, so the only difference
   between that run and the others is the limiters. `Task 9` adds a diff check.
9. **`default-limits` and "errors at 0".** Registry `IMP-M15-09` says "`errors` at 0" and "records at least
   one `RATE_LIMIT_EXCEEDED`" in one sentence. For that scenario "errors" means unexpected errors: every
   `tb_errors` sample carries `expected=true|false`, and `RATE_LIMIT_EXCEEDED` is expected only there.
10. **Metric names.** The registry writes `errors`, `games_completed` and so on; the metrics are
    `tb_errors`, `tb_games_completed`, … (the decision list). The registry's names mean those.
11. **Summary location.** `IMP-M15-13` says `loadtest/reports/SUMMARY.md`; the decision list says a *Phase A
    results* subsection of `load-testing.md` §13. Both are written: `SUMMARY.md` holds the three answers
    and the capacity table, the §13 subsection holds a five-line pointer and the Follow-ups list stays in §13.
12. **`up-down` and `soak` need the `ramp-to-break` ceiling**, passed as `PAIRS`. The report line
    `Ceiling (pairs): <n>` is machine-read.

### Review Focus

Five failure modes most likely to survive a green smoke run, each with the check that catches it:

1. **A threshold evaluates the wrong population.** Thresholds are global in k6, so without step tags a
   ramp aborts on the cumulative p95 and "the ceiling" is meaningless. Task 9: the stepper unit test and
   `THRESHOLD_SCALE=0.001` must abort within 60 s and exit non-zero.
2. **A stale frame satisfies a later wait.** A matched frame left in a buffer completes the next game's
   `GAME_OVER` wait instantly. Task 8: `selftest.js` (consume-on-match, buffer clear) and the three-game
   smoke with `tb_errors` at 0 and `tb_games_completed` at 3.
3. **The measurement measures k6.** An unpinned k6, a 1,024 file-descriptor limit, synchronous HTTP in the
   loop or a heartbeat that is never sent all look like platform failures. Task 9: `run.sh` pins and raises
   `ulimit -n`; `check-generator.sh` flags steps; Task 8 asserts the heartbeat in the smoke log.
4. **Reset leaves state that makes run N+1 differ from run 1** (a registered Game Host lease in Redis, a
   room still `IN_PROGRESS`, a warm JIT). Task 7: reset scales every service to zero before it touches
   Postgres and Redis, and the post-reset assertions count `lt-%` users and Redis keys.
5. **A "measurement" session changes the system.** Run items must leave `git diff --stat` inside
   `loadtest/reports/`, `docs/specs/deployment/load-testing.md`, `STATUS.md` and the registry. The run
   protocol's final step prints that diff and stops if anything else is listed.

---

## Shared interfaces

Every module below is written in the task that owns it (stated per block). Later tasks import them
exactly as shown.

### `loadtest/lib/config.js` (Task 7)

```js
const e = (k, d) => (__ENV[k] !== undefined && __ENV[k] !== '' ? __ENV[k] : d);
const n = (k, d) => Number(e(k, d));
const baseUrl = e('BASE_URL', 'http://turnbase.localhost').replace(/\/$/, '');
const host = baseUrl.replace(/^https?:\/\//, '');          // host[:port]
export const cfg = {
  baseUrl, host, origin: baseUrl,
  wsUrl: baseUrl.replace(/^http/, 'ws') + '/ws',
  hostIp: e('HOST_IP', ''),                                // maps host -> ip when ::1 does not work
  gameId: e('GAME_ID', '2cc66e36-52e6-4144-9a10-09d09c982ce4'),
  userPrefix: e('USER_PREFIX', 'lt-'),
  password: e('PASSWORD', 'Loadtest-Passw0rd-2026'),
  thinkMinMs: n('THINK_MIN_MS', 0), thinkMaxMs: n('THINK_MAX_MS', 0),
  freshRoomEvery: n('FRESH_ROOM_EVERY', 5),
  stepSeconds: n('STEP_SECONDS', 120), settleSeconds: n('SETTLE_SECONDS', 20),
  thresholdScale: n('THRESHOLD_SCALE', 1),
  coldWindowMs: n('COLD_WINDOW_MS', 30000),
  startTimeoutMs: n('START_TIMEOUT_MS', 120000), stepTimeoutMs: n('STEP_TIMEOUT_MS', 10000),
  errorBackoffMs: n('ERROR_BACKOFF_MS', 1000),
};
export const userName = (i) => cfg.userPrefix + String(i).padStart(5, '0');
export const pairUsers = (p) => [userName(2 * p), userName(2 * p + 1)];   // VU id v -> pair v-1
export const hostsOption = () => (cfg.hostIp ? { [cfg.host.split(':')[0]]: cfg.hostIp } : {});
```

### `loadtest/lib/metrics.js` (Task 7 declares the metrics; Task 9 adds `stepper` and `thresholds`)

| Name | Type | Notes |
|---|---|---|
| `tb_login`, `tb_room_create`, `tb_room_join`, `tb_lobby_event`, `tb_game_start`, `tb_move_rtt`, `tb_game_duration` | Trend (`true`, ms) | `tb_game_start` carries `cold=true\|false` |
| `tb_games_completed`, `tb_errors` | Counter | `tb_errors` tags `code`, `expected` |
| `tb_ws_disconnects` | Counter | unexpected socket closes only |
| `tb_active_games` | Gauge | 1 at game start, 0 at game end, per VU (see deviation 6) |
| `tb_op_failed` | Rate | 1 failed op, 0 ok op; denominator of the error-rate threshold |
| `tb_provision_created`, `tb_provision_existing` | Counter | `provision.js` only; `add(0)` once per iteration so the line always prints |

```js
export const m = { login, roomCreate, roomJoin, lobbyEvent, gameStart, moveRtt, gameDuration,
                   gamesCompleted, errors, wsDisconnects, activeGames, opFailed };
export function ok()                      // opFailed.add(false, stepper.tags())
export function fail(code)                // errors.add(1,{code,expected}); opFailed.add(true, ...)
export function expectCodes(list)         // codes counted expected=true (default-limits only)
export const stepper                      // Task 9: configure(segments, settleSeconds), tags()
export function thresholds({ steps, abort, extra })   // Task 9
```

### `loadtest/lib/stomp.js` (Task 8)

```js
export function encodeFrame(command, headers, body)   // 'CMD\nk:v\n\nbody\0'
export function parseFrames(data)                     // -> [{command, headers, body, msg}]  (msg = parsed JSON or null)
export class StompClient {
  constructor(url, headers, hooks)   // hooks: { onUnexpectedClose() }
  connect(timeoutMs)                 // Promise; resolves on CONNECTED, rejects on ERROR/close/timeout
  subscribe(destination)             // -> subscription id
  unsubscribe(id)
  send(destination, type, payload)   // -> t0 (Date.now() before the write); body {type, correlationId, payload}
  waitFor(pred, timeoutMs, code)     // Promise<frame>; frame.t = arrival Date.now(); consumes the match
  clear()                            // drops buffered frames
  close()
}
```

### `loadtest/lib/player.js` (HTTP half in Task 7; sockets in Task 8)

```js
export class Player {
  constructor(name, cookies)         // cookies: [{name, value}] from setup(), may be empty
  async login()                      // POST /api/auth/login; records tb_login; fills the jar
  async request(method, path, body, name)   // http.asyncRequest + Host header + jar; returns {res, ms}
  cookieHeader()                     // 'a=b; c=d' from the jar, for the WebSocket upgrade
  async ensureConnected()            // opens the socket once per user, subscribes the two user queues
}
export function loginAll(userCount)  // setup(): logs in lt-00000.. in batches; returns {cookies: {name: [{name,value}]}}
export function errorCode(res)       // 429 -> RATE_LIMIT_EXCEEDED, 5xx -> http_5xx, body.code, else http_<status>
```

### Scenario conventions (Tasks 9 and 10)

Every scenario file exports `options`, `setup` (calls `loginAll`) and a `default` function that calls
`pairSession`. `export function pairSession(pair, { games })` plays `games` games in **one** room.
`default` is `await pairSession(getPair(data), { games: cfg.freshRoomEvery })`. Stepped scenarios call
`stepper.configure(...)` at module level. No scenario sets thresholds by hand; they call `thresholds()`.

### Results layout (git-ignored, Task 9)

`loadtest/results/<YYYYMMDD-HHMMSS>-<scenario>/` holds `k6.log`, `summary.json`, `samples.csv`
(`epoch,k6_cpu_pct,vm_cpu_pct,load1`), `pods.csv` (`epoch,pod,cpu_m,mem_mi`), `start.epoch`, `end.epoch`,
`exit-code`, `params.txt`, `steps.csv`, `prom/<name>.json`, `cluster.txt`.

---

## Task 7 — IMP-M15-07 Scaffold, overlay, install, reset, preflight, provisioning

**Repo:** `turnbase` (umbrella) and, for Step 3, `turnbase-platform`. **Files:**

- Create: `loadtest/.gitignore` (`results/`), `loadtest/README.md`,
  `loadtest/helm/values-loadtest.yaml`, `loadtest/install.sh`, `loadtest/reset.sh`,
  `loadtest/preflight.sh`, `loadtest/lib/config.js`, `loadtest/lib/metrics.js` (metric declarations
  only), `loadtest/lib/player.js` (HTTP half), `loadtest/scenarios/provision.js`
- Modify: `turnbase-platform/deploy/helm/turnbase/values.yaml`,
  `templates/postgres-statefulset.yaml`, `templates/redis-statefulset.yaml`;
  `docs/implementation/registry.md` (the row status only), `docs/implementation/INDEX.md`
  only if `check-corpus.py` asks

- [ ] **Step 0: Claim and branch.** `work-item` steps 1 to 3: set `IMP-M15-07` to `WIP (session N)` in
  the register table, `git switch -c feat/m15-07-loadtest-scaffold`, read `local-environment.md` §4 to §6,
  §7.6, §7.8 (the Helm install commands `IMP-M15-06` recorded). Run
  `command -v k6 kubectl helm jq curl taskset >/dev/null && echo tools-ok`. Expected: `tools-ok`.

- [ ] **Step 1: Failing check first.** `ls loadtest 2>&1 | head -1`. Expected: `ls: cannot access 'loadtest'`.

- [ ] **Step 2: Preflight script.** Create `loadtest/preflight.sh`. It runs every check, prints one line
  per failure (`PREFLIGHT FAIL: <what>`), prints `PREFLIGHT OK` and exits 0 when none failed, and exits 1
  otherwise. It does not stop at the first failure. Checks, in this order:
  1. `kubectl config current-context` equals `docker-desktop`;
  2. `kubectl get nodes docker-desktop` reports `Ready`;
  3. `helm version --short` and `k6 version` succeed;
  4. `docker image inspect turnbase/platform:dev turnbase/game-host:dev turnbase/frontend:dev`;
  5. `helm status turnbase` is `deployed`;
  6. every pod in the namespace is `Ready` (`kubectl get pods --no-headers`, none whose READY column is
     `n/m` with `n<m`, none in a phase other than `Running`/`Completed`);
  7. `curl -s -o /dev/null -m 5 -w '%{http_code}' ${BASE_URL:-http://turnbase.localhost}/api/games`
     answers an HTTP status (any non-`000`; the exact path may be adjusted to a public endpoint, and the
     result noted in the README).
  Checks 5 to 7 are skipped with `PREFLIGHT NOTE:` when called as `preflight.sh --cluster-only`
  (used before the first install).

- [ ] **Step 3: Chart values for Postgres and Redis resources** (`turnbase-platform`, own branch
  `feat/chart-postgres-redis-resources`). Add `postgres.resources: {}` and `redis.resources: {}` to
  `values.yaml`, and under each container in `templates/postgres-statefulset.yaml` and
  `templates/redis-statefulset.yaml` add
  `resources:\n  {{- toYaml .Values.postgres.resources | nindent 12 }}` (same idiom as
  `templates/platform-deployment.yaml:65`). Verify:
  ```bash
  cd turnbase-platform/deploy/helm/turnbase
  helm template t . -f values-local.yaml --set postgres.ownerPassword=x,postgres.appPassword=x,redis.password=x,minio.rootUser=x,minio.rootPassword=xxxxxxxx,minio.appAccessKey=a,minio.appSecretKey=bbbbbbbb,auth.jwtKeySet=x,admin.username=a,admin.password=b,observability.grafana.adminPassword=x \
    --set postgres.resources.limits.cpu=2 --set redis.resources.limits.cpu=1 \
    | grep -c 'cpu: "\?[12]"\?'
  ```
  Expected: `2` or more (adjust the secret `--set` flags to whatever `helm lint` demands; the point is the
  two values render). `helm lint . -f values-local.yaml -f values-local.secrets.yaml` exits 0. Commit
  `feat(helm): resources for Postgres and Redis`, merge `--ff-only`, push, delete the branch (local and
  remote), then in the umbrella `git add turnbase-platform` on the Task 7 branch (the ref bump).

- [ ] **Step 4: The overlay.** Create `loadtest/helm/values-loadtest.yaml` exactly:
  ```yaml
  # Phase A load-test overlay, applied after values-local (and the secrets file). Every value here is
  # fixed for all Phase A runs (m15-test-definition-plan.md); a run item never edits it.
  # requests == limits, so the cgroup caps are the figures reported. If the Docker Desktop VM has
  # fewer than 12 CPUs, halve every cpu below and record it in the report.
  origins:
    platform: http://turnbase.localhost
    gameFrontendTemplate: "http://{gameId}.games.localhost"
  platform:
    replicaCount: 1
    autoscaling:
      enabled: false
    resources:
      requests: { cpu: "4", memory: 3Gi }
      limits:   { cpu: "4", memory: 3Gi }
    extraEnv:
      - { name: SPRING_PROFILES_ACTIVE, value: "local,loadtest" }
      - { name: JDK_JAVA_OPTIONS, value: "-XX:MaxRAMPercentage=70" }
  gamehost:
    replicaCount: 1
    resources:
      requests: { cpu: "4", memory: 4Gi }
      limits:   { cpu: "4", memory: 4Gi }
    extraEnv:
      - { name: JDK_JAVA_OPTIONS, value: "-XX:MaxRAMPercentage=70" }
  postgres:
    resources:
      requests: { cpu: "2", memory: 1Gi }
      limits:   { cpu: "2", memory: 1Gi }
  redis:
    resources:
      requests: { cpu: "1", memory: 512Mi }
      limits:   { cpu: "1", memory: 512Mi }
  observability:
    prometheus:
      remoteWriteReceiver: true
  ```
  Check the key names against `values.yaml` as `IMP-M15-06` left it (`platform.autoscaling.enabled`,
  `observability.prometheus.remoteWriteReceiver`, `extraEnv`). If `IMP-M15-06` named one differently,
  the chart wins and this file follows it; record the difference in the README. Verify the YAML parses:
  `python3 -c 'import yaml,sys; yaml.safe_load(open("loadtest/helm/values-loadtest.yaml"))' && echo ok`
  (if PyYAML is absent use `helm template` in Step 6 as the parse check).

- [ ] **Step 5: `install.sh`.** `loadtest/install.sh [--default-limits]` (extra file; reset and the
  `default-limits` scenario both need it). Behaviour:
  1. refuse unless `kubectl config current-context` is `docker-desktop`;
  2. if `turnbase-platform/deploy/helm/turnbase/values-local.secrets.yaml` is missing, create it with
     `umask 077` from `values-local.secrets.example.yaml`'s keys using `openssl rand -hex 16` for every
     password and key, and for `auth.jwtKeySet` the JSON
     `{"active":{"kid":"k1","secret":"<openssl rand -base64 32>","notBefore":"2020-01-01T00:00:00Z"},"retired":[]}`;
     `minio.rootPassword`, `minio.appSecretKey` at least 8 characters; print `generated dummy secrets
     (git-ignored)`;
  3. `helm upgrade --install turnbase turnbase-platform/deploy/helm/turnbase -f …/values-local.yaml -f
     …/values-local.secrets.yaml -f loadtest/helm/values-loadtest.yaml --set platform.seed=$PWD/turnbase-game-tictactoe/target/seed
     --wait --timeout 10m` (use the seed flag and any other flag `local-environment.md` lists for the
     install; with `--default-limits` the last `-f` is `loadtest/helm/values-default-limits.yaml`).
  4. `kubectl rollout restart` is **not** run here; `reset.sh` owns restarts.
  If the `target/seed` zip is missing, build it (`turnbase-game-tictactoe` README) before Step 6.

- [ ] **Step 6: Install and run the preflight.** `bash loadtest/preflight.sh --cluster-only`; then
  `bash loadtest/install.sh`; then `bash loadtest/preflight.sh`. Expected: `PREFLIGHT OK` twice, and
  `helm get values turnbase | grep -c 'SPRING_PROFILES_ACTIVE'` prints `1`. Prove the failure path:
  `kubectl config use-context <another>` is not available on every machine, so instead run
  `BASE_URL=http://127.0.0.1:1 bash loadtest/preflight.sh; echo "exit=$?"`. Expected: a
  `PREFLIGHT FAIL:` line naming the URL check, `exit=1`.

- [ ] **Step 7: Profile check.** `kubectl logs deploy/turnbase-platform | grep -m1 -i 'profiles are active'`
  shows `local, loadtest` (the Spring line is `The following 2 profiles are active: "local", "loadtest"`);
  `kubectl logs deploy/turnbase-platform | grep -c RateLimitEnabledProfileCheck` prints `0` failures (the
  class name appears only in a stack trace on refusal). If the grep matches, the platform refused to boot:
  read the message, which names the switch.

- [ ] **Step 8: `config.js`, `metrics.js`, HTTP half of `player.js`.** Write them to the interfaces above.
  `player.js` details:
  - `request()` uses `http.asyncRequest(method, cfg.baseUrl + path, body, {jar, headers, tags:{name}})`
    with headers `Host: cfg.host`, `Content-Type: application/json` when a body is sent. The `name` tag
    is a template (`POST /api/rooms/{id}/participants`), never the URL, so metric cardinality stays flat.
  - `login()` posts `{usernameOrEmail, password}`; the cookie lands in the jar. It adds
    `res.timings.duration` to `m.login`. A non-200 calls `fail(errorCode(res))` and returns `false`.
  - `errorCode(res)`: `res.status === 0` -> `network`; body `code` when the body is JSON with a string
    `code`; else 429 -> `RATE_LIMIT_EXCEEDED`; 5xx -> `http_5xx`; else `http_<status>`.
  - `loginAll(n)`: for users `0..n-1`, in batches of `LOGIN_PARALLEL` (default 8) with `http.batch`, log in
    and collect `res.cookies` as `[{name, value: cookies[name][0].value}]`; returns `{ cookies }`. This is
    the pre-login that keeps Argon2 out of the measured window; set `setupTimeout: '10m'` in scenarios.
  - `m.login` is recorded here only (never inside the pair loop).

- [ ] **Step 9: `provision.js`.** Options: `hosts: hostsOption()`, one scenario `provision` with
  `shared-iterations`, `vus: 8`, `iterations: Number(__ENV.USERS || 2000)`, `maxDuration: '10m'`. Each
  iteration takes `i = exec.scenario.iterationInTest`, name `userName(i)` and:
  `m` counters `add(0)`; login; `200` -> `tb_provision_existing.add(1)`; `401` or `404` -> register
  `{username, email: name + '@example.com', password, confirmPassword: password}` (expect `201`; any other
  status is `fail(errorCode)`), `tb_provision_created.add(1)`, then log in again and expect `200`.
  Registration is bounded by the 8 VUs; it runs outside every measurement window. The `loadtest` profile
  must have switched registration limiting off (Step 7), otherwise this fails with
  `RATE_LIMIT_EXCEEDED` after 3 users: that is the profile not being active, not a script bug.

- [ ] **Step 10: Provision, twice.**
  ```bash
  k6 run loadtest/scenarios/provision.js 2>&1 | grep -E 'tb_provision_(created|existing)|tb_errors|checks'
  k6 run loadtest/scenarios/provision.js 2>&1 | grep -E 'tb_provision_(created|existing)'
  ```
  Expected: first run `tb_provision_created....: 2000` and `tb_provision_existing...: 0`; second run
  `tb_provision_created....: 0` and `tb_provision_existing...: 2000`. A login for `lt-00001`:
  `curl -s -o /dev/null -w '%{http_code}\n' -H 'Content-Type: application/json' -d '{"usernameOrEmail":"lt-00001","password":"Loadtest-Passw0rd-2026"}' http://turnbase.localhost/api/auth/login`
  prints `200`. If `HOST_IP` was needed, note it in the README.

- [ ] **Step 11: `reset.sh`.** `loadtest/reset.sh` (no arguments). Refuse unless the context is
  `docker-desktop`. Then:
  1. `kubectl scale deploy/turnbase-frontend deploy/turnbase-platform deploy/turnbase-gamehost --replicas=0`
     and wait until no pod of those three remains (`kubectl wait --for=delete pod -l … --timeout=120s`,
     tolerate "no matching resources");
  2. Postgres, as the owner role, the same SQL as `turnbase-platform/Makefile` `reset-db`:
     `kubectl exec statefulset/turnbase-postgres -- psql -v ON_ERROR_STOP=1 -U turnbase_owner -d turnbase -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT USAGE, CREATE ON SCHEMA public TO turnbase_app; CREATE EXTENSION IF NOT EXISTS pgcrypto; CREATE EXTENSION IF NOT EXISTS pg_trgm; CREATE EXTENSION IF NOT EXISTS btree_gin;"`
     (Flyway recreates the tables when the platform starts);
  3. `kubectl exec statefulset/turnbase-redis -- sh -c 'redis-cli -a "$TURNBASE_REDIS_PASSWORD" FLUSHALL'`;
  4. scale back to 1, platform first, `kubectl rollout status` each (`--timeout=300s`; the Game Host
     boot wedges about one time in five and `supervise.sh` restarts it, so allow two rounds);
  5. print `RESET OK`.
  Scaling every service to zero before touching the stores is deliberate: a live Game Host would
  re-register its lease and a live platform would re-create rows (Review Focus 4). Prometheus is left
  running; its history is the evidence for earlier runs.

- [ ] **Step 12: Verify reset.**
  ```bash
  bash loadtest/reset.sh
  kubectl exec statefulset/turnbase-postgres -- psql -U turnbase_owner -d turnbase -tA -c "SELECT count(*) FROM app_user WHERE username LIKE 'lt-%'"
  kubectl exec statefulset/turnbase-redis -- sh -c 'redis-cli -a "$TURNBASE_REDIS_PASSWORD" DBSIZE' 2>/dev/null
  ```
  Expected: `RESET OK`, `0`, and a `DBSIZE` of a handful of keys (the Game Host lease and the platform's
  startup keys; record the number in the README as "the seed's"). Then
  `bash loadtest/preflight.sh && k6 run loadtest/scenarios/provision.js 2>&1 | grep tb_provision_created`
  prints `…: 2000` again.

- [ ] **Step 13: README.** `loadtest/README.md`: purpose (one paragraph), prerequisites, the run
  procedure as a numbered list (build images, `install.sh`, `preflight.sh`, `provision`, `run.sh start`,
  `run.sh wait`, `snapshot.sh`, report, `reset.sh`), what each script does, the environment variables of
  `config.js` in a table, the single-node and shared-VM statement (deviation 4), the `.wslconfig`
  recommendation (memory only, e.g. `[wsl2] memory=15GB`; record the file or "absent" in every report),
  `HOST_IP`, the 8.5 GiB total of the memory limits and why they stay below the VM size, and a *Scripts added by Task 9* placeholder section
  that Task 9 fills. Task 7 writes everything except that section.

- [ ] **Step 14: Close.** The register already lists `IMP-M15-07`'s `Repo` as `turnbase-platform` (chart:
  Postgres and Redis resources) plus the umbrella; bump the `turnbase-platform` submodule ref after the
  Step 3 merge is green. Run `bash -n loadtest/*.sh`, `python3 scripts/check-corpus.py`
  (expected `clean`), then `work-item` steps 8: row `DONE`, STATUS.md replaced, merge `--ff-only`, push,
  delete the branch locally and on the remote. `LOOP_STATUS: DONE IMP-M15-07`.

---

## Task 8 — IMP-M15-08 STOMP client and the pair game loop

**Repo:** `turnbase` (umbrella). **Files:**

- Create: `loadtest/lib/stomp.js`, `loadtest/lib/pair.js`, `loadtest/scenarios/smoke.js`,
  `loadtest/test/selftest.js`
- Modify: `loadtest/lib/player.js` (the socket half), `loadtest/README.md` (a *Scenarios* table row)

- [ ] **Step 0: Claim, branch, preflight.** `IMP-M15-08` to `WIP`, `git switch -c feat/m15-08-k6-client`,
  `bash loadtest/preflight.sh` (expected `PREFLIGHT OK`), read the read-list. If preflight fails, run
  `bash loadtest/reset.sh` once, then preflight again; a still-failing cluster check is `BLOCKED`.

- [ ] **Step 1: Selftest first (red).** Create `loadtest/test/selftest.js`. It imports `parseFrames`,
  `encodeFrame` from `../lib/stomp.js` and the pure helpers `winner`, `isOver`, `pickEmpty` from
  `../lib/pair.js`, and uses k6 `check`. Options `{ iterations: 1, thresholds: { checks: ['rate==1'] } }`.
  Required assertions (each a `check`):
  - `encodeFrame('SEND', {destination:'/app/x'}, '{"a":1}')` equals `"SEND\ndestination:/app/x\n\n{\"a\":1}\0"`.
  - `parseFrames("\n")` is `[]` (a heart-beat); `parseFrames("MESSAGE\ndestination:/topic/a\n\n{\"type\":\"X\"}\0\nMESSAGE\ndestination:/topic/b\n\n{\"type\":\"Y\"}\0")`
    yields two frames whose `msg.type` are `X` and `Y` and whose headers carry the destinations.
  - A frame with a body containing `\n\n` inside a JSON string keeps the whole body.
  - A frame with a non-JSON body has `msg === null`.
  - `winner(['X','X','X',e,e,e,e,e,e])` is `'X'` for any `e`; `isOver` is true on a full board with no
    winner; `pickEmpty` never returns an occupied cell over 1,000 draws.
  Run `k6 run loadtest/test/selftest.js`. Expected now: fails (modules missing).

- [ ] **Step 2: `stomp.js`.** Write to the interface. Required behaviours, each named so the review can
  find it:
  - `connect`: opens `new WebSocket(url, null, { headers })`; on `open` sends
    `CONNECT` with `accept-version:1.2` and `heart-beat:10000,10000`, and starts a
    `setInterval(() => ws.send('\n'), 4000)`. **The server closes a client that does not heart-beat**; this is
    the one behaviour `driver.mjs` comments on. Resolve on `CONNECTED`; reject on `ERROR`, on close before
    `CONNECTED`, or after `timeoutMs`.
  - Frame stamping: the arrival time `f.t = Date.now()` is taken once per WebSocket message, before parsing.
  - `waitFor(pred, ms, code)`: scan the buffer first and **remove** the first match; otherwise register a
    waiter. A frame handed to a waiter is not buffered. On timeout reject with an `Error` whose `.code` is
    `code` (default `timeout`); on socket close reject every waiter with `.code = 'ws_closed'`.
    The buffer keeps at most 256 frames (drop the oldest).
  - A STOMP `ERROR` frame or a `MESSAGE` on `/user/queue/errors` is buffered like any frame (the pair loop
    decides); an `ERROR` frame additionally closes the client.
  - Unexpected close (we did not call `close()`): call `hooks.onUnexpectedClose()` once.
  - `send` returns `t0` taken immediately before `ws.send`. `correlationId` is a locally generated v4-shaped
    id from `Math.random` (no jslib).
  No `unsubscribe` frame is sent for a socket that is closing.

- [ ] **Step 3: Socket half of `Player`.** `ensureConnected()` returns at once when the socket is open;
  otherwise it builds `new StompClient(cfg.wsUrl, { Host: cfg.host, Origin: cfg.origin, Cookie: this.cookieHeader() }, { onUnexpectedClose })`,
  connects (10 s), subscribes `/user/queue/errors` and `/user/queue/game` once, and keeps it for the VU's
  life: **one socket per user**. `onUnexpectedClose` does `m.wsDisconnects.add(1, stepper.tags())` and marks
  the client dead, so the next `ensureConnected()` reconnects. A 401 on upgrade is retried once after
  `login()`. Expose the client as `player.ws`.

- [ ] **Step 4: `pair.js`.** Exports `getPair(data)`, `pairSession(pair, {games})`, and the pure helpers
  `winner`, `isOver`, `pickEmpty`. Port the protocol from `driver.mjs` exactly:

  | Step | Action |
  |---|---|
  | create | host `POST /api/rooms {gameId, visibility:'PUBLIC', spectatingEnabled:false}`; expect `201`; `roomId = json.roomId ?? json.room?.roomId`; `m.roomCreate.add(ms)` |
  | join | guest `POST /api/rooms/{id}/participants {role:'PLAYER'}`; expect `201`; `m.roomJoin.add(ms)` |
  | subscribe | both `subscribe('/topic/room.{id}')` |
  | per game: clear | both `ws.clear()` |
  | ready | guest `send('/app/room.{id}.member','TOGGLE_READY',{ready:true})` (idempotent, so the rematch needs no special case); host `waitFor(READINESS_CHANGED)`; `m.lobbyEvent.add(f.t - t0)` |
  | start | host `send('/app/room.{id}.host','START_GAME')`; **both** `waitFor(GAME_STARTED)` (timeout `startTimeoutMs`, code `start_timeout`); `m.gameStart.add(f.t - t0, {cold})` |
  | game topic | both `subscribe('/topic/game.{sid}')`, then both `send('/app/game.{sid}.sync','REQUEST_GAME_SYNC')`, both `waitFor(GAME_SYNC)` -> `view.yourMark`, `view.board`, `view.turn` |
  | moves | loop below |
  | end | both `waitFor(GAME_OVER)`, `m.gameDuration.add(now - tFirstMove)`; both `waitFor(GAME_ENDED)` (on the room topic); `m.gamesCompleted.add(1)`; unsubscribe the game topic |

  *Cold.* `cold = (pair.gamesStarted === 0 && Date.now() - exec.scenario.startTime < cfg.coldWindowMs)`,
  tag value the string `'true'` or `'false'`; `pair.gamesStarted++` after each start. `reset.sh` restarts the
  Game Host, so a run's first starts are cold.

  *Moves.* The empty value is `board[0]` of the initial board (all cells equal at start); do not hard-code
  it. The mover is the player whose `yourMark === turn`. Pick a random empty cell, `t0 = mover.ws.send(
  '/app/game.{sid}.action','SUBMIT_ACTION',{cell})`, then `mover.ws.waitFor` the `GAME_EVENT` with
  `msg.sessionId === sid` and `payload.type === 'move' && payload.cell === cell` (or `payload.type ===
  'rejected'`, which is `fail('move_rejected')` and ends the game). `m.moveRtt.add(f.t - t0, tags)`. Apply
  `board[cell] = payload.mark; turn = payload.next`. Stop when `isOver(board)` (local win/draw check; a
  harness helper, not platform logic). Think time: before each `send`, sleep a uniform random value in
  `[thinkMinMs, thinkMaxMs]` when `thinkMaxMs > 0`.

  *Accounting.* After every step that succeeds `ok()`; any throw inside `pairSession` is caught once at
  the top: `fail(e.code || 'exception')`, then (always, in `finally`) both users
  `DELETE /api/rooms/{id}/participants/me` (expect `204`, ignore other results, not counted as failures),
  both unsubscribe the room topic, and after a failure `sleep(cfg.errorBackoffMs)` so a failing system is
  not hammered by a hot loop. `m.activeGames.add(1)` at game start and `add(0)` at game end or abort.
  On a pair's very first iteration the previous room is unknown to the VU; a stale membership is released
  by the single-room rule when the room is created (`room-rest-api.md` §2 and FR-JOIN-007; confirm the
  create path releases and, if it does not, record that in the README and let `reset.sh` cover it).
  `getPair(data)` returns a module-level cache keyed by `exec.vu.idInTest - 1`; a VU id above the number of
  provisioned pairs (1,000) throws `Error('VU id beyond provisioned users')` so a mis-sized scenario fails
  loudly. Timeouts: `stepTimeoutMs` for every wait except `GAME_STARTED`.

  Protocol facts the code must not assume: the board's empty value, the type of `turn`, and the
  `GAME_SYNC` field names are read from the live payload during Step 6; if one differs from the line above,
  fix it in one named function (`readView(f)`) and add a sentence to the README.

- [ ] **Step 5: Green selftest.** `k6 run loadtest/test/selftest.js`. Expected: exit 0, `checks.........: 100.00%`.

- [ ] **Step 6: `smoke.js`.** One pair, three games: one room with two games (the second is the rematch),
  then a fresh room with one. Options: `hosts`, `setupTimeout`, one scenario `shared-iterations` with
  `vus: 1, iterations: 1, maxDuration: '3m'`, `setup() { return loginAll(2); }`, thresholds
  `{ 'tb_errors': ['count==0'], 'tb_games_completed': ['count>=3'] }`, `summaryTrendStats:
  ['avg','p(50)','p(95)','p(99)','max','count']`. Default function:
  `const pair = getPair(data); await pairSession(pair,{games:2}); await pairSession(pair,{games:1});`
  Run it (the stack is freshly provisioned, so the Game Host is cold):
  ```bash
  k6 run loadtest/scenarios/smoke.js 2>&1 | tee /tmp/smoke.out | tail -45
  echo "exit=${PIPESTATUS[0]}"
  ```
  Expected: `exit=0`; `tb_games_completed....: 3`; `tb_errors` absent or `0`; and each of
  `tb_login tb_room_create tb_room_join tb_lobby_event tb_game_start tb_move_rtt tb_game_duration
  tb_games_completed tb_errors tb_ws_disconnects tb_active_games tb_op_failed` listed. `tb_errors` and
  `tb_ws_disconnects` print only when they received a sample: emit `add(0)` for each once in `setup`'s
  caller (the first iteration) so the summary lists them; `tb_game_start` must show both a
  `cold:true` and a `cold:false` sub-sample set in `jq` of a `--summary-export` file (one cold start, two
  warm). If the run is slow because it is the first start, that is the cold start, not a defect.

- [ ] **Step 7: Heartbeat proof.** Run the smoke with `--http-debug` is too noisy; instead run it with
  `THINK_MIN_MS=5000 THINK_MAX_MS=5000 k6 run -e THINK_MIN_MS=5000 -e THINK_MAX_MS=5000 loadtest/scenarios/smoke.js`
  (about 90 s of idle sockets between moves) and confirm `tb_ws_disconnects` stays `0` and
  `tb_errors` at `0`. Expected: both zero. A disconnect here means the 4 s client heart-beat is not
  being sent.

- [ ] **Step 8: Clean-room proof.** After the smoke:
  ```bash
  kubectl exec statefulset/turnbase-postgres -- psql -U turnbase_owner -d turnbase -c '\dt' | grep -i partic
  ```
  to find the participants table, then count the rows of `lt-%` users with `left_at IS NULL`
  (`SELECT count(*) FROM <table> rp JOIN users u ON u.id = rp.user_id WHERE u.username LIKE 'lt-%' AND rp.left_at IS NULL`).
  Expected: `0`. Record the real table and column names in the README.

- [ ] **Step 9: Repeatability.** Run the smoke three times in a row; each must exit 0 with
  `tb_games_completed` at 3 (this catches stale-frame and subscription-race failures, Review Focus 2).
  One failure in three is a defect: read the `tb_errors` code, fix it, repeat.

- [ ] **Step 10: Close.** README *Scenarios* row for `smoke`; `bash -n`; `python3 scripts/check-corpus.py`
  (expected `clean`); register `DONE`, STATUS.md replaced, merge `--ff-only`, push, delete the branch.
  `LOOP_STATUS: DONE IMP-M15-08`.

---

## Task 9 — IMP-M15-09 Scenarios, thresholds, scripts and the report template

**Repo:** `turnbase` (umbrella). **Files:**

- Create: `loadtest/scenarios/{parallelism,ramp-to-break,start-rate,soak,up-down,default-limits}.js`,
  `loadtest/run.sh`, `loadtest/sample-generator.sh`, `loadtest/check-generator.sh`,
  `loadtest/snapshot.sh`, `loadtest/steps-table.sh`, `loadtest/check-report.sh`,
  `loadtest/reports/TEMPLATE.md`, `loadtest/helm/values-default-limits.yaml`,
  `loadtest/test/check-generator-selftest.sh`, `loadtest/test/check-overlays.sh`
- Modify: `loadtest/lib/metrics.js` (`stepper`, `thresholds`, `expectCodes`), `loadtest/test/selftest.js`
  (stepper and threshold cases), `loadtest/README.md` (*Scripts* section)

- [ ] **Step 0: Claim, branch, preflight.** `IMP-M15-09` to `WIP`, `git switch -c feat/m15-09-scenarios`,
  `bash loadtest/preflight.sh`, provisioned users present (`k6 run loadtest/scenarios/provision.js` if the
  count of `lt-%` users is not 2,000).

- [ ] **Step 1: Stepper tests first (red).** Extend `selftest.js`: with `stepper.configure([{tag:'10',
  seconds:120},{tag:'20',seconds:120}], 20, fakeNow)` (the stepper accepts an injectable `now()` and
  `startTime` for tests), `tags()` returns `{step:'warmup'}` at 5 s, `{step:'10'}` at 30 s,
  `{step:'warmup'}` at 125 s, `{step:'20'}` at 150 s and keeps `{step:'20'}` after the last segment's end.
  `thresholds({steps:['10','20'], abort:true, scale:0.001})` returns a key
  `"tb_move_rtt{step:10}"` whose entries are
  `{threshold:'p(95)<0.2', abortOnFail:true, delayAbortEval:'30s'}` and `p(99)<0.5`, a key
  `"tb_game_start{step:10,cold:false}"` with `p(95)<1` and `p(99)<2`, and `"tb_op_failed{step:10}"` with
  `rate<0.00001`; with `steps:[null]` the keys have no `step` tag. `abort:false` yields entries without
  `abortOnFail`. Expect red.

- [ ] **Step 2: `stepper` and `thresholds`.** In `metrics.js`:
  ```js
  const LIMITS = [                       // metric, extra tag, p95 ms, p99 ms
    ['tb_move_rtt', null, 200, 500],
    ['tb_room_create', null, 200, 500],
    ['tb_room_join', null, 200, 500],
    ['tb_lobby_event', null, 300, 600],
    ['tb_game_start', 'cold:false', 1000, 2000],
  ];
  export function thresholds({ steps = [null], abort = false, scale = cfg.thresholdScale, extra = {} }) {
    const out = {};
    const entry = (t) => (abort ? { threshold: t, abortOnFail: true, delayAbortEval: '30s' } : t);
    for (const s of steps) {
      const key = (name, tag) => {
        const tags = [s == null ? null : `step:${s}`, tag].filter(Boolean).join(',');
        return tags ? `${name}{${tags}}` : name;
      };
      for (const [name, tag, p95, p99] of LIMITS)
        out[key(name, tag)] = [entry(`p(95)<${p95 * scale}`), entry(`p(99)<${p99 * scale}`)];
      out[key('tb_op_failed')] = [entry(`rate<${0.01 * scale}`)];
    }
    return { ...out, ...extra };
  }
  ```
  `stepper.configure(segments, settleSeconds, clock)` stores `segments = [{tag, seconds}]`; `tags()` computes
  `elapsed = now() - exec.scenario.startTime` (ms epoch, verified in k6 2.2.0), picks the segment, returns
  `{step: 'warmup'}` while `elapsed - segmentStart < settleSeconds*1000` and the segment tag otherwise, and
  `{}` when never configured. The first `settleSeconds` of each segment are tagged `warmup` so a new step's
  first few samples cannot trip an `abortOnFail` threshold on a one-sample p95 (a risk that remains in
  principle: the threshold is checked every few seconds and `delayAbortEval` counts from the test start,
  not from the step; the report states it). Every `add` call in `pair.js` and `player.js` spreads
  `stepper.tags()`. `expectCodes(list)` sets the codes counted `expected:'true'`. Run the selftest:
  `k6 run loadtest/test/selftest.js` -> `checks.........: 100.00%`.

- [ ] **Step 3: Scenarios.** All share the conventions above. Minimum-size parameters are the env values
  in the table; the registry requires each to start, run at most two minutes and exit 0 with
  `tb_errors` at 0 (for `default-limits`: `tb_errors{expected:false}` at 0 and at least one
  `RATE_LIMIT_EXCEEDED`).

  | Scenario | Executor and shape (defaults) | Pass thresholds | Minimum-size parameters |
  |---|---|---|---|
  | `parallelism` | `ramping-vus`; levels 1,2,4,8,16,32,64,128,256 pairs; each step `STEP_SECONDS` (120) with a 10 s ramp; `thresholds({steps:levels, abort:false})` (they exist to create the per-step sub-metrics) | none abort | `STEP_SECONDS=20 SETTLE_SECONDS=5 LEVELS=1,2` |
  | `ramp-to-break` | `ramping-vus`; start 10 pairs, +10 per step, max 1,000; `abort:true` | all, abort | `STEP_SECONDS=20 SETTLE_SECONDS=5 START_PAIRS=2 STEP_PAIRS=2 MAX_PAIRS=6` |
  | `start-rate` | `ramping-arrival-rate`; `startRate:1`, `timeUnit:'1s'`, rates 1,2,4,8,16,32 games/s, 10 s ramp then hold; `preAllocatedVUs: 50`, `maxVUs: MAX_PAIRS` (400); each iteration `pairSession(pair,{games:1})`; steps tagged by rate | all, no abort | `STEP_SECONDS=20 SETTLE_SECONDS=5 RATES=1,2` |
  | `soak` | `ramping-vus`: 2 min to `PAIRS`, hold `HOLD_MINUTES` (30), 1 min down; `PAIRS` is required (throw if absent); thresholds global (`steps:[null]`, no abort) | all, no abort | `PAIRS=2 HOLD_MINUTES=1 RAMP_SECONDS=10` |
  | `up-down` | `ramping-vus`: 0 -> `PAIRS` over `RAMP_MINUTES` (5), hold `HOLD_MINUTES` (5), -> 0 over 5, hold 5 at zero; `PAIRS` required; segments `up`,`hold`,`down`,`idle` tagged `phase`-style via the stepper (`settle 0`); thresholds global | none abort | `PAIRS=2 RAMP_MINUTES=0.25 HOLD_MINUTES=0.25` (about 60 s) |
  | `default-limits` | `constant-vus`, `vus: 20` pairs, `duration: '3m'` (`DURATION`); `expectCodes(['RATE_LIMIT_EXCEEDED'])`; thresholds `{'tb_errors{expected:false}':['count==0'], 'tb_errors{code:RATE_LIMIT_EXCEEDED}':['count>0'], 'tb_errors{code:http_5xx}':['count==0']}`; does **not** provision (the stock limiters forbid registration beyond 3 per hour) | those three | `VUS=4 DURATION=60s` |

  Each reads its parameters from `__ENV` with the defaults shown, builds `levels`/`segments` once at module
  level, and sets `stepper.configure(...)`. Ramp stage lists are
  `levels.flatMap(p => [{target:p, duration:`${ramp}s`}, {target:p, duration:`${step-ramp}s`}])` with
  `ramp = Math.min(10, Math.floor(STEP_SECONDS/4))`. `gracefulRampDown: '30s'`, `gracefulStop: '60s'`.
  `setup` is `loginAll(2 * maxPairs)`; `soak`, `up-down` and `default-limits` log in only the users they
  need. `default-limits` logs in with a small `LOGIN_PARALLEL` (2) because the public tier is live.

- [ ] **Step 4: Generator-bound check.** `loadtest/sample-generator.sh <run-dir>`: loops until
  `<run-dir>/exit-code` exists. Every 5 s it appends `epoch,k6_cpu_pct,vm_cpu_pct,load1` to
  `samples.csv`: `k6_cpu_pct` is the delta of `utime+stime` ticks (fields 14 and 15 of
  `/proc/<pid>/stat`, `CLK_TCK` 100) of `pgrep -n -x k6` over the interval, as a percentage of **one**
  core (so 4 cores can reach 400); `vm_cpu_pct` is the busy share of the first line of `/proc/stat`;
  `load1` the first field of `/proc/loadavg`. Every third sample it appends
  `epoch,pod,cpu_m,mem_mi` rows from `kubectl top pods --no-headers` to `pods.csv`.
  `loadtest/check-generator.sh <samples.csv> <start_epoch> <segment_seconds> <k6_cores> [settle_seconds=20]`
  prints one line per segment, `segment N: k6 mean X% of Y% -> generator-bound` or `-> ok`, using the mean of
  samples in the segment after the settle window and the limit `0.8 * k6_cores * 100`. Test it on a synthetic
  input in `loadtest/test/check-generator-selftest.sh`:
  ```bash
  printf '%s\n' '1000,100,10,1.0' '1005,100,10,1.0' '1010,100,10,1.0' '1065,330,50,6.0' '1070,340,50,6.0' '1075,335,50,6.0' > /tmp/syn.csv
  bash loadtest/check-generator.sh /tmp/syn.csv 1000 60 4 5
  ```
  Expected two lines: `segment 1: k6 mean 100% of 320% -> ok` and
  `segment 2: k6 mean 335% of 320% -> generator-bound` (the selftest script asserts both with `grep`).

- [ ] **Step 5: `run.sh`.** Two subcommands (the plan's long-run mechanism):
  - `loadtest/run.sh start <scenario> [VAR=value …]` creates
    `loadtest/results/$(date +%Y%m%d-%H%M%S)-<scenario>/`, writes `params.txt` (the `VAR=value` pairs and
    the date), runs `preflight.sh`, captures `cluster.txt` (`docker info` CPUs and memory,
    `kubectl get nodes -o wide`, `kubectl top nodes`, `helm get values turnbase`,
    `git submodule status`, `git rev-parse HEAD`, `cat ~/.wslconfig` or `wslconfig: absent`,
    `k6 version`), ensures `kubectl port-forward svc/turnbase-prometheus 9090:9090` is running (start one in
    the background if `curl -s localhost:9090/-/ready` fails), then in the background:
    ```bash
    ulimit -n "$(ulimit -Hn)"                       # 1,024 sockets is not enough for 2,000 players
    cores=$(( $(nproc) >= 12 ? 4 : 2 )); first=$(( $(nproc) - cores ))
    ( K6_PROMETHEUS_RW_SERVER_URL=http://localhost:9090/api/v1/write \
      K6_PROMETHEUS_RW_TREND_STATS='p(50),p(95),p(99),max,count' K6_PROMETHEUS_RW_PUSH_INTERVAL=5s \
      nohup taskset -c "$first-$(( $(nproc) - 1 ))" k6 run -o experimental-prometheus-rw \
        --summary-export "$DIR/summary.json" $(for kv in "${VARS[@]}"; do printf -- '-e %s ' "$kv"; done) \
        loadtest/scenarios/<scenario>.js > "$DIR/k6.log" 2>&1
      echo $? > "$DIR/exit-code"; date +%s > "$DIR/end.epoch" ) &
    date +%s > "$DIR/start.epoch"; bash loadtest/sample-generator.sh "$DIR" &
    ```
    and prints `RUN_DIR=<dir>`. It returns at once.
  - `loadtest/run.sh wait <run-dir> [seconds=280]` polls for `exit-code` every 5 s; prints the last
    non-empty line of `k6.log` and exits `0` when the file exists (also printing its content), `124` after
    the budget. Exit code `99` (thresholds crossed) is a normal finished run; `run.sh` never treats it as
    failure.
  The raw output is `summary.json` plus the Prometheus samples, not a per-sample JSON stream: a 30-minute
  1,000-pair run emits hundreds of millions of samples. Say so in the README.

- [ ] **Step 6: `steps-table.sh` and `snapshot.sh`.**
  `loadtest/steps-table.sh <summary.json>` writes `steps.csv` (`segment,metric,count,p95,p99,pass`)
  from the `tb_*{step:…}` entries of the `--summary-export` file with `jq`. **Inspect one real summary
  first** (`jq 'keys' summary.json; jq '.metrics | keys[:20]' summary.json`) and adapt the filter to the
  schema k6 2.2.0 emits for sub-metrics and thresholds; the CSV columns are the contract, the `jq` is not.
  `loadtest/snapshot.sh <run-dir>` reads `start.epoch`/`end.epoch`, and for each PromQL in the list in
  *Run protocol* runs `curl -s --data-urlencode "query=…" --data-urlencode "start=…" --data-urlencode
  "end=…" --data-urlencode "step=15" http://localhost:9090/api/v1/query_range` into `prom/<name>.json`;
  then prints per segment (segment length from `params.txt` `STEP_SECONDS`, default 120) the mean and
  maximum of each series' values as a markdown table. It also appends to `cluster.txt` the output of
  `kubectl get pods -o json | jq -r '.items[] | [.metadata.name, ([.status.containerStatuses[]?.restartCount]|add), ([.status.containerStatuses[]?|.lastState.terminated.reason // empty]|join(","))] | @tsv'`
  (restarts and `OOMKilled`) and `redis-cli INFO memory` / `INFO clients` from the Redis pod
  (`used_memory_human`, `connected_clients`). A series that does not exist is printed as `n/a` and listed
  under `Missing metrics:` (never silently dropped).

- [ ] **Step 7: `TEMPLATE.md`.** Create `loadtest/reports/TEMPLATE.md`. Every field the run fills reads
  `FILL`; constants are written out. Sections and fields, in this order:
  1. `# <scenario> report, <date>` and one-line verdict (`FILL`).
  2. **Run**: scenario, parameters (`params.txt`), start and end (UTC), duration, k6 exit code, k6 version,
     k6 pinned to CPUs `FILL`, run directory.
  3. **Environment**: Docker Desktop VM CPUs `FILL`, memory `FILL` (from `docker info`), `.wslconfig`
     `FILL` (content or "absent"), host load during the run `FILL` (`samples.csv` mean and max of `load1`,
     `vm_cpu_pct`), root commit `FILL`, one line per submodule SHA `FILL` (6 lines), image IDs `FILL`,
     chart values `FILL` (the `helm get values turnbase` block), pod resources (the overlay table, or the
     halved one), `ingress path: ingress-nginx -> frontend nginx -> platform`.
  4. **Thresholds**: the §6 table with a `Target` column (constants), `Observed p95`, `Observed p99` and
     `Pass` columns (`FILL`), including the error-rate row and the capacity rows (500 concurrent sessions,
     5,000 WebSockets: `reached` / `not reached` / `not attempted` plus the limiting factor).
  5. **Steps**: the `steps.csv` table, one row per step, with moves/s, `tb_move_rtt` p50/p95/p99,
     `tb_game_start` warm and cold, errors by code, Game Host CPU cores, platform CPU cores, generator-bound
     (`yes`/`no`), threshold verdict.
  6. **Result**: `Ceiling (pairs): FILL` (one integer, or `<n> (not reached)` when no step failed;
     defined as the last step all of whose thresholds passed and that is not generator-bound), `First to
     break: FILL` (exactly one of: `Game Host CPU`, `Espresso contention`, `DB pool`, `Redis`, `platform
     threads`, `ingress / frontend nginx`, `k6 itself`, `memory (OOM)`, `none`), `Evidence: FILL`.
  7. **Server side**: the snapshot tables (Game Host and platform CPU, heap, threads, GC, Hikari, HTTP
     p95/p99, 5xx rate, active WebSockets/rooms/sessions, Redis memory and clients at start and end,
     restarts and `OOMKilled`), `Missing metrics: FILL`.
  8. **Errors by code**: table (`FILL`).
  9. **Findings**: bullets, each with numbers and the suspected cause (`FILL`; "none" is a valid fill).
  10. **Constants**, written verbatim in the template and never edited:
      - "This is a single-node, laptop ceiling: Docker Desktop Kubernetes on one WSL2 VM shared with the
        load generator. It is the ceiling of this machine, not of the platform."
      - "Latency is measured per request from a closed-loop client at the configured think time, so
        coordinated omission applies: when the system slows, the client issues fewer requests and the
        percentiles understate the delay a constant-rate client would see. `start-rate` is open-loop."
      - "One step is generator-bound when the k6 process averages more than 80% of its pinned cores after
        the settle window; such a step never counts as the platform's breaking point."
      - "The first `SETTLE_SECONDS` of every step are excluded from that step's thresholds."
  `loadtest/check-report.sh <report.md>` exits 1 and lists the line numbers while any line contains
  the literal `FILL` or while a required heading is missing; it exits 0 and prints `REPORT COMPLETE`
  otherwise. Run it on the template: expected exit 1 with many `FILL` lines (the check works).

- [ ] **Step 8: Overlay equality.** Create `loadtest/helm/values-default-limits.yaml` as a copy of
  `values-loadtest.yaml` without the `SPRING_PROFILES_ACTIVE` entry (and without
  `observability.prometheus.remoteWriteReceiver`, so the chart is as `values-local` would render; the
  remote-write flag is harmless but the point is "limiters on"). `loadtest/test/check-overlays.sh` diffs
  the two files and asserts the only differences are those two keys (`diff <(grep -v …) …`), exit 0 on
  success.

- [ ] **Step 9: Run every scenario at minimum size.** For each row of the table:
  ```bash
  bash loadtest/run.sh start <scenario> <min-params…>
  bash loadtest/run.sh wait loadtest/results/<dir> 280     # repeat on 124
  cat loadtest/results/<dir>/exit-code                      # expected 0
  grep -E 'tb_errors|tb_games_completed|checks' loadtest/results/<dir>/k6.log | tail -5
  ```
  Expected: exit-code `0`, `tb_errors` at `0` (`default-limits`: no `expected:false` errors, at least one
  `RATE_LIMIT_EXCEEDED`, no `http_5xx`), `tb_games_completed` positive, each run at most two minutes.
  `default-limits` first needs the stack redeployed: `bash loadtest/install.sh --default-limits`, the run,
  then `bash loadtest/install.sh` and `bash loadtest/preflight.sh` to restore. Run `steps-table.sh` and
  `snapshot.sh` once on the `ramp-to-break` directory and fix the `jq`/PromQL until the tables print.
  Delete the minimum-size run directories afterwards (they are git-ignored; do not leave 2-minute data
  that a later reader could mistake for a baseline): `rm -rf loadtest/results/*`.

- [ ] **Step 10: Abort proof.**
  ```bash
  bash loadtest/run.sh start ramp-to-break THRESHOLD_SCALE=0.001 STEP_SECONDS=20 SETTLE_SECONDS=5 START_PAIRS=2 STEP_PAIRS=2 MAX_PAIRS=10
  bash loadtest/run.sh wait <dir> 120; cat <dir>/exit-code; grep -ci 'threshold' <dir>/k6.log
  ```
  Expected: the run ends within 60 s of starting traffic, `exit-code` is `99`, the log names a crossed
  threshold. A run that finishes all steps with exit 0 means the thresholds are not step-tagged (Review
  Focus 1): fix `metrics.js`, not the expected value.

- [ ] **Step 11: README and close.** Fill the README *Scripts* section (one line per script, the
  `start`/`wait` pair, the sampling files). `bash -n loadtest/*.sh loadtest/test/*.sh`;
  `bash loadtest/test/check-generator-selftest.sh` and `bash loadtest/test/check-overlays.sh` exit 0;
  `python3 scripts/check-corpus.py` `clean`; register `DONE`; STATUS.md; merge `--ff-only`, push, delete.
  `LOOP_STATUS: DONE IMP-M15-09`.

---

## Task 10 — IMP-M15-10 `contexts` scenario (droppable)

**Repo:** `turnbase` (umbrella). **Files:** `loadtest/scenarios/contexts.js`,
`loadtest/lib/bundles.sh` (builds the copies), and either README text (built) or an edit to
`docs/specs/deployment/load-testing.md` §5 (dropped).

The scenario spreads sessions of the same game over several `gameId`/version pairs, so that the Game Host
holds several Espresso contexts (one per `{gameId}:{gameVersion}`). Four bundle copies, 50 pairs, 5 minutes.
The manifest has **no** `gameId`: a game's id is the upload's identity (the URL
`POST /api/games/{gameId}/versions`, and the seed file name), so a copy needs a new id, and may need a
rewritten `version`.

- [ ] **Step 0: Claim, branch** `feat/m15-10-contexts`, preflight, read `bundle-format.md` and
  `local-environment.md` §6.

- [ ] **Step 1: Pick the route.** Try in this order and stop at the first that yields a playable game:
  1. **Upload API** as a developer-role user: create a game record, then `POST
     /api/games/{newGameId}/versions` with the copied zip (manifest `version` edited to `1.0.<k>`,
     `title` suffixed with `<k>`), poll the version to `ACTIVE`. Read `bundle-format.md` and
     `catalog-rest-api.md` for the exact request shapes; do not guess them.
  2. **Seeder directory:** copy the zip to `<newGameId>.zip` (a fresh UUID each) into the seed directory
     and restart the platform (the seeder skips already-seeded games).
  The copies are made by `loadtest/lib/bundles.sh <k>`: unzip the seed bundle into a temp directory, edit
  `manifest.json` with `jq`, re-zip. The copies are test artifacts, not committed.

- [ ] **Step 2: Decide.** If a copy is accepted and a room can be created with the new `gameId` and a game
  played to `GAME_OVER` by hand (a one-off `k6 run` of the smoke with `-e GAME_ID=<id>`), the scenario is
  **built**. If every route is refused by the bundle identity rules (signature, ownership, catalog
  moderation, unique title), the scenario is **dropped**: add to `load-testing.md` §5 under *`contexts`:
  late and droppable* one paragraph, "Dropped on <date> by `IMP-M15-10`: <route tried>, refused with
  `<exact validation error text and HTTP status>`", delete any half-written `contexts.js`, and skip to Step 5.
  Dropping is a valid, complete outcome; do not weaken a safety rule to avoid it.

- [ ] **Step 3 (built): the scenario.** `contexts.js`: `setup()` prepares the four ids (reads them from
  `CONTEXT_IDS`, comma separated, filled by `bundles.sh`/the upload route; each must be a playable game)
  and logs in `2 * PAIRS` users. `constant-vus`, `vus: PAIRS` (50), `duration: '5m'`; pair `i` plays
  `ids[i % 4]` (the pair loop takes `gameId` as an option: add `opts.gameId` to `pairSession`, default
  `cfg.gameId`). Thresholds `thresholds({steps:[null]})`, no abort. Minimum size:
  `PAIRS=4 DURATION=60s CONTEXT_IDS=<four ids>`.

- [ ] **Step 4 (built): prove the spread.** After the minimum run, show at least two contexts live on the
  host: `kubectl exec statefulset/turnbase-redis -- sh -c 'redis-cli -a "$TURNBASE_REDIS_PASSWORD" keys "*session*"'`
  is not the proof; use the Game Host's own signal: its log (`kubectl logs deploy/turnbase-gamehost | grep -i context`)
  naming at least two distinct `gameId:version` keys. Record the command and its output in the README.

- [ ] **Step 5: Close.** README *Scenarios* row (built) or the dropped paragraph (done in Step 2);
  `python3 scripts/check-corpus.py` `clean`; register `DONE` either way; STATUS.md; merge, push, delete.
  `LOOP_STATUS: DONE IMP-M15-10`.

---

## Run protocol

These are **measurement items**: nothing in `turnbase-*`, the chart, `loadtest/helm/*.yaml` or the
scenarios changes because a number is bad. A bad number is a result. The only permitted harness edit is a
fix for a harness failure (below). The item is `DONE` when every report exists, is committed and passes
`bash loadtest/check-report.sh`.

### One run, start to finish (every scenario follows this)

- [ ] **R1. Reset and install.** `bash loadtest/reset.sh`, then `bash loadtest/install.sh` (it is a no-op
  upgrade when nothing changed; for `default-limits` it is `install.sh --default-limits`, and it is
  restored to `install.sh` after), then `bash loadtest/preflight.sh` (expected `PREFLIGHT OK`). If any pod is `Pending` for insufficient
  memory (`kubectl get pods`, `kubectl describe pod <pod>` shows `Insufficient memory`), report `BLOCKED`
  with that `kubectl describe` output; do not lower the limits in `values-loadtest.yaml` or anywhere else.
- [ ] **R2. Provision** (not for `default-limits`, which reuses the users provisioned after the reset):
  `k6 run loadtest/scenarios/provision.js 2>&1 | grep tb_provision_created` -> `2000`.
  For `default-limits`: reset, install the loadtest overlay, provision, then
  `install.sh --default-limits` (the DB survives the upgrade), preflight, then run.
- [ ] **R3. Start and poll.** `bash loadtest/run.sh start <scenario> <VAR=value…>`; note `RUN_DIR`. Then
  loop `bash loadtest/run.sh wait <RUN_DIR> 280`, emitting `LOOP_PHASE: testing <scenario> <elapsed>`
  after each return, until it returns 0. Between polls do nothing else that touches the cluster.
- [ ] **R4. Collect.** `bash loadtest/steps-table.sh <RUN_DIR>/summary.json`,
  `bash loadtest/check-generator.sh <RUN_DIR>/samples.csv $(cat <RUN_DIR>/scenario.epoch) <STEP_SECONDS> <cores>`,
  `bash loadtest/snapshot.sh <RUN_DIR>`. Read `<RUN_DIR>/k6.log` for `dropped_iterations` and for the
  line that names an aborted threshold.
- [ ] **R5. Report.** `cp loadtest/reports/TEMPLATE.md loadtest/reports/$(date +%F)-<scenario>.md` and fill
  every `FILL` from the run directory (`cluster.txt` has the SHAs, VM size, chart values, restarts).
  Judge **what broke first** with the evidence order: generator-bound flag first (a generator-bound step
  cannot be the platform's), then Game Host CPU near its 4-core limit, then a flat Game Host CPU with flat
  throughput (Espresso contention: take a thread dump of the Game Host at the plateau step with
  `kubectl exec deploy/turnbase-gamehost -- jcmd 1 Thread.print` in a **separate re-run of that step only**,
  paste the relevant 30 lines), `hikaricp_connections_pending`, Redis `used_memory`/`connected_clients`,
  platform thread count and CPU, `OOMKilled` restarts, then ingress/frontend nginx (errors with
  `502/504` and idle pods). Then `bash loadtest/check-report.sh <report>` -> `REPORT COMPLETE`.
- [ ] **R6. Clean up.** `bash loadtest/reset.sh` leaves the stack empty. Keep `loadtest/results/`
  (git-ignored) until the item closes.

A run that **fails for harness reasons** (the k6 script throws, a parser misses a frame, `steps-table.sh`
jq breaks, the generator check mis-parses) is fixed in the same item: edit only under `loadtest/`, commit it
separately as `fix(loadtest): …`, document the fix and the discarded run under **Findings** in the report
("harness fix: …"), and rerun from R1. A run that fails because **the system under test** failed (pods
crash, errors above the threshold, the platform stops answering) is a result: finish R4 to R6, record it.
If the system is so broken that `reset.sh` cannot restore it (`PREFLIGHT` still failing after two resets),
that is `BLOCKED` with the failing command named.

### PromQL for the snapshot (Prometheus at `localhost:9090`, jobs `platform` and `gamehost`)

`snapshot.sh` holds this list verbatim; names are the Micrometer defaults. Before the first run, confirm
each exists with `curl -s localhost:9090/api/v1/label/__name__/values | jq -r '.data[]' | grep -c <name>`;
a missing one is printed as `n/a`, listed under *Missing metrics*, and never replaced by a guess.

| Name | Expression |
|---|---|
| `gamehost_cpu_cores` | `max(process_cpu_usage{job="gamehost"}) * max(system_cpu_count{job="gamehost"})` |
| `platform_cpu_cores` | `max(process_cpu_usage{job="platform"}) * max(system_cpu_count{job="platform"})` |
| `gamehost_heap_bytes` | `sum(jvm_memory_used_bytes{job="gamehost",area="heap"})` |
| `platform_heap_bytes` | `sum(jvm_memory_used_bytes{job="platform",area="heap"})` |
| `gamehost_threads` | `max(jvm_threads_live_threads{job="gamehost"})` |
| `platform_threads` | `max(jvm_threads_live_threads{job="platform"})` |
| `gamehost_gc_seconds_per_s` | `sum(rate(jvm_gc_pause_seconds_sum{job="gamehost"}[1m]))` |
| `platform_gc_seconds_per_s` | `sum(rate(jvm_gc_pause_seconds_sum{job="platform"}[1m]))` |
| `http_p95_seconds` | `histogram_quantile(0.95, sum by (le) (rate(http_server_requests_seconds_bucket{job="platform"}[1m])))` |
| `http_p99_seconds` | `histogram_quantile(0.99, sum by (le) (rate(http_server_requests_seconds_bucket{job="platform"}[1m])))` |
| `http_5xx_per_s` | `sum(rate(http_server_requests_seconds_count{job="platform",status=~"5.."}[1m]))` |
| `http_req_per_s` | `sum(rate(http_server_requests_seconds_count{job="platform"}[1m]))` |
| `hikari_active` | `max(hikaricp_connections_active{job="platform"})` |
| `hikari_pending` | `max(hikaricp_connections_pending{job="platform"})` |
| `ws_connections` | `sum(turnbase_websocket_connections_active)` |
| `rooms_active` | `sum(turnbase_rooms_active)` |
| `sessions_active` | `sum(turnbase_game_sessions_active)` |
| `up` | `up` |

k6's own series arrive through the remote-write output as `k6_tb_*`. The authoritative k6 numbers are the
`summary.json` percentiles, not these; the Prometheus copies are for the Grafana view only.

### `IMP-M15-11` — parallelism and ramp-to-break

1. Runs, in this order, each with the full R1 to R6:
   - `parallelism` with the defaults (levels 1 to 256, 120 s each, about 19 minutes): start/wait.
   - `ramp-to-break` with the defaults (start 10 pairs, +10 per step, 120 s, max 1,000, abort on a failed
     threshold). It ends at the first failing step, or after 100 steps (3 h 20 min) if nothing fails. If it
     reaches step 30 (300 pairs) with everything passing, let it run: the polling loop is the cost.
2. `parallelism` report, beyond the template: a table of moves/s (= `count(tb_move_rtt{step:L}) /
   (STEP_SECONDS - SETTLE_SECONDS)`) against Game Host CPU cores per step, and one of three sentences:
   "moves/s scaled roughly linearly until Game Host CPU saturated at <step>", "moves/s plateaued at <step>
   with Game Host CPU at <x> of 4 cores (something serialises)", or "generator-bound from <step>: not
   conclusive". For the plateau case, the thread dump from R5.
3. `ramp-to-break` report: `Ceiling (pairs): <n>` as the template defines it, **what broke first**, and the
   two capacity statements: 500 concurrent sessions (= 500 pairs; compare `sessions_active` at the ceiling
   step) and 5,000 WebSockets. 5,000 sockets need 2,500 pairs and 1,000 pairs is the provisioned maximum,
   so the WebSocket target is measured by **idle sockets**: after the ramp, run
   `PAIRS=1000 bash loadtest/run.sh start soak HOLD_MINUTES=2 THINK_MIN_MS=600000 THINK_MAX_MS=600000`
   is *not* enough (2,000 sockets). Record honestly: "reached up to 2,000 sockets (1,000 pairs), the
   remaining 3,000 not attempted: no provisioned users" unless the ceiling is below 1,000 pairs, in which
   case state the ceiling in sockets (`2 x ceiling`) and the limiting factor. Do not extrapolate.
4. Findings: every degradation (a step that failed, a 5xx, a restart, an OOM kill, a plateau) becomes a
   bullet in the report's **Findings** and an entry in `load-testing.md` §13 (format below).
5. Close: `git diff --stat origin/master` lists only `loadtest/reports/`, `docs/specs/deployment/load-testing.md`,
   `STATUS.md`, `docs/implementation/registry.md` (and, if a harness fix was needed, `loadtest/**` in its own
   commit, named in the report). Anything else listed: stop and revert it. Register `DONE`, STATUS.md
   replaced, `python3 scripts/check-corpus.py` `clean`, merge `--ff-only`, push, delete the branch.
   `LOOP_STATUS: DONE IMP-M15-11`.

### `IMP-M15-12` — start-rate, default-limits, contexts

1. Prerequisite: `IMP-M15-10` is DONE (built or dropped) and the `IMP-M15-11` reports exist. Read the `ramp-to-break` ceiling for context only; these
   scenarios do not depend on it.
2. `start-rate` with the defaults (1, 2, 4, 8, 16, 32 games/s, 120 s each, about 12 minutes; start/wait
   anyway for the 280 s poll cap). Report: the highest rate whose step passed *and* shows no
   `dropped_iterations` in its window (`Ceiling (pairs)` line reads `Ceiling (games/s): <n>` in this
   report; `check-report.sh` accepts either), `tb_game_start` p95 and p99 warm and cold separately, and
   whether `game_start` degraded before `move_rtt` did.
3. `default-limits`: the full R1/R2 sequence in the order of R2 above, `DURATION=3m`, 20 pairs. Report:
   the number of `RATE_LIMIT_EXCEEDED` (from `tb_errors{code:RATE_LIMIT_EXCEEDED}`), which mechanism
   rejected (HTTP API/public tier or WebSocket bucket: read the platform log's `RATE_LIMIT` lines with
   `kubectl logs deploy/turnbase-platform --since=15m | grep -ci rate`), and whether **anything else**
   broke (`tb_errors{expected:false}`, 5xx, restarts). Restore the loadtest overlay afterwards.
4. `contexts`: if `IMP-M15-10` was *built*, run it with the 50 pairs and 5 minutes of the defaults; the
   report compares its moves/s and `move_rtt` with the `parallelism` step at 50 to 64 pairs and says whether
   spreading sessions over four contexts changed throughput. If `IMP-M15-10` was *dropped*, no run is
   attempted: add one line to the report index (the `SUMMARY.md` in `IMP-M15-13`; until then a line in the
   `start-rate` report's *Findings*): "`contexts` not run: dropped by `IMP-M15-10`, reason in
   `load-testing.md` §5."
5. Findings and §13 entries as in `IMP-M15-11`; the same close-out diff check.
   `LOOP_STATUS: DONE IMP-M15-12`.

### `IMP-M15-13` — soak, up-down and the Phase A summary

Prerequisite: the `IMP-M15-11` and `IMP-M15-12` reports exist (the `ceiling` below reads the `ramp-to-break` report).

1. Derive the load: `ceiling=$(grep -m1 '^Ceiling (pairs):' loadtest/reports/*-ramp-to-break.md | grep -o '[0-9]\+' | head -1)`
   and `PAIRS=$(( ceiling * 7 / 10 ))` (at least 1). Record both figures in each report.
2. `soak`: R1/R2, then `bash loadtest/run.sh start soak PAIRS=$PAIRS HOLD_MINUTES=30`. It runs about 33
   minutes: poll every 280 s. Before and after (the load phase boundaries), `snapshot.sh` writes the
   values the report needs: Game Host and platform heap, thread count, Redis `used_memory` and
   `connected_clients`, Hikari active, `ws_connections`. Report: the load used (the arithmetic), those
   values at the start of the hold and at its end, and the trend (a growth of more than 20% in heap after
   GC, threads, Redis memory or clients across the hold is a leak suspect and a Finding).
3. `up-down`: R1/R2, then `run.sh start up-down PAIRS=$PAIRS` (5 + 5 + 5 + 5 minutes, defaults). Report:
   whether heap, threads, Redis memory and clients, `ws_connections`, `rooms_active` and `sessions_active`
   returned to the values taken before the ramp, after the zero-load hold, each as a number pair.
4. `loadtest/reports/SUMMARY.md` (register it in no INDEX: it is under `loadtest/`, not `docs/`): one page
   with a table linking the six or seven reports; three answers, each in two to four sentences with
   numbers: (a) the worst-case load (the ceiling, the first thing to break), (b) behaviour as load rises and
   falls (the `parallelism`, `soak` and `up-down` conclusions), (c) where it breaks and why; a capacity table
   (500 concurrent sessions, 5,000 WebSockets: `reached` / `not reached` with the limiting factor); the
   single-node statement; and the list of every §13 entry with a link.
5. `load-testing.md` §13: below the Follow-ups list add `### Phase A results` (five lines: date, ceiling,
   what broke first, capacity targets, link to `loadtest/reports/SUMMARY.md`). Follow-ups entries, one per
   degradation, in this format, appended in report order:
   ```
   - **<short title>** (`loadtest/reports/<file>.md`). Symptom: <numbers>. Suspected cause: <one sentence>.
     Not checked: <what would confirm it>.
   ```
   Replace the `_No entries yet._` line when the first entry is added. Findings are never registry items.
6. Delete this plan: `git rm docs/implementation/m15-test-definition-plan.md`, remove its row from
   `docs/implementation/INDEX.md`, `python3 scripts/check-corpus.py` `clean`.
7. Close: the same diff check as `IMP-M15-11` (plus the two deletions); register `DONE` for `IMP-M15-13`;
   STATUS.md replaced with the Phase A outcome and "Phase B has its own design round" as the next
   priority; merge, push, delete the branch. `LOOP_STATUS: DONE IMP-M15-13`.

---

## Self-review checklist (the session that writes this plan, already applied)

- [x] Every registry *Done when* clause for `07…13` maps to a step (07: Steps 2 to 13; 08: Steps 6 to 9;
  09: Steps 3 to 11; 10: Steps 2 to 5; 11 to 13: the protocol).
- [x] Every decision in the orchestrator's list appears as fixed text; deviations are numbered above.
- [x] Interfaces named in later tasks are declared in *Shared interfaces* (`stepper`, `thresholds`,
  `loginAll`, `pairSession`, `getPair`, `expectCodes`, `Player`, `StompClient`).
- [x] No step relies on an unverified k6 feature: `k6/websockets` headers, per-player cookie jar,
  `exec.scenario.startTime`, `ramping-arrival-rate`, per-step sub-metric thresholds with `abortOnFail` and
  `experimental-prometheus-rw` were all exercised against k6 2.2.0 during planning. Not exercised: the
  `--summary-export` sub-metric schema (Task 9, Step 6 inspects it) and `options.hosts` for WebSocket
  upgrades (Task 7 and `HOST_IP`).
