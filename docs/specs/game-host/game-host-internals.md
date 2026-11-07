# Game Host & Execution Internals

Implementation-level design for the **Game Host** service and the **Orchestration
Service execution pipeline** that pairs with it: how a trusted, official Java game
backend is loaded into an Espresso context, invoked through the GDK Host, has its
state persisted, and how the resulting effects are delivered exactly once — across
normal operation, timeouts, failures, and crashes.

This spec realizes the *server side* of
[`../internal-grpc/gamehost.proto`](../internal-grpc/gamehost.proto) and the
Game-Host / Orchestration halves of the platform-architecture requirements. It is
the document that closes review blockers **GAME-I1/I2** (Game Host internals),
**GAME-B2** (crash-recovery double-apply), and the execution-pipeline half of
**GAME-B1** (effect delivery).

- **Requirements:** `docs/requirements/platform-architecture.md`
  (FR-CTX-*, FR-SESS-*, FR-LOAD-*, FR-REG-*, FR-ORCH-*, FR-ROUTE-*, FR-DELIVER-*,
  FR-FAIL-*, FR-SEC-*, FR-OBS-*, NFR-*).
- **Contract realized:** [`../internal-grpc/gamehost.proto`](../internal-grpc/gamehost.proto)
  and [`../internal-grpc/orchestration-gamehost-protocol.md`](../internal-grpc/orchestration-gamehost-protocol.md).
- **Developer surface honored:** [`../gdk-api/backend-gdk-api.md`](../gdk-api/backend-gdk-api.md)
  (`TurnBaseGame`, effects, `GameOutcome`, determinism contract).
- **Decisions:** [`../../decisions/INDEX.md`](../../decisions/INDEX.md) —
  ADR-0001 (local-first / gVisor production-only), ADR-0005 (Espresso spike gates
  this spec), ADR-0006 (official-only trusted Java for the MVP).
- **Spike evidence:** [`../../reviews/2026-07-02-mvp-readiness/espresso-spike-results.md`](../../reviews/2026-07-02-mvp-readiness/espresso-spike-results.md).

---

## 1. Scope & seams

**In scope**

- Game Host process internals: Espresso context topology and lifecycle (FR-CTX-*),
  session & instance model (FR-SESS-*), the GDK Host (guest bridge + host shim) and
  the JSON serialization boundary, guest classpath / JDK-21 packaging, artifact
  loading (FR-LOAD-*), registration/health (FR-REG-*), observability (FR-OBS-*).
- The FR-CTX isolation requirements mapped to the **concrete, spike-verified**
  mechanism that enforces each (§4).
- The Orchestration Service **execution pipeline**: per-session action queue and
  sequence allocation (FR-ROUTE-*), the idempotency/exactly-once machinery
  (FR-FAIL-004), Game Host selection & routing (FR-ORCH-*), effect fan-out to the
  WebSocket Gateway (FR-DELIVER-*), failure & crash recovery (FR-FAIL-*).
- The **shared Redis session record** contract co-owned by both services (§8).

**Out of scope (seams to other specs)**

