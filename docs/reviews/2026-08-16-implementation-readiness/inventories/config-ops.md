# TurnBase Configuration, Operational and Deployment Surface Inventory

## Table 1 — Configuration Keys

| Key / property name | Owning service | Type | Default | What it controls | Source `file:line` |
|---|---|---|---|---|---|
| `turnbase.room.grace-period` | Platform Monolith | Duration | `60s` | Grace period for player reconnection after disconnect | local-environment.md:326 |
| `turnbase.room.migration-window` | Platform Monolith | Duration | `20s` | Time window for host migration during disconnection | local-environment.md:327 |
| `turnbase.room.idle-window` | Platform Monolith | Duration | `30m` | Idle time before a Lobby room is purged | local-environment.md:328 |
| `turnbase.room.lease.ttl` | Platform Monolith | Duration | `10s` | Time-to-live for room ownership leases | local-environment.md:329 |
| `turnbase.room.lease.renew-interval` | Platform Monolith | Duration | `3s` | Interval for renewing room ownership leases | local-environment.md:330 |
| `turnbase.room.lease.self-evict-after` | Platform Monolith | Duration | `6s` | Time before an instance evicts itself from a lease | local-environment.md:331 |
| `turnbase.jobs.deadline-sweep.interval` | Platform Monolith | Duration | `5s` | Interval for deadline sweep job execution | local-environment.md:343 |
| `turnbase.jobs.reconcile.interval` | Platform Monolith | Duration | `60s` | Interval for reconciliation job execution | local-environment.md:344 |
| `turnbase.jobs.reconcile.startup-suppression` | Platform Monolith | Duration | `120s` | Suppression window for reconciliation after startup | local-environment.md:345 |
| `turnbase.jobs.reconcile.orphan-age` | Platform Monolith | Duration | `10m` | Age threshold for orphaned session artifacts | local-environment.md:346 |
| `turnbase.jobs.guest-cleanup.interval` | Platform Monolith | Duration | `1h` | Interval for guest account cleanup job | local-environment.md:347 |
| `turnbase.jobs.notification-purge.interval` | Platform Monolith | Duration | `24h` | Interval for notification purge job | local-environment.md:348 |
| `turnbase.jobs.room-purge.interval` | Platform Monolith | Duration | `24h` | Interval for closed room purge job | local-environment.md:349 |
| `turnbase.jobs.upload-slot-cleanup.interval` | Platform Monolith | Duration | `15m` | Interval for upload slot cleanup job | local-environment.md:350 |
| `turnbase.uploads.validation-lease` | Platform Monolith | Duration | `10m` | Time window for game-version bundle validation | local-environment.md:351 |
| `turnbase.retention.closed-room` | Platform Monolith | Duration | `7d` | Retention period for closed room records | local-environment.md:361 |
| `turnbase.retention.notification` | Platform Monolith | Duration | `30d` | Retention period for notification records | local-environment.md:362 |
| `turnbase.retention.friend-request` | Platform Monolith | Duration | `30d` | Retention period for friend request records | local-environment.md:363 |
| `turnbase.retention.guest-account` | Platform Monolith | Duration | `24h` | Retention period for guest account records | local-environment.md:364 |
| `turnbase.auth.session-ttl` | Platform Monolith | Duration | `24h` | Session token lifetime (registered and guest) | local-environment.md:373 |
| `turnbase.accounts.rename-window` | Platform Monolith | Duration | `30d` | Window for account name changes | local-environment.md:374 |
| `turnbase.social.friend-cap` | Platform Monolith | Integer | `50` | Maximum number of friends per user | local-environment.md:375 |
| `turnbase.pagination.default-page-size` | Platform Monolith | Integer | `25` | Default page size for list endpoints | local-environment.md:376 |
| `turnbase.pagination.max-page-size` | Platform Monolith | Integer | `100` | Maximum page size for list endpoints | local-environment.md:377 |
| `turnbase.uploads.max-bundle-size` | Platform Monolith | Size | `256MB` | Maximum size for game bundle uploads | local-environment.md:389 |
| `turnbase.uploads.slot-ttl` | Platform Monolith | Duration | `1h` | Time-to-live for pre-signed upload URLs | local-environment.md:390 |
| `turnbase.http.max-body-size` | Platform Monolith | Size | `64KB` | Maximum HTTP request body size | local-environment.md:391 |
| `turnbase.rate-limit.enabled` | Platform Monolith | Boolean | `true` | Enable/disable rate limiting (fails startup if false outside test/e2e) | local-environment.md:405 |
| `turnbase.security.trusted-proxies` | Platform Monolith | CIDR list | `10.0.0.0/8,172.16.0.0/12` | Trusted proxy CIDR blocks for X-Forwarded-For | local-environment.md:406 |
| `turnbase.platform.origin` | Platform Monolith | URL | `http://turnbase.localhost:8080` | Platform origin URL | local-environment.md:412 |
| `turnbase.game-frontend.origin-template` | Platform Monolith | URL template | `http://{gameId}.games.localhost:8080` | Game frontend origin template | local-environment.md:413 |
| `turnbase.gamehost.handler-timeout` | Game Host | Duration | `30s` | Timeout for game effect handler execution | local-environment.md:424 |
| `turnbase.gamehost.interrupt-escalation-grace` | Game Host | Duration | `5s` | Grace period for interrupt escalation | local-environment.md:425 |
| `turnbase.gamehost.context-idle-eviction` | Game Host | Duration | `5m` | Idle time before game context eviction | local-environment.md:426 |
| `turnbase.gamehost.memory-pressure-threshold` | Game Host | Percentage | `80%` | Memory pressure threshold for context eviction | local-environment.md:427 |
| `turnbase.gamehost.redis-unavailable-window` | Game Host | Duration | `60s` | Window for Redis unavailability tolerance | local-environment.md:428 |
| `turnbase.gamehost.retry-limit` | Game Host | Integer | `3` | Retry limit for game action execution | local-environment.md:429 |
| `turnbase.gamehost.grpc.max-message-size` | Game Host | Size | `32MB` | Maximum gRPC message size | local-environment.md:430 |
| `turnbase.gamehost.guest-java-home` | Game Host | Path | `/opt/graalvm-guest-jdk21` | Path to GraalVM guest JDK | local-environment.md:431 |
| `spring.datasource.url` | Platform Monolith | JDBC URL | `jdbc:postgresql://postgres:5432/turnbase` | PostgreSQL connection string | local-environment.md:441 |
| `spring.datasource.hikari.maximum-pool-size` | Platform Monolith | Integer | `20` | Maximum database connection pool size | local-environment.md:442 |
| `spring.data.redis.url` | Platform Monolith, Game Host | Redis URL | `redis://redis:6379` | Redis connection string | local-environment.md:443 |
| `turnbase.artifact-store.endpoint` | Platform Monolith, Game Host | URL | `http://minio:9000` | MinIO/S3 endpoint | local-environment.md:444 |
| `management.server.port` | Platform Monolith | Integer | `8081` | Management port for actuator and admin API | local-environment.md:445 |
| `management.server.address` | Platform Monolith | IP address | `127.0.0.1` (compose) / unset (Kubernetes) | Management server bind address | local-environment.md:446 |
| `logging.level.root` | All services | Log level | `INFO` | Root logger level | local-environment.md:447 |
| `management.tracing.sampling.probability` | Platform Monolith | Decimal (0-1) | `0.1` | Trace sampling probability | local-environment.md:448 |
| `spring.profiles.active` | All services | String | `local` | Active Spring profiles | local-environment.md:449 |
| `server.shutdown` | Platform Monolith | Mode | `graceful` | Shutdown behavior | local-environment.md:181 |
| `spring.lifecycle.timeout-per-shutdown-phase` | Platform Monolith | Duration | `30s` | Maximum drain time per shutdown phase | local-environment.md:182 |
| `spring.flyway.enabled` | Platform Monolith | Boolean | `true` | Enable Flyway migrations | schema-migrations.md:210 |
| `spring.flyway.locations` | Platform Monolith | Path | `classpath:db/migration` | Location of migration files | schema-migrations.md:211 |
| `spring.flyway.out-of-order` | Platform Monolith | Boolean | `false` | Allow out-of-order migration execution | schema-migrations.md:212 |
| `spring.flyway.validate-on-migrate` | Platform Monolith | Boolean | `true` | Validate migrations before applying | schema-migrations.md:213 |
| `spring.flyway.baseline-on-migrate` | Platform Monolith | Boolean | `false` | Auto-baseline unmanaged databases | schema-migrations.md:214 |
| `spring.flyway.clean-disabled` | Platform Monolith | Boolean | `true` | Disable Flyway clean command | schema-migrations.md:215 |
| `turnbase.rate-limit.auth.failures-before-lockout` | Platform Monolith | Integer | `5` | Failed attempts before auth lockout | rate-limiting.md:276 |
| `turnbase.rate-limit.auth.initial-lockout` | Platform Monolith | Duration | `30s` | Initial lockout duration for auth failures | rate-limiting.md:277 |
| `turnbase.rate-limit.api.capacity` | Platform Monolith | Integer | `100` | General API rate limit capacity | rate-limiting.md:279 |
| `turnbase.rate-limit.api.window` | Platform Monolith | Duration | `10s` | General API rate limit window | rate-limiting.md:280 |
| `turnbase.rate-limit.upload.capacity` | Platform Monolith | Integer | `10` | Upload rate limit capacity per user per hour | rate-limiting.md:282 |
| `turnbase.rate-limit.upload.window` | Platform Monolith | Duration | `1h` | Upload rate limit window | rate-limiting.md:283 |
| `turnbase.rate-limit.public.capacity` | Platform Monolith | Integer | `200` | Public endpoint rate limit capacity | rate-limiting.md:285 |
| `turnbase.rate-limit.public.window` | Platform Monolith | Duration | `1m` | Public endpoint rate limit window | rate-limiting.md:286 |
| `turnbase.rate-limit.minting.guest.capacity` | Platform Monolith | Integer | `5` | Guest account creation rate limit per IP per hour | rate-limiting.md:288 |
| `turnbase.rate-limit.minting.guest.window` | Platform Monolith | Duration | `1h` | Guest minting rate limit window | rate-limiting.md:289 |
| `turnbase.rate-limit.minting.registration.capacity` | Platform Monolith | Integer | `3` | User registration rate limit per IP per hour | rate-limiting.md:290 |
| `turnbase.rate-limit.minting.registration.window` | Platform Monolith | Duration | `1h` | Registration rate limit window | rate-limiting.md:291 |
| `turnbase.rate-limit.ws.connection.capacity` | Platform Monolith | Integer | `30` | WebSocket connection frame burst capacity | rate-limiting.md:293 |
| `turnbase.rate-limit.ws.connection.refill` | Platform Monolith | Rate | `10/1s` | WebSocket connection frame refill rate | rate-limiting.md:294 |
| `turnbase.rate-limit.ws.snapshot.capacity` | Platform Monolith | Integer | `2` | Snapshot request burst capacity | rate-limiting.md:295 |
| `turnbase.rate-limit.ws.snapshot.refill` | Platform Monolith | Rate | `1/3s` | Snapshot request refill rate | rate-limiting.md:296 |
| `turnbase.rate-limit.ws.action.capacity` | Platform Monolith | Integer | `10` | Game action frame burst capacity | rate-limiting.md:297 |
| `turnbase.rate-limit.ws.action.refill` | Platform Monolith | Rate | `5/1s` | Game action frame refill rate | rate-limiting.md:298 |
| `turnbase.rate-limit.ws.chat.capacity` | Platform Monolith | Integer | `5` | Chat message frame burst capacity | rate-limiting.md:299 |
| `turnbase.rate-limit.ws.chat.refill` | Platform Monolith | Rate | `1/1s` | Chat message frame refill rate | rate-limiting.md:300 |
| `turnbase.rate-limit.ws.command.capacity` | Platform Monolith | Integer | `10` | Room command frame burst capacity | rate-limiting.md:301 |
| `turnbase.rate-limit.ws.command.refill` | Platform Monolith | Rate | `2/1s` | Room command frame refill rate | rate-limiting.md:302 |
| `turnbase.rate-limit.ws.subscribe.capacity` | Platform Monolith | Integer | `20` | Subscription frame burst capacity | rate-limiting.md:303 |
| `turnbase.rate-limit.ws.subscribe.refill` | Platform Monolith | Rate | `1/1s` | Subscription frame refill rate | rate-limiting.md:304 |
| `turnbase.rate-limit.ws.max-connections-per-user` | Platform Monolith | Integer | `4` | Maximum concurrent WebSocket connections per user | rate-limiting.md:306 |
| `turnbase.rate-limit.ws.violations-before-close` | Platform Monolith | Integer | `20` | Dropped frames before connection close | rate-limiting.md:307 |
| `turnbase.rate-limit.ws.violation-window` | Platform Monolith | Duration | `10s` | Window for counting violations | rate-limiting.md:308 |
| `turnbase.rate-limit.ws.lockout.initial` | Platform Monolith | Duration | `30s` | Initial WebSocket reconnect lockout | rate-limiting.md:309 |
| `turnbase.rate-limit.ws.lockout.max` | Platform Monolith | Duration | `15m` | Maximum WebSocket reconnect lockout | rate-limiting.md:310 |

