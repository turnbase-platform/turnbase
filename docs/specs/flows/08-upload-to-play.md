# Flow 08 — From a Bundle on Disk to a Game Being Played

A developer has a built game bundle. This traces it to a room playing it: upload, validation,
catalog, and the first `CreateSession` that loads it into an Espresso context.

**Components:** developer's machine, Platform Monolith, object storage (MinIO/S3), PostgreSQL, Game
Host, and eventually a browser.

**Read [ADR-0006](../../decisions/0006-game-trust-model-java-official-only.md) first.** For the MVP
`runtime: "jvm"` is the only runtime and it is **official-only** — untrusted Java cannot be isolated
on GraalVM CE. So the community path below is fully specified and, in the MVP, only ever walked by a
platform operator. It is specified anyway because retrofitting ownership and review onto a live
catalog is a data migration, and because `game-catalog.md` and `admin-tooling.md` describe the
community path in full.

---

## A. Request an upload slot

| # | Actor | Action | Durable state |
|---|---|---|---|
| 1 | Developer | `POST /api/games/{gameId}/versions` `{version:"1.2.0", bundleSize: 42000000}` | — |
| 2 | Monolith | Tier: upload budget (10/hour) | Redis |
| 3 | Monolith | Version strictly higher than the current active version — compared as **three integers**, not as text (`FR-GAME-009`) | — |
| 4 | Monolith | `bundleSize` within `turnbase.uploads.max-bundle-size` (256 MB, `FR-BUNDLE-006`) | — |
| 5 | Monolith | `INSERT INTO game_version (…, status='PENDING', declared_size_bytes, upload_expires_at)` | **`game_version`** |
| 6 | Monolith | Pre-signed PUT URL via `ArtifactStore` | — |
| 7 | Monolith | `201 {uploadId, uploadUrl, expiresAt}` | — |

