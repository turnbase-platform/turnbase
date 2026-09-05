# Game Development Experience Requirements

This document defines the requirements for the Game Development Kit (GDK), game packaging, upload pipeline, and local development workflow. It specifies what the platform provides to game developers and the constraints on game bundles.

> **MVP scope (ADR-0006):** the Espresso spike (ADR-0005) showed in-JVM Espresso on GraalVM CE cannot
> isolate *untrusted* Java. The **MVP therefore hosts official, first-party Java games only** —
> community-uploaded and privately-hosted **backends are disabled for the MVP**, in any language.
> The Java (JVM) GDK described here is exercised by the official games; **untrusted third-party
> backends return post-MVP** (hardened-container Java, and new **JS/Python GDKs** on GraalJS/GraalPy).
> The upload/packaging requirements below describe the full target design; for the MVP they apply to
> the first-party/official deployment path and to frontend assets, not to an untrusted backend upload
> path. See [`../decisions/0006-game-trust-model-java-official-only.md`](../decisions/0006-game-trust-model-java-official-only.md).

## Related Documents

- `game-contracts.md` — communication protocol between platform and game BE/FE
- `game-catalog.md` — game listing, detail pages, management, versioning
- `game-rooms.md` — room lifecycle, team templates, game parameters, host controls
- Platform Architecture (TBD) — Game Host internals, container lifecycle, Truffle context management
- `../decisions/INDEX.md` — ADR-0006 (game trust model — official-only Java backends for the MVP)

## Related API Specifications

- [gdk-api/backend-gdk-api.md](../specs/gdk-api/backend-gdk-api.md) — Backend GDK API design: `TurnBaseGame`, lifecycle hooks, contexts, effects, results, outcome, data model (implements FR-GDK-001–016)
- [gdk-api/frontend-gdk-api.md](../specs/gdk-api/frontend-gdk-api.md) — Frontend GDK API design: `TurnBaseClient`, event callbacks, `sendAction`, origin validation, shell bootstrap (implements FR-FEGDK-001–009)
- [manifest/manifest-schema.md](../specs/manifest/manifest-schema.md) — Game manifest schema: `manifest.json` structure, JSON Schema artifact, validation rules, error model (implements FR-MANIFEST-001–009)
- [file-uploads.md](../specs/api-design/file-uploads.md) — Pre-signed URL upload flow for game bundles (implements FR-UPLOAD-001–009)
- [error-handling.md](../specs/api-design/error-handling.md) — Bundle validation error format (implements FR-UPLOAD-008)
- [game-frontend/game-asset-serving.md](../specs/game-frontend/game-asset-serving.md) — Game FE serving origin, URL scheme, iframe sandbox & CSP, server-rendered bootstrap document (implements FR-ASSET-001–009, CON-006)

---

## Stakeholders

| Role | Description |
|------|-------------|
| Game Developer | Registered user who builds games using the GDK; writes game logic, packages bundles, tests locally, uploads to the platform |
| Platform | Validates uploaded bundles, stores them, provisions runtime environments, serves the FE GDK to game iframes |
| Game Host | Platform-internal runtime that loads and executes game BE code; consumes the game bundle's backend component and provides the GDK API implementation at runtime |
| Player | End user who plays games; indirectly affected by GDK quality and developer tooling |

---

## Definitions

| Term | Meaning |
|------|---------|
| **GDK API** | A compile-time library providing interfaces, data types, and effect builders for game backend development. Contains no implementation. Language-specific (one per supported language). |
| **GDK Host** | Platform-internal library that implements the GDK API interfaces. Handles in-process invocation across the host/guest boundary, serialization, session management. Ships in the container image, never distributed to developers. |
| **FE GDK** | A JavaScript/TypeScript library wrapping the postMessage protocol. Provides event callbacks and action sending for game frontends. |
| **Game Bundle** | A single archive file containing the game's backend code, frontend code, and manifest. The unit of upload and deployment. |
| **Manifest** | A JSON file at the root of the game bundle declaring metadata, capabilities, entry points, and configuration. The single source of truth for game properties. |
| **Test Harness** | A local development tool that simulates the platform environment, enabling end-to-end testing of game BE and FE without deploying to the platform. |

