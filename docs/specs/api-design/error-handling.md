# Error Handling

## Standard: RFC 9457 Problem Details

All error responses follow [RFC 9457 (Problem Details for HTTP APIs)](https://www.rfc-editor.org/rfc/rfc9457). Spring Boot 3.x includes native `ProblemDetail` support.

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

Upload validation failures (`game-development-experience.md FR-UPLOAD-008`) return 422 `business-rule-violation` with the `errors` extension populated with all validation failures in a single response — same field error structure as validation failures, with `field` replaced by `check` to identify the failed validation rule:

```json
{
  "type": "https://turnbase.io/errors/business-rule-violation",
  "title": "Bundle Validation Failed",
  "status": 422,
  "detail": "The uploaded bundle failed validation.",
  "instance": "/api/games/abc/versions/upload-id/confirm",
  "errors": [
    { "check": "manifest.version", "message": "Version 1.0.0 is not strictly higher than current version 1.2.0" },
    { "check": "backend.gdkClasses", "message": "JAR contains GDK API classes. Declare the GDK API as 'provided' scope." }
  ]
}
```
