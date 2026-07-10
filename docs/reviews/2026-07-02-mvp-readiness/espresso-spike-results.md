# Espresso Feasibility Spike — Results

**Date:** 2026-07-10
**Gates:** ADR-0005 (Espresso spike gates the Game Host internals spec), review blocker **GAME-I1**, open questions **OQ-001/OQ-002**
**Runtime under test:** GraalVM CE 21.0.2+13.1 (`21.0.2-graalce`, JVMCI 23.1) — the free Community Edition for JDK 21 the project targets.
**Polyglot / Espresso version:** `23.1.2` (Maven artifacts, since GraalVM for JDK 21 ships Espresso as `org.graalvm.polyglot:java-community`, not a bundled `gu` component).

## Purpose

ADR-0005 required a small technical spike, run **before** freezing the FR-CTX enforcement design,
to answer two unverified assumptions about **in-JVM Espresso on GraalVM CE for JDK 21**:

1. Which of the FR-CTX isolation controls actually work on CE (heap cap, no filesystem, no network,
   `System.exit` containment, forced termination)?
2. Does Espresso context startup fit the (now deferred) 3s/5s startup Musts?

## Method

A throwaway Maven project boots an Espresso (`java`) guest context, loads a trivial untrusted
"guest game" (`guest.TrivialGame`, on the guest `java.Classpath`, never on the host classpath),
and invokes methods that each probe one control. Each probe is isolated in try/catch; a call that
**returns** where it should have been blocked is a **LEAK**, a call that **throws** (surfacing as a
`PolyglotException`) means the control held. The host builder used the strictest polyglot lockdown:
`allowHostAccess(NONE)`, `allowHostClassLoading(false)`, `allowCreateThread(false)`,
`allowCreateProcess(false)`, `allowIO(IOAccess.NONE)`, `allowEnvironmentAccess(NONE)`.

(The spike project lives in a transient scratchpad, not committed. Re-create from this report if
needed; it is ~3 small files.)

## Results

| FR-CTX control | Result on CE 21 | Evidence |
|----------------|-----------------|----------|
| **Boot at all** | ⚠️ Only with **native access enabled** | `allowNativeAccess(false)` → `EspressoError: Native access is not allowed by the host environment but it's required to load Espresso/Java`. Espresso cannot boot without polyglot native access. |
| **Java 21 guest** | ⚠️ Requires an external `java.JavaHome` | The bundled Maven `espresso-runtime-resources` guest JDK is **17.0.7**. A Java-21 (class major 65) guest is rejected (`Unsupported major.minor version 65.0`) until `java.JavaHome` points at a real JDK 21. |
| FR-CTX-002 startup | ✅ Fast | create + class-load + first guest call: **cold ≈ 0.56–0.66 s, warm ≈ 0.25–0.45 s** (host JVM already warm; excludes container/JVM cold start). |
| FR-CTX-001/003 cross-context isolation | ✅ Isolated | Static `KEEP` list grown in context A (size 4) reads back as 0 in context B — separate heaps/statics per context. |
| FR-CTX-006 `System.exit` containment | ✅ Contained | Guest `System.exit(42)` disposes **only the guest context** (`java.ExitHost=false` is the default); the host process survived and the run continued. Caveat: it kills the *whole* context (every session sharing that game-version context), consistent with FR-FAIL-007. |
| FR-CTX-008 forced termination | ✅ Works | A hot `while(true)` loop was stopped by `Context.interrupt(5s)` in **≈ 5 ms**; the guest invocation ended with `PolyglotException: Execution got interrupted`. `close(true)` is available as escalation. |
| **FR-CTX-004 no filesystem** | ❌ **LEAK** | Guest read `/etc/passwd` and returned `root:x:0:0:...`. `IOAccess.NONE` did **not** block it. |
| **FR-CTX-005 no network** | ❌ **LEAK** | Guest opened a TCP connection to a public IP:80 successfully. |
| **FR-CTX-007 per-context heap cap** | ❌ **Unavailable** | `sandbox.MaxHeapMemory` requires a `SandboxPolicy` of `CONSTRAINED`+; every such policy is rejected on CE (`validation ... failed`), and the option is an Oracle-GraalVM feature. |
| SandboxPolicy tiers (`CONSTRAINED`/`ISOLATED`/`UNTRUSTED`) | ❌ Unusable with Espresso on CE | All rejected; Espresso only runs at the effective `TRUSTED` level (native access on, no policy). |