**Row count: 81**

---

## Table 2 — Secrets

| Secret name | Consumed by | Rotation story | Source `file:line` |
|---|---|---|---|
| JWT signing key | Platform Monolith | Yes — key set with active + retired keys; graceful rotation without mass logout; emergency immediate retirement possible | secrets-and-configuration.md:20 |
| PostgreSQL password | Platform Monolith | With a two-phase change — create second role or set new password with old still valid, restart app, then invalidate old | secrets-and-configuration.md:21 |
| Redis password | Platform Monolith, Game Host | With a two-phase change (same protocol as PostgreSQL) | secrets-and-configuration.md:22 |
| MinIO access key + secret | Platform Monolith, Game Host | Yes — issue second key pair, then retire first pair | secrets-and-configuration.md:23 |
| Google OAuth client secret | Platform Monolith | Yes — Google permits two concurrent client secrets | secrets-and-configuration.md:24 |
| Admin Basic-auth credentials | Platform Monolith | Restart — no graceful rotation mechanism stated | secrets-and-configuration.md:25 |
| Grafana admin password | Grafana | Restart — no graceful rotation mechanism stated | secrets-and-configuration.md:26 |

**Row count: 7**

---

## Table 3 — Containers / Services / Ports

| Container | Image or stack | Port(s) | Depends on | Readiness condition | Source `file:line` |
|---|---|---|---|---|---|
| Platform Monolith | `turnbase/platform` | 8080 (HTTP, WS, game assets), 8081 (management + admin API) | PostgreSQL, Redis, MinIO | Flyway complete, Postgres pool live, Redis reachable with `maxmemory-policy=noeviction`, `platform:sentinel` written | local-environment.md:22, :135 |
| Game Host | `turnbase/game-host` | 9090 (gRPC), 8081 (management) | Redis, MinIO, Platform Monolith (to register) | Espresso context factory warm, Redis reachable, artifact store reachable, `Register` acknowledged by monolith | local-environment.md:23, :136 |
| PostgreSQL 16 | `postgres:16-alpine` | 5432 | — | `pg_isready` | local-environment.md:24, :134 |
| Redis 7 | `redis:7-alpine` | 6379 | — | `PING` | local-environment.md:25, :134 |
| MinIO | `minio/minio` | 9000 (S3 API), 9001 (console) | — | `mc ready` | local-environment.md:26, :134 |
| Prometheus | `prom/prometheus` | 9090 (remapped to 9091 on host due to Game Host conflict) | — | own probes | local-environment.md:27, :137 |
| Grafana | `grafana/grafana` | 3000 | Prometheus, Loki, Tempo | own probes | local-environment.md:28, :137 |
| Loki | `grafana/loki` | 3100 | — | own probes | local-environment.md:29, :137 |
| Tempo | `grafana/tempo` | 4317 (OTLP gRPC), 3200 (HTTP) | — | own probes | local-environment.md:30, :137 |

