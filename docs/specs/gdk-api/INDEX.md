# GDK API Specifications

Implementation-level design of the **public Game Development Kit (GDK) API** —
the contracts third-party developers code against to build TurnBase games. These
are developer-facing artifacts published to Maven Central / npm, distinct from
the platform-internal GDK Host (which implements them) and the internal gRPC
contract (which they map onto).

## Scope

The compile-time API surface: interfaces, data types, effect/result builders,
and the runtime contract developers must honor. Realizes
`docs/requirements/game-development-experience.md` (FR-GDK-*, FR-FEGDK-*) and the
developer-facing half of `docs/requirements/game-contracts.md`.

## Files

| File | Topic |
|------|-------|
| [backend-gdk-api.md](backend-gdk-api.md) | JVM backend API: `TurnBaseGame<S>`, the four lifecycle hooks, context interfaces (typed inputs), the sealed `Effect` model + `Effects` factory, per-hook result types, `GameOutcome`, `GameState` marker, `Player`/`Team`/`GameParameters`, and the runtime/determinism contract |

> Frontend GDK API (`TurnBaseClient`, postMessage callbacks, `sendAction`) is
> reserved for a future sibling `frontend-gdk-api.md` in this directory.

## Key Decisions

- **Single type parameter** `TurnBaseGame<S extends GameState>`; the action type
  is supplied per call via `ActionContext.action(Class<A>)`, not a second class
  parameter.
- **State is a method parameter and return value** on every hook except
  `onInit`; it is never carried on the context and never crosses the gRPC wire.
- **`Effect` is a sealed interface** with one public record per type, built only
  through the static `Effects` factory — giving the GDK Host an exhaustive map to
  proto while keeping construction funneled.
- **Per-hook result types** (`InitResult`…`PlayerLeftResult`) keep signatures
  self-documenting; a shared fluent builder shape avoids duplicated logic.
- **`onPlayerJoined` has a default no-op**, so a minimal game implements three
  methods (NFR-DX-002).
- **Proto amended:** a `name` field was added to the gRPC `Team` message to back
  the GDK `Team.name()` accessor required by FR-GDK-011.
- **Pre-release:** the API may break between iterations; NFR-COMPAT-001's
  backward-compatibility guarantee does not yet apply.
