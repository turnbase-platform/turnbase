# ADR-0019: All guest contexts share one Espresso engine

- **Status:** Accepted
- **Date:** 2026-10-19
- **Deciders:** Project owner (acceptance rule, `IMP-M16-05`)
- **Amends:** `../specs/game-host/game-host-internals.md` §4.2 (context-builder configuration), §6.1, §18
- **Relates to:** [ADR-0005](0005-game-sandbox-espresso-spike.md),
  [`espresso-spike-results.md`](../reviews/2026-07-02-mvp-readiness/espresso-spike-results.md)
- **Executed by:** `IMP-M16-05` in [`registry.md`](../implementation/registry.md)

## Context

`load-testing.md` §13 finding 9: four Espresso contexts cost about three times the CPU and twice the heap
of one. `EspressoContextFactory` built every context without an `Engine`, so each one got an engine of its
own and, with it, its own copy of the Truffle caches, the loaded guest JDK and the compiled code.

## Decision

The Game Host creates **one `org.graalvm.polyglot.Engine`** (Spring bean `guestEngine`) and builds every
guest context on it (`Context.Builder.engine(...)`). The warm-up context uses the same engine. Contexts stay
separate; every option in §4.2 is set per context exactly as before.

**Acceptance rule (the owner's).** Adopt if the game-host tests pass and a committed benchmark shows at
least 25% lower CPU time *or* at least 25% lower heap after GC than per-context engines. The benchmark is
`EngineSharingBenchmarkIT` (`src/test/java/io/turnbase/gamehost/espresso/bench/`, run under
`-Pintegration`). Each mode runs in its own JVM; the run boots four contexts (the guest classpath is the
test classpath, one context per distinct key), creates a session in each and plays 100 moves in each, then
reads process CPU time (`getProcessCpuTime`, which includes the compiler threads) and the heap after three
`System.gc()` calls with the contexts still open. GraalVM CE 21.0.2, Espresso 23.1.2.

| Measured (seven runs per mode, 100 and 200 moves, 2026-10-19) | Engine per context | One shared engine | Saving |
|---|---|---|---|
| Heap after GC | 319–321 MB | 220 MB | **31%** |
| Process CPU time | 104–121 s | 103–119 s | −1% to 4% |
| Wall time | 12.9–15.1 s | 12.7–14.9 s | about 2% |

Heap clears the 25% bar; CPU does not and nothing is claimed for it. The shared engine is therefore
adopted for the heap, and the benchmark fails if the saving falls below the bar.

## Security reasoning

A shared engine shares **compiled code and caches**, not the guest heap. Each context keeps its own guest
heap, statics, classpath and options, so FR-CTX-001/003 hold: `SharedEngineIsolationTest` shows the statics
of two sibling contexts on one engine stay apart. The Espresso-owned rows of `game-host-internals.md` §4
also hold with a sibling on the same engine: a guest `System.exit` ends only its own context (FR-CTX-006),
and a runaway handler is interrupted and force-closed while the sibling keeps its state and keeps answering
(FR-CTX-008). The container-owned rows (filesystem, network, memory; §4.3) are untouched: the engine is not
an isolation boundary today and does not become one.

## Observed on the way (none of it caused by sharing; all of it measured the same with an engine per context)

1. **A JVM can create only twelve Espresso contexts in its lifetime.** The thirteenth fails with
   `EspressoError: Cannot load library: eden`, whether the earlier ones were closed with `close()` or
   `close(true)` and with or without a shared engine (a loop creating and closing one context at a time
   failed at the 13th in both modes). The cause is not established; it matches Espresso's isolated native
   namespaces, which `GameHostWarmupTest` already calls "finite per JVM". Every context creation counts,
   including the re-creation of a context that idle eviction (§6.3) closed. This is recorded as `OQ-6` in
   `game-host-internals.md` §18 for the owner; this ADR does not decide it (`IMP-M20-18` did: the host counts creations and retires at the limit). The test build now forks one JVM
   per test class (`reuseForks=false` on Surefire) because the Espresso tests together spend more than twelve.
2. **`allowEnvironmentAccess(EnvironmentAccess.NONE)` does not hide the host environment.** A guest
   `System.getenv("PATH")` returns the host's value with the factory's options. It is the same cause as the
   filesystem and network leaks (native access), so it is the container's to contain, and anything in the
   Game Host pod's environment is readable by game code. Added to the §4.3 table.
3. **All contexts on one engine must use the same host-access configuration** (`IllegalStateException:
   Found different host access configuration for a context with a shared engine`). The factory already
   gives every context `HostAccess.NONE`.
4. **No per-context resource limit is usable.** `sandbox.MaxHeapMemory` is unavailable on CE (spike). A
   `ResourceLimits` statement limit on an Espresso context did not return within 150 s in a probe (not
   investigated further, not committed), so `Context.interrupt` / `close(true)` stays the only per-context
   stop, as §4 says.

## Consequences

- Positive: about a third less heap for four contexts; the warm-up now warms the code real contexts run.
- Negative: contexts share an engine's caches, so a crash that corrupts the engine (as opposed to one
  context) takes every context with it; the pod restarts either way, and sessions recover from Redis (§9.3).
- The engine is closed after the context manager at shutdown (bean dependency order).