**Row count: 9**

---

## Table 4 — Scheduled Jobs and Sweeps

| Job name | Interval | What it does | Requirement ID it satisfies | Source `file:line` |
|---|---|---|---|---|
| deadline-sweep | 5s (configurable) | Enforces time-based room transitions: grace-period expiry and deferred closure of host disconnect; closes elapsed migration windows; drains durable game-input notifications | FR-JOB-006 | local-environment.md:343; platform-operations.md:150 |
| reconcile | 60s (configurable) | Reconciles room records against live game-session state; re-drives owed session teardowns; deletes orphaned artifacts; resolves In-Progress rooms with no session; closes idle Lobby rooms; adopts rooms with lost owners | FR-JOB-007 | local-environment.md:344; platform-operations.md:150 |
| guest-cleanup | 1h (configurable) | Permanently deletes guest accounts whose session token has expired | FR-JOB-001 | local-environment.md:347; platform-operations.md:144 |
| notification-purge | 24h (configurable) | Permanently deletes notifications older than retention window (default 30 days) | FR-JOB-002 | local-environment.md:348; platform-operations.md:145 |
| room-purge | 24h (configurable) | Permanently deletes closed room records older than retention window (default 7 days), cascading to participant, team, invite records | FR-JOB-009 | local-environment.md:349; platform-operations.md:152 |
| upload-slot-cleanup | 15m (configurable) | Reclaims upload slots: moves expired PENDING slots to EXPIRED, deletes storage; moves PROCESSING versions past validation lease to FAILED | FR-JOB-012 | local-environment.md:350; platform-operations.md:153 |

