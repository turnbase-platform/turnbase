# Backend GDK API — `TurnBaseGame`, Effects, Inputs & Lifecycle Hooks

Implementation-level design for the **public backend Game Development Kit (GDK)
API** — the Java surface that third-party developers implement to build a
TurnBase game backend.

This spec realizes the developer-facing half of the contract:

- **Requirements:** `docs/requirements/game-development-experience.md`
  (FR-GDK-001…016, NFR-DX-001/002, CON-001/003/004/007) and
  `docs/requirements/game-contracts.md` (FR-IN-*, FR-RESP-*, FR-EFF-*,
  FR-OUTCOME-*, FR-STATE-*, FR-PROC-*).
- **Wire realization:** the types here map onto
  `docs/specs/internal-grpc/gamehost.proto`. The GDK API is what the developer
  sees; the GDK Host (platform-internal, never distributed) translates between
  this API and the gRPC messages.

> **Pre-release status.** The GDK API is pre-1.0. Breaking changes are expected
> and acceptable between iterations; the backward-compatibility guarantee of
> NFR-COMPAT-001 does **not** yet apply. The compatibility regime begins at the
> first stable major release.

---

## 1. Scope

**In scope:** the JVM backend API — the `TurnBaseGame<S>` interface and its four
lifecycle hooks, the per-hook context interfaces (the typed *inputs*), the
effect model and `Effects` factory, the per-hook result types, the structured
`GameOutcome`, the `GameState` marker, and the supporting data model
(`Player`, `Team`, `GameParameters`).

**Out of scope (separate specs):**

- Frontend GDK (`TurnBaseClient`, postMessage callbacks, `sendAction`) —
  reserved for a sibling `frontend-gdk-api.md`.
- GDK Host internals (in-process invocation, Truffle contexts, serialization
  engine) — `../game-host/game-host-internals.md`.
- Game bundle/manifest format, upload pipeline, test harness — covered by
  `game-development-experience.md` and forthcoming specs.

---

## 2. Artifact & packaging

| Property | Value |
|----------|-------|
| Maven coordinates | `io.turnbase:turnbase-sdk` |
| npm (FE half, separate) | `@turnbase/gdk` (not covered here) |
| Dependency scope | `provided` (Maven) / `compileOnly` (Gradle) — **must not** be bundled in the game JAR (FR-GDK-014, FR-UPLOAD-005) |
| Bytecode target | Java 21 (CON-007); no Java 22+ APIs |
| Contents | Interfaces, records, enums, builders **only** — no `main`, no I/O, no serialization logic (FR-GDK-015) |

### Package layout

| Package | Contents |
|---------|----------|
| `io.turnbase.gdk` | `TurnBaseGame`, `GameState` |
| `io.turnbase.gdk.context` | `InitContext`, `ActionContext`, `PlayerJoinedContext`, `PlayerLeftContext`, `PlayerLeftReason` |
| `io.turnbase.gdk.effect` | `Effect` (sealed) + variants, `Effects` factory |
| `io.turnbase.gdk.result` | `InitResult`, `ActionResult`, `PlayerJoinedResult`, `PlayerLeftResult` |
| `io.turnbase.gdk.model` | `Player`, `Team`, `GameParameters`, `GameOutcome` |

All types listed below are `public`. Context and result *interfaces* are
interfaces so the platform can evolve implementations independently (FR-GDK-003);
value types are `record`s.

---

## 3. The game interface & lifecycle hooks

A game backend is a single class implementing `TurnBaseGame<S>`, where `S` is the
developer's game-state type (FR-GDK-001). The manifest's backend entry point
names this class (FR-MANIFEST-008).