| Seam | Owned by |
|------|----------|
| The gRPC message shapes, topology, error-model, message-size rules | [`../internal-grpc/`](../internal-grpc/INDEX.md) (settled) |
| The `TurnBaseGame` API, contexts, effects, `GameOutcome`, determinism rules | [`../gdk-api/backend-gdk-api.md`](../gdk-api/backend-gdk-api.md) (settled) |
| **Client-facing** realization of effect delivery — STOMP topics, `/user/queue/game`, the game-event envelope/catalogue, client-side dedup by `(sequence, index)`, the `Resync`-based catch-up flow, action-send authorization | [`../api-design/websocket.md` § Game Session Protocol](../api-design/websocket.md#game-session-protocol) (GAME-B1/I4/I6) — this spec stops at *"Orchestration hands effect E to the WebSocket Gateway, addressed to recipient set R, tagged with `sequence` N"* |
| gVisor, cluster provisioning, NetworkPolicy YAML, IaC | Deployment & infrastructure spec (planned) — this spec states the *required container properties* (§4) but not how they are provisioned |
| Manifest validation, bundle/upload pipeline | [`../manifest/`](../manifest/INDEX.md) + upload-pipeline spec (planned) |

**Trust posture (ADR-0006).** The MVP hosts **official, first-party Java only**.
Every resource limit and isolation control below is therefore justified as
**robustness against a *buggy* game plus defense-in-depth**, *not* as an
adversarial boundary against hostile code. Untrusted hosting (hardened container +
gVisor for Java; GraalJS/GraalPy for JS/Python) is deferred post-MVP behind the
same gRPC seam.

---

## 2. Architecture at a glance

```
                Platform Monolith
        ┌─────────────────────────────────┐         Game Host pod (GraalVM CE 21 host JVM)
        │  Orchestration Service (domain) │         ┌──────────────────────────────────────────┐
Player  │  ┌───────────────────────────┐  │  gRPC   │  GameHostService (server)                 │
  WS ◄──┼──┤ effect fan-out / delivery │  │ dispatch│   host shim ──► Espresso Context: chess@1.4│
Gateway │  │ (FR-DELIVER)              │◄─┼─────────┼── (Value handle) │  guest bridge jar        │
        │  └───────────────────────────┘  │  (mTLS) │                  │  + game JAR              │
        │  ┌───────────────────────────┐  │         │                  │  ├─ session A instance   │
        │  │ per-session queue +       │──┼─────────┼──►               │  └─ session B instance   │
        │  │ sequence + routing (Redis)│  │         │   host shim ──► Espresso Context: catan@2.0 │
        │  └───────────────────────────┘  │         │                                             │
        │  ┌───────────────────────────┐  │  gRPC   │  GameHostRegistryService (client)          │
        │  │ GameHostRegistryService   │◄─┼─────────┼── Register / Heartbeat / ReportContexts     │
        │  │ (server)                  │  │ registry│                                             │
        │  └───────────────────────────┘  │         └──────────────────────────────────────────┘
        └───────────────┬─────────────────┘                 │ artifact fetch        │ state persist
                        │                                    ▼                       ▼
                        └──────────────── Redis ◄──── Artifact Store           Redis (session record)
                     (routing, queue, sequence,     (local FS / MinIO / S3)
                      watermark, session record,
                      liveness lease)
```

- **Host process** — Java 21 on **GraalVM CE for JDK 21**. Serves `GameHostService`
  (dispatch), is a *client* of `GameHostRegistryService` (control), and talks to
  Redis + Artifact Store. One host process per pod; the MVP runs a single instance
  (FR-SCALE-001; scale-out deferred, ADR-0001).
- **Guest** — one Espresso polyglot `Context` per `ContextKey` = `(game_id,
  game_version)` (FR-CTX-001). Sessions of the same version multiplex within it.
- **Channel of record is Redis, not the gRPC connection** (per the protocol doc).

---

## 3. The GDK Host — guest bridge + host shim

The GDK Host is the platform-internal layer that translates between the gRPC
messages and the developer's `TurnBaseGame`. It straddles the host/guest boundary
in two halves.

### 3.1 Host shim (host JVM)

Per context, the host shim owns the polyglot `Context`, obtains a single guest
`Value` handle to the guest bridge entrypoint, and drives invocations. It never
touches game classes; it exchanges only **JSON strings, primitives, and byte
arrays** with the guest. The host builder uses the spike-validated configuration
(§4.2).

### 3.2 Guest bridge (inside the Espresso context)

A **platform-authored** jar placed on the guest classpath. It carries:

- the compiled **GDK API classes** (`io.turnbase.gdk.*`) — so the game's
  `implements TurnBaseGame` resolves at load time. *The developer's JAR must not
  bundle these* (`provided`/`compileOnly` scope, FR-GDK-014, upload check
  FR-UPLOAD-005);
- the **serialization engine** (Jackson + platform ObjectMapper config, §5);
- the concrete GDK context/result/parameter/effect implementations;
- an **invocation entrypoint** whose methods take/return the platform JSON envelope
  (§3.3).

Because Jackson runs *guest-side*, it reflects the game's own state/action/payload
classes (which live only on the guest classpath) natively — the host never needs
to see them.

### 3.3 The guest-boundary call interface

The host shim invokes these guest-bridge methods (all arguments and returns are
`String`/primitive, never rich objects):

| Method | Inputs (JSON/primitive) | Returns |
|--------|-------------------------|---------|
| `createSession(sessionId, entryPointFqcn, teamsJson, parametersJson)` | entry-class FQCN + roster + materialized params | `InvocationEnvelope` |
| `processAction(sessionId, stateJson, playerJson, payloadJson)` | current state + action | `InvocationEnvelope` |
| `processPlayerJoined(sessionId, stateJson, playerJson)` | current state + joiner | `InvocationEnvelope` |
| `processPlayerLeft(sessionId, stateJson, playerJson, reason)` | current state + leaver | `InvocationEnvelope` |
| `resync(sessionId, stateJson, viewerJson, role)` | current state + viewer | `ViewEnvelope` |
| `disposeSession(sessionId)` | — | `void` |
| `restoreSession(sessionId, entryPointFqcn)` | entry-class FQCN only, from the Redis record's `entryPointFqcn` (§8.1) | `void` |

**`restoreSession` exists for crash recovery only** (§9.3) — a Game Host that has no live guest-side
instance for a `sessionId` (a fresh process, or a fresh `ContextKey` context) but finds a session
record in Redis calls it once before the first `processAction`/`processPlayerJoined`/
`processPlayerLeft`/`resync` for that session. It instantiates the entry class and populates the
guest bridge's session map exactly as `createSession` does, but **does not call `onInit`** — the
state it will operate on is the persisted `stateJson`, not a freshly-initialized one, and re-running
`onInit` on a session already mid-game would violate the same idempotency guarantee `onInit` itself
depends on. A host that already holds a live instance for the session (the common case — no crash)
never calls it.

`teamsJson`, `playerJson`, and the `GameOutcome` in the envelope are **platform
types** (mirroring the proto `Team`/`PlayerRef`/`GameOutcome`) serialized with a
platform-fixed schema the host also understands. Everything game-defined —
`stateJson`, action `payloadJson`, effect payloads, `resultsPayload` — is an
**opaque JSON string** the host copies verbatim into proto `bytes` (UTF-8).

`entryPointFqcn` is a plain string, not JSON — the host shim passes
`CreateSessionRequest.entry_point_fqcn` straight through unparsed (IMP-GATE-79). It is resolved
once per `ContextKey` (§6.1) but sent on every `CreateSession` because the bridge, not the host,
owns the guest classloader that resolves it; a repeated classload of an already-loaded FQCN is a
cache hit, not re-work.

**`InvocationEnvelope`** (a platform schema, JSON):

```jsonc
{
  "status": "OK" | "FAILED",
  "failureKind": "HANDLER_EXCEPTION" | "MALFORMED_OUTPUT" | "STATE_TOO_LARGE",  // FAILED only
  "message": "diagnostic for platform logs (never shown to players)",           // FAILED only
  "stateJson": "…",              // next state, opaque; OK only
  "effects": [                   // ordered; OK only
    { "type": "BROADCAST",      "payloadJson": "…" },
    { "type": "SEND_TO_PLAYER", "playerId": "uuid", "payloadJson": "…" },
    { "type": "SEND_TO_TEAM",   "teamId": "uuid",   "payloadJson": "…" },
    { "type": "LOG",            "text": "…" },
    { "type": "GAME_OVER",      "outcome": { … }, "resultsPayloadJson": "…" }
  ]
}
```

**`ViewEnvelope`** (the read-only `resync` reply — FR-IN-006):

```jsonc
{
  "status": "OK" | "FAILED",
  "failureKind": "HANDLER_EXCEPTION" | "MALFORMED_OUTPUT",  // FAILED only
  "message": "diagnostic for platform logs",                // FAILED only
  "viewJson": "…"    // opaque per-viewer view; OK only. No state, no effects.
}
```

The host shim parses this platform envelope and maps `effects[]` to the proto
`Effect` oneof by an **exhaustive switch** (guaranteed exhaustive because `Effect`
is sealed in the GDK — FR-EFF), `stateJson` to the retained/persisted state bytes,
and `outcome` structurally to proto `GameOutcome`. **State never crosses the gRPC
wire** (FR-RESP-001a, CON-006).

### 3.4 Parameter materialization (GAME-I5)

`parametersJson` is a flat JSON object of `key → value` with **every declared
parameter present** — the Orchestration Service materializes manifest defaults
before `CreateSession` so `GameParameters` getters never see an absent key
(backend-gdk-api §5). The guest bridge wraps this object in a `GameParameters`
implementation whose typed getters (`getInt`/`getEnum`/…) read it, throwing
`ParameterAccessException` on type mismatch / unknown key.

### 3.5 Seed derivation

`InitContext.seed()` (backend-gdk-api §4) is derived **by the GDK Host** from `session_id`, not
generated: `seed = the low 64 bits of SHA-256(session_id)`. Nothing is added to
`CreateSessionRequest` and nothing is persisted, because the session id is already assigned by
Orchestration, already unique per game instance, and already stable across an RPC retry — so a
derived seed inherits all three properties for free.

A generated seed would need a home. Stored on the Game Host it is lost with the pod; stored in
Redis it becomes a second writer to the `session:{id}` record §9.1 reserves for the Game Host
alone; added to the proto it becomes a value Orchestration must persist and re-send identically on
every retry, which is a durability problem invented to solve a naming one.

The derivation must be stable across Game Host versions — a game's initial state is established
once at `onInit` and never recomputed, so a changed derivation cannot corrupt a live session, but
it would make the fixture games of §16 and the harness round trip
(`../gdk-api/test-harness.md` §6) non-reproducible.

### 3.6 Where the two halves are built

§3.2 and §5 say the serialization engine is "one module reused by" the guest bridge, the test harness
and the upload validator, and neither says *which repository builds it* — while the repository graph
(`conventions.md` §5) has three consumers in three repositories and no edge that lets two of them
share code with the third. Resolved (`IMP-GATE-69`):

| Artifact | Built by | Coordinates | Contents |
|----------|----------|-------------|----------|
| **Serialization component** | `turnbase-sdk` | `io.github.turnbase-platform:turnbase-serialization` | The platform `ObjectMapper` configuration, the serialize → deserialize → re-serialize round-trip routine, the §5 size-limit checks, and a Jackson-free **capability descriptor** (which types the configured mapper can and cannot bind — the table `bundle-format.md` §4.4 reads). Package `io.turnbase.serialization`. |
| **Guest bridge JAR** | `turnbase-game-host` | none — an image file at `turnbase.gamehost.sdk-jar-path` (`local-environment.md` §7.8), not published | `io.turnbase.gdk.*` (from `turnbase-sdk`), the serialization component, Jackson, and the §3.2 implementations and §3.3 entrypoint. Sources live in package `io.turnbase.gamehost.bridge`, which the host shim must never import. |

**Why the SDK repository.** It is the only repository all three consumers can already depend on:
`turnbase-game-host` depends on it today, the harness (`io.github.turnbase-platform:turnbase-harness`) is published
from it, and `turnbase-sdk` may depend on neither `turnbase-common` nor `turnbase-game-host`
(its own `CLAUDE.md`), which rules out both of the other homes. It is a **separate artifact from
`io.github.turnbase-platform:turnbase-sdk`** because that jar is what developers compile against with `provided`
scope; Jackson and the engine are not part of the API they are promised (NFR-COMPAT-001) and must not
arrive on their compile classpath through it.

**The guest bridge is built by the Game Host** because it ships in the Game Host image and versions
with it (`bundle-format.md` §6.1: the range is a property of the deployed bridge). It is a second
artifact of the same Maven module — a shaded jar of `io.turnbase.gamehost.bridge`,
`turnbase-sdk`, `turnbase-serialization` and Jackson — **without relocation**: the game's own classes
resolve `io.turnbase.gdk.*` and `com.fasterxml.jackson.annotation.*` by their real names, and
relocating either breaks `implements TurnBaseGame` and `@JsonProperty` (`bundle-format.md` F4 exists
because that overlap is real). The Spring Boot fat jar must not be what `sdk-jar-path` points at.

**Consequence for the platform.** `StateSerializabilityAnalyzer` (`IMP-M4-03`) currently hardcodes the
capability knowledge because this artifact did not exist. It should read the capability descriptor
instead; that follow-up is recorded on `IMP-M4-03`, not scheduled as its own item, and does not gate
anything.

---

## 4. Isolation: FR-CTX requirement → concrete mechanism

Per the spike, in-JVM Espresso on CE enforces **some** controls and leaks others.
This is the authoritative mapping the spec commits to. "Container" = the required
pod properties (§4.1); "Espresso" = a context-builder option (§4.2).

| Requirement | Enforced by | Mechanism | Spike status |
|-------------|-------------|-----------|--------------|
| FR-CTX-001 context-per-version | Espresso | one `Context` per `ContextKey` | ✅ isolated heaps/statics |
| FR-CTX-003 memory isolation across contexts | Espresso | separate context heaps | ✅ verified |
| FR-CTX-006 no `System.exit` escape | Espresso | `java.ExitHost=false` (default) — guest `System.exit` disposes only the guest context | ✅ verified |
| FR-CTX-008 handler CPU/wall-clock limit | Espresso | `Context.interrupt(deadline)`, escalate to `close(true)` | ✅ verified (~5 ms) |
| **FR-CTX-004 no filesystem** | **Container** | read-only root filesystem; only a `tmpfs` artifact-cache mount is writable (FR-SEC-003); gVisor mediates syscalls in production | ❌ Espresso leaks — container required |
| **FR-CTX-005 no network** | **Container** | egress `NetworkPolicy` allowing only Orchestration (gRPC), Artifact Store, Redis, health (FR-SEC-002) | ❌ Espresso leaks — container required |
| **FR-CTX-007 per-context memory cap** | **Container** | pod cgroup memory limit (a *pod-wide* cap, not per-context; Oracle-only `sandbox.MaxHeapMemory` is not used — CON-001) | ❌ Espresso/CE lacks it |
| FR-CTX-009/010 idle & pressure eviction | Host | idle timer + LRU (§6.3) | n/a |
| FR-CTX-011 Espresso runtime | Espresso | `java` language context, JDK-21 guest (§4.2) | ✅ |
| FR-CTX-012 polyglot extensibility | Host | runtime abstraction keyed by `manifest.runtime` (§10) | design |

> **MVP consequence.** The pod-wide cgroup limit means the practical granularity of
> FR-CTX-007 is *per pod*, not per game-version. For the single-instance official-only
> MVP this is sufficient (a runaway game trips the pod limit → the pod restarts →
> sessions recover from Redis, §9). A true per-context heap cap is an Oracle-GraalVM
> feature and a post-MVP high-density concern (OQ-1).

### 4.1 Required container properties (stated here, provisioned by the deployment spec)

- Read-only root filesystem + a single writable `tmpfs` mount for the artifact
  cache (FR-SEC-003).
- Egress restricted to Orchestration / Artifact Store / Redis / health (FR-SEC-002).
- Non-root user (FR-SEC-004).
- cgroup memory limit (backs FR-CTX-007 at pod granularity).
- **Production only:** gVisor (`runsc`) OCI runtime (FR-SEC-001) — deferred locally
  (WSL2 cannot run `runsc`, ADR-0001).

### 4.2 Context-builder configuration (spike-locked)

```
Context.newBuilder("java")
   .allowNativeAccess(true)          // MANDATORY — Espresso cannot boot without it (spike)
   .option("java.JavaHome", "/opt/graalvm-guest-jdk21")   // ship a real JDK 21 guest (§7.3)
   .option("java.ExitHost", "false") // FR-CTX-006 (default; set explicitly for clarity)
   .option("java.Classpath", guestBridgeJar + ":" + gameJar)   // §7
   .allowHostAccess(HostAccess.NONE) // host objects never reachable from guest
   .allowHostClassLoading(false)
   .allowCreateProcess(false)
   .allowEnvironmentAccess(EnvironmentAccess.NONE)
   .build();
```

**One engine for all contexts (IMP-M16-05, [ADR-0019](../../decisions/0019-shared-espresso-engine.md)).**
Every context is built with `.engine(sharedEngine)` — one `Engine` per Game Host, created at startup — and
otherwise exactly as above. The engine shares compiled code and caches, not the guest heap, so the
Espresso rows of §4 hold per context. An engine requires one host-access configuration for all its contexts,
which `HostAccess.NONE` on every context already is.

`IOAccess.NONE` / `sandbox.MaxHeapMemory` are **not** relied upon as enforcement —
the spike proved they do not interpose Espresso's native `java.io`/`java.net`; the
container provides FS/network/memory (CON-001 correction). Native access is on, so
the guest JDK's native methods run against the (container-restricted) host OS.

### 4.3 The container dependency (defense in depth, stated so it is not silent)

FR-SEC-005 promises two independent layers (`platform-architecture.md` FR-SEC-005,
NFR-SEC-003). On GraalVM CE the Espresso layer is the *weaker* one, and several guarantees
the guest context appears to give are actually the container's. Nothing in the JVM
changes for this note; it records what the design leans on.

| Guarantee | Held in-JVM by Espresso? | Actually held by |
|-----------|--------------------------|------------------|
| Heap/static isolation between game-version contexts (FR-CTX-001/003) | ✅ yes | Espresso |
| `System.exit` containment (FR-CTX-006) | ✅ yes | Espresso (`java.ExitHost=false`) |
| Handler wall-clock stop (FR-CTX-008) | ✅ yes | Espresso (`Context.interrupt`) |
| No filesystem access (FR-CTX-004) | ❌ **no** — guest read `/etc/passwd` with `IOAccess.NONE` | **Container**: read-only rootfs, non-root user |
| No network access (FR-CTX-005) | ❌ **no** — guest opened a TCP connection | **Container**: egress `NetworkPolicy` |
| Memory cap (FR-CTX-007) | ❌ **no** — `sandbox.MaxHeapMemory` is Oracle-GraalVM-only | **Container**: pod cgroup limit (pod-wide, not per context) |
| Host environment variables hidden from the guest (`allowEnvironmentAccess(NONE)`) | ❌ **no** — a guest `System.getenv("PATH")` returns the host's value (ADR-0019) | **Container**: nothing secret in the Game Host pod's environment |
| Syscall-level containment of the native `java.io`/`java.net` surface Espresso forces open (`allowNativeAccess(true)`) | ❌ no | **gVisor** (`runsc`), production only (FR-SEC-001; ADR-0001) |

Evidence and the tests behind each row:
[`espresso-spike-results.md`](../../reviews/2026-07-02-mvp-readiness/espresso-spike-results.md).

**What follows from this.**

- A breach of the container layer removes the only enforcement of FR-CTX-004/005/007; the
  Espresso layer does not back it up. The "two layers contain each other" reading of FR-SEC-005
  therefore holds for cross-context isolation, exit and timeouts, **not** for filesystem,
  network or memory.
- The model is safe for the MVP only because the Game Host runs **trusted, official Java
  games** (ADR-0006). The row labelled "container" is robustness plus defense in depth for
  such code, not an adversarial boundary; it must be completed (hardened container + gVisor)
  before untrusted backends are hosted.
- **The container properties of §4.1 are not provisioned today.** Neither the Compose stack
  (`deploy/compose/docker-compose.yml`) nor the Helm chart (`gamehost-deployment.yaml`) sets a
  read-only root filesystem, a `securityContext`, a memory limit (the chart's
  `gamehost.resources` defaults to `{}`), an egress `NetworkPolicy` or a gVisor
  `runtimeClassName`; only the image's non-root `USER` is in force. "It ran locally" says nothing about the container layer.

---

## 5. Serialization engine (shared component — GRMP-F4)

- **Format:** JSON via Jackson (CON-004, FR-GDK-013). State types and payloads are
  plain JSON-serializable records/POJOs; developers write **no** serialization code.
- **Where it runs:** entirely **guest-side**, inside the bridge, over guest classes.
- **Shared artifact.** The exact ObjectMapper configuration and the round-trip
  serialize↔deserialize logic live in **one module** — `io.github.turnbase-platform:turnbase-serialization`,
  built by `turnbase-sdk` (§3.6) — reused by (a) the guest bridge
  and (b) the local test harness / upload validator. This makes the **GRMP-F4
  round-trip smoke test** structural: a state object that fails to round-trip is
  caught at upload/harness time with the *same* engine that runs in production, so
  the two cannot drift.
- **Limits (checked guest-side, mapped to `GameFailureKind`):**

  | Check | Failure |
  |-------|---------|
  | serialized `stateJson` > 10 MB (`game-contracts.md` NFR-SIZE-001, FR-STATE-004) | `STATE_TOO_LARGE` |
  | any serialized effect payload > 10 MB (NFR-SIZE-002) | `MALFORMED_OUTPUT` |
  | result null / null state / unserializable / `ActionDecodeException` / any hook throw | `HANDLER_EXCEPTION` or `MALFORMED_OUTPUT` per backend-gdk §9 |

---

## 6. Context, session & instance model

### 6.1 Context (per game-version)

- **Creation on demand (FR-CTX-002).** On the first input for a `ContextKey` with no
  live context, the host fetches the backend JAR (§7), builds the context (§4.2), then
  calls `bridge.createSession` (§3.3), which loads and verifies the entry class (§7.2)
  guest-side, keyed by the `entryPointFqcn` the host passes through from
  `CreateSessionRequest` (IMP-GATE-79). Concurrent requests for the same cold
  `ContextKey` are coalesced behind a single creation (one context, not a race of
  many).
- **Bounded concurrent boots (IMP-M16-04).** Booting Espresso is CPU-bound and
  concurrent boots slow each other (four at once take twice as long as one:
  `load-testing.md` §13, finding 8). A fair `Semaphore` in `BootWatchdog` lets at most
  `turnbase.gamehost.max-concurrent-boots` (default `2`) guest boots run at once; the
  others queue in arrival order. The boot-timeout timer (§11) starts when a boot
  **acquires its permit**, not when it is queued, so a queued boot cannot trip it. The
  wait has no timeout of its own: it ends with the caller's gRPC deadline on
  `CreateSession`. Creation of one key never blocks another: `GameContextManager` keeps
  an in-flight `CompletableFuture` per cold key (waiters of the same key join it; a
  failure is rethrown to them and not cached) and builds the context outside any map
  lock.
- **Engine and context budget (IMP-M16-05).** All contexts run on one shared `Engine`
  ([ADR-0019](../../decisions/0019-shared-espresso-engine.md), §4.2). A JVM can create only twelve
  Espresso contexts in its lifetime, closed or not (`OQ-6`); `ContextBudget` counts them and retires the host at the limit.
- **Reporting (FR-REG-002).** The set of live `ContextKey`s is reported to
  Orchestration for warm-host selection (§11).

### 6.2 Session & the `TurnBaseGame` instance (per session)

- **One instance per session** (owner decision). At `CreateSession` the bridge
  instantiates the entry class (no-arg constructor) and stores it in a guest-side
  `Map<sessionId, TurnBaseGame>` within its context; it is discarded at
  `disposeSession`. This is defensive against a buggy official game holding instance
  fields, at negligible cost for MVP session counts. *(The determinism contract
  would permit a single shared stateless instance per context; revisit as a density
  optimization — OQ-3.)*
- **Session→context binding (FR-SESS-002).** The host keeps `sessionId → ContextKey`.
- **Per-session single-flight (FR-SESS-006).** The host serializes inputs for one
  session (never two concurrent invocations for the same session). **Different
  sessions run concurrently**, including within the same context (owner decision) —
  see the interrupt caveat in §12.

### 6.3 Context eviction

- **Idle (FR-CTX-009, Should).** When a context's last session ends, an idle timer
  (default 5 min, configurable) starts; on expiry with no new session the context is
  closed and resources freed.
- **Memory pressure (FR-CTX-010, Must).** When host memory exceeds a configurable
  threshold, evict idle contexts **LRU**, regardless of the idle timer. **A context
  with any active session is never evicted.**

---

## 7. Game code loading & guest classpath (FR-LOAD-*)

### 7.1 Fetch & cache

- Fetch the backend JAR from the **Artifact Store** — an interface with local-FS
  (dev), MinIO (local K8s), and S3 (prod) implementations (FR-LOAD-002, CON-007).
- Cache fetched JARs on the writable `tmpfs` mount (FR-LOAD-003); a cache hit skips
  the fetch. **LRU eviction by size limit** (FR-LOAD-004), but **never evict a JAR
  backing a live context**.

### 7.2 Entry class discovery (FR-LOAD-005)

The bridge receives the manifest `backend.entryPoint` FQCN as `createSession`'s
`entryPointFqcn` argument (§3.3) — Orchestration resolves it from the manifest and sends it
in `CreateSessionRequest.entry_point_fqcn`, the same read that materializes `parameters`
(§3.4, IMP-GATE-79). The bridge loads that FQCN via the guest classloader,
verifies it implements `TurnBaseGame`, and instantiates it. Missing class or wrong
type → the session fails with `GAME_FAILURE_KIND_CODE_LOAD_ERROR` (surfaced at
`CreateSession` as transport `FAILED_PRECONDITION`, per the protocol error model).

### 7.3 Guest JDK-21 packaging (spike follow-up)

The Maven `espresso-runtime-resources` guest is **JDK 17**, which rejects the
project's Java-21 (class major 65) game bytecode. The Game Host image therefore
**ships a real JDK 21** and points `java.JavaHome` at it (§4.2). This is a build
requirement on the Game Host container image, recorded here so it is not lost.

---

## 8. State representation & the shared Redis session record

**Canonical state is serialized JSON** (owner decision). The host holds it as bytes
in local memory (primary read/write path, `platform-architecture.md` FR-SESS-003 —
qualified because `user-accounts.md` defines an unrelated FR-SESS-003 about login
session displacement) and mirrors it to Redis
(FR-SESS-003a). Rich state objects exist **only transiently inside the guest**
during an invocation. This keeps the host fully game-agnostic and makes recovery,
eviction, and persistence portable.

### 8.1 The session record (co-owned contract)

One atomic record per session, the single source of truth for recovery and
idempotency (closes **GAME-B2**):

```jsonc
// Redis key: session:{sessionId}   (see §13 for the full key map)
{
  "contextKey":          { "gameId": "…", "gameVersion": "1.4.0" },
  "entryPointFqcn":      "…",     // set once at CreateSession; needed to reconstruct the guest
                                  // instance on recovery (§9.3) — never rewritten after
  "stateJson":           "…",     // opaque; the last successfully-applied state
  "lastAppliedSequence": 42,      // highest sequence *consumed* (CreateSession = 0)
  "lastOutcome":         "OK",    // "OK" | "FAILED" — the outcome at lastAppliedSequence
  "lastEffects":         [ … ],   // effects produced at lastAppliedSequence; [] when FAILED
  "lastFailure":         null     // the GameFailure at lastAppliedSequence; null when OK
}
```

- Written by the **Game Host** (it computes state + effects).
- Read by the **Game Host** on recovery, and by the **Orchestration Service** for
  the delivery watermark (§9.2) and terminal cleanup.
- **`entryPointFqcn` is written once, at `CreateSession`, and is not part of the per-invocation atomic
  update below** — it never changes for the life of the session, so it carries no torn-write risk.
  It exists solely so a Game Host recovering the session on a different instance (§9.3) can call
  `GameBridgeClient.restoreSession` without Orchestration having to resend it, which no RPC after
  `CreateSession` does (see §3.3).
- **`lastEffects` retention** enables idempotent replay of the *most recent*
  sequence. It is not a full history; `game_over` results and the game log are
  retained separately by Orchestration for join/reconnect replay (FR-DELIVER-003).
- **`lastOutcome` / `lastFailure` exist because a burned sequence must be replayable.**
  `../internal-grpc/orchestration-gamehost-protocol.md` advances `lastAppliedSequence` on a *failed*
  input — the sequence is consumed, and a redelivery must return the same failure rather than invoke a
  handler that has already run and thrown. Without a place to record the outcome, the replay branch
  (§9.1 step 1) would return `lastEffects` with `OK`, and those effects belong to the *previous*
  input. That is a silent wrong answer: the client is told an action succeeded and handed somebody
  else's effects. `lastAppliedSequence` is therefore the highest sequence **consumed**, not the
  highest successfully applied, and `lastOutcome` says which.
- **Atomicity requirement.** `{stateJson, lastAppliedSequence, lastOutcome, lastEffects, lastFailure}`
  MUST be written as **one atomic unit** (a Lua script or `MULTI/EXEC`). A torn write that
  advanced the sequence without the matching state is the exact bug GAME-B2 flags;
  the atomic record forbids it. The failure path writes the same unit — it is not a partial update. A
  torn write that advanced the sequence without recording the outcome produces exactly the GAME-B2
  class of bug on the failure path that the atomic record forbids on the success path.

### 8.2 Redis durability (OPS-4)

The MVP runs a **single Redis instance** with no HA (per the platform-operations
OQ-001 resolution). The **accepted loss window** is a single in-flight action at the
moment of a Redis-node loss; all committed state is durable to the last successful
write. This dependency is called out for the data-operations spec; the atomic-record
requirement above is what makes recovery correct *given* a surviving Redis.

---

## 9. Invocation, sequencing, idempotency & recovery

### 9.1 The three dispatch flows

**`CreateSession` (idempotent — closes the GAME-B2 create hole):**

```
1. If session:{id} already exists in Redis → return its lastEffects with OK
   (do NOT re-run onInit).                                   ← idempotent create
2. Else: select/create the context (§6.1, §7); bridge.createSession(...).
3. On OK: atomically write session record { contextKey, stateJson,
   lastAppliedSequence = 0, lastEffects = <onInit effects> }.
4. Return ProcessResult(sequence = 0, OK, effects).
```

Step 1's guard is only correct because **`session:{sessionId}` has exactly one writer, the Game Host**
(§13). Its presence means "onInit has already run and its effects are recorded", and nothing else may
create it. An Orchestration pre-write of the same key — plausible, since Orchestration allocates the
`sessionId` and writes every other key of the family — turns the idempotency guard into an
unconditional short-circuit: the first `CreateSession` returns an empty `lastEffects` with `OK`, the
handler never runs, and the game begins with no state and no opening effects. Flow 02 step 6 names the
keys Orchestration does write.

**`ProcessInput` (idempotent replay by `sequence`):**

```
1. If input.sequence ≤ record.lastAppliedSequence → REPLAY:
     lastOutcome == OK     → return ProcessResult(sequence, OK, record.lastEffects)
     lastOutcome == FAILED → return ProcessResult(sequence, FAILED, record.lastFailure)
   Do NOT invoke the handler.                        ← at-most-once application
2. If session not in local memory → load record from Redis (recovery, §9.3);
   NOT_FOUND if no record exists at all (terminal).
3. Acquire the per-session single-flight lock (§6.2).
4. bridge.process*(sessionId, record.stateJson, …) under the 30 s watchdog (§12).
5. On OK: atomically write { stateJson', lastAppliedSequence = input.sequence,
   lastOutcome = OK, lastEffects = effects', lastFailure = null };
   then return ProcessResult(sequence, OK, effects').
6. On failure: atomically write { stateJson unchanged, lastAppliedSequence = input.sequence,
   lastOutcome = FAILED, lastEffects = [], lastFailure = failure }; then return
   ProcessResult(sequence, FAILED, failure). The sequence is burned — the game state is
   unchanged, but the input has been consumed and must not be re-invoked on redelivery.
```

The persist-then-return order (step 5) implements FR-FAIL-006: the host does not ACK
(`OK`) until the Redis write succeeds, so a delivered success always has durable
state behind it.

**`Resync` (read-only — the client catch-up path, FR-IN-006):**

```
1. If session not in local memory → load record from Redis (same recovery as above);
   NOT_FOUND if no record exists.
2. Acquire the per-session single-flight lock (§6.2) — so the view is composed
   against a fully-applied, non-torn state.
3. bridge.resync(sessionId, record.stateJson, viewerJson, role) under the watchdog.
4. Return ResyncResponse(view, as_of_sequence = record.lastAppliedSequence).
```

It writes **nothing**: no session record, no `lastAppliedSequence` advance, no
sequence allocation, no queue entry, no delivery-watermark change. It therefore
needs no idempotency machinery — a duplicate `Resync` is simply re-executed. A
failure fails only the attaching client (`RESYNC_FAILED` to that client) and does
**not** increment the per-session consecutive-failure counter (§9.4): a read cannot
corrupt a game. `as_of_sequence` is what makes client catch-up race-free — see the
[game-session WebSocket spec](../api-design/websocket.md#game-session-protocol).

**`TerminateSession`:** dispose the guest instance (`disposeSession`), drop
local-memory state, delete `session:{id}` from Redis (FR-SESS-005). Idempotent
(terminating an already-gone session is a no-op success) — this guarantee is
normative in the protocol contract, not merely an implementation property, because
the durable re-drive of [ADR-0010](../../decisions/0010-session-teardown-ordering.md)
retries terminations whose response was lost.

**Terminate does not acquire the single-flight lock.** It marks the session
terminated, deletes the Redis record and returns immediately (2s deadline); the guest
instance is disposed once any in-flight handler releases the lock, and that handler's
result is discarded. Terminate must **not** use `Context.interrupt` — that is
context-scoped and would reach sibling sessions sharing the context (§12).

**What the host remembers afterwards.** The host's per-session structures (the session→context binding, the lock, the guest instance) are released at terminate, or when the in-flight handler releases the lock. The one thing kept is the set of terminated session ids, which rejects a late input and discards an in-flight result. It expires after **5 minutes** and holds at most **10,000** ids, oldest first (3 retries × 35 s dispatch deadline = 105 s is the longest a late input can arrive). Without that bound the set, and the guest instances nobody disposed, grew for the life of the process (load-test finding 16).

**Key cleanup.** `TerminateSession` deletes `session:{id}`. The Orchestration-owned
keys for that session — `routing:`, `queue:`, `seq:`, `delivered:`, `failcount:` — are
deleted by the caller as part of the same teardown routine. Historically only the
retry-limit path (§9.4) did this, which left the full key family behind on exactly the
path room closure uses; the reconciliation sweep
(`platform-operations.md` FR-JOB-007) collects any strays.

### 9.2 Sequence allocation & exactly-once delivery (Orchestration side)

- **Allocation.** On enqueue, the Orchestration Service assigns a **monotonic
  per-session `sequence`** via a Redis counter (`INCR seq:{sessionId}`), and appends
  the input to the per-session FIFO queue (`queue:{sessionId}`, FR-ROUTE-001).
  `player_joined`/`player_left` are enqueued in the same queue, preserving total
  order (FR-ROUTE-004).
- **Sequential dispatch (FR-ROUTE-002).** A per-session dispatcher pops the head,
  dials the routed Game Host pod (from `routing:{sessionId}`), and awaits
  `ProcessResult`. The **next** input is dispatched only after the prior result is
  received. The input stays in the queue until an `OK`/terminal result (FR-ROUTE-003).
- **Delivery watermark (exactly-once delivery).** Orchestration keeps
  `delivered:{sessionId}` = highest `sequence` delivered to clients. On receiving
  `ProcessResult(seq, OK, effects)`:
  - if `seq > delivered` → fan out effects (§10), then set `delivered = seq`;
  - if `seq ≤ delivered` → the result is a replay; **suppress delivery** (already
    sent). Combined with the Game Host's at-most-once *application*, this yields
    **exactly-once application + at-least-once delivery**, with final client-side
    dedup keyed by `sequence` in the WS layer (GAME-B1).
- After delivery, dequeue the head and advance the dispatcher.

### 9.3 Crash recovery

**Game Host crash (FR-FAIL-002, NFR-REL-002 < 30 s):** the liveness lease (§11)
expires, nothing happens until a session next needs its host. The first input whose routed host
is unreachable (or gone from the registry) makes Orchestration quarantine that host for the lease TTL,
select a new one, rewrite `routing:{sessionId}` and **re-dispatch the head-of-queue input**
(`GameInputService.reassign`; lazy, `OQ-5`). The
new host has no local state → loads `session:{id}` from Redis (§9.1 step 2), calls
`GameBridgeClient.restoreSession(sessionId, record.entryPointFqcn)` (§3.3) to recreate
the guest instance without re-running `onInit`, sets the state, and proceeds. Because
the instance is stateless and the record *is* the state, **no history replay is
needed**.

**The in-flight action** (being processed at crash) is still in the queue (never
dequeued without `OK`). If the dead host had actually applied it (advanced
`lastAppliedSequence`, atomic §8.1) but died before returning, the re-dispatch hits
§9.1 step 1 → **replay**, so the action is not double-applied (GAME-B2 closed). If it
had not applied it, the new host applies it fresh. Either way: exactly-once.

*Reassignment is lazy, on the next input, not at lease expiry: decided by measurement in §18 `OQ-5`.*

**Platform pod crash (the other direction).** When the Platform Monolith pod that owns
a room dies, the Game Host is unaffected: the session record is intact, and no guest
state is lost. The room is adopted by another pod under the ownership claim of
[ADR-0008](../../decisions/0008-room-ownership-lifecycle.md), and the adopting pod
re-creates the session dispatcher and re-dispatches the head of `queue:{sessionId}`.
Exactly-once survives this **with no Game Host change**: replay by `sequence` (§9.1
step 1), the `delivered:{sessionId}` watermark (§9.2) and client-side `asOfSequence`
dedup already compose to give it. While a room is ownerless nothing dispatches its
queue — acceptable, because by the invariant in ADR-0008 no client is attached to
observe the pause.

**Context crash / OOM (FR-FAIL-007, NFR-REL-001):** a context crash affects only its
own sessions; other contexts continue. Affected sessions' records remain in Redis and
are reassigned to a fresh context (same or new host). Surfaced as
`GAME_FAILURE_KIND_CONTEXT_CRASH`.

**Redis unavailable (FR-FAIL-006):** the host keeps serving from local memory but
**withholds `OK`** until the persist succeeds (retry with backoff). If Redis stays
down beyond a configurable window (default 60 s), affected sessions are failed
gracefully (§9.4). *Note:* the per-call gRPC deadline (game timeout + overhead) is
shorter than 60 s, so a sustained outage surfaces first as `DEADLINE_EXCEEDED`
re-dispatches; the 60 s window bounds how long the host keeps trying before it
abandons the sessions. (Interplay documented; not a correctness hole.)

### 9.4 Failure counting & permanent failure (FR-FAIL-001/003/005)

Orchestration keeps a **per-session consecutive-failure counter**, incremented on
any processing failure (transport `DEADLINE_EXCEEDED`/`RESOURCE_EXHAUSTED`, or
in-band `PROCESS_STATUS_FAILED`), **reset on any `OK`**. On the **3rd consecutive
failure** it calls `TerminateSession(RETRY_LIMIT)`, cleans up
`session:{id}`/`queue:{id}`/counters, notifies the Room Service (room → Lobby), and
pushes a failure notification to all participants via the WS Gateway. `UNAVAILABLE`
(host down) triggers **reassignment first** (§9.3) and only counts toward the limit
if reassignment cannot make progress.

---

## 10. Effect delivery & fan-out (Orchestration → WebSocket Gateway)

On a deliverable `ProcessResult` (§9.2), Orchestration resolves each effect to a
recipient set and **direct-pushes** it to the WebSocket Gateway (FR-DELIVER-001,
CON-005 — no intermediate bus), **preserving list order** (FR-DELIVER-004,
FR-RESP-004):

| Effect | Recipients (FR-DELIVER-002) |
|--------|------------------------------|
| `broadcast` | all players **and** spectators |
| `send_to_player` | the one `playerId` (never spectators/others) |
| `send_to_team` | all players on `teamId` (never spectators/other teams) |
| `log` | platform-managed log entry; stored for the session and rendered outside the game iframe |
| `game_over` | all players and spectators; **terminal** |

- **Spectators** receive only `broadcast`, `player_joined`, `player_left`,
  `game_over` (FR-DELIVER-002).
- **Log retention (FR-DELIVER-003).** `log` entries are stored for the session so a
  mid-game joiner / reconnecting player can be shown the full log. The log is the
  **only** thing retained per session: there is no effect journal. A client's game
  view is reconstructed on attach by the read-only `Resync` path (§9.1), not by
  replaying past effects. Delivery of the retained log to an attaching client is the
  **game-session WebSocket spec**'s `GAME_SYNC`.
- **`onInit` may return `log` effects only.** Its effects are fanned out at sequence 0,
  when no client has subscribed yet, and there is no effect journal; a `log` entry is
  retained and replayed to every attaching client, any other kind would reach nobody.
  The GDK enforces this in the type (`InitResult` carries `List<LogEffect>`,
  `backend-gdk-api.md` §7), so the host never receives a client-facing effect from
  `init`. Initial state reaches clients through `Resync`
  (game-contracts.md FR-IN-006/FR-FE-001, review **I6**).
- **`game_over` handling.** After the game-over effect is delivered, Orchestration
  marks the session terminated, persists the `GameOutcome` to game history (see
  `game-history.md`), notifies the Room Service, then calls `TerminateSession` with
  `TERMINATION_REASON_GAME_OVER` to free Game Host state (FR-ORCH-003). Only the
  first `game_over` per session is honored (FR-EFF-007); no inputs are dispatched
  after it (FR-EFF-006).

  **The Room Service notification and the owed teardown commit together.** Game end
  is a *detach* — the room returns to Lobby (FR-LIFE-002) while the session is torn
  down — and it is the most frequent detach path there is. It therefore uses the same
  durable to-do as room closure ([ADR-0010](../../decisions/0010-session-teardown-ordering.md)):
  the room-state change and a teardown row are written in one transaction, and the
  `TerminateSession` call follows outside it. Without this, a crash between the
  notification and the terminate leaks the session — and the leak pins an Espresso
  context (§6.3) and its JAR (§7.1) for the life of the process.

**Seam.** This spec addresses effects *to* the Gateway with a recipient set and a
`sequence`; the mapping onto STOMP topics/queues and the client envelope is the
game-session WebSocket spec's job (GAME-B1) — now written:
[`../api-design/websocket.md` § Game Session Protocol](../api-design/websocket.md#game-session-protocol).
It also fixes the fan-out locality this spec left implicit: **session affinity follows
room affinity** (ADR-0002), so the pod running a session's dispatcher is the pod
holding every participant's WebSocket, and fan-out is a local call.

---

## 11. Registration, health & drain (FR-REG-*)

The Game Host is the **client** of `GameHostRegistryService`:

- **`Register`** on startup — advertise the dialable pod address + `runtime_types`
  (`["jvm"]` for the MVP). Receives the heartbeat interval + lease TTL.
- **`Heartbeat`** (bidi stream) — periodic load signals (`active_sessions`,
  `active_contexts`, `memory_used_percent`) refresh the Redis liveness lease; the
  server may push `drain=true` for graceful scale-in, and a host that received `SIGTERM`
  announces `draining=true` on an immediate beat (`IMP-M18-13`): the registry stops
  selecting it while it serves its sessions for `drain-period`, then `Deregister`s.
  Lease expiry ⇒ instance
  considered failed within NFR-REL-002 (< 30 s) → recovery (§9.3).
- **`ReportContexts`** — full snapshot of live `ContextKey`s for warm-host selection
  (FR-ORCH-004).
- **`Deregister`** on graceful shutdown — stop routing new sessions here (FR-REG-004).
- **Health endpoint** — liveness/readiness for Kubernetes and the failure detector
  (FR-REG-003).

**Host selection (FR-ORCH-001/004).** The keys are in §13. To place a new session, any Orchestration
replica takes the members of `hosts` and keeps those that (1) have a live `hostlease:{instanceId}`,
(2) are not `draining`, and (3) list `jvm` in `runtimeTypes`, and (4) are below their per-host session
cap (FR-SCALE-005, `load-testing-phase-b.md` §5.1). Among them it prefers instances whose
`contexts:{instanceId}` contains `{gameId}:{gameVersion}` (warm); **if every warm candidate is at its cap, a
cold one is chosen**, so a new replica takes load while the warm one still has no room. **While fewer than `warm-hosts`
(default 2) hosts are warm for the game and a cold candidate is below its cap, the cold one is chosen** (`session 251`): the
standby is warmed by one real start, so a drain or a failover lands on a host that already has the context instead of paying
a 21 to 28 s cold boot at 1 CPU. Ties — and the
no-warm-host case, where any candidate will create the context on demand — break on lowest `activeSessions`, then on
`instanceId` in lexical order, so the choice is deterministic for a given Redis state. No candidate
(every host at its cap included) is a transport-level `UNAVAILABLE` for the caller (session creation fails; nothing is written to
the room). The chosen `instanceId` is written to `routing:{sessionId}`; the dial address is always
re-read from `host:{instanceId}`, never copied into the routing key, so a host that re-registers at a
new address needs no routing rewrite. `Register` sets the `hosts` member, the `host:` hash and the
lease in that order and is idempotent for an `instanceId` already present; `Deregister` deletes the
lease first, then the `host:` hash, the `contexts:` set and the `hosts` member, so a concurrent
selection never sees a routable instance whose entry is half gone.

**Liveness timing.** `RegisterResponse` hands the Game Host `turnbase.orchestration.heartbeat-interval`
and `turnbase.orchestration.lease-ttl` (`../deployment/local-environment.md` §7.8); the lease TTL must
exceed the interval by at least a factor of two so a single delayed heartbeat does not fail a healthy
host, and stay under NFR-REL-002's 30 s detection bound.

**Warm-up before readiness (IMP-M7-09).** Before `Register`, and so before Spring publishes readiness,
the Game Host runs one synthetic session of an embedded trivial game (`io.turnbase.gamehost.bridge.WarmupGame`,
shipped in the guest bridge jar) through a **throwaway** guest context: `createSession`, one action, `resync`,
`disposeSession`, then the context is closed. It never touches `GameContextManager`, the Redis session record or
`ReportContexts`, so it cannot appear in history, statistics, `contexts:{instanceId}` or the active-session load
signal. A failure is logged at WARN and startup continues cold. What it removes is the one-time process-level
cost (native library load, Truffle/Espresso first-use); the per-context Espresso boot remains, because contexts
share no code (a shared `Engine` was measured and did not help). **It is off by default**
(`turnbase.gamehost.warmup-enabled`, `local-environment.md` §7.8): it is an extra Espresso boot in the JVM, and the
boot-wedge measurement below found that this extra boot makes the next, real boot wedge about ten times as often (21 of 80 cold starts against 2 of 80).
With it off the first game start boots cold: a median of 6.5 s (3.6 to 7.7) in the measurement runs, against 3.4 to 3.9 s after a warm-up.

**Healthy only once registered (IMP-M10-08).** Registration runs on a background thread so a monolith that is not up never blocks process start, which left a window where the host was ready but unknown to the registry and a first `START_GAME` found `NO_HOST_AVAILABLE`. A `registration` health contributor is `DOWN` until the first `Register` is acknowledged, then `UP` for good (a later re-register is not an outage), so `/actuator/health` — the Compose healthcheck — stays unhealthy until the orchestrator can route here.

**A wedged guest boot takes the host out of service ([ADR-0018](../../decisions/0018-game-start-resilience.md)).** Between one cold boot in ten and one in five deadlocks in Truffle's native interface (glibc 2.34: the `nfi-gc` thread against the boot thread's `dlsym`) and stalls the *whole* JVM at a safepoint: no Java thread runs, `jcmd` cannot attach, SIGTERM is ignored, `/actuator/health` does not answer, and until its lease lapses the host stays registered while every `CreateSession` times out. Nothing inside the JVM can act on that, so the image's entrypoint is `docker/supervise.sh`: it runs the JVM as a child in a loop, and after a 45 s grace per JVM SIGKILLs it and starts the next one at once when four consecutive probes of `/actuator/health/liveness` (`curl -sf`: only a 2xx is an answer; the liveness group excludes Redis and Postgres) get none, so a wedge never meets the kubelet's restart back-off. The script exits non-zero, and the restart policy (`restart: unless-stopped` under Compose, the pod's under Kubernetes) takes over, only after 5 JVM deaths within 10 minutes. It writes the JVM's pid to `/tmp/jvm.pid` and timestamps every line. As a second layer for a stuck guest thread in an otherwise live JVM, every guest boot — warm-up and each new context — runs under a `BootWatchdog` (`turnbase.gamehost.boot-timeout`, default 20 s): on expiry `HostWedge` publishes `LivenessState.BROKEN`, writes the marker file `turnbase.gamehost.wedge-marker` (default `/tmp/turnbase-wedged`), deregisters (4 s grace) and tries to halt the JVM with **exit code 70**; the supervisor checks the marker every second, grace or not, SIGKILLs the JVM at once and removes the file. The host starts no external process (the image has no `kill` binary). Both are mitigations for a runtime defect: revisit them on every GraalVM bump.

**Boot-wedge measurement (IMP-M16-03).** `loadtest/boot-wedge-repro.sh <cycles> <pairs>` deletes the Game Host pod, waits for the new
one to be Ready, runs the smoke scenario so that the first real guest boot happens through the platform with the Tic-Tac-Toe bundle,
and counts both wedge modes in the pod's logs: mode A (the supervisor's `killing it`: the whole-JVM stall) and mode B (the
`BootWatchdog` line `Guest boot wedged`). One cycle is one container cold start; the table is a rate of cold starts that wedged.

| Run (`loadtest/results/<dir>`) | Cycles, pairs | Wedged cycles (A / B) | Rate |
|---|---|---|---|
| Baseline, warm-up on (`20261019-192247-boot-wedge`) | 40, 1 | 11 (11 / 1) | 27.5 % |
| Experiment 1: warm-up context kept open until the first real boot has finished (`20261019-201630-boot-wedge`) | 40, 1 | 10 (10 / 0) | 25 % |
| Experiment 2: warm-up skipped (`20261019-210357-boot-wedge`) | 40, 1 | 0 (0 / 0) | 0 % |
| Rerun of the landed fix, warm-up off by default (`20261019-213729-boot-wedge`) | 40, 1 | 2 (2 / 0) | 5 % |

What the logs show. Every wedge, in every run, happens in the first real game boot, after `Game context created`; the warm-up's own boot never
wedged in the 80 cold starts that ran one. Hypothesis tested first: the throwaway warm-up context,
closed at once, races the real boot's native-library loading. Experiment 1 kept that context open and the rate did not move (25 against
27.5 %), so the race is not between the warm-up context's *close* and the real boot. Experiment 2, chosen from the evidence (the wedge
needs an earlier Espresso boot in the same JVM), dropped the warm-up: 2 wedges in 80 cold starts against 21 in 80 with it. The cause
inside Truffle's native interface is not found and not fixable here (ADR-0018 *Context*); the second boot is what raises the odds, not
what the deadlock needs, since 2 of 80 still wedged without it. The residual rate is covered by the supervisor above (about 50 s to a
working game in a wedged cycle, `seconds_to_first_game` 47 to 53 s in the CSVs). Not measured: contention (`<pairs>` 4), because the
baseline reproduced; a second game on one host (its second context is the same extra boot, `IMP-M16-05` should repeat the 40 cycles
with two games).
For the single-instance MVP these are implemented but trivially satisfied
(host selection always resolves to the one instance); the machinery exists so
scale-out is a config change, not a redesign (ADR-0001).

