# M15 Blockers Implementation Plan

> **Working file, deleted once spent** (CLAUDE.md, *Working files are deleted once spent*). It
> carries `IMP-M15-01…06`, the items that must land before any load test can be measured; the
> registry's *Done when* clauses stay authoritative, this file only orders the steps. Steps use
> checkbox (`- [ ]`) syntax.

**Goal:** make the platform and the Helm chart measurable: every rate-limiting mechanism
independently switchable under a guarded profile, HTTP latency histograms, a Game Host that
advertises a dialable address, and a chart that runs the Game Host and a Prometheus that scrapes both
services.

**Architecture:** spec first (Task 1), then three independent code changes in three repositories
(Tasks 2, 3, 4, any order or in parallel), then the chart (Task 5), which consumes the other three
through built images. No new module, no new dependency. Everything below is existing Spring Boot
configuration, one existing `ApplicationRunner`, one extracted method and Helm templates.

**Tech Stack:** Java 21, Spring Boot 4.1, Jackson 3 (`tools.jackson`), Bucket4j, Micrometer, JUnit 5 +
AssertJ, Helm 3, Docker Desktop Kubernetes.

**Spec:** [`docs/specs/deployment/load-testing.md`](../specs/deployment/load-testing.md) §3.1, §3.2,
§3.3, §4 (A0, A1, A1a), §7, §11.

---

## Global Constraints

- Java 21; Spring Boot 4.1; host-side JSON is Jackson 3 (`tools.jackson`). No new dependency.
- `./mvnw spotless:apply` before every commit in a Java repository; the build fails on
  unformatted code.
- Every Java task ends with `./mvnw test` and `./mvnw verify -Pintegration` green in its repository.
- One branch per repository (`feat/` + description), merged `--ff-only` into `master` and deleted,
  locally and on the remote, **in the same session**. No pull requests (ADR-0012). Commits are
  Conventional Commits (`conventions.md` §4). Submodule refs in this repository move only after the
  submodule's build and tests pass.
- Specification before code. If a step reveals that two documents disagree, stop and use the
  `spec-defect` skill; do not reconcile silently. Task 1 lands, and `python3 scripts/check-corpus.py`
  is clean, before Tasks 2 to 5 start.
- Every safety default stays as it is. A test asserts each new switch defaults to enabled; nothing in
  this plan loosens a default, a profile rule or a port exposure.

## Review Focus

Reviewers should spend their attention on:

1. **The safety rule.** Can any combination of the new switches reach a production-like boot
   (`local` alone, or no profile) with a limiter off? `RateLimitEnabledProfileCheck` is the only
   guard; read every branch of it.
2. **Gating completeness.** Each switch must gate its mechanism at every place that mechanism acts
   (admission, refund, lockout write, lockout read), or a disabled limiter still costs Redis calls or
   still closes sockets.
3. **The master switch now covers WebSocket limits.** `WebSocketRateLimitProperties`' Javadoc has
   claimed this since `IMP-M2-02`; the code never did it.
4. **Secret scoping in the chart.** The Game Host Secret must hold only the Redis password and the
   scoped artifact-store credential. Never the JWT key set, the admin pair or the database password.
5. **Defaults unchanged.** The Compose path and the stock chart behave exactly as before.

---

## Task 1: Specification groundwork (`IMP-M15-01`, `IMP-M15-02`)

**Repo:** `turnbase` (docs). **Files:**

- Modify: `docs/specs/api-design/rate-limiting.md` (*Configuration and environments*, the `properties`
  block, and the *Tier 6* note on the kill switch)
