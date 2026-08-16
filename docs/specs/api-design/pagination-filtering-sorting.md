# Pagination, Filtering, and Sorting

Applies to all GET endpoints that return collections: game catalog, room list, notification center, game version history, etc.

## Pagination

Offset-based, 1-indexed pages. Spring Data's `Pageable` is configured via `PageableHandlerMethodArgumentResolver` with 1-based page indexing (`one-indexed-parameters: true`).

### Query Parameters

| Param | Default | Max | Description |
|-------|---------|-----|-------------|
| `page` | `1` | — | Page number, 1-indexed |
| `size` | `25` | `100` | Items per page |

The `size` maximum of 100 is enforced server-side and capped silently at the maximum value rather than rejecting the request.

### Response Envelope

All list endpoints return this structure:

```json
{
  "content": [ ... ],
  "pagination": {
    "page": 1,
    "size": 25,
    "totalElements": 143,
    "totalPages": 6
  }
}
```

The `pagination` block provides all values required by the navigation controls described in `game-catalog.md FR-CAT-004` (first, prev, next, last, current page, total pages).

### Offset pagination drifts under concurrent insert, and that is accepted

`OFFSET`/`LIMIT` addresses a *position*, not a row. If rows are inserted above the window between two
requests, page 2 re-shows items already seen on page 1; paging backwards can skip one. This is not an
edge case for one list in particular: the **notification centre** is designed around continuous
real-time insertion (`notifications-invitations.md` FR-NOTIF-007) and is paginated by FR-NOTIF-009, so
a notification arriving while the user reads page 1 shifts everything down by one.

**Offset stays, for every list including that one.** The duplicate is visible and self-correcting on
refresh, the affected lists are small and read in a single sitting, and a keyset cursor would have to
be threaded through six endpoints and the `pagination` envelope above — which exists to drive
numbered page controls (FR-CAT-004) that a cursor cannot produce, because a cursor has no page count
and no "jump to last". Paying that cost to remove a duplicate row from a notification list is the
wrong trade for this system.

What the implementation must do is make the drift *bounded* rather than arbitrary: every paginated
query carries a **total ordering** — the sort column plus the primary key as a final tiebreaker. Two
rows with the same `created_at` otherwise sort non-deterministically between requests, which turns a
predictable one-row shift into rows appearing and vanishing at random. `ORDER BY created_at DESC, id
DESC`, never `ORDER BY created_at DESC` alone.

Revisit if a list is ever expected to exceed a few hundred rows under active insert; at that point the
deep-offset scan cost, not the duplicate, is the reason to change.

## Filtering

Filters are expressed as typed query parameters specific to each resource. Comma-separated values or repeated params are both accepted for multi-value filters.

**Examples:**

```
GET /api/games?search=chess&minPlayers=2&maxPlayers=4
GET /api/rooms?status=LOBBY,IN_PROGRESS&gameName=chess&minPlayers=2
GET /api/games?tags=strategy,card-game
```

Server-side filtering is mandatory — client-side filtering is not acceptable (`game-catalog.md CON-002`).

### Implementation

Spring Data JPA Specifications compose filter predicates from query params. Each filterable resource exposes a `SpecificationBuilder` that maps typed query params to JPA predicates and combines them with `AND`. This keeps repository interfaces clean and avoids dynamic JPQL strings.

Filterable endpoints document their accepted filter params via `@ParameterObject` on the filter DTO, which SpringDoc picks up automatically for the Swagger UI.

Database indexes must exist on all filterable and sortable columns. Index requirements are noted in each resource's requirements document (e.g. `game-catalog.md NFR-SCAL-001`).

## Sorting

**Query parameter:** `sort=<field>,<direction>` where direction is `asc` or `desc`. Omitting direction defaults to `asc`. Multiple sort fields are supported by repeating the param:

```
GET /api/games?sort=name,asc
GET /api/games?sort=createdAt,desc&sort=name,asc
```

Only explicitly whitelisted fields are accepted as sort keys per endpoint. Requests specifying an unsupported sort field receive a 400 response with a clear error message listing the accepted fields.

### Implementation

Spring's `Sort` is derived from the `Pageable` resolver. A `SortFieldValidator` component — consulted before the query executes — checks the provided field names against the per-resource whitelist and returns a 400 `validation-failed` Problem Detail if any field is invalid.

### Default Sort

Each list endpoint declares an explicit default sort, applied when no `sort` param is provided. The default matches the requirements for that resource (e.g. `game-catalog.md FR-CAT-007` specifies creation date descending as the catalog default).
