# Frontend GDK API — `TurnBaseClient`, Events & Actions

Implementation-level design for the **public frontend Game Development Kit (GDK)
API** — the TypeScript/JavaScript library a game frontend uses to talk to the
TurnBase platform from inside its sandboxed iframe.

This spec realizes the developer-facing frontend contract:

- **Requirements:** `docs/requirements/game-development-experience.md`
  (FR-FEGDK-001…009, CON-002/006) and `docs/requirements/game-contracts.md`
  (FR-FE-001…006, FR-FA-001…003, NFR-SEC-004).
- **Sibling spec:** [backend-gdk-api.md](backend-gdk-api.md) — the JVM half. The
  event payloads a backend sends via `Effects.broadcast`/`sendToPlayer`/
  `sendToTeam` are exactly what this client surfaces through `onGameEvent`; the
  `action` payloads this client sends arrive at the backend's
  `ActionContext.action(...)`.

> **Pre-release status.** The FE GDK is pre-1.0. Breaking changes are expected
> and acceptable between iterations (consistent with the backend GDK).

---

## 1. Scope

**In scope:** the browser-side API — the `TurnBaseClient` class, its lifecycle
(bootstrap, ready handshake, dispose), the five inbound event callbacks, the
`sendAction` method, the init/event context types, origin validation, and the
platform-shell **bootstrap contract** the client depends on.

**Out of scope (separate specs):**

- Backend GDK (`TurnBaseGame`, effects, outcome) — [backend-gdk-api.md](backend-gdk-api.md).
- The platform HTML shell that hosts the iframe and injects the bootstrap global
  (CON-006) — Platform Architecture / frontend platform spec. This spec **defines
  the bootstrap contract** (§9) the shell must satisfy but not the shell itself.
- The platform↔player WebSocket transport that ultimately carries effects/actions
  (CON-006) — the FE GDK never sees it; it speaks only `postMessage`.

---

## 2. Distribution & packaging

| Property | Value |
|----------|-------|
| npm package | `@turnbase/gdk` (FR-FEGDK-007) |
| Module formats | ESM + CJS, with bundled `.d.ts` TypeScript declarations (FR-FEGDK-009) |
| Runtime dependencies | **none** — framework- and engine-agnostic (FR-FEGDK-008) |
| Target | Any browser context that can run inside a sandboxed iframe; no DOM framework assumed |

The game bundle ships only JS/CSS/assets (CON-006); the FE GDK is bundled into
the game's build output like any npm dependency. Developers never write
`postMessage` code directly (FR-FEGDK-005).

---

## 3. The client class

```ts
/**
 * Client for a TurnBase game frontend. Instantiate once, register callbacks,
 * then call start(). All platform communication is funneled through this object;
 * games never touch postMessage directly (FR-FEGDK-001/005).
 *
 * @typeParam TAction - the game's action payload type (sent via sendAction)
 * @typeParam TEvent  - the game's event payload type (received via onGameEvent)
 */
export class TurnBaseClient<TAction = unknown, TEvent = unknown> {
  constructor(options?: TurnBaseClientOptions);

  // --- callback registration (FR-FEGDK-002); each replaces the prior handler,
  //     returns `this` for chaining ---
  onInit(cb: (ctx: InitContext) => void): this;
  onGameEvent(cb: (event: TEvent) => void): this;
  onPlayerJoined(cb: (player: Player) => void): this;
  onPlayerLeft(cb: (player: Player) => void): this;
  onGameOver(cb: (results: unknown) => void): this;

  /** Begin listening and announce readiness to the platform (see §4). Safe to
   *  call once; subsequent calls are no-ops. */
  start(): void;

  /** Send a player action to the platform (FR-FEGDK-003, FR-FA-001). Valid only
   *  after the `init` event has been delivered. */
  sendAction(payload: TAction): void;

  /** Remove the message listener and stop the client. Idempotent. */
  dispose(): void;
}

export interface TurnBaseClientOptions {
  /**
   * Override the trusted parent origin. Normally omitted — the client reads it
   * from the shell bootstrap (§9). Intended for the local test harness, which
   * injects its own origin. SHOULD NOT be set by production game code.
   */
  parentOrigin?: string;
}
```

**Callback model.** One handler per event (setter-style), replaceable; this fits
a game's single render loop better than an `addEventListener` fan-out and keeps
the surface minimal. Registration order is irrelevant; handlers must be set
before `start()` so no early event is missed.