```java
package io.turnbase.gdk;

import io.turnbase.gdk.context.*;
import io.turnbase.gdk.result.*;

/**
 * A TurnBase game backend. Implemented by game developers; instantiated and
 * invoked by the GDK Host. Implementations must be deterministic functions of
 * their inputs (see §9) and hold no mutable static state.
 *
 * @param <S> the game-state type, a JSON-serializable type implementing
 *            {@link GameState}
 */
public interface TurnBaseGame<S extends GameState> {

    /** Game start. No prior state exists; the result establishes the initial
     *  state (FR-IN-002, FR-STATE-005). */
    InitResult<S> onInit(InitContext ctx);

    /** A player submitted an action (FR-IN-003). */
    ActionResult<S> onAction(S state, ActionContext ctx);

    /** A player joined mid-session (FR-IN-004, Should). Default: state
     *  unchanged, no effects. Override to react to late joins. */
    default PlayerJoinedResult<S> onPlayerJoined(S state, PlayerJoinedContext ctx) {
        return PlayerJoinedResult.of(state);
    }

    /** A player was confirmed lost — grace period expired or host kick
     *  (FR-IN-005). Never invoked during the grace period (CON-007). */
    PlayerLeftResult<S> onPlayerLeft(S state, PlayerLeftContext ctx);

    /**
     * Compose this viewer's current picture of the game (FR-IN-006).
     *
     * <p>Invoked every time a client attaches to the session: at game start, on
     * reconnection, and on mid-game join. The returned view is delivered to that
     * viewer alone, and is the first {@code game_event} their frontend receives.
     *
     * <p><b>Read-only.</b> Returns a view payload — no state, no effects. The
     * platform persists nothing from it. Return exactly what this viewer is
     * entitled to see: their own hidden information plus the public position for
     * a player, and the public position alone for a spectator
     * ({@code ctx.role()}), because the platform cannot filter an opaque payload
     * on the game's behalf (NFR-SEC-002).
     *
     * <p>Initial state must be established here rather than in {@code onInit}'s
     * effects: at game start no client has subscribed yet, so {@code onInit}
     * effects are not delivery-guaranteed (FR-FE-001).
     */
    ViewResult onResync(S state, ResyncContext ctx);
}
```

**State as parameter and return value (FR-IN-001, FR-RESP-002).** Every hook
except `onInit` receives the current state as its first parameter and returns the
next state in its result. The state is never carried on the context; the GDK Host
holds it in local memory between invocations and supplies it here. A result
**must** always carry a state, even if unchanged.

**Minimal implementation surface (NFR-DX-002).** `onInit`, `onAction`,
`onPlayerLeft`, and `onResync` are abstract; `onPlayerJoined` has a default. A
game that does not support mid-game join implements **four** methods — the top of
the 2–4-method target. `onResync` has no default deliberately: a default would
have to return an empty view, which silently produces a blank game for every
reconnecting player. Failing to compile is the better outcome.

---

## 4. Contexts (typed inputs, Platform → Game BE)

Each hook receives a read-only context interface exposing exactly the data the
corresponding input carries (FR-GDK-003…007). Contexts never expose game state.

```java
package io.turnbase.gdk.context;

import io.turnbase.gdk.model.GameParameters;
import io.turnbase.gdk.model.Player;
import io.turnbase.gdk.model.Team;
import java.util.List;

/** init input. */
public interface InitContext {
    /** Teams with their assigned players, as configured in the lobby. */
    List<Team> teams();
    /** Host-configured game parameters (FR-GDK-004). */
    GameParameters parameters();

    /**
     * A deterministic random seed for this session.
     *
     * <p>§9 forbids "randomness without a seed carried in state". This is that seed. Use it to
     * construct {@code new Random(ctx.seed())} and carry the resulting values — or the seed
     * itself — in game state; never call {@code new Random()}, {@code Math.random()}, or any
     * clock.
     *
     * <p>Derived by the GDK Host from the session id, so it is stable for the life of a session
     * and across any replay of {@code CreateSession}, and different for every rematch (a rematch
     * is a new session with a new id). Two sessions never share a seed; one session never
     * changes it.
     */
    long seed();
}

/** action input. */
public interface ActionContext {
    /** The acting player; identity is attached server-side and cannot be
     *  spoofed by the FE (FR-FA-002, NFR-SEC-001). */
    Player player();

    /**
     * Deserialize the opaque action payload into the developer's action type
     * (FR-GDK-005). The GDK Host performs JSON deserialization.
     *
     * @param type the action class; for a game with multiple move kinds this is
     *             typically one sealed interface (e.g. {@code Move.class})
     * @throws ActionDecodeException if the payload cannot be read as {@code type}
     */
    <A> A action(Class<A> type);
}

/** player_joined input. */
public interface PlayerJoinedContext {
    Player player();
}

/** player_left input. */
public interface PlayerLeftContext {
    Player player();
    PlayerLeftReason reason();
}

public enum PlayerLeftReason {
    /** Grace period expired without reconnection (reconnection-flow.md). */
    GRACE_PERIOD_EXPIRED,
    /** The host kicked the player. */
    KICKED,
    /** Confirmed voluntary departure mid-game; bypasses the grace period
     *  (FR-IN-005, reconnection-flow.md FR-DC-005). */
    LEFT
}

/** resync input — read-only view request for one viewer (FR-IN-006). */
public interface ResyncContext {
    /** Whether the viewer is playing or spectating. */
    ViewerRole role();

    /** The viewing player, or empty for a spectator (who holds no player
     *  identity in the session). */
    java.util.Optional<Player> viewer();
}

public enum ViewerRole { PLAYER, SPECTATOR }
```

