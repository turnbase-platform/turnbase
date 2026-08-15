# Platform Data Model — Game Catalog, Versions and Review

## Scope

The relational schema behind the game catalog: game records, their versions and bundles, the
searchable tag projection, and the admin review queue that governs the badge.

Sources: [`../../requirements/game-catalog.md`](../../requirements/game-catalog.md),
[`../../requirements/admin-tooling.md`](../../requirements/admin-tooling.md),
[`../manifest/manifest-schema.md`](../manifest/manifest-schema.md),
[`../api-design/file-uploads.md`](../api-design/file-uploads.md).

Conventions are those of [`data-model.md`](data-model.md) *Convention*. `room.game_id` and
`room.game_version` reference this schema; `app_user` is defined in
[`data-model-accounts.md`](data-model-accounts.md).

**One rule shapes this document: the manifest is the source of truth for everything a game
declares** (`manifest-schema.md`), so no column here may restate manifest content unless it needs an
index shape the manifest's `jsonb` cannot provide. Every such column is a *projection* that can be
rebuilt from the stored manifest and checked against it, not an independent copy.

**The rule has exactly one exception, and it is named rather than implied.** FR-GAME-008 makes
`title`, `shortDescription` and the info document **owner-editable without a new version upload** —
so those three are not projections of anything: after the first edit the manifest and the catalog
legitimately disagree, and the catalog is right. They live on `game`, not on `game_version`, and
§1 states what the manifest's copies mean thereafter. Everything else derived from a manifest lives
on the version and is rebuildable.

---

## 1. `game`

```sql
CREATE TABLE game (
  game_id                  uuid PRIMARY KEY,
  owner_user_id            uuid        NULL REFERENCES app_user(user_id),
  title                    text        NOT NULL,
  short_description        text        NOT NULL,
  info_doc_markdown        text        NULL,

  badge                    text        NOT NULL DEFAULT 'UNVERIFIED',
  listed                   boolean     NOT NULL DEFAULT false,

  active_version_id        uuid        NULL,
  completed_session_count  bigint      NOT NULL DEFAULT 0,

  created_at               timestamptz NOT NULL DEFAULT now(),
  updated_at               timestamptz NOT NULL DEFAULT now(),
  archived_at              timestamptz NULL,
  deleted_at               timestamptz NULL,

  CONSTRAINT game_badge_ck CHECK (badge IN ('OFFICIAL','VERIFIED','UNVERIFIED')),
  CONSTRAINT game_official_ownerless_ck CHECK ((badge = 'OFFICIAL') = (owner_user_id IS NULL))
);

CREATE INDEX game_public_idx ON game (created_at DESC)
  WHERE deleted_at IS NULL AND archived_at IS NULL AND listed AND badge <> 'UNVERIFIED';
CREATE INDEX game_owner_idx ON game (owner_user_id) WHERE deleted_at IS NULL;
CREATE INDEX game_title_trgm_idx ON game USING gin (lower(title) gin_trgm_ops);
```

### Badge and listing are two fields because they answer two different questions

`badge` is the platform's judgement (FR-BADGE-001…004); `listed` is the owner's intent (FR-GAME-005,
FR-GAME-006). Collapsing them into a single visibility enum loses the owner's choice across a badge
change, which matters because badges move without the owner acting: FR-GAME-014 clears Verified on
every new version upload.

**Submitting for review is the owner's publish intent, and approval realizes it — so approval sets
`listed = true`.** FR-REV-004 says approval "makes it publicly visible in the catalog", which is not
satisfied by setting the badge alone: a first-time game has `listed = false` from FR-GAME-005's
default, so badge-only approval would leave it invisible and FR-REV-004 unimplemented. Approval
writing both fields is safe rather than presumptuous because approval is only reachable through
FR-PRV-004's voluntary submission; nobody is published who did not ask to be.

`listed` still earns its place after that, on the one path where the two fields genuinely diverge:
FR-GAME-006's delist. An owner who takes a Verified game out of the catalog keeps `badge =
'VERIFIED'` and a subsequent re-listing needs no re-review. With a single enum, delisting would
either destroy the badge or need a second value to remember it.

Public catalog visibility is therefore a conjunction, expressed once and indexed by
`game_public_idx`:

```sql
deleted_at IS NULL AND archived_at IS NULL AND listed
  AND badge <> 'UNVERIFIED' AND active_version_id IS NOT NULL