---

## 12. Timeouts, failures & `GameFailureKind` mapping

**Handler timeout (FR-CTX-008).** Each invocation runs under a watchdog (default
30 s, configurable, aligned with the GDK contract). On expiry the host calls
`Context.interrupt(graceDeadline)`; the invocation ends with a `PolyglotException`
→ `GAME_FAILURE_KIND_TIMEOUT`. If interrupt does not yield within an escalation
grace, the host calls `Context.close(true)` → the context is destroyed →
`GAME_FAILURE_KIND_CONTEXT_CRASH` for **all** sessions in that context (FR-FAIL-007).

> **Interrupt blast-radius caveat (owner-accepted).** `Context.interrupt` is
> **context-scoped**, not per-invocation. If two sessions in one context run
> concurrently and one times out, the interrupt may also abort the sibling
> invocation. The sibling surfaces as a retryable failure with its **state
> uncommitted** (§9.1 commits only on OK), so it is simply re-dispatched from the
> queue with no data loss. Acceptable because timeouts are rare bugs in trusted
> code; a per-session-isolated interrupt (e.g. context-per-session, or serialized
> per-context invocation) is a documented alternative for higher concurrency (OQ-2).

**Full mapping** (host detects → in-band `ProcessResult` unless noted):

| Condition | `GameFailureKind` / status |
|-----------|-----------------------------|
| Hook threw (incl. `ActionDecodeException`, `ParameterAccessException`) | `HANDLER_EXCEPTION` |
| Watchdog fired | `TIMEOUT` |
| Null/invalid result, bad effects, effect payload > 10 MB | `MALFORMED_OUTPUT` |
| Serialized state > 10 MB | `STATE_TOO_LARGE` |
| Context OOM / `System.exit` disposal / `close(true)` escalation | `CONTEXT_CRASH` |
| Entry class missing / not a `TurnBaseGame` | `CODE_LOAD_ERROR` (→ `FAILED_PRECONDITION` at create) |
| Host unreachable / crashed | transport `UNAVAILABLE` (reassign, §9.3) |
| Message over the size ceiling | transport `RESOURCE_EXHAUSTED` |
| Session unknown & no Redis record | transport `NOT_FOUND` (terminal) |