- Modify: `docs/specs/deployment/local-environment.md` (§7.6 table, §7.8 table and the paragraph
  after it, §4 item 3's `kind` claim)
- Modify: `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` (*Addressing the Game Host
  pods*)
- Modify: `docs/specs/deployment/observability.md` (*Exposure*)
- Modify: `docs/specs/deployment/INDEX.md` (the `kind` sentence on line 29)
- Modify: `docs/specs/flows/03-game-turn.md` (`SubmitInput` to `ProcessInput`)
- Modify: `docs/requirements/platform-operations.md` and `docs/requirements/INDEX.md` (new IDs)
- Modify: `STATUS.md` (the "Kubernetes manifests do not exist yet" sentence)

**Property names fixed here, used verbatim by Tasks 2, 4 and 5.**

| Property | Env | Default |
|---|---|---|
| `turnbase.rate-limit.switches.auth-lockout` | `TURNBASE_RATE_LIMIT_SWITCHES_AUTH_LOCKOUT` | `true` |
| `turnbase.rate-limit.switches.api` | `TURNBASE_RATE_LIMIT_SWITCHES_API` | `true` |
| `turnbase.rate-limit.switches.upload` | `TURNBASE_RATE_LIMIT_SWITCHES_UPLOAD` | `true` |
| `turnbase.rate-limit.switches.public` | `TURNBASE_RATE_LIMIT_SWITCHES_PUBLIC` | `true` |
| `turnbase.rate-limit.switches.guest-minting` | `TURNBASE_RATE_LIMIT_SWITCHES_GUEST_MINTING` | `true` |
| `turnbase.rate-limit.switches.registration-minting` | `TURNBASE_RATE_LIMIT_SWITCHES_REGISTRATION_MINTING` | `true` |
| `turnbase.rate-limit.ws.switches.connection` | `TURNBASE_RATE_LIMIT_WS_SWITCHES_CONNECTION` | `true` |
| `turnbase.rate-limit.ws.switches.snapshot` | `TURNBASE_RATE_LIMIT_WS_SWITCHES_SNAPSHOT` | `true` |
| `turnbase.rate-limit.ws.switches.action` | `TURNBASE_RATE_LIMIT_WS_SWITCHES_ACTION` | `true` |
| `turnbase.rate-limit.ws.switches.chat` | `TURNBASE_RATE_LIMIT_WS_SWITCHES_CHAT` | `true` |
| `turnbase.rate-limit.ws.switches.command` | `TURNBASE_RATE_LIMIT_WS_SWITCHES_COMMAND` | `true` |
| `turnbase.rate-limit.ws.switches.subscribe` | `TURNBASE_RATE_LIMIT_WS_SWITCHES_SUBSCRIBE` | `true` |
| `turnbase.rate-limit.ws.switches.violation-lockout` | `TURNBASE_RATE_LIMIT_WS_SWITCHES_VIOLATION_LOCKOUT` | `true` |
| `turnbase.rate-limit.ws.switches.max-connections-per-user` | `TURNBASE_RATE_LIMIT_WS_SWITCHES_MAX_CONNECTIONS_PER_USER` | `true` |
| `turnbase.gamehost.advertised-address` | `TURNBASE_GAMEHOST_ADVERTISED_ADDRESS` | absent |

- [ ] **Step 1: Pin what is missing.** Run
  `grep -c "switches\." docs/specs/api-design/rate-limiting.md docs/specs/deployment/local-environment.md`
  and `grep -c "advertised-address" docs/specs/deployment/local-environment.md docs/specs/internal-grpc/orchestration-gamehost-protocol.md`.
  Expected: every count is `0`. These are the failing checks.
- [ ] **Step 2: Specify the switches.** In `rate-limiting.md` *Configuration and environments* add the
  fourteen `switches` keys above to the `properties` block with one sentence each on what the switch
  turns off. State the effective rule: a mechanism acts only when the master
  `turnbase.rate-limit.enabled` and its own switch are both `true`. In the *Tier 6* section replace
  the "single kill switch" wording: the master switch gates Tier 6 too, and each bucket, the violation
  lockout and the connection cap also have their own. In `local-environment.md` §7.6 add the same
  keys and the rule, and add `loadtest` beside `test` and `e2e`.
- [ ] **Step 3: Specify the profile rule.** Both documents state: with the master switch or any
  switch off, the application starts only when `test`, `e2e` or `loadtest` is active; `local` alone
  does not permit it; the refusal message names every disabled switch by property name. Define the
  `loadtest` profile in §7.6: it turns every switch off except
  `turnbase.rate-limit.ws.switches.max-connections-per-user` and leaves the master switch on, and it
  is never activated by default.
- [ ] **Step 4: Specify the advertised address.** In `orchestration-gamehost-protocol.md` *Addressing
  the Game Host pods* and `local-environment.md` §7.8 add `turnbase.gamehost.advertised-address` and
  its resolution order: configured value verbatim when it contains `:`; configured value plus
  `:` and `grpc.port` when it does not; the local host name plus the port when blank or absent;
  `localhost:` plus the port when the host name does not resolve. Say the chart sets it from the pod
  IP.
- [ ] **Step 5: Specify the metrics.** In `observability.md` *Exposure* state that
  `http.server.requests` publishes percentile histograms with a 5 ms minimum and 30 s maximum
  expected value, and that the Helm Prometheus carries the two-job scrape config shown there (the
  chart does not have it today; `IMP-M15-06` adds it).
- [ ] **Step 6: Define the NFRs.** In `platform-operations.md` add `NFR-LOAD-001` (warm game start,
  p95 < 1 s and p99 < 2 s, cold start recorded and not gated), `NFR-LOAD-002` (`move_rtt` p99 <
  500 ms), `NFR-LOAD-003` (non-game HTTP p99 < 500 ms), `NFR-LOAD-004` (lobby event p99 < 600 ms),
  priority Should, each linking `load-testing.md` §7, and add the Related Documents link. Add
  `NFR-LOAD` to that document's *Defines* cell in `docs/requirements/INDEX.md`. Confirm first with
  `grep -rn "NFR-LOAD\b" docs/` that the prefix is unused; `FR-LOAD-*` is the Game Host's artifact
  loading and is a different prefix.
- [ ] **Step 7: File the recon defects (`IMP-M15-02`).** Replace `SubmitInput` with `ProcessInput` in
  `flows/03-game-turn.md` step 3 and anywhere else `grep -rn SubmitInput docs/specs` finds it
  (`local-environment.md` §2 line 148 included). Reword the `kind` sentences in
  `deployment/INDEX.md` and `local-environment.md` §4 item 3 to say no such job exists yet. Fix the
  `STATUS.md` sentence (the chart exists; the Game Host half has never run under it until
  `IMP-M15-06`). Run the `spec-defect` skill for the two owner decisions (eager versus lazy
  reassignment in `game-host-internals.md` §9.3; 99% versus 99.9% `NFR-AVAIL-001`) and record them
  without resolving them.
- [ ] **Step 8: Verify.** `python3 scripts/check-corpus.py` is clean, and the Step 1 greps now
  return non-zero counts.
- [ ] **Step 9: Commit.** `docs(specs): rate-limit switches, advertised address, load NFRs`; merge
  `--ff-only` and delete the branch.

---

## Task 2: Toggleable rate-limiting mechanisms (`IMP-M15-03`)

**Repo:** `turnbase-platform`. **Files**, all under `src/main/java/io/turnbase/platform/` unless
stated:

- Modify: `common/RateLimitProperties.java`, `common/RateLimitInterceptor.java`,
  `common/RateLimitEnabledProfileCheck.java`
- Modify: `websocket/WebSocketRateLimitProperties.java`, `websocket/WebSocketRateLimiter.java`,
  `websocket/WebSocketChannelInterceptor.java`
- Modify: `src/main/resources/application.yml`
- Create: `src/main/resources/application-loadtest.yml`
- Tests, under `src/test/java/io/turnbase/platform/`: modify `common/RateLimitEnabledProfileCheckTest`,
  `common/RateLimitInterceptorIT`, `websocket/WebSocketRateLimiterTest`,
  `ConfigurationDefaultsTest`, and whichever existing test drives `CONNECT` through
  `WebSocketChannelInterceptor`; create `LoadtestProfileTest`

**Design notes.**

- Add a nested `Switches` record to each properties class with `@DefaultValue("true")` booleans
  named as in Task 1, and mark the `switches` component `@DefaultValue` so a YAML without the key
  binds all-true. Give each `Switches` a static `allEnabled()` so the test fixtures that construct the
  records by hand (`RateLimitEnabledProfileCheckTest.properties`, `WebSocketRateLimiterTest.newLimiter`)
  change by one argument.
- `common` must not depend on `websocket` (Spring Modulith, ADR-0014; `websocket` already depends on
  `common`). So the profile check reads the switch keys from the `Environment`, not from the typed
  records, and keeps one `List<String>` of the fourteen keys. `WebSocketRateLimiter` takes
  `RateLimitProperties` for the master flag.
- Gates, in the order a request meets them. `RateLimitInterceptor.classify` returns `null` for a
  disabled tier, and it must do so for `upload` and `public` separately: a disabled `upload` tier
  must not fall through to `api`. `preHandle` skips `admitAuthAttempt` when `auth-lockout` is off and
  `consumeMintingToken` when the matching minting switch is off; with no attribute set,
  `afterCompletion` already refunds nothing. In `WebSocketRateLimiter.checkFrame`, skip
  `consume(..., "connection", ...)` and each class bucket when its switch is off, and make
  `onViolation` never reach `writeLockout` or `ForceClose` when `violation-lockout` is off (it
  returns the ordinary `Drop`). `isLockedOut` returns `false` when `violation-lockout` is off, so a
  lockout key left by an earlier run cannot refuse a connection. The connection cap is bypassed in
  `WebSocketChannelInterceptor` (around the `registry.tryRegister(..., maxConnectionsPerUser())` call)
  when `max-connections-per-user` is off.

- [ ] **Step 1: Write the failing tests.**
  - `RateLimitEnabledProfileCheckTest`: `perMechanismSwitchOffFailsUnderLocalProfile` (a single
    switch off, profile `local`, expects `IllegalStateException` whose message contains that switch's
    full property name), `severalSwitchesOffAreAllNamedInTheMessage`,
    `perMechanismSwitchOffPassesUnderLoadtestProfile`, `perMechanismSwitchOffFailsWithNoProfile`,
    `masterOffStillFailsUnderLocalProfile` (the existing behaviour, kept), `allSwitchesOnPassUnderAnyProfile`.
    Build the environment with `MockEnvironment.withProperty(...)`.
  - `RateLimitInterceptorIT`: `disabledApiTierAdmitsMoreThanItsCapacity`,
    `disabledUploadTierDoesNotFallThroughToTheApiBucket`, `disabledPublicTierAdmitsMoreThanItsCapacity`,
    `disabledAuthLockoutNeverLocksOutRepeatedBadLogins` (also asserts no `rate:auth:*` key exists in
    Redis afterwards), `disabledGuestMintingDoesNotAffectRegistrationMinting` (and the converse), and
    `masterOffStillRequiresTestOrE2eOrLoadtest`. Boot with `--spring.profiles.active=test` and one
    `--turnbase.rate-limit.switches.<name>=false`, using the existing `bootApplication(String...)`
    helper and the `guest()` helper.
  - `WebSocketRateLimiterTest`: `disabledMasterSwitchAllowsEveryFrame`,
    `disabledConnectionBucketAllowsFramesThatWouldExhaustIt`,
    `disabledClassBucketAllowsItsFramesButNotOthers`,
    `disabledViolationLockoutDropsButNeverForceClosesOrWritesALockout` (verify no `set` on the
    mocked `valueOperations`), `disabledViolationLockoutMakesIsLockedOutFalseDespiteAStoredKey`.
  - `WebSocketChannelInterceptor` coverage: `disabledConnectionCapAdmitsMoreConnectionsThanTheCap`,
    in whichever existing test class already drives `CONNECT` through the interceptor.
  - `ConfigurationDefaultsTest`: extend `bindsEveryTunableToItsSection7Default` with
    `assertThat(rateLimit.switches().api()).isTrue()` and the same for all fourteen, through the real
    `application.yml`.
  - `LoadtestProfileTest` (new, `ApplicationContextRunner` with
    `ConfigDataApplicationContextInitializer` and `spring.profiles.active=local,loadtest`): every
    switch is `false` except `ws.switches.max-connections-per-user`, and the master `enabled` is
    `true`.
- [ ] **Step 2: Run, expect failure.**
  `./mvnw test -Dtest='RateLimitEnabledProfileCheckTest,WebSocketRateLimiterTest,ConfigurationDefaultsTest,LoadtestProfileTest'`.
  Expected: compilation errors or failures naming the missing `switches`.
- [ ] **Step 3: Implement.** Add the `Switches` records and the YAML keys (each as
  `${TURNBASE_RATE_LIMIT_SWITCHES_<NAME>:true}`, next to the budget it governs). Apply the gates
  described above. Rewrite `RateLimitEnabledProfileCheck.run`: collect the master key if
  `rateLimit.enabled()` is false plus every key in the list whose `Environment` value is `false`; if
  the collection is non-empty and `environment.matchesProfiles("test", "e2e", "loadtest")` is false,
  throw `IllegalStateException` starting
  `"rate limiting is disabled (" + String.join(", ", disabled) + ") but is only honoured under the test, e2e or loadtest profile (local-environment.md §7.6); active profiles: "`.
  Fix the `WebSocketRateLimitProperties` Javadoc to describe the two-level rule it now implements.
  Create `application-loadtest.yml` setting thirteen switches to `false` and leaving
  `max-connections-per-user` and the master flag alone.
- [ ] **Step 4: Run the new tests, expect green.** Same command as Step 2, then
  `./mvnw test`.
- [ ] **Step 5: Integration and module rules.** `./mvnw verify -Pintegration` (includes
  `ModularityTest`, which fails the build if `common` reached into `websocket`). Fix, never suppress.
- [ ] **Step 6: Format and commit.** `./mvnw spotless:apply`, then
  `feat(rate-limit): per-mechanism switches, loadtest profile, master switch covers Tier 6`.
  Merge `--ff-only`, delete the branch locally and on the remote.

---

## Task 3: HTTP latency histograms (`IMP-M15-04`)

**Repo:** `turnbase-platform`. **Files:**

- Modify: `src/main/resources/application.yml` (the `management.metrics` block, beside `tags`)
- Create: `src/test/java/io/turnbase/platform/HttpLatencyHistogramTest.java`
- Create: `src/test/java/io/turnbase/platform/HttpLatencyHistogramIT.java`

- [ ] **Step 1: Write the failing tests.**
  - `HttpLatencyHistogramTest.httpServerRequestsPublishesAPercentileHistogramBetween5msAnd30s`,
    in the style of `ActuatorLoggersAccessTest` (`ApplicationContextRunner` plus
    `ConfigDataApplicationContextInitializer`): binds
    `management.metrics.distribution.percentiles-histogram.http.server.requests` as `Boolean` and
    asserts `true`, and binds `...minimum-expected-value.http.server.requests` to `5ms` and
    `...maximum-expected-value.http.server.requests` to `30s`.
  - `HttpLatencyHistogramIT.prometheusEndpointExposesHttpServerRequestBuckets`, extending
    `PostgresIntegrationTest` with the boot helper `RateLimitInterceptorIT` uses and
    `--management.server.port=0` (compare `TurnBaseApplicationIT`): `GET /api/games` on the public
    port once, then `GET /actuator/prometheus` on the management port, and assert the body contains a
    line starting `http_server_requests_seconds_bucket{` that includes `le="`. Pick the public
    endpoint from the live route list rather than assuming `/api/games`.
- [ ] **Step 2: Run, expect failure.**
  `./mvnw test -Dtest=HttpLatencyHistogramTest`; the binder `get()` throws `NoSuchElementException`.
- [ ] **Step 3: Implement.** Add under `management.metrics`:
  `distribution.percentiles-histogram.http.server.requests: true`,
  `distribution.minimum-expected-value.http.server.requests: 5ms`,
  `distribution.maximum-expected-value.http.server.requests: 30s`. Keep the existing `tags` block. Add
  a one-line comment citing `observability.md` *Exposure* and `platform-operations.md` FR-MET-001.
- [ ] **Step 4: Run, expect green.** `./mvnw test`, then
  `./mvnw verify -Pintegration`.
- [ ] **Step 5: Format and commit.** `./mvnw spotless:apply`, then
  `feat(metrics): percentile histograms on http.server.requests`. Merge `--ff-only`, delete the
  branch.

---

## Task 4: Configurable Game Host advertised address (`IMP-M15-05`)

**Repo:** `turnbase-game-host`. **Files**, under `src/main/java/io/turnbase/gamehost/`:

- Modify: `GameHostProperties.java` (new last component `@Nullable String advertisedAddress`, with no
  default so it binds `null`)
- Modify: `registration/RegistrationLifecycle.java` (line 46 call site and the private
  `resolveAdvertisedAddress` near line 108)
- Create: `registration/AdvertisedAddress.java` (package-private final class, one static method
  `resolve(@Nullable String configured, int grpcPort, Supplier<String> hostName)`; the supplier
  throws `UnknownHostException` through a small functional interface, so the fourth case is testable
  without touching the real resolver)
- Modify: `src/main/resources/application.yml` (`advertised-address: ${TURNBASE_GAMEHOST_ADVERTISED_ADDRESS:}`)
- Tests, under `src/test/java/io/turnbase/gamehost/`: create `registration/AdvertisedAddressTest`;
  modify `GameHostPropertiesTest`

- [ ] **Step 1: Write the failing tests.**
  - `AdvertisedAddressTest`: `configuredValueWithAColonIsUsedVerbatim` (`"10.1.2.3:7000"`, port
    9090, expects `10.1.2.3:7000`), `configuredValueWithoutAColonGetsThePortAppended`
    (`"10.1.2.3"` gives `10.1.2.3:9090`), `blankValueFallsBackToTheHostNameAndPort`,
    `absentValueFallsBackToTheHostNameAndPort`, `unresolvableHostNameFallsBackToLocalhostAndPort`.
  - `GameHostPropertiesTest`: extend `bindsEveryTunableToItsSection78Default` with
    `assertThat(properties.advertisedAddress()).isNull()`, and add
    `bindsAnExplicitAdvertisedAddress` using `.withPropertyValues("turnbase.gamehost.advertised-address=10.0.0.9")`.
- [ ] **Step 2: Run, expect failure.** `./mvnw test -Dtest='AdvertisedAddressTest,GameHostPropertiesTest'`;
  compile error on the missing class and accessor.
- [ ] **Step 3: Implement.** Extract the body of `resolveAdvertisedAddress` into
  `AdvertisedAddress.resolve`, adding the configured-value branches ahead of the host-name fallback;
  `RegistrationLifecycle` calls it with `properties.advertisedAddress()`, the gRPC port and
  `InetAddress.getLocalHost()::getHostName`-backed supplier. Add the property to `application.yml`
  with an empty default, which the blank branch handles. Nothing else changes: Compose behaviour is
  identical because the variable is unset there.
- [ ] **Step 4: Run, expect green.** `./mvnw test`, then `./mvnw verify -Pintegration`.
- [ ] **Step 5: Format and commit.** `./mvnw spotless:apply`, then
  `feat(registration): configurable advertised address`. Merge `--ff-only`, delete the branch.

---

## Task 5: The Game Host runs under the Helm chart (`IMP-M15-06`)

**Repo:** `turnbase-platform` (the chart lives at `deploy/helm/turnbase`); the driver is in this
repository at `.claude/skills/run-turnbase/driver.mjs`. **Files**, under
`turnbase-platform/deploy/helm/turnbase`:

- Modify: `templates/gamehost-configmap.yaml`, `templates/gamehost-deployment.yaml`,
  `templates/platform-configmap.yaml`, `templates/platform-deployment.yaml`,
  `templates/observability/prometheus.yaml`, `values.yaml`, `values-local.yaml`
- Create: `templates/gamehost-secret.yaml`, `templates/observability/prometheus-configmap.yaml`
- Modify: `docs/specs/deployment/local-environment.md` (verified Helm install commands)

**Facts established by reading the chart (2026-10-18).** The Game Host Deployment has `envFrom` its
ConfigMap only: no Redis host (the image defaults to the hostname `redis`, the chart's Service is
`<release>-redis`), no Redis password, no artifact-store endpoint, bucket or credential, and the
ConfigMap sets `SPRING_PROFILES_ACTIVE=local`. Its liveness and readiness probes already exist, on
`/actuator/health/liveness` and `/actuator/health/readiness`. The platform has no `extraEnv`.
`values-local.yaml` serves origins on port 8080, but ingress-nginx on Docker Desktop listens on 80.
The Prometheus Deployment uses the image's default config (self-scrape only). `driver.mjs` already
honours `PLATFORM_HOST` and `PLATFORM_URL`.

- [ ] **Step 1: Prove the failure.** Install the unchanged chart on Docker Desktop Kubernetes with the
  git-ignored `values-local.secrets.yaml`, the platform and Game Host images built from the Task 2 to
  4 branches (`docker build -t turnbase/platform:dev .` in `turnbase-platform`, the same with
  `turnbase/game-host:dev` in `turnbase-game-host`). Expected: the Game Host pod is not Ready or the
  `hosts` set in Redis is empty
  (`kubectl exec <redis-pod> -- redis-cli -a <password> smembers hosts`, the set key is `hosts`, `HostRegistry.HOSTS`). Record the observed symptom in
  `local-environment.md`'s Helm section.
- [ ] **Step 2: Lint before changing anything.** `helm lint deploy/helm/turnbase -f deploy/helm/turnbase/values-local.yaml -f deploy/helm/turnbase/values-local.secrets.yaml`
  is clean.
- [ ] **Step 3: Game Host configuration.** In `gamehost-configmap.yaml` add
  `SPRING_DATA_REDIS_HOST: "{{ .Release.Name }}-redis"`, `SPRING_DATA_REDIS_PORT: "6379"`,
  `TURNBASE_ARTIFACT_STORE_ENDPOINT: "http://{{ .Release.Name }}-minio:9000"` and
  `TURNBASE_ARTIFACT_STORE_BUCKET: {{ .Values.minio.bucket | quote }}`, mirroring the platform's.
  Create `gamehost-secret.yaml` with exactly `SPRING_DATA_REDIS_PASSWORD`,
  `TURNBASE_ARTIFACT_STORE_ACCESS_KEY` and `TURNBASE_ARTIFACT_STORE_SECRET_KEY`, each with the same
  `required` guard the platform Secret uses. Add the `secretRef` to the Deployment's `envFrom`.
- [ ] **Step 4: Dialable address.** In `gamehost-deployment.yaml` add an `env` entry
  `TURNBASE_GAMEHOST_ADVERTISED_ADDRESS` with `valueFrom.fieldRef.fieldPath: status.podIP`. The value
  has no port, which the Task 4 resolution order completes with `grpc.port`.
- [ ] **Step 5: `extraEnv`.** Add `platform.extraEnv: []` and `gamehost.extraEnv: []` to `values.yaml`
  and render them in both Deployments' `env` with `{{- with .Values.<c>.extraEnv }}{{ toYaml . | nindent 12 }}{{- end }}`.
  Container `env` wins over `envFrom`, so this is the override hook `IMP-M15-07` uses for
  `SPRING_PROFILES_ACTIVE`.
- [ ] **Step 6: Origins.** Change `values-local.yaml` to
  `origins.platform: http://turnbase.localhost` and
  `origins.gameFrontendTemplate: "http://{gameId}.games.localhost"`. Keep the values file's comment
  explaining that ingress-nginx listens on 80.
- [ ] **Step 7: Prometheus.** Create `prometheus-configmap.yaml` with the two-job config from
  `observability.md` *Exposure*, with targets `<release>-platform:<platform.managementPort>` and
  `<release>-gamehost:<gamehost.managementPort>`; mount it in the Deployment at `/etc/prometheus`
  and pass `--config.file=/etc/prometheus/prometheus.yml`. Add
  `observability.prometheus.remoteWriteReceiver: false` to `values.yaml`; when `true`, add
  `--web.enable-remote-write-receiver` to the container `args`.
- [ ] **Step 8: Render checks.** `helm template` with the values from Step 2 and assert, by
  `grep`: the Game Host Secret contains no `JWT`, `ADMIN` or `DATASOURCE` key; the Game Host
  Deployment contains `status.podIP`; both Deployments render an `extraEnv` entry when given
  `--set 'gamehost.extraEnv[0].name=X,gamehost.extraEnv[0].value=1'`; the Prometheus args contain
  `--web.enable-remote-write-receiver` only with the flag set. Re-run `helm lint`.
- [ ] **Step 9: Verify live.** `helm upgrade --install turnbase deploy/helm/turnbase -f values-local.yaml -f values-local.secrets.yaml`,
  then confirm in this order and record the commands in `local-environment.md`: all pods Ready; the
  `hosts` set holds one member whose address is the Game Host pod IP with port `9090`;
  `node .claude/skills/run-turnbase/driver.mjs game` passes against `http://turnbase.localhost`
  (set `PLATFORM_URL`); Prometheus `/api/v1/targets` shows both jobs `up`;
  `http_server_requests_seconds_bucket` returns a series. Any failure here is a defect in the chart or
  in Tasks 2 to 4; fix it where it lives.
- [ ] **Step 10: Commit.** In `turnbase-platform`:
  `feat(helm): run the Game Host, extraEnv hook, Prometheus scrape config`; in this repository:
  `docs(deployment): verified Helm install on Docker Desktop`. Merge `--ff-only`, delete the
  branches, then move the submodule refs.
- [ ] **Step 11: Close out.** Mark `IMP-M15-01…06` `DONE` in `registry.md` with their evidence,
  replace the `STATUS.md` "Last Session Summary", run `python3 scripts/check-corpus.py`, and delete
  this file together with its row in `docs/implementation/INDEX.md`.
