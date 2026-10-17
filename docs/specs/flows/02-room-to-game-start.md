# Flow 02 — Create a Room, Join, Ready Up, Start

Alice creates a room from the catalog, Bob joins, they are assigned to teams, Bob readies, Alice
starts. This is the flow that establishes room ownership, and it is the first one to reach the Game
Host.

**Components:** two browsers, Platform Monolith, PostgreSQL, Redis, Game Host.

---

## A. Create

| # | Actor | Action | Durable state |
|---|---|---|---|
| 1 | Alice | **Create Room** on `/games/:id` (`VW-GDET-003`) → `POST /api/rooms` `{gameId, visibility, spectatingEnabled}` | — |
| 2 | Monolith | Catalog preconditions ([catalog §1](../platform/data-model-catalog.md)): game not deleted or archived (`FR-GAME-013`); if unlisted, Alice is the owner (`FR-GAME-007`); if `UNVERIFIED`, Alice is the owner (`FR-PRV-002`) | — |
| 3 | Monolith | Reads `game.active_version_id` → `game_version.manifest`. **Pins the version now**: `room.game_version` is a text snapshot, not a live pointer, so an upload mid-lobby cannot change the game underneath the room (`FR-GAME-010/011`) | — |
| 4 | Monolith | One transaction: `INSERT INTO room (…, state='LOBBY', version=0, owner_epoch=0)`; instantiate `count.min` teams per template at `configuredSize = size.max` (`FR-TEAM-012`); `INSERT INTO room_participant` for Alice, `role='PLAYER'`, `join_order=0`; `room.host_user_id = alice` | **`room`, `room_team` ×N, `room_participant`** |
| 5 | Monolith | `201`, `Location: /api/rooms/{roomId}` | — |
| 6 | Alice's browser | Navigates to `/rooms/{roomId}`, opens the STOMP connection at `/ws` if not already open | — |

**Nothing is claimed yet.** Room creation writes Postgres and touches no Redis lease. Ownership is
established by the first *client attach*, not by creation — [ADR-0008](../../decisions/0008-room-ownership-lifecycle.md)
makes ownership a lease-gated claim, and a room created by a REST call that lands on an arbitrary
instance has no reason to be owned by that instance.

**Step 4 instantiates teams eagerly** rather than on first join. `FR-TEAM-012` settled this: a room
with no teams has no answer to "which team does the second player go to", and auto-assignment
(`FR-TEAM-005`) needs a deterministic tie-break that `(template_index, team_index)` provides.

---

## B. Alice attaches — the claim

| # | Actor | Action | Durable state |
|---|---|---|---|
| 1 | Alice | `SUBSCRIBE /topic/room.{roomId}` | — |
| 2 | Monolith | Channel-level guard: Alice is a member → allowed. A non-member is **silently dropped**, not errored (`room-websocket.md` authorization model) | — |
| 3 | Monolith | **Claim script** (Redis, atomic): if `room:{roomId}:pod` is unset or names a pod whose `pod:{podId}:alive` key is gone, set it to this pod and `INCR room:{roomId}:epoch` | **Redis: ownership key, epoch** |
| 4 | Monolith | Fenced write: `UPDATE room SET owner_instance_id=…, owner_epoch=:myEpoch, ownerless_since=NULL WHERE room_id=… AND owner_epoch < :myEpoch` | **`room` ownership columns** |
| 5 | Alice | `SEND /app/room.{roomId}.member` `{type:"REQUEST_ROOM_STATE"}` | — |
| 6 | Monolith | Unicast `ROOM_STATE` on `/user/queue/room-state`, carrying `version` | — |

**Step 4's guard is `owner_epoch < :myEpoch`, not equality.** A claimant that stalled between the
Redis claim and this write could otherwise stamp a *lower* epoch over a later tenure's, making every
one of the legitimate owner's fenced mutations match zero rows — it would self-evict and drop all its
clients while the stale adoption put its connected players into grace windows. The Redis script is
atomic, so no two tenures share an epoch; nothing orders their Postgres writes, so the write orders
itself.

**Step 3's claim script is also the failure detector.** There is no dead-instance watcher anywhere in
the platform. A room whose owner died stays unowned until someone tries to claim it — a returning
client here, or the reconciliation sweep ([flow 05](05-owner-loss-and-adoption.md)).

---

## C. Bob joins

