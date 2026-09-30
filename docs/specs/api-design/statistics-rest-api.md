# Per-Game Statistics REST API

The wire shapes `per-game-statistics.md` describes but never gives: the games-played count on the
game detail page (FR-STATS-010…012) and the inline stats on a user profile (FR-STATS-020…027). The
schema side was settled — `data-model-history.md` §3 names the counter's single writer and the two
live queries — but no document named a response field or a route, and `catalog-rest-api.md` §6
explicitly excluded per-game statistics from the detail response (**`IMP-GATE-90`**).

Realizes `../../requirements/per-game-statistics.md` FR-STATS-010…012, FR-STATS-020…027.

## Related

| Document | What it supplies |
|---|---|
| [catalog-rest-api.md](catalog-rest-api.md) §4 | `GET /api/games/{gameId}`, which carries the game-level count |
| [history-rest-api.md](history-rest-api.md) §2 | The privacy resolution this endpoint reuses verbatim |
| [profile-rest-api.md](profile-rest-api.md) | `visibleSections`, whose `"statistics"` member gates §2 |
| [../platform/data-model-history.md](../platform/data-model-history.md) §3 | The counter, its single writer, and the two profile queries with their indexes |

---

## 1. Game-level count — a field of `GET /api/games/{gameId}`

No new route. FR-STATS-012 reads "the game's denormalized session counter", and
`data-model-history.md` §3 calls it "one column read on a row the detail page already loads". The
detail response (`catalog-rest-api.md` §4) gains one field:

```json
{ "completedSessionCount": 1284 }
```

`completedSessionCount` is `game.completed_session_count`, a JSON number (`0` for a game never
completed, never `null`). It is read in the same query as the rest of the row, fetched per request
(FR-STATS-012), and covers registered and guest sessions alike (FR-STATS-003, FR-STATS-010). It is
never decremented and account deletion does not touch it (FR-STATS-004, FR-ACCT-008). The same
visibility, `404` and `410` rules as the rest of §4 apply; the list endpoint (§3) does not carry it.

---

## 2. `GET /api/users/{username}/statistics`

| Method | Path | Auth | Success | Requirements |
|---|---|---|---|---|
| `GET` | `/api/users/{username}/statistics` | Public, privacy-resolved | `200` | FR-STATS-020…027 |

Served under the profile, like `/history` and `/friends`. Unknown username → `404`.

```json
{
  "totalPlayed": 17,
  "mostPlayedGame": { "gameId": "3f9c1e2a-...", "title": "Chess" }
}
```

- `totalPlayed` — `count(*) FROM game_history_entry WHERE user_id = :u`; `0` in the zero state.
- `mostPlayedGame` — the §3 query of `data-model-history.md` (most entries, ties broken by ascending
  `game.title`). `null` in the zero state (FR-STATS-023) — the client renders the placeholder.
  `title` is the live catalog title, not the history snapshot, because the entry links to the
  game's detail page (FR-STATS-022). A game whose row is missing or soft-deleted is skipped in the
  ranking, so the linked game always exists; if no candidate remains, `mostPlayedGame` is `null`.

### 2.1 Privacy resolution

Identical to `history-rest-api.md` §2, applied to the `"statistics"` member of `visibleSections`
(FR-PROF-006…007). When it is not visible to the viewer — private profile, or the section hidden,
and the caller is not the owner (FR-STATS-027) — the response is `200` with the **zero-state body**
`{ "totalPlayed": 0, "mostPlayedGame": null }`, not `403`/`404`. The owner always sees their own
values. A `GUEST` (FR-STATS-026, FR-GUEST-009), a soft-deleted or erased profile answers the same
zero-state `200`: guests accrue no entries, and erased entries are pseudonymized and match no
`user_id` (`data-model-history.md` §4). The client hides the section from `visibleSections` and the
guest envelope, never from this body.

Spectator participation writes no entry (FR-STATS-002) and an unfinished session writes none
(FR-STATS-001); both are enforced by the writer of `data-model-history.md` §1, not here.

---

## 3. Requirements traceability

| Requirement | Realized by |
|---|---|
| FR-STATS-010, FR-STATS-012 | §1 — `completedSessionCount`, read live |
| FR-STATS-011 | Frontend placement only (`IMP-M6-06`) |
| FR-STATS-020, FR-STATS-023 | §2 — `totalPlayed`, zero state |
| FR-STATS-021, FR-STATS-022 | §2 — `mostPlayedGame` with `gameId` for the link |
| FR-STATS-024, FR-STATS-025 | §2 — a separate live endpoint fetched per profile load |
| FR-STATS-026, FR-STATS-027 | §2.1 |
| FR-STATS-001…004 | The single writer of `data-model-history.md` §1/§3 (`IMP-M5-01`) |