---

## Functional Requirements

### GDK API — Backend (JVM)

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-GDK-001 | Game interface | The GDK API must provide a generic interface `TurnBaseGame<S>` that game developers implement. The type parameter `S` represents the game state type. | Must |
| FR-GDK-002 | Handler methods | The `TurnBaseGame<S>` interface must declare handler methods corresponding to the input types defined in `game-contracts.md`: `onInit`, `onAction`, `onPlayerJoined`, `onPlayerLeft`, `onResync`. Each handler receives a typed context object and returns a result containing the new state and an effects list — except `onResync` (FR-IN-006), which is **read-only**: it returns a per-viewer view payload and carries no state and no effects. | Must |
| FR-GDK-003 | Context interfaces | The GDK API must provide context interfaces for each handler: `InitContext`, `ActionContext`, `PlayerJoinedContext`, `PlayerLeftContext`, `ResyncContext`. These are interfaces, not concrete classes, allowing the platform to evolve implementations independently. | Must |
| FR-GDK-004 | InitContext | `InitContext` must provide access to: the list of teams with assigned players (IDs, display names, team IDs) and the game parameters as configured by the host. | Must |
| FR-GDK-005 | ActionContext | `ActionContext` must provide access to: the acting player's information (ID, display name, team ID) and a typed accessor for the action payload, parameterized by the developer's action type. | Must |
| FR-GDK-006 | PlayerJoinedContext | `PlayerJoinedContext` must provide access to: the joining player's information (ID, display name, team ID). | Should |
| FR-GDK-007 | PlayerLeftContext | `PlayerLeftContext` must provide access to: the departing player's information (ID, display name, team ID) and the departure reason (`grace_period_expired` or `kicked`). | Must |
| FR-GDK-008 | Effect builders | The GDK API must provide a static effect builder class (`Effects`) with methods: `broadcast(payload)`, `sendToPlayer(playerId, payload)`, `sendToTeam(teamId, payload)`, `log(text)`, `gameOver(outcome, resultsPayload)`. Payload parameters are generic, typed by the developer's own event/payload classes. | Must |
| FR-GDK-009 | Result types | The GDK API must provide generic result types for each handler (e.g., `InitResult<S>`, `ActionResult<S>`) that encapsulate the new game state and an ordered list of effects. A builder pattern should be provided for constructing results. | Must |
| FR-GDK-010 | Outcome type | The GDK API must provide a structured outcome type for the `game_over` effect, with fields for: team results (team ID, placement, stats map), player results (player ID, stats map), and draw flag, as defined in `game-contracts.md` FR-OUTCOME-001 through FR-OUTCOME-003. | Must |
| FR-GDK-011 | Data types | The GDK API must provide data types for platform concepts used in contexts: `Player` (ID, display name, team ID), `Team` (ID, name, players), and `GameParameters` (typed access to parameter values). | Must |
| FR-GDK-012 | State marker interface | The GDK API must provide a marker interface (e.g., `GameState`) that all game state types must implement. This interface carries no methods; it signals to the GDK Host that the type is intended as game state. | Must |
| FR-GDK-013 | State serialization via JSON | Game state types must be serializable to and from JSON. The GDK Host handles serialization transparently. The developer works with plain Java objects (POJOs, records) with serializable fields. No manual serialization code is required from the developer — **within stated constraints**, because "no serialization code" is only achievable if the state type stays inside what a platform-owned, platform-configured `ObjectMapper` can round-trip without developer input. The constraints (records or classes compiled with `-parameters`; map keys limited to scalar types; no polymorphic, interface-typed or `Object`-typed fields) are specified in `../specs/gdk-api/backend-gdk-api.md` §5.1. They are normative: the upload pipeline rejects a state type that violates them, so a requirement that promised transparency without naming them would have games rejected for breaking rules the GDK never stated. | Must |
| FR-GDK-014 | Provided dependency | The GDK API is a compile-time-only dependency. Game developers must declare it with `provided` scope (Maven) or `compileOnly` (Gradle). The GDK API classes must not be bundled in the game's JAR. The GDK Host provides these classes at runtime. | Must |
| FR-GDK-015 | No implementation in API | The GDK API library must contain no implementation logic — no host-invocation or transport handling, no serialization code, no main method. It provides only interfaces, data types, and builder utilities. | Must |
| FR-GDK-016 | GDK version in manifest | The manifest must declare the GDK API version the game was built against. The platform uses this for compatibility validation. | Must |

