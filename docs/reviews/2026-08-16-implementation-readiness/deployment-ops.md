# Deployment, local stack, migrations, config, secrets, observability — implementation-readiness audit

**Agent:** Sonnet 5 · **Files reviewed:** 11 in full (7 owned + platform-operations.md's requirements
body + 6 platform data-model docs read for Q2 only + rate-limiting.md for Q4 cross-check) · **Date:** 2026-08-16

## Coverage

Read in full: `docs/specs/deployment/local-environment.md` (523 lines), `schema-migrations.md`,
`secrets-and-configuration.md`, `docs/requirements/platform-operations.md`,
`docs/decisions/0011-schema-migrations.md`, `0003-mvp-availability-target.md`,
`0001-local-first-mvp-platform.md`. For Q2 only, read all six schema documents in full:
`docs/specs/platform/data-model.md`, `data-model-accounts.md`, `data-model-social.md`,
`data-model-catalog.md`, `data-model-history.md`, `data-model-notifications.md`, `room-lifecycle.md`.
For Q4's cross-check, read `docs/specs/api-design/rate-limiting.md` in full.

Not read, and out of my slice: `admin-tooling.md`, `game-host-internals.md`, `room-websocket.md`,
`file-uploads.md`, `manifest-schema.md` — cited by my files but owned by other agents. Where a finding
below depends on one of those, it is marked `UNVERIFIED` or the dependency is stated explicitly. I did
one targeted grep across all of `docs/` for the string `bucket` to confirm a MinIO bucket name is
genuinely never defined anywhere in the corpus (F3) — that is a existence check, not a content audit of
files outside my slice.

