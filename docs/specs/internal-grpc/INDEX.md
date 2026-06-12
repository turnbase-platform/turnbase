# Internal gRPC Specifications

Service-to-service gRPC contracts between platform backend components. These are
**internal** protocols, not client-facing APIs (client-facing protocols live in
[../api-design/](../api-design/INDEX.md)).

## Scope

The internal protocols that connect the Orchestration Service (a domain within the
Platform Monolith) to the Game Host service for game session execution: session
lifecycle, input dispatch, effect return, and Game Host registration/health.

## Files

| File | Topic |
|------|-------|
| [gamehost.proto](gamehost.proto) | proto3 definition of the `GameHostService` (dispatch) and `GameHostRegistryService` (control) services |
| [buf.yaml](buf.yaml) | buf module config for validating/linting the proto (STANDARD ruleset) |
| [orchestration-gamehost-protocol.md](orchestration-gamehost-protocol.md) | Design rationale, topology decision, processing/idempotency semantics, error model, message-size and security/observability rules |

## Key Decisions

- **Topology:** dual service with unary dispatch. Game Host serves the dispatch RPCs (Orchestration is client, dialing the pod from the Redis routing table); Orchestration serves the registry RPCs (Game Host is client, dialing a stable ClusterIP). Chosen over a single Game-Host-initiated bidi stream, which would pin sessions to one Orchestration replica and break statelessness (FR-ORCH-002/006/007).
- **Channel of record is Redis, not the connection** — gRPC connections are disposable; any Orchestration replica can route any input.
- **Unary, atomic responses** — one input in, one ordered effect list out, matching the synchronous game handler; per-session ordering enforced by the Redis queue, not the transport.
- **Per-session `sequence` numbers** give idempotent re-dispatch (at-most-once application) plus a Redis delivery watermark for exactly-once delivery.
- **Two-tier error model** — transport failures via gRPC status codes (reroutable); game-code failures in-band via `ProcessStatus.FAILED` + typed `GameFailure` (retry-limited).
- **Game state never crosses this wire**; all game-defined payloads are opaque `bytes`.