### GDK API — Frontend (JavaScript/TypeScript)

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-FEGDK-001 | Client class | The FE GDK must provide a `TurnBaseClient` class that game frontends instantiate to communicate with the platform. | Must |
| FR-FEGDK-002 | Event callbacks | The `TurnBaseClient` must provide callback registration methods: `onInit(callback)`, `onGameEvent(callback)`, `onPlayerJoined(callback)`, `onPlayerLeft(callback)`, `onGameOver(callback)`, corresponding to the frontend events in `game-contracts.md` FR-FE-001 through FR-FE-005. | Must |
| FR-FEGDK-003 | Send action | The `TurnBaseClient` must provide a `sendAction(payload)` method that sends a player action to the platform. The payload is opaque and defined by the game. Player identity is not included; the platform attaches it. | Must |
| FR-FEGDK-004 | Init context | The `onInit` callback must receive: the current player's information (ID, display name, team ID), the full player roster, and the team structure. | Must |
| FR-FEGDK-005 | PostMessage abstraction | The FE GDK must fully abstract the postMessage communication layer. Game developers must not interact with `postMessage` directly. | Must |
| FR-FEGDK-006 | Origin validation | The FE GDK must validate the origin of incoming postMessage events, accepting only messages from the platform's parent window. | Must |
| FR-FEGDK-007 | NPM distribution | The FE GDK must be distributed as an npm package (e.g., `@turnbase/gdk`). | Must |
| FR-FEGDK-008 | Framework agnostic | The FE GDK must have no framework dependencies. It must work with any JavaScript framework (React, Vue, Svelte, plain JS) or game engine (Phaser, PixiJS, etc.). | Must |
| FR-FEGDK-009 | TypeScript types | The FE GDK must provide TypeScript type definitions. Generic type parameters should be available for action payloads and game event payloads so developers can define their own types. | Must |

### Game Bundle Format

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-BUNDLE-001 | Archive format | A game bundle is a single archive file (ZIP) containing backend code, frontend code, and a manifest. | Must |
| FR-BUNDLE-002 | Archive structure | The archive must contain a `manifest.json` at the root. Backend and frontend components are placed in paths declared by the manifest. | Must |
| FR-BUNDLE-003 | Backend component — JVM | For JVM games, the backend component is a single fat JAR containing the game's compiled code and all non-GDK dependencies. | Must |
| FR-BUNDLE-004 | Frontend component | The frontend component is a build output directory containing JavaScript, CSS, and asset files. The manifest declares the JS entry point. | Must |
| FR-BUNDLE-005 | Info document | The bundle may optionally include a Markdown document providing game information and rules. The manifest declares the path to this document. If not provided, the game's short description (from the manifest) is displayed on the game detail page. | Should |
| FR-BUNDLE-006 | Bundle size limit | The total bundle size must not exceed 256 MB. The platform rejects bundles exceeding this limit. This limit is configurable at the platform level. | Must |
| FR-BUNDLE-007 | Language-agnostic structure | The archive structure must not be specific to any backend language. The manifest's `runtime` field determines how the platform interprets the backend component. Future runtimes (Python, Go, etc.) use the same archive structure with different backend content. | Must |

