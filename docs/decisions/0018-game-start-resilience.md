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
   `docker/supervise.sh`, which runs the JVM as a child **in a loop** and probes
   `/actuator/health/liveness` on the management port with `curl -sf`, so only a 2xx is an answer (a
   503 is silent; the liveness group excludes Redis and Postgres, so a dependency outage never restarts
   the host). After a 45 s start-up grace per JVM, four consecutive silent probes SIGKILL the JVM
   (`kill` is a shell builtin; the image has no `kill` binary) and the loop starts a new one at once,
   so a wedge never reaches the kubelet's restart back-off. Only after 5 JVM deaths within 10 minutes
   does the script exit non-zero and leave the rest to the restart policy (`restart: unless-stopped`
   under Compose, the pod's under Kubernetes). A TERM or INT is passed to the JVM and the script exits
   with its status. The current JVM's pid is in `/tmp/jvm.pid` and every line the script prints
   carries an ISO-8601 UTC timestamp. It has to be a separate process because nothing inside a stalled
   JVM runs — this was found the hard way: an in-JVM watchdog logged the wedge and then never reached
   its own `halt`. That in-JVM `BootWatchdog` is kept for the case where only the guest thread is
   stuck: it guards every guest boot with `turnbase.gamehost.boot-timeout` (20 s), and on expiry
   `HostWedge` publishes `LivenessState.BROKEN`, writes the marker file `turnbase.gamehost.wedge-marker`
   (default `/tmp/turnbase-wedged`), deregisters and tries `Runtime.halt(70)` after 4 s. The supervisor
   checks the marker every second (grace or not), SIGKILLs the JVM at once and removes the file. The
   former `kill -9` fallback from inside the JVM is gone: it always failed, there being no `kill`
   binary. The in-JVM path is best-effort; the supervisor is the guarantee.
   *Amended 2026-10-19 (IMP-M16-03):* the start-up warm-up context made the wedge about ten times
   likelier (11 of 40 cold starts against 2 of 40), so it is off by default
   (`turnbase.gamehost.warmup-enabled`); `game-host-internals.md` §11 holds the measurement.
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

- A wedge costs the supervisor's detection plus a restart instead of a permanent outage. Measured in
  the cluster (IMP-M16-02, `kill -STOP` of the JVM, twice in a row on one pod): **17.2 s and 16.0 s**
  from the STOP to the new JVM's first log line, the pod's restart count 0. Before the respawn loop
  the same event took about 6 minutes (the kubelet's CrashLoopBackOff, load-testing finding 18); a player who starts during it waits, with feedback, and normally
  succeeds on the retry. The wedge is common enough here (about one start in four) that two attempts left roughly one start in eleven failing; the third attempt is the measured answer. Worst case for a start is about 3 × 35 s of timeouts plus the waits between them before it gives up.
- Every Game Host image now runs a shell wrapper as PID 1; `docker stop` still reaches the JVM because
  the wrapper forwards SIGTERM.
- Two new orchestration properties and one game-host property; all have defaults and none changes the
  proto.
- `FAILED` is published before the unicast `GAME_START_FAILED` error, so the lobby's spinner always
  resolves for everyone.
