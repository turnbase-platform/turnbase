# Rooms, room lifecycle and the realtime protocol — implementation-readiness audit

**Agent:** Opus · **Files reviewed:** 15 in full, 9 sampled · **Date:** 2026-08-16

## Coverage

**Read in full:**

- `docs/specs/platform/room-lifecycle.md` (676 lines)
- `docs/specs/api-design/room-websocket.md` (736 lines)
- `docs/specs/api-design/websocket.md` (508 lines)
- `docs/specs/api-design/room-chat-websocket.md`
- `docs/specs/platform/data-model.md`
- `docs/decisions/0002-websocket-room-affinity.md`, `0008-room-ownership-lifecycle.md`,
  `0009-grace-deadline-durability.md`, `0010-session-teardown-ordering.md`
- `docs/requirements/game-rooms.md`, `reconnection-flow.md`, `in-room-chat.md`
- `docs/specs/flows/02-room-to-game-start.md`, `04-disconnect-and-return.md`,
  `05-owner-loss-and-adoption.md`, `07-room-closure.md`

**Sampled (targeted reads / greps, cited where used):** `docs/specs/flows/06-game-end-and-rematch.md`
(§C–§F), `docs/requirements/platform-operations.md` (FR-JOB-005…008, FR-DEPLOY-001…003, NFR-JOB-001/002,
FR-MET-005), `docs/specs/deployment/local-environment.md` (§7.2 config surface, §5 drain),
`docs/specs/api-design/rate-limiting.md` (Tier 6 buckets), `docs/specs/platform/data-model-accounts.md`
(§ erasure scatter), `docs/requirements/platform-views.md` (VW-ROOMS-005),
`docs/specs/api-design/rest-conventions.md`, `docs/specs/api-design/pagination-filtering-sorting.md`.

**Could NOT check:**

- `docs/specs/flows/03-game-turn.md` and `game-host/game-host-internals.md` — the game-execution half of
  the reconnect path (`Resync`, `lastAppliedSequence`, the delivery watermark). I traced the *client-facing*
  contract in `websocket.md` and took the Game Host side on its word. Scenario 6's game-stream half is
  therefore **UNVERIFIED** below the `REQUEST_GAME_SYNC` seam.
- `platform-architecture.md` FR-FAIL-003/005/006 and `notifications-invitations.md` FR-INV-008/009 —
  referenced by my documents, read only through the quotes those documents carry.
- Whether the *frontend* client spec exists for the pinned card / rejoin entry points. I checked
  `platform-views.md` for VW-ROOMS-005 only.

**Deliberately not re-reported (per brief):** room-lifecycle OQ-001/002/003, websocket.md OQ-001/002.

---

## Summary

| # | Severity | One-line | Location |
|---|---|---|---|
| 1 | BLOCKER | Grace expiry in a **Lobby** room inserts a `player_left` outbox row with no `session_id` — `NOT NULL` violation aborts the expiry forever | `docs/specs/platform/room-lifecycle.md:396-418`, `docs/specs/platform/data-model.md:315` |
| 2 | BLOCKER | Graceful drain / self-eviction closes client sockets, which fires the ordinary disconnect handler — the exact FR-DC-007 cascade the carve-out exists to prevent | `docs/specs/platform/room-lifecycle.md:236-240`, `:170-174`, `docs/specs/flows/04-disconnect-and-return.md:16-18` |
| 3 | BLOCKER | Chat consumes the room `version` but is delivered to a *subset* of `/topic/room.{roomId}` subscribers — permanent gap-detect storm for spectators and off-team players | `docs/specs/api-design/room-chat-websocket.md:29-31`, `docs/specs/api-design/room-websocket.md:726` |
| 4 | BLOCKER | Deadline-sweep duty 2's predicate matches **every** released participant, so voluntary leaves, kicks and closures each draw a phantom `PLAYER_LOST` + closure evaluation | `docs/specs/platform/room-lifecycle.md:557-560`, `docs/specs/platform/data-model.md:218-224` |
| 5 | BLOCKER | `detachSession`'s transaction mutates the `room` row with **no version bump and no epoch fence**, contradicting §1.5's "every mutation of the `room` row" | `docs/specs/platform/room-lifecycle.md:477-492`, `:176-194` |
| 6 | BLOCKER | "Record the closure as owed" names no table, column or sweep duty — and `data-model-accounts.md` says the same closure is **synchronous** | `docs/specs/platform/room-lifecycle.md:468`, `:475-476`, `docs/specs/platform/data-model-accounts.md:395,422` |
| 7 | BLOCKER | AI players are load-bearing in the wire protocol and in the closure predicate, and have **no representation in the schema** | `docs/specs/api-design/room-websocket.md:151-158,566`, `docs/specs/platform/room-lifecycle.md:403-405`, `docs/specs/platform/data-model.md:158-178` |
| 8 | BLOCKER | No REST specification exists for the room API — the entry point for every join/create/rejoin scenario | `docs/specs/api-design/INDEX.md`, `docs/specs/flows/02-room-to-game-start.md:15-19` |
| 9 | AMBIGUITY | `detachSession` step 4 inserts a `session_teardown` row unconditionally; the two most common closures have **no session** | `docs/specs/platform/room-lifecycle.md:484-485`, `docs/specs/platform/data-model.md:137` |
| 10 | AMBIGUITY | Room client has no rule for deltas received between `SUBSCRIBE` and the first `ROOM_STATE` — the literal table produces a snapshot-request storm | `docs/specs/api-design/room-websocket.md:723-727`, cf. `docs/specs/api-design/websocket.md:441` |
| 11 | AMBIGUITY | Reconciliation guards: `room-lifecycle.md` exempts the owed-teardown duty from both FR-JOB-008 guards; `platform-operations.md` exempts only the adoption duty | `docs/specs/platform/room-lifecycle.md:615-638`, `docs/requirements/platform-operations.md:151` |
| 12 | GAP | FR-EXPIRY-006 (game end resolves outstanding reservations) has no statement anywhere; flow 06 omits it from the game-end detach entirely | `docs/requirements/reconnection-flow.md:88`, `docs/specs/flows/06-game-end-and-rematch.md:88-90` |
| 13 | GAP | Lobby immediate-leave (FR-DC-002) has no algorithm in `room-lifecycle.md` — §3.1 is scoped to `IN_PROGRESS` only | `docs/specs/platform/room-lifecycle.md:333-354`, `docs/specs/flows/04-disconnect-and-return.md:30-33` |
| 14 | GAP | "Evict spectators" and the definition of "member" for the subscribe guard are both unspecified | `docs/specs/platform/room-lifecycle.md:491`, `docs/specs/api-design/room-websocket.md:587` |
| 15 | GAP | Deadline-sweep duty 2 has no supporting index; the only participant index is partial on the **opposite** predicate | `docs/specs/platform/data-model.md:180-182`, `docs/specs/platform/room-lifecycle.md:557` |
| 16 | GAP | `ROOM_STATE.spectatorCapacity` has no home — not a column, not a config key | `docs/specs/api-design/room-websocket.md:138`, `docs/requirements/game-rooms.md:163` |
| 17 | DRIFT | `room-lifecycle.md` §4 — the document that owns `detachSession` — is missing flow 07's step 3b (delete `room_invitation`) | `docs/specs/platform/room-lifecycle.md:483-486`, `docs/specs/flows/07-room-closure.md:43` |
| 18 | DRIFT | Flow 02 §B's adoption `UPDATE` omits `migration_window_expires_at`; flow 05 §C includes it; §1.4 step 7 arms it on **every** adoption including room creation | `docs/specs/flows/02-room-to-game-start.md:40`, `docs/specs/flows/05-owner-loss-and-adoption.md:67`, `docs/specs/platform/room-lifecycle.md:148-152` |
| 19 | DRIFT | Adoption (§1.4) is never reconciled with room creation: step 1 loads a `room` row that may not exist yet | `docs/specs/platform/room-lifecycle.md:127`, `docs/specs/flows/02-room-to-game-start.md:22` |
| 20 | GAP | §3.1's "after commit: bump the version, broadcast" is a second transaction with no recovery if the process dies between | `docs/specs/platform/room-lifecycle.md:352-354` |
| 21 | NIT | §1.4 step 7 hard-codes `now() + 20s` where the value is a config key | `docs/specs/platform/room-lifecycle.md:149` |

---

## Findings

### F1 — BLOCKER — Grace expiry in a Lobby room cannot commit: `game_input_outbox.session_id` is `NOT NULL`

**Where:** `docs/specs/platform/room-lifecycle.md:394-418`, `docs/specs/platform/data-model.md:313-316`,
`docs/specs/platform/room-lifecycle.md:143-147`

**Quotes:**

> "In the transaction:
>  1. The `UPDATE` above.
>  2. Insert the `player_left` row into `game_input_outbox`." (room-lifecycle.md:396-398)

> "4. Evaluate closure — **only if the room is `IN_PROGRESS`**." (room-lifecycle.md:402)