**Step 3 is the requirement's own worked example, and text ordering gets it backwards.** `'1.10.0' <
'1.9.0'` as strings, so a text comparison would *reject* the upload `FR-GAME-009` says to accept.
`game_version.version_major/minor/patch` are `GENERATED … STORED` integers and every comparison uses
them.

**Step 7's URL is itself a bearer credential** with the lifetime of `turnbase.uploads.slot-ttl`.
It appears in a response body and is therefore truncated at the query string in every log line
([`secrets-and-configuration.md`](../deployment/secrets-and-configuration.md) §6).

---

## B. Upload, direct to storage

The client `PUT`s the ZIP to `uploadUrl`. **The monolith is not in the transfer** — 256 MB never
passes through the application, which is why `turnbase.http.max-body-size` can be 64 KB without
contradiction.

Confirm: `POST /api/games/{gameId}/versions/{uploadId}/confirm` → `202 Accepted`. The stored object's
actual size is checked against `declared_size_bytes`; larger → `422`. A confirm after `expiresAt` →
`410 Gone`, and the slot moves to `EXPIRED`.

---

## C. Validation, asynchronous

`status='PROCESSING'`. Every check runs and **all failures are reported together**
(`FR-UPLOAD-008`) as a `422` with a `{check, message}` array — a developer should not fix one error
per round trip.

| Stage | Realizes |
|---|---|
| Archive integrity and safety — traversal, symlinks, zip-slip, uncompressed ceiling | [`bundle-format.md`](../manifest/bundle-format.md) |
| `manifest.json` present and parses | `FR-UPLOAD-002` |
| Manifest schema, both layers | [`manifest-schema.md`](../manifest/manifest-schema.md) |
| Declared `backend.path`, `frontend.entryPoint`, `infoDoc` exist in the archive | `FR-UPLOAD-003` |
| Entry class implements `TurnBaseGame` | `FR-UPLOAD-004` |
| GDK API classes absent from the JAR | `FR-UPLOAD-005` |
| `gdkApiVersion` within the supported range | `NFR-COMPAT-001`, GAME-I7 |
| Version strictly higher than active | `FR-UPLOAD-006` |
| Serialization round-trip smoke test | GRMP lesson F4 |

Validation is **static analysis** — no game code is executed (`NFR-UPLOAD-002`). The tension between
that rule and the round-trip test, and how it resolves, is
[`bundle-format.md`](../manifest/bundle-format.md)'s to settle; it is called out here because it is
the one check in the list whose *placement* is a design decision rather than a mechanic.

Unknown manifest keys are **warnings, not failures** — `tag` for `tags`, `capabilites` for
`capabilities` — surfaced alongside a successful result so a typo reaches the developer without
failing the upload. They land in `validation_warnings`.

**On failure**: `status='FAILED'`, `validation_errors` holds the array, the developer polls
`GET …/versions/{uploadId}` or receives `BUNDLE_VALIDATION_COMPLETE` on the SSE stream.

---

## D. Activation

One transaction:

| # | Action |
|---|---|
| 1 | Incumbent `ACTIVE` version → `SUPERSEDED`, `superseded_at = now()` |
| 2 | New version → `ACTIVE`, `activated_at = now()` |
| 3 | `game.active_version_id` repointed |
| 4 | `game_tag` rebuilt from the new manifest's `tags` |
| 5 | `game.badge`: `VERIFIED` → `UNVERIFIED` (`FR-GAME-014`). `OFFICIAL` is untouched |
| 6 | Derived columns written: `min_players`, `max_players`, capability flags |

**Step 1 must precede step 2** because `game_version_active_key` is a non-deferrable partial unique
index. If two uploads race, one fails on that index rather than leaving a game with two active
versions and an `active_version_id` naming one of them arbitrarily.

**Step 4 rebuilds the tag projection; steps 5–6 do not touch `game.title` or
`game.short_description`.** The manifest seeds those **only when the `game` row is created**, on the
first successful activation. Rebuilding them on every activation would silently revert an
`FR-GAME-008` rename the platform had already accepted. This is the one place the catalog's
"projections, never copies" rule is broken, and it is broken because `FR-GAME-008` makes those three
fields owner-editable without a version upload — so they are not projections of anything.

**Step 5 has a consequence worth seeing in one place.** For a community game, chaining `FR-GAME-010`
(activate immediately), `FR-GAME-014` (clear Verified) and `FR-BADGE-004` (Unverified is private)
means publishing a patch takes the game **out of the catalog** and makes it unhostable by anyone but
its owner, until an operator re-approves it. Rooms already running are unaffected — `FR-GAME-011`
keeps the previous version alive while any room references it.

---

## E. Review

| # | Actor | Action |
|---|---|---|
| 1 | Developer | Submits for review (`FR-PRV-004`) → `INSERT INTO game_review (game_id, version_id)` |
| 2 | — | `game_review_open_key` (partial unique on undecided) permits exactly one open review per game |
| 3 | Operator | `GET /admin/reviews` on the **loopback-bound management port**, HTTP Basic (`FR-ADM-001/002`). Ordered by `submitted_at` ascending via `game_review_queue_idx` |
| 4 | Operator | Approve → `decision='APPROVED'`, `badge='VERIFIED'`, **and `listed=true`**; `GAME_APPROVED` notification |
| 4b | Operator | Reject → `decision='REJECTED'` + reason; badge stays `UNVERIFIED`; `GAME_REJECTED` notification carrying the reason (`FR-REV-005/006`) |

**Step 4 writes `listed` as well as `badge`, and that is a fix.** `FR-REV-004` says approval "makes it
publicly visible in the catalog" — but a first-time game has `listed=false` from `FR-GAME-005`'s
default, so a badge-only approval leaves it invisible and the requirement unimplemented. Writing both
is safe rather than presumptuous because approval is only reachable through `FR-PRV-004`'s voluntary
submission: nobody is published who did not ask to be.

**There is no `review_state` column on `game`.** Pending-review is exactly "an undecided row exists",
and a mirrored enum would be a second place for that fact to be wrong.

---

## F. In the catalog

Public visibility is one conjunction, indexed by `game_public_idx`:

```
deleted_at IS NULL AND archived_at IS NULL AND listed
  AND badge <> 'UNVERIFIED' AND active_version_id IS NOT NULL