**Row count: 6**

---

## Table 5 — Timing and Budget Constants

| Constant | Value | Applies to | Source `file:line` |
|---|---|---|---|
| Room grace period | 60s | Time for player reconnection after disconnect | local-environment.md:326 |
| Room migration window | 20s | Host transfer delay during disconnection | local-environment.md:327 |
| Room idle window | 30m | Lobby room purge after inactivity | local-environment.md:328 |
| Lease time-to-live | 10s | Room ownership lease validity | local-environment.md:329 |
| Lease renewal interval | 3s | Ownership lease refresh frequency | local-environment.md:330 |
| Lease self-eviction | 6s | Time before instance evicts itself from lease | local-environment.md:331 |
| Deadline sweep interval | 5s | Grace expiry and migration deadline enforcement | local-environment.md:343 |
| Reconciliation sweep interval | 60s | Room state reconciliation and repair | local-environment.md:344 |
| Reconciliation startup suppression | 120s | Delay before first reconciliation run after startup | local-environment.md:345 |
| Orphan artifact age threshold | 10m | Age before orphaned session artifacts deleted | local-environment.md:346 |
| Guest cleanup interval | 1h | Expired guest account deletion frequency | local-environment.md:347 |
| Notification purge interval | 24h | Notification cleanup frequency | local-environment.md:348 |
| Room purge interval | 24h | Closed room cleanup frequency | local-environment.md:349 |
| Upload slot cleanup interval | 15m | Expired upload slot cleanup frequency | local-environment.md:350 |
| Upload validation lease | 10m | Bundle validation time window | local-environment.md:351 |
| Session token lifetime | 24h | JWT session validity (registered + guest) | local-environment.md:373 |
| Account rename window | 30d | Time between allowed account name changes | local-environment.md:374 |
| Closed room retention | 7d | How long to keep closed room records | local-environment.md:361 |
| Notification retention | 30d | How long to keep notification records | local-environment.md:362 |
| Friend request retention | 30d | How long to keep friend request records | local-environment.md:363 |
| Guest account retention | 24h | How long to keep guest account records after expiry | local-environment.md:364 |
| Upload slot TTL | 1h | Pre-signed URL validity for bundle upload | local-environment.md:390 |
| Game Host handler timeout | 30s | Maximum time for game effect handler execution | local-environment.md:424 |
| Interrupt escalation grace | 5s | Time before escalating interrupt to termination | local-environment.md:425 |
| Context idle eviction | 5m | Time before idle game context is evicted | local-environment.md:426 |
| Redis unavailable window | 60s | Redis unavailability tolerance window | local-environment.md:428 |
| Monolith startup target | ≤30s | Readiness probe pass time (JVM + Flyway + pool) | local-environment.md:159 |
| Game Host registration target | ≤60s | Time from monolith readiness to Game Host `Register` acknowledged | local-environment.md:159 |
| Total startup budget | ≤90s | Cumulative startup time against 120s suppression window | local-environment.md:160 |
| Graceful shutdown drain timeout | 30s | Maximum time to drain in-flight requests | local-environment.md:182 |
| Pod termination grace period | 60s | Kubernetes grace period for shutdown sequence | local-environment.md:184 |
| PreStop hook sleep | 5s | Delay before shutdown to let ingress remove endpoint | local-environment.md:183 |
| Migration lock timeout | 5s | Flyway advisory lock acquisition timeout | schema-migrations.md:83 |
| Migration statement timeout | 60s | Per-statement execution timeout for migrations | schema-migrations.md:84 |
| Tier 1 auth lockout initial | 30s | First lockout duration after failed attempts | rate-limiting.md:277 |
| Tier 1 failures threshold | 5 | Failed attempts before lockout | rate-limiting.md:276 |
| Tier 2 rate window | 10s | General API rate limit window | rate-limiting.md:280 |
| Tier 2 capacity | 100 | General API requests per window | rate-limiting.md:279 |
| Tier 3 window | 1h | Upload rate limit window per user | rate-limiting.md:283 |
| Tier 3 capacity | 10 | Version uploads per user per hour | rate-limiting.md:282 |
| Tier 4 capacity | 200 | Public endpoint requests per minute | rate-limiting.md:285 |
| Tier 4 window | 1m | Public endpoint rate limit window | rate-limiting.md:286 |
| Tier 5 guest capacity | 5 | Guest accounts per IP per hour | rate-limiting.md:288 |
| Tier 5 guest window | 1h | Guest creation rate limit window | rate-limiting.md:289 |
| Tier 5 registration capacity | 3 | Registrations per IP per hour | rate-limiting.md:290 |
| Tier 5 registration window | 1h | Registration rate limit window | rate-limiting.md:291 |
| Tier 6 connection burst | 30 | WebSocket frame burst capacity | rate-limiting.md:293 |
| Tier 6 connection sustained | 10/1s | WebSocket frame sustained rate | rate-limiting.md:294 |
| Tier 6 snapshot burst | 2 | Snapshot request burst | rate-limiting.md:295 |
| Tier 6 snapshot sustained | 1/3s | Snapshot request sustained rate | rate-limiting.md:296 |
| Tier 6 action burst | 10 | Game action burst | rate-limiting.md:297 |
| Tier 6 action sustained | 5/1s | Game action sustained rate | rate-limiting.md:298 |
| Tier 6 chat burst | 5 | Chat message burst | rate-limiting.md:299 |
| Tier 6 chat sustained | 1/1s | Chat message sustained rate | rate-limiting.md:300 |
| Tier 6 command burst | 10 | Room command burst | rate-limiting.md:301 |
| Tier 6 command sustained | 2/1s | Room command sustained rate | rate-limiting.md:302 |
| Tier 6 subscribe burst | 20 | Subscription frame burst | rate-limiting.md:303 |
| Tier 6 subscribe sustained | 1/1s | Subscription frame sustained rate | rate-limiting.md:304 |
| Tier 6 max connections | 4 | Concurrent WebSocket connections per user | rate-limiting.md:306 |
| Tier 6 violations before close | 20 | Dropped frames before connection termination | rate-limiting.md:307 |
| Tier 6 violation window | 10s | Time window for violation counting | rate-limiting.md:308 |
| Tier 6 lockout initial | 30s | First reconnect lockout duration | rate-limiting.md:309 |
| Tier 6 lockout max | 15m | Maximum reconnect lockout duration | rate-limiting.md:310 |
| Database pool size | 20 | Maximum concurrent database connections | local-environment.md:442 |
| HTTP p95 latency target | <200ms | Non-game-session endpoint response latency | platform-operations.md:188 |
| WebSocket effect delivery latency | <50ms | Platform internal effect delivery (excluding Game Host) | platform-operations.md:189 |
| Error rate alert threshold | >1% | Over 5-minute window | platform-operations.md:91 |
| Latency alert threshold | >1000ms p95 | Over 5-minute window | platform-operations.md:92 |
| Game failure rate threshold | >1% of active sessions | Over 10-minute window | platform-operations.md:93 |
| Database saturation alert | >80% | Connection pool utilization over 2 minutes | platform-operations.md:94 |
| Reconciliation repairs alert | >3 consecutive runs | Without repair between | platform-operations.md:96 |
| Unrepaired room alert | >10 minutes | Detection without repair action | platform-operations.md:96 |
| Owed teardown alert | >15 minutes | Outstanding teardown without completion | platform-operations.md:97 |

