# Game Host & Execution Internals

Implementation-level design of the **Game Host** service and the **Orchestration
Service execution pipeline** that pairs with it — the server-side realization of the
[internal gRPC contract](../internal-grpc/INDEX.md) and the developer-facing
[GDK API](../gdk-api/INDEX.md).

## Scope

How a trusted, official Java game backend is loaded into an Espresso context,
invoked through the GDK Host, has its state serialized and persisted, and how the
resulting effects are delivered exactly once — across normal operation, timeouts,
failures, and crashes. Realizes the FR-CTX/FR-SESS/FR-LOAD/FR-REG/FR-ORCH/FR-ROUTE/
FR-DELIVER/FR-FAIL/FR-SEC/FR-OBS requirements of
`docs/requirements/platform-architecture.md`.

## Files

| File | Topic |
|------|-------|
| [game-host-internals.md](game-host-internals.md) | Process/isolation topology, the GDK Host (guest bridge + host shim) and JSON serialization boundary, FR-CTX→mechanism mapping, context/session/instance model, artifact loading, the shared Redis session record, sequencing/idempotency/crash-recovery (GAME-B2), effect fan-out (GAME-B1 exec half), timeouts & failure mapping, registration/health, observability, config, testing |

## Key Decisions

- **Runtime model:** Espresso inside a hardened container (ADR-0006 owner decision).
  One GraalVM CE 21 host JVM per pod hosts one Espresso `Context` per game-version;
  sessions multiplex within a context. Preserves the Truffle showcase and the
  FR-CTX-012 polyglot roadmap.
- **Isolation split (spike-locked):** Espresso enforces cross-context isolation,
  `System.exit` containment, and forced termination; the **container** enforces
  no-filesystem / no-network / memory cap (Espresso on CE leaks all three). For
  trusted official code these are robustness + defense-in-depth, not an adversarial
  boundary.
- **GDK Host is two halves:** a guest bridge jar (GDK API classes + Jackson +
  context/result impls) on the guest classpath, and a host shim that exchanges only
  JSON strings/primitives across the boundary. The host stays fully game-agnostic.
- **Canonical state = serialized JSON**, held in host memory + Redis; the guest
  (de)serializes per invocation. The serialization engine is a **shared component**
  reused by the test harness/upload validator (structural GRMP-F4 round-trip test).
- **One `TurnBaseGame` instance per session.**
- **Crash-recovery correctness (GAME-B2):** an atomic Redis session record
  `{stateJson, lastAppliedSequence, lastEffects}`, idempotent `CreateSession`, and
  `sequence`-keyed replay give exactly-once application + at-least-once delivery.
- **Scope seam:** covers the execution pipeline end-to-end down to *"hand effect to
  the WebSocket Gateway with recipient set + sequence"*; the client-facing STOMP
  topics/envelope are the game-session WebSocket spec (GAME-B1, planned).
