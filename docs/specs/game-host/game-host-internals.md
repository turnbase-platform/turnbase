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
| `createSession(sessionId, teamsJson, parametersJson)` | roster + materialized params | `InvocationEnvelope` |
| `processAction(sessionId, stateJson, playerJson, payloadJson)` | current state + action | `InvocationEnvelope` |
| `processPlayerJoined(sessionId, stateJson, playerJson)` | current state + joiner | `InvocationEnvelope` |
| `processPlayerLeft(sessionId, stateJson, playerJson, reason)` | current state + leaver | `InvocationEnvelope` |
| `resync(sessionId, stateJson, viewerJson, role)` | current state + viewer | `ViewEnvelope` |
| `disposeSession(sessionId)` | — | `void` |

`teamsJson`, `playerJson`, and the `GameOutcome` in the envelope are **platform
types** (mirroring the proto `Team`/`PlayerRef`/`GameOutcome`) serialized with a
platform-fixed schema the host also understands. Everything game-defined —
`stateJson`, action `payloadJson`, effect payloads, `resultsPayload` — is an
**opaque JSON string** the host copies verbatim into proto `bytes` (UTF-8).

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

`IOAccess.NONE` / `sandbox.MaxHeapMemory` are **not** relied upon as enforcement —
the spike proved they do not interpose Espresso's native `java.io`/`java.net`; the
container provides FS/network/memory (CON-001 correction). Native access is on, so
the guest JDK's native methods run against the (container-restricted) host OS.

---

## 5. Serialization engine (shared component — GRMP-F4)

- **Format:** JSON via Jackson (CON-004, FR-GDK-013). State types and payloads are
  plain JSON-serializable records/POJOs; developers write **no** serialization code.
- **Where it runs:** entirely **guest-side**, inside the bridge, over guest classes.
- **Shared artifact.** The exact ObjectMapper configuration and the round-trip
  serialize↔deserialize logic live in **one module** reused by (a) the guest bridge
  and (b) the local test harness / upload validator. This makes the **GRMP-F4
  round-trip smoke test** structural: a state object that fails to round-trip is
  caught at upload/harness time with the *same* engine that runs in production, so
  the two cannot drift.
- **Limits (checked guest-side, mapped to `GameFailureKind`):**

  | Check | Failure |
  |-------|---------|
  | serialized `stateJson` > 10 MB (NFR-SIZE-001, FR-STATE-004) | `STATE_TOO_LARGE` |
  | any serialized effect payload > 10 MB (NFR-SIZE-002) | `MALFORMED_OUTPUT` |
  | result null / null state / unserializable / `ActionDecodeException` / any hook throw | `HANDLER_EXCEPTION` or `MALFORMED_OUTPUT` per backend-gdk §9 |

---

## 6. Context, session & instance model

### 6.1 Context (per game-version)

- **Creation on demand (FR-CTX-002).** On the first input for a `ContextKey` with no
  live context, the host fetches the backend JAR (§7), builds the context (§4.2),
  loads and verifies the entry class (§7.2), then proceeds. Concurrent requests for
  the same cold `ContextKey` are coalesced behind a single creation (one context,
  not a race of many).
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

The bridge loads the manifest `backend.entryPoint` FQCN via the guest classloader,
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
in local memory (primary read/write path, FR-SESS-003) and mirrors it to Redis
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
  "stateJson":           "…",     // opaque; the last successfully-applied state
  "lastAppliedSequence": 42,      // highest sequence applied (CreateSession = 0)
  "lastEffects":         [ … ]    // proto-mapped effects produced at lastAppliedSequence
}
```

- Written by the **Game Host** (it computes state + effects).
- Read by the **Game Host** on recovery, and by the **Orchestration Service** for
  the delivery watermark (§9.2) and terminal cleanup.
- **`lastEffects` retention** enables idempotent replay of the *most recent*
  sequence. It is not a full history; `game_over` results and the game log are
  retained separately by Orchestration for join/reconnect replay (FR-DELIVER-003).
- **Atomicity requirement.** `{stateJson, lastAppliedSequence, lastEffects}` MUST be
  written as **one atomic unit** (a Lua script or `MULTI/EXEC`). A torn write that
  advanced the sequence without the matching state is the exact bug GAME-B2 flags;
  the atomic record forbids it.

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

**`ProcessInput` (idempotent replay by `sequence`):**

```
1. If input.sequence  ≤ record.lastAppliedSequence → REPLAY record.lastEffects
   with OK; do NOT invoke the handler.               ← at-most-once application