> "**A `LOBBY` room is deliberately exempt from step 4, and the exemption is load-bearing.** Reservations
> normally exist only in `IN_PROGRESS` rooms (§3.1, FR-DC-002), but §1.4 step 4 opens them in *any*
> state … **Those Lobby reservations do expire**" (room-lifecycle.md:409-414)

> "`session_id    uuid        NOT NULL,`" (data-model.md:315)

> "4. For every participant with `connection_count > 0` and **no** reservation already outstanding, open
> a grace period at `now() + graceSeconds`" (room-lifecycle.md:143-144) — §1.4, adoption, unconditioned on
> room state.

**Blocks:** the `GraceExpiryService` / deadline-sweep duty 1 transaction, and the Flyway migration for
`game_input_outbox`.

**Scenario:** Single-replica MVP, local stack restart (the path ADR-0008 says "actually runs").

1. Room R is in `LOBBY` with three participants connected. `room.active_session_id IS NULL`.
2. The owning instance is SIGKILLed. Instance B adopts R. §1.4 step 4 opens a 60s reservation for all
   three (this is mandatory — FR-DC-007 forbids treating the loss as a leave in *any* state).
3. Nobody returns. 60s later, deadline-sweep duty 1 selects the three rows.
4. §3.2's `UPDATE` runs, rowcount 1. §3.3 step 2 then inserts a `player_left` row into
   `game_input_outbox` — but there is no `sessionId`. The column is `NOT NULL`, so the insert throws and
   **the whole transaction rolls back**, including the `UPDATE`.
5. The reservation is never resolved. `grace_expires_at` stays in the past, so the row re-selects on
   every 5-second tick and fails identically, forever, at ERROR level, for the life of the room.
6. §3.4 excludes it from `disconnectedPlayers` (`grace_expires_at > now()` is false), and it is not
   connected — so those three players render as "present but unavailable" permanently, and the room is
   never collected by the idle-Lobby duty either, because it will never satisfy the connection predicate
   in a way anyone re-evaluates. The stuck-room class ADR-0009 was written to remove, reintroduced on the
   most-travelled path.

The alternative reading — "skip the insert when there is no session" — is correct but is nowhere written,
and the surrounding paragraph goes out of its way to carve out step 4 *and only step 4* for the Lobby case,
which reads as deliberate confirmation that steps 1–3 apply unchanged.

Related and unresolved even under the charitable reading: §3.3 step 3 broadcasts `PLAYER_LOST` with
`reason: GRACE_PERIOD_EXPIRED` and `leave_reason = 'GRACE_EXPIRED'` for a player who was never in a game.
`PLAYER_LEFT` and `leave_reason = 'LEFT'` are the plausible alternative and nothing chooses.

**Suggested resolution:** `room-lifecycle.md` §3.3 should state the Lobby branch explicitly and completely:
skip step 2 when `room.active_session_id IS NULL`, skip step 4, and name the event and `leave_reason` the
Lobby branch emits. The condition belongs on `active_session_id`, not on `state`, so it also covers the
narrow window in which a room has transitioned but the session is already detached.

---

### F2 — BLOCKER — Graceful drain closes its own clients' sockets, and nothing suppresses the disconnect handler

**Where:** `docs/specs/platform/room-lifecycle.md:231-241` (§1.6), `:168-174` (§1.5 layer 3),
`docs/specs/flows/04-disconnect-and-return.md:13-19`, `docs/requirements/reconnection-flow.md:48` (FR-DC-007)

**Quotes:**

> "4. Send `RECONNECT_REQUIRED` to attached clients as a STOMP `ERROR` frame — **which closes the
> connection** … 5. Release each owned room (§1.3); delete `pod:{podId}:alive`." (room-lifecycle.md:236-240)

> "a **nil reply proves the lease lapsed** and is unconditionally fatal — drop every owned room, **close
> those sockets with `RECONNECT_REQUIRED`**, drop in-memory state" (room-lifecycle.md:170-172)

> "| 2 | Monolith | STOMP session closes; `SessionDisconnectEvent` fires |
>  | 3 | Monolith | Under the room lock: `room_participant.connection_count--` for Bob |
>  | 5 | Monolith | Reached 0, room is `IN_PROGRESS` … → open a reservation" (flow 04:15-18)

> "A disconnect caused by owner-pod loss (FR-DC-006) is **never** treated as an immediate leave, in any
> room state. Without this carve-out, a rolling deploy would make every player of every Lobby room
> 'leave', which makes the host's departure trigger room closure … deleting every Lobby room on the
> platform on every deploy." (reconnection-flow.md:48)

**Blocks:** the `SessionDisconnectEvent` `@EventListener`, and the `SmartLifecycle` / `@PreDestroy` drain
bean. These are two different classes written by two different people, and the coupling between them is
not written down anywhere.

**Scenario:** Rolling deploy. Instance A owns 200 Lobby rooms.

1. A enters drain. Step 4 sends `RECONNECT_REQUIRED` and closes every socket.
2. Each close fires `SessionDisconnectEvent` **on instance A, while A still owns the room and still holds
   its epoch**. The handler of flow 04 §A runs: `connection_count--` → 0 → room is `LOBBY` → FR-DC-002
   immediate leave → `PLAYER_LEFT`, `left_at = now()`.
3. The host is among them. FR-XFER-002 fires: host left, no other human player remains (they all just
   "left" too) → **the room closes**, `closed_reason = 'NO_PLAYERS_REMAINING'`.
4. All 200 Lobby rooms are permanently destroyed by a routine deploy. This is verbatim the outcome
   FR-DC-007 was written to prevent; the carve-out exists in the requirement and has no mechanism on the
   drain path.
5. For `IN_PROGRESS` rooms the same handler opens a grace reservation for every player, directly
   contradicting three documents that assert the opposite: room-lifecycle.md:244-245 ("the whole event is
   normally absorbed inside the migration window with **no grace periods opened at all**"),
   ADR-0009:100 and flow 05:193.

The crash path is safe by accident (the process is gone, so no handler runs), which is exactly why this is
easy to miss — the flow-04 trace and the flow-05 trace each look correct in isolation.

§1.5 layer 3 (self-eviction) has the identical shape and the identical hole.

**Suggested resolution:** `room-lifecycle.md` §1.6 and §1.5 layer 3 must state that the instance enters a
mode in which `SessionDisconnectEvent` performs **no** participant mutation for rooms it is releasing —
neither `connection_count--`, nor reservation opening, nor immediate leave — and that the durable
consequence of the drain is exactly the `connection_count` zeroing performed by the *next* owner's §1.4
step 5. That also keeps FR-DC-006's "grace deadlines are established when the loss is *observed* — at
adoption" true, which the current drain sequence violates.

---

### F3 — BLOCKER — Chat consumes the room version but is not delivered to every room-topic subscriber

**Where:** `docs/specs/api-design/room-chat-websocket.md:27-31`,
`docs/specs/api-design/room-websocket.md:80`, `:119`, `:723-727`,
`docs/specs/api-design/rate-limiting.md:161`

**Quotes:**

> "The `version` counter is **shared with the room lobby event stream** — each `CHAT_MESSAGE` event
> increments the same per-room version sequence as lobby events. This means a client receiving chat events
> and lobby events on `/topic/room.{roomId}.*` can apply them in a single monotonic version sequence for
> gap detection" (room-chat-websocket.md:29-31)

> "| `/topic/room.{roomId}.chat` | server→client | Room players **only (not spectators)** |"
> (room-websocket.md:56)

> "Spectators receive all events on this topic. Chat events are on separate topics … and **are not
> received by spectators**." (room-websocket.md:119)

> "| `delta.version > localVersion + 1` | Gap detected — send `REQUEST_ROOM_STATE`; **discard deltas until
> new snapshot arrives** |" (room-websocket.md:726)

> "| `snapshot` | `REQUEST_GAME_SYNC` …, `REQUEST_ROOM_STATE` … | **1 per 3 s** | 2 |"
> (rate-limiting.md:161)

**Blocks:** the `ChatMessageHandler`, the room version allocator, and the frontend room reducer.

**Scenario:** A room with one spectator and two teams.

1. Spectator holds `localVersion = 42`. It is subscribed to `/topic/room.{roomId}` only — the
   `SubscriptionInterceptor` rejects it on `.chat` by design.
2. A player sends a chat message. Version 43 is consumed; `CHAT_MESSAGE` goes to `.chat`. The spectator
   receives nothing.
3. Someone toggles ready. `READINESS_CHANGED` at version 44 arrives on the room topic.
4. Spectator: `44 > 42 + 1` → gap → `REQUEST_ROOM_STATE`, and **discards all deltas** until the snapshot
   lands.
5. Chat is permitted at 1/s with burst 5 per player. `REQUEST_ROOM_STATE` is permitted at 1 per 3s with
   burst 2. The spectator exhausts its snapshot bucket in two requests, receives `RATE_LIMIT_EXCEEDED`,
   and — per its own reconciliation rule — is now discarding every delta with no path back to a snapshot.
   Its view of the room is frozen for as long as anyone is chatting.
6. The same happens to every player with respect to the *other* team's `/topic/room.{roomId}.team.{teamId}`
   messages, and to any player not yet assigned to a team.

Two further consequences of the shared counter that no document addresses: an ephemeral chat message would
have to perform the fenced `UPDATE room SET version = …` of room-lifecycle.md §1.5 (a Postgres write per
chat line, on a surface explicitly designed to persist nothing, FR-MSG-005); and `data-model.md:74`
describes `room.version` as "the per-room event version carried by every WebSocket delta" without listing
chat among its producers.

**Suggested resolution:** `room-chat-websocket.md` should own the fix and take chat **out** of the room
version sequence entirely — chat already carries `messageId` for dedup and `serverTimestamp` for ordering
(room-chat-websocket.md:57,63), and FR-MSG-006's fire-and-forget delivery gives gap detection nothing to
repair. `room-websocket.md:80`'s "incremented exactly once per state-mutating event" is already the correct
rule; chat is not a state mutation.

---

### F4 — BLOCKER — Deferred-tail sweep fires a phantom `PLAYER_LOST` for every voluntary leave, kick and closure

**Where:** `docs/specs/platform/room-lifecycle.md:557-560` (§5.1 duty 2),
`docs/specs/platform/data-model.md:218-224`, `:172-175`

**Quotes:**

> "2. **Deferred tails** — resolutions committed by a foreign instance
> (`left_at IS NOT NULL AND lost_announced_at IS NULL`, §3.3): bump version → broadcast `PLAYER_LOST` →
> set `lost_announced_at` → **evaluate closure**." (room-lifecycle.md:557-560)

> "**`lost_announced_at`** exists for **one case**: a player holding a reservation joins another room, and
> the instance handling that join is not the one that owns the old room." (data-model.md:218-219)

> "`leave_reason  text  NULL,  -- LEFT | KICKED | GRACE_EXPIRED | EARLY_RELEASE | ROOM_CLOSED | GAME_ENDED`"
> (data-model.md:173-174)

**Blocks:** deadline-sweep duty 2's query, and every handler that sets `left_at` (voluntary leave, kick,
game-end reservation resolution, closure slot release).

