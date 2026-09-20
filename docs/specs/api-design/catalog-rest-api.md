# Catalog REST API

The HTTP surface `game-catalog.md`'s Catalog Listing and Game Detail sections describe but never give
a shape to: `GET /api/games` and `GET /api/games/{gameId}`. Both are public, read-only, and the only
two routes this document defines — everything else `game-catalog.md` FR-GAME-* names (upload, edit,
delist, delete) is a mutation on a different surface, built by whichever item eventually opens it
(`IMP-M4-01`'s own gate history records the gap rather than closing it here).

Realizes `game-catalog.md` FR-CAT-001…010, FR-GDET-001…009, NFR-PERF-001…002, NFR-SCAL-001,
NFR-SEC-001…002, NFR-USAB-001…002 and `admin-tooling.md` FR-PRV-001.

## Related

| Document | What it supplies |
|---|---|
| [rest-conventions.md](rest-conventions.md) | Status codes, the `/api/games/{id}` read/mutate ownership predicates, the `404`-vs-`403` rule |
| [pagination-filtering-sorting.md](pagination-filtering-sorting.md) | The list envelope, `page`/`size`/`sort` parameters, the `JdbcClient` filtering mechanism |
| [error-handling.md](error-handling.md) | RFC 9457 Problem Details and the type taxonomy |
| [input-validation.md](input-validation.md) § *The game info document* | Why the info doc is returned as raw Markdown, never HTML |
| [../platform/data-model-catalog.md](../platform/data-model-catalog.md) | `game`, `game_version`, `game_tag` — every column this document reads, `game_public_idx`'s visibility predicate |
| [../platform/data-model.md](../platform/data-model.md) §1–2 | `room`, `room_participant` — the active player count `room_open_game_idx` serves |
| [../../requirements/game-catalog.md](../../requirements/game-catalog.md) | FR-CAT-001…010, FR-GDET-001…009 |
| [../../requirements/admin-tooling.md](../../requirements/admin-tooling.md) | FR-PRV-001, FR-BADGE-001…004 |

---

## 1. Endpoints

| Method | Path | Auth | Success | Requirements |
|---|---|---|---|---|
| `GET` | `/api/games` | Public, owner-resolved | `200` | FR-CAT-001…010, NFR-PERF-001, NFR-SCAL-001 |
| `GET` | `/api/games/{gameId}` | Public, owner-resolved | `200` | FR-GDET-001…009, NFR-PERF-002 |

**"Public, owner-resolved"** means no session is required, but a valid `turnbase_session` cookie is
read when present to resolve `principal` for the visibility carve-out below — the same optional-auth
shape `/api/users/{username}` already uses for profile privacy (`rest-conventions.md`). A guest
session resolves to a principal like any other; there is no separate guest rule here.

---

## 2. Visibility

Both endpoints apply `game_public_idx`'s predicate
(`data-model-catalog.md` §1) **unless the resolved principal is the game's owner**:

```sql
deleted_at IS NULL AND archived_at IS NULL AND listed
  AND badge <> 'UNVERIFIED' AND active_version_id IS NOT NULL
```

For the owner, `badge <> 'UNVERIFIED'` and `listed` are both waived — an owner sees and can open their
own Unverified or unlisted game (`admin-tooling.md` FR-PRV-001, `game-catalog.md` FR-GDET-009).
`deleted_at IS NULL` and `active_version_id IS NOT NULL` are **not** waived for anyone, including the
owner: a soft-deleted game is FR-GDET-007's "no longer exists" case (§4), and a game with no active
version has nothing to display regardless of who is asking.

This carve-out is deliberately narrow. `admin-tooling.md` FR-PRV-002 — hosting a room for a private or
Unverified game — is a `/api/rooms` concern, not this document's; nothing here grants a non-owner any
access this predicate does not already give them.

---

## 3. `GET /api/games` — catalog listing

```
GET /api/games?search=chess&minPlayers=2&maxPlayers=4&tags=strategy,card-game&sort=createdAt,desc&page=1&size=25
```

Query parameters, all optional:

| Param | Type | Effect |
|---|---|---|
| `search` | string | Case-insensitive substring match against title, author username, and tag (FR-CAT-005), via `game_title_trgm_idx`, `app_user_username_trgm_idx`, `game_tag_trgm_idx` |
| `minPlayers`, `maxPlayers` | integer | Overlap filter against the active version's `min_players`/`max_players` (FR-CAT-006): `min_players <= :maxPlayers AND max_players >= :minPlayers`, each bound applied only when present |
| `tags` | comma-separated or repeated | Games whose active-version tag projection (`game_tag`) contains **any** of the given tags |
| `page`, `size`, `sort` | per `pagination-filtering-sorting.md` | `size` default 25, max 100 (FR-CAT-004) |

`sort` whitelist (FR-CAT-007), each with `game_id` appended as the tiebreaker: `title`, `author`,
`minPlayers`, `maxPlayers`, `version`, `createdAt`, `updatedAt`. Default: `createdAt,desc`.
`author` sorts on `coalesce(u.username, '')` (`data-model-catalog.md` §1's deterministic-null-owner
rule) — ascending places platform-authored rows first, descending last. An unlisted `sort` field is
`400` (`SortFieldValidator`, `error-handling.md`'s `validation-failed`).

**Response — `200 OK`:**

```json
{
  "content": [
    {
      "gameId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "title": "Chess",
      "authorUsername": "TurnBase",
      "shortDescription": "The classic two-player strategy game.",
      "minPlayers": 2,
      "maxPlayers": 2,
      "supportsAi": true,
      "supportsSpectators": true,
      "version": "1.0.0",
      "badge": "OFFICIAL",
      "createdAt": "2026-08-01T10:00:00Z",
      "updatedAt": "2026-09-01T10:00:00Z"
    }
  ],
  "pagination": { "page": 1, "size": 25, "totalElements": 1, "totalPages": 1 }
}
```

`authorUsername` is always a string, never `null` — a null-owner (Official) row renders `"TurnBase"`
(`data-model-catalog.md` §1). `badge` is one of `OFFICIAL`, `VERIFIED`, `UNVERIFIED`, read from the
single `game.badge` column (FR-BADGE-001) — an Unverified row appears here only when the caller is its
owner (§2). `version`, `minPlayers`, `maxPlayers`, `supportsAi`, `supportsSpectators` are read through
`game.active_version_id` (`data-model-catalog.md` §2's derived capability columns), which visibility
already guarantees is non-null.

`shortDescription` (`game.short_description`) is included on every row so FR-CAT-003's inline row
expansion reveals it from the row the client already fetched — expanding a row triggers no second
network call.

---

## 4. `GET /api/games/{gameId}` — game detail

**Unknown or invisible `gameId` (deleted, unlisted-to-this-caller, Unverified-to-this-caller, or no
active version): `404`**, `error-handling.md`'s `not-found` type — indistinguishable from each other
by design (NFR-SEC-002, FR-GDET-008). **Soft-deleted (`deleted_at IS NOT NULL`) is the one exception**:
FR-GDET-007 requires a distinguishable "this game no longer exists" response, so a request for a
`gameId` that exists in `game` with `deleted_at IS NOT NULL` returns `410 Gone`
(`error-handling.md`'s `gone` type) instead of `404` — the one case in this document where existence
is deliberately revealed, because the row is gone on purpose and forever, not hidden.

The two responses are checked in this order: `deleted_at IS NOT NULL` → `410`; otherwise, fails the
rest of §2's predicate for this caller → `404`.

**Response — `200 OK`:**

```json
{
  "gameId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "title": "Chess",
  "authorUsername": "TurnBase",
  "shortDescription": "The classic two-player strategy game.",
  "infoDocMarkdown": "## How to play\n\n...",
  "minPlayers": 2,
  "maxPlayers": 2,
  "supportsAi": true,
  "supportsSpectators": true,
  "tags": ["strategy", "classic"],
  "version": "1.0.0",
  "badge": "OFFICIAL",
  "activePlayerCount": 4,
  "createdAt": "2026-08-01T10:00:00Z",
  "updatedAt": "2026-09-01T10:00:00Z"
}
```

`infoDocMarkdown` is `game.info_doc_markdown`, returned **verbatim as Markdown source** — never
rendered, never returned as an HTML string (`input-validation.md` § *The game info document*; IR-19).
It is `null` when the developer never supplied one; FR-GDET-003's fallback to `shortDescription` when
absent is a **client-side** rendering choice, not a server default — the field is `null`, not a copy
of `shortDescription`, so the client can tell "absent" from "identical to the short description" and
render the correct one of `IMP-M6-06`'s two Markdown-renderer call sites accordingly.

`activePlayerCount` (FR-GDET-005) is the count of `room_participant` rows with `role = 'PLAYER' AND
left_at IS NULL`, joined to `room` rows for this `gameId` with `state <> 'CLOSED'`
(`data-model.md` §1's `room_open_game_idx`, whose documented purpose is exactly this query). A
participant in grace still counts — `left_at IS NULL` is the same "still holds a slot" predicate the
room lifecycle spec uses elsewhere, and a player who stepped away for a few seconds has not stopped
being in the room. It is computed once per request (NFR-PERF-002 — "no real-time update mechanism is
required"), never pushed.

`tags` is the full `game_tag` projection for this game, ordered by insertion is not guaranteed —
returned alphabetically for a stable response.

---

## 5. Errors

| Status | Cause |
|---|---|
| `400` | Unlisted `sort` field, or `minPlayers`/`maxPlayers`/`page`/`size` failing basic type/range validation |
| `404` | §4's invisible-or-nonexistent `gameId` |
| `410` | §4's soft-deleted `gameId` |

No `401`/`403` on either route — both are public, and §2's carve-out is resolved from an optional
principal rather than enforced as a precondition.

---

## 6. What is deliberately absent

- **No mutation.** Upload, metadata edit, publish/delist, delete (FR-GAME-001…013) are a different,
  not-yet-built surface. `rest-conventions.md`'s Authorization table already names the `/api/games/{id}`
  mutate predicate (owner-only, `404`-then-`403`) for whichever item builds it.
- **No submission endpoint.** `admin-tooling.md` FR-PRV-004 (the owner's submit-for-review action) is
  unclaimed by any item in the registry as of this writing (`admin-rest-api.md` §7 already disclaims
  building it on the Basic-auth surface); it belongs on this listener, session-authenticated, when
  some future item picks it up.
- **No per-game statistics beyond `activePlayerCount`** — `per-game-statistics.md` is explicitly out of
  scope for `game-catalog.md` (*Out of Scope*).

## 7. Requirements traceability

| Requirement | Realized by |
|---|---|
| FR-CAT-001…010 | §3 |
| FR-GDET-001…009 | §4 |
| NFR-PERF-001, NFR-SCAL-001 | §3 — trigram and btree indexes named per filter |
| NFR-PERF-002 | §4 — `activePlayerCount` computed once per request |
| NFR-SEC-001, NFR-SEC-002 | §2, §4 — the visibility predicate and the 404/410 split |
| NFR-USAB-001, NFR-USAB-002 | §4's `410`, §3/§4's `badge` field |
| `admin-tooling.md` FR-PRV-001 | §2 |
