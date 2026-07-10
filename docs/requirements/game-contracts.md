# Game Contracts (API) Requirements

This document defines the communication protocol between the TurnBase platform and game backends/frontends. It specifies the message types, data structures, routing rules, and behavioral guarantees that both sides must adhere to.

> **MVP scope (ADR-0006):** this contract is language-agnostic by design — it is the seam that lets
> different guest runtimes (Espresso/Java now; GraalJS/GraalPy later) host games behind one protocol.
> For the MVP only the **Java runtime** is implemented and it is **official-only** (untrusted Java
> cannot be isolated on GraalVM CE — ADR-0005). The contract itself is unchanged by this scoping.

## Related Documents

- `game-rooms.md` — room lifecycle, team management, host controls
- `reconnection-flow.md` — disconnect detection, grace period, re-entry
- `in-room-chat.md` — chat channels and messaging
- `per-game-statistics.md` — statistics and counters
- Game Development Experience (TBD) — GDK library design, packaging, developer workflow
- Platform Architecture (TBD) — Game Host internals, orchestration, container lifecycle

## Related API Specifications

- [internal-grpc/](../specs/internal-grpc/INDEX.md) — Orchestration Service ↔ Game Host gRPC contract. The inputs (`init`/`action`/`player_joined`/`player_left`), responses, effect types, and structured `game_over` outcome defined here are realized on the wire in `gamehost.proto`.
- [gdk-api/backend-gdk-api.md](../specs/gdk-api/backend-gdk-api.md) — Backend GDK API. The developer-facing realization of these inputs, effects, responses, and the `game_over` outcome as Java types (`TurnBaseGame`, contexts, `Effects`, result types, `GameOutcome`).
- [gdk-api/frontend-gdk-api.md](../specs/gdk-api/frontend-gdk-api.md) — Frontend GDK API. The developer-facing realization of the FE events (FR-FE-*) and actions (FR-FA-*) as the `TurnBaseClient` TS API (`onInit`/`onGameEvent`/…, `sendAction`).

---

## Stakeholders

| Role | Description |
|------|-------------|
| Platform (Orchestration Service) | Routes messages between game BE/FE, manages game state storage, enforces protocol constraints, manages session lifecycle |
| Game Host | Platform-internal component running inside a GraalVM container; multiplexes sessions, invokes game code in-process via Truffle/Espresso contexts across the host/guest boundary (see `../specs/game-host/`) |
| Game Backend (Game BE) | Developer-supplied code implementing game logic; receives inputs with state, returns new state and effects |
| Game Frontend (Game FE) | Developer-supplied JS/TS code running in a sandboxed iframe; receives routed events from the platform, sends player actions |
| Player Client | The platform's own frontend that wraps the game iframe, renders the game log, manages the WebSocket connection to the platform |
| Spectator | A player in spectator role; receives only broadcast effects |
| Game Developer | Third party writing games against the GDK API; consumes this contract as their integration specification |

---

## Definitions

| Term | Meaning |
|------|---------|
| **Input** | A typed message sent from the platform to the game BE, representing an event the game must process |
| **Effect** | A typed instruction returned by the game BE to the platform, describing side effects to execute |
| **Game State** | A serializable blob owned and produced by the game BE, stored by the platform, opaque to the platform |
| **Session** | One active game instance, identified by a unique session ID (UUID) |
| **Payload** | Opaque game-specific data within inputs and effects; only the game BE and FE understand its contents |
| **Action** | A player-initiated event sent from the game FE to the platform, routed to the game BE as an input |

---

## Functional Requirements

### Backend Protocol — Inputs (Platform → Game BE)