```

The `badge <> 'UNVERIFIED'` term is FR-BADGE-004 and FR-PRV-001: an unverified game is private no
matter what the owner sets `listed` to. `active_version_id IS NOT NULL` keeps a game whose only
upload failed validation out of the catalog, which no requirement states but every one of them
assumes — FR-CAT-002 lists a "current version" column that would otherwise be blank.

### A new version delists a community game until it is re-reviewed

FR-GAME-010 activates a new version immediately, FR-GAME-014 clears Verified on upload, and
FR-BADGE-004 makes Unverified private. Chained, publishing a patch to a popular community game takes
it out of the catalog and — via FR-PRV-002 — makes it unhostable by anyone but its owner, until an
operator approves it again. Existing rooms are unaffected: FR-GAME-011 keeps the previous version
alive for as long as rooms are using it.

That is what the requirements say, and it is defensible (verification attests to *code*, and the code
changed). It is recorded here because it is not obvious from any single requirement, and because it
is the reason `listed` must survive the badge change. Whether the previous Verified version should
remain *active* until the new one is approved is OQ-001 below.

### `owner_user_id` is nullable, and null means first-party

FR-OFF-001 has an operator upload a game directly as Official, and FR-BADGE-002 forbids the Official
badge on community-uploaded games. There is no operator *account* — admin access is HTTP Basic on a
localhost-bound port with static credentials (FR-ADM-001/002), not a session on an `app_user`. So an
Official game has no owner row to point at.

`game_official_ownerless_ck` is written as an **equivalence** rather than an implication, because the
read path depends on the converse. `badge <> 'OFFICIAL' OR owner_user_id IS NULL` would state only
that an Official game has no owner, leaving a Verified game with a null owner perfectly legal — and
that row would render the platform's own name as its author under the rule below. The direction that
matters for correctness is the unenforced one, so both are enforced.

FR-CAT-002 requires an author username in every catalog row. For a null owner the catalog renders the
platform name; FR-CAT-007's sort by author must therefore place these rows deterministically
(`ORDER BY coalesce(u.username, '') ...`) rather than leaving them to `NULLS` default ordering, which
differs between ascending and descending.

**Under ADR-0006 the MVP has no community games at all** — `runtime: "jvm"` is the only runtime and
is official-only — so for the MVP every row here has `owner_user_id IS NULL`, `badge = 'OFFICIAL'`,
and the review queue (§4) is empty. The schema is written for the post-MVP state because retrofitting
ownership onto a catalog is a data migration, and because `game-catalog.md` and `admin-tooling.md`
specify the community path in full.

### `completed_session_count` is declared here and written elsewhere

FR-STATS-004 requires a denormalized per-game session counter that is incremented at completion and
never decremented, including for sessions played entirely by guests. Its writer, and the idempotency
key that keeps a re-delivered `game_over` from double-counting, are in
[`data-model-history.md`](data-model-history.md) §3.

### `title` and `short_description`: the manifest seeds them once and never again

`manifest.title` and `manifest.shortDescription` are required and validated
(`manifest-schema.md`), and `game.title` / `game.short_description` restate them — the one place this
document's opening rule is broken, because FR-GAME-008 makes both owner-editable without a version
upload and a column the owner can edit is not rebuildable from anything.

The rule, which neither requirement states and both need:

> The manifest's values are used **only when the `game` row is created**, on the first successful
> activation. Every later activation leaves `title`, `short_description` and `info_doc_markdown`
> untouched, whatever the new manifest says.

Without it, activation is ambiguous in a way that breaks one requirement or the other. If activation
rebuilt them from the manifest, an FR-GAME-008 rename would be silently reverted by the developer's
next upload — the platform undoing an edit it accepted, with no message. If activation ignores them
without saying so, `manifest.title` is a required, validated field that the platform reads once and
then permanently disregards, which is worth stating rather than discovering.

The consequence is that a manifest and a catalog row may legitimately disagree after an edit, and the
catalog row wins. The manifest's copy remains meaningful to the test harness and to a developer
inspecting a bundle; it is simply not the platform's display value any more.

`info_doc_markdown` follows the same rule and has an additional wrinkle: `manifest.infoDoc` is a
*path into the archive*, so what is stored here is the resolved content of that file at first
activation, not the path.

### Soft delete keeps the row; archival is about the artifacts

FR-GAME-012 makes deletion a soft delete precisely so history entries stay meaningful, and FR-GDET-007
requires the detail page to say "this game no longer exists" rather than 404. Both need the row.

`archived_at` is FR-ACCT-007's state for a game whose owner deleted their account. See §5 for why
that requirement's second sentence cannot be implemented as written.

### Where the write-side rules are enforced

`game_public_idx`'s predicate is the *read* rule and is stated above. Three requirements are write
rules over the same columns, and none of them can be a constraint — each is a precondition on a
statement in another table:

| Rule | Requirement | Checked at | Predicate |
|---|---|---|---|
| No new rooms for a deleted game | FR-GAME-013 | room creation | `game.deleted_at IS NULL AND game.archived_at IS NULL` |
| Only the owner may host a private game | FR-GAME-007 | room creation | `game.listed OR :creator = game.owner_user_id` |
| Only the owner may host an Unverified game | FR-PRV-002 | room creation | `game.badge <> 'UNVERIFIED' OR :creator = game.owner_user_id` |

`room.game_id`'s foreign key is unconditional and deliberately so — it must keep pointing at a
soft-deleted game for the rooms that were already running when it was deleted (FR-GAME-013's second
sentence). The FK therefore cannot carry any of these rules, which is why they are named here: they
are the complete set of catalog preconditions on `INSERT INTO room`, and a room-creation handler that
implements the read predicate instead of this table gets FR-GAME-007 and FR-PRV-002 backwards for the
owner.

---

## 2. `game_version`

```sql
CREATE TABLE game_version (
  version_id            uuid PRIMARY KEY,
  game_id               uuid        NOT NULL REFERENCES game(game_id) ON DELETE CASCADE,
  version               text        NOT NULL,
  version_major         integer     NOT NULL GENERATED ALWAYS AS (split_part(version,'.',1)::integer) STORED,
  version_minor         integer     NOT NULL GENERATED ALWAYS AS (split_part(version,'.',2)::integer) STORED,
  version_patch         integer     NOT NULL GENERATED ALWAYS AS (split_part(version,'.',3)::integer) STORED,

  status                text        NOT NULL,
  manifest              jsonb       NULL,
  gdk_api_version       text        NULL,

  bundle_object_key     text        NULL,
  declared_size_bytes   bigint      NOT NULL,
  stored_size_bytes     bigint      NULL,
  upload_expires_at     timestamptz NOT NULL,
  validation_errors     jsonb       NULL,
  validation_warnings   jsonb       NULL,

  min_players           integer     NULL,
  max_players           integer     NULL,
  supports_ai           boolean     NULL,
  supports_spectators   boolean     NULL,
  supports_mid_game_join boolean    NULL,

  claimed_by            text        NULL,
  claimed_until         timestamptz NULL,

  created_at            timestamptz NOT NULL DEFAULT now(),
  activated_at          timestamptz NULL,
  superseded_at         timestamptz NULL,
  bundle_purged_at      timestamptz NULL,

  CONSTRAINT game_version_format_ck CHECK (version ~ '^[0-9]+\.[0-9]+\.[0-9]+$'),
  CONSTRAINT game_version_status_ck CHECK (status IN
    ('PENDING','PROCESSING','ACTIVE','FAILED','EXPIRED','SUPERSEDED','DISCARDED'))
);