**Action typing.** `action(Class<A>)` takes a class token because
`TurnBaseGame<S>` is parameterized on state only — the action type is not known
at the class level, so it is supplied per call. Developers are encouraged to
model all moves as a single (often `sealed`) type and decode once:
`Move move = ctx.action(Move.class)`. Generic container payloads
(`List<Foo>`, etc.) are not directly supported by the class-token form; wrap them
in a named type. `ActionDecodeException` is an unchecked exception in
`io.turnbase.gdk.context`; throwing it (or any exception) from a hook surfaces as
`GAME_FAILURE_KIND_HANDLER_EXCEPTION` on the wire (see §9).

---

## 5. Data model

```java
package io.turnbase.gdk.model;

import java.util.List;
import java.util.UUID;

/** A player as seen by game code. Maps to proto {@code PlayerRef}. */
public record Player(UUID id, String displayName, UUID teamId) {}

/** A team and its players, as configured in the lobby. Maps to proto
 *  {@code Team}. {@code name} is resolved from the manifest team template. */
public record Team(UUID id, String name, List<Player> players) {}
```

UUIDs are exposed as `java.util.UUID` (the wire carries canonical strings; the
GDK Host converts). `Team.name()` is the team's lobby **instance** display name
(`"{template.name} {index}"`, e.g. `"Attacker 1"`, `"Team 2"`), resolved from the
manifest team template by the Orchestration Service — see §10 for the wire
dependency this introduces.

### `GameParameters`

Typed, read-only access to host-configured parameters (FR-GDK-011). The
accessor set mirrors the manifest parameter types (FR-MANIFEST-005): `integer`,
`decimal`, `boolean`, `string`, `enum`. Parameters always resolve to a value
(the manifest declares a default for every parameter), so the required getters
never return absent; `Optional` variants exist for code that wants to branch on
explicit host configuration.

```java
public interface GameParameters {
    int     getInt(String key);
    double  getDecimal(String key);
    boolean getBoolean(String key);
    String  getString(String key);
    /** The selected enum option, as its declared option string. */
    String  getEnum(String key);

    /** True if {@code key} is a declared parameter. */
    boolean contains(String key);
    /** All declared parameter keys. */
    java.util.Set<String> keys();
}
```

Type mismatch (e.g. `getInt` on a `string` parameter) or an unknown key throws
an unchecked `ParameterAccessException`.

### `GameState` marker

```java
package io.turnbase.gdk;

/** Marker for game-state types. Carries no methods; signals to the GDK Host
 *  that the type is the session's serializable state (FR-GDK-012). */
public interface GameState {}
```

State types are plain JSON-serializable Java objects — `record`s or POJOs with
serializable fields (FR-GDK-013, CON-004). No serialization code is written by
the developer; the GDK Host serializes/deserializes transparently.

### 5.1 What "transparently" requires of your state type

FR-GDK-013 promises no serialization code, and that promise holds only inside a boundary. The
`ObjectMapper` is **platform-owned, guest-side and not configurable by the game**: there is no hook to
register a module, a `KeyDeserializer` or a mix-in, because the GDK is an interfaces-only artifact
that carries no Jackson at all. So anything the default configuration cannot round-trip, nothing can.

These are **normative**. The upload pipeline rejects a violating state type
([`../manifest/bundle-format.md`](../manifest/bundle-format.md) §4), and the state is serialized on
**every** invocation (`../game-host/game-host-internals.md` §8), so a violation that reaches
production fails on the first action of the first game rather than lurking.