**Writer/deleter trace (the pattern the brief flagged):**

- **Writers of `lost_announced_at`:** §3.3 step 3 (the local winner of a grace expiry) and §5.1 duty 2.
  That is the complete set — grep confirms no other producer in the corpus.
- **Deleters:** none. The column is only ever set.
- **Writers of `left_at` that do *not* set `lost_announced_at`:** FR-DC-005 voluntary leave
  (`leave_reason = 'LEFT'`), FR-KICK-001/002/003 (`'KICKED'`), FR-EXPIRY-006 game-end resolution
  (`'GAME_ENDED'`), and `detachSession` step 3's "release slots" (`'ROOM_CLOSED'`).

The predicate therefore selects a strictly larger set than the intent, and nothing narrows it.

**Scenario:**

1. Alice clicks **Leave Room** in an `IN_PROGRESS` room. The owning instance sets
   `left_at = now(), leave_reason = 'LEFT'`, bumps the version, broadcasts `PLAYER_LEFT` (FR-DC-005,
   room-websocket.md:226). `lost_announced_at` stays `NULL`.
2. Within 5 seconds the deadline sweep's duty 2 selects her row on the *same* instance —
   `left_at IS NOT NULL AND lost_announced_at IS NULL` matches — bumps the version again and broadcasts
   `PLAYER_LOST { playerId: alice, reason: "GRACE_PERIOD_EXPIRED" }`.
3. Every client renders "Alice's grace period expired" five seconds after rendering "Alice left". No
   `player_left` outbox row accompanies it (steps 1–2 of §3.3 are not repeated), so the platform and the
   game backend now disagree about *why* she is gone.
4. Duty 2 then **evaluates closure** on a room the owner already evaluated. Two closure evaluations racing
   on the same room is exactly the state §4 step 2's idempotency check exists to absorb — but the second
   evaluation runs on a *different* trigger and may close a room the first deliberately left open.
5. The same fires once for every kicked player, and once for every participant released by
   `detachSession` step 3 in a room that has just closed — `PLAYER_LOST` broadcast into a `CLOSED` room.

**Suggested resolution:** `room-lifecycle.md` §5.1 duty 2 should own this. Narrow the predicate to the
resolutions §3.3 can actually defer — `leave_reason IN ('GRACE_EXPIRED', 'EARLY_RELEASE') AND
lost_announced_at IS NULL AND left_at IS NOT NULL` — and state normatively that **every** local path that
sets `left_at` also stamps `lost_announced_at` in the same statement, so the column means "announced or
not applicable" rather than "grace-expired and announced". `data-model.md`'s column comment should be
updated to match, since it currently describes a single narrow case that the predicate does not encode.

---

### F5 — BLOCKER — `detachSession` mutates the `room` row with no version bump and no epoch fence

**Where:** `docs/specs/platform/room-lifecycle.md:477-492` (§4), `:176-194` (§1.5 layer 4),
`docs/decisions/0008-room-ownership-lifecycle.md:51-54`, `docs/specs/api-design/room-websocket.md:308-316`

**Quotes:**

> "4. **Owner-epoch fence.** Every room mutation commits
> `UPDATE room SET version = :new, ... WHERE room_id = :id AND version = :expected AND owner_epoch = :myEpoch`."
> (room-lifecycle.md:176-177)

> "**One deliberate carve-out.** 'Every room mutation' means every mutation of the **`room` row**.
> Resolving a reservation (§3.2) touches `room_participant` only" (room-lifecycle.md:188-190) — one
> carve-out, and `detachSession` is not it.

> "  1. SELECT ... FROM room WHERE room_id = :roomId FOR UPDATE
>    …
>    3. room.state = nextState; room.active_session_id = NULL
>       if CLOSED: closed_at = now(), closed_reason = :reason" (room-lifecycle.md:479-483)

> "```json
> { "type": "ROOM_CLOSED", **"version": 49**, …" (room-websocket.md:309-311)

**Blocks:** `detachSession`'s repository method, and the `ROOM_CLOSED` / `GAME_ENDED` event builders.

**Two distinct defects in one place:**

*(a) The fence is missing.* §1.5 states the fence covers every mutation of the `room` row and names
exactly one carve-out, which this is not. `detachSession`'s TX substitutes `SELECT … FOR UPDATE` — a
*local* row lock, which orders concurrent transactions but does nothing about a stale owner.

Scenario: Redis `maxmemory` eviction or flush drops instance A's lease (the residual hole §1.5 and flow 05
§G both acknowledge). Instance B wrongfully takes over on epoch 7. A's clients are still attached. A's
game-end handler fires and calls `detachSession(room, session-1, 'game_over', 'LOBBY')`. Step 0's claim
returns *redirect*, so A records the closure as owed and returns — **if** it re-runs the claim. But the
retry-limit path (caller 4) and the sweep both arrive on threads that already claimed earlier in their
work; the spec does not say the claim is re-run per call. Where the claim is stale, A's TX commits
`state = 'LOBBY', active_session_id = NULL` with no fence and **durable divergence lands in the `room`
table** — precisely the property room-lifecycle.md:205 and ADR-0008:121 both assert is impossible: "**No
divergence becomes durable in the `room` table**". A then terminates a session B considers live.

*(b) No version is allocated.* `ROOM_CLOSED` and `GAME_ENDED` are documented as versioned events on
`/topic/room.{roomId}` (room-websocket.md:309, :362), and room-websocket.md:80 says version "is
incremented exactly once per state-mutating event" — this is the most state-mutating event there is. §4's
TX never touches `room.version`, so an implementer must invent whether `ROOM_CLOSED` carries the old
version, `version + 1`, or none. Choosing "old version" makes every attached client discard it
(`delta.version <= localVersion` → Discard), which is unrecoverable because ADR-0010:115 already notes "a
closed room emits no further events for a client to detect a gap against."

**Suggested resolution:** `room-lifecycle.md` §4 should own this. Add `version = :expected + 1` and
`AND version = :expected AND owner_epoch = :myEpoch` to the step-3 update, state that a zero rowcount
aborts the transaction and self-evicts per §1.5 layer 4, and state that step 7's broadcast carries the
newly committed version. Flow 06 §D and flow 07's skeletons need the same change.

---

### F6 — BLOCKER — "Record the closure as owed" has no store, and two documents disagree on whether it is even asynchronous

**Where:** `docs/specs/platform/room-lifecycle.md:466-476`, `docs/specs/flows/07-room-closure.md:26,34,81-84`,
`docs/specs/flows/06-game-end-and-rematch.md:83`, `docs/specs/platform/data-model-accounts.md:395,422-424`,
`docs/specs/platform/room-lifecycle.md:592-598` (§5.2 duty table)

**Quotes:**

> "A caller that cannot claim the room **records the closure as owed** and hands it to the reconciliation
> sweep, which claims first. This makes REST- and job-initiated closure **asynchronous**"
> (room-lifecycle.md:468-470)