CREATE UNIQUE INDEX game_version_key ON game_version (game_id, version);
CREATE UNIQUE INDEX game_version_active_key ON game_version (game_id) WHERE status = 'ACTIVE';
CREATE INDEX game_version_order_idx ON game_version (game_id, version_major, version_minor, version_patch);
CREATE INDEX game_version_upload_expiry_idx ON game_version (upload_expires_at) WHERE status = 'PENDING';
CREATE INDEX game_version_stuck_idx ON game_version (claimed_until) WHERE status = 'PROCESSING';
CREATE INDEX game_version_players_idx ON game_version (min_players, max_players) WHERE status = 'ACTIVE';
CREATE INDEX game_version_gdk_idx ON game_version (gdk_api_version) WHERE status IN ('ACTIVE','SUPERSEDED');

ALTER TABLE game ADD CONSTRAINT game_active_version_fk
  FOREIGN KEY (active_version_id) REFERENCES game_version(version_id);
```

### Version ordering is three integers, because `x.y.z` does not sort as text

FR-GAME-009 compares segments "as integers left to right — e.g. `1.10.0 > 1.9.0`". As text,
`'1.10.0' < '1.9.0'`, so a `text` ordering gets the requirement's own worked example backwards and
would accept an upload the requirement says to reject. The three generated columns are the only place
this is decided; every comparison — the strictly-higher check on upload, FR-CAT-007's sort by
version — uses them.

They are `GENERATED ... STORED` rather than application-populated so that the parse cannot disagree
with the string it came from.

**`game_version_format_ck` does not protect those casts, and it is worth being precise about why.**
PostgreSQL evaluates stored generated columns *before* it evaluates check constraints
(`ExecComputeStoredGenerated` runs ahead of `ExecConstraints` in `ExecInsert`), so an insert of
`version = '1.2'` never reaches the check: it fails on `version_patch` with
`invalid input syntax for type integer: ""`, naming no constraint and no rule. The cast is the actual
enforcement; the check is a documentation of the format and a guarantee the planner and any later
query can rely on. Malformed input is rejected either way, but the diagnostic is the wrong one, so
the format is validated at the upload boundary where a `422` can name the field
([`../api-design/file-uploads.md`](../api-design/file-uploads.md)) rather than being left to the
database to reject badly.

### The badge transition at activation is `VERIFIED → UNVERIFIED` **only**

FR-GAME-014 clears *Verified* status on a new version upload. Applied as an unconditional
`badge = 'UNVERIFIED'` — which is how `file-uploads.md` step 3.6 and an earlier version of §8's
traceability row read it — **every official upload aborts**, and under ADR-0006 that is every upload
the MVP has.

The mechanism is `game_official_ownerless_ck`, and it is doing exactly what it should. An Official
game has `owner_user_id IS NULL`; the check is an equivalence, so writing `badge = 'UNVERIFIED'` on a
row with a null owner violates it and rolls back the activation transaction. An operator publishing
v1.1.0 of an official game would find that no official game can ever be updated — on the only path
the MVP exercises.

So the transition is narrowed, and stated as a transition rather than an assignment:

| Current badge | After activation |
|---|---|
| `VERIFIED` | `UNVERIFIED` — re-review required (FR-GAME-014) |
| `UNVERIFIED` | `UNVERIFIED` — no change |
| `OFFICIAL` | `OFFICIAL` — **unchanged.** FR-GAME-014 speaks only of Verified status, and an operator's own upload does not need the operator's approval |

This is also the shape that survives the one-directional-to-equivalence tightening of §1: the check
turned a silent badge corruption into a loud transaction failure, which is what a constraint is for.

### `game_version_active_key` is FR-GAME-010

"Only one version of a game is active at a time" is a partial unique index on `game_id` over
`status = 'ACTIVE'`. Activation is one transaction: the incumbent moves to `SUPERSEDED`, the new row
to `ACTIVE`, `game.active_version_id` is repointed, and the tag projection (§3) is rebuilt. If two
uploads race, one fails on this index rather than leaving a game with two active versions and an
`active_version_id` that names one of them arbitrarily.

### The status set extends `file-uploads.md`, which stops at the upload

[`file-uploads.md`](../api-design/file-uploads.md) defines `PENDING → PROCESSING → ACTIVE | FAILED`,
which is complete for the upload API but leaves a version with no state to move to when it stops
being current. Three states are added:

| Status | Entered when | Requirement |
|---|---|---|
| `EXPIRED` | Confirm never arrived before `upload_expires_at`; the slot is reclaimed | file-uploads.md error table (410 Gone) |
| `SUPERSEDED` | A newer version activated; rooms may still be running on this one | FR-GAME-010, FR-GAME-011 |
| `DISCARDED` | The version is **retired** and no non-closed room references it; bundle purged | FR-GAME-011, FR-ACCT-007 |

`DISCARDED` is a terminal record, not a deleted row: `room.game_version` and
`game_history_entry.game_version` are text and may still name it, and an operator asked why a bundle
is gone needs an answer. The bundle bytes are what actually go away, recorded by `bundle_purged_at`.

### `PROCESSING` needs an exit, and a lease is the only thing that can give it one

`PENDING` expires on `upload_expires_at`. `PROCESSING` had **no exit at all**: a validation job whose
instance dies leaves the row in `PROCESSING` forever, and because `game_version_key` is unique on
`(game_id, version)`, that **permanently burns the version number** — the developer can never retry
`1.2.0`, on any path, for the life of the platform.

`claimed_by` and `claimed_until` are the lease that makes the stuck row detectable. The validator
stamps them when it takes the row from `PENDING` to `PROCESSING` and renews while it works; a sweep
finds `PROCESSING` rows whose `claimed_until` has passed and moves them to `FAILED` with a synthetic
`{check: "pipeline.abandoned"}` entry. `game_version_stuck_idx` serves it, partial because no other
status can be abandoned.

Nothing weaker works. An age check on `created_at` cannot distinguish a slow 256 MB validation from a
dead one, and would have to be set longer than the slowest legitimate run — during which the version
number is still burned. The lease is the standard answer and this is the standard reason for it.

### `FAILED` and `EXPIRED` bundles are purged immediately

Neither status is reachable from the retirement predicate above — retirement is defined over
`SUPERSEDED` and `ACTIVE` — so without a rule here, every failed upload leaves up to 256 MB in object
storage forever. Failed uploads are the *normal* case during development, so "forever" compounds
quickly.

On entry to `FAILED` or `EXPIRED` the stored object is deleted and `bundle_purged_at` is set, with no
status change. Nothing is lost: `validation_errors` is durable in Postgres and independent of the
object, so the developer's error report survives, and they still hold the ZIP they uploaded. The row
stays as the record of the attempt and as the thing §7's reclamation policy consults.

### What "retired" means, and why it is not "superseded"

A version is **retired** when no future room can be created on it. Two disjoint ways to get there:

```sql
status = 'SUPERSEDED'                              -- a newer version took over (FR-GAME-010)
OR (status = 'ACTIVE' AND EXISTS (SELECT 1 FROM game g
      WHERE g.game_id = game_version.game_id
        AND (g.deleted_at IS NOT NULL OR g.archived_at IS NOT NULL)))