Game-level failures are **deterministic** (re-dispatch won't fix) but still counted
toward the retry limit (§9.4); transport failures are infrastructure signals handled
by reassignment. This is the two-tier model of the protocol doc, realized.

---

## 13. Redis data model

| Key | Type | Owner (writer) | Contents / TTL |
|-----|------|----------------|----------------|
| `session:{sessionId}` | hash/json | Game Host | the atomic session record (§8.1). Deleted on terminate. **TTL 24h, refreshed on every write.** |
| `routing:{sessionId}` | string | Orchestration | `instanceId` currently holding the session. Cleared on host failure. **TTL 24h, refreshed on every write.** |
| `queue:{sessionId}` | list | Orchestration | pending inputs in arrival order (FR-ROUTE-001). **TTL 24h, refreshed on every write.** |
| `gamekey:{sessionId}` | string | Orchestration | the session's `ContextKey`, formatted `{gameId}:{gameVersion}` like the members of `contexts:{instanceId}`. Written with `routing:` at session creation; it is what lets Orchestration re-run host selection (§11) to reassign the session when its host is `UNAVAILABLE` (FR-ORCH-005), because `routing:` holds only an `instanceId`. Deleted with the rest of the family. **TTL 24h, refreshed on every write.** |
| `roster:{sessionId}` | hash | Orchestration | the players the session **started** with, `userId → teamId`, written with `gamekey:` at session creation. The room's own participant rows lose a player who leaves, so the roster read at `game_over` for history and statistics (`flows/06` §B–C) must not come from them — a forfeit's outcome names the leaver. Deleted with the rest of the family. **TTL 24h, refreshed on every write.** |
| `seq:{sessionId}` | counter | Orchestration | monotonic `sequence` allocator (§9.2). **TTL 24h, refreshed on every write.** |
| `delivered:{sessionId}` | string | Orchestration | delivery watermark (§9.2). **TTL 24h, refreshed on every write.** |
| `failcount:{sessionId}` | counter | Orchestration | consecutive-failure counter (§9.4). **TTL 24h, refreshed on every write.** |
| `gamelog:{sessionId}` | list | Orchestration (effect fan-out) | the session's retained `log` effects, one JSON `{sequence, index, entry}` per element in `(sequence, index)` order (§10, FR-DELIVER-003) — what `GAME_SYNC.payload.log` replays. The only per-session effect data retained. Deleted with the rest of the family. **TTL 24h, refreshed on every write.** |
| `hosts` | set | Orchestration | `instanceId`s that have registered and not deregistered — the enumeration point for host selection (§11). No TTL; a member whose `host:{instanceId}` has expired is `SREM`ed when next read. |
| `host:{instanceId}` | hash | Orchestration (in `Register`, `Heartbeat`, `Deregister`) | the instance's registry entry: `address` (the dialable `RegisterRequest.address`, which every replica dials — `orchestration-gamehost-protocol.md` *Addressing the Game Host pods*), `runtimeTypes` (comma-separated), `activeSessions`, `activeContexts`, `memoryUsedPercent` (the latest heartbeat's load signals) and `draining` (`true`/`false`). **TTL 24h, refreshed on every write.** Liveness is *not* read from this key — that is `hostlease`. |
| `hostlease:{instanceId}` | string + TTL | Orchestration, on the Game Host's behalf (each `Register` and `Heartbeat` sets it) | liveness lease; the value is the `instanceId`, the TTL is `turnbase.orchestration.lease-ttl`; expiry ⇒ failed (§11). The Game Host never touches Redis's registry keys — it reaches them only through `GameHostRegistryService`. |
| `contexts:{instanceId}` | set | Orchestration, from `ReportContexts` (replaced atomically with each full snapshot) | live `ContextKey`s for warm selection (§11), one member per key, formatted `{gameId}:{gameVersion}`. **TTL 24h, refreshed on every write.** |
| `pod:{podId}:alive` | string + TTL | Platform Monolith pod (self) | pod liveness lease, TTL 10s renewed every 3s; gates room-ownership takeover ([ADR-0008](../../decisions/0008-room-ownership-lifecycle.md)). |
| `room:{roomId}:pod` | string | claim/release scripts only | owning pod for the room. No TTL — ownership is released explicitly or taken over under the liveness gate (ADR-0008). |
| `platform:sentinel` | string | Platform Monolith (at startup) | no TTL. Its absence while Redis is *reachable* proves the datastore was reset, letting reconciliation report one mass-loss event instead of N per-room warnings (`platform-operations.md` FR-JOB-008). |

