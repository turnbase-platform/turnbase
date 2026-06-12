# REST API Conventions

## Base Path

All REST endpoints are served under `/api/`. There is no URL version prefix. API evolution is managed through new routes and deprecation headers — see [Versioning and Deprecation](#versioning-and-deprecation).

## URL Structure

- Plural nouns, lowercase: `/api/games`, `/api/rooms`, `/api/users`
- Hyphenated multi-word segments: `/api/game-rooms`
- Nested resources for owned sub-resources, one level deep: `/api/rooms/{roomId}/players`, `/api/games/{gameId}/versions`
- Flat when nesting would exceed two levels

## HTTP Methods

| Method | Semantics | Success Status |
|--------|-----------|---------------|
| GET | Read resource or collection | 200 |
| POST | Create new resource | 201 + `Location` header pointing to the new resource |
| PUT | Replace full editable representation | 200 |
| PATCH | Targeted partial update (flag, single field, or tightly related field group) | 200 |
| DELETE | Remove resource | 204 |

**PUT vs PATCH:** Use PUT when the client submits the complete editable body of a resource (e.g., updating all game metadata fields together). Use PATCH when the client submits only the changed subset — a single field, a flag toggle, or a group of fields that are always changed together (e.g., toggling profile section visibility).

## Status Codes

| Status | Used for |
|--------|----------|
| 200 OK | Successful read or update |
| 201 Created | Successful creation; `Location` header points to the new resource |
| 202 Accepted | Request accepted for asynchronous processing (e.g. bundle validation) |
| 204 No Content | Successful deletion or action with no response body |
| 400 Bad Request | Input validation failure |
| 401 Unauthorized | Missing, expired, or invalid session token |
| 403 Forbidden | Authenticated but insufficient permission |
| 404 Not Found | Resource does not exist (or is intentionally hidden, e.g. private game — `game-catalog.md NFR-SEC-002`) |
| 409 Conflict | Unique constraint violation (duplicate username, email) |
| 410 Gone | Resource existed but has been permanently removed (e.g. expired upload slot) |
| 422 Unprocessable Entity | Business rule violation (e.g. game version not strictly higher, bundle validation failure) |
| 429 Too Many Requests | Rate limit exceeded — see [rate-limiting.md](rate-limiting.md) |
| 500 Internal Server Error | Unexpected server failure |
| 503 Service Unavailable | Transient upstream failure (e.g. storage unreachable during bundle confirm) |

## Request Format

All request bodies use `Content-Type: application/json`. No XML support.

## Response Format

All response bodies use `Content-Type: application/json`. Successful responses return the resource directly with no wrapper envelope, except list endpoints which include pagination metadata — see [pagination-filtering-sorting.md](pagination-filtering-sorting.md).

Error responses follow RFC 9457 Problem Details — see [error-handling.md](error-handling.md).

## Authentication

All endpoints except those listed as public in `user-accounts.md NFR-SEC-006` require a valid session token delivered as an `httpOnly`, `Secure`, `SameSite=Strict` cookie (`user-accounts.md CON-004`). Unauthenticated requests to protected endpoints receive a 401 response.

## Versioning and Deprecation

No version prefix is used in URLs. Breaking changes are handled by:

1. Adding a new route with the updated contract
2. Marking the old route deprecated in code (`@Deprecated` on the handler method)
3. Attaching deprecation response headers to all responses from the deprecated handler via a filter:

```
Deprecation: Sat, 01 Jan 2027 00:00:00 GMT
Sunset: Sat, 01 Jul 2027 00:00:00 GMT
Link: </api/new-route>; rel="successor-version"
```

Headers follow RFC 8594. No endpoint is removed without a `Sunset` header and at least one release cycle of advance warning. See [openapi-documentation.md](openapi-documentation.md) for how deprecation is reflected in the Swagger UI.