2. If session not in local memory → load record from Redis (recovery, §9.3);
   NOT_FOUND if no record exists at all (terminal).
3. Acquire the per-session single-flight lock (§6.2).
4. bridge.process*(sessionId, record.stateJson, …) under the 30 s watchdog (§12).
5. On OK: atomically write { stateJson', lastAppliedSequence = input.sequence,
   lastEffects = effects' }; then return ProcessResult(sequence, OK, effects').
6. On failure: return ProcessResult(sequence, FAILED, failure) — state unchanged.
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
(terminating an already-gone session is a no-op success).

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
expires → Orchestration marks the instance failed, clears `routing:{sessionId}` for
its sessions, selects a new host, and **re-dispatches the head-of-queue input**. The
new host has no local state → loads `session:{id}` from Redis (§9.1 step 2),
recreates the context + instance, sets the state, and proceeds. Because the instance
is stateless and the record *is* the state, **no history replay is needed**.

**The in-flight action** (being processed at crash) is still in the queue (never
dequeued without `OK`). If the dead host had actually applied it (advanced
`lastAppliedSequence`, atomic §8.1) but died before returning, the re-dispatch hits
§9.1 step 1 → **replay**, so the action is not double-applied (GAME-B2 closed). If it
had not applied it, the new host applies it fresh. Either way: exactly-once.

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
- **`onInit` effects are not delivery-guaranteed.** They are fanned out at sequence 0,
  when typically no client has subscribed yet. This is by design and is why `Resync`
  exists (game-contracts.md FR-IN-006/FR-FE-001, review **I6**).
- **`game_over` handling.** After the game-over effect is delivered, Orchestration
  marks the session terminated, persists the `GameOutcome` to game history (see
  `game-history.md`), notifies the Room Service, then calls `TerminateSession` to
  free Game Host state (FR-ORCH-003). Only the first `game_over` per session is
  honored (FR-EFF-007); no inputs are dispatched after it (FR-EFF-006).

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
  server may push `drain=true` for graceful scale-in. Lease expiry ⇒ instance
  considered failed within NFR-REL-002 (< 30 s) → recovery (§9.3).
- **`ReportContexts`** — full snapshot of live `ContextKey`s for warm-host selection
  (FR-ORCH-004).
- **`Deregister`** on graceful shutdown — stop routing new sessions here (FR-REG-004).
- **Health endpoint** — liveness/readiness for Kubernetes and the failure detector
  (FR-REG-003).

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
| `session:{sessionId}` | hash/json | Game Host | the atomic session record (§8.1). Deleted on terminate. |
| `routing:{sessionId}` | string | Orchestration | `instanceId` currently holding the session. Cleared on host failure. |
| `queue:{sessionId}` | list | Orchestration | pending inputs in arrival order (FR-ROUTE-001). |
| `seq:{sessionId}` | counter | Orchestration | monotonic `sequence` allocator (§9.2). |
| `delivered:{sessionId}` | string | Orchestration | delivery watermark (§9.2). |
| `failcount:{sessionId}` | counter | Orchestration | consecutive-failure counter (§9.4). |
| `hostlease:{instanceId}` | string + TTL | Game Host (via heartbeat) | liveness lease; expiry ⇒ failed (§11). |
| `contexts:{instanceId}` | set | Game Host | reported live `ContextKey`s for warm selection (§11). |

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