**Row count: 92**

---

## Table 6 — Rate-Limit Buckets

| Tier | Bucket | Limit | Window | Key (what it is keyed on) | Response on breach | Source `file:line` |
|---|---|---|---|---|---|---|
| 1 | Auth failures (login, register, password change, auth-method add/remove) | 5 failed attempts → 30s lockout; each subsequent doubles duration | per-IP, per-lockout | IP (IPv4: /32, IPv6: /64) | 429 with `Retry-After: 30` | rate-limiting.md:60–72 |
| 2 | General API (all authenticated endpoints not covered by other tiers) | 100 requests per 10-second sliding window | per-user | userId | 429 with `Retry-After: 4` | rate-limiting.md:77–92 |
| 3 | Upload sub-bucket (`POST /api/games/{gameId}/versions` Step 1) | 10 version uploads per user per rolling hour | per-user, per-hour | userId | 429 (subset of Tier 2, independent bucket) | rate-limiting.md:97–105 |
| 4 | Unauthenticated reads (catalog, public profiles, game detail) | 200 requests per minute per IP | per-IP | IP (IPv4: /32, IPv6: /64) | 429 (implicit) | rate-limiting.md:106–113 |
| 5 | Account minting (guest creation + registration) | Guest: 5/IP/hr; Registration: 3/IP/hr (counts successes only) | per-IP, per-hour | IP for guest and registration separately | 429 `rate-limit-exceeded` with `Retry-After: seconds until refill` | rate-limiting.md:116–142 |
| 6 | WebSocket inbound frames (STOMP post-CONNECT) | snapshot: 1/3s sustained + 2 burst; action: 5/s + 10 burst; chat: 1/s + 5 burst; command: 2/s + 10 burst; subscribe: 1/s + 20 burst; connection: 10/s + 30 burst | per-principal, per-bucket | principal (userId/guestId) — **pod-local JVM memory, not distributed** | ERROR frame to `/user/queue/errors` with code `RATE_LIMIT_EXCEEDED`; connection close on >20 violations/10s; reconnect lockout 30s–15m | rate-limiting.md:146–244 |