```

**The second disjunct is not an embellishment; without it §5's whole amendment does nothing.** A
developer with a single-version game who deletes their account leaves that version `ACTIVE` forever —
no newer version will ever arrive, because the owner is gone — so a discard predicate keyed on
`SUPERSEDED` would never fire, and the bundle bytes FR-ACCT-007 exists to remove would be retained
permanently. The single-version game is the *common* case, so the gap is not a corner. The same
applies to FR-GAME-012's ordinary soft delete.

Discarding an `ACTIVE` version therefore also clears `game.active_version_id`, in the same
transaction. That vacates `game_version_active_key` and leaves the game with no active version, which
is exactly right: it is deleted or archived, `game_public_idx` already excludes it on `deleted_at` /
`archived_at`, and the `active_version_id IS NOT NULL` term of the public predicate is a second,
independent reason it cannot reappear in the catalog.

**One version is never retired: the most recently approved one.** See §5 and OQ-001 — a game whose
current version was rejected must not also lose the artifact of the last version an operator
approved.

The room-reference half of the predicate is
`NOT EXISTS (SELECT 1 FROM room WHERE game_id = :g AND game_version = :v AND state <> 'CLOSED')`,
served by `room_open_game_idx` ([`data-model.md`](data-model.md) §1).

### Derived capability columns exist for the query planner, not for the reader

`min_players`, `max_players` and the three capability flags are computed from
`manifest.teamTemplates` and `manifest.capabilities` at validation time and written once. FR-CAT-002
says min/max players are "derived from the game's team templates and stored server-side", so this is
the requirement's own instruction. `min_players` is the sum of `size.min × count.min` across
templates and `max_players` the sum of `size.max × count.max`; both are recomputable from the stored
`manifest`, which is what makes them a projection rather than a second source of truth.

They live on the version and **not** on `game`, so the catalog reads them through
`game.active_version_id`. Copying them onto `game` would buy single-table index locality for
FR-CAT-006's player-count filter, at the cost of six columns that must be rewritten on every
activation and that can silently disagree with the active version. At catalog scale — tens to low
thousands of games — the join to a primary key costs nothing measurable against NFR-PERF-001's 300 ms
budget, and the drift is a real bug class. If the catalog ever outgrows that, the fix is a
materialized view refreshed at activation, which is a projection with an explicit rebuild rather than
a copy maintained by hand.

`game_version_players_idx` is a btree, and a btree cannot use its second column after a range scan on
the first — so for FR-CAT-006's overlap predicate
(`min_players <= :qmax AND max_players >= :qmin`, a range on both) it narrows on `min_players` and
filters the rest. That is adequate at the scale argued above and is what the index claims; it is not
a full answer to the predicate, and a GiST range index would be the escalation if the catalog ever
made it worth one.

`gdk_api_version` is a copy of `manifest.gdkApiVersion` and earns the column by needing a btree the
`jsonb` cannot give it: GAME-I7's compatibility check asks the reverse question — *which stored
versions fall outside the platform's currently supported GDK range* — which is a range scan over
every version, run when the platform's supported range changes, not a lookup of one document.

### `manifest` is stored whole

Every capability, parameter declaration and team template the platform needs at room-creation and
session-start time is in the manifest. Storing the validated document as `jsonb` means room creation
reads one column instead of reassembling a structure from a dozen, the `parameters` whitelist that
[`../api-design/input-validation.md`](../api-design/input-validation.md) enforces on
`CHANGE_PARAMETERS` has a source, and a validator change can be re-run against historical bundles
without unpacking them from object storage.

`validation_warnings` holds the non-fatal unknown-key warnings `manifest-schema.md` requires the
upload UI to render, and `validation_errors` the `{check, message}` array of a `FAILED` version.

---

## 3. `game_tag`

```sql
CREATE TABLE game_tag (
  game_id  uuid NOT NULL REFERENCES game(game_id) ON DELETE CASCADE,
  tag      text NOT NULL,
  PRIMARY KEY (game_id, tag)
);

