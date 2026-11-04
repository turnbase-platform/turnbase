# Archive — M15 Load and scalability testing, Phase A

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim by `IMP-M20-01`. Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M15-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M15-01 | Load-testing spec groundwork | docs | — | DONE |
| IMP-M15-02 | Recon spec defects filed | docs | M15-01 | DONE |
| IMP-M15-03 | Toggleable rate-limiting mechanisms | platform | M15-01 | DONE |
| IMP-M15-04 | HTTP latency histograms | platform | M15-01 | DONE |
| IMP-M15-05 | Configurable Game Host advertised address | game-host | M15-01 | DONE |
| IMP-M15-06 | Game Host runs under the Helm chart | platform (chart), docs | M15-03, M15-04, M15-05 | DONE |
| IMP-M15-07 | Load-test scaffold: overlay, reset, user provisioning | platform (chart), docs (umbrella) | M15-06 | DONE |
| IMP-M15-08 | k6 STOMP client and pair game loop | docs (umbrella) | M15-07 | DONE |
| IMP-M15-09 | Load scenarios, thresholds and report template | docs (umbrella) | M15-08 | DONE |
| IMP-M15-10 | `contexts` scenario (droppable) | docs (umbrella) | M15-09 | DONE |
| IMP-M15-11 | Phase A runs — parallelism and ramp-to-break | docs (umbrella) | M15-09 | DONE |
| IMP-M15-12 | Phase A runs — start-rate, default-limits, contexts | docs (umbrella) | M15-10, M15-11 | DONE |
| IMP-M15-13 | Phase A runs — soak, up-down and Phase A summary | docs (umbrella) | M15-11, M15-12 | DONE |

---

## M15 — Load and scalability testing, Phase A

Opened 2026-10-18 from [`load-testing.md`](../../specs/deployment/load-testing.md): the owner wants to know
how much the platform carries in the worst case, how it behaves as load rises and falls, and where it
breaks, focused on room creation, game start and player actions. Phase A measures what exists on one
Docker Desktop Kubernetes node, with one Platform instance and one Game Host; Game Host autoscaling is
Phase B and gets its own design round.

