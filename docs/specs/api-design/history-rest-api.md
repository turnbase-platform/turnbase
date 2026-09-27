# Game History REST API

The HTTP surface `game-history.md`'s Profile History Tab section describes but never gives a shape
to: `GET /api/users/{username}/history`. No document previously defined a read endpoint for
`game_history_entry` at all — `data-model-history.md` built the schema and its three indexes
specifically to answer this tab (FR-HIST-024…026), but nothing exposed them over HTTP
(**`IMP-GATE-81`**).

Realizes `../../requirements/game-history.md` FR-HIST-020…030.

## Related

| Document | What it supplies |
|---|---|
| [rest-conventions.md](rest-conventions.md) | Status codes, the optional-auth "public, privacy-resolved" shape `/api/users/{username}` already uses |
| [pagination-filtering-sorting.md](pagination-filtering-sorting.md) | The list envelope, `page`/`size` parameters |
| [error-handling.md](error-handling.md) | RFC 9457 Problem Details and the type taxonomy |
| [social-rest-api.md](social-rest-api.md) §7 | The privacy-resolved sub-resource pattern this endpoint reuses verbatim |
| [../platform/data-model-history.md](../platform/data-model-history.md) §2 | `game_history_entry` — every column this document reads, the three partial indexes it relies on |
| [../../requirements/game-history.md](../../requirements/game-history.md) | FR-HIST-020…030 |
| [../../requirements/user-accounts.md](../../requirements/user-accounts.md) | FR-PROF-006…007 — the `history` section's visibility rule this endpoint enforces |

---

## 1. Endpoint

| Method | Path | Auth | Success | Requirements |
|---|---|---|---|---|
| `GET` | `/api/users/{username}/history` | Public, privacy-resolved | `200` | FR-HIST-020…029 |

Served under the profile it belongs to, the same way `GET /api/users/{username}/friends`
(`social-rest-api.md` §7) serves the Friends tab's content rather than folding it into the profile
response itself — a history page can be paginated and searched independently of whatever else the
profile loads.

Unknown username → `404`, matching the profile endpoint.

---

## 2. Privacy resolution

**Identical to the friends section's, not a second copy of it.** The profile response's
`visibleSections` already says whether `"history"` is in the set for this `(username, viewer)` pair
(FR-PROF-006…007). This endpoint re-runs the identical check rather than trusting the client to have
read the profile response first. When `"history"` is not visible — private profile, or a public
profile with the history section hidden, and the caller is not the owner — the response is `200` with
an empty `content` array and `pagination.totalElements: 0`, not `403`/`404`: a distinguishable error
here would only repeat what `visibleSections` already discloses, and an empty list is one less shape
for the client to branch on.

The owner sees their own full history regardless of their own privacy settings (FR-HIST-028,
FR-PROF-007). A `GUEST` or soft-deleted profile resolves the same way it does for
`GET /api/users/{username}` — username-only / the erasure placeholder — so this endpoint answers `200`
with an empty `content` array for either, which is also simply correct: guests accrue no history
(FR-HIST-003) and a soft-deleted account's entries are pseudonymized and no longer linked to any
username (`data-model-history.md` §4).

---

## 3. Query parameters and search

| Param | Default | Description |
|---|---|---|
| `page` | `1` | 1-indexed, per `pagination-filtering-sorting.md` |
| `size` | `25` | Max `100`, per `pagination-filtering-sorting.md`; the default matches `game-history.md` FR-HIST-026 |
| `search` | — | Optional. Case-insensitive substring match against the entry's `game_name_snapshot`, applied server-side (FR-HIST-025), using `ghe_user_name_trgm_idx` |

No `sort` parameter is exposed. FR-HIST-024 names one order — `completed_at` descending — and it is
the only one `ghe_user_recent_idx` is built for; there is no second requirement asking for another.

---

## 4. Response shape

```json
{
  "content": [
    {
      "gameId": "3f9c1e2a-...",
      "gameName": "Chess",
      "gameLinkable": true,
      "completedAt": "2026-09-20T14:03:00Z",
      "outcomeLabel": "Victory",
      "playerStats": { "movesPlayed": 41 },
      "teamStats": { "captures": 9 }
    }
  ],
  "pagination": { "page": 1, "size": 25, "totalElements": 1, "totalPages": 1 }
}
```

**`gameName`** is `game_history_entry.game_name_snapshot` (FR-HIST-006, FR-HIST-021), never a live
read of the catalog row — the whole point of the snapshot is that it survives a title change or a
deletion.

**`gameLinkable`** is `true` only when a `game` row for `gameId` exists and its `deleted_at IS NULL`.
It is computed here, server-side, rather than left to the client to discover by calling
`GET /api/games/{gameId}` per entry — `data-model-history.md` §2's own note ("a missing or
soft-deleted row degrades to plain text") is what this field makes literal without an N+1 lookup.
`false` is exactly FR-HIST-023: the card renders `gameName` as plain text, no link.

**`outcomeLabel`** is the platform-derived string FR-HIST-010…013 define, computed at read time from
the stored `draw`, `placement` and `team_count` columns (`data-model-history.md` §2 *"placement and
team_count are stored; the label is not"*) rather than duplicated in the frontend:

| Condition | `outcomeLabel` |
|---|---|
| `draw = true` | `"Draw"` |
| `draw = false`, `placement = 1` | `"Victory"` |
| `draw = false`, `placement > 1`, `team_count = 2` | `"Defeat"` |
| `draw = false`, `placement > 1`, `team_count > 2` | ordinal of `placement`, e.g. `"2nd place"`, `"3rd place"`, `"4th place"` (standard English ordinal suffix rules, including the 11th/12th/13th exception) |

**`playerStats` / `teamStats`** are the entry's `player_stats` / `team_stats` JSONB columns, each
**omitted from the response entirely when empty** (`@JsonInclude(NON_EMPTY)`), matching FR-HIST-022's
"if either map is empty or absent, that section is omitted" — the same omit-rather-than-empty-object
convention `GET /api/users/{username}` already uses for hidden sections.

---

## 5. Requirements traceability

| Requirement | Realized by |
|---|---|
| FR-HIST-020 | The endpoint's existence — a dedicated route, not folded into the profile response |
| FR-HIST-021 | `gameName`, `gameLinkable`, `outcomeLabel`, `completedAt` |
| FR-HIST-022 | `playerStats` / `teamStats`, omitted when empty |
| FR-HIST-023 | `gameLinkable = false` |
| FR-HIST-024 | The endpoint's one, non-configurable sort |
| FR-HIST-025 | `search` |
| FR-HIST-026 | `page` / `size`, reusing `pagination-filtering-sorting.md` |
| FR-HIST-027 | An empty `content` array is a valid, distinguishable `200` — the frontend's empty-state condition (`IMP-M6-06`) |
| FR-HIST-028 | Owner override in §2 |
| FR-HIST-029 | `visibleSections` re-check in §2 |
| FR-HIST-030 | No entry is ever returned once its `user_id` is nulled — §2's resolution already excludes it (partial index) |