| Rule | Why | Violation |
|---|---|---|
| A `record`, or a class compiled with `-parameters` | Deserialization needs constructor parameter names, which are erased without that flag. A build that silently loses it is the GRMP defect this rule exists for | **Fatal** |
| Map keys are `String`, `enum`, `UUID` or a boxed integral type | A key of any other type serializes via `toString()` and deserializes to garbage, and you cannot register a `KeyDeserializer`. `Map<Position, Piece>` — the most natural board representation on a board-game platform — is exactly this trap | **Fatal** |
| No interface-typed, abstract-typed or `Object`-typed fields | Polymorphic deserialization needs `@JsonTypeInfo`, and the annotation is not on your classpath. A `List<Piece>` where `Piece` is an interface loses every subtype | **Fatal** |
| No reference cycles | Jackson recurses until it overflows. Model the back-reference as an id | **Warning** — statically undecidable in general |
| Prefer `int`/`long` over `float`/`double` for values that must compare exactly | JSON has one number type; a round trip is lossy at the edges | Advisory |
| `Set` and `Map` iteration order is not preserved | Use a `List` if order is part of the state | Advisory |

Collections of records, nested records, enums, `Optional`, `String`, boxed and primitive numerics,
`boolean`, `UUID` and `java.time` types all round-trip without any of this mattering. A state type
built from those and nothing else cannot violate the fatal rules.

**The state is a value, not an object graph.** Every rule above is a restatement of that: if the
state can be written down as JSON and read back as an equal value, it is a valid game state, and if
it cannot, the GDK's transparency promise was never going to hold for it.

---

## 6. Effects (Game BE → Platform)

`Effect` is a **sealed** interface with one public `record` per effect type. The
sealed hierarchy lets the GDK Host map effects to proto with an exhaustive
`switch`; developers never construct variants directly — they use the `Effects`
factory.

```java
package io.turnbase.gdk.effect;

import io.turnbase.gdk.model.GameOutcome;
import java.util.UUID;

public sealed interface Effect
        permits BroadcastEffect, SendToPlayerEffect, SendToTeamEffect,
                LogEffect, GameOverEffect {}

/** To all players' FEs and all spectators (FR-EFF-001). */
public record BroadcastEffect(Object payload) implements Effect {}

/** To one player's FE only (FR-EFF-002). */
public record SendToPlayerEffect(UUID playerId, Object payload) implements Effect {}

/** To all players on one team (FR-EFF-003). */
public record SendToTeamEffect(UUID teamId, Object payload) implements Effect {}

/** A platform-managed game-log entry. Text supports the basic Markdown of
 *  FR-LOG-002 (bold, italic, strikethrough, inline code). Rich color
 *  annotation syntax is deferred (game-contracts.md OQ-001). (FR-EFF-004) */
public record LogEffect(String text) implements Effect {}

/** Game end. Terminal and single per session (FR-EFF-005/006/007). */
public record GameOverEffect(GameOutcome outcome, Object resultsPayload)
        implements Effect {}
```

### `Effects` factory (FR-GDK-008)

```java
package io.turnbase.gdk.effect;

import io.turnbase.gdk.model.GameOutcome;
import java.util.UUID;

public final class Effects {
    private Effects() {}

    public static Effect broadcast(Object payload) { ... }
    public static Effect sendToPlayer(UUID playerId, Object payload) { ... }
    public static Effect sendToTeam(UUID teamId, Object payload) { ... }
    public static Effect log(String text) { ... }
    public static Effect gameOver(GameOutcome outcome, Object resultsPayload) { ... }
}
```

**Payloads are opaque, developer-typed objects** serialized to JSON by the GDK
Host (FR-STATE-002, CON-004); the platform never inspects them. `payload` and
`resultsPayload` must be non-null (use an empty object for "no data"). A single
serialized effect payload must not exceed **10 MB** (NFR-SIZE-002).

**Ordering & terminality.** Effects are applied in list order (FR-RESP-004).
After a `gameOver` effect is processed the session ends; later effects in the
*same* result list are still applied first, then the session terminates
(FR-EFF-006). Only the first `gameOver` across the session is honored
(FR-EFF-007).

---

## 7. Result types

Each hook returns a per-hook result (FR-GDK-009) pairing the next state with an
ordered effect list. All four types share the same shape and a shared fluent
builder; `ActionResult` is shown in full, the others are identical in form.