**Sequencing (owner decision).** Blockers first (`01…06`: spec changes, the toggleable rate limits, the
latency histograms, the Game Host's address and the chart that runs it), then the test definition
(`07…10`: scaffold, harness, scenarios), then the runs and their reports (`11…13`). The order to build in
is `01` → `02`, `03`, `04`, `05` → `06` → `07` → `08` → `09` → `10` → `11` → `12`, `13`. The test definition and the run protocol were in `m15-test-definition-plan.md`,
deleted by the session that closed `13`; the harness is documented in `loadtest/README.md`.

**Measurement only (owner decision).** `11…13` produce committed reports stating where and why the
system breaks. They do not fix what they find: no code, chart or overlay change, and a bad number is a
result, not a failure. Each degradation goes into the run's report and into
[`load-testing.md`](../../specs/deployment/load-testing.md) §13 *Follow-ups*; the owner prioritises those
afterwards. A run item never adds a registry item.

**Live-environment items (`06…13`).** These need Docker Desktop's Kubernetes running. Each starts with a
preflight (`06`: the plan's Step 0; `07` onwards: `loadtest/preflight.sh`, which `07` creates). A missing
`values-local.secrets.yaml` is generated from its example (it is git-ignored) and is not a blocker. A
cluster that is down is `BLOCKED`, naming the failed command, after re-running it once live. A command
that will run longer than eight minutes runs in the background and is polled at most every five
minutes, because the loop's stall warning fires after 15 minutes without output and one shell call is
capped at ten. See `work-item` *Live-environment and measurement items*.

**Owner decisions.** `02` records two spec conflicts that need an owner's choice. Recording is the whole
of that item; it is `DONE` when recorded and it never reports `BLOCKED` for want of the decision.

### IMP-M15-01 — Load-testing spec groundwork

**Repo:** `turnbase` (docs) · **Depends on:** nothing

**Read first:**
- `docs/implementation/m15-blockers-plan.md`, Task 1 (its property-name table is authoritative)
- `docs/specs/deployment/load-testing.md` §4 (A0, A1, A1a), §7, §11
- `docs/specs/api-design/rate-limiting.md` (*Tier 6*, *Configuration and environments*)
- `docs/specs/deployment/local-environment.md` §7.6, §7.8, §8 (the paragraph beginning "E2E runs with")
- `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` (*Addressing the Game Host pods*)
- `docs/specs/deployment/observability.md` (*Exposure*)
- `docs/requirements/platform-operations.md` (*Related Documents*, the NFR table) and `docs/requirements/INDEX.md`

**Satisfies:** `platform-operations.md` FR-MET-001 (the latency histogram it already requires); the
four `NFR-LOAD` requirements this item defines

**Done when:**
- **Switches specified.** `grep -oh 'turnbase\.rate-limit\.\(ws\.\)\?switches\.[a-z-]*' docs/specs/api-design/rate-limiting.md | sort -u | wc -l`
  prints `14`, and the same command on `docs/specs/deployment/local-environment.md` prints `14`. Each is
  described as defaulting to `true`.
- **Profile rule specified.** `grep -n 'loadtest' docs/specs/api-design/rate-limiting.md docs/specs/deployment/local-environment.md`
  matches in both files. Both say the master switch or any per-mechanism switch may be off only under
  `test`, `e2e` or `loadtest`, that `local` alone does not permit it, and that the refusal names every
  disabled switch. `local-environment.md` §8's e2e paragraph no longer says only the master switch.
- **Master switch scope stated.** `rate-limiting.md` *Tier 6* says the master switch gates the WebSocket
  limits as well as Tiers 1 to 5.
- **Game Host address specified.** `grep -ln 'advertised-address' docs/specs/internal-grpc/orchestration-gamehost-protocol.md docs/specs/deployment/local-environment.md`
  lists both. Both give the four-step resolution order, say the chart sets it from the pod IP, and say an
  IPv6 literal must be given bracketed with its port (`[fd00::1]:9090`) and a bare one is unsupported.
- **Metrics specified.** `grep -n 'percentile' docs/specs/deployment/observability.md` matches in
  *Exposure*, which states the 5 ms and 30 s bounds.
- **New NFRs.** `grep -c 'NFR-LOAD-00[1-4]' docs/requirements/platform-operations.md` prints at least
  `4`; `docs/requirements/INDEX.md` lists `NFR-LOAD` under that document's *Defines*; `load-testing.md`
  §7 and that document link each other.
- `python3 scripts/check-corpus.py` prints `clean`.

### IMP-M15-02 — Recon spec defects filed

**Repo:** `turnbase` (docs) · **Depends on:** IMP-M15-01

**Read first:**
- `docs/specs/deployment/load-testing.md` §11 (*Known spec defects found during recon*)
- `.claude/skills/spec-defect/SKILL.md`
- `docs/specs/flows/03-game-turn.md` (step 3) and `docs/specs/internal-grpc/gamehost.proto` (`ProcessInput`)
- `docs/specs/game-host/game-host-internals.md` §9.3 and §18 (*Open questions*)
- `turnbase-platform/src/main/java/io/turnbase/platform/game/GameInputService.java` (where a dead host is reassigned)
- `docs/requirements/platform-operations.md` (NFR-AVAIL-001, *Open Questions*) and `docs/requirements/platform-architecture.md` (NFR-AVAIL-001, *Open Questions*)
- `docs/specs/deployment/INDEX.md`, `docs/specs/deployment/local-environment.md` §2 and §4
- `STATUS.md` (*Last Session Summary*, "Not done / open")

**Done when:**
- **`SubmitInput` is fixed.** `grep -rn 'SubmitInput' docs/specs` prints nothing.
- **`kind` claim is fixed.** `docs/specs/deployment/INDEX.md` and `local-environment.md` §4 state that no
  CI job applies the chart to a `kind` cluster; `grep -n 'kind. cluster' docs/specs/deployment/*.md`
  finds no sentence claiming one exists.
- **`STATUS.md` is fixed.** It no longer says the Kubernetes manifests do not exist.
- **Reassignment is recorded, not decided.** `game-host-internals.md` §18 has a new `OQ-5` stating
  that §9.3 describes eager reassignment on lease expiry while the code reassigns lazily on the next
  input, naming both readings and the file that implements the lazy one. §9.3 gains one sentence
  pointing at `OQ-5`. **The agent does not choose a side and does not edit the code.**
- **NFR-AVAIL-001 is recorded, not decided.** `platform-operations.md` *Open Questions* has a new
  `OQ-004` stating 99% there against 99.9% in `platform-architecture.md`, and `platform-architecture.md`
  *Open Questions* has a new `OQ-004` pointing at it. Neither table row is changed.
- `python3 scripts/check-corpus.py` prints `clean`.

**How the two records differ from a gate.** An open question in a spec's *Open questions* section is the
`spec-defect` skill's record for a defect that waits on the owner. It is not a `Gate:` line and the row
is not `BLOCKED`: no other item depends on either answer. Do not open a gate for them, and do not report
`BLOCKED`. The item is `DONE` when the five records above exist.

### IMP-M15-03 — Toggleable rate-limiting mechanisms

**Repo:** `turnbase-platform` · **Depends on:** IMP-M15-01

**Read first:**
- `docs/implementation/m15-blockers-plan.md`, Task 2
- `docs/specs/api-design/rate-limiting.md` (*Tier 6*, *Configuration and environments*, as amended by `IMP-M15-01`)
- `docs/specs/deployment/local-environment.md` §7.6
- `turnbase-platform/src/main/java/io/turnbase/platform/common/` : `RateLimitProperties.java`, `RateLimitInterceptor.java`, `RateLimitEnabledProfileCheck.java`
- `turnbase-platform/src/main/java/io/turnbase/platform/websocket/` : `WebSocketRateLimitProperties.java`, `WebSocketRateLimiter.java`, `WebSocketChannelInterceptor.java`
- `turnbase-platform/src/main/resources/application.yml` (`turnbase.rate-limit`)
- `docs/decisions/0014-modular-monolith-spring-modulith.md` (`common` must not depend on `websocket`)

**Satisfies:** `user-accounts.md` NFR-SEC-003 (the auth limits stay on by default; the new switches
are guarded by the profile rule)

**Done when:**
- **Switches exist and default on.** `./mvnw test -Dtest=ConfigurationDefaultsTest` passes, asserting
  all 14 switches are `true` through the real `application.yml`.
- **Effective rule.** A mechanism acts only when the master `turnbase.rate-limit.enabled` and its own
  switch are both `true`. `./mvnw test -Dtest='WebSocketRateLimiterTest'` passes with
  `disabledMasterSwitchAllowsEveryFrame`.
- **Each gate is honoured.** The plan's Task 2 test names all pass: a disabled HTTP tier admits without
  consuming a token or arming a refund (`RateLimitInterceptorIT`); a disabled WebSocket bucket allows its
  frames; a disabled violation lockout never force-closes or writes a lockout and `isLockedOut` is
  `false`; a disabled connection cap admits more than the cap (`WebSocketChannelInterceptorTest`).
- **Safety rule.** `./mvnw test -Dtest=RateLimitEnabledProfileCheckTest` passes: a switch off under
  `local` or no profile throws `IllegalStateException` whose message contains every disabled property
  name; under `test`, `e2e` or `loadtest` it does not.
- **`loadtest` profile.** `./mvnw test -Dtest=ConfigurationDefaultsTest` also passes `loadtestProfileTurnsEverySwitchOffExceptTheConnectionCap`: with `local,loadtest` every
  switch is `false` except `turnbase.rate-limit.ws.switches.max-connections-per-user`, and the master
  switch is `true`.
- `./mvnw spotless:apply`, `./mvnw verify` and `./mvnw verify -Pintegration` are green (this includes
  `ModularityTest`); the branch is merged `--ff-only`, pushed and deleted; the `turnbase-platform` ref is
  bumped.

### IMP-M15-04 — HTTP latency histograms

**Repo:** `turnbase-platform` · **Depends on:** IMP-M15-01

**Read first:**
- `docs/implementation/m15-blockers-plan.md`, Task 3
- `docs/specs/deployment/observability.md` (*Exposure*, as amended by `IMP-M15-01`)
- `turnbase-platform/src/main/resources/application.yml` (`management.metrics`)
- `turnbase-platform/src/test/java/io/turnbase/platform/ActuatorLoggersAccessTest.java` (the test style to copy)

**Satisfies:** `platform-operations.md` FR-MET-001; `platform-operations.md` FR-ALERT-002 (`HighLatencyP95`
can finally be evaluated)

**Done when:**
- `grep -n 'percentiles-histogram' turnbase-platform/src/main/resources/application.yml` shows
  `http.server.requests: true` with minimum 5 ms and maximum 30 s alongside, outside any profile block.
- `./mvnw test -Dtest=HttpLatencyHistogramTest` passes.
- `./mvnw verify -Pintegration` passes, including `HttpLatencyHistogramIT`, which finds an
  `http_server_requests_seconds_bucket{` line with an `le="` label on the management port.
- `./mvnw spotless:apply` run; branch merged `--ff-only`, pushed and deleted; the `turnbase-platform` ref bumped.

### IMP-M15-05 — Configurable Game Host advertised address

**Repo:** `turnbase-game-host` · **Depends on:** IMP-M15-01

**Read first:**
- `docs/implementation/m15-blockers-plan.md`, Task 4
- `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` (*Addressing the Game Host pods*, as amended by `IMP-M15-01`)
- `docs/specs/deployment/local-environment.md` §7.8
- `turnbase-game-host/src/main/java/io/turnbase/gamehost/` : `GameHostProperties.java`, `registration/RegistrationLifecycle.java`
- `turnbase-game-host/src/test/java/io/turnbase/gamehost/GameHostPropertiesTest.java`

**Satisfies:** `platform-architecture.md` FR-REG-001 (the address the host advertises is dialable)

**Done when:**
- `./mvnw test -Dtest=AdvertisedAddressTest` passes: configured value with `:` verbatim; without `:`
  plus `:` and the gRPC port; blank or absent gives the host name and port; an unresolvable host name
  gives `localhost:` and the port.
- `./mvnw test -Dtest=GameHostPropertiesTest` passes with the `null` default and an explicit binding.
- A bare IPv6 literal is not handled, as `local-environment.md` §7.8 says; no test asserts otherwise.
- `./mvnw spotless:apply`, `./mvnw verify` and `./mvnw verify -Pintegration` are green; branch merged
  `--ff-only`, pushed and deleted; the `turnbase-game-host` ref bumped.

### IMP-M15-06 — Game Host runs under the Helm chart

**Repo:** `turnbase-platform` (chart), `turnbase` (docs) · **Depends on:** IMP-M15-03, IMP-M15-04, IMP-M15-05

**Environment:** a live Docker Desktop Kubernetes cluster. Missing secrets are generated, not a blocker;
a cluster that is down is `BLOCKED`.

**Read first:**
- `docs/specs/deployment/load-testing.md` §3.1, §4 (A0, A1)
- `docs/specs/deployment/local-environment.md` §4, §5, §6, §7.8
- `docs/specs/deployment/observability.md` (*Exposure*)
- `turnbase-platform/deploy/helm/turnbase/` : `values.yaml`, `values-local.yaml`, `values-local.secrets.example.yaml`, `templates/gamehost-*.yaml`, `templates/platform-{configmap,deployment}.yaml`, `templates/observability/prometheus.yaml`
- `.claude/skills/run-turnbase/driver.mjs`

**Satisfies:** `platform-architecture.md` FR-REG-001 (a Game Host registers under Kubernetes);
`platform-operations.md` FR-MET-007 (Prometheus scrapes the services)

**Done when:**
- **Chart is valid.** `helm lint turnbase-platform/deploy/helm/turnbase -f …/values-local.yaml -f …/values-local.secrets.yaml`
  exits 0 and `helm template` passes the plan's Step 8 greps: the Game Host Secret holds exactly the
  Redis password and the scoped artifact-store pair; the Game Host Deployment sets
  `TURNBASE_GAMEHOST_ADVERTISED_ADDRESS` from `status.podIP`; both Deployments render `extraEnv`;
  the remote-write flag appears only when enabled.
- **Origins.** `grep -n 'origins' -A3 turnbase-platform/deploy/helm/turnbase/values-local.yaml` shows no `:8080`.
- **Live.** `kubectl get pods` shows every pod `Running` and ready; `redis-cli smembers hosts` prints one
  host id whose `host:<id>` hash has `address` `<pod IP>:9090` (the set holds ids, not addresses; corrected session 207);
  `PLATFORM_HOST=turnbase.localhost PLATFORM_URL=http://turnbase.localhost node .claude/skills/run-turnbase/driver.mjs game`
  exits 0; Prometheus `/api/v1/targets` lists the platform and Game Host jobs `up`; the query
  `http_server_requests_seconds_bucket` returns a series.
- `local-environment.md`'s Helm install section holds the commands that were run, with the seed path flag.
- `python3 scripts/check-corpus.py` prints `clean`; `turnbase-platform` branch merged `--ff-only`,
  pushed and deleted; the `turnbase-platform` ref bumped; `docs/implementation/m15-blockers-plan.md` and
  its `INDEX.md` row deleted.

**Evidence (session 207).** Chart lint and render greps clean; `kubectl get pods` all Running/ready;
`host:<id>` `address` `10.1.3.217:9090` equals the Game Host pod IP; the driver's `game` scenario exited 0
(start 3.8 s, moves 35 to 316 ms, spectator `ROLE_NOT_ELIGIBLE`, outsider 0 frames); Prometheus lists
`platform` and `gamehost` `up` and `http_server_requests_seconds_bucket` returns 295 series.

### IMP-M15-07 — Load-test scaffold: overlay, reset, user provisioning

**Repo:** `turnbase-platform` (chart: Postgres and Redis resources), `turnbase` (umbrella: `loadtest/`) · **Depends on:** IMP-M15-06

**Environment:** a live Docker Desktop Kubernetes cluster with the `IMP-M15-06` install. This item
creates `loadtest/preflight.sh` first and runs it; later items start with it. Missing secrets are
generated, not a blocker; a cluster that is down is `BLOCKED`.

**Read first:**
- `docs/implementation/m15-test-definition-plan.md`, *Task 7 — IMP-M15-07*
- `docs/specs/deployment/load-testing.md` §4 (A1, A2), §8 (*Run procedure*, reset)
- `turnbase-platform/deploy/helm/turnbase/` : `values-local.yaml`, `values.yaml` (`extraEnv`, `resources`), `templates/postgres-statefulset.yaml`, `templates/redis-statefulset.yaml`
- `turnbase-platform/Makefile` (`reset-db`)
- `.claude/skills/run-turnbase/driver.mjs` (how the stack is addressed)

**Satisfies:** none (test tooling)

**Done when:**
- **Chart values exist.** `grep -n 'resources' turnbase-platform/deploy/helm/turnbase/values.yaml` shows
  `postgres.resources` and `redis.resources`, and the plan's Step 3 `helm template … | grep -c 'cpu: "\?[12]"\?'`
  prints at least `2`; `helm lint` exits 0 with the local values and secrets.
- `bash loadtest/preflight.sh` exits 0 on a ready cluster and non-zero, naming the failed check, otherwise.
- `loadtest/helm/values-loadtest.yaml` installs on top of `values-local`: `helm get values turnbase`
  shows `SPRING_PROFILES_ACTIVE=local,loadtest`, one platform replica without autoscaling, one Game Host
  replica, and requests equal to limits on the platform (3Gi), Game Host (4Gi), Postgres (1Gi) and
  Redis (512Mi); `kubectl get pods` shows none `Pending`.
- The platform log shows the `loadtest` profile active and no `RateLimitEnabledProfileCheck` failure.
- Provisioning creates 2,000 `lt-*` users: a second run reports 0 created, and a login for `lt-00001` returns 200.
- `bash loadtest/reset.sh` empties the stack (`SELECT count(*) FROM app_user WHERE username LIKE 'lt-%'`
  returns 0 and `redis-cli dbsize` is no more than the seed's) and provisioning then works again.
- `loadtest/README.md` documents the run procedure, the reset and the `.wslconfig` recommendation.
- `python3 scripts/check-corpus.py` prints `clean`; the `turnbase-platform` chart branch is green, merged
  `--ff-only`, pushed and deleted, its ref bumped; the umbrella branch merged to `master` and pushed.

### IMP-M15-08 — k6 STOMP client and pair game loop

**Repo:** `turnbase` (umbrella; nothing to bump) · **Depends on:** IMP-M15-07

**Environment:** live cluster; run `bash loadtest/preflight.sh` first.

**Read first:**
- `docs/implementation/m15-test-definition-plan.md`, *Task 8 — IMP-M15-08*
- `docs/specs/deployment/load-testing.md` §3.5, §3.6, §4 (A3)
- `.claude/skills/run-turnbase/driver.mjs` (a working STOMP exchange to port)
- `docs/specs/api-design/websocket.md` (frames and destinations the plan names)

**Satisfies:** none (test tooling)

**Done when:**
- `k6 run` of the `smoke` scenario (one pair, three games, a rematch and a fresh room) exits 0 with
  `errors` at 0 and `games_completed` at 3 or more.
- The k6 end-of-test summary lists every custom metric in `load-testing.md` §4 (A3):
  `login`, `room_create`, `room_join`, `lobby_event`, `game_start`, `move_rtt`, `game_duration`,
  `games_completed`, `errors`, `ws_disconnects`.
- After the run, `bash loadtest/reset.sh` is not needed for the next run to start: the VU's defensive
  cleanup left no `lt-*` user in a room (`SELECT count(*) FROM room_participant rp JOIN app_user u ON u.user_id = rp.user_id WHERE u.username LIKE 'lt-%' AND rp.left_at IS NULL`
  returns 0; table names corrected session 209).
- `python3 scripts/check-corpus.py` prints `clean`; merged to `master` and pushed.

### IMP-M15-09 — Load scenarios, thresholds and report template

**Repo:** `turnbase` (umbrella; nothing to bump) · **Depends on:** IMP-M15-08

**Environment:** live cluster; run `bash loadtest/preflight.sh` first. Scenario checks are short
(about two minutes each); the full runs belong to `IMP-M15-11…13`.

**Read first:**
- `docs/implementation/m15-test-definition-plan.md`, *Task 9 — IMP-M15-09*
- `docs/specs/deployment/load-testing.md` §5, §6, §8, §10
- `loadtest/README.md` and the `loadtest/` scripts `IMP-M15-08` produced

**Satisfies:** none (test tooling)

**Done when:**
- Each of `ramp-to-break`, `soak`, `up-down`, `parallelism`, `start-rate` and `default-limits` starts under
  `k6 run` with its minimum-size parameters (the plan lists them), runs for no more than two minutes, and
  exits 0 with `errors` at 0; `default-limits` additionally records at least one `RATE_LIMIT_EXCEEDED`.
- The §6 threshold set is encoded; a deliberately impossible threshold (`THRESHOLD_SCALE=0.001`)
  makes `ramp-to-break` abort and exit non-zero.
- A step where k6 uses more than 80% of its available CPU is flagged `generator-bound` in the output
  (the plan's check script prints it on a synthetic input).
- `loadtest/reports/TEMPLATE.md` has every field `load-testing.md` §8 lists, including the
  single-node-ceiling statement, the `.wslconfig` cap and the coordinated-omission note.
- `python3 scripts/check-corpus.py` prints `clean`; merged to `master` and pushed.

**Evidence (session 210).** Selftest 31 of 31 checks (stepper and threshold cases). Each scenario at its minimum size exited 0 with `tb_errors` at 0 and ran 49 to 84 s: `parallelism`, two `ramp-to-break` runs, `start-rate`, `soak`, `up-down`; `default-limits` (after `install.sh --default-limits`) exited 0 with 20 `RATE_LIMIT_EXCEEDED`, `expected:false` and `http_5xx` at 0. `THRESHOLD_SCALE=0.001` aborted `ramp-to-break` after 31 s with exit 99. `check-generator-selftest.sh` and `check-overlays.sh` exit 0; `check-report.sh` exits 1 on `TEMPLATE.md`. Harness fixes found live: `install.sh` now removes the application pods before an upgrade (a rolling update needs a second 4-CPU platform pod and hung `Insufficient cpu`); a `ready_timeout` race on the room subscription (`SUBSCRIBE_SETTLE_MS`); `up-down` runs its zero-load hold as a sleeping VU because k6 drops a trailing zero-VU stage; `scenario.epoch` (from the `TB_SETUP_DONE` log line) is the start of step 1, not `start.epoch`.

### IMP-M15-10 — `contexts` scenario (droppable)

**Repo:** `turnbase` (umbrella; nothing to bump) · **Depends on:** IMP-M15-09

**Environment:** live cluster; run `bash loadtest/preflight.sh` first.

**Read first:**
- `docs/implementation/m15-test-definition-plan.md`, *Task 10 — IMP-M15-10*
- `docs/specs/deployment/load-testing.md` §5 (*`contexts`: late and droppable*)
- `docs/specs/manifest/bundle-format.md` and `docs/specs/deployment/local-environment.md` §6 (bundle identity and the upload pipeline)

**Done when:** exactly one of these holds, and the item is `DONE` either way:
- **Built.** The scenario starts under `k6 run` with minimum parameters and the sessions it creates spread
  over at least two `gameId`/version pairs (`redis-cli` or the report shows distinct contexts per host).
- **Dropped.** The test-only bundle copy was refused by the bundle identity rules, and
  `load-testing.md` §5 records the refusal, quoting the validation error. `IMP-M15-12` then runs no
  `contexts` scenario.
- `python3 scripts/check-corpus.py` prints `clean`; merged to `master` and pushed.

**Evidence (session 211).** Built. Route: the seeder directory. `loadtest/lib/bundles.sh 4` made four copies (fresh UUID, `title` suffixed, `version` 1.0.1 to 1.0.4); after `reset.sh` the platform logged `Seeded official game <id> version 1.0.<k>` for each and all four `game_version` rows were `ACTIVE`. `k6 run` of `contexts.js` with `PAIRS=4 DURATION=60s` exited 0, `tb_errors` 0, 2,105 games in 60 s, and `kubectl logs deploy/turnbase-gamehost | grep 'Game context created'` printed four lines with four distinct `gameId`/`gameVersion` pairs. `pairSession` takes `gameId` (default `cfg.gameId`). The copies were removed from the seed directory and the stack reset afterwards.

### IMP-M15-11 — Phase A runs — parallelism and ramp-to-break

**Repo:** `turnbase` (umbrella; nothing to bump) · **Depends on:** IMP-M15-09

**Environment:** live cluster, fresh `loadtest/reset.sh` before each scenario. Measurement only. Any
run longer than eight minutes goes in the background, polled at most every five minutes with a
`LOOP_PHASE` line each time. A bad number is a result.

**Read first:**
- `docs/implementation/m15-test-definition-plan.md`, *Run protocol* (its *R1 to R6* steps and its `IMP-M15-11` section)
- `docs/specs/deployment/load-testing.md` §5 (`parallelism`), §6, §8, §12, §13
- `loadtest/README.md` and `loadtest/reports/TEMPLATE.md`

**Satisfies:** `platform-architecture.md` NFR-SCALE-001 and `platform-operations.md` NFR-PERF-003, as
measured: reached or not reached, with the limiting factor

**Done when:**
- `ls loadtest/reports/*-parallelism.md loadtest/reports/*-ramp-to-break.md` lists one committed report
  each, every template field filled, the commit SHAs of every submodule and the chart values recorded.
- The `parallelism` report states, with the moves/s and Game Host CPU per step, whether throughput
  scaled or plateaued, and where it plateaued if so.
- The `ramp-to-break` report states the ceiling (the last passing step), what broke first, and whether
  the 500-concurrent-sessions and 5,000-WebSocket targets were reached, each with the limiting factor.
- Every degradation is an entry in `load-testing.md` §13. `git diff --stat` for the session touches
  only `loadtest/reports/`, `load-testing.md`, `STATUS.md` and the registry.
- `python3 scripts/check-corpus.py` prints `clean`; merged to `master` and pushed.

### IMP-M15-12 — Phase A runs — start-rate, default-limits, contexts

**Repo:** `turnbase` (umbrella; nothing to bump) · **Depends on:** IMP-M15-10, IMP-M15-11 (`10` is `DONE` whether built or dropped)

**Environment:** as `IMP-M15-11`.

**Read first:**
- `docs/implementation/m15-test-definition-plan.md`, *Run protocol* (its *R1 to R6* steps and its `IMP-M15-12` section)
- `docs/specs/deployment/load-testing.md` §5 (`start-rate`, `default-limits`, `contexts`), §6, §8, §13
- `loadtest/reports/` : the `IMP-M15-11` reports, for the ceiling and the report shape

**Satisfies:** `NFR-LOAD` warm game start target, as measured (the requirements `IMP-M15-01` defines)

**Done when:**
- `ls loadtest/reports/*-start-rate.md loadtest/reports/*-default-limits.md` lists one committed report
  each. The `start-rate` report states the highest passing arrival rate and `game_start` p95 and p99,
  warm and cold separately. The `default-limits` report counts the `RATE_LIMIT_EXCEEDED` responses and
  states whether anything else broke.
- If `IMP-M15-10` built the scenario, `loadtest/reports/*-contexts.md` exists and says whether sessions
  spread over contexts changed throughput against `parallelism`. If `IMP-M15-10` dropped it, no
  `contexts` run is attempted and the report index says so.
- Every degradation is an entry in `load-testing.md` §13; no code, chart or overlay file changed.
- `python3 scripts/check-corpus.py` prints `clean`; merged to `master` and pushed.

**Evidence (session 213).** Three reports, each `check-report.sh` `REPORT COMPLETE`, each run on a fresh `reset.sh` stack with no code, chart or overlay change. `start-rate`: 1 to 32 games/s, no threshold crossed, warm `game_start` p95 11 to 16 ms and p99 13 to 18 ms (35 / 43 ms in one stalled step), cold first start 4.95 s; ceiling 16 games/s, because the 32 games/s step lost 146 iterations and had 54 `ready_timeout` in a 15 s stall; no resource near its limit, so the degradation rate was not reached. `default-limits`: 320 `RATE_LIMIT_EXCEEDED`, one per iteration, 0 unexpected errors, 0 5xx, HTTP tiers never fired. `contexts`: attempt 1 failed (Game Host wedged on its first start with four contexts, health 503, never restarted, 0 games in 357 s), the rerun was clean: 810 moves/s against 909 and 897 in `parallelism`, move p95 58 ms, warm start p95 66 ms, Game Host CPU 2.95 cores against 0.99 for one context. `load-testing.md` §13 gained items 7 to 12. `IMP-M15-13` uses `jcmd 7` for thread dumps.

### IMP-M15-13 — Phase A runs — soak, up-down and Phase A summary

**Repo:** `turnbase` (umbrella; nothing to bump) · **Depends on:** IMP-M15-11, IMP-M15-12

**Environment:** as `IMP-M15-11`. The soak holds for as long as the plan says (over an hour is expected):
background it, poll at most every five minutes.

**Read first:**
- `docs/implementation/m15-test-definition-plan.md`, *Run protocol* (its *R1 to R6* steps and its `IMP-M15-13` section)
- `docs/specs/deployment/load-testing.md` §5 (`soak`, `up-down`), §8, §12, §13
- `loadtest/reports/` : the `ramp-to-break` report (its ceiling sets the soak load at about 70%)

**Satisfies:** none (the owner's questions: leaks, release of resources, behaviour as load falls)

**Done when:**
- `ls loadtest/reports/*-soak.md loadtest/reports/*-up-down.md` lists one committed report each. The soak
  report gives the load used (70% of the ceiling, with the figure), and heap, thread count, Redis memory
  and connection counts at the start and end. The up-down report states whether those returned to their
  starting values after the load fell to zero.
- `loadtest/reports/SUMMARY.md` answers the owner's three questions (worst-case load, behaviour as load
  rises and falls, where it breaks) from the six reports, and marks the capacity targets reached or not
  reached with the limiting factor.
- `load-testing.md` §13 holds every degradation from `IMP-M15-11…13`; `SUMMARY.md` links each.
- `docs/implementation/m15-test-definition-plan.md` and its `INDEX.md` row are deleted.
- `python3 scripts/check-corpus.py` prints `clean`; merged to `master` and pushed.

**Evidence (session 214).** `soak` (49 pairs = 70 x 7 / 10, 30 min hold): every target met, no restart; Redis 3.18 -> 13.75 MB (86,271 keys), platform threads 125 -> 151, Game Host heap after GC 251 -> 371 MB, HTTP p95 10 -> 48 ms with requests per second down 25%, and a loss of ownership of about 35 rooms at 17.5 min after which `rooms_active` stayed doubled. `up-down` (attempt 1 lost to a Game Host wedge on its first cold start, attempt 2 clean): sockets, rooms, sessions and Hikari back to 0 within 30 s; platform threads 57 -> 109 and Redis 1.77 -> 6.91 MB (36,047 keys, two per room) not released. `SUMMARY.md` answers the three questions; neither capacity target was reached (about 55 sessions, 140 sockets at the ceiling). `load-testing.md` §13 items 13 to 18 and *Phase A results* added; the test-definition plan is deleted.