**TTLs are a backstop, not the cleanup mechanism** — teardown deletes these keys
explicitly (§9.1). The 24h expiry exists so that any leak class, including one that
escapes the durable re-drive, cannot grow Redis without bound. It is deliberately far
longer than any real session, so a live game can never be collected by it.

All Orchestration state is in Redis, keeping the service stateless & horizontally
scalable (FR-ORCH-006/007, CON-011). Session-record writes are atomic (§8.1);
delivery + dequeue + watermark advance are performed as a guarded unit so a replay
cannot double-deliver.

---

## 14. Observability (FR-OBS-*)

- **Metrics (Game Host):** active context count (FR-OBS-001); total + per-context
  session count (FR-OBS-002); per-context memory where the Truffle API exposes it
  (FR-OBS-003, Should); action latency histogram (FR-OBS-004).
- **Metrics (Orchestration):** active sessions, queue depth (total + per-session),
  effect-delivery latency, Game Host instance count, session-failure count, Redis op
  latency (FR-OBS-009).
- **Events:** context create/destroy (with reason: idle | pressure | crash),
  context crash (FR-OBS-005); session create/complete/fail with reason (FR-OBS-006);
  artifact cache hit/miss (with fetch latency)/eviction (FR-OBS-007, Should).
- **Correlation (FR-OBS-008):** `sessionId` on all session-scoped logs/metrics;
  `gameId`+`gameVersion` on game-scoped events; `instanceId`+`ContextKey` on
  control/context events. W3C trace context propagates via gRPC metadata (one span
  per dispatch), per the protocol doc.