```

Search (`FR-CAT-005`) matches one input against name, author and tags by case-insensitive substring,
server-side (`CON-002`), over three trigram GIN indexes: `game_title_trgm_idx`, `game_tag_trgm_idx`
and `app_user_username_trgm_idx`. The last is partial on `kind='REGISTERED' AND deleted_at IS NULL`,
so guests and deleted-account tombstones cannot surface in a search that also serves `FR-SOC-002`.

---

## G. Serving and playing

The validated bundle is unpacked into `/g/{gameId}/{version}/`
([`game-asset-serving.md`](../game-frontend/game-asset-serving.md) §4.1), served from
`http://{gameId}.games.localhost:8080` — a **different registrable domain** from the platform origin
(ADR-0007).

| # | Component | Action |
|---|---|---|
| 1 | Monolith | Room created; `room.game_version` pinned from `game.active_version_id` at that moment |
| 2 | Monolith | `START_GAME` → `CreateSession(gameId, version, …)` |
| 3 | Game Host | Selects a warm Espresso context for `(gameId, version)` or creates one; fetches the JAR from the artifact store through its cache |
| 4 | Espresso | Guest classloader loads the game; `onInit` at sequence 0 |
| 5 | Client | Loads `gameFrontendUrl` into a sandboxed iframe; the shell's trusted postMessage origin is exactly `new URL(gameFrontendUrl).origin` |

**Step 1 pins the version at room creation, not at session start.** A rematch after a mid-lobby
publish plays the same code the first game did.

**Step 3 is why `SUPERSEDED` exists as a distinct state.** A version that is no longer current may
still be loaded by the Game Host for as long as a room references it; only when no non-closed room
does can it be discarded and its bundle purged.

---

## H. End of life

| Transition | When |
|---|---|
| `ACTIVE` → `SUPERSEDED` | A newer version activates |
| retired → `DISCARDED` | No non-closed room references it, and it is not the most recently approved version |
| bundle purged | With `DISCARDED`; `bundle_purged_at` records it |

**"Retired" is not the same as "superseded",** and conflating them leaves the common case broken. A
single-version game whose owner deletes their account never gets a newer version, so a discard
predicate keyed on `SUPERSEDED` would never fire and `FR-ACCT-007`'s artifact purge would purge
nothing at all. Retirement is therefore `SUPERSEDED` **or** `ACTIVE` on a game that is archived or
deleted.

**The most recently approved version is never discarded.** Without that exclusion, the sequence
"upload → badge cleared → submit → *rejected* → old rooms end" deletes the bytes of the last version
an operator ever approved, leaving a permanently delisted game whose only surviving artifact is the
one that was rejected — reached entirely by individually correct operations.

---

## Defects surfaced

| Defect | Fix |
|---|---|
| `FR-ACCT-007` permanently deleted the game record that `FR-GAME-012` soft-deletes specifically to preserve history — and the loss falls on *opponents'* records, which ADR-0004 exists to prevent | `FR-ACCT-007` amended: artifacts are purged, the row is retained ([catalog §5](../platform/data-model-catalog.md)) |
| `DISCARDED` was unreachable for a single-version archived game, so that amendment purged nothing in the common case | "Retired" defined as two disjoint conditions ([catalog §2](../platform/data-model-catalog.md)) |
| `FR-REV-004`'s "makes it publicly visible" was unimplemented for a first approval — `listed` stayed `false` | Approval writes both fields (§E) |
| Rejecting a new version eventually destroys the last approved bundle, an unrecoverable state reached by correct operations | Discard predicate excludes the most recently approved version ([catalog §5.1](../platform/data-model-catalog.md)) |
| Whether activation rebuilds `title`/`short_description` from the manifest was unspecified; one reading silently reverts an accepted rename, the other makes a required manifest field permanently ignored | Manifest seeds them once, at `game` row creation ([catalog §1](../platform/data-model-catalog.md)) |
| `game_review.version_id` was nullable on a premise the status machine denies (`DISCARDED` is a record, not a deletion), defeating stale-decision detection | `NOT NULL` |
| An open review outlived its owner's account deletion, sitting in the admin queue forever addressed to a developer who cannot be notified | `WITHDRAWN` decision, written by the erasure transaction |