Nothing in my slice was skipped. I did not verify PostgreSQL's exact privilege-check ordering for
`CREATE EXTENSION IF NOT EXISTS` against an already-existing extension under a non-superuser role
(relevant to ADR-0011 §6's claim) — that is a runtime behavior I cannot confirm by reading documents,
so I have deliberately not filed a finding on it.

## Summary

| # | Severity | One-line | Location |
|---|---|---|---|
| 1 | BLOCKER | FR-CICD-003 requires PR-time coverage "across all test types combined," but OQ-002 moves e2e to post-merge — the PR gate cannot compute a number that needs data that doesn't exist yet | `docs/requirements/platform-operations.md:107`, `:232` |
| 2 | BLOCKER | Two-role Postgres provisioning (`turnbase_app` / `turnbase_owner`) has no init mechanism, and the secrets inventory names only one undifferentiated "PostgreSQL password" | `docs/specs/deployment/secrets-and-configuration.md:21`, `:173-191`; `docs/decisions/0011-schema-migrations.md:99-109` |
| 3 | BLOCKER | No MinIO bucket name or creation mechanism is named anywhere in the corpus | `docs/specs/deployment/local-environment.md:444`; `docs/specs/deployment/secrets-and-configuration.md:204-213` |
| 4 | GAP | No environment-variable names for Postgres/Redis/MinIO credentials or the OAuth client ID, unlike every other secret in the doc | `docs/specs/deployment/secrets-and-configuration.md:16-27`, `:219`; `docs/specs/deployment/local-environment.md:441-446` |
| 5 | GAP | No `build:`/Dockerfile/image-tag strategy for `turnbase/platform` and `turnbase/game-host` in either compose or the Helm chart | `docs/specs/deployment/local-environment.md:22-23`, `:233-244` |
| 6 | GAP | No persistent-volume strategy stated for the compose profile (Postgres/Redis/MinIO/Grafana data) | `docs/specs/deployment/local-environment.md:227-232` |
| 7 | GAP | Metrics/tracing/logging/alerting wiring is unspecified beyond the requirement statements: no OTLP endpoint property, no Prometheus scrape config, no compose log-shipping to Loki, no Grafana provisioning, no Alertmanager/alert-rule mechanism | `docs/specs/deployment/local-environment.md:437-449`; `docs/requirements/platform-operations.md:66-97` |
| 8 | GAP | `session_teardown` retry backoff (10s doubling, 5-min cap) has no property/env-var entry in the "consolidated" configuration table | `docs/specs/platform/room-lifecycle.md:594`; `docs/specs/deployment/local-environment.md:339-351` |
| 9 | DRIFT | schema-migrations.md calls `room_participant.team_id → room_team(team_id)` one of "the two circular foreign keys," but by its own stated table order and the inline `REFERENCES` in data-model.md it isn't circular at all | `docs/specs/deployment/schema-migrations.md:155-161`; `docs/specs/platform/data-model.md:162` |
| 10 | DRIFT | Inconsistent bigint auto-increment idiom across sibling schema docs (`bigserial` vs `GENERATED ALWAYS AS IDENTITY`), no stated convention | `docs/specs/platform/data-model.md:314`; `docs/specs/platform/data-model-history.md:81`; `docs/specs/platform/data-model-notifications.md:29` |
| 11 | DRIFT | "Four are the system, five are the observability stack" is reversed against the document's own table (5 system rows, 4 observability rows) | `docs/specs/deployment/local-environment.md:16-17`, `:22-30` |
| 12 | DRIFT | data-model-notifications.md's stated reason for deferring the `notification.invitation_id` FK ("won't reference a table that doesn't exist yet") is inconsistent with the baseline's own table order, where `room_invitation` is created before `notification` | `docs/specs/platform/data-model-notifications.md:179-185`; `docs/specs/deployment/schema-migrations.md:155-158` |
| 13 | NIT | local-environment.md's opening claim of "every tunable... in one table" is directly contradicted by §7.6's own carve-out one section later | `docs/specs/deployment/local-environment.md:8-9`, `:398-401` |

## Findings

### F1 — BLOCKER — PR-time coverage gate cannot compute a number that requires post-merge data

**Where:** `docs/requirements/platform-operations.md:106-107`, `:232`

**Quotes:**
> "On every pull request to `main`, the pipeline must: ... (4) enforce coverage thresholds. The PR cannot be merged if any check fails." (FR-CICD-002, line 106)
> "All services must maintain ≥70% line coverage across all test types combined. Coverage is measured and reported as part of the PR pipeline." (FR-CICD-003, line 107)
> "**Resolved:** Unit and integration tests run in the PR pipeline and block merge. E2E tests run post-merge on `main` (triggered by the same merge commit, not blocking the PR)." (OQ-002, line 232)

**Blocks:** The GitHub Actions coverage-gating step in `turnbase-platform`'s PR workflow — whatever job computes "≥70% across all test types combined" and fails the PR check.

**Scenario:** A PR's unit+integration coverage is 65% but the missing 5% is exercised only by e2e paths. Per FR-CICD-003 the PR-time number must include e2e ("all test types combined," "as part of the PR pipeline"), so the gate should fail. But per OQ-002, e2e doesn't run until after the same commit merges to `main` — there is no e2e coverage data available at PR time to combine. An implementer following FR-CICD-003 literally cannot build the described check; one following OQ-002 literally cannot honor "combined" or "as part of the PR pipeline." Whichever a low-effort agent picks, the other requirement in the same document is violated, and nothing in the document says which one is authoritative.

**Suggested resolution:** `platform-operations.md` should own the fix, since both statements live in it: either FR-CICD-003's coverage threshold is scoped to "unit + integration coverage, measured at PR time" (mirroring the frontend's `FR-CICD-011` carve-out, which explicitly narrows to unit tests), with e2e coverage tracked as a separate post-merge metric that does not block the PR gate; or OQ-002 is revisited so e2e runs pre-merge for coverage purposes. The frontend requirement (FR-CICD-011) already sets the precedent for narrowing FR-CICD-003's scope per pipeline — extending the same pattern to the backend closes this cleanly.

---

### F2 — BLOCKER — No provisioning mechanism for the two-role Postgres model