| # | Actor | Action | Durable state |
|---|---|---|---|
| 1 | Bob | Opens an invite link `/rooms/join/{code}` (`FR-LINK-002`) or accepts an invitation notification (`FR-INV-004`) | — |
| 2 | Monolith | Resolves `room.invite_code`; checks state, capacity, visibility | — |
| 3 | Monolith | Both a player slot and a spectator slot free → `VW-JOIN-002` prompts for a role. Otherwise auto-selects | — |
| 4 | Monolith | Single-room rule (`FR-JOIN-007`): if Bob holds a slot elsewhere, prompt to abandon (`FR-JOIN-008`) | — |
| 5 | Monolith | Under the room lock: auto-assign to the team with fewest members, tie-broken by `(template_index, team_index)` (`FR-TEAM-005`); `INSERT INTO room_participant`; `room.version++` **committed** | **`room_participant`, `room.version`** |
| 6 | Monolith | Broadcast `PLAYER_JOINED` on `/topic/room.{roomId}` at the new `version` | — |
| 7 | Bob | Subscribes, `REQUEST_ROOM_STATE`, receives the snapshot | — |

**Step 5 commits the version before step 6 publishes it**, and that ordering is a fix, not a
convention. Clients discard `delta.version <= localVersion`. An instance that published first and
committed second — or an adopting instance working from a freshly-zeroed in-memory counter — would
re-issue versions clients have already applied, and they would drop them **silently**. That is
strictly worse than a gap, which is at least detected.

**If Bob's `SUBSCRIBE` lands on a different instance**, the affinity hint at the ingress is advisory
(`FR-DEPLOY-002`). The receiving instance runs the claim script, finds the lease held, and returns
`ROOM_UNAVAILABLE_RETRY` — the client retries and the ingress routes it correctly. In the
single-replica MVP this never fires; during a rolling deploy it does.

---

## D. Teams and readiness

| Command | Destination | Effect |
|---|---|---|
| `REASSIGN_PLAYER` | `/app/room.{roomId}.host` | Alice moves Bob → `PLAYER_REASSIGNED` |
| `ADD_TEAM` / `REMOVE_TEAM` / `RESIZE_TEAM` | host | Bounded by the manifest's `count` and `size` ranges |
| `ADD_AI_PLAYER` | host | Only if `capabilities.ai` (`FR-HOST-003`). AI players are always ready (`FR-READY-002`) |
| `CHANGE_PARAMETERS` | host | Keys **whitelisted** against the manifest's declared `parameters` |
| `TOGGLE_READY` | `/app/room.{roomId}.member` | Bob only — the host never sends this (`FR-READY-001`) |

Every one takes the room lock, bumps `version`, commits, then broadcasts. Every one is charged the
`command` bucket (2/s, burst 10) at the interceptor.

**`CHANGE_PARAMETERS` is a whitelist, not a size cap**, and the distinction matters. `manifest.json`
declares a typed parameter schema, so unknown keys are *rejected* rather than merely bounded — which
removes the amplification vector by construction. A cap would still let a host push 4 KB of
attacker-chosen data through the platform into every room member's client.

**The host has no readiness state.** `START_GAME` is their readiness (`FR-READY-001`), which is why
`VW-RLOBBY-003` hides the toggle from them and why `room_participant.ready` is simply never set for
the host.

---

## E. `START_GAME`

| # | Actor | Action | Durable state |
|---|---|---|---|
| 1 | Alice | `SEND /app/room.{roomId}.host` `{type:"START_GAME"}` | — |
| 2 | Monolith | Channel guard `principal.id == room.hostId` — a **fast-fail only** | — |
| 3 | Monolith | Under the room lock, **re-validate host identity** and every `FR-TEAM-009` condition | — |
| 4 | Monolith | Any condition fails → `START_CONDITIONS_NOT_MET` listing them, unicast. Stop | — |
| 5 | Monolith | Materialize parameter defaults from the manifest for keys the host never set — the Game Host receives a complete set, never a partial one | — |
| 6 | Monolith | Allocate `sessionId`; write the **Orchestration-owned** Redis keys — `routing:`, `queue:`, `seq:`, `delivered:`, `failcount:`. **Not** `session:{sessionId}` — that record is the Game Host's (`../game-host/game-host-internals.md` §13) and pre-writing it would satisfy `CreateSession`'s idempotency guard on the very first call, so `onInit` would never run | **Redis routing keys** |
| 7 | Monolith | gRPC `CreateSession(sessionId, gameId, version, roster, teams, parameters)` → Game Host | — |
| 8 | Game Host | Selects or creates an Espresso context for `(gameId, version)`; loads the bundle from the artifact store; invokes `onInit` at **sequence 0** | Game Host in-memory + Redis |
| 9 | Monolith | On OK: under the room lock, `room.state='IN_PROGRESS'`, `room.active_session_id=sessionId`, `version++`, commit | **`room`** |
| 10 | Monolith | Broadcast `GAME_STARTED {sessionId, gameFrontendUrl}` on `/topic/room.{roomId}` | — |
| 11 | Both clients | Load the iframe from `gameFrontendUrl`, subscribe to the game destinations, then `REQUEST_GAME_SYNC` — see [flow 03](03-game-turn.md) | — |