```java
package io.turnbase.gdk.result;

import io.turnbase.gdk.GameState;
import io.turnbase.gdk.effect.Effect;
import java.util.ArrayList;
import java.util.List;

public record ActionResult<S extends GameState>(S state, List<Effect> effects) {

    /** Result with the given state and no effects (FR-RESP-003). */
    public static <S extends GameState> ActionResult<S> of(S state) {
        return new ActionResult<>(state, List.of());
    }

    /** Start a builder seeded with the (mandatory) next state. */
    public static <S extends GameState> Builder<S> from(S state) {
        return new Builder<>(state);
    }

    public static final class Builder<S extends GameState> {
        private final S state;
        private final List<Effect> effects = new ArrayList<>();
        private Builder(S state) { this.state = state; }

        public Builder<S> effect(Effect e)            { effects.add(e); return this; }
        public Builder<S> effects(List<Effect> es)    { effects.addAll(es); return this; }
        public ActionResult<S> build() {
            return new ActionResult<>(state, List.copyOf(effects));
        }
    }
}
```

`InitResult<S>`, `PlayerJoinedResult<S>`, and `PlayerLeftResult<S>` mirror this
exactly. Distinct types (rather than one shared result) keep hook signatures
self-documenting per FR-GDK-009; the shared builder shape keeps the
implementation duplication mechanical. The contained state is **mandatory**
(FR-RESP-002); the effect list may be empty (FR-RESP-003).

Typical usage:

```java
return ActionResult.from(next)
        .effect(Effects.log("**" + ctx.player().displayName() + "** played"))
        .effect(Effects.broadcast(new MovePlayed(cell, mark)))
        .build();
```

### `ViewResult` — the odd one out

`onResync` is the only hook that returns neither state nor effects, so it has its
own result type carrying a single opaque view payload (FR-RESP-005):

```java
package io.turnbase.gdk.result;

/** The view one viewer sees right now. No state, no effects — a resync cannot
 *  change the game (FR-IN-006). */
public record ViewResult(Object view) {
    public static ViewResult of(Object view) { return new ViewResult(view); }
    /** For a game with nothing to show this viewer yet. */
    public static ViewResult empty() { return new ViewResult(new Object()); }
}
```

`view` is a developer-typed object serialized to JSON like any effect payload,
non-null, and subject to the same 10 MB ceiling (NFR-SIZE-002). It reaches the
viewer's frontend as their first `game_event` — so it is normally the game's own
"full state" message type, the same one a frontend would rebuild from anyway:

```java
@Override
public ViewResult onResync(ChessState state, ResyncContext ctx) {
    return ViewResult.of(switch (ctx.role()) {
        case PLAYER    -> state.viewFor(ctx.viewer().orElseThrow().id());
        case SPECTATOR -> state.publicView();
    });
}
```

---

## 8. Structured outcome (`GameOutcome`)

Consumed by the platform for game history and statistics; **not** delivered to
the FE (the FE gets the separate `resultsPayload`) (FR-GDK-010, FR-OUTCOME-*).

```java
package io.turnbase.gdk.model;

import java.util.List;
import java.util.Map;
import java.util.UUID;

public record GameOutcome(
        List<TeamResult> teamResults,
        List<PlayerResult> playerResults,
        boolean draw) {

    public record TeamResult(UUID teamId, int placement, Map<String, String> stats) {}
    public record PlayerResult(UUID playerId, Map<String, String> stats) {}

    public static Builder builder() { return new Builder(); }

    public static final class Builder {
        // accumulates team/player results and draw flag
        public Builder teamResult(UUID teamId, int placement, Map<String, String> stats) { ... }
        public Builder playerResult(UUID playerId, Map<String, String> stats) { ... }
        public Builder draw(boolean draw) { ... }
        public GameOutcome build() { ... }
    }
}
```

- `placement` is the 1-based finishing position (FR-OUTCOME-001). When `draw` is
  true, multiple teams may share a placement (FR-OUTCOME-003).
- `stats` keys are strings; **values are stringified by the GDK** — the platform
  stores them as opaque `string→string` maps and never interprets them
  (FR-OUTCOME-004, matching the proto `map<string,string>`). For non-string
  game values, the developer passes the desired string form.
- `stats` is optional per entry (`Map.of()` for none).

---

## 9. Runtime & determinism contract

Constraints the developer must honor; the GDK Host and Orchestration Service
enforce them, surfacing violations as the `GameFailureKind` values in
`gamehost.proto`.