**Generics.** `TAction`/`TEvent` are class-level because they are stable for a
given game (FR-FEGDK-009). `onGameEvent` delivers a **single unified stream** —
the FE cannot tell whether a payload came from `broadcast`, `send_to_player`, or
`send_to_team`, and only receives payloads it is entitled to (FR-FE-002). Games
that send heterogeneous events should make `TEvent` a discriminated union.

---

## 4. Lifecycle & handshake

```
construct ──▶ register callbacks ──▶ start()
                                       │
                                       ├─ read window.__TURNBASE__ (bootstrap, §9)
                                       ├─ attach window 'message' listener
                                       │    (filtered by parentOrigin + source, §8)
                                       └─ post { type: 'ready' } ▶ window.parent
                                                                  (targetOrigin = parentOrigin)
platform ◀───────────────────────────────────────────────────────────────────┘
   │
   └─ posts 'init' ▶ iframe ──▶ onInit(ctx)   (platform guarantees init is first;
                                               FR-FE-001)
   └─ later: 'game_event' / 'player_joined' / 'player_left' / 'game_over'
```

- `start()` is the single explicit step that activates the client. Before it,
  no messages are processed; this guarantees the `ready` signal is sent only
  after the game has registered its handlers.
- The platform sends exactly one `init` event, before any other event
  (FR-FE-001). The client surfaces it via `onInit`.
- If the shell bootstrap is missing or malformed and no `parentOrigin` override
  was supplied, `start()` throws synchronously — the game cannot run untrusted.

---

## 5. Init context

```ts
export type Role = 'player' | 'spectator';

export interface InitContext {
  /** This client's role for the session. */
  role: Role;
  /** The current player, or null for spectators (FR-FE-006). */
  self: Player | null;
  /** Full roster: every player with id, display name, team id (FR-FEGDK-004). */
  roster: Player[];
  /** Team structure for the session. */
  teams: Team[];
  /** The session id (also present in the bootstrap; echoed for convenience). */
  sessionId: string;
}
```

One `onInit` callback serves both roles; games branch on `role` (and the
nullability of `self`). A spectator receives `init`, a unified `game_event`
stream limited to `broadcast`-originated payloads, plus `player_joined`,
`player_left`, and `game_over` (FR-FE-006); it never receives `send_to_player`/
`send_to_team` payloads (enforced server-side, NFR-SEC-002).

---

## 6. Data model

```ts
export interface Player {
  id: string;          // UUID
  displayName: string;
  teamId: string;      // UUID
}

export interface Team {
  id: string;          // UUID
  name: string;        // display name from the manifest team template
  players: Player[];
}
```

Mirrors the backend `Player`/`Team` (and the gRPC `PlayerRef`/`Team`). UUIDs are
canonical strings on the postMessage wire.

---

## 7. Actions (Game FE → Platform)

`sendAction(payload)` is the **only** outbound message a game can produce
(FR-FA-003). The client wraps it as `{ type: 'action', payload }` and posts it to
`window.parent` with `targetOrigin = parentOrigin`. **Player identity is never
included** — the platform attaches it server-side from the iframe's session
context, so a malicious FE cannot spoof another player (FR-FA-002, NFR-SEC-001).

`payload` is the developer's opaque `TAction`; the platform does not inspect it
and routes it to the backend's `onAction` as the action payload. Calling
`sendAction` before `init` is a programming error and throws.

---

## 8. Origin validation & security

The message listener accepts an event only if **both** hold (FR-FEGDK-006,
NFR-SEC-004):

1. `event.origin === parentOrigin` (the value from the bootstrap, §9), and
2. `event.source === window.parent`.

Events failing either check are dropped silently (optionally surfaced through an
internal debug hook; never delivered to game callbacks). Malformed or
unrecognized message shapes from a valid origin are ignored. The client never
posts with `targetOrigin: '*'`: both `ready` and every `action` are addressed to
`parentOrigin`, so no payload leaks to an unexpected embedder.

The trusted origin is **not** derived from any received message (which would be
circular); it comes only from the shell bootstrap or the explicit harness
override.

---

## 9. Platform-shell bootstrap contract

The platform HTML shell that frames the game iframe (CON-006) **must** inject a
bootstrap global into the iframe document *before the game bundle's JS executes*:

```ts
// Injected by the platform shell; read by TurnBaseClient.start().
interface TurnBaseBootstrap {
  parentOrigin: string;  // the exact origin TurnBaseClient must trust
  sessionId: string;     // the active session UUID
}
declare global {
  interface Window { __TURNBASE__?: TurnBaseBootstrap; }
}
```