**Where:** `docs/specs/deployment/secrets-and-configuration.md:16-27`, `:173-191`; `docs/decisions/0011-schema-migrations.md:99-109`

**Quotes:**
> "| PostgreSQL password | Platform Monolith | With a two-phase change | `.env` |" (secrets-and-configuration.md:21 — one row, one secret)
> "`turnbase_app` | The application at runtime and Flyway | `CONNECT`, `USAGE` on the schema, DML on all tables, DDL |
> `turnbase_owner` | Provisioning only | Owns the database; `CREATE EXTENSION` |" (secrets-and-configuration.md:177-178)
> "`pg_trgm` and `btree_gin` are created by the database provisioning step — the init script in the local Postgres container, and the equivalent in any future managed instance — as a superuser." (ADR-0011:101-102)

**Blocks:** Writing the `postgres` service block of `docker-compose.yml` (which env vars bootstrap the container: `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB`?) and the "init script" ADR-0011 refers to but never names, locates, or specifies the content of.

**Scenario:** Two roles are described (`turnbase_app`, unprivileged; `turnbase_owner`, provisioning-only with `CREATE EXTENSION`), but the secrets inventory names exactly **one** "PostgreSQL password" secret with no indication which role it authenticates. An implementer writing the compose file has to invent the bootstrap: the most natural reading of the official `postgres:16-alpine` image is to set `POSTGRES_USER`/`POSTGRES_PASSWORD` to the credential the app already has (since that's the only one named) and let the image's default init behavior make that user the database owner — which makes `turnbase_app` a superuser-equivalent role, directly violating FR-CRED-005 ("The application's database role must not hold superuser") the moment `docker compose up` first runs. The two-role split specified in prose is silently defeated by the one place its wiring should have been specified but wasn't.

**Suggested resolution:** `secrets-and-configuration.md` §4 should name both roles' env vars explicitly (e.g. `TURNBASE_DB_OWNER_PASSWORD` / `TURNBASE_DB_APP_PASSWORD`) and `local-environment.md` or `schema-migrations.md` should point at (or inline) the actual provisioning init script — e.g. a `docker-entrypoint-initdb.d/*.sql` file that creates `turnbase_owner` as the bootstrap superuser-equivalent, creates `turnbase_app` with only the stated grants, and creates the extensions — so the compose Postgres service and the K8s equivalent have a concrete artifact to reference.

---

### F3 — BLOCKER — MinIO bucket name and creation are never specified

**Where:** `docs/specs/deployment/local-environment.md:444`; `docs/specs/deployment/secrets-and-configuration.md:204-213`

**Quote:**
> "`turnbase.artifact-store.endpoint` | `http://minio:9000` | `TURNBASE_ARTIFACT_STORE_ENDPOINT`" (local-environment.md:444 — the entire artifact-store configuration surface)

**Blocks:** The `minio` compose service (whether a bucket-creation step — `mc mb`, an init container, or app-side auto-create at startup — is needed) and the upload pipeline the seeder is said to drive for real (`local-environment.md` §6: "the seeder drives the real upload pipeline... calls the same request-slot → PUT → confirm → validate → activate path").

**Scenario:** `docker compose up` brings MinIO up empty — MinIO does not auto-create buckets. `make seed` runs, calls the real upload pipeline (§6), and the first PUT against a pre-signed URL for a bucket that doesn't exist fails. Nothing in the corpus names a bucket (I grepped every file under `docs/` for the literal string `bucket` and found no MinIO bucket definition anywhere), so there is no `turnbase.artifact-store.bucket`-shaped property either — the config surface (§7.9) gives only the endpoint, nothing else about the object store.

**Suggested resolution:** `secrets-and-configuration.md` §4 (MinIO / S3) or `local-environment.md` §7.9 should own a bucket name property and state how the bucket comes to exist locally — most naturally a one-shot `mc mb` step in the compose file (an `mc` container with `depends_on: minio` that runs once and exits) mirrored by a Helm post-install hook, or the platform asserting/creating it at startup the way it already asserts the Redis eviction policy.

---

### F4 — GAP — No environment-variable names for datastore/OAuth credentials

**Where:** `docs/specs/deployment/secrets-and-configuration.md:16-27`, `:219`; `docs/specs/deployment/local-environment.md:441-446`

**Quotes:**
> "| Secret | Consumer | Rotatable without downtime | Local source |" (secrets-and-configuration.md:18 — the inventory table's columns; no "property / env var" column exists)
> "Registered with Google, stored as `TURNBASE_OAUTH_GOOGLE_CLIENT_SECRET`. The client **ID** is not a secret and appears in the authorization redirect" (secrets-and-configuration.md:219 — names the secret's env var but not the client ID's)

**Blocks:** Writing `.env.example` (secrets-and-configuration.md §2 says this file "contains no values — only keys," but the keys themselves are named nowhere for Postgres, Redis, or MinIO) and the Spring properties (`spring.datasource.username`/`password`, `spring.data.redis.password`, whatever binds MinIO's access/secret key) — none of these property names appear in local-environment.md §7.9's "Infrastructure" table, which gives `spring.datasource.url` and `spring.data.redis.url` but stops there. The JWT key and the OAuth client secret get explicit names; the other four secrets (Postgres, Redis, MinIO×2) and the OAuth client ID do not.

**Scenario:** An implementer writing `.env.example` per §2's instruction ("the checklist for a new machine") has nothing to transcribe for `DB_PASSWORD` vs `POSTGRES_PASSWORD` vs `SPRING_DATASOURCE_PASSWORD` — any of the three is a defensible guess, and two engineers picking differently produce a `.env.example` that silently doesn't match the properties file, which is exactly the class of drift §2 says the file exists to prevent.

**Suggested resolution:** Add a "Property / env var" column to the secrets-and-configuration.md §1 inventory table, using the same binding rule local-environment.md §7 already states, and add the corresponding rows to local-environment.md §7.9 (which currently documents only the non-secret shape of the datastore connections).

---

### F5 — GAP — No image build/tag strategy for the two first-party images

**Where:** `docs/specs/deployment/local-environment.md:22-23`, `:233-244`

**Quotes:**
> "| **Platform Monolith** | `turnbase/platform` | ... |" and "| **Game Host** | `turnbase/game-host` | ... |" (lines 22-23 — image names given, no tag)
> "values.yaml                   # defaults = §7 defaults" (line 236 — no mention of `image.tag`'s default)

**Blocks:** The `platform` and `game-host` service blocks in `docker-compose.yml` and the `image.tag` default in `values-local.yaml`. This is greenfield — no registry, no CI-published image exists yet (FR-CICD-006 only builds images on merge to `main`, which hasn't happened).

**Scenario:** An implementer runs `docker compose up` per §5's documented command with no `build:` stanza specified anywhere. Docker Compose will try to *pull* `turnbase/platform` and `turnbase/game-host` from a registry that has never had anything pushed to it, and the quick-start fails on a clean machine — the exact scenario this question is testing. The doc never states whether compose builds locally (`build: { context: ../../.. }`) or expects a pre-built local image, nor what tag the local build should carry.

**Suggested resolution:** `local-environment.md` §4/§5 should add a `build:` stanza (context + Dockerfile path) for both services in the documented compose file layout, and state the local tag convention (e.g. `:local` or `:dev`), distinct from the SHA-tagged images FR-CICD-006 produces for deployed environments.

---

### F6 — GAP — No persistence strategy for the compose profile's data

**Where:** `docs/specs/deployment/local-environment.md:227-232`, `:246-249`

**Quote:**
> "Postgres, Redis and MinIO are `StatefulSet`s with `PersistentVolumeClaim`s so a `helm upgrade` does not reset the database." (line 246 — Kubernetes only)

**Blocks:** The `postgres`/`redis`/`minio`/`grafana` service blocks in `docker-compose.yml` — specifically, whether they declare named volumes.

**Scenario:** The Kubernetes profile explicitly commits to durable storage (PVCs) so an upgrade doesn't lose data. Nothing parallel is stated for compose. Without a named volume, `docker compose down` (even without `-v`) removes anonymous volumes created by `up`, so every `docker compose down && docker compose up` cycle silently wipes Postgres/MinIO — which may be the intended "quick start is ephemeral" design, but it is never stated as a decision, and it directly affects whether `make reset-db` (§6, "drop schema, re-migrate, re-seed") is meaningfully different from just restarting the stack.

**Suggested resolution:** State explicitly in `local-environment.md` §5 or §6 whether the compose profile uses named volumes (persisting across restarts, with `make reset-db` as the deliberate reset path) or is intentionally ephemeral per `up`/`down` cycle. Either is defensible; the document should say which.

---

### F7 — GAP — Metrics/tracing/logging/alerting wiring is unspecified beyond the requirement text

**Where:** `docs/specs/deployment/local-environment.md:437-449` (§7.9, the only tracing-adjacent config); `docs/requirements/platform-operations.md:66-97` (FR-MET/FR-TRACE/FR-ALERT)

**Quotes:**
> "`management.tracing.sampling.probability` | `0.1` | `MANAGEMENT_TRACING_SAMPLING_PROBABILITY`" (local-environment.md:448 — the entire tracing configuration surface)
> "Alerts must be routed to a configurable notification channel (e.g., email, Slack webhook). Alert routing configuration is external to the application." (FR-ALERT-005, platform-operations.md:95)

**Blocks:** Everything needed to make the observability stack actually observe anything: (a) the OTLP exporter endpoint property pointing the OpenTelemetry Java agent at Tempo's `:4317` (Tempo is a container with a documented port, but nothing in §7 configures the app to send spans there — only the sampling *rate* is a property); (b) a Prometheus scrape config (`prometheus.yml`) naming the platform's and Game Host's `/actuator/prometheus` targets — no such file, or its content, is referenced anywhere in my slice; (c) a log-shipping mechanism from the compose containers' stdout into Loki — CON-004 says logs are "collected by Kubernetes and forwarded to Grafana Loki," which describes the K8s path (a DaemonSet-style collector, itself unnamed in the Helm template list: `observability/` is listed with no file names, unlike every other component's templates which are enumerated) but describes **no** mechanism at all for the compose profile, where there is no Kubernetes log collector; (d) Grafana datasource/dashboard provisioning (nothing states whether Grafana auto-provisions Prometheus/Loki/Tempo as datasources or whether that's a manual first-login step); (e) an Alertmanager or equivalent — none of the nine containers is Alertmanager, and FR-ALERT-005 explicitly requires routing to "a configurable notification channel," which needs *some* component to exist.

**Scenario:** `docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d` per §5's documented command brings up Grafana/Prometheus/Loki/Tempo, but: Grafana has no datasources configured (blank on first login), Prometheus has nothing to scrape (no target list), Tempo receives no spans (the app was never told its endpoint), and no container ships the other eight containers' logs into Loki. The "primary learning goal" OQ-003 names for including this stack cannot be exercised by the documented `docker compose up` command alone — an implementer has to design the entire wiring layer from scratch, informed only by the bare Prometheus-format/OTel-agent/JSON-log requirement statements in `platform-operations.md`.

**Suggested resolution:** This is real, scoped design work, not a one-line fix — `local-environment.md` should gain a subsection (or a new file under `docs/specs/deployment/`) covering: the OTLP endpoint property, a committed `prometheus.yml` (or its generation), Grafana provisioning files (`datasources.yaml`, dashboard folder), the compose log-shipping component (e.g. a Promtail/Alloy sidecar reading the Docker socket) and its Kubernetes equivalent, and a stated choice for alert routing (Grafana unified alerting vs. Prometheus Alertmanager as a tenth container).

---

### F8 — GAP — `session_teardown` retry backoff has no configuration entry

**Where:** `docs/specs/platform/room-lifecycle.md:594`; `docs/specs/deployment/local-environment.md:339-351` (§7.2, the scheduled-jobs configuration table)

**Quote:**
> "| Owed teardown | `session_teardown` row with `next_attempt_at <= now()` | `terminateAndCleanup`; on failure `attempts++`, backoff 10s doubling to a 5min cap |" (room-lifecycle.md:594)

**Blocks:** The `TeardownRetryScheduler` (or equivalent) implementation — specifically the two magic numbers (`10s` initial backoff, `5min` cap) that every other duration-shaped value in this corpus is expressed as a `turnbase.*` property (§7.1–7.8 cover 25+ such properties, including every other interval named in `room-lifecycle.md`: grace period, migration window, lease TTL/renew/self-evict, all four sweep intervals).

**Scenario:** A low-effort implementation agent transcribing `local-environment.md` §7 as "the configuration surface" (its own stated purpose, line 8-9) will not encounter this value at all, since it exists only as prose in `room-lifecycle.md`. It gets hardcoded as `Duration.ofSeconds(10)` / `Duration.ofMinutes(5)` inside `terminateAndCleanup`, breaking the pattern every sibling interval follows and making it untunable without a code change — inconsistent with the rest of the document's design intent (every other job/lease/retention value is explicitly a `@ConfigurationProperties` field).

**Suggested resolution:** Add `turnbase.jobs.teardown-retry.initial-backoff` (`10s`) and `turnbase.jobs.teardown-retry.max-backoff` (`5m`) to `local-environment.md` §7.2, alongside the other scheduled-job properties.

---

### F9 — DRIFT — A foreign key mislabelled as circular

**Where:** `docs/specs/deployment/schema-migrations.md:155-161`; `docs/specs/platform/data-model.md:162`

**Quotes:**
> "3. Tables in dependency order: `app_user`, ..., `room`, `room_team`, `room_participant`, `room_invitation`, ... 4. The two circular foreign keys, added after both endpoints exist: `game.active_version_id → game_version(version_id)` and `room_participant.team_id → room_team(team_id)`." (schema-migrations.md:155-161)
> "team_id               uuid        NULL REFERENCES room_team(team_id)," (data-model.md:162 — an **inline** reference inside `CREATE TABLE room_participant`, not a deferred `ALTER TABLE`)

**Blocks:** Writing `V1__baseline.sql`'s ordering and deferred-constraint section. An implementer following this instruction literally would write an unnecessary `ALTER TABLE room_participant ADD CONSTRAINT ... FOREIGN KEY (team_id) REFERENCES room_team(team_id)` after both tables exist, when the schema document it's transcribing already shows the reference inline (and correctly so, since `room_team` precedes `room_participant` in the very ordering given one paragraph earlier — there is no cycle: `room_team` only references `room`, nothing references back from `room_team` to `room_participant`).

**Scenario:** This particular case is harmless if followed literally (deferring an FK that didn't need deferring still produces a working schema), but it undermines confidence in the "two circular foreign keys" claim being exhaustive and correct, and it is exactly the kind of contradiction between the prose and the DDL shown a few files over that a low-reasoning-effort transcription agent has no way to resolve on its own — it will either trust the prose (harmless here) or, worse, start doubting the stated table order.

**Suggested resolution:** `schema-migrations.md` §5 should state that only `game.active_version_id ↔ game_version.game_id` is circular, and that `room_participant.team_id → room_team(team_id)` is an ordinary inline reference given the stated table order — or simply drop the second bullet.

---

### F10 — DRIFT — Inconsistent bigint auto-increment idiom across sibling documents

**Where:** `docs/specs/platform/data-model.md:314` (`game_input_outbox`); `docs/specs/platform/data-model-history.md:81` (`game_history_entry`); `docs/specs/platform/data-model-notifications.md:29` (`notification.event_seq`)

**Quotes:**
> "id            bigserial PRIMARY KEY," (data-model.md:314)
> "entry_id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY," (data-model-history.md:81)
> "event_seq          bigint GENERATED ALWAYS AS IDENTITY," (data-model-notifications.md:29)

**Blocks:** Nothing correctness-critical (both idioms produce a working auto-incrementing bigint), but it is exactly the kind of inconsistency Q2 asks about: `data-model.md`'s *Convention* section (lines 22-25) states type conventions for the whole corpus but says nothing about which auto-increment idiom to use, and the five sibling documents don't converge on one on their own.

**Scenario:** A migration-writing agent transcribing all six documents literally will produce a baseline with two different idioms for structurally identical "auto-incrementing bigint PK" columns, with no way to tell from the corpus whether that's intentional or an oversight.

**Suggested resolution:** `data-model.md`'s *Convention* section should state a single idiom (PostgreSQL's own documentation recommends `GENERATED ALWAYS AS IDENTITY` over `serial`/`bigserial` since PG10), and `game_input_outbox`'s `id` column should be updated to match.

---

### F11 — DRIFT — System vs. observability container count is reversed

**Where:** `docs/specs/deployment/local-environment.md:16-17`, `:22-30`

**Quotes:**
> "Nine containers. Four are the system, five are the observability stack that `platform-operations.md` OQ-003 puts inside the local environment..." (lines 16-17)
> Table rows 22-26: Platform Monolith, Game Host, PostgreSQL 16, Redis 7, MinIO (**five** rows)
> Table rows 27-30: Prometheus, Grafana, Loki, Tempo (**four** rows)

**Blocks:** Nothing downstream directly depends on the prose count (the table itself, which is what an implementer actually transcribes, is correct), but the compose directory layout one section later compounds the confusion:
> "├── docker-compose.yml            # the four core services" (line 230)
— if "four core services" means the system containers, that's also wrong (there are five); if it means something else, it's never said what.

**Scenario:** Low value for direct implementation risk (the table is unambiguous and is what gets transcribed), but it's a clean, cheap self-contradiction worth fixing before it's cited elsewhere as "four core services" by a document that trusts the prose instead of counting the table.

**Suggested resolution:** Swap "four" and "five" at line 16-17, and change "the four core services" at line 230 to "the five core services."

---

### F12 — DRIFT — Deferred-FK rationale doesn't match the stated table order

**Where:** `docs/specs/platform/data-model-notifications.md:179-185`; `docs/specs/deployment/schema-migrations.md:155-158`

**Quotes:**
> "The foreign key is attached here rather than inline in §1 because `notification` is declared first and PostgreSQL will not reference a table that does not exist yet." (data-model-notifications.md:179-181)
> "...`room`, `room_team`, `room_participant`, `room_invitation`, `session_teardown`, `game_input_outbox`, `game_session_completion`, `game_history_entry`, `notification`, `shedlock`." (schema-migrations.md:155-158 — `room_invitation` precedes `notification`)

**Blocks:** Nothing correctness-critical — the deferred `ALTER TABLE` pattern always works regardless of order. But the *reason* given for the pattern ("declared first... won't reference a table that doesn't exist yet") only holds if `notification` is created before `room_invitation`; per the baseline's own table order, it's the other way around, so an inline `REFERENCES room_invitation(invitation_id)` on `notification.invitation_id` would have worked too.

**Scenario:** A document-consistency check (not a runtime one) — worth noting because it's the same failure pattern as F9: prose reasoning about ordering that doesn't match the order stated in the document that actually governs baseline construction.

**Suggested resolution:** Either note in `data-model-notifications.md` that the deferred pattern is used for document-presentation-order reasons (this file describes `notification` before `room_invitation`) rather than baseline-order reasons, or simply drop the incorrect justification.

---

### F13 — NIT — Overclaimed completeness of the configuration table

**Where:** `docs/specs/deployment/local-environment.md:8-9`, `:398-401`

**Quotes:**
> "**Section 7 is the configuration surface** — every tunable named anywhere in the corpus, with its default and environment variable, in one table." (lines 8-9)
> "The full tier table is in `../api-design/rate-limiting.md` § *Configuration* and is not duplicated here." (§7.6, lines 398-399)

**Blocks:** Nothing — cosmetic, but worth a one-line fix since the preamble is what a reader trusts before checking whether a value they need is actually in the table.

**Suggested resolution:** Soften the preamble to "every tunable not already centrally documented elsewhere" or similar.

---

## What checked out

- **Monolith readiness independence from the Game Host** (`local-environment.md` §3) is thoroughly
  reasoned and consistent with `room-lifecycle.md` §5.2's "no Game Host probe" design — the two
  documents agree on why reconciliation trusts the session record rather than pinging the Game Host.
- **Redis `noeviction`/`appendonly` requirement** is stated with a concrete enforcement mechanism
  (startup assertion via `CONFIG GET maxmemory-policy`) and is consistent with `room-lifecycle.md`
  §1.5's explanation of why eviction is dangerous (wrongful ownership takeover).
- **Migration naming, immutability, and CI enforcement** (`schema-migrations.md` §2, §6) are concrete
  and mechanically checkable: timestamp-based names avoid merge collisions, and the three CI checks
  (Apply/Drift/Checksum) map cleanly onto FR-DB-001/002.
- **Backward-compatibility rules** (ADR-0011 §3, `schema-migrations.md` §4) give an explicit
  permitted/forbidden list and the expand→migrate→contract pattern, checkable by ADR-0011's own
  single review question. This is enforceable by a reviewer without further interpretation.
- **The one genuinely circular FK** (`game.active_version_id ↔ game_version.game_id`) is handled
  consistently between `data-model-catalog.md` §1-2 and `schema-migrations.md` §5 — column declared
  nullable with no inline reference in `game`, then a deferred `ALTER TABLE` after `game_version`
  exists, in an order that actually matches the stated table sequence.
- **Extensions are centralized correctly.** `pg_trgm` and `btree_gin` are both named in the baseline
  (`schema-migrations.md` §5 item 1) and both are actually used by indexes in the schema documents
  (`game_title_trgm_idx`, `game_tag_trgm_idx`, `app_user_username_trgm_idx`, `ghe_user_name_trgm_idx`)
  — no orphaned extension and no missing one. `citext` is correctly absent: the design deliberately
  uses functional `lower()` indexes instead, stated consistently in `data-model-accounts.md`.
- **JWT rotation** (`secrets-and-configuration.md` §3) is fully specified end to end: algorithm choice
  with reasoning, key-set JSON shape, three-step rotation procedure, and the live-connection
  consequences (§3.4) — including the specific tradeoff of an emergency rotation forfeiting
  in-progress games, stated plainly rather than glossed over.
- **Guest two-phase purge** (`data-model-accounts.md` §1) has concrete SQL predicates for both phases,
  and the reasoning for why a single-phase job is impossible (non-cascading FKs on `room_participant`
  and `room.host_user_id`) is consistent with `data-model.md`'s explanation of why those FKs have no
  cascade.
- **Shutdown sequence** in `local-environment.md` §3 maps every setting (`server.shutdown=graceful`,
  `preStop: sleep 5`, `terminationGracePeriodSeconds=60`) to a specific consequence of skipping it,
  and is consistent with FR-DEPLOY-001's stated ordering and with `room-lifecycle.md` §1.6's graceful
  shutdown procedure.
- **Type conventions** (`timestamptz`, `text` not `varchar`, `uuid` for most PKs) are followed
  consistently across all six schema documents, with the two justified, explicitly-argued exceptions
  (`game_history_entry.entry_id`, `game_input_outbox.id` — both bigint for volume/ordering reasons,
  though see F10 for their own mutual inconsistency).