**Steps 6–9 are resilient to a cold or restarting Game Host, and visible
([ADR-0018](../../decisions/0018-game-start-resilience.md)).** Orchestration makes at most three
`CreateSession` attempts. If no host is eligible it first polls for `turnbase.orchestration.host-wait`
(40 s, before each attempt). `UNAVAILABLE` — a stale pooled channel after a host restart — retries on a
fresh channel. `DEADLINE_EXCEEDED` quarantines that host for `quarantine-ttl` (60 s) and retries on
another; three timeouts end as `HOST_UNRESPONSIVE`. Any other failure is `SESSION_CREATION_FAILED` and is
not retried. Throughout, the Monolith publishes `GAME_START_STATUS` (`STARTING`, `WAITING_FOR_HOST`,
`LOADING_GAME`, `RETRYING`, then `FAILED` with its reason) on `/topic/room.{roomId}.start`, which every
participant receives; the sequence ends with `GAME_STARTED` (step 10) or with `FAILED` and the unicast
`GAME_START_FAILED`. The retry is safe because `CreateSession` is idempotent per `sessionId`.

**Step 3 re-validates under the lock because host identity is mutable runtime state.** The
channel-level check reads a `Principal` bound at connect time; `TRANSFER_HOST` can have landed since.
The same two-level pattern appears throughout the protocol — cheap guard at the interceptor,
authoritative check in the handler under the lock.

**Step 5 is where a whole class of game bug is removed.** Every manifest parameter declares a
`default`, so Orchestration materializes the complete set and the GDK's `GameParameters` accessors
never return absent. A game that only ever sees complete parameters cannot have a
missing-parameter code path to get wrong.

**Step 10's `gameFrontendUrl` is absolute and server-composed.** The client never assembles it and
never derives the game origin from a build-time constant: the shell's trusted postMessage origin is
exactly `new URL(gameFrontendUrl).origin`, and the whole isolation argument of
[ADR-0007](../../decisions/0007-game-frontend-separate-domain.md) rests on that origin being the one
the server chose.

**`onInit`'s effects are fanned out to nobody**, and this is expected rather than a bug. At sequence
0 every player is still navigating from lobby to game view with an unloaded iframe. `FR-FE-001` was
amended to stop promising initial state via `send_to_player`; establishing a player's view is
`onResync`'s job, and the resync is the first `game_event` any freshly loaded game FE receives —
at start, on reconnect, and on late join alike.

---

## What is durable at each point

| After | Survives a crash | Does not |
|---|---|---|
| Create (A) | Room, teams, host, Alice's participant row | Nothing — no lease exists yet |
| Attach (B) | Ownership mirror in `room` | The Redis lease itself, which is the point: it expires and the room becomes claimable |
| Join (C) | Bob's row, the bumped `version` | Bob's socket |
| Start (E9) | `state='IN_PROGRESS'`, `active_session_id` | Game state, which lives in Redis with an accepted loss window (ADR-0001) |

The row that matters most is `room.active_session_id`. It is the durable fact that a session belongs
to this room, and three separate mechanisms read it: the game-input outbox's `NOT_FOUND` rule, the
detach idempotency check, and reconciliation's In-Progress-without-a-session duty.

---

## Defects surfaced

None new. This flow crosses ground the previous session already repaired — the commit-before-publish
ordering, the `owner_epoch < :myEpoch` guard, and the epoch's existence as a fence distinct from the
room version were all fixes from that pass, and walking the flow confirms they compose.

Two things worth recording as *not* defects, because both look like one:

- **Room creation claims nothing.** Deliberate: adopting a room with no clients attached computes
  nothing in a turn-based game, so eager claiming is cost with no benefit (ADR-0008).
- **A room can be In Progress with no owner.** Also deliberate. Deadlines are persisted absolute
  timestamps ([ADR-0009](../../decisions/0009-grace-deadline-durability.md)), so an unowned room's
  deadlines are still enforceable — by whichever instance adopts it, bounded by `NFR-JOB-002` at 90
  seconds.