This section defines the contract at two levels:
- **GDK-level (developer-facing):** The game code receives the current game state and an input, and returns new state plus effects. The developer always works with state as a method parameter and return value.
- **Platform-level (Orchestration Service → Game Host):** The Orchestration Service sends only the input event. The Game Host holds game state in memory between invocations and is responsible for providing it to the game code internally.

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-IN-001 | Input structure — GDK level | Every invocation of a game handler method includes: the current game state (provided by the Game Host from local memory) and a type-specific input context. The developer's handler always receives state as a parameter. | Must |
| FR-IN-001a | Input structure — platform level | Every input sent from the Orchestration Service to the Game Host includes: the session ID, the input type, and a type-specific payload. Game state is not transmitted; it is held by the Game Host. | Must |
| FR-IN-002 | `init` input | Sent when the game session starts. The payload contains: the list of teams with their assigned players (IDs, display names, team IDs), and the game parameters as configured by the host in the lobby. The game state field is empty for this input. The game BE must return the initial game state and any initial effects. | Must |
| FR-IN-003 | `action` input | Sent when a player submits an action from the game FE. The payload contains: the acting player's information (ID, display name, team ID) and the action payload (opaque, defined by the game). | Must |
| FR-IN-004 | `player_joined` input | Sent when a player joins a game mid-session (late join). The payload contains: the joining player's information (ID, display name, team ID). | Should |
| FR-IN-005 | `player_left` input | Sent when a player is confirmed lost. The payload contains: the departing player's information (ID, display name, team ID) and the reason (`grace_period_expired`, `kicked`, or `left`). The three reasons correspond to: grace period expiring without reconnection (`reconnection-flow.md` FR-EXPIRY-002), a host kick (`reconnection-flow.md` FR-KICK-002/003), and a **confirmed voluntary leave** during an in-progress game (`reconnection-flow.md` FR-DC-005 — explicit "Leave Room", abandonment to join another room, or account deletion). The `left` reason is delivered immediately, bypassing the grace period. An **involuntary** disconnection is *never* signalled during its grace period; the game BE is not notified until that grace period resolves into one of the three reasons above (see `reconnection-flow.md` FR-GRACE-003). | Must |

### Backend Protocol — Responses (Game BE → Platform)

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-RESP-001 | Response structure — GDK level | Every game handler method must return: the new game state and an ordered list of effects. The Game Host captures the returned state and stores it in local memory. | Must |
| FR-RESP-001a | Response structure — platform level | Every response from the Game Host to the Orchestration Service includes: the session ID and an ordered list of effects. Game state is not transmitted; it is retained by the Game Host. | Must |
| FR-RESP-002 | State always returned (GDK level) | The game handler must return a game state in every response, even if the state is unchanged. The Game Host replaces its locally held state with the returned value. | Must |
| FR-RESP-003 | Empty effects valid | An empty effects list is a valid response. It indicates the input was processed but no side effects are needed. | Must |
| FR-RESP-004 | Effect ordering guarantee | The platform must process the returned effects in the order they appear in the list. The game BE may rely on this ordering for correct behavior (e.g., a log entry appearing before a broadcast, or a broadcast preceding a game_over). | Must |

### Backend Protocol — Effect Types

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-EFF-001 | `broadcast` effect | Sends an opaque payload to all players' game FEs and all spectators. The platform does not inspect or modify the payload. | Must |
| FR-EFF-002 | `send_to_player` effect | Sends an opaque payload to a single player's game FE, identified by player ID (UUID). The payload is not delivered to spectators or other players. | Must |
| FR-EFF-003 | `send_to_team` effect | Sends an opaque payload to all players on a specific team, identified by team ID (UUID). The payload is not delivered to spectators or players on other teams. | Must |
| FR-EFF-004 | `log` effect | Adds an entry to the platform-managed game log. The entry is a text string that supports basic Markdown formatting (bold, italic, strikethrough, inline code) and color annotations. The platform renders log entries in its own UI, outside the game iframe. Log entries are displayed in the order they are received. | Must |
| FR-EFF-005 | `game_over` effect | Signals that the game has ended. The payload contains two parts: (a) a structured outcome for platform use (game history, statistics), and (b) an opaque results payload for the game FE. Upon receiving this effect, the platform terminates the game session on the backend side. The game FE remains active to display results until dismissed by the player. | Must |
| FR-EFF-006 | `game_over` is terminal | After the platform processes a `game_over` effect, no further inputs are sent to the game BE for that session. If additional effects follow `game_over` in the same response, they are processed in order before the session terminates. | Must |
| FR-EFF-007 | Single `game_over` per session | Only the first `game_over` effect in a session is honored. If the game BE returns `game_over` in a subsequent response (due to a bug), the platform ignores it. | Must |

### Game Over — Structured Outcome

The structured outcome within the `game_over` effect is used by the platform for game history and statistics. The game FE does not consume this structure; it uses the separate opaque results payload.

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-OUTCOME-001 | Team results | The outcome must include a `teamResults` array. Each entry contains: the team ID (UUID), a placement (integer, 1-based finishing position), and an optional stats map (string keys, arbitrary values). | Must |
| FR-OUTCOME-002 | Player results | The outcome must include a `playerResults` array. Each entry contains: the player ID (UUID) and an optional stats map (string keys, arbitrary values). | Must |
| FR-OUTCOME-003 | Draw flag | The outcome must include a `draw` boolean indicating whether the game ended in a draw. When `draw` is true, multiple teams may share the same placement value. | Must |
| FR-OUTCOME-004 | Stats are opaque | The platform stores the stats maps from team and player results but does not interpret their contents. Display of stats is handled by the game FE or by the platform's generic key-value rendering in game history views. | Must |