**Row count: 6**

---

## Table 7 — Metrics, Logs and Alerts

| Name | Kind | Source `file:line` |
|---|---|---|
| HTTP request count per endpoint | Metric | platform-operations.md:70 |
| HTTP latency histogram (p50, p95, p99) per endpoint | Metric | platform-operations.md:70 |
| HTTP error rate per endpoint | Metric | platform-operations.md:70 |
| WebSocket connection count | Metric | platform-operations.md:71 |
| Active room count | Metric | platform-operations.md:72 |
| Active game session count | Metric | platform-operations.md:72 |
| Registered user count | Metric | platform-operations.md:72 |
| Friend request queue depth | Metric | platform-operations.md:72 |
| PostgreSQL connection pool utilization | Metric | platform-operations.md:73 |
| PostgreSQL query latency histogram | Metric | platform-operations.md:73 |
| PostgreSQL error count | Metric | platform-operations.md:73 |
| Redis operation latency by concern (game-state persistence, action queue, leases, rate-limiting) | Metric | platform-operations.md:74 |
| Redis error count by concern | Metric | platform-operations.md:74 |
| JVM heap usage | Metric | platform-operations.md:75 |
| JVM GC pause duration and frequency | Metric | platform-operations.md:75 |
| JVM thread count | Metric | platform-operations.md:75 |
| Scheduled job last-run timestamp | Metric | platform-operations.md:147 |
| Scheduled job execution count | Metric | platform-operations.md:147 |
| Reconciliation repair counts per duty (detected, applied, skipped) | Metric | platform-operations.md:155 |
| Structured log entry (timestamp, severity, service name, correlation IDs) | Log | platform-operations.md:61 |
| Correlation IDs (requestId, userId, sessionId, roomId, gameId) | Log | platform-operations.md:62 |
| Log level (TRACE, DEBUG, INFO, WARN, ERROR) | Log | platform-operations.md:63 |
| Trace ID and span ID in MDC and logs | Log | platform-operations.md:84 |
| Applied reconciliation repair entry (room ID, session ID, duty, detection age, action) | Log | platform-operations.md:156 |
| Reconciliation run abort reason | Log | platform-operations.md:156 |
| Error rate exceeds 1% over 5 minutes | Alert | platform-operations.md:91 |
| HTTP p95 latency exceeds 1000ms over 5 minutes | Alert | platform-operations.md:92 |
| Game session failure rate exceeds 1% over 10 minutes | Alert | platform-operations.md:93 |
| PostgreSQL pool utilization exceeds 80% for >2 minutes | Alert | platform-operations.md:94 |
| Reconciliation repairs applied on >3 consecutive runs | Alert | platform-operations.md:96 |
| Room remains unrepaired for >10 minutes | Alert | platform-operations.md:96 |
| Owed game-session teardown outstanding >15 minutes | Alert | platform-operations.md:97 |