### Root cause of the FS/network leaks

Espresso on CE **cannot boot without polyglot native access**. Once native access is enabled, the
guest JDK's `java.io`/`java.net` execute the standard JDK native methods (`libjava`, sockets)
straight against the host OS. Truffle's `IOAccess` governs the *Truffle-mediated* `FileSystem`
abstraction, not the guest JDK's own native syscalls, so it does not interpose here. The leak is
**not** an artifact of pointing `java.JavaHome` at an external JDK — it reproduces identically with
the **bundled managed JDK 17 guest** (no external home). Enumerating Espresso's language options
(`java.NativeBackend`, `java.EnableNativeAccess`, `java.ExitHost`, …) confirms there is **no**
built-in knob to interpose a filesystem/network deny policy; the strong per-context controls
(heap cap, sandbox tiers) are Oracle-GraalVM-only.

## Conclusion

**In-JVM Espresso on GraalVM CE for JDK 21 does not, by itself, satisfy the FR-CTX Musts.**
It delivers three things cleanly — per-game-version heap/static isolation (FR-CTX-001/003),
`System.exit` containment (FR-CTX-006), and per-invocation forced termination (FR-CTX-008) — plus
fast context startup. But the three isolation Musts that matter most for running *untrusted* code —
**no filesystem (FR-CTX-004), no network (FR-CTX-005), and a per-context memory cap (FR-CTX-007)** —
are **not enforceable in-context on CE**. Filesystem and network access leak straight to the host
OS; the memory-cap mechanism is Oracle-GraalVM-only.

This is the outcome ADR-0005 anticipated: the **OQ-002 process/container-isolation fallback is
required for the MVP**, not merely a contingency. Espresso alone is insufficient as the security
boundary on CE.

## Recommendation for the Game Host internals spec

Obtain FS/network/memory isolation from the **OS/container layer**, and decide Espresso's role
against that backdrop. Two viable shapes:

1. **Espresso inside a hardened container (recommended to evaluate first).** Keep Espresso for its
   ergonomics — in-process GDK invocation, `Context.interrupt` forced termination, and running
   multiple game versions densely in one JVM — but run each Game Host in a container with **no
   network** (network policy / no egress), an **empty or read-only filesystem** (read-only rootfs +
   `tmpfs`, seccomp), and a **cgroup memory limit** per pod. The container provides FR-CTX-004/005/007;
   Espresso provides FR-CTX-001/003/006/008. gVisor in production (ADR-0001 defers it).
2. **Plain-JVM process isolation (OQ-002 literal).** One standard JDK 21 process/container per
   game-version context; drop Espresso. Simpler and the isolation story is entirely OS-level, but
   loses the shared-heap density (FR-CTX-001) and the clean in-process invocation boundary.

Because a hardened container is required for FS/net/memory **either way**, Espresso's marginal value
reduces to (a) in-process invocation + forced termination and (b) multi-version JVM density. Both
are real but not decisive; the internals spec should choose deliberately.

### Concrete follow-ups the internals spec must record

- **Guest JDK packaging:** the Game Host image must ship a **JDK 21** and pass it as `java.JavaHome`
  (or use a matching `espresso-runtime-resources` build); the default Maven Espresso guest is JDK 17.
- **Native access is mandatory** for Espresso on CE — the FR-CTX enforcement design cannot assume
  `allowNativeAccess(false)`.
- **Drop `IOAccess.NONE` / `sandbox.MaxHeapMemory` as the stated enforcement mechanisms** for
  FR-CTX-004/005/007; cite the container-layer controls instead. Record the CE limitation in
  `game-contracts.md` CON-001 (its "everything is available in CE" claim is false for these three).