Rationale: security-critical configuration (the trusted origin) is provided by
the trusted shell, not by game code and not inferred from message traffic. The
rich init context (roster, teams, self, role) is **not** in the bootstrap; it
arrives as the first `init` postMessage event so the platform can populate it at
session start. The local test harness satisfies the same contract by injecting
its own bootstrap (or via the `parentOrigin` constructor override).

> **Cross-spec dependency.** This contract must be honored by the
> platform-frontend shell spec (not yet written). Recorded here as the
> authoritative definition until that spec references it.

---

## 10. Inbound message envelope (internal)

The client abstracts these away (FR-FEGDK-005); they are documented so the
platform shell and test harness emit the right shapes. Every inbound message is
`{ type, ... }`; `type` discriminates.

| `type` | Payload fields | Surfaced as | Requirement |
|--------|----------------|-------------|-------------|
| `init` | `role`, `self`, `roster`, `teams`, `sessionId` | `onInit(ctx)` | FR-FE-001 |
| `game_event` | `payload` (opaque `TEvent`) | `onGameEvent(payload)` | FR-FE-002 |
| `player_joined` | `player` | `onPlayerJoined(player)` | FR-FE-003 |
| `player_left` | `player` | `onPlayerLeft(player)` | FR-FE-004 |
| `game_over` | `results` (opaque) | `onGameOver(results)` | FR-FE-005 |

Outbound: `{ type: 'ready' }` (handshake) and `{ type: 'action', payload }`
(FR-FA-001). `game_over` delivers the opaque **results** payload from the
backend's `Effects.gameOver(outcome, resultsPayload)` — never the structured
`GameOutcome`, which is platform-only (FR-FE-005).

---

## 11. Minimal example (number-guessing FE)

Pairs with the backend example in [backend-gdk-api.md](backend-gdk-api.md) §11.

```ts
import { TurnBaseClient } from '@turnbase/gdk';

type Guess = { value: number };
type Feedback = { hint: string; win: boolean };

const client = new TurnBaseClient<Guess, Feedback>();

client
  .onInit((ctx) => {
    if (ctx.role === 'spectator') renderSpectatorView(ctx);
    else renderGuessInput(ctx.self!); // self is non-null for players
  })
  .onGameEvent((e) => showHint(e.hint, e.win))
  .onPlayerLeft((p) => note(`${p.displayName} left`))
  .onGameOver((r) => showResults(r))
  .start();

function submit(n: number) {
  client.sendAction({ value: n }); // identity attached server-side
}
```

---

## 12. Requirements traceability

| Requirement | Realized by |
|-------------|-------------|
| FR-FEGDK-001 | `TurnBaseClient` class (§3) |
| FR-FEGDK-002 | `onInit`/`onGameEvent`/`onPlayerJoined`/`onPlayerLeft`/`onGameOver` (§3) |
| FR-FEGDK-003 | `sendAction(payload)` (§7) |
| FR-FEGDK-004 | `InitContext` (self, roster, teams) (§5) |
| FR-FEGDK-005 | postMessage fully abstracted; envelope internal (§3, §10) |
| FR-FEGDK-006 | Origin validation (§8) |
| FR-FEGDK-007 | `@turnbase/gdk` npm package (§2) |
| FR-FEGDK-008 | No framework/runtime deps (§2) |
| FR-FEGDK-009 | `.d.ts` types + `TAction`/`TEvent` generics (§2, §3) |
| FR-FE-001…006 | Inbound events + spectator filtering (§5, §10) |
| FR-FA-001…003 | `sendAction`, no client identity, single message type (§7) |
| NFR-SEC-004 | Origin validation on every inbound message (§8) |

---

## 13. Open questions

- **OQ-001 — Reconnection re-init.** On reconnect (reconnection-flow.md), does
  the platform resend `init` with current state, or a distinct `resync` event?
  The current model assumes the game FE rebuilds from the renewed `init` +
  replayed `game_event`s; a dedicated resync event may be added later.
- **OQ-002 — Multiple `onGameEvent` listeners.** A single handler is specified.
  If real games need fan-out (e.g. separate UI vs. audio listeners), an
  `addGameEventListener` variant can be added without breaking the setter form.
- **OQ-003 — Debug hook for dropped messages.** §8 mentions an optional internal
  hook for origin-rejected messages; whether to expose it publicly for local
  debugging is deferred to the test-harness spec.
