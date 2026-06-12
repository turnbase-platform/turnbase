# OpenAPI Documentation

## Tool

**SpringDoc OpenAPI 3.x** (`springdoc-openapi-starter-webmvc-ui`).

## Endpoints

| Path | Content |
|------|---------|
| `/api/docs` | Swagger UI — interactive browser |
| `/api/docs/openapi.json` | Machine-readable OpenAPI 3.x specification |

Both endpoints are available in all environments. In production, access may be restricted to internal networks via ingress rules.

## Configuration

```yaml
springdoc:
  api-docs:
    path: /api/docs/openapi.json
  swagger-ui:
    path: /api/docs
  default-produces-media-type: application/json
  default-consumes-media-type: application/json
```

## Annotation Conventions

All controllers and DTOs are annotated for documentation:

| Annotation | Location | Purpose |
|-----------|----------|---------|
| `@Tag` | Controller class | Groups related endpoints in the Swagger UI |
| `@Operation` | Handler method | Summary and description of the endpoint |
| `@ApiResponse` | Handler method | Documents each distinct response status with its schema |
| `@Schema` | DTO fields | Descriptions, examples, constraints (min/max length, pattern) |
| `@ParameterObject` | Filter/pagination DTOs | Expands query param objects into individual documented params |

## Shared ProblemDetail Schema

The RFC 9457 `ProblemDetail` response schema (see [error-handling.md](error-handling.md)) is registered globally as a reusable OpenAPI component. All `@ApiResponse` error annotations reference this shared schema. This ensures consistent error documentation across all endpoints without per-endpoint repetition.

Example:

```java
@ApiResponse(responseCode = "400", description = "Validation failed",
    content = @Content(schema = @Schema(ref = "#/components/schemas/ProblemDetail")))
```

## Deprecation

When an endpoint is retired:

1. `@Deprecated` on the Java handler method — SpringDoc renders it as visually deprecated in the Swagger UI
2. A response filter attaches RFC 8594 headers to all responses from deprecated handlers:

```
Deprecation: Sat, 01 Jan 2027 00:00:00 GMT
Sunset: Sat, 01 Jul 2027 00:00:00 GMT
Link: </api/new-route>; rel="successor-version"
```

See [rest-conventions.md — Versioning and Deprecation](rest-conventions.md#versioning-and-deprecation) for the full deprecation policy.