**Row count: 43**

---

## Section 8 — Observations

### (a) Configuration keys with different defaults across files

**None found.** All configuration keys that appear in multiple files state consistent defaults.

### (b) Timing constants with conflicting values

**None found.** No timing constant appears with two different stated values across the five files.

### (c) Secrets with no stated rotation story

**None.** All seven secrets have explicit rotation stories:
- JWT signing key: graceful + emergency paths (secrets-and-configuration.md:20)
- PostgreSQL password: two-phase change procedure (secrets-and-configuration.md:21)
- Redis password: two-phase change procedure (secrets-and-configuration.md:22)
- MinIO keys: secondary key pair then retire (secrets-and-configuration.md:23)
- Google OAuth: permits two concurrent secrets (secrets-and-configuration.md:24)
- Admin credentials: restart procedure (secrets-and-configuration.md:25)
- Grafana password: restart procedure (secrets-and-configuration.md:26)

### (d) Jobs with conflicting interval statements

**None found.** All job intervals stated in local-environment.md §7.2 match those in platform-operations.md Scheduled Jobs section:
- deadline-sweep: 5s in both
- reconcile: 60s in both
- guest-cleanup: 1h in both
- notification-purge: 24h in both
- room-purge: 24h in both
- upload-slot-cleanup: 15m in both
