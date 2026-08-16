# Schema Migrations

How the PostgreSQL schema described in [`../platform/`](../platform/INDEX.md) comes into existence and
evolves. Realizes [ADR-0011](../../decisions/0011-schema-migrations.md) and
`../../requirements/platform-operations.md` FR-DB-001…004.

Scope: the Platform Monolith's relational database. The Game Host has no relational store
(`platform-operations.md` CON-002) and no migrations. Redis has no schema and no migration concept —
its keys and TTLs are documented in [`../game-host/game-host-internals.md`](../game-host/game-host-internals.md) §13
and are recreated by the code that writes them.

---

## 1. Layout

```
turnbase-platform/
└── src/main/resources/db/
    ├── migration/                       # Flyway, versioned, forward-only
    │   ├── V202608091200__baseline.sql
    │   └── V202608141530__add_notification_delivered_at.sql
    └── schema.sql                       # generated; the cumulative result, committed
```

| Path | Role |
|---|---|
| `db/migration/V*.sql` | The authority. What the database is. |
| `db/schema.sql` | A `pg_dump --schema-only` of a database built from those migrations, regenerated and committed with every schema change. Not applied to anything; it exists so a change is reviewable as a diff. |
| `docs/specs/platform/data-model*.md` | Normative for column names and for *why* the schema is shaped as it is. Not applied to anything either. |

The three must agree, and CI enforces the first two (§6). The third is enforced by review, which is
why a schema change is not merged without the corresponding documentation edit.

---

## 2. Naming

```
V<YYYYMMDDHHmm>__<snake_case_description>.sql
```

`V202608141530__add_notification_delivered_at.sql`. Description in the imperative, naming the object
changed.

Timestamps rather than a sequence (`V001`, `V002`). Two branches developed in parallel will pick the
same next integer and produce a version collision that Flyway rejects at startup — after merge, on
someone else's machine. Timestamps collide only if two migrations are authored in the same minute.

Out-of-order execution stays **disabled** (`spring.flyway.out-of-order=false`, the default). A
migration that lands with a timestamp earlier than one already applied is a merge that needs
re-timestamping, not a situation to tolerate: allowing it means the schema an engineer gets depends
on the order in which they pulled.

Repeatable migrations (`R__`) are not used. Nothing in this schema is a view, function or trigger
whose definition should be re-applied on change; the one thing that looks like a candidate — the
`pg_trgm` extension — is created once in the baseline.

---

## 3. Execution

Flyway runs inside the application at startup, through Spring Boot's autoconfiguration, before the
application context finishes refreshing and therefore before the readiness probe can pass
([`local-environment.md`](local-environment.md) §3).

**Concurrency is safe by construction.** Flyway takes a PostgreSQL advisory lock on the schema-history
table before doing anything, so when a rolling deploy starts a second instance while the first is
still serving, the second blocks until it holds the lock and then finds nothing to do — or applies
the migration exactly once while every other instance waits. No leader election, no init container,
no manual step.

**Running migrations in the application rather than as a separate job is a deliberate choice for this
platform.** A separate migration job is the right answer when the migration is long or when the
application must not hold DDL privileges; neither applies here. The MVP's migrations are seconds
long, the deployment is a single local cluster, and coupling the migration to the process that needs
the schema removes the failure mode where the two are deployed out of order. If a migration ever
becomes long enough to matter, the escalation is a Kubernetes `Job` with the same Flyway
configuration, gated ahead of the Deployment — which changes the invocation and nothing else.

**Migration sessions are time-bounded:**

```
lock_timeout      = 5s
statement_timeout = 60s
```

Set on the Flyway connection only, not globally. Without `lock_timeout`, an `ALTER TABLE` that queues
behind a long-running query holds an `ACCESS EXCLUSIVE` lock *request* which blocks every subsequent
reader of that table — the migration does not merely wait, it takes the table down while waiting. A
five-second failure that aborts the deploy is strictly better than an outage that looks like a
database hang.

---

## 4. What a migration may contain

### Permitted in any release

- `CREATE TABLE`, `CREATE INDEX`, `CREATE SEQUENCE`, `CREATE EXTENSION IF NOT EXISTS`.
- `ADD COLUMN` that is nullable, or has a non-volatile `DEFAULT` (PostgreSQL 11+ rewrites no rows).
- `ADD CONSTRAINT ... NOT VALID`, followed in a **later** migration by `VALIDATE CONSTRAINT`.
- Backfills, in batches, when the table is large enough that a single `UPDATE` would hold a long
  transaction.

### Forbidden within a release (ADR-0011 §3)

- `DROP COLUMN`, `DROP TABLE`, `ALTER COLUMN ... TYPE` (narrowing), `RENAME`.
- `SET NOT NULL` on an existing column — it takes an `ACCESS EXCLUSIVE` lock and scans the whole
  table, and the previous application version is still writing nulls.
- Any constraint that the previous version's writes would violate.

A rename is `ADD COLUMN` → backfill → dual-write → (next release) `DROP COLUMN`. Three steps and two
deploys, which is the price of the rollback FR-CICD-008 advertises.

### `CREATE INDEX CONCURRENTLY`

Required whenever an index is added to a table that already holds production data, because the
non-concurrent form takes a lock that blocks writes for the duration of the build. It cannot run
inside a transaction, so the migration must opt out:

```sql
-- flyway:executeInTransaction=false
DROP INDEX IF EXISTS notification_undelivered_idx;
CREATE INDEX CONCURRENTLY notification_undelivered_idx ON notification (user_id, event_seq)
  WHERE delivered_at IS NULL;
```

