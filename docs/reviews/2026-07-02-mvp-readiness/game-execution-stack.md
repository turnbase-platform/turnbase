# Game Execution Stack — Spec Review (game-stack-review agent)

Read all in-scope docs (requirements/platform-architecture.md, game-contracts.md, game-development-experience.md; specs/gdk-api/*, specs/internal-grpc/*, specs/manifest/*) and traced the chain through adjacent websocket.md, file-uploads.md, and game-history.md where the lifecycle passes through them. Excluded gaps already tracked (bundle/upload spec, test harness, shell spec, reconnection re-init, log colors, AI/bots, timers, memory benchmark, scale-in draining).

## BLOCKER findings

### B1. Per-player / per-team effect delivery has no WebSocket destination
**Files:** `docs/specs/api-design/websocket.md` (Topics table), `docs/requirements/platform-architecture.md` FR-DELIVER-002, `docs/requirements/game-contracts.md` NFR-SEC-002, `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` ("Idempotency and exactly-once delivery")

The only game-effect destination defined is `/topic/game.{sessionId}`, whose audience is "session players + spectators". `send_to_player` and `send_to_team` payloads must never reach unauthorized recipients (NFR-SEC-002, a Must with "no client-side trust"), which is impossible on a single shared topic — anything pushed there reaches every subscriber. Room chat solved the analogous problem with `/topic/room.{roomId}.team.{teamId}`, but the game path has no per-team topic and no `/user/queue/game.*` destination. Additionally, websocket.md claims "the game event type catalogue is defined in game-contracts.md", but game-contracts.md defines the *postMessage* events (FR-FE-*), not the STOMP envelope: there is no defined STOMP `type`/payload for `game_event`, `log`, `player_joined/left`, `game_over`, or session-failure delivery. Finally, the gRPC protocol doc's exactly-once story ends with "client-side dedup keyed by `sequence`" — but no spec puts `sequence` in any client-facing message. The chain from `ProcessResult.effects` to the player's iframe is unspecified at its most security-sensitive link.

**Resolution:** Extend websocket.md with: `/topic/game.{sessionId}` (broadcast + log + player_joined/left + game_over), `/topic/game.{sessionId}.team.{teamId}` (subscription-validated by team membership), and `/user/queue/game` for `send_to_player`; define the STOMP envelope types (`GAME_EVENT`, `GAME_LOG`, `GAME_OVER`, `PLAYER_JOINED`, `PLAYER_LEFT`, `SESSION_FAILED`), each carrying `sessionId` and `sequence` for dedup. Register the catalogue in game-contracts.md's "Related API Specifications".

### B2. Crash recovery as specified can double-apply an action (idempotency cache not durable)
**Files:** `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` ("Idempotency", "Crash recovery"), `docs/requirements/platform-architecture.md` FR-FAIL-002/004, FR-SESS-003a/b, `gamehost.proto` (`ProcessInputRequest.sequence`)

The protocol says the Game Host "retains the last processed `(sequence → effects)` per session" and replays it for duplicates — but never says where. If it lives only in local memory, the flagship recovery scenario corrupts state: host persists post-action state to Redis, crashes before its response reaches Orchestration, the action stays in the queue (FR-ROUTE-003) and is re-dispatched to a fresh host, which loads the *post-action* state from Redis (FR-SESS-003b, "transparently, without a distinct error"), sees no dedup record, and applies the same action a second time. FR-FAIL-004's claim that "the only state loss is an in-flight action... re-dispatched from the queue" is wrong under this exact interleaving. The same hole exists for `CreateSession`, which has no idempotency mechanism at all (`sequence` is 0): a re-issued `CreateSession` after a lost response re-runs `onInit` and resets state.

**Resolution:** Specify the Redis session record as a single atomically-written document: `{ state, lastAppliedSequence, lastEffects }` (one write per handler completion). On state load, the host restores the dedup watermark; a duplicate `sequence ≤ lastAppliedSequence` replays `lastEffects` (or empty for older ones). Make `CreateSession` idempotent on `session_id`: if state already exists locally or in Redis, return the cached init effects with `PROCESS_STATUS_OK` instead of re-running `onInit`.

### B3. Game FE bundle serving — origin, path, and enforcement of the iframe sandbox — is unspecified
**Files:** `docs/requirements/game-contracts.md` CON-004, NFR-SEC-004; `docs/specs/gdk-api/frontend-gdk-api.md` §8–9; `docs/requirements/platform-architecture.md` (Artifact Store stakeholder); `docs/specs/manifest/manifest-schema.md` (`frontend.entryPoint`)

No document says how the FE assets inside the uploaded ZIP become a running iframe: who unpacks the bundle, what URL the assets are served from (monolith proxy? object store/CDN? path scheme per game/version?), and — critically — from **what origin**. The frontend GDK's entire security model (§8: `event.origin === parentOrigin`; §9: bootstrap injected "before the game bundle's JS executes") presupposes an origin architecture that doesn't exist anywhere: if the game iframe is sandboxed without `allow-same-origin` its origin is opaque and the parent cannot script `window.__TURNBASE__` into it; if it is same-origin with the platform, game code can reach platform cookies/DOM, violating CON-004. Likewise CON-004's "no direct network access" for game FEs is only achievable via a CSP on the game-asset responses, and no spec defines the iframe `sandbox` attributes or that CSP. The shell spec is tracked as missing, but the *serving origin + sandbox/CSP decision* is a prerequisite architectural choice the already-written FE GDK bootstrap contract silently depends on.

**Resolution:** Add a "game asset serving & origin" section (in the planned bundle spec or shell spec, but decide now): serve game assets from a dedicated sandbox origin (e.g. `games.turnbase.io` or `{gameId}.games.turnbase.io`), unpacked into the Artifact Store at upload-validation time; iframe uses `sandbox="allow-scripts allow-same-origin"` on the *distinct* origin (safe because that origin holds no credentials), so a shell-generated HTML page served from that origin can inline the `__TURNBASE__` bootstrap plus a `<script src>` for the manifest `frontend.entryPoint`; responses carry a CSP restricting `connect-src`/`frame-src`/`form-action` to `'none'` and script/style/img sources to the bundle's own path.

## IMPORTANT findings

### I1. Truffle/Espresso sandbox enforcement is asserted, never specified — and feasibility on GraalVM CE is unverified
**Files:** `docs/requirements/platform-architecture.md` FR-CTX-003…008, CON-001; `docs/specs/gdk-api/backend-gdk-api.md` §9

FR-CTX-004/005/006/007/008 demand no filesystem, no network, no `System.exit`, per-context heap caps, and per-invocation CPU limits — all "intercepted by the Truffle sandbox policy" — but no spec says *which mechanism* enforces each (Context builder options? host-access policy? guest classpath curation? cancellation strategy for the 30 s limit?). CON-001's claim that everything needed is "fully available in CE" is doubtful for two Musts: Truffle's strong sandbox tiers and `sandbox.MaxHeapMemory`-style per-context memory limits are Oracle GraalVM features (and largely JS-only); pre-empting a hot loop in guest Java needs an explicit design. This is distinct from the tracked memory benchmark: it is the enforcement design itself. There is also no Game Host internals spec at all (GDK Host injection into the guest, JSON serialization engine, guest classpath layering for the `provided` GDK classes) — everything between `ProcessInputRequest` and `TurnBaseGame.onAction` is unwritten.

**Resolution:** Write a Game Host internals spec mapping each FR-CTX isolation requirement to a concrete mechanism validated on CE 23. Concrete defaults: Espresso context with `allowNativeAccess(false)`, `allowCreateProcess(false)`, host access limited to the GDK Host bridge, guest classpath = GDK API + game JAR only; wall-clock timeout enforced host-side via a watchdog calling `Context.interrupt()` then `close(true)` (context loss is tolerated by FR-FAIL-007); memory enforced at gVisor/pod level plus context-count caps if per-context heap caps prove Oracle-only — and record the CE limitation in CON-001. Run this as the top technical-risk spike immediately; OQ-002's process-isolation fallback is the escape hatch.

### I2. Same-game cross-session isolation contradicts NFR-SEC-001; game instance lifecycle undefined
**Files:** `docs/requirements/platform-architecture.md` NFR-SEC-001 vs FR-CTX-001; `docs/specs/gdk-api/backend-gdk-api.md` §3, §9

NFR-SEC-001 demands game code "must not be able to access memory, state, or data belonging to other games **or sessions** — Complete isolation", but FR-CTX-001 deliberately runs all sessions of a game version in one shared context: same-game sessions share a heap and static state by design, so a buggy or malicious game can observe other rooms' concurrent matches (e.g. leak hidden hands). The GDK spec only *asks* developers not to do this ("no mutable static state") — a convention, not enforcement. Relatedly, nothing says whether the Game Host creates one `TurnBaseGame` instance per session or a shared singleton per context; §9's "need not be thread-safe across sessions" is false for a singleton with instance fields, since different sessions process concurrently (FR-SESS-006).

**Resolution:** Reword NFR-SEC-001 to guarantee isolation *between game titles/versions* (the context boundary) and document same-game cross-session isolation as a non-guarantee. Specify the instance model: one `TurnBaseGame` instance per session, so instance fields are session-scoped and never concurrently invoked; statics remain shared and untrusted-by-design.

### I3. Failed-action semantics let any player kill a session; "retry" of deterministic failures is ambiguous
**Files:** `docs/requirements/platform-architecture.md` FR-FAIL-001/003; `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` (Error model); `docs/specs/gdk-api/backend-gdk-api.md` §4 (`ActionDecodeException`), §9

The FE is untrusted and `/app/game.{sessionId}.action` accepts an opaque payload — any participant can bypass the game UI and send garbage. Per the specs, the resulting `ActionDecodeException` surfaces as `HANDLER_EXCEPTION`; the protocol doc itself notes game-code failures are deterministic ("re-dispatching will not fix"), yet Orchestration retries to the FR-FAIL-003 limit and then **terminates the whole session** — a trivially exploitable griefing vector. It is also ambiguous what "3 consecutive failures" means: is the same failing input re-dispatched 3 times, or dropped after one failure with a per-session counter? The two readings produce very different behavior.

**Resolution:** Specify that `PROCESS_STATUS_FAILED` on an `action` input **drops that action** (dequeue, notify only the acting player via `/user/queue/errors`), does not re-dispatch it, and increments the per-session consecutive-failure counter FR-FAIL-003's limit applies to; only transport-level failures (`UNAVAILABLE`) re-dispatch the same input. Failures on `init`/`player_left` (inputs the game cannot proceed without) keep the terminate-on-failure path.

### I4. Action-send authorization on the WebSocket is unspecified
**Files:** `docs/specs/api-design/websocket.md` (Authorization), `docs/requirements/game-contracts.md` NFR-SEC-001

The `SubscriptionInterceptor` covers *subscriptions* to `/topic/...`, but nothing specifies validation of client SEND frames to `/app/game.{sessionId}.action`: that the sender is a session member, is a **player** (spectators must not act), and that the session is active. Identity attachment (FR-FA-002) is specified; permission to act is not.

**Resolution:** Extend the interceptor contract: SEND to `/app/game.{sessionId}.action` is rejected unless the authenticated user is an active, non-spectator participant of that session.

### I5. Lobby parameters: wire encoding undefined; "opaque" claim contradicts the manifest contract
**Files:** `gamehost.proto` (`CreateSessionRequest.parameters` comment), `docs/specs/gdk-api/backend-gdk-api.md` §5 (`GameParameters`), `docs/specs/manifest/manifest-schema.md` (parameters)

The proto comment says parameters are "opaque, game-defined... the platform never inspects this" — contradicting the rest of the stack: the platform *defines* the parameter schema (manifest), renders the lobby UI from it, validates host input against min/max/options, and constructs the values. Meanwhile the GDK Host must decode those `bytes` to serve `getInt`/`getEnum`/etc., and no spec defines the encoding, nor who materializes defaults (the Game Host has no manifest access). As written, `GameParameters` cannot be implemented.

**Resolution:** Fix the proto comment; specify: Orchestration serializes a UTF-8 JSON object `{key: value}` with native JSON types per the manifest type, with **all** declared parameters materialized (defaults applied by Orchestration from the manifest). State the same UTF-8-JSON rule once for all opaque `bytes` payloads (actions, effects, results).

### I6. Initial effect delivery race: `onInit` effects can be emitted before any client is subscribed
**Files:** `docs/requirements/game-contracts.md` FR-FE-001; `docs/requirements/platform-architecture.md` FR-DELIVER-001/003; `docs/specs/gdk-api/frontend-gdk-api.md` §4

`CreateSession` runs at game start and returns effects immediately — including the per-player initial state that FR-FE-001 explicitly delegates to `send_to_player` effects — but at that moment players are still navigating from lobby to game view, loading the iframe, and completing the `ready` handshake. Only the log has mandated retention (FR-DELIVER-003, and only "Should"). Nothing says effects are buffered per recipient until subscription + iframe-ready, so under the spec as written every player can miss their own initial state on every normal game start. (Distinct from the tracked reconnection re-init question.)

**Resolution:** Specify per-session effect retention in Redis (effects tagged with `sequence`, retained until session end or a size/age cap) and deliver-on-subscribe replay from sequence 0 on first attach; the same mechanism later serves reconnection.

### I7. `gdkApiVersion` compatibility check has no owner or mechanism
**Files:** `docs/specs/manifest/manifest-schema.md` (Scope), `docs/specs/api-design/file-uploads.md` (validation steps 2–5), `docs/requirements/game-development-experience.md` FR-GDK-016, NFR-COMPAT-001

The manifest spec punts the `gdkApiVersion` supported-range check to "the platform", but the upload pipeline's validation step list doesn't include it, and no spec defines the supported range or how the Game Host's shipped GDK Host version relates to it. During the pre-1.0 window where breaking changes are allowed, an unchecked mismatch fails at *runtime* (context load / linkage error) instead of at upload. The proto side is fine (buf `breaking: FILE`, versioned `v1` package, proto-home relocation already tracked).

**Resolution:** In the upcoming upload-pipeline spec, add: reject bundles whose `gdkApiVersion` is not in the platform's configured supported set (pre-1.0 default: exact-match the single GDK version the current Game Host image ships). Surface the supported version(s) in developer docs.

## MINOR findings

### M1. CPU-time vs wall-clock timeout conflation
`platform-architecture.md` FR-CTX-008 calls the 30 s budget a "CPU time limit" and cites `game-contracts.md` NFR-REL-002, which is a wall-clock response timeout (as is the gRPC deadline). A blocked (not spinning) handler consumes no CPU and would never trip a CPU limit. **Resolution:** define one wall-clock handler budget (30 s) as the enforced limit; drop or demote the CPU framing.

### M2. `GameOutcome` completeness unvalidated, but game history depends on it
`game-history.md` FR-HIST-005 derives placement from "the player's team entry in `teamResults`" and team count from `teamResults.length`; nothing requires the outcome to cover every team/player or use roster-valid IDs (`gamehost.proto` GameOutcome, backend GDK §8). An incomplete outcome silently breaks history. **Resolution:** Orchestration validates on `game_over` (every roster team present exactly once, placements ≥ 1, IDs match roster); violations → `MALFORMED_OUTPUT`.

### M3. Per-session `sequence` generation across stateless replicas unstated
"Monotonic per-session sequence assigned by the Orchestration Service" — with interchangeable replicas this must be Redis-atomic tied to enqueue, or two replicas can mint the same number. **Resolution:** one sentence in the protocol doc: sequence is allocated atomically in Redis at enqueue time.

### M4. Leftover "stdin/stdout protocol" references contradict the Espresso in-process design
`game-contracts.md` CON-001/CON-005 and stakeholder table, `platform-architecture.md` NFR-SEC-002, and the GDK Host definition in `game-development-experience.md` all describe the Game Host ↔ game code boundary as a "stdin/stdout protocol", but the actual design (Espresso contexts, GDK Host invoking `TurnBaseGame` in-process per backend-gdk-api.md §10) has no stdin/stdout anywhere. Misleading to a Game Host or test-harness implementer. **Resolution:** sweep to "the in-process GDK Host invocation boundary".

## Overall verdict

The developer-facing surface (backend/frontend GDK, manifest, proto message shapes) is genuinely implementation-ready — types, traceability, and cross-references are consistent, and the effect-type contradiction I hunted for between requirements, GDK, and proto does not exist. What is *not* shippable yet is the connective tissue at the two ends of the chain: on the client side, effect delivery has no secure WebSocket destination model, and the game-iframe origin/serving/sandbox architecture that the FE GDK's security section already assumes is written nowhere (B1, B3, I4, I6); on the runtime side, the flagship crash-recovery design double-applies actions as specified (B2), and the Espresso sandbox enforcement the whole security story rests on is asserted rather than designed, with real doubt about GraalVM CE feature availability (I1). I'd treat B1–B3 as hard prerequisites to starting implementation of the Orchestration↔client path and the Game Host, run I1 as an immediate prototype spike (it could force the process-isolation fallback that platform-architecture.md OQ-002 already names), and close the remaining IMPORTANT items in one focused spec pass — roughly one gap-closure session plus one spike away from MVP-implementable, rather than MVP-ready today.