### Manifest Schema

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-MANIFEST-001 | Required metadata | The manifest must include: game title, short description (max 100 characters), version (`x.y.z` format), GDK API version, runtime type (e.g., `jvm`), backend entry point, and frontend entry point. | Must |
| FR-MANIFEST-002 | Team templates | The manifest must include a `teamTemplates` array as defined in `game-rooms.md` FR-TEAM section. Each entry declares: name (conditional), size.min, size.max, count.min, count.max. | Must |
| FR-MANIFEST-003 | Capability flags | The manifest must include boolean flags for: AI support, spectator support, mid-game join support. | Must |
| FR-MANIFEST-004 | Configurable parameters | The manifest may include a `parameters` array defining host-configurable game parameters. Each parameter declares: key (unique identifier), display name, type, and default value. | Should |
| FR-MANIFEST-005 | Parameter types | Supported parameter types are: `integer` (with min, max, default), `decimal` (with min, max, default), `boolean` (with default), `string` (with maxLength, default), `enum` (with options list, default). | Should |
| FR-MANIFEST-006 | Tags | The manifest must include a tags array (1–10 tags, each max 24 characters, free-form text), consistent with `game-catalog.md` FR-GAME-003. | Must |
| FR-MANIFEST-007 | Info document path | The manifest may include an optional path to a Markdown info document within the bundle. | Should |
| FR-MANIFEST-008 | Backend entry point — JVM | For JVM runtime, the backend entry point is the fully qualified class name implementing `TurnBaseGame` (e.g., `com.example.ChessGame`). | Must |
| FR-MANIFEST-009 | Frontend entry point | The frontend entry point is the relative path to the JavaScript entry file within the bundle (e.g., `frontend/main.js`). | Must |

### Upload Pipeline

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-UPLOAD-001 | Web UI upload | Game developers can upload game bundles through the platform's web UI on their profile page, as established in `game-catalog.md` FR-GAME-001. | Must |
| FR-UPLOAD-002 | Manifest validation | On upload, the platform must validate the manifest against the expected schema. Missing required fields, invalid types, or malformed values result in rejection with a detailed error message. | Must |
| FR-UPLOAD-003 | Structure validation | On upload, the platform must verify that the backend and frontend entry points declared in the manifest exist within the bundle. | Must |
| FR-UPLOAD-004 | Entry class validation — JVM | For JVM bundles, the platform must verify that the declared entry class exists in the submitted JAR and implements the `TurnBaseGame` interface. | Must |
| FR-UPLOAD-005 | GDK class conflict check | The platform must verify that the submitted JAR does not contain GDK API classes. If GDK classes are detected, the upload is rejected with an error explaining that the GDK API must be declared as a `provided`/`compileOnly` dependency. | Must |
| FR-UPLOAD-006 | Version validation | The platform must verify that the submitted version is strictly higher than the current active version, as defined in `game-catalog.md` FR-GAME-009. | Must |
| FR-UPLOAD-007 | Bundle size validation | The platform must reject bundles exceeding the configured size limit (default 256 MB). | Must |
| FR-UPLOAD-008 | Detailed error reporting | When validation fails, the platform must return a detailed error report listing all validation failures with human-readable descriptions. Multiple errors may be reported in a single response. | Must |
| FR-UPLOAD-009 | CLI upload | Game developers can upload game bundles via a CLI tool or API endpoint, enabling integration with CI/CD pipelines. This requires API token authentication. | Could |

### Game Frontend Serving & Isolation