- **Keep** `Context.interrupt`/`close(true)` as the FR-CTX-008 mechanism and `java.ExitHost=false`
  (default) as the FR-CTX-006 mechanism — both verified.
- **OQ-001** (per-context memory overhead) remains open; it was out of scope for this go/no-go spike
  and should be benchmarked when the density model (shape 1 vs 2) is chosen.

## Follow-up (2026-07-10): would gVisor or Oracle GraalVM change this?

Two follow-up levers were tested/analysed. **Neither removes the need for OS/container-level
FS+network isolation.**

### gVisor — helps, but at the OS layer (not the in-JVM layer)

gVisor (`runsc`) is a user-space kernel that intercepts guest syscalls. It is the right **production
mechanism** for the FR-CTX-004/005 denial that Espresso cannot provide in-JVM: run the Game Host pod
with no egress + read-only rootfs, and gVisor mediates every syscall the guest JDK's native `java.io`/
`java.net` attempt — also shrinking the blast radius of a JVM/Espresso escape (defense-in-depth
around the native-access surface Espresso forces open). What gVisor does **not** provide: per-game-
version isolation *inside* one JVM, or a per-context heap cap — memory stays a cgroup/pod limit and
all versions sharing a JVM share one sandbox. It is complementary to the container config, not a
substitute, and ADR-0001 already defers it to production (WSL2 can't run `runsc` locally). It does
not change any in-JVM finding above.

### Oracle GraalVM 21.0.11 — buys exactly one extra control (the heap cap)

Ran the same probes on **Oracle GraalVM 21.0.11** (`21.0.11-graal`, GRAALVM_VERSION 23.1.11) using
the **Oracle** Espresso artifact (`org.graalvm.polyglot:java`, not `-community`):

| Control | CE 21 (java-community) | Oracle GraalVM 21 (java) |
|---------|------------------------|--------------------------|
| FR-CTX-001/003 cross-version isolation | ✅ | ✅ |
| FR-CTX-006 `System.exit` containment | ✅ | ✅ |
| FR-CTX-008 forced termination | ✅ | ✅ |
| FR-CTX-002 startup | ✅ | ✅ |
| **FR-CTX-007 per-context heap cap** | ❌ unavailable | ✅ **enforced** — `sandbox.MaxHeapMemory=96MB` blocked a 256 MB allocation (`Maximum heap memory limit … exceeded`, resource-exhausted) |
| **FR-CTX-004 filesystem** | ❌ leak | ❌ **still leaks** |
| **FR-CTX-005 network** | ❌ **still leaks** | ❌ **still leaks** |

Crucially, `sandbox.MaxHeapMemory` is honored on Oracle even under the **`TRUSTED`** policy — the only
policy Espresso can use. Every stricter tier is unusable with an Espresso guest: `CONSTRAINED`
rejects `java.Classpath` ("can only be used up to the TRUSTED sandbox policy" — so no guest game can
be loaded) **and** forbids native access (which Espresso needs to boot); `ISOLATED`/`UNTRUSTED`
additionally require native-image isolates Espresso does not run in here. So Oracle GraalVM cannot
deny FS/network at the policy level either — those still require the OS/container layer.

**Net:** Oracle GraalVM's only advantage over CE for this platform is a **per-context (per-game-
version) heap cap** inside a shared JVM. But since a hardened container is required anyway for
FS/network, that container's **cgroup memory limit already caps memory at the pod level** for free.
The per-context cap only matters if many game versions are packed into one JVM/pod and each needs an
independent memory ceiling (a high-density optimization). It does **not** move the MVP off the
OS/container-isolation requirement.

**Recommendation on edition:** **Stay on GraalVM CE** (honours CON-001's "Oracle GraalVM is not
required") and obtain FS/network/memory from the container layer (gVisor in production, plain
no-network/read-only-FS + cgroup memory limit locally). Revisit Oracle GraalVM only post-MVP **if**
a high-density "many game versions per JVM" model makes per-context heap caps worth the departure
from CE — and note Oracle GraalVM for JDK 21 is free under the GFTC but is not the Community Edition.