> "  0. Claim the room (§1.2). On redirect, **record the closure as owed** and return —
>      the sweep will perform it." (room-lifecycle.md:475-476)

> "| `room` | rooms hosted with no other human remaining: `state = 'CLOSED'`,
> `closed_reason = 'ACCOUNT_DELETED'`; otherwise host transfer |" (data-model-accounts.md:395)

> "The erasure is **one transaction**, and the room work is the part that can fail on contention (**it
> takes the room lock**). It is ordered **last** so that a retry re-runs only the idempotent operations
> above it" (data-model-accounts.md:422-424)

**Blocks:** `DELETE /api/users/me` (the erasure transaction), the guest-cleanup job FR-JOB-001, and
reconciliation duty (a).

**Part 1 — the store does not exist.** I grepped the whole corpus for "owed": the phrase "record the
closure as owed" appears in exactly three places (room-lifecycle.md §4, flow 07, flow 06) and **nothing
defines where.** Candidates and why each fails:

- `session_teardown` — inserted at step 4, *inside* the transaction that step 0 never reaches; and it
  records a teardown to the Game Host, not a room-state change. Its `reason` maps 1:1 onto proto
  `TerminationReason`, not onto `closed_reason`.
- `room.reconcile_flagged_at` — the two-strike marker (data-model.md:112), single-valued, wrong semantics.
- §5.2's five duties — no duty has an "owed closure" predicate. "Idle Lobby" requires `last_activity_at`
  past the idle window, which a just-abandoned room does not satisfy; "In Progress, no session" requires
  the session record to be *absent*, which it is not.

**Scenario:** Alice hosts a room with a live session and one spectator, and deletes her account. The
`DELETE /api/users/me` lands on instance C; the room is owned by A. Step 0's claim returns redirect. C
records the closure "as owed" — into nothing. Nobody ever closes the room. `room.host_user_id` still
references Alice's (soft-deleted) `app_user` row; the spectator stays subscribed to a room whose host does
not exist; the session pins an Espresso context and its JAR for the life of the Game Host process
(ADR-0010:33-35).

**Part 2 — the two documents contradict, and neither is marked authoritative.** `data-model-accounts.md`
says the room closure happens *inside* the erasure transaction, synchronously, under "the room lock".
`room-lifecycle.md` §4 and flow 07 say a REST thread structurally *cannot* do this. Both are load-bearing
schema/lifecycle documents. Worse, "it takes the room lock" is itself wrong on the multi-instance path: the
room lock is a JVM-local `ReentrantLock` (room-websocket.md:33), so instance C acquiring it serializes
nothing against owner A.

**Suggested resolution:** `room-lifecycle.md` §4 should own it, because it is the document that introduced
the deferral. Either (a) add a durable owed-closure record — the cheapest form is
`room.closure_owed_reason text NULL` plus a §5.2 duty predicated on it, and it costs one column because the
room row is already the thing being closed; or (b) drop the deferral and have the non-owning caller commit
the closure under the fence, accepting that the `ROOM_CLOSED` broadcast is lost and letting FR-REJOIN-008
carry it. Whichever is chosen, `data-model-accounts.md:422-424` must be amended in the same change — its
"one transaction … takes the room lock" sentence is incompatible with (a) and misleading under (b).

---

### F7 — BLOCKER — AI players exist in the protocol and in the closure predicate, and nowhere in the schema

**Where:** `docs/specs/api-design/room-websocket.md:151-158`, `:208-222`, `:444`, `:561`, `:566`, `:665`,
`:669`; `docs/specs/platform/room-lifecycle.md:403-405`; `docs/specs/platform/data-model.md:157-178`,
`:227-238`; `docs/requirements/game-rooms.md:79`, `:115`, `:126`

**Quotes:**

> "\"aiPlayers\": [ { \"aiPlayerId\": \"uuid\", \"displayName\": \"string\", \"teamId\": \"uuid\" } ]"
> (room-websocket.md:151-156)

> "| `ADD_AI_PLAYER` | `teamId: uuid` | Lobby; game supports AI players (FR-HOST-003); target team has an
> available slot |" (room-websocket.md:566)

> "If no participant remains with `left_at IS NULL AND role = 'PLAYER'` that is **not an AI**, detach the
> session (§4) with next state `CLOSED`" (room-lifecycle.md:403-405)

> "`user_id  uuid  NOT NULL REFERENCES app_user(user_id),`
>  `role     text  NOT NULL,      -- PLAYER | SPECTATOR`" (data-model.md:160-161)

> "`teams[i].memberIds` contains all player IDs assigned to that team (human and AI); cross-reference with
> `aiPlayers` to determine AI status." (room-websocket.md:186)

**Blocks:** the Flyway migration for `room_participant`, the `ADD_AI_PLAYER` handler, `KICK_PLAYER` on an
AI target, `REASSIGN_PLAYER` on an AI target, the `ROOM_STATE` serializer, the FR-TEAM-005/011
auto-assignment count, the FR-TEAM-009 start-condition check, and `room-lifecycle.md` §3.3's closure
predicate.

**Scenario:** An implementer writes `ADD_AI_PLAYER`. `data-model.md` §2 is normative for names
(`data-model.md:22`), and it offers `room_participant(room_id, user_id NOT NULL → app_user, role ∈
{PLAYER, SPECTATOR})`. There is no `is_ai` column, no `ai_player` table, no `display_name`, and `user_id`
cannot be null. The three reachable choices are all wrong in a different way:

- Synthesise an `app_user` row per AI → AI players appear in friend search, statistics, guest purge
  (`app_user_guest_purge` sweeps by `kind`/`purgeable_after`) and account-deletion scatter.
