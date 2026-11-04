# Archive — M14 Game start resilience

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim by `IMP-M20-01`. Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M14-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M14-01 | Game start waits, retries, quarantines and publishes progress | platform, docs | — | DONE |
| IMP-M14-02 | Game Host boot watchdog and restart supervision | game-host, platform | — | DONE |
| IMP-M14-03 | Game start progress in the lobby | frontend | M14-01 | DONE |

---

## M14 — Game start resilience

Opened 2026-10-17 by [ADR-0018](../../decisions/0018-game-start-resilience.md). On a freshly set-up stack
*Start* failed with "The game could not be started" until the Game Host was restarted by hand, and
the lobby showed nothing meanwhile. The corpus amendments (`room-websocket.md`, flow 02 §E,
`game-host-internals.md` §11, `local-environment.md`, `VW-RLOBBY-018`) landed with the ADR.

### IMP-M14-01 — Game start waits, retries, quarantines and publishes progress

**Repo:** `turnbase-platform`

**Done when:**
- `GameSessionService.create` makes at most three attempts, waits up to `host-wait` for a host on the
  first, retries `UNAVAILABLE` on a fresh channel, and quarantines a host that times out for
  `quarantine-ttl`; `selectHost` skips quarantined hosts. A unit test covers each branch.
- `START_GAME` failures carry `NO_HOST_AVAILABLE`, `HOST_UNRESPONSIVE` or `SESSION_CREATION_FAILED`
  with an actionable message.
- `GAME_START_STATUS` is published on `/topic/room.{id}.start` and the subscription is authorised for
  current participants only.

### IMP-M14-02 — Game Host boot watchdog and restart supervision

**Repo:** `turnbase-game-host`, `turnbase-platform` (Compose)

**Done when:**
- The image's entrypoint (`docker/supervise.sh`) SIGKILLs a JVM that stops answering its health
  probe, so a whole-JVM stall ends in a restart. Every guest boot also runs under `BootWatchdog`; on
  expiry the host reports DOWN, deregisters, halts with code 70 and SIGKILLs itself if that hangs.
  Unit tests cover the watchdog, the wedge sequence, the health indicator and Spring's choice of
  `HostWedge` constructor.
- The Compose `gamehost` service has `restart: unless-stopped`.
- Forty consecutive Game Host restarts, each followed by a full game on the driver, all pass.

### IMP-M14-03 — Game start progress in the lobby

**Repo:** `turnbase-frontend`

**Depends on:** IMP-M14-01

**Done when:**
- Every lobby participant, spectators included, sees a spinner and the phase's sentence from
  `GAME_START_STATUS`; the host's Start button is disabled while a start is running; a failure shows
  its reason and what to do; the display clears on `GAME_STARTED`.