How an uploaded frontend bundle becomes a running iframe. These requirements are the browser-side
half of the platform's trust boundary; the serving origin is part of the **authentication** model,
not a presentation detail (see FR-ASSET-001). Realized by
[`../specs/game-frontend/game-asset-serving.md`](../specs/game-frontend/game-asset-serving.md).

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-ASSET-001 | Separate registrable domain | Game frontends must be served from a registrable domain distinct from the platform's, so that game code is **cross-site** with the platform session cookie. A subdomain of the platform domain is insufficient: `SameSite` is a site check, not an origin check, so a same-site game frame could issue fully credentialed requests to the platform API. | Must |
| FR-ASSET-002 | Per-game origin | Each game is served from its own origin, derived from the game's identifier, so that one game's frontend cannot read another's browser storage. The origin is produced from a configured template; collapsing the template to a constant (a single shared games origin) must remain possible without any contract change. | Must |
| FR-ASSET-003 | Platform-rendered bootstrap document | The platform serves the iframe's HTML document itself and injects the FE GDK bootstrap (trusted parent origin + session id) into it **before** the game's JavaScript executes. The trusted parent origin comes from server configuration only — never from a URL parameter, a request header, or a compiled-in constant. | Must |
| FR-ASSET-004 | Minimal iframe capabilities | The game iframe is granted the ability to run scripts and to have its own origin, and nothing else: it must not be able to navigate the parent frame, open popups, submit forms, open modal dialogs, trigger downloads, or use any Permissions-Policy feature (camera, microphone, geolocation). | Must |
| FR-ASSET-005 | Content-Security-Policy on game responses | All game frontend responses must carry a CSP that denies everything by default, permits network access only to the game's own bundle (satisfying `game-contracts.md` CON-004's "no direct network access"), forbids nested frames and form submissions, and permits only the platform to frame the game. | Must |
| FR-ASSET-006 | Isolation is trust-independent | The iframe's isolation configuration must be **identical for every game regardless of its trust badge** (Official / Verified / Unverified). No code path may weaken isolation based on a trust level, so no such path can fail open. | Must |
| FR-ASSET-007 | Version pinning per session | The frontend bundle version is resolved once, when the game session is created, and every participant in that session is served that version for its whole lifetime. Republishing a game must not swap the code under a live session. | Must |
| FR-ASSET-008 | Server-supplied frontend URL | The client receives the absolute game frontend URL from the server (in the game-start event and in the room snapshot) and never assembles it. The serving origin must be deploy-time configuration, never baked into a frontend build artifact. | Must |
| FR-ASSET-009 | Route isolation by host | The platform API must not be reachable on the game serving host, and game frontend routes must not be reachable on the platform host. | Must |

### Test Harness

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-HARNESS-001 | Local bridge | The test harness must simulate the platform's role: launch the game BE, serve the game FE in a browser, and route messages between them using the same protocol defined in `game-contracts.md`. | Must |
| FR-HARNESS-002 | Bundle validation | The test harness must validate the game bundle structure and manifest using the same validation rules as the platform upload pipeline (FR-UPLOAD-002 through FR-UPLOAD-005, FR-UPLOAD-007), from the same shared artifact so the two cannot drift. Validation runs automatically before launching the local environment. | Must |
| FR-HARNESS-003 | Multi-player simulation | The test harness must support multiple simultaneous players by allowing multiple browser windows/tabs to connect, each representing a different player. | Must |
| FR-HARNESS-004 | Game log rendering | The test harness must render the game log with the same formatting as the platform (Markdown + color annotations), so developers can verify log output visually. | Must |
| FR-HARNESS-005 | Mock player actions | The test harness must provide a mechanism (e.g., debug panel or CLI interface) to send mock actions from simulated players without requiring a browser window for each player. This enables automated testing scenarios. | Should |
| FR-HARNESS-006 | CLI distribution | The test harness is distributed as a CLI tool that game developers install locally. | Must |
| FR-HARNESS-007 | Team and parameter configuration | The test harness must allow the developer to configure team assignments and game parameters before starting a game session, simulating the lobby configuration experience. | Must |
| FR-HARNESS-008 | Hot reload — frontend | The test harness should support frontend hot reload during development, reloading the game FE in the browser when source files change without restarting the game session. | Could |
| FR-HARNESS-010 | Serialization round trip | The harness must additionally execute a **round-trip test of the game's state type** that the upload pipeline cannot: serialize the state produced by `onInit`, deserialize it, and report any state that does not survive. The upload pipeline performs only *static* serializability analysis, because NFR-UPLOAD-002 forbids executing game code during upload validation — so this is the only place in the corpus where the round trip is actually run, and without it the check GRMP lesson F4 asks for is required by nothing. The harness should extend it to the state after each simulated action, which is where a state shape the initial state never reaches is discovered. | Must |

---

## Non-Functional Requirements

| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-DX-001 | Developer Experience | A game developer with Java and web development experience should be able to create, test, and upload a minimal working game (e.g., a number guessing game) using the GDK and test harness with only the GDK documentation. | < 2 hours from first read to upload | Should |
| NFR-DX-002 | Developer Experience | The GDK API for a new game requires implementing a single interface with a small, fixed set of handler methods: `onInit`, `onAction`, `onPlayerLeft`, `onResync` are required; `onPlayerJoined` has a default. No boilerplate setup, configuration files, or framework initialization beyond the manifest. | ≤ 5 methods, ≤ 4 required | Must |
| NFR-UPLOAD-001 | Performance | Bundle upload and validation must complete within a reasonable time for bundles up to the size limit. | < 30s for 256 MB bundle | Should |
| NFR-UPLOAD-002 | Security | Uploaded game JARs are treated as untrusted code. The upload pipeline must not execute any code from the bundle during validation. Static analysis and metadata inspection only. | No code execution during validation | Must |
| NFR-COMPAT-001 | Compatibility | The GDK API must maintain backward compatibility within the same major version, **effective from the v1.0.0 release**. Games built against GDK API v1.x must run on any platform supporting GDK API v1.y where y ≥ x. During the pre-release period (0.x), the API is unstable and may introduce breaking changes between versions without a major bump; this carve-out lapses at v1.0.0. Cross-major-version compatibility strategy is deferred to a future specification. | Same major version (from v1.0.0) | Must |
| NFR-SIZE-001 | Limits | Maximum game bundle size | 256 MB (configurable) | Must |

---

## Constraints

| ID | Description |
|----|-------------|
| CON-001 | The initial backend GDK API targets JVM languages (Java, Kotlin, Scala). Additional language GDKs follow the same interface patterns but are separate artifacts. |
| CON-002 | The frontend GDK is JavaScript/TypeScript only. Games using other frontend technologies (e.g., Rust+WASM) compile to JS and use the same FE GDK. |
| CON-003 | The GDK API and GDK Host are separate artifacts. The API is public in intent (published to Maven Central / npm once a license is chosen — deferred, `IMP-GATE-25`). In the interim, the Maven artifact publishes to GitHub Packages like the internal libraries; the npm package does not, since GitHub Packages' npm registry requires a scope matching the owning org (`turnbase-platform`), which `@turnbase/gdk` (FR-FEGDK-007) cannot satisfy — npm publication waits for the public registry along with the license. The Host is platform-internal (never distributed to developers). |
| CON-004 | Game state serialization uses JSON. The GDK Host handles serialization transparently; game developers work with plain objects. |
| CON-005 | The manifest is the single source of truth for all game metadata. Metadata changes that require a new version (team templates, capability flags, parameters, tags) can only be updated via a new bundle upload, as defined in `game-catalog.md` FR-GAME-008. |
| CON-006 | The game frontend is served within a platform-controlled HTML shell that injects the FE GDK. The game bundle contains only the JS/CSS/asset build output, not an HTML file. |
| CON-007 | Game backend code must target Java 21. GraalVM Espresso provides a Java 21 guest JVM inside the Game Host; Java 22+ APIs are unavailable at runtime. The GDK artifact is compiled targeting Java 21 bytecode. |

---

## Out of Scope

- Game contracts protocol details (defined in `game-contracts.md`)
- Game Host implementation, Truffle context management, container lifecycle (Platform Architecture document)
- Platform UI for game management, catalog, and detail pages (defined in `game-catalog.md`)
- API token management and CLI authentication for programmatic uploads (future specification)
- GDK API cross-major-version compatibility strategy (future specification)
- Additional backend language GDKs beyond JVM (future, follows same patterns)
- Game content moderation or review process
- AI/bot player development APIs (future specification)

---

## Open Questions

- **OQ-001** — Test harness distribution mechanism: the exact packaging (standalone binary, npm package, Docker-based CLI, or combination) needs to be determined during implementation planning.
- **OQ-002** — FE hot reload in test harness: feasibility depends on the harness architecture. If the harness serves the FE via a local dev server, hot reload is straightforward. If it bundles the FE into the iframe differently, it may require more work.
- **OQ-003** — GDK API cross-major-version compatibility: the strategy for breaking changes across major GDK versions (migration tooling, deprecation periods, multi-version Game Host support) is deferred to a future specification.
- **OQ-004** — Log color annotation syntax: the exact syntax for color annotations in log entries needs to be defined as part of the GDK API specification. Referenced from `game-contracts.md` OQ-001.