CREATE INDEX game_tag_trgm_idx ON game_tag USING gin (lower(tag) gin_trgm_ops);
```

Tags are declared in the manifest and, per FR-GAME-008, change only through a new version upload — so
they belong to the version, not the game. This table is nevertheless keyed by `game_id`: it is the
searchable **projection of the active version's tags**, rebuilt inside the activation transaction of
§2.

The projection exists because FR-CAT-005 matches tags by case-insensitive **substring**, server-side
(`game-catalog.md` CON-002). A `jsonb` array inside `game_version.manifest` cannot carry a trigram
index, and a
version-scoped child table would put a second join and a status filter inside the hottest query in
the catalog to search rows that are never searched — no requirement matches against the tags of a
superseded version.

The same reasoning is why tags are projected and the capability columns of §2 are not: **project only
what needs an index shape the source cannot provide.** The capability columns need a btree, which the
join already gives; the tags need a GIN.

### The trigram indexes and the `pg_trgm` extension

`game_tag_trgm_idx`, `game_title_trgm_idx` (§1) and `app_user_username_trgm_idx`
([`data-model-accounts.md`](data-model-accounts.md) §1) together answer FR-CAT-005 — one search input
matching name, author and tags — and NFR-SCAL-001's requirement that those be indexed. They require
`CREATE EXTENSION pg_trgm`, which is a privileged statement and therefore a baseline-migration
concern rather than something the application can do at startup; see
[ADR-0011](../../decisions/0011-schema-migrations.md).

The same GIN index serves FR-SOC-002's *prefix* match on username, so no separate
`text_pattern_ops` btree is needed.

---

## 4. `game_review`

```sql
CREATE TABLE game_review (
  review_id        uuid PRIMARY KEY,
  game_id          uuid        NOT NULL REFERENCES game(game_id) ON DELETE CASCADE,
  version_id       uuid        NOT NULL REFERENCES game_version(version_id),
  submitted_at     timestamptz NOT NULL DEFAULT now(),
  decided_at       timestamptz NULL,
  decision         text        NULL,   -- APPROVED | REJECTED | WITHDRAWN
  rejection_reason text        NULL,
  decided_by       text        NULL,   -- admin Basic-auth principal, or 'system'

  CONSTRAINT game_review_decision_ck CHECK (
    (decided_at IS NULL AND decision IS NULL AND rejection_reason IS NULL AND decided_by IS NULL)
 OR (decided_at IS NOT NULL AND decision IN ('APPROVED','REJECTED','WITHDRAWN') AND decided_by IS NOT NULL)
  ),
  CONSTRAINT game_review_reason_ck CHECK (decision <> 'REJECTED' OR rejection_reason IS NOT NULL)
);

