# Error Handling

## Standard: RFC 9457 Problem Details

All error responses follow [RFC 9457 (Problem Details for HTTP APIs)](https://www.rfc-editor.org/rfc/rfc9457). Spring Framework (6.0+, and so Spring Boot 4.1) includes native `ProblemDetail` support.

Enable the baseline with:

```properties
spring.mvc.problemdetails.enabled=true
```

This automatically wraps standard Spring MVC exceptions (`MethodNotAllowedException`, `HttpMessageNotReadableException`, `NoHandlerFoundException`, etc.) in Problem Detail format.

## Response Shape

```json
{
  "type": "https://turnbase.io/errors/validation-failed",
  "title": "Validation Failed",
  "status": 400,
  "detail": "One or more fields failed validation.",
  "instance": "/api/users",
  "errors": [
    { "field": "username", "message": "Username already taken" },
    { "field": "password", "message": "Must be at least 8 characters" }
  ]
}
```

| Field | Description |
|-------|-------------|
| `type` | Stable URI identifying the error category. Does not need to resolve in Phase 0 but follows the pattern so a documentation page can be added later. |
| `title` | Human-readable summary of the error type. Consistent for the same `type`. |
| `status` | HTTP status code (mirrors the response status). |
| `detail` | Human-readable explanation specific to this occurrence. |
| `instance` | The request path that triggered the error. |
| `errors` | Extension field. Array of field-level validation errors. Present only on `validation-failed` responses. Omitted on all other error types. |

## Error Type Taxonomy

| Type slug | Full `type` URI | Status | Used for |
|-----------|-----------------|--------|----------|
| `validation-failed` | `.../errors/validation-failed` | 400 | Bean Validation failures, malformed request body |
| `unauthenticated` | `.../errors/unauthenticated` | 401 | Missing, expired, or invalid session token |
| `forbidden` | `.../errors/forbidden` | 403 | Authenticated but insufficient permission |
| `not-found` | `.../errors/not-found` | 404 | Resource does not exist |
| `conflict` | `.../errors/conflict` | 409 | Unique constraint violations (username, email) |
| `gone` | `.../errors/gone` | 410 | Resource existed but is permanently unavailable (e.g. expired upload slot) |
| `payload-too-large` | `.../errors/payload-too-large` | 413 | Request body exceeds the 64 KB cap — see [input-validation.md](input-validation.md) |
| `business-rule-violation` | `.../errors/business-rule-violation` | 422 | Domain rule failures (e.g. version not strictly higher, bundle validation errors) |
| `rate-limit-exceeded` | `.../errors/rate-limit-exceeded` | 429 | Too many requests — see [rate-limiting.md](rate-limiting.md) |
| `internal-error` | `.../errors/internal-error` | 500 | Unexpected server failures |
| `service-unavailable` | `.../errors/service-unavailable` | 503 | Transient upstream failure |
| `room-unavailable-retry` | `.../errors/room-unavailable-retry` | 503 | The room's owning instance could not be reached; the caller must back off and re-run the join flow. Carries a `retryAfterMs` extension alongside `Retry-After`. Deliberately distinct from `service-unavailable` and named to match the STOMP error code of the same condition — see [room-rest-api.md](room-rest-api.md) §7 |

### WebSocket errors are not Problem Details

This document covers **REST only**. A WebSocket command failure is delivered as an `ERROR` frame on
`/user/queue/errors` carrying a `code`, `correlationId` and optional `details` — a different envelope
with a different vocabulary, and no `type` URI or HTTP status. The taxonomy above does not apply and
must not be forced onto it: a STOMP frame has no status line, and inventing one would give clients two
error shapes that look interchangeable and are not.

**The registry of every WebSocket error code lives in
[room-websocket.md](room-websocket.md) § *Error codes*** — including the two game-session codes,
`ACTION_TOO_LARGE` and `ACTION_REJECTED`. Build the client-side enum from that one table.

The two vocabularies meet in exactly one place: `room-unavailable-retry` (REST) and
`ROOM_UNAVAILABLE_RETRY` (STOMP) are the same condition on the two transports, deliberately named to
match, and both carry `retryAfterMs`.

## Implementation: @ControllerAdvice

A single `GlobalExceptionHandler` extends `ResponseEntityExceptionHandler`:

```java
@ControllerAdvice
public class GlobalExceptionHandler extends ResponseEntityExceptionHandler {
    // MethodArgumentNotValidException  → 400 validation-failed with field errors array
    // ConstraintViolationException     → 400 validation-failed with field errors array
    // NotFoundException subclasses     → 404 not-found
    // ConflictException subclasses     → 409 conflict
    // BusinessRuleException subclasses → 422 business-rule-violation
    // Catch-all Exception              → 500 internal-error (stack trace logged, never in response)
}
```

Domain exceptions form a shallow hierarchy — `DomainException` → `NotFoundException`, `ConflictException`, `BusinessRuleException` — so the handler maps them by supertype. Adding a new domain exception inherits the correct mapping automatically without modifying the handler.

The `errors` array for field-level validation failures is added via `ProblemDetail.setProperty("errors", fieldErrors)`.

Stack traces are logged at `ERROR` level with the correlation request ID but are never included in the response body.

## Bundle Validation Errors

Bundle validation failures (`game-development-experience.md FR-UPLOAD-008`) use the `{check, message}`
entry shape — the same structure as field validation errors, with `field` replaced by `check` to
identify the failed rule. They are reported over **two** different responses, because validation
happens in two phases and no single response can carry both.

### Synchronous — `422` from the request that failed

Checks that run before the platform accepts what that request asked for fail the request that made
them, in this shape. Two requests can produce it, not one: `POST /api/games/{gameId}/versions`
(stages A1-A4 — version format, ordering, declared size) and `POST
/api/games/{gameId}/versions/{uploadId}/confirm` (stage B1 — the stored object exists and its size
does not exceed what was declared, [file-uploads.md](file-uploads.md) § Size Validation). Both are
checks the platform can evaluate before doing anything asynchronous, and both fail the request that
triggered them rather than the version resource:

```json
{
  "type": "https://turnbase.io/errors/business-rule-violation",
  "title": "Upload Rejected",
  "status": 422,
  "detail": "The requested version cannot be uploaded.",
  "instance": "/api/games/abc/versions",
  "errors": [
    { "check": "manifest.version", "message": "Version 1.0.0 is not strictly higher than current version 1.2.0" }
  ]
}
```

`confirm`'s own synchronous outcomes are not limited to this shape — `410 Gone` (the slot expired)
and `503` (storage unreachable) are ordinary Problem Details with no `errors` array, per
[file-uploads.md](file-uploads.md)'s error table. Only stage B1 uses the `{check, message}` shape,
because it is the one confirm-time check this taxonomy actually governs.

### Asynchronous — `200` from the version resource

Everything that requires the bundle bytes *and cannot be checked before storing them* — manifest
schema, entry points, GDK class absence, serializability — runs **after** `confirm` has already
returned `202 Accepted` ([file-uploads.md](file-uploads.md)). There is no request left to fail for
any of this. The result is the **state of the version resource**, read from `GET
/api/games/{gameId}/versions/{uploadId}`:

```json
{
  "uploadId": "550e8400-e29b-41d4-a716-446655440000",
  "version": "1.2.0",
  "status": "FAILED",
  "createdAt": "2026-06-11T13:00:00Z",
  "errors": [
    { "check": "backend.gdkClasses", "message": "JAR contains GDK API classes. Declare the GDK API as 'provided' scope." }
  ],
  "warnings": [
    { "check": "manifest.capabilites", "message": "Unrecognized key 'capabilites' — did you mean 'capabilities'?" }
  ]
}
```

**A Problem Detail is wrong here and the distinction is not pedantic.** The `GET` succeeded: it was
asked for the state of a version and it returned it. Answering `422` would tell a client that *its
request* was unprocessable, and a client that treats 4xx as "retry differently" will loop against a
resource whose state is never going to change. `FR-UPLOAD-008`'s "all failures in one response" holds
within each phase, which is the most that is possible — a check on the archive cannot be reported by
a response sent before the archive was uploaded.

`warnings` is present on success too, carrying non-fatal findings such as unrecognized manifest keys
(`manifest-schema.md`), and never on its own causes a rejection.

*An earlier version of this section showed one `422` from `…/confirm` mixing a step-1 synchronous
check with an async one — a response that cannot be produced, from an endpoint that returns `202`.*
