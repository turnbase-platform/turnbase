# ADR-0018: Starting a game survives a cold, restarting or wedged Game Host, and says what it is doing

- **Status:** Accepted
- **Date:** 2026-10-17
- **Deciders:** Project owner
- **Amends:** `../specs/flows/02-room-to-game-start.md` §E (steps 7 and 9), `../specs/api-design/room-websocket.md`
  (`START_GAME` failure reasons, a new side topic), `../specs/game-host/game-host-internals.md` §11
- **Relates to:** [ADR-0006](0006-game-trust-model-java-official-only.md), [ADR-0012](0012-repo-strategy-polyrepo-submodules.md)
- **Executed by:** milestone **M14** in [`registry.md`](../implementation/registry.md) (`IMP-M14-01…03`)

## Context

On a freshly set-up stack, pressing *Start* in a ready lobby failed with "The game could not be
started" and went on failing until the Game Host was restarted by hand. The message named no cause and
offered no way out. Four independent defects produced it:

1. **A wedged guest boot.** Between one cold boot in ten and one in five (measured: 5 of 23 restarts) of the Game Host deadlocks inside Truffle's
   native interface: its `nfi-gc` thread and the guest boot thread's `dlsym` contend for the glibc 2.34
   loader lock. What follows is a **whole-JVM stall**: the VM Thread waits for a safepoint that never
   arrives, so no Java thread runs, `jcmd` cannot attach, SIGTERM and SIGQUIT are ignored and
   `/actuator/health` does not answer. The process is alive, so nothing restarts it, and Docker
   marks the container unhealthy but does not act on that. Until its lease (15 s) lapses the host is
   still registered, and every `CreateSession` runs to the 35 s `dispatchDeadline`. Neither the OTel agent, GC tuning nor quiescing the NFI thread changes the rate; this is
   a runtime defect we mitigate, not one we can remove.
2. **A stale pooled channel.** After a host restart the first `CreateSession` on the pooled gRPC
   channel failed `UNAVAILABLE` and was reported as a final failure. `CreateSession` is idempotent per
   session id, so one retry is safe.
3. **No waiting.** A start issued before the host had registered failed `NO_HOST_AVAILABLE` at once,
   though registration is seconds away on a cold stack.
4. **No feedback.** The client showed a static button for up to 35 s, then a generic error.

## Decision

1. **The platform waits, retries, and sets a bad host aside.** `GameSessionService.create` makes
   at most three attempts. With no eligible host it polls for `turnbase.orchestration.host-wait`
   (default 40 s) before each — a quarantined host is typically about to be restarted by the
   supervisor, and its replacement registers under a new instance id. `UNAVAILABLE` retries on a fresh channel. `DEADLINE_EXCEEDED`
   **quarantines** the host in Redis for `quarantine-ttl` (default 60 s) — `selectHost` skips it — and
   retries elsewhere; a lease alone cannot express "alive but useless". Any other gRPC failure, and an
   `onInit` failure, is `SESSION_CREATION_FAILED` and is **not** retried: the game, not the host, is
   at fault.
2. **A process outside the JVM kills a wedged Game Host.** The image's entrypoint is
   `docker/supervise.sh`, which runs the JVM as a child and probes `/actuator/health` on the management
   port. After a 45 s start-up grace, four consecutive silent probes (any HTTP answer counts, a 503
   included) SIGKILL the JVM and exit non-zero; the restart policy (`restart: unless-stopped` under
   Compose, the pod's under Kubernetes) boots a fresh one. It has to be a separate process because
   nothing inside a stalled JVM runs — this was found the hard way: an in-JVM watchdog logged the
   wedge and then never reached its own `halt`. That in-JVM `BootWatchdog` is kept for the case where
   only the guest thread is stuck: it guards every guest boot with `turnbase.gamehost.boot-timeout`
   (20 s), and on expiry `HostWedge` marks health DOWN, deregisters, halts with exit code 70 and
   SIGKILLs itself as a fallback. It is best-effort; the supervisor is the guarantee.
3. **Failures name their cause.** `START_GAME` failures carry `reason` ∈ `NO_HOST_AVAILABLE`,
   `HOST_UNRESPONSIVE`, `SESSION_CREATION_FAILED`, each with a message that says what to do ("try
   again in a minute"). The exception's own message is still never forwarded (unchanged).
4. **Start progress is a broadcast, not a reply.** While a start runs, the platform publishes
   `GAME_START_STATUS {phase, reason?}` on a new topic `/topic/room.{roomId}.start`, with phases
   `STARTING`, `WAITING_FOR_HOST`, `LOADING_GAME`, `RETRYING`, `FAILED`. Every lobby participant —
   players and spectators — sees a spinner and a sentence; it is not only the host's.
   The topic is **ephemeral and unversioned**: it is not replayed, and a client that attaches
   mid-start simply shows nothing until the next phase or `GAME_STARTED`. Subscription is
   allowed to any current participant of the room; anyone else is silently dropped.

## Alternatives rejected

- **Raise `dispatchDeadline`.** Makes a wedge a longer hang.
- **Put progress on `/topic/room.{id}`.** That topic is versioned and replayed from the room
  snapshot; a transient phase there would be replayed stale after the start finished.
- **Fix the deadlock.** It sits in GraalVM's NFI on glibc 2.34; no upstream fix is available to pin.
  Revisit on each GraalVM bump and delete the watchdog if it is gone.
- **Make the client poll `/health`.** Polling is excluded by the project's constraints.

## Consequences

- A wedge costs the supervisor's detection (about 20 s after its grace) plus a restart (about 15 s)
  instead of a permanent outage; a player who starts during it waits, with feedback, and normally
  succeeds on the retry. The wedge is common enough here (about one start in four) that two attempts left roughly one start in eleven failing; the third attempt is the measured answer. Worst case for a start is about 3 × 35 s of timeouts plus the waits between them before it gives up.
- Every Game Host image now runs a shell wrapper as PID 1; `docker stop` still reaches the JVM because
  the wrapper forwards SIGTERM.
- Two new orchestration properties and one game-host property; all have defaults and none changes the
  proto.
- `FAILED` is published before the unicast `GAME_START_FAILED` error, so the lobby's spinner always
  resolves for everyone.