CREATE UNIQUE INDEX game_review_open_key ON game_review (game_id) WHERE decided_at IS NULL;
CREATE INDEX game_review_queue_idx ON game_review (submitted_at) WHERE decided_at IS NULL;
CREATE INDEX game_review_approved_idx ON game_review (game_id, decided_at DESC)
  WHERE decision = 'APPROVED';
```

**There is no `review_state` column on `game`.** Pending-review is exactly "an undecided row exists
here", and a mirrored enum on `game` would be a second place for that fact to be recorded and a
second place for it to be wrong. `game_review_open_key` guarantees at most one open review per game,
so the existence test is unambiguous; `game_review_queue_idx` is FR-REV-002's queue, ordered oldest
first, over the same partial set.

**The row is the audit trail.** NFR-AUD-001 requires every admin action to be written to the
structured log, and it is — but a log is not queryable from the application, and FR-REV-005's
rejection reason has to be shown to the developer in a notification. `decided_by`, `decided_at` and
`rejection_reason` make the decision durable and attributable to the Basic-auth principal that made
it (FR-ADM-002). Because those credentials are static and shared (`admin-tooling.md` CON-002),
`decided_by` identifies the credential, not a person; that is a limitation of the admin model, not of
this table.

**Rejection is non-destructive** (FR-REV-006): the review row is decided, the game keeps
`badge = 'UNVERIFIED'` and its owner. Whether the developer may then resubmit is `admin-tooling.md`
OQ-001 and is not resolved here; the schema permits it — a second row can be opened once the first is
decided — without asserting the policy.

**`WITHDRAWN` is a third decision, written by the platform rather than an operator.** It closes a
review whose subject stopped being reviewable: the owner deleted their account
([`data-model-accounts.md`](data-model-accounts.md) §5), or deleted the game. Without it, an
undecided row for an archived game sits in FR-REV-002's queue forever, addressed to a developer who
cannot be notified of any outcome. `decided_by` records `system` in that case, which is why the
column's comment admits a non-human principal.

**`version_id` is `NOT NULL`.** An earlier draft made it nullable "so a submission survives its
version being discarded", which is not a hazard: §2 is explicit that `DISCARDED` is a terminal record
and not a deleted row, and the foreign key has no `ON DELETE` action, so nothing can remove the
referenced row. A nullable column would only defeat the stale-decision detection the same paragraph
relies on — a decision made against a version the owner has since replaced is recognisable exactly
because both identifiers are always present.

`game_review_approved_idx` answers one question, asked by §2's discard predicate and by §5: which
version of this game was most recently approved? It is partial because no other decision is ever the
answer.

---

## 5. Defect — FR-ACCT-007 destroys the record FR-GAME-012 preserves

`user-accounts.md` FR-ACCT-007 states that games uploaded by a deleted user are "archived immediately
and made invisible to the public", and that "archived games are **permanently deleted** once no
active game sessions reference them".

That last clause cannot be executed against this schema without breaking two things that other
requirements guarantee:

1. **FR-GAME-012 exists to prevent exactly this.** It makes ordinary deletion a *soft* delete
   explicitly "to preserve game history entries". A hard delete on the account-deletion path destroys
   the same rows by a different route — and it is not the departing user's history that is lost, it
   is every *opponent's*, which is the outcome ADR-0004 was written to avoid.
2. **The condition is unreachable in the sense it intends.** "No active game sessions reference them"
   is satisfiable within minutes, but `game_history_entry` references the game for the lifetime of the
   platform (FR-RET-003, no automated purge). Read as "no references at all", the delete never
   happens; read as "no live sessions", it happens while history still points at it.

**Resolution.** FR-ACCT-007 is amended so that what is permanently deleted is the **bundle
artifacts**, not the catalog row: `game.archived_at` is set immediately (invisibility, which is what
the requirement's first sentence asks for), and once no non-closed room references it, each **retired**
version moves to `DISCARDED` and its bundle is purged. Archival is one of the two ways a version
becomes retired (§2) — the other being ordinary supersession — and it exists in that predicate
because without it a single-version game, which is the common case, would keep its artifacts forever
and this amendment would purge nothing at all. The `game` row is retained, soft-deleted.

The amendment is consistent with FR-RET-005, which already treats artifacts rather than catalog rows
as the thing with a retention policy — though note that FR-RET-005 protects artifacts only "while the
game is listed", so it offers an archived game no protection and no conflict.

This is why `game_history_entry.game_id` carries **no foreign key** to `game`
([`data-model-history.md`](data-model-history.md) §2): even with the amendment, history must not be
able to block or be broken by a catalog operation, for the same reason it holds no reference to the
room.

### 5.1 The last approved version is never discarded

Retirement plus the room-reference test is not sufficient on its own, because of what it does after a
rejection. Follow a Verified, published game with rooms live on v1.1.0 whose owner uploads v1.2.0:
FR-GAME-014 clears the badge, v1.1.0 becomes `SUPERSEDED`, the owner submits, and an operator
**rejects**. The rooms on v1.1.0 eventually end, FR-GAME-011 fires exactly as designed, and the
bytes of the last version an operator ever approved are deleted — leaving a permanently delisted game
whose only surviving artifact is the version that was rejected, with no rollback in §2's status
machine and possibly no resubmission at all (`admin-tooling.md` OQ-001).

The discard predicate of §2 therefore carries one exclusion:

```sql
AND version_id <> (SELECT r.version_id FROM game_review r
                    WHERE r.game_id = game_version.game_id AND r.decision = 'APPROVED'
                    ORDER BY r.decided_at DESC LIMIT 1)