The `DROP ... IF EXISTS` is not defensive clutter. A concurrent build that fails leaves an **invalid**
index behind that PostgreSQL will not use and will not replace, and Flyway records the migration as
failed. The retry has to clear the corpse before rebuilding, and because the script is not
transactional, the retry is the only cleanup there is.

Non-concurrent `CREATE INDEX` remains correct in the baseline, where the tables are empty.

---

## 5. The baseline

`V202608091200__baseline.sql` contains, in this order:

1. `CREATE EXTENSION IF NOT EXISTS pg_trgm;` and `CREATE EXTENSION IF NOT EXISTS btree_gin;` — see
   ADR-0011 §6. Provisioning creates them; these statements make a missing extension a startup
   failure with a clear message rather than a runtime failure inside a catalog query.

   `pg_trgm` backs the four substring searches (game title, tag, username, history game-name).
   `btree_gin` is needed by one index only — `ghe_user_name_trgm_idx`, which puts a scalar `user_id`
   in front of a trigram column so FR-HIST-025's search is scoped to one user inside the index
   rather than filtered after it
   ([`../platform/data-model-history.md`](../platform/data-model-history.md) §2). Both are
   `contrib` modules shipped with the standard PostgreSQL distribution and with the
   `postgres:16-alpine` image, so neither is an operational dependency beyond the privilege to
   create it.
2. `CREATE SEQUENCE guest_serial_seq AS bigint MINVALUE 0 START WITH 0;`
   ([`../platform/data-model-accounts.md`](../platform/data-model-accounts.md) §1).
3. Tables in dependency order: `app_user`, `user_auth_method`, `user_session`,
   `user_privacy_settings`, `friendship`, `friend_request`, `game`, `game_version`, `game_tag`,
   `game_review`, `room`, `room_team`, `room_participant`, `room_invitation`, `session_teardown`,
   `game_input_outbox`, `game_session_completion`, `game_history_entry`, `notification`, `shedlock`.
4. **One** circular foreign key, added after both endpoints exist:
   `game.active_version_id → game_version(version_id)`, whose other leg is
   `game_version.game_id → game(game_id)`.

   `room_participant.team_id → room_team(team_id)` is **not** circular and needs no deferral: it is
   an ordinary inline `REFERENCES` (`../platform/data-model.md` §2), and `room_team` precedes
   `room_participant` in the order above. Nothing in `room_team` references back. It is called out
   here only because an earlier revision of this list named it, and a transcriber who deferred it
   would produce a working schema by an unnecessary route — then reasonably start doubting the table
   order itself.
5. Every index from the six schema documents.

`shedlock` is in the baseline rather than left to the library's auto-DDL (FR-JOB-005). A table that
appears in the database but not in the migration history is a table nobody can review, and its
absence on a fresh instance is discovered when the first scheduled job runs, not at startup.

---

## 6. Verification in CI

Three checks, in the platform submodule's PR workflow (`platform-operations.md` FR-CICD-002):

| Check | What it does | Fails when |
|---|---|---|
| **Apply** | Runs every migration against an empty PostgreSQL container | Any migration is invalid, or depends on an object created later |
| **Drift** | `pg_dump --schema-only` the result, normalise, diff against committed `db/schema.sql` | The dump was not regenerated after a schema change |
| **Checksum** | `flyway validate` against a database migrated from the previous commit | An already-applied migration file was edited in place |

The third is the one that catches the most damaging mistake. Editing an applied migration is
undetectable locally — the developer's database already has the change — and produces a checksum
mismatch on every other machine and in every environment that ran the old version. The rule is that
an applied migration is immutable; a correction is a new file.

**There is no check that the migrations agree with the schema documents.** That comparison is prose
against DDL and cannot be automated honestly; it is a review responsibility, and ADR-0011 §4 states
which side wins when they disagree.

---

## 7. Seed data

Seeds are **not** migrations. They are applied by an `ApplicationRunner` active only under the
`local` and `e2e` Spring profiles, reading `db/seed/*.sql`, and every statement is idempotent
(`ON CONFLICT DO NOTHING` against fixed UUIDs).

Keeping them out of the migration history is what makes them safe to change: a seed is edited
constantly during development, and a Flyway-versioned seed would trip the checksum check of §6 every
time. It also means no environment can accidentally acquire demo data by running migrations.

What is seeded, and how a developer resets it, is in
[`local-environment.md`](local-environment.md) §6.

---

## 8. Configuration

| Property | Default | Notes |
|---|---|---|
| `spring.flyway.enabled` | `true` | `false` only in unit tests with no database |
| `spring.flyway.locations` | `classpath:db/migration` | |
| `spring.flyway.out-of-order` | `false` | §2 |
| `spring.flyway.validate-on-migrate` | `true` | Checksum enforcement at startup, not only in CI |
| `spring.flyway.baseline-on-migrate` | `false` | An unmanaged existing database must fail loudly, not be adopted silently |
| `spring.flyway.clean-disabled` | `true` | `flyway:clean` drops every object in the schema; it must not be reachable from a running application under any profile |

`baseline-on-migrate=false` and `clean-disabled=true` are the two that matter. The first prevents
Flyway from stamping an unknown database as "already at baseline" and then applying nothing — which
turns a misconfigured connection string into a silently empty schema. The second removes the one
Flyway command that can destroy a database, from every environment, including the ones where somebody
might reasonably want it.