---

## 15. Configuration surface (per-env — GRMP-F6)

All tunable via env/config, never hard-coded:

| Setting | Default |
|---------|---------|
| handler timeout | 30 s |
| interrupt→`close(true)` escalation grace | 5 s |
| context idle-eviction timer | 5 min |
| host memory-pressure eviction threshold | e.g. 80 % |
| artifact cache size limit | configurable |
| gRPC message-size ceiling | ~16–32 MB (protocol doc) |
| Redis-unavailable session-fail window | 60 s |
| heartbeat interval / lease TTL | from `RegisterResponse` |
| retry limit | 3 (FR-FAIL-003) |
| Artifact Store backend + endpoint | local-FS (dev) |
| guest `java.JavaHome` | `/opt/graalvm-guest-jdk21` |
| concurrent guest boots (`turnbase.gamehost.max-concurrent-boots`) | 2 (§6.1) |
| Espresso contexts created per JVM (`turnbase.gamehost.max-context-creations`) | 12 (§6.1, `OQ-6`) |

---

## 16. Testing strategy

- **Unit (host):** effect-envelope → proto exhaustive-switch mapping; idempotency
  (`CreateSession` replay, `sequence ≤ lastApplied` replay); session-record atomicity
  (torn-write rejection); failure→`GameFailureKind` mapping.