```

served by `game_review_approved_idx` (§4). One bundle per game is retained beyond its useful life,
which is a bounded and small cost against the alternative: an unrecoverable state reached by a
sequence of individually correct operations. The exclusion does not apply on the FR-ACCT-007 path —
an archived game has no owner to recover it and nothing to recover it *to*, so every version is
retired there.

---

## 6. What is deliberately absent

- **No `review_state` on `game`.** §4.
- **No denormalized author username.** Usernames are mutable (FR-ACCT-002); a copy on `game` would go
  stale on the first rename, and FR-CAT-002's author column has to show the current one.
- **No tag taxonomy table.** Tags are free-form with no admin-managed list (`game-catalog.md`
  Out of Scope), so a `tag` dimension table would only add a join.
- **No rating, review or favourite tables.** Out of scope.
- **No `active_player_count` column.** FR-GDET-005 is a live count over open rooms, fetched once per
  page load and explicitly not real-time; a stored counter would need a writer on every join, leave,
  disconnect and room closure to be as correct as one query.
- **No per-version download or play counters.** `completed_session_count` is per game
  (FR-STATS-004); nothing asks for a per-version breakdown.

---

## 7. Open questions

- **OQ-001** — FR-GAME-014 clears Verified at upload and FR-GAME-010 activates the new version
  immediately, so a community game leaves the catalog the moment it is patched and stays out until an
  operator re-approves it (§1). If that re-approval is a **rejection**, the game is stuck: its
  `ACTIVE` version is one an operator refused, the previously approved version is `SUPERSEDED` and
  cannot be reactivated, and §2's status machine has no rollback. §5.1 keeps that version's *artifact*
  from being deleted, so the state is recoverable in principle — but nothing in the schema or the
  requirements says how, and `admin-tooling.md` OQ-001 leaves open whether resubmission is even
  permitted. The clean alternative is a "pending version" distinct from the active one, which the
  single-active-version model of FR-GAME-010 does not have. Dormant for the MVP under ADR-0006; must
  be resolved before community uploads open.
- **OQ-003** — FR-REV-001's "pending review" state has no owner-facing representation. §4 models it
  as an undecided row, which serves FR-REV-002's admin queue, but FR-UPROF-002 gives owners
  management actions per game and FR-PRV-004 lets them submit "at any time" — so a second submission
  is attemptable and fails on `game_review_open_key` as a raw unique violation rather than as a
  domain error. The read is trivial (`EXISTS` over the same partial index); what is missing is a
  requirement saying the owner sees it.
- **OQ-002** — `decided_by` identifies a shared static credential rather than a person
  (`admin-tooling.md` CON-002). Adequate for a single operator; not adequate as an audit trail if the
  operator set ever grows beyond one.

---

## 8. Requirements traceability

| Requirement | Realized by |
|---|---|
| FR-CAT-002/007 | `game` ⋈ `game_version` (active) ⋈ `app_user`; `version_major/minor/patch` |
| FR-CAT-004 | keyset/offset pagination over `game_public_idx` |
| FR-CAT-005 | `game_title_trgm_idx`, `game_tag_trgm_idx`, `app_user_username_trgm_idx` |
| FR-CAT-006 | `game_version_players_idx` (narrows; see §2) |
| FR-GAME-008 | `title` / `short_description` / `info_doc_markdown` on `game`, manifest-seeded once (§1) |
| FR-ACCT-005 (owner deletion) | `game_review` → `WITHDRAWN` (§4) |
| GAME-I7 | `game_version_gdk_idx` |
| FR-GDET-007/008 | `deleted_at`, `game_public_idx` predicate |
| FR-GAME-002/003 | `manifest`, `game_tag` |
| FR-GAME-005/006 | `listed` (default false) |
| FR-GAME-009 | `version_major/minor/patch` + `game_version_format_ck` |
| FR-GAME-010 | `game_version_active_key` |
| FR-GAME-011 | retirement → `DISCARDED` (§2), `room_open_game_idx`, less §5.1's exclusion |
| FR-GAME-012 | `game.deleted_at` |
| FR-GAME-013 / FR-GAME-007 / FR-PRV-002 | room-creation preconditions, §1 *Where the write-side rules are enforced* |
| FR-GAME-014 | `badge` reset at activation; `listed` preserved |
| FR-REV-004 (public visibility) | approval writes `badge` **and** `listed` (§1) |
| FR-BADGE-001…004 | `game.badge` + `game_badge_ck` |
| FR-REV-001…006 | `game_review`, `game_review_open_key`, `game_review_queue_idx` |
| FR-OFF-001/002 | `badge = 'OFFICIAL'`, `game_official_ownerless_ck`, no review row |
| FR-PRV-001 | `badge <> 'UNVERIFIED'` in the public predicate |
| FR-ACCT-007 | `archived_at` + version `DISCARDED`; see §5 |
| FR-STATS-004 | `completed_session_count` (writer in `data-model-history.md` §3) |
| NFR-SCAL-001 | the three trigram indexes + `game_version_players_idx` |