### Frontend Protocol — Events (Platform → Game FE)

The platform communicates with the game FE via the `postMessage` API into the sandboxed iframe. Each message is a structured object with a `type` field.

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-FE-001 | `init` event | Sent once when the game iframe is loaded and ready. The payload includes: the current player's information (ID, display name, team ID), the full roster (all players with IDs, display names, team IDs), and the team structure. The game-specific initial state is delivered separately via `send_to_player` effects from the game BE's `init` response. | Must |
| FR-FE-002 | `game_event` event | Delivers an opaque payload originating from a `broadcast`, `send_to_player`, or `send_to_team` effect. The platform routes the payload according to the effect type. The game FE receives only payloads it is entitled to (its own `send_to_player`, its team's `send_to_team`, and all `broadcast` payloads). The game FE does not know which effect type produced the event — it receives a unified stream. | Must |
| FR-FE-003 | `player_joined` event | Sent when a player joins the game mid-session. The payload contains: the joining player's information (ID, display name, team ID). | Should |
| FR-FE-004 | `player_left` event | Sent when a player is confirmed lost (grace period expired, kicked, or voluntary leave — the three reasons of FR-IN-005). The payload contains: the departing player's information (ID, display name, team ID). | Must |
| FR-FE-005 | `game_over` event | Sent when the game ends. The payload contains the opaque results data from the `game_over` effect (not the structured outcome — that is for platform use only). The game FE uses this to render the results view. | Must |
| FR-FE-006 | Spectator event filtering | Spectators receive only `game_event` events originating from `broadcast` effects. They do not receive events from `send_to_player` or `send_to_team` effects. Spectators receive `player_joined`, `player_left`, and `game_over` events. | Must |

### Frontend Protocol — Actions (Game FE → Platform)

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-FA-001 | `action` message | The game FE sends player actions to the platform via `postMessage`. Each message contains: the type (`action`) and an opaque payload defined by the game. | Must |
| FR-FA-002 | Player identity not in action | The game FE does not include player identity in the action message. The platform identifies the acting player from the iframe's session context and attaches player information before routing to the game BE. | Must |
| FR-FA-003 | Single message type | The `action` message is the only message type the game FE may send to the platform. All game-specific communication (moves, signals, UI events) is encoded within the action payload. | Must |

### Game State Contract

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-STATE-001 | State format | The game state is an arbitrary serializable object. The format is defined by the game developer. The Game Host holds it in memory as an opaque blob without inspection or modification. | Must |
| FR-STATE-002 | State serialization | The game state must be serializable and deserializable by the game BE. The GDK and Game Host are responsible for the serialization mechanism; the game developer works with native language objects. Serialization is used for state persistence (future Redis integration) and size limit enforcement, not for per-action transmission. | Must |
| FR-STATE-003 | State immutability by platform | No platform component outside the Game Host may read, modify, filter, or interpret the game state. The Orchestration Service never receives or stores game state directly. | Must |
| FR-STATE-004 | State size limit | The serialized game state must not exceed 10 MB. The platform rejects responses where the state exceeds this limit and terminates the game session with an error. This limit is configurable at the platform level. | Must |
| FR-STATE-005 | Init state | The `init` input is sent with an empty state field. The game BE's response to `init` establishes the initial game state. | Must |

### Game Log

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-LOG-001 | Log rendering | The platform renders game log entries in its own UI, outside the game iframe. The log is visible to all players and spectators. | Must |
| FR-LOG-002 | Log entry format | Each log entry is a text string supporting basic Markdown formatting (bold, italic, strikethrough, inline code) and color annotations. The exact color annotation syntax is defined by the GDK. | Must |
| FR-LOG-003 | Log ordering | Log entries are displayed in the order they are received from the game BE, interleaved chronologically with entries from other effect responses in the same session. | Must |
| FR-LOG-004 | Log persistence | Log entries are persisted for the duration of the game session. Players who join mid-game or reconnect after a disconnect can view the full log from the start of the session. | Should |
| FR-LOG-005 | Log is read-only for game FE | The game FE has no access to the game log. The log is entirely platform-managed. | Must |

### Processing Guarantees

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-PROC-001 | Sequential processing | The platform processes inputs for a given session one at a time. A new input is not sent until the previous response has been received and its effects processed. | Must |
| FR-PROC-002 | Action queuing | When multiple player actions arrive for the same session concurrently, the platform queues them and delivers them sequentially to the game BE in arrival order. | Must |
| FR-PROC-003 | No game-initiated communication | The game BE cannot initiate communication. It only produces output in response to an input from the platform. All autonomous game behavior (timers, delayed events) must be managed internally by the game BE, triggered by subsequent inputs. | Must |

---

## Non-Functional Requirements

| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-PERF-001 | Performance | Platform overhead for routing an input to the game BE and delivering resulting effects to players (excluding game BE processing time) | < 100ms p95 | Should |
| NFR-PERF-002 | Performance | Effect delivery latency from game BE response to player client receipt | < 200ms p95 | Should |
| NFR-SIZE-001 | Limits | Maximum serialized game state size per session | 10 MB (configurable) | Must |
| NFR-SIZE-002 | Limits | Maximum individual effect payload size | 10 MB (configurable) | Must |
| NFR-SEC-001 | Security | Player identity on actions is determined server-side from session context; the game FE cannot spoof player identity | No client-side trust | Must |
| NFR-SEC-002 | Security | Effect routing enforced server-side; `send_to_player` and `send_to_team` payloads are never delivered to unauthorized recipients | No client-side trust | Must |
| NFR-SEC-003 | Security | Game state is opaque to the platform; no platform component reads, modifies, or makes decisions based on state contents | Full opacity | Must |
| NFR-SEC-004 | Security | The game FE iframe is sandboxed; the platform validates postMessage origins on every message received from the iframe | Origin validation | Must |
| NFR-REL-001 | Reliability | If the game BE fails to respond to an input (crash, timeout, malformed output), the platform terminates the game session and notifies all participants | Graceful degradation | Must |
| NFR-REL-002 | Reliability | Game BE processing timeout — if the game BE does not respond within a platform-configured duration, the input is considered failed | Default: 30s (configurable) | Must |

---

## Constraints

| ID | Description |
|----|-------------|
| CON-001 | The backend protocol is realized by **in-process invocation** across the Game Host↔guest boundary (the Game Host invokes the game inside a GraalVM Truffle/Espresso context), using a language-agnostic JSON serialization format. The invocation mechanism and wire format are a Game Host implementation concern (see `../specs/game-host/`), not part of this contract. |
| CON-002 | The frontend protocol uses the browser `postMessage` API between the platform parent window and the game iframe. |
| CON-003 | The game BE code is stateless from the developer's perspective — handlers receive state and return new state. The Game Host holds state in local memory (primary) and persists it to Redis (durability). The Orchestration Service does not store or transmit game state; it routes inputs and delivers effects only. |
| CON-004 | The game FE runs in a sandboxed iframe with no direct network access, no access to platform cookies or storage, and no ability to navigate the parent frame. |
| CON-005 | The game BE must not use the network or filesystem or communicate with external systems; its only interaction with the platform is the in-process invocation managed by the Game Host. For the MVP's trusted official Java this is a **contract obligation** on the author, enforced at the **container layer** (no-egress network policy, read-only filesystem; gVisor in production) — **not** an in-JVM sandbox: the Espresso spike (ADR-0005) showed GraalVM CE does not deny filesystem/network in-context. See `../specs/game-host/game-host-internals.md` §4 and ADR-0006. |
| CON-006 | The platform manages the WebSocket connection to player clients. The game BE and game FE do not manage their own transport. |
| CON-007 | Grace period mechanics are handled entirely by the platform. The game BE is not notified of player disconnections until the grace period expires or the player is kicked (see `reconnection-flow.md`). |

---

## Out of Scope

- GDK library API design and language-specific bindings (Game Development Experience document)
- Game packaging format, manifest structure, upload mechanism (Game Development Experience document)
- Game Host internal architecture, Truffle context management, container lifecycle (Platform Architecture document)
- In-process invocation mechanism and session multiplexing (Platform Architecture document; `../specs/game-host/`)
- Platform WebSocket transport implementation (existing platform infrastructure)
- In-room chat protocol (defined in `in-room-chat.md`)
- Room lifecycle management and lobby mechanics (defined in `game-rooms.md`)
- AI/bot player interface (future specification)
- Replay and spectator recording systems (future specification)

---

## Open Questions

- **OQ-001** — Log color annotation syntax: the exact syntax for color annotations in log entries needs to be defined in the GDK specification. This contract establishes that color support exists but defers the format.
- **OQ-002** — AI/bot player interface: how AI players submit actions is not defined here. AI players may be injected by the game BE internally or by a future platform-level AI system. Deferred to a future specification.
- **OQ-003** — Timer mechanism: the game BE currently manages timers internally, triggered by subsequent player actions. If a platform-managed timer system (`request_timer` / `timer_fired`) is needed in the future, it would be added as a new effect type and input type to this contract.
