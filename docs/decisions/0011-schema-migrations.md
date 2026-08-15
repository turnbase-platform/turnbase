# ADR-0011: Schema migrations — Flyway, forward-only, backward-compatible

- **Status:** Accepted
- **Date:** 2026-08-09
- **Deciders:** Project owner
- **Source:** MVP Readiness Review 2026-07-02 — OPS-3 (open since July, never closed)

## Context

The corpus now defines the platform's entire relational schema across six documents under
[`docs/specs/platform/`](../specs/platform/INDEX.md) — around thirty tables — and **names no
migration tool anywhere**. The tables are described as though they simply exist. Nothing states how
they come into being on a fresh database, how a column is added to a running one, which artifact an
engineer should trust when a document and the database disagree, or what happens to a schema change
during a deploy.

Three facts make this more than paperwork:

1. **The deploy overlaps two application versions.** `platform-operations.md` FR-DEPLOY-001 describes
   a graceful drain in which an instance releases room ownership before exiting, and ADR-0008's claim
   path is written for a successor instance that is already running. That is a rolling update, and it
   means the new version's schema and the old version's code are live at the same time — even in the
   single-instance MVP, which is precisely where that path is exercised on every restart.
2. **FR-CICD-008 promises rollback by re-deploying a previous image tag.** With a forward-only schema
   — and Flyway Community has no undo — rolling the application back to N−1 only works if migration N
   left a schema that N−1 can still run against. The rollback story the pipeline advertises is
   *false* unless backward compatibility is a rule.
3. **Two extensions are required.** `pg_trgm` backs the substring searches over game title, tags,
   username and history game-name ([`data-model-catalog.md`](../specs/platform/data-model-catalog.md)
   §3), and `btree_gin` backs the one index that scopes a trigram search to a single user
   ([`data-model-history.md`](../specs/platform/data-model-history.md) §2). `CREATE EXTENSION` is
   privileged, so it cannot be left to "the application will do it at startup" without deciding who
   the application connects as.

## Decision

### 1. Flyway, with plain SQL migrations

Flyway Community, wired through Spring Boot's autoconfiguration, running at application startup.

Liquibase was the alternative. It was rejected because its value — a database-agnostic changelog in
XML/YAML/JSON from which it generates dialect-specific DDL — buys portability the project has ruled
out: `platform-operations.md` CON-002 fixes PostgreSQL as the relational store, and the schema
documents lean on PostgreSQL-specific features throughout (partial indexes, `jsonb`, generated
columns, GIN with `gin_trgm_ops`, identity columns). Expressing those through an abstraction layer
means writing native SQL inside a changelog wrapper — Liquibase's own escape hatch — at which point
the abstraction is pure overhead, and the reviewer of a schema change reads XML instead of the DDL
they will have to reason about in production.

Flyway's migrations *are* the DDL. The schema documents already contain the SQL; a Flyway migration
is that SQL with a filename.

### 2. Forward-only

There are no `undo` migrations. A mistake is corrected by a new migration, never by reversing an
applied one. This is partly a constraint of Flyway Community, but it would be the decision regardless:
an undo script is written when the schema is healthy and executed when it is not, is exercised by
nothing, and cannot restore data a `DROP` destroyed.

Rollback of the *application* remains supported (FR-CICD-008) and is what rule 3 exists to protect.

### 3. Every migration must be backward compatible with the previous application version

A migration may not break the code that is currently running. Concretely, within a single release:

- Adding a table, a column, an index or a constraint that the previous version does not know about is
  permitted.
- Dropping or renaming a column or table is **not**. Neither is narrowing a type, adding a `NOT NULL`
  to an existing column, or adding a constraint the previous version's writes would violate.
- A destructive change is executed as **expand → migrate → contract** across at least two releases:
  release *N* adds the new shape and writes both; release *N+1*, once no running instance reads the
  old shape, removes it.

The rule is checkable at review time by a single question: *if this migration ran and the deploy then
rolled back to the previous image, would the previous image still work?*

### 4. The migration files are authoritative; the specs are normative

When a schema document and a migration disagree, **the migration is what the database is**. The
documents remain normative for two things a migration cannot express: the *names* — which the rest of
the corpus cites by hand — and the *reasons*, which is the entire content of those documents and the
thing that keeps the next change from undoing a deliberate decision.

A schema change is therefore not complete until both are updated, and the guard against drift is
mechanical rather than cultural: CI applies every migration to an empty database, dumps the result,
and fails if it differs from a committed `db/schema.sql`. That makes the cumulative effect of a
migration reviewable as a diff, which a directory of incremental scripts otherwise is not.

### 5. Baseline DDL lives in the platform submodule, not in this repository

Migrations live in `turnbase-platform` at `src/main/resources/db/migration/`, versioned and deployed
with the code that depends on them. This repository holds the design documents. The initial baseline
is transcribed by hand from the six schema documents into `V202608091200__baseline.sql`; from that
point the documents are maintained alongside the migrations rather than ahead of them.

The Game Host has no relational database (`platform-operations.md` CON-002 — Redis only), so it has
no migrations and no Flyway dependency.

### 6. Extensions are provisioned, and the migration asserts them

`pg_trgm` and `btree_gin` are created by the database provisioning step — the init script in the
local Postgres container, and the equivalent in any future managed instance — as a superuser. The
baseline migration issues `CREATE EXTENSION IF NOT EXISTS` for both, which succeeds as a no-op when
provisioning did its job and succeeds outright when the migration user happens to be privileged. If
neither holds, startup fails at the baseline with an unambiguous error rather than later, at the
first catalog search, with a missing-operator-class failure that reads like a query bug.

Both are `contrib` modules in the standard distribution, so this is a privilege question rather than
an install one.

## Consequences

- **Positive.** The schema has a single mechanical source of truth, an audit trail with timestamps
  and checksums, and a fresh database is one `docker compose up` away from the same shape as any
  other. The backward-compatibility rule makes FR-CICD-008's rollback real rather than nominal, and
  it is exercised on every local restart rather than only in production.
- **Negative.** Destructive changes take two releases and interim schemas carry columns nobody reads.
  That cost is accepted: the alternative is a deploy that can only go forwards.
- **Constraint on migration authorship.** `CREATE INDEX CONCURRENTLY` cannot run inside a transaction,
  so any migration using it must opt out of Flyway's transactional wrapping and must therefore be
  idempotent on its own — a failed concurrent build leaves an invalid index that the next attempt has
  to drop. The rule and its handling are in
  [`schema-migrations.md`](../specs/deployment/schema-migrations.md) §4.
- **Startup ordering.** Migrations run before the application serves traffic, which is what the
  readiness gate in [`local-environment.md`](../specs/deployment/local-environment.md) §3 depends on;
  a migration that takes minutes will hold a rolling deploy open for that long, which FR-DEPLOY-003
  bounds.

## Affected documents

- `docs/specs/deployment/schema-migrations.md` — new; the operational detail.
- `docs/specs/platform/data-model*.md` — authority statement (§4) added to `data-model.md`.
- `docs/requirements/platform-operations.md` — new FR-DB-001…004; CON-012.
- Review INDEX — resolves OPS-3.