- **Unit (shared serialization):** the **round-trip smoke test** (GRMP-F4) run
  through the *same* engine used in production and in the harness.
- **Integration (real Espresso, CE 21):** load a fixture game JAR into a live
  context and assert the spike-verified behaviors — cross-context isolation
  (FR-CTX-001/003), `System.exit` containment (FR-CTX-006), `Context.interrupt`
  timeout (FR-CTX-008), and end-to-end `CreateSession`→`ProcessInput`→`game_over`.
- **Integration (recovery):** kill/drop a host mid-session and assert Redis-backed
  recovery with no double-apply (GAME-B2) and exactly-once delivery.
- **Coverage:** the execution path is critical (> 70 %, per CLAUDE.md).

---

## 17. Requirements traceability

| Requirement(s) | Realized by |
|----------------|-------------|
| FR-CTX-001/003/006/008/011 | §4 (Espresso), §6 |
| FR-CTX-004/005/007 | §4 (container), §4.1 |
| FR-CTX-002/009/010/012 | §6.1, §6.3, §10-runtime-abstraction |
| FR-SESS-001…006 | §6.2, §8, §9.1 |
| FR-LOAD-001…005 | §7 |
| FR-REG-001…004 | §11 |
| FR-ORCH-001…007 | §9.2/§9.3/§11, §13 |
| FR-ROUTE-001…005 | §9.2, §13 |
| FR-DELIVER-001…004 | §10 |
| FR-FAIL-001…007 | §9.3, §9.4, §12 |
| FR-SEC-001…005 | §4.1 |
| FR-OBS-001…009 | §14 |
| Idempotency / crash recovery (GAME-B2) | §8.1, §9.1, §9.3 |
| Effect delivery (GAME-B1, exec half) | §10 |
| Serialization round-trip (GRMP-F4) | §5, §16 |
| GDK Host injection / guest classpath (GAME-I1/I2) | §3, §7 |

