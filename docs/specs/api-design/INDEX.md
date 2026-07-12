# API Design Specifications

This directory defines the TurnBase platform API design: conventions, protocols, and patterns for all client-server communication exposed by the Platform Monolith.

## Scope

These specifications cover the HTTP REST API, WebSocket protocol, and SSE channel consumed by the React frontend. Internal service-to-service communication (gRPC between Orchestration Service and Game Host) is defined in [../internal-grpc/](../internal-grpc/INDEX.md).

## Files

| File | Topic |
|------|-------|
| [rest-conventions.md](rest-conventions.md) | URL structure, HTTP methods, status codes, versioning and deprecation strategy, CORS/Origin policy and CSRF |
| [pagination-filtering-sorting.md](pagination-filtering-sorting.md) | List endpoint conventions: pagination, filtering, sorting |
| [error-handling.md](error-handling.md) | RFC 9457 Problem Details, `@ControllerAdvice`, error taxonomy |
| [file-uploads.md](file-uploads.md) | Pre-signed URL upload flow for game bundles |
| [websocket.md](websocket.md) | STOMP-over-WebSocket: topics, authentication, message envelope — **and the game session protocol**: effect delivery destinations, game event catalogue, `resync`-based catch-up, action-send authorization |
| [room-websocket.md](room-websocket.md) | Room WebSocket protocol: room affinity, lobby event catalogue, command catalogue, authorization |
| [room-chat-websocket.md](room-chat-websocket.md) | Room chat WebSocket protocol: CHAT_MESSAGE event, SEND_CHAT_MESSAGE command, spectator exclusion |
| [sse-notifications.md](sse-notifications.md) | Server-Sent Events for platform notifications |
| [rate-limiting.md](rate-limiting.md) | Rate limiting tiers, Bucket4j + Redis implementation |
| [openapi-documentation.md](openapi-documentation.md) | SpringDoc OpenAPI 3.x, Swagger UI, deprecation markers |

## Key Decisions

- No URL versioning — evolution via new routes + `Deprecation`/`Sunset` headers (RFC 8594)
- RFC 9457 Problem Details for all error responses
- Offset-based 1-indexed pagination with typed query param filtering backed by JPA Specifications
- Pre-signed URL flow for game bundle uploads (MinIO in dev/test via Testcontainers, S3 in production)
- Single multiplexed STOMP-over-WebSocket per client for game and lobby real-time events
- Game effects are routed by destination, not filtered on the client: `broadcast` → session topic, `send_to_team` → membership-validated team topic, `send_to_player` → per-user queue (NFR-SEC-002)
- A client attaching to a game session catches up by asking the **game backend** for its current view (read-only `resync`), not by replaying a platform-held effect journal
- Separate SSE stream per authenticated user for platform notifications
- Bucket4j + Redis for distributed rate limiting across monolith replicas
- CORS is default-deny and state-changing requests are **Origin-checked server-side** — CORS blocks reading a response, not sending the request, so it is not a CSRF defense on its own. Game frontends are cross-site by construction ([game-frontend/](../game-frontend/INDEX.md)), which is what keeps the `SameSite=Strict` model sound.