| Rule | Detail | Wire mapping on violation |
|------|--------|---------------------------|
| Pure function of inputs | A hook's output must depend only on `(state, context)`. No mutable static state, no clocks, no randomness without a seed carried in state. **The seed comes from `InitContext.seed()`** (§4) — a rule forbidding unseeded randomness is unsatisfiable for any game with hidden information unless the platform supplies one, so it does. | — (correctness) |
| No external I/O | No network, filesystem, or external calls (CON-005). The only interaction is the in-process GDK Host invocation. | — (contract obligation; **enforced at the container layer**, not an in-JVM sandbox exception — GraalVM CE does not deny FS/network in-context, ADR-0005; see `../game-host/game-host-internals.md` §4) |
| No self-initiated comms | A hook only produces output in response to an input (FR-PROC-003). Timers/delayed events must be derived from future actions, holding deadlines in state. | — |
| Sequential processing | Inputs for a session are delivered one at a time, in arrival order (FR-PROC-001/002). Hooks need not be thread-safe across sessions but must not share state between sessions. | — |
| Handler timeout | A hook must return within the configured budget (default **30 s**, NFR-REL-002). | `TIMEOUT` |
| State size | Serialized state ≤ **10 MB** (`game-contracts.md` NFR-SIZE-001, FR-STATE-004). | `STATE_TOO_LARGE` |
| Effect payload size | Each serialized effect payload ≤ **10 MB** (NFR-SIZE-002). | `MALFORMED_OUTPUT` |
| Valid output | Result must be non-null with a non-null state and well-formed effects. | `MALFORMED_OUTPUT` |
| Exceptions terminate | A thrown exception fails the input; after the retry limit the session terminates (NFR-REL-001). | `HANDLER_EXCEPTION` |
| `onResync` is read-only | It must not mutate the state object it is handed, and its view must be derived only from `(state, viewer)`. It may be invoked at any time, any number of times, including several times for the same viewer. | `HANDLER_EXCEPTION` (fails **only** that viewer's attach — never the session, and never counted toward the retry limit; FR-RESP-005) |

A failed input does not silently drop: the Orchestration Service applies
retry-limit semantics and, on exhaustion, terminates the session and notifies
participants (FR-FAIL-* in the gRPC protocol doc). `onResync` is the sole
exception — a failed read cannot corrupt a game, so it fails only the client that
requested it.

---

## 10. Relationship to the gRPC contract

The GDK Host translates between this API and
`docs/specs/internal-grpc/gamehost.proto`:

| GDK API type | proto message |
|--------------|---------------|
| `InitContext` (teams, parameters) | `CreateSessionRequest.teams`, `.parameters` |
| `ActionContext` | `ActionInput` |
| `PlayerJoinedContext` | `PlayerJoinedInput` |
| `PlayerLeftContext` + `PlayerLeftReason` | `PlayerLeftInput` + `PlayerLeftReason` |
| `ResyncContext` + `ViewerRole` | `ResyncRequest` + `ViewerRole` |
| `ViewResult.view` | `ResyncResponse.view` (opaque `bytes`) |
| `Player` | `PlayerRef` |
| `Team` | `Team` |
| `Effect` variants | `Effect` oneof (`BroadcastEffect`…`GameOverEffect`) |
| `GameOutcome` / `TeamResult` / `PlayerResult` | `GameOutcome` / `TeamResult` / `PlayerResult` |
| result `state` | retained in Game Host memory; **never** on the wire (FR-RESP-001a) |

**Proto change made by this spec.** FR-GDK-011 requires `Team.name`, which the
gRPC `Team` message did not carry. A `string name = 3` field was added to the
`Team` message in `gamehost.proto`. The Orchestration Service populates it with
the team's instance display name (`"{template.name} {index}"`) when it builds
`CreateSessionRequest` — see `orchestration-gamehost-protocol.md` "Roster and
team-name resolution". The GDK exposes it as `Team.name()`.

**`onResync` maps to its own RPC, not to `ProcessInput`.** It mutates nothing:
no sequence, no state write, no effects, and its result goes to the requesting
client alone. `gamehost.proto` therefore carries a dedicated `Resync` RPC — see
`orchestration-gamehost-protocol.md` "`Resync` — the read-only path".

---

## 11. Minimal example (number-guessing game)

Illustrates the full surface with the smallest possible game (supports the
NFR-DX-001 "first game in < 2 hours" goal).

```java
public record GuessState(int secret, int attempts) implements GameState {}
public record Guess(int value) {}                       // action payload
public record GuessFeedback(String hint, boolean win) {} // FE event payload

public final class GuessingGame implements TurnBaseGame<GuessState> {

    @Override public InitResult<GuessState> onInit(InitContext ctx) {
        int max = ctx.parameters().getInt("maxValue");
        // Seeded from ctx.seed(), never `new Random()` — see the determinism rules in §9.
        var state = new GuessState(new java.util.Random(ctx.seed()).nextInt(max) + 1, 0);
        return InitResult.from(state)
                .effect(Effects.log("Game started — guess a number from 1 to " + max))
                .build();
    }

    @Override public ActionResult<GuessState> onAction(GuessState s, ActionContext ctx) {
        int guess = ctx.action(Guess.class).value();
        var next = new GuessState(s.secret(), s.attempts() + 1);
        if (guess == s.secret()) {
            var outcome = GameOutcome.builder()
                    .playerResult(ctx.player().id(), java.util.Map.of("attempts", String.valueOf(next.attempts())))
                    .draw(false).build();
            return ActionResult.from(next)
                    .effect(Effects.log("**" + ctx.player().displayName() + "** guessed it!"))
                    .effect(Effects.gameOver(outcome, new GuessFeedback("correct", true)))
                    .build();
        }
        String hint = guess < s.secret() ? "higher" : "lower";
        return ActionResult.from(next)
                .effect(Effects.sendToPlayer(ctx.player().id(), new GuessFeedback(hint, false)))
                .build();
    }

    @Override public PlayerLeftResult<GuessState> onPlayerLeft(GuessState s, PlayerLeftContext ctx) {
        return PlayerLeftResult.of(s); // single-player; nothing to clean up
    }

    @Override public ViewResult onResync(GuessState s, ResyncContext ctx) {
        // The secret is hidden information: never put it in a view.
        return ViewResult.of(new GuessFeedback("attempts so far: " + s.attempts(), false));
    }
}
```

---

## 12. Requirements traceability

| Requirement | Realized by |
|-------------|-------------|
| FR-GDK-001 | `TurnBaseGame<S>` (§3) |
| FR-GDK-002 | `onInit`/`onAction`/`onPlayerJoined`/`onPlayerLeft`/`onResync` (§3) |
| FR-GDK-003 | Context interfaces (§4) |
| FR-GDK-004 | `InitContext` (§4) |
| FR-GDK-005 | `ActionContext.action(Class)` (§4) |
| FR-GDK-006 | `PlayerJoinedContext` (§4) |
| FR-GDK-007 | `PlayerLeftContext` + `PlayerLeftReason` (§4) |
| FR-IN-006, FR-RESP-005 | `onResync` + `ResyncContext` + `ViewResult` (§3, §4, §7) |
| FR-GDK-008 | `Effects` factory (§6) |
| FR-GDK-009 | Result types + builder (§7) |
| FR-GDK-010 | `GameOutcome` (§8) |
| FR-GDK-011 | `Player`, `Team`, `GameParameters` (§5) |
| FR-GDK-012 | `GameState` marker (§5) |
| FR-GDK-013 | JSON-serializable state, no dev serialization code (§5) |
| FR-GDK-014 | `provided`/`compileOnly` scope (§2) |
| FR-GDK-015 | API contains no implementation logic (§2) |
| FR-GDK-016 | GDK version declared in manifest (manifest spec; referenced) |
| FR-RESP-002/003/004 | Mandatory state, empty-effects-valid, ordering (§7, §6) |
| FR-EFF-001…007 | Effect model & terminality (§6) |
| FR-OUTCOME-001…004 | `GameOutcome` (§8) |
| FR-STATE-001…005 | State model & limits (§5, §9) |
| FR-PROC-001…003 | Determinism contract (§9) |
| NFR-DX-002 | 4 abstract methods + 1 default (§3) |

---

## 13. Open questions

- **OQ-001 — Generic action payloads.** `action(Class<A>)` cannot express
  generic container types (e.g. `List<Move>`). If a real game needs this, add a
  `TypeReference`-style overload. Deferred until a concrete need appears; the
  recommended pattern (a single named/`sealed` action type) avoids it.
- **OQ-002 — `GameParameters` enum typing.** Enum parameters are returned as
  their option `String` (`getEnum`). A type-safe `<E extends Enum<E>> E
  getEnum(String, Class<E>)` overload could be added once enum parameter usage
  is exercised by real games.
- **OQ-003 — Rich log formatting.** Color annotation syntax for `LogEffect`
  remains deferred (game-contracts.md OQ-001 / game-development-experience.md
  OQ-004); only the basic Markdown of FR-LOG-002 is in scope now.
