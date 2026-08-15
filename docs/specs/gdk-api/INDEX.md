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
| [backend-gdk-api.md](backend-gdk-api.md) | JVM backend API: `TurnBaseGame<S>`, the five lifecycle hooks (four mutating + the read-only `onResync`), context interfaces (typed inputs), the sealed `Effect` model + `Effects` factory, per-hook result types, `GameOutcome`, `GameState` marker, `Player`/`Team`/`GameParameters`, and the runtime/determinism contract |
| [frontend-gdk-api.md](frontend-gdk-api.md) | TS/JS frontend API: `TurnBaseClient` (generics for action/event payloads), lifecycle & ready handshake, the five inbound event callbacks, `sendAction`, `InitContext` with role/spectator handling, origin validation, and the platform-shell bootstrap contract |
| [test-harness.md](test-harness.md) | The local test harness: running a game with no platform — topology, two-origin serving, simulated players and lifecycle inputs, the executing serialization round trip, and an explicit list of what it cannot tell you |

## Key Decisions

- **Single type parameter** `TurnBaseGame<S extends GameState>`; the action type
  is supplied per call via `ActionContext.action(Class<A>)`, not a second class
  parameter.
- **State is a method parameter and return value** on every hook except
  `onInit`; it is never carried on the context and never crosses the gRPC wire.
- **`onResync` is the read-only hook** (FR-IN-006): it takes state + a viewer and
  returns that viewer's opaque view — no state, no effects. It is how every client
  obtains its picture of a game (at start, on reconnect, on late join), because the
  platform cannot compose a per-viewer snapshot of state it is forbidden to read.
  Its result becomes the first `game_event` the viewer's frontend receives.
- **`Effect` is a sealed interface** with one public record per type, built only
  through the static `Effects` factory — giving the GDK Host an exhaustive map to
  proto while keeping construction funneled.
- **Per-hook result types** (`InitResult`…`PlayerLeftResult`) keep signatures
  self-documenting; a shared fluent builder shape avoids duplicated logic.
- **`onPlayerJoined` has a default no-op**, so a minimal game implements four
  methods (NFR-DX-002). `onResync` deliberately has **no** default — a default
  empty view would silently produce a blank game for every reconnecting player.
- **Proto amended:** a `name` field was added to the gRPC `Team` message to back
  the GDK `Team.name()` accessor required by FR-GDK-011; a dedicated `Resync` RPC
  was added for the read-only hook (it allocates no sequence and writes no state).
- **Pre-release:** the API may break between iterations; NFR-COMPAT-001's
  backward-compatibility guarantee does not yet apply.

### Frontend

- **`TurnBaseClient<TAction, TEvent>`** with class-level generics; one
  replaceable handler per event; explicit `start()` triggers the ready handshake.
- **Shell-injected bootstrap global** (`window.__TURNBASE__ = { parentOrigin,
  sessionId }`) supplies the trusted origin — never inferred from message traffic.
  The rich init context arrives as the first `init` postMessage.
- **Spectators** represented in one `onInit` via `role: 'player' | 'spectator'`
  and a nullable `self`.
- **Origin validation** requires both `event.origin === parentOrigin` and
  `event.source === window.parent`; outbound posts are never `'*'`-targeted.
- New **bootstrap contract** (§9), honored by
  [`../platform-frontend/shell-architecture.md`](../platform-frontend/shell-architecture.md).

### Test harness

- **The harness does not sandbox, and says so.** Embedding a guest JDK and a Truffle context in a
  developer tool would trade a millisecond startup for a multi-hundred-megabyte download, to catch a
  class of mistake the platform catches anyway. It audits and warns instead.
- **It serves two origins locally** (`localhost` and `game.localhost`). One origin would be simpler
  and would hide every mistake the origin separation exists to catch — a shell accepting `'*'`, or a
  game reading `window.parent.document`, works perfectly until it is deployed.
- **The executing serialization round trip lives here and nowhere else** (FR-HARNESS-010). Upload
  validation is static because NFR-UPLOAD-002 forbids running game code; the two halves together are
  the answer to GRMP lesson F4.
- **It shares the validator and the `ObjectMapper` configuration** rather than reimplementing them. A
  rule enforced differently from the platform is worse than one not enforced, because it teaches the
  developer something false.