---

## 18. Open questions

- **OQ-1 — per-context memory overhead & FR-CTX-007 granularity.** The MVP caps
  memory at the pod (cgroup); a true per-context cap is Oracle-GraalVM-only. Benchmark
  Espresso per-context overhead (spike OQ-001) before designing high-density
  many-versions-per-pod packing and revisit whether an Oracle-edition per-context cap
  is worth departing from CE.
- **OQ-2 — per-session interrupt isolation.** The context-scoped `Context.interrupt`
  caveat (§12) is accepted for the MVP. If cross-session concurrency density grows,
  evaluate serialized-per-context invocation or context-per-session.
- **OQ-3 — instance sharing.** One `TurnBaseGame` instance per session is the MVP
  default; the purity contract permits a single shared instance per context as a
  memory optimization once real games validate the no-mutable-field assumption.
- **OQ-4 — live-object state cache.** JSON-as-canonical state deserializes per
  invocation. If a real game's state (de)serialization proves a hotspot within the
  30 s budget, add an opt-in live-guest-object cache keyed by session (still
  persisting JSON to Redis).
- **OQ-5 — eager or lazy reassignment after a Game Host dies. Resolved 2026-10-29 (`IMP-M18-12`): lazy.**
  §9.3 once read as *eager* (reassign at lease expiry); the code reassigned *lazily* on the first
  `ProcessInput` whose routed host is unreachable. Eager was implemented behind a switch and both modes
  ran one ten-scenario correctness suite (kill mid-move applied and not applied, idle kill with the next
  input after 1 s, the TTL and the reassignment, a pending timer, a zombie host, two kills in succession, a
  planned drain, concurrent inputs). Neither mode had a correctness failure of its own and both recovered
  well inside NFR-REL-002, so the tie rule chose lazy, the code that exists; eager's sweep and switch were
  removed. Evidence: [`docs/reviews/2026-10-29-m18-reassignment`](../../reviews/2026-10-29-m18-reassignment/INDEX.md).
  The suite found one defect common to both and fixed it: two kills within one lease TTL could re-select the
  first dead host, so `reassign` now quarantines the failed host for the lease TTL.
- **OQ-6 — a JVM can create only twelve Espresso contexts in its lifetime. Resolved 2026-11-06 (`IMP-M20-18`): the host counts creations and retires at the limit.**
  Measured by `IMP-M16-05` and reproduced by `IMP-M20-18` (GraalVM CE 21.0.2, glibc 2.39): creating,
  initialising and closing one context at a time succeeds twelve times and the thirteenth fails with
  `EspressoError: Cannot load library: eden`, on one shared engine, with the `nfi-dlmopen` backend named
  explicitly, and with closed contexts. The bound matches glibc's sixteen `dlmopen` namespaces (`DL_NNS`),
  of which Espresso takes one per context and the closing of a context does not return it; this was not
  proven (no loader trace), the count of twelve is. Every creation counts, also the re-creation of a
  context that idle or memory-pressure eviction closed (§6.3) and the one a restored session needs
  (§9.3). Before the decision the thirteenth creation surfaced as a gRPC `INTERNAL` and every later one
  did too: the host stayed registered, healthy and unable to start any game.
  **Decision:** `ContextBudget` counts creations against `turnbase.gamehost.max-context-creations`
  (default `12`; the warm-up context, when enabled, takes one). The creation past the budget is refused
  before Espresso is asked and answers `UNAVAILABLE`, so the Platform picks another host (§11). The first
  refusal retires the host: it announces `draining`, serves its sessions for `drain-period`, deregisters,
  then exits through the wedge path (marker file, supervisor starts a fresh JVM with a fresh budget). What
  remains is reassigned lazily (OQ-5). Not chosen: evicting less (it only postpones the thirteenth and
  trades memory for it) and an early restart before the limit (it kills sessions that would have fit).
  Pinned by `ContextBudgetTest` and `HostWedgeTest`.