- Add an untracked column → diverges from the document declared normative for names, which is the exact
  failure `data-model.md:6-9` exists to prevent ("four independent designs each invented their own column
  names for the same concepts").
- Store AI membership only in `room_team` → then `room-lifecycle.md` §3.3's predicate "no participant
  remains with `left_at IS NULL AND role = 'PLAYER'` **that is not an AI**" evaluates over a set that
  cannot contain an AI, so the qualifier is dead code and the *intent* — a room with only AI players left
  must close — is silently unimplemented. An `IN_PROGRESS` room with one human and three AI players whose
  human's grace expires would then stay open forever with a live session.

That last branch is why this is a BLOCKER rather than a GAP: the omission is not merely "AI is unbuilt", it
makes a *stated* closure rule unwritable, and the failure is silent.

**Suggested resolution:** `data-model.md` §2/§3 should own it. Given FR-HOST-003 and FR-TEAM-008 are both
`Should` priority, the honest options are (a) add the representation now — a nullable `user_id` plus
`ai_display_name`, with `CHECK (user_id IS NOT NULL OR ai_display_name IS NOT NULL)` and the primary key
moved off `(room_id, user_id)`; or (b) declare AI players out of MVP scope in one place and strike
`aiPlayers`, `AI_PLAYER_ADDED`, `ADD_AI_PLAYER`, `AI_NOT_SUPPORTED`, and the "that is not an AI" qualifier
from the specs that assume them. What must not survive is the current state, where the wire protocol is
fully specified and the storage is absent.

---

### F8 — BLOCKER — There is no REST specification for the room API

**Where:** `docs/specs/api-design/` (directory listing — no rooms document),
`docs/specs/flows/02-room-to-game-start.md:15-19`, `:61-67`;
`docs/specs/api-design/room-websocket.md:26`, `:672`; `docs/specs/platform/room-lifecycle.md:85`, `:254-258`

**Quotes:**

> "When a player joins or creates a room **via the REST endpoint**, the server claims the room if it is
> ownerless (or confirms the existing claim) and sets a routing hint in the response"
> (room-websocket.md:26)

> "| `ROOM_UNAVAILABLE_RETRY` | … **Also returned by the REST join/rejoin call, where it is an HTTP error
> rather than a frame** |" (room-websocket.md:672)

> "| `0` — redirect | Refresh the client's affinity hint to the named live owner and **return a retry
> directive**. Do **not** proxy. |" (room-lifecycle.md:85)

> "| 1 | Alice | … → `POST /api/rooms` `{gameId, visibility, spectatingEnabled}` |" (flow 02:15) — the only
> endpoint definition in the corpus, and it is in a narrative trace.

**Blocks:** every REST controller in the room slice: create, list, join, join-as-spectator, join-by-invite,
leave, rejoin.

`docs/specs/api-design/` contains `rest-conventions.md`, `error-handling.md`, `input-validation.md`,
`file-uploads.md`, `openapi-documentation.md`, `pagination-filtering-sorting.md`, `rate-limiting.md`,
`sse-notifications.md`, and the three WebSocket documents. There is no room REST document.
`rest-conventions.md:11` gives `/api/rooms/{roomId}/players` as a *naming example*;
`pagination-filtering-sorting.md:44` gives `GET /api/rooms?status=…&gameName=…&minPlayers=2` as a
*pagination example*. Neither is a specification.

**Scenario (the brief's scenario 1, which I could not answer from the corpus):** two players `POST` a join
for the last slot in a room. The serialisation is answerable — room-websocket.md:98 puts every REST-
originated mutation behind the owning pod's `ReentrantLock`, and room-lifecycle.md:85 redirects a
non-owning instance rather than letting it write, so the two joins do serialise. But **what the loser
receives is not specified anywhere.** The STOMP error table has `TEAM_FULL` (room-websocket.md:660), which
is a WebSocket frame code, not an HTTP response. `error-handling.md` defines the envelope but has no room
error catalogue. FR-LIST-003a says only "the operation fails with an alert and the list is refreshed"
(game-rooms.md:42), which is UI behaviour, not a status code or an error code. An implementer will invent
`409` or `422` and a code string, and the frontend will be written against whatever they invented.

This is also the single root cause behind the brief's mechanical list. Of the requirements cited by no
spec, these are genuinely unspecified and all belong to the missing document: **FR-CREATE-001, FR-CREATE-002,
FR-CREATE-004, FR-JOIN-001, FR-JOIN-002, FR-JOIN-003, FR-JOIN-004, FR-JOIN-005, FR-JOIN-011, FR-LIST-002,
FR-LIST-005, FR-LIST-007, FR-HOST-001, FR-HOST-002.** (Coverage of the remainder is itemised under *What
checked out*.)

`FR-LIST-002` additionally has a schema consequence: "Min and max player counts are **stored server-side**
for efficient filtering" (game-rooms.md:40), and `data-model.md` §1's `room` table has no such columns —
only `room_open_game_idx` on `(game_id, game_version)`.

**Suggested resolution:** a new `docs/specs/api-design/room-rest.md`, registered in
`docs/specs/api-design/INDEX.md`, owning the endpoint set, request/response shapes, the room error-code
catalogue with HTTP statuses, and the claim/redirect behaviour on join and rejoin that room-lifecycle.md
§1.2 and §1.7 currently describe only from the server's side. It should be sequenced before any room
controller work. **Note:** this overlaps the `inv-api` slice; flagging so the orchestrator can deduplicate.

---

### F9 — AMBIGUITY — `detachSession` inserts a `session_teardown` row unconditionally, but two of the five closure paths have no session

**Where:** `docs/specs/platform/room-lifecycle.md:479-485`, `docs/specs/flows/07-room-closure.md:23,39-44`,
`docs/specs/platform/data-model.md:133-139`, `:286-288`

**Quotes:**

> "  2. if room.active_session_id <> :sessionId: COMMIT; return    -- already detached, idempotent
>    …
>    4. INSERT INTO session_teardown (session_id, room_id, reason)
>         VALUES (...) ON CONFLICT (session_id) DO NOTHING" (room-lifecycle.md:480-485)

> "`session_id      uuid PRIMARY KEY,`" (data-model.md:287)

> "Closure must, in the transaction that sets `state = 'CLOSED'`: 1. record the owed session teardown,
> **if a session is attached**" (data-model.md:136-137)

**Blocks:** `detachSession`, and specifically the idle-Lobby reconciliation duty and the FR-XFER-002 host-
leave-in-lobby path.

**Scenario:** Flow 07 lists the idle-Lobby duty as caller 5 (`FR-JOB-007d` → `CLOSED`, `IDLE_TIMEOUT`,
flow 07:133). A Lobby room has `active_session_id IS NULL`. `detachSession(roomId, null, 'IDLE_TIMEOUT',
CLOSED)`:

- Step 2: `null <> null`. In SQL this is `NULL` (not true) and in Java `null != null` is `false`, so both
  readings fall through — correct by accident.
- Step 4: inserts `session_teardown` with `session_id = NULL`, which is the primary key. The insert throws,
  the transaction aborts, and **the idle-Lobby duty never closes any room.** Since idle-Lobby is the
  designated collector for abandoned Lobby rooms (room-lifecycle.md:418, flow 07:117), abandoned rooms
  accumulate forever.

`data-model.md:137` states the guard ("if a session is attached") in a paragraph about closure obligations,
which is why I have graded this AMBIGUITY rather than BLOCKER — but neither of the two documents that
carry the *algorithm* repeats it, and flow 07 explicitly lists step 4 with no condition.

The same applies to the FR-XFER-002 Lobby host-leave path, which is the ordinary way a lobby dies.

**Suggested resolution:** `room-lifecycle.md` §4 should own it: guard steps 4 **and** 5 on
`:sessionId IS NOT NULL`, and make step 2's idempotency comparison explicitly null-safe
(`IS DISTINCT FROM`). Flow 07's skeleton needs the same edit.

---

### F10 — AMBIGUITY — No rule for room deltas received before the first `ROOM_STATE`

**Where:** `docs/specs/api-design/room-websocket.md:619-627`, `:718-728`;
`docs/specs/api-design/websocket.md:437-446`, `:113`

**Quotes:**

> "3. Client subscribes to `/topic/room.{roomId}` … 4. Client sends `REQUEST_ROOM_STATE` … 6. Client
> receives snapshot, sets `localVersion = snapshot.version`." (room-websocket.md:623-626)

> "| `delta.version > localVersion + 1` | Gap detected — send `REQUEST_ROOM_STATE`; discard deltas until
> new snapshot arrives |" (room-websocket.md:726)

Contrast the game protocol, which has the row the room protocol lacks:

> "| Message received **before** `GAME_SYNC` has arrived | **Buffer it** |" (websocket.md:441)

**Blocks:** the frontend room reducer, and the `snapshot` rate-limit budget the client must live within.

**Scenario:** The subscribe-then-request ordering of step 3→4 is deliberate and correct (it is the same
race-free argument websocket.md:188-195 makes for the game stream). But it guarantees the client can
receive deltas *before* its first snapshot, with `localVersion` unset. Applying the table literally with
`localVersion = 0`: a delta at version 42 satisfies `42 > 0 + 1` → gap → the client sends a **second**
`REQUEST_ROOM_STATE`, competing with the one already in flight. On a mass reconnect after a pod loss —
where every client attaches at once into a busy room — each client burns both `snapshot` tokens (1 per 3s,
burst 2, rate-limiting.md:161) in the first second and then sits discarding deltas.

The two readings an implementer will pick between are "discard pre-snapshot deltas silently, the snapshot
supersedes them" and "follow the table". They differ in observable load and, under sustained traffic, in
whether the client ever converges.

A related unstated dependency: `websocket.md:113` sets `setPreservePublishOrder(true)` and justifies it
purely for the game stream. That setting is broker-wide, and if enabled it is also what orders
`/user/queue/room-state` against `/topic/room.{roomId}` for a single session — which is load-bearing for
the room snapshot flow and is not mentioned in `room-websocket.md` at all.

**Suggested resolution:** `room-websocket.md` § Client Reconciliation should add the missing row —
"message received before the first `ROOM_STATE`: buffer (or discard); do not gap-detect" — mirroring
websocket.md:441, and § Snapshot Delivery should state the broker ordering property it depends on.

---

### F11 — AMBIGUITY — The two documents disagree on which reconciliation duties keep the FR-JOB-008 guards

**Where:** `docs/specs/platform/room-lifecycle.md:615-638` (§5.4), `docs/requirements/platform-operations.md:151`,
`docs/specs/platform/data-model.md:286-296`

**Quotes:**

> "2. **Two strikes.** … **The unowned-room duty is exempt** … **The other three repair duties** are all
> inferences about missing state and do take the two strikes." (room-lifecycle.md:622-628)

> "3. **Startup suppression.** No repair within 120s of instance start. … **Duties (b), (c) and (d)** are
> inferences about missing state and do keep the guard." (room-lifecycle.md:629-638)

> "**guards (a) and (b) both exempt the room-adoption duty (FR-JOB-007e)**" (platform-operations.md:151) —
> exempting exactly one duty, not two.

**Blocks:** the reconciliation job's duty dispatcher, and the `session_teardown` schema.

There are five duties (room-lifecycle.md:592-598): (a) owed teardown, (b) orphaned artifacts, (c)
In-Progress-no-session, (d) idle Lobby, (e) unowned room. `room-lifecycle.md` §5.4 exempts (e) explicitly
and, by counting ("the other three", "(b), (c) and (d)"), exempts (a) implicitly. `platform-operations.md`
FR-JOB-008 exempts (e) only, which puts (a) under both guards.

**Scenario:** An implementer follows FR-JOB-008 literally.

1. Startup suppression: for 120s after every restart, no owed teardown is re-driven. Since a full-stack
   restart is the MVP's routine path and a Game Host restart is "the *common* failure"
   (room-lifecycle.md:502-503), this systematically delays the retry of exactly the failures that arise
   from the restart, and each leaked session pins an Espresso context and its JAR (ADR-0010:33-35).
2. Two-strike: the implementer needs somewhere to record the first observation. `room.reconcile_flagged_at`
   is room-scoped and `session_teardown` is keyed by session with a room that may have been purged
   (data-model.md:305-306) — so it must be a new column. But the two-strike rule is nonsensical here
   anyway: a `session_teardown` row is not an inference about missing state, it is a to-do the platform
   wrote itself, and it already carries its own scheduling in `next_attempt_at`.

**Suggested resolution:** `platform-operations.md` FR-JOB-008 should be amended to match
`room-lifecycle.md` — exempt both the owed-teardown duty (a) and the adoption duty (e), on the grounds that
neither infers anything: (a) re-drives a record the platform itself wrote, (e) reads an absent lease. And
`room-lifecycle.md` §5.4 should say "(a) and (e)" explicitly rather than leaving (a) to be inferred from a
count.

---

### F12 — GAP — FR-EXPIRY-006 has no statement, and the game-end flow omits it entirely

**Where:** `docs/requirements/reconnection-flow.md:88`, `docs/specs/platform/room-lifecycle.md:483`,
`docs/specs/flows/06-game-end-and-rematch.md:88-90`, `docs/specs/flows/07-room-closure.md:42`,
`docs/decisions/0009-grace-deadline-durability.md:88-89`

**Quotes:**

> "| FR-EXPIRY-006 | Game end resolves outstanding reservations | … Every reservation still outstanding at
> that moment is **resolved immediately as a departure, with no game-engine notification** — the session it
> referred to is over. |" (reconnection-flow.md:88)

> "  3. room.state = nextState; room.active_session_id = NULL
>        …
>        release slots / **clear reservations** / reset readiness **per the path**" (room-lifecycle.md:481-483)

> "  3. room.state = 'LOBBY'; room.active_session_id = NULL; **reset all readiness**"
> (flow 06:88) — reservations are not mentioned on the one path where FR-EXPIRY-006 applies.

**Blocks:** `detachSession` step 3 for all five callers.

`room-lifecycle.md`'s "per the path" is the entire specification, and **there is no path table**. Nowhere
does any document say, for each of the five callers: which participants get `left_at` set, which
`leave_reason` value (the enum offers `LEFT | KICKED | GRACE_EXPIRED | EARLY_RELEASE | ROOM_CLOSED |
GAME_ENDED`, data-model.md:173-174 — two of which, `ROOM_CLOSED` and `GAME_ENDED`, have no writer named
anywhere), whether `PLAYER_LOST` or `PLAYER_LEFT` is broadcast, and whether `lost_announced_at` is stamped.

**Scenario:** Game end. Bob is 30 seconds into a grace reservation. Flow 06 §D — the document that owns the
game-end detach — does not clear it. So the room returns to `LOBBY` with a live reservation. 30 seconds
later the deadline sweep's duty 1 selects Bob's row and runs §3.3 — landing straight in **F1**: an outbox
insert with no session, in a `LOBBY` room. The two findings compound: FR-EXPIRY-006 exists precisely to
prevent this state, and the flow that must implement it does not.

Even given the F1 fix, the outcome differs by reading: `leave_reason = 'GAME_ENDED'` with no broadcast
(FR-EXPIRY-006's plain text) versus `'GRACE_EXPIRED'` with `PLAYER_LOST` (what §3.2/§3.3 actually do). Under
the second, Bob is told his grace expired for a game that finished.

**Suggested resolution:** `room-lifecycle.md` §4 should replace "per the path" with a five-row table —
caller × (`left_at`, `leave_reason`, event broadcast, `lost_announced_at`) — and state the game-end row as
FR-EXPIRY-006 requires: resolve all outstanding reservations with `leave_reason = 'GAME_ENDED'`, no outbox
row, no `PLAYER_LOST`, `lost_announced_at` stamped (see F4). Flow 06 §D step 3 needs the corresponding line.

---

### F13 — GAP — The Lobby immediate-leave path has no algorithm

**Where:** `docs/specs/platform/room-lifecycle.md:333-336` (§3.1 scope),
`docs/specs/flows/04-disconnect-and-return.md:30-33`, `docs/requirements/reconnection-flow.md:43,48`

**Quotes:**

> "Under the room lock, on the owning instance, when a participant's `connection_count` reaches zero **in
> an `IN_PROGRESS` room**:" (room-lifecycle.md:333-334)

> "| Room in `LOBBY` | Immediate leave, no reservation (`FR-DC-002`) — **unless** this is owner-instance
> loss (`FR-DC-007`) |" (flow 04:31)

**Blocks:** the `SessionDisconnectEvent` handler.

`room-lifecycle.md` §3 covers `IN_PROGRESS` only. Flow 04 names the Lobby branch in one table cell and gives
no statement. So for the Lobby disconnect — which is the *more common* disconnect, since most room time is
lobby time — an implementer has no `UPDATE`, no `leave_reason`, no answer to whether host transfer
(FR-XFER-001) or closure evaluation (FR-XFER-002) runs in the same transaction or after commit, and no
answer to the question that matters most: **how the handler distinguishes an individual Lobby disconnect
from an owner-pod-loss disconnect** (FR-DC-007). The corpus's implicit answer is "owner-pod loss never
reaches this handler, because the owner is dead" — which is exactly the assumption **F2** shows to be false
on the drain and self-eviction paths.

**Suggested resolution:** `room-lifecycle.md` should gain a §3.0 giving the Lobby branch the same treatment
§3.1 gives the In Progress branch: the statement, the `leave_reason`, the event, the ordering of host
transfer and closure evaluation relative to the commit, and the explicit statement that the drain and
self-eviction paths do not enter it (per F2).

---

### F14 — GAP — "Evict spectators" is undefined, and so is "member" for the subscribe guard

**Where:** `docs/specs/platform/room-lifecycle.md:491`, `docs/specs/flows/07-room-closure.md:49`,
`docs/specs/api-design/room-websocket.md:587-591`, `:331`, `docs/specs/platform/data-model.md:189-196`

**Quotes:**

> "  7. broadcast ROOM_CLOSED (or the game-end transition) ; **evict spectators**" (room-lifecycle.md:491)

> "| `/topic/room.{roomId}` (subscribe) | **Sender is a member or spectator of the room** | Silent drop |"
> (room-websocket.md:587)

> "Clients **should** unsubscribe and navigate away on receipt." (room-websocket.md:331)

**Blocks:** `detachSession` step 7, and the `SubscriptionInterceptor`.

**(a) Eviction.** "Evict spectators" appears twice as a step and is defined nowhere. In Spring STOMP the
server cannot revoke a subscription; the options are closing the WebSocket session, sending a per-user
`ERROR` frame (which also closes it), or doing nothing and relying on the client's "should unsubscribe".
These are observably different — the third leaves a spectator holding an open socket into a dead room,
which is the exact outcome room-lifecycle.md:470-471 says the whole asynchronous-closure design exists to
avoid ("a spectator silently stranded in a subscription to a dead room has nothing to repair it"). If the
answer is "the client unsubscribes on `ROOM_CLOSED`", then step 7's second clause is not a server action
and should not be written as one.

**(b) "Member".** The interceptor needs a predicate over `room_participant`. `data-model.md:189-196` gives
three row states (Present / In grace / Released), and the guard does not say which qualify. Consequences of
each reading: if "Released" counts, a player whose grace expired keeps receiving every room event on a
second still-open tab indefinitely — and there is no re-check, because the interceptor runs at `SUBSCRIBE`
only. If it does not count, a player *in grace* on a second tab (`left_at IS NULL`,
`grace_reservation_id IS NOT NULL`) must still be admitted, or FR-GRACE-006's multi-connection semantics
break.

**Suggested resolution:** `room-websocket.md` § Authorization Model should define "member" as a predicate
over `room_participant` in `data-model.md`'s vocabulary (`left_at IS NULL`, any `role`), state that
subscriptions are *not* re-evaluated after the fact, and either define eviction as an explicit server
action or delete the phrase from both step-7 pseudocodes.

---

### F15 — GAP — Deadline-sweep duty 2 has no index, and the one participant index is partial on the opposite predicate

**Where:** `docs/specs/platform/data-model.md:180-182`, `:367-370`;
`docs/specs/platform/room-lifecycle.md:557`, `:534`

**Quotes:**

> "CREATE INDEX room_participant_grace_due_idx
>   ON room_participant (grace_expires_at)
>   WHERE **grace_expires_at IS NOT NULL AND left_at IS NULL**;" (data-model.md:180-182)

> "2. **Deferred tails** … (**`left_at IS NOT NULL` AND `lost_announced_at IS NULL`**, §3.3)"
> (room-lifecycle.md:557)

> "`room_participant_grace_due_idx` spans only players *currently in grace* … so the 5-second deadline sweep
> is an index-only scan of a nearly empty index rather than a table scan." (data-model.md:367-370)

**Blocks:** the Flyway migration for `room_participant`.

Duty 2's predicate is the logical complement of the index's `left_at IS NULL` clause, and §3.2 sets
`grace_expires_at = NULL` when it resolves — so a deferred-tail row satisfies *neither* index condition. The
duty therefore runs a **sequential scan of the entire `room_participant` table every 5 seconds**, joined to
`room` for the ownership partition. `room_participant` is append-only by design ("Rows are **not deleted**
on departure", data-model.md:153) and only purged 7 days after room closure (FR-JOB-009), so this table is
the largest and fastest-growing in the room schema. `data-model.md`'s index-rationale section states the
5-second sweep is index-only, which is true of duty 1 and false of duty 2.

Note this interacts with **F4**: with duty 2's predicate correctly narrowed, the index becomes
`(room_id) WHERE left_at IS NOT NULL AND lost_announced_at IS NULL`, which is near-empty in steady state.
Fixing F4 makes the index cheap; leaving F4 unfixed makes it match every departed participant ever.

**Suggested resolution:** `data-model.md` §2 adds a partial index matching duty 2's final predicate, and §5
records it. Sequence after F4, so the predicate is settled first.

---

### F16 — GAP — `ROOM_STATE.spectatorCapacity` has no source

**Where:** `docs/specs/api-design/room-websocket.md:138`, `:541`, `:666`;
`docs/requirements/game-rooms.md:163`; `docs/specs/platform/data-model.md:39-64`;
`docs/specs/deployment/local-environment.md` §7.2

**Quotes:**

> "\"spectatorCapacity\": 8," (room-websocket.md:138)

> "| `SWITCH_TO_SPECTATOR` | … Lobby; spectating enabled for room; **spectator capacity not exceeded**
> (NFR-SPEC-001 …) |" (room-websocket.md:541)

> "| NFR-SPEC-001 | Scalability | Maximum spectators per room is **configurable at the platform level**;
> default is 8 | Default: 8 | Must |" (game-rooms.md:163)

**Blocks:** the `ROOM_STATE` serializer, the `SWITCH_TO_SPECTATOR` handler, and the join-as-spectator
capacity check (FR-JOIN-005).

The `room` table has `spectating_enabled boolean` but no capacity column — correctly, since NFR-SPEC-001
says hosts have no control over the limit. But I grepped `local-environment.md`'s configuration surface
(§7.2, which lists `turnbase.room.grace-period`, `.migration-window`, `.idle-window`, `.lease.*`) and there
is **no spectator-capacity key**. So the value that three separate protocol behaviours depend on has no
declared home in either store.

**Suggested resolution:** add `turnbase.room.spectator-capacity` (default `8`, cited to NFR-SPEC-001) to
`local-environment.md` §7.2's room table. One line; low risk; blocks three handlers if missed.

---

### F17 — DRIFT — `room-lifecycle.md` §4 is missing flow 07's step 3b

**Where:** `docs/specs/platform/room-lifecycle.md:479-489`, `docs/specs/flows/07-room-closure.md:43,56-61`,
`docs/specs/platform/data-model.md:136-142`

**Quotes:**

> "  3b. DELETE FROM room_invitation WHERE room_id = :r              -- FR-INV-008" (flow 07:43)

> "**Step 3b is easy to lose**, and it is the one addition this trace forced." (flow 07:56)

room-lifecycle.md §4's pseudocode goes 3 → 4 → 5 with no 3b. Flow 07 says explicitly that this step is easy
to lose, then leaves it out of the document that owns the algorithm. An implementer writing
`detachSession` works from `room-lifecycle.md` §4 — it is the spec, flow 07 is a narrative — and will omit
invitation deletion. Bounded by `room_invitation.expires_at` (FR-INV-009) as flow 07 notes, so the damage is
a stale actionable notification rather than a permanent one; hence DRIFT rather than GAP.

**Suggested resolution:** copy step 3b into `room-lifecycle.md` §4's pseudocode. One line.

---

### F18 — DRIFT — Adoption's migration-window arming is inconsistent across three documents, and fires on ordinary claims

**Where:** `docs/specs/platform/room-lifecycle.md:148-152`, `docs/specs/flows/05-owner-loss-and-adoption.md:67`,
`docs/specs/flows/02-room-to-game-start.md:40`, `docs/requirements/reconnection-flow.md:106`

**Quotes:**

> "7. Start the migration window (FR-HDISC-004) by setting `room.migration_window_expires_at = now() + 20s`."
> (room-lifecycle.md:148-149) — unconditional, on every adoption.

> "`UPDATE room SET owner_instance_id='B', owner_epoch=:myEpoch, ownerless_since=NULL,
> **migration_window_expires_at=now()+:window** WHERE …`" (flow 05:67)

> "`UPDATE room SET owner_instance_id=…, owner_epoch=:myEpoch, ownerless_since=NULL WHERE room_id=… AND
> owner_epoch < :myEpoch`" (flow 02:40) — **no** `migration_window_expires_at`.

> "| FR-HDISC-004 | Migration window after owner-pod loss | **Following an owner-pod loss (FR-DC-006)**,
> host transfer is deferred" (reconnection-flow.md:106) — scoped to owner-pod loss.

**Blocks:** the adoption procedure and deadline-sweep duty 3.

Flow 02 §B is the *first ever* claim of a freshly created room. Under §1.4 the claim script returns `2`
(ADOPTED — the free branch), so adoption runs, so step 7 arms a 20-second migration window on a room that
has never had an owner and has suffered no pod loss. Flow 02's own `UPDATE` omits the column, so the two
flows model the same code path differently.

Consequence: for the first 20 seconds of every room's life, and for 20 seconds after any ordinary claim of
a momentarily-unowned room, `room.migration_window_expires_at` is set. §3.1's host-transfer line ("apply
host transfer (FR-HDISC-001) **unless the migration window is open**", room-lifecycle.md:352-353) then
suppresses a legitimate individual host transfer, and duty 3 performs it up to 20 seconds late. Small
window, real behaviour difference, and the three documents give three different answers about whether it
happens at all.

**Suggested resolution:** `room-lifecycle.md` §1.4 step 7 should state the condition under which the window
is armed — the natural one is "only when step 4 opened at least one reservation, or step 5 zeroed at least
one `connection_count`", which is precisely the observable signature of an owner-pod loss and is false for
a fresh or genuinely idle room. Flow 02 §B and flow 05 §C should then agree.

---

### F19 — DRIFT — Adoption assumes a `room` row that room creation may not have written yet

**Where:** `docs/specs/platform/room-lifecycle.md:125-131`, `docs/specs/flows/02-room-to-game-start.md:18,22-24`

**Quotes:**

> "1. **Load the room from Postgres.** It is authoritative; nothing is reconstructed from Redis."
> (room-lifecycle.md:127)

> "**Nothing is claimed yet.** Room creation writes Postgres and touches no Redis lease. Ownership is
> established by the first *client attach*, not by creation" (flow 02:22-23)

Flow 02 settles it — the `INSERT` (step A4) precedes the claim (step B3) because the claim happens on the
client's `SUBSCRIBE`, which cannot occur before the `201` response. So adoption always finds a row. But
`room-lifecycle.md` never says this, and §1.4 step 3's guard (`owner_epoch < :myEpoch`, with
`owner_epoch bigint NOT NULL DEFAULT 0` and the first claim yielding epoch 1) only works because of the
`DEFAULT 0` — a fact stated in `data-model.md:54` and relied upon in neither §1.4 nor flow 02's step-4
commentary. Cheap to state; an implementer who adds an eager claim to room creation (a natural
optimisation, and one nothing forbids in §1.2) will find step 1 loading nothing.

**Suggested resolution:** `room-lifecycle.md` §1.4 should state the precondition — "a `room` row exists;
creation commits before any claim can be issued for it" — and §1.2 should say that room creation does not
claim, which currently lives only in flow 02.

---

### F20 — GAP — §3.1's "after commit" is a second transaction with no crash recovery

**Where:** `docs/specs/platform/room-lifecycle.md:336-354`, `:352-353`, `:557`

**Quotes:**

> "**After commit:** bump the version, broadcast `PLAYER_DISCONNECTED`, and apply host transfer
> (FR-HDISC-001) unless the migration window is open." (room-lifecycle.md:352-353)

**Blocks:** the disconnect handler.

The reservation `UPDATE` (§3.1) commits in one transaction; the version bump — a *separate* fenced
`UPDATE room` — commits in a second. The brief asked for every "then" with no death semantics; this is one.
If the process dies between them, the reservation exists durably and `PLAYER_DISCONNECTED` was never sent,
no version was burned, and **no sweep duty recovers it**: duty 2's predicate requires `left_at IS NOT NULL`,
which a live reservation does not satisfy.

Observable effect: other clients continue to render the player as connected. It self-heals only for a
client that happens to resnapshot for some other reason (§3.4's `disconnectedPlayers` derives from
`grace_expires_at`, so a snapshot is correct), and otherwise the first thing anyone learns is
`PLAYER_LOST` 60 seconds later with no preceding disconnect event. Also lost is the FR-HDISC-001 host
transfer, which would leave the room headless until duty 3's migration-window expiry — and duty 3 only runs
if `migration_window_expires_at` is set, which on an individual disconnect it is not.

Severity is GAP rather than BLOCKER because the durable state is correct and only the announcement is lost.

**Suggested resolution:** `room-lifecycle.md` §3.1 should either fold the version bump into the same
transaction as the reservation (the natural fix — both are Postgres writes, and §2.1's nesting already
permits a single transaction inside the lock) or state the recovery path explicitly.

---

### F21 — NIT — §1.4 step 7 hard-codes a configured value

`docs/specs/platform/room-lifecycle.md:149` writes `room.migration_window_expires_at = now() + 20s`, while
`local-environment.md` §7.2 defines `turnbase.room.migration-window` (default `20s`, cited to FR-HDISC-004
and room-lifecycle §1.4) and flow 05:67 correctly writes `now()+:window`. NFR-CONF-002 requires
configurability. Cosmetic — replace `20s` with `:migrationWindow`.

---

## What checked out

Actively verified as consistent and implementable:

- **Numeric constants agree across every document.** 10s lease TTL (ADR-0008:39, room-lifecycle.md:38,
  platform-operations.md:74, local-environment.md:329), 3s renew (ADR-0008:39, room-lifecycle.md:38,
  local-environment.md:330), 6s self-evict (room-lifecycle.md OQ-001, flow 05:163,
  local-environment.md:331), 20s migration window (reconnection-flow.md:32 & NFR-CONF-002,
  room-lifecycle.md:149, local-environment.md:327), 60s grace (reconnection-flow.md FR-GRACE-002,
  websocket.md:17, local-environment.md:326), 5s deadline sweep (platform-operations.md FR-JOB-006,
  room-lifecycle.md:534, local-environment.md:343), 60s reconcile (platform-operations.md FR-JOB-007,
  room-lifecycle.md:590), 120s startup suppression (platform-operations.md FR-JOB-008a,
  room-lifecycle.md:630), 30m idle window (platform-operations.md FR-JOB-007d, flow 07:117,
  local-environment.md:328), 10m orphan age (platform-operations.md FR-JOB-007b, room-lifecycle.md:595),
  90s NFR-JOB-002 (platform-operations.md:193, flow 05:115). Every one is also a named config key with the
  same default. **No disagreements found.** local-environment.md:333 additionally states the three lease
  values as a *set* with the invariants that must hold, which is the right framing.
- **The epoch fence is correctly specified on the ownership writes.** Adoption uses `owner_epoch < :myEpoch`
  (room-lifecycle.md:130, ADR-0008:72-76, flow 02:40, flow 05:67, data-model.md:79-84) with the monotonicity
  argument stated identically in all four. Release uses `owner_epoch = :myEpoch` (room-lifecycle.md:112) and
  never clears the epoch (room-lifecycle.md:116, data-model.md:102, flow 05:200). Version-bumping mutations
  use `version = :expected AND owner_epoch = :myEpoch` (room-lifecycle.md:176, room-websocket.md:113,
  data-model.md:81, ADR-0008:53). The one carve-out — reservation resolution touching `room_participant`
  only — is stated with its reason (room-lifecycle.md:188-194). The **only** gap I found in fence coverage
  is `detachSession` (F5) and duty 3's column clear.
- **Scenario 3 (deadline expiring during adoption) composes correctly, including the failure branch.** Old
  owner A and new owner B can both select the row; §3.2's rowcount arbitrates, so it fires exactly once.
  If A wins the `room_participant` update but then fails its post-commit version CAS against B's newer
  epoch, A aborts and self-evicts (room-lifecycle.md:177-178) — leaving the reservation resolved, the
  outbox row committed (same transaction, room-lifecycle.md:396-398), and `lost_announced_at` null, which
  duty 2 recovers. It can fire zero times only while the room is unowned, which room-lifecycle.md:548-552
  states as an explicit, bounded cost rather than leaving it to be discovered.
- **Scenario 7 (rematch) is clean.** `session_teardown` keyed by `session_id` (data-model.md:299-302,
  ADR-0010:47-60), fresh `sessionId` per start made normative (ADR-0010:51), all Redis keys
  `{sessionId}`-scoped, `detachSession` step 2's idempotency on `active_session_id <> :sessionId`, and the
  `NOT_FOUND` rule testing `active_session_id` rather than teardown history (data-model.md:270-278, flow
  04:122-134). I traced session A's owed teardown re-driving four seconds into session B (flow 06 §F) and
  found no path by which A's teardown touches B's state. The reasoning for *why* the obvious alternative
  test fails is written down in two places, which is what makes it safe against a low-effort agent.
- **`session_teardown` writers and deleters are complete and consistent.** Writers: `detachSession` step 4
  (`ON CONFLICT DO NOTHING`) and `terminateAndCleanup` (c) for the backoff bookkeeping. Deleters:
  `terminateAndCleanup` (b) on OK, reached both inline and from §5.2 duty (a). No FK on `room_id`
  (data-model.md:305), so the FR-JOB-009 purge cannot orphan or destroy it. `TerminateSession` idempotency
  and `NOT_FOUND`-means-success are both promoted to the contract (ADR-0010:88-90, flow 07:189). The row is
  written inside the transaction, before any remote call, on every path.
- **`game_input_outbox.dispatched_at` on-ACK-not-on-attempt** is stated with its failure mode in three
  places (data-model.md:347-355, flow 04:118-120, room-lifecycle.md:487) and the `sequence`-persisted-once
  rule likewise (data-model.md:338-345, ADR-0009:58-62, flow 04:114). The outbox drain's exemption from
  ownership partitioning is justified identically in room-lifecycle.md:576-584, flow 04:57-63 and
  platform-operations.md FR-JOB-006.
- **Scenario 2's version continuity holds.** V1 (persist before publish) and V2 (assign, never `max()`) are
  stated in ADR-0008:95-108, room-websocket.md:111/720, room-lifecycle.md:298-306/§2.2 and flow 05:77-80
  with the same reasoning, and the normative nesting (lock outer → transaction inner → publish after
  commit, before unlock) is stated explicitly as a warning against the `@Transactional`-on-handler idiom in
  both room-lifecycle.md:281-284 and room-websocket.md:113. The gap-detect-then-resnapshot path is
  correctly identified as the takeover mechanism rather than an edge case (room-websocket.md:728).
- **Ownership re-verification at `SUBSCRIBE`** is specified consistently in ADR-0008:130-133,
  room-lifecycle.md:260-264 and room-websocket.md:700-708, including the two distinct arrival points for
  `ROOM_UNAVAILABLE_RETRY` and the reason the retry budget is sub-second rather than multi-second.
- **Scenario 5 (host transfers, new host disconnects inside the migration window)** resolves correctly:
  §3.1 defers the transfer while the window is open, and duty 3 (room-lifecycle.md:561-568) clears the
  column and performs the deferred transfer against the *current* host, covering both "disconnected" and
  "released". The window is not re-armed or extended, and it does not need to be — 20s < 60s grace, so the
  new host is still in their reservation when duty 3 fires. `data-model.md:106-110` and
  reconnection-flow.md FR-HDISC-004 both explain why the column is persisted rather than in-JVM. The only
  defect on this path is F18's over-arming.
- **`host_user_id` nullability** is reasoned and traced to the requirement that produces it
  (data-model.md:86-92, reconnection-flow.md FR-HDISC-003's final sentence), closing the dangling-reference
  case that duty 3 would otherwise create.
- **Requirement coverage — genuinely specified despite being cited by no spec:** FR-JOIN-007 (single-room /
  early release) is fully specified via FR-EXPIRY-004 in room-lifecycle.md §3.3 and flow 04 §D.
  FR-JOIN-008/009/010 (abandonment prompts) are client-side and covered by `platform-views.md`.
  FR-HOST-008 (parameters preserved on rematch) is satisfied structurally — `room.parameters` is a column
  and `detachSession` step 3 does not touch it. FR-HDISC-002 is covered at room-websocket.md:510.
  FR-KICK-001/002/003/004 are covered by room-websocket.md:571's `KICK_PLAYER` note. FR-LIST-003/004 are
  covered by `pagination-filtering-sorting.md`. FR-LIST-006 is covered by `platform-views.md`.
  FR-EXPIRY-003 / FR-REJOIN-002 are covered by `platform-views.md` VW-ROOMS-005. NFR-CONF-002 is covered by
  `local-environment.md` §7.2. FR-CHAN-001/002/003/004, FR-MSG-001/002/003/004/005/006 and
  FR-SWITCH-001/002 are covered by `room-chat-websocket.md` (FR-MSG-003 and FR-SWITCH-* are pure client
  rendering and need no server spec). FR-TEAM-008 is covered by room-websocket.md:566's `ADD_AI_PLAYER`
  *protocol* — but see F7 for its storage.
- **STOMP destination coverage.** For all six room destinations plus the two chat destinations, the
  subscriber set, the authorising predicate and the on-subscribe behaviour are all stated
  (room-websocket.md:53-62, :585-591; room-chat-websocket.md:17-23, :91-95), with `AntPathMatcher`
  non-overlap and the `.`-separator constraint written down for both room and game patterns. The only
  unresolved questions are F14's definition of "member" and the fact that subscribe-time ownership
  re-verification is stated for `/topic/room.{roomId}` but not for the chat and team topics.
