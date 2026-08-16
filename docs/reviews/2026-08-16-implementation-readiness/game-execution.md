# Game execution stack — implementation-readiness audit

**Agent:** Opus (high effort) · **Files reviewed:** 16 read in full, 7 sampled · **Date:** 2026-08-16

## Coverage

**Read in full:**

- `docs/specs/game-host/game-host-internals.md` (765 lines)
- `docs/specs/game-host/INDEX.md`
- `docs/specs/internal-grpc/gamehost.proto` (456 lines)
- `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` (367 lines)
- `docs/specs/gdk-api/backend-gdk-api.md` (677 lines)
- `docs/specs/gdk-api/test-harness.md`
- `docs/specs/gdk-api/INDEX.md`
- `docs/requirements/game-contracts.md`
- `docs/requirements/platform-architecture.md`
- `docs/decisions/0006-game-trust-model-java-official-only.md`
- `docs/reviews/2026-07-02-mvp-readiness/espresso-spike-results.md`
- `docs/specs/flows/03-game-turn.md`, `06-game-end-and-rematch.md`, `INDEX.md`

**Sampled (targeted reads, not full):**

- `docs/specs/api-design/websocket.md` lines 120–409 (the whole Game Session Protocol) — the fan-out
  seam my slice hands off to.
- `docs/specs/flows/02-room-to-game-start.md` §E and "What is durable" — the `CreateSession` caller.
- `docs/specs/platform/data-model.md` §4 (`session_teardown`, `game_input_outbox`).
- `docs/specs/manifest/bundle-format.md` §6 (`gdkApiVersion` compatibility) — scenario 7.
- `docs/decisions/0010-session-teardown-ordering.md` decision §2.
- `docs/specs/gdk-api/frontend-gdk-api.md` — grepped for the BE↔FE event seam only.

**Not checked (declared):**

- `docs/decisions/0005-game-sandbox-espresso-spike.md` — I read the spike *results* document it gates
  and the two requirement docs that cite it, and every FR-CTX claim I checked reconciles against the
  results. I did **not** open ADR-0005 itself. Findings F9/F11 touch the sandbox and are marked where
  they depend on this.
- `docs/requirements/game-development-experience.md` — FR-GDK-* / FR-HARNESS-* are cited from the
  specs I did read; I verified FR-GDK-016 and FR-HARNESS-010 by grep, not by reading the document.
  Any FR-GDK numbering error in `backend-gdk-api.md` §12 would not have been caught.
- `docs/specs/manifest/manifest-schema.md` beyond the `gdkApiVersion` / `runtime` rows.
- ADR-0006's "official-only needs a concrete enforcement point" consequence — I confirmed the
  *manifest* side exists but did not trace the deployment path that is supposed to enforce it. Flagged
  as UNVERIFIED inside F10.

---

## Summary

| # | Severity | One-line | Location |
|---|---|---|---|
| F1 | BLOCKER | `session:{id}` has two claimed writers; the Orchestration pre-write disarms `CreateSession`'s idempotency guard so `onInit` never runs | `docs/specs/flows/02-room-to-game-start.md:115`, `docs/specs/game-host/game-host-internals.md:647`, `docs/requirements/platform-architecture.md:130` |
| F2 | BLOCKER | The two owning docs disagree on whether `lastAppliedSequence` advances on a *failed* input — and the session record has nowhere to store a failure, so the replay path returns `OK` with the previous input's effects | `docs/specs/internal-grpc/orchestration-gamehost-protocol.md:271`, `docs/specs/game-host/game-host-internals.md:404-412`, `:358-362` |
| F3 | BLOCKER | The proto tells the Game Host to reject out-of-order sequences; the prose makes forward sequence gaps normal. A defensive implementer freezes every session after its first failed action | `docs/specs/internal-grpc/gamehost.proto:39-40`, `docs/specs/internal-grpc/orchestration-gamehost-protocol.md:270` |
| F4 | BLOCKER | No server-side check that `SendToPlayerEffect.player_id` is a participant of the session; `/user/queue/game` is explicitly not session-scoped. NFR-SEC-002 (Must) is not achieved | `docs/specs/api-design/websocket.md:133`, `:255`, `:261`, `docs/requirements/game-contracts.md:169` |
| F5 | AMBIGUITY | `CreateSession` has no failure branch anywhere. `onInit` throws → room is left `IN_PROGRESS` pointing at a session that does not exist | `docs/specs/flows/02-room-to-game-start.md:118`, `docs/specs/game-host/game-host-internals.md:390-399` |
| F6 | AMBIGUITY | "`UNAVAILABLE` … only counts toward the limit if reassignment cannot make progress" — "cannot make progress" is defined nowhere and bounds nothing | `docs/specs/game-host/game-host-internals.md:526-527` |
| F7 | AMBIGUITY | FR-FAIL-001's failure notification names only "the acting player". `player_joined` / `player_left` / `CreateSession` failures have no notification target | `docs/requirements/platform-architecture.md:185`, `docs/specs/internal-grpc/orchestration-gamehost-protocol.md:272` |
| F8 | GAP | `game-contracts.md` NFR-REL-001 still carries the pre-reconciliation "terminate on failure" text and is cited by three specs as if it said "after the retry limit" | `docs/requirements/game-contracts.md:172`, `docs/specs/gdk-api/backend-gdk-api.md:540`, `:84` |
| F9 | GAP | Guest thread creation is enforced nowhere: absent from the §4 mechanism table, absent from the §4.2 builder, and the harness tells developers the Game Host blocks it | `docs/specs/game-host/game-host-internals.md:198-246`, `docs/specs/gdk-api/test-harness.md:174` |
| F10 | GAP | Host-JVM heap sizing vs. the cgroup limit is unspecified, and it is the only thing standing between "unbounded allocation" and the FR-CTX-007 story | `docs/specs/game-host/game-host-internals.md:212`, `:689-706` |
| F11 | DRIFT | `test-harness.md` says filesystem/network calls are "blocked by the Game Host's context configuration" — the exact claim the spike disproved — and points at the wrong section | `docs/specs/gdk-api/test-harness.md:57-59` |
| F12 | DRIFT | Flow 03 says transport failures do **not** consume the retry budget; both owning documents say they do | `docs/specs/flows/03-game-turn.md:161`, `docs/specs/internal-grpc/orchestration-gamehost-protocol.md:245` |
| F13 | DRIFT | Flow 03 calls the RPC `SubmitInput` and gives `onAction` three parameters | `docs/specs/flows/03-game-turn.md:70`, `:74` |
| F14 | DRIFT | `NFR-REL-002` means two different things in two requirement docs, unqualified — while the identical `FR-SESS-003` collision *is* qualified twice | `docs/requirements/game-contracts.md:173`, `docs/requirements/platform-architecture.md:223` |
| F15 | DRIFT | The GDK's flagship example violates the determinism rule stated 60 lines above it | `docs/specs/gdk-api/backend-gdk-api.md:598`, `:532` |
| F16 | DRIFT | Opaque-payload byte encoding (UTF-8 JSON) is stated only in the internals spec; the proto's payload fields say only "opaque" | `docs/specs/internal-grpc/gamehost.proto:180`, `docs/specs/game-host/game-host-internals.md:150` |
| F17 | NIT | `TerminateSession`'s proto comment names a caller that does not exist and omits the normative idempotency guarantee | `docs/specs/internal-grpc/gamehost.proto:67-70` |
| F18 | NIT | Stale index/package-table entries | `docs/specs/game-host/INDEX.md:48`, `docs/specs/gdk-api/backend-gdk-api.md:59-61` |

---

## Findings

### F1 — BLOCKER — Two documents claim to write `session:{sessionId}`, and the Game Host's create-idempotency guard reads it

**Where:** `docs/specs/flows/02-room-to-game-start.md:115`,
`docs/specs/game-host/game-host-internals.md:647` and `:392-398`,
`docs/requirements/platform-architecture.md:130`,
`docs/decisions/0010-session-teardown-ordering.md:53`

**Quotes:**

> "| 6 | Monolith | Allocate `sessionId`; **write the session record and routing keys to Redis** | **Redis session keys** |" (flow 02:115)

> "| `session:{sessionId}` | hash/json | **Game Host** | the atomic session record (§8.1). Deleted on terminate." (game-host-internals:647)

> "1. If session:{id} already exists in Redis → return its lastEffects with OK
>    (do NOT re-run onInit).                                   ← idempotent create" (game-host-internals:393-394)

> "FR-ORCH-001 | Session creation | When the Room Service signals a game start, the Orchestration Service must **create a session record**, select a Game Host instance …" (platform-architecture:130)

> "`CreateSession` is idempotent on the existence of the session record, so a reused id whose record had leaked would **silently resume the finished game** instead of starting a new one." (ADR-0010:53)

**Blocks:** `GameStartService.startGame()` in the Platform Monolith (the pre-`CreateSession` Redis
write), and `GameHostServiceImpl.createSession()` in the Game Host (the idempotency guard). Also the
Redis key-ownership constants shared by both.

**Scenario:** Alice presses **Start Game**. The Monolith, following flow 02 step 6 and FR-ORCH-001,
allocates `sessionId` and writes `session:{sessionId}` alongside `routing:`/`queue:`/`seq:`. It then
calls `CreateSession`. The Game Host executes §9.1 step 1, finds the key present, and returns
`ProcessResult(sequence=0, OK, effects=[])` **without instantiating the game, without invoking
`onInit`, and without ever creating a state**. The Monolith sees `OK`, sets `room.state='IN_PROGRESS'`
(flow 02:118) and broadcasts `GAME_STARTED`. Every client then sends `REQUEST_GAME_SYNC`, the Game
Host has no session in memory, loads the (Orchestration-shaped, stateless) record from Redis, and
either `NOT_FOUND`s or resyncs against a `stateJson` that was never written. Every game start on the
platform is broken, and it is broken *silently* — the create returns `OK`.

The flows INDEX's tie-break rule ("the component document wins") does not rescue this, because the
second voice is `FR-ORCH-001`, a **Must requirement** that uses the same phrase "session record" for
an Orchestration-created artifact. Nothing in the corpus defines the term to mean only
`session:{sessionId}`, and `game-host-internals.md` §8 titles it "the **shared** Redis session record
… **co-owned** by both services" (:44, :340, :350), which reads as licence for either side to write it.

**Suggested resolution:** `game-host-internals.md` §8.1/§13 should own the fix and state the writer
exclusively and negatively: *"`session:{sessionId}` is written **only** by the Game Host. The
Orchestration Service must never create it; its existence is the sole signal that `onInit` has already
run."* Then rename the Orchestration-side artifact in `flow 02:115` and `FR-ORCH-001` to something
that cannot collide (e.g. "session routing entry"), and note in `platform-architecture.md` that
FR-ORCH-001's "session record" means the `routing:`/`queue:`/`seq:` family of §13, not `session:`.

---

### F2 — BLOCKER — Failed inputs: `lastAppliedSequence` both does and does not advance, and the record cannot represent a failure either way

**Where:** `docs/specs/internal-grpc/orchestration-gamehost-protocol.md:269-271`,
`docs/specs/game-host/game-host-internals.md:404-412` and `:355-362`

**Quotes:**

> "| Does `lastAppliedSequence` advance? | **Yes**, to the failed input's sequence. A redelivery of the same sequence must be a replay returning the same failure, not a second invocation of a handler that has already run and thrown |" (protocol doc:271)

> "1. If input.sequence  ≤ record.lastAppliedSequence → REPLAY record.lastEffects
>    with OK; do NOT invoke the handler.               ← at-most-once application" (game-host-internals:404-405)

> "6. On failure: return ProcessResult(sequence, FAILED, failure) — **state unchanged**." (game-host-internals:412)

> ```jsonc
> {
>   "contextKey":          { … },
>   "stateJson":           "…",
>   "lastAppliedSequence": 42,
>   "lastEffects":         [ … ]
> }
> ``` (game-host-internals:356-362 — no failure field)

**Blocks:** `GameHostServiceImpl.processInput()` — specifically the branch at the top of the method
and the Redis write in the commit path — and `SessionRecord` (the Redis DTO/Lua script).

**Scenario:** Two defects, and the second survives whichever document you pick.

*Defect A (the contradiction).* Sequence 43 arrives; `onAction` throws. Under the protocol doc the host
writes `lastAppliedSequence = 43`; under `game-host-internals.md` §9.1 step 6 it writes nothing at all
(the atomic write is step 5, reached only "On OK"). Now the Game Host pod dies and the
platform re-dispatches 43 from the queue (§9.3: "the in-flight action … is still in the queue").
Implementation A replays; implementation B re-invokes the handler. For a `player_left` re-driven from
the durable outbox — which reuses the same sequence forever (`data-model.md` §4.2) — implementation B
re-invokes on every single retry, which is exactly the double-apply GAME-B2 was closed to prevent.

*Defect B (the hole neither document closes).* Take the protocol doc's rule and follow it. The record
now says `lastAppliedSequence = 43`, but `lastEffects` still holds **sequence 42's** effects, because
there is no field in §8.1 for a failure and step 6 produced no effects. Sequence 43 is re-dispatched.
§9.1 step 1 fires: `43 ≤ 43` → "REPLAY record.lastEffects **with OK**". The host answers
`ProcessResult(43, OK, <sequence 42's effect list>)`. Orchestration compares `43 > delivered(=42)`,
fans the effects out a second time to every player, advances `delivered = 43`, and resets
`failcount:{sessionId}` to zero because it saw an `OK` (§9.4: "reset on any `OK`"). A failed action is
laundered into a success, the previous turn's broadcast is delivered twice, and the retry limit that
was supposed to catch a persistently-broken game is disarmed by the very failure it counts.

**Suggested resolution:** `game-host-internals.md` §8.1 must own this — it owns the record schema. Add
a `lastResult` discriminator to the atomic record (`{status: OK|FAILED, failure: {kind, message}}`
alongside `lastEffects`), make the §9.1 step-6 write atomic and mandatory on failure (advancing
`lastAppliedSequence`, leaving `stateJson` untouched), and change step 1 to replay the *recorded
status* rather than an unconditional `OK`. Then correct §9.1 step 6's "state unchanged" to "state
unchanged, **record advanced**" so it stops reading as "no write". The protocol doc's GAME-I3 table is
already correct and should be cited as the authority.

---

### F3 — BLOCKER — The proto orders a defensive rejection that the prose makes catastrophic

**Where:** `docs/specs/internal-grpc/gamehost.proto:39-40` and `:159-167`,
`docs/specs/internal-grpc/orchestration-gamehost-protocol.md:270`,
`docs/specs/api-design/websocket.md:383`

**Quotes:**

> "// Per-session ordering is enforced by the Orchestration Service's Redis-backed
> // queue (FR-ROUTE-002), NOT by the transport. The Game Host still **rejects
> // out-of-order/duplicate sequences defensively** (see ProcessInputRequest.sequence)." (proto:38-40)

> "| Is the `sequence` consumed? | **Yes.** It is burned. The game stream is deliberately sparse … and a hole carries no information, so no client notices |" (protocol doc:270)

> "The failed input is **dropped, not re-dispatched**, and its sequence is consumed" (websocket.md:383)

**Blocks:** the sequence-validation guard at the head of `GameHostServiceImpl.processInput()`.

**Scenario:** "Rejects out-of-order sequences" has exactly one natural implementation:
`if (seq != lastApplied + 1) reject`. The prose then guarantees that condition is violated in normal
operation. Bob submits an action at sequence 43; `onAction` throws; 43 is burned. Carol submits the
next action, which is allocated sequence 44. `lastApplied` is 42 (or 43, per F2 — either way there is
a hole the moment two inputs fail, or one fails under the `game-host-internals.md` reading). The host
rejects 44 as out-of-order. Orchestration counts a failure, dispatches 45, which is rejected too.
Three rejections and `TerminateSession(RETRY_LIMIT)` kills a perfectly healthy game whose only sin was
one bad click. This is a codegen-follows-the-proto / humans-follow-the-prose split of exactly the kind
the brief flags: the field-level comment at :163-166 is correct ("applies each sequence at most once
and replays the cached result for a duplicate") and the service-level comment three screens above it
is not.

Note that `game-host-internals.md` §9.1 does not adjudicate: it specifies the `≤ lastApplied` branch
and an unconditional else, and never mentions a forward gap at all. So the proto comment is the only
statement in the corpus about gaps, and it is wrong.

**Suggested resolution:** `gamehost.proto` owns it. Replace "rejects out-of-order/duplicate sequences
defensively" with "replays any sequence at or below `lastAppliedSequence`; **forward gaps are normal**
(a failed input burns its sequence) and must be applied, not rejected." Add the same sentence as an
explicit third branch in `game-host-internals.md` §9.1 so the internals spec states it rather than
implying it.

---

### F4 — BLOCKER — `send_to_player` is delivered to a principal with no check that the principal is in the session

**Where:** `docs/specs/api-design/websocket.md:133`, `:255`, `:261`, `:399-403`,
`docs/requirements/game-contracts.md:169` (NFR-SEC-002),
`docs/specs/game-host/game-host-internals.md:536-541`,
`docs/specs/internal-grpc/orchestration-gamehost-protocol.md:296-315`

**Quotes:**

> "| `sessionId` | The session the message belongs to. Required on every game message — **`/user/queue/game` is not session-scoped in its destination.** |" (websocket.md:133)

> "| `send_to_player` | `/user/queue/game` — **resolved by Spring from the target principal** | FR-EFF-002 |" (websocket.md:255)

> "a `send_to_player` payload rides a per-user queue whose destination **a client** cannot guess or subscribe to on another's behalf" (websocket.md:261)

> "NFR-SEC-002 | Security | Effect routing enforced server-side; `send_to_player` and `send_to_team` payloads are **never delivered to unauthorized recipients** | No client-side trust | **Must**" (game-contracts.md:169)

> "| `send_to_player` | the one `playerId` (never spectators/others) |" (game-host-internals:538)

**Blocks:** `EffectFanOutService.deliver(Effect, Session)` in the Orchestration domain — the branch
that turns a `SendToPlayerEffect` into `simpMessagingTemplate.convertAndSendToUser(playerId, "/queue/game", …)`.

**Scenario:** This is the answer to "a game returns an effect referencing a player who has left", and
the answer is that nothing is specified — but the sharper case is the one that also breaks a Must.

Take a game whose `onPlayerLeft` handler has an off-by-one and re-emits `Effects.sendToPlayer(departed.id(), hand)`
after the player is gone. That player is still logged into TurnBase, sitting in another room, with a
live WebSocket and a `/user/queue/game` subscription for *their own* session. Spring resolves the user
destination from the principal — which is a platform-wide identity, not a session membership — and
delivers a `GAME_EVENT` carrying another game's opaque payload into their client. The `sessionId`
field on the envelope (:133) exists precisely because the queue is not session-scoped, so the *client*
could filter — but making that the defence means NFR-SEC-002's "no client-side trust" is satisfied by
client-side trust.

Now generalise the `playerId` from "someone who left" to "any UUID the game chooses". Nothing between
the guest bridge and Spring validates it. The three checks that exist all guard the wrong direction:
the channel guards at :399-403 authorize *subscribers*, the team-topic membership check makes
`send_to_team` safe by construction (a bogus `teamId` topic has no subscribers), and `game-host-internals.md`
§10's table asserts the routing rule without specifying who enforces it. Note that the corpus already
does this validation for the *other* game-supplied identity: the `GameOutcome` table at protocol
doc:296-315 checks "`playerResults` player ids | every id is a participant of this session". The
effect path has no equivalent. Under ADR-0006 the MVP's games are first-party, which makes this a bug
class rather than an attack — but the fail-open is not labelled as ADR-0006-dependent anywhere, and
`websocket.md:379` explicitly reasons about game code as untrusted elsewhere in the same document.

**Suggested resolution:** `websocket.md` § Game Session Protocol should own it, since it owns the
destination mapping. Add to the `GAME_EVENT` routing table: *"Before delivery, the Orchestration
Service resolves `player_id` against the session roster. An effect naming a non-participant is
**dropped** and logged at WARN with `sessionId` and `gameId`; it is not a `GameFailure` (the turn
succeeded) and does not count toward the retry limit."* Mirror the same rule for `send_to_team`'s
`team_id` for symmetry, and cross-reference it from `game-host-internals.md` §10's table so the
fan-out implementer sees it.

---

### F5 — AMBIGUITY — `CreateSession` has no failure branch

**Where:** `docs/specs/flows/02-room-to-game-start.md:116-119`,
`docs/specs/game-host/game-host-internals.md:390-399`,
`docs/specs/internal-grpc/orchestration-gamehost-protocol.md:248`

**Quotes:**

> "| 9 | Monolith | **On OK:** under the room lock, `room.state='IN_PROGRESS'`, `room.active_session_id=sessionId`, `version++`, commit |" (flow 02:118)

> "**`CreateSession` (idempotent — closes the GAME-B2 create hole):** 1 … 2 … 3. **On OK:** atomically write session record … 4. Return ProcessResult(sequence = 0, OK, effects)." (game-host-internals:390-398)

> "| `FAILED_PRECONDITION` | Context could not be loaded for the session | **Fail the session** |" (protocol doc:248)

**Blocks:** the `catch`/else arm of `GameStartService.startGame()` — the one that has to decide what
the room's state is when `CreateSession` does not return `OK`.

**Scenario:** An official game's `onInit` throws (a null manifest parameter it forgot to default, say),
or the entry class is missing and the host answers `FAILED_PRECONDITION` with `CODE_LOAD_ERROR`. Both
documents describe only the `OK` path. The three plausible readings an implementer will pick from:

1. *Leave the room in Lobby and unicast an error to the host.* Correct, but there is no error type for
   it — `START_CONDITIONS_NOT_MET` (flow 02:113) is a precondition list, not a backend fault.
2. *Apply FR-FAIL-001*: drop the input, notify the acting player, count one failure. But there is no
   acting player at create (F7), and "drop the input" leaves the room in whatever state step 9 left it.
3. *Apply FR-FAIL-005 / `SESSION_FAILED`.* That requirement is scoped to "when a session is permanently
   failed (**after retry limit**)" (platform-architecture:189), and one `FAILED_PRECONDITION` is not
   three consecutive failures.

Worse, per F1's step 6 the Monolith has already written Redis keys under `sessionId`. If it takes
reading 1 and returns to Lobby without cleaning up, `routing:`/`seq:`/`queue:` leak for 24h (the TTL
backstop at game-host-internals:648-652) and the reconciliation sweep (FR-JOB-007) has to collect them.
If it takes reading 3, the room goes to Lobby anyway but by a path that also emits `SESSION_FAILED` on
a `/topic/game.{sessionId}` nobody has subscribed to yet.

**Suggested resolution:** `game-host-internals.md` §9.1 should own it, next to the `CreateSession`
flow, because it already owns the terminal-cleanup key list. Specify: a non-`OK` `CreateSession`
leaves the room in **Lobby** (never `IN_PROGRESS`), deletes the Orchestration key family for the
abandoned `sessionId`, allocates a fresh `sessionId` on the next attempt (required by ADR-0010 §2
anyway), does **not** enter the consecutive-failure counter (there is no session to fail), and
unicasts a distinct `GAME_START_FAILED` to the host carrying the `GameFailureKind` but not the message
(same redaction rule as `ACTION_REJECTED`). `websocket.md`'s command catalogue would need the new
error type.

---

### F6 — AMBIGUITY — "only counts toward the limit if reassignment cannot make progress"

**Where:** `docs/specs/game-host/game-host-internals.md:526-527`,
`docs/specs/internal-grpc/orchestration-gamehost-protocol.md:292-294`,
`docs/requirements/platform-architecture.md:187`

**Quotes:**

> "`UNAVAILABLE` (host down) triggers **reassignment first** (§9.3) and **only counts toward the limit if reassignment cannot make progress**." (game-host-internals:526-527)

> "FR-FAIL-003's 'across container restarts or re-dispatches' refers to `UNAVAILABLE` and crash recovery (FR-FAIL-002/004) … **Those attempts count toward the same limit**" (protocol doc:292-294)

> "After **3 consecutive failures** for the same session (across container restarts or re-dispatches), the Orchestration Service permanently fails the session" (platform-architecture:187)

**Blocks:** `SessionDispatcher.onTransportFailure()` — the increment/skip decision on
`failcount:{sessionId}`.

**Scenario:** For the MVP there is exactly one Game Host instance (FR-SCALE-001, ADR-0001), so
"reassignment" resolves to the same pod every time. The pod is CrashLoopBackOff-ing. Every dispatch
returns `UNAVAILABLE`. Reassignment "makes progress" in the sense that it finds a host and dials it —
so under `game-host-internals.md`'s rule the counter never increments and the dispatcher retries
forever, holding the queue, the room, and the room's WebSocket subscriptions in limbo indefinitely.
Under the protocol doc's rule the session fails after three attempts and the room returns to Lobby.
Neither document bounds the retry count, the backoff, or defines the predicate. FR-FAIL-002 mentions
"exponential backoff" but no ceiling.

A second, opposite reading is just as available: "cannot make progress" = "no *other* healthy host
exists", which in a single-instance MVP is true on the first `UNAVAILABLE`, collapsing the rule to the
protocol doc's. Two competent implementers will land on opposite sides of "hangs forever" vs. "kills
the session on the first blip during a rolling restart".

**Suggested resolution:** `game-host-internals.md` §9.4 owns it. Replace the predicate with a number:
*"An `UNAVAILABLE` triggers reassignment and re-dispatch with exponential backoff, up to N attempts
(configurable, default 3, listed in §15). Each exhausted reassignment cycle increments
`failcount:{sessionId}` once — not each individual dial."* That reconciles with FR-FAIL-003's
"across container restarts or re-dispatches" and gives §15 a value it is currently missing.

---

### F7 — AMBIGUITY — The failure notification has no recipient for non-action inputs

**Where:** `docs/requirements/platform-architecture.md:185` (FR-FAIL-001),
`docs/specs/internal-grpc/orchestration-gamehost-protocol.md:272`,
`docs/specs/api-design/websocket.md:379`

**Quotes:**

> "The Orchestration Service **drops that input**, **notifies the acting player** that their action was rejected, and counts the failure toward FR-FAIL-003's limit." (FR-FAIL-001, platform-architecture:185)

> "| Is anybody told? | **Yes** … **The acting player** receives a unicast `ACTION_REJECTED` on `/user/queue/errors`" (protocol doc:272)

> "A frame that is admitted, enqueued, dispatched, and then fails inside the game handler … produces `ACTION_REJECTED` on `/user/queue/errors`" (websocket.md:379)

**Blocks:** `SessionDispatcher.onProcessFailed()` — resolving the notification target from the input
type.

**Scenario:** Three of the four things that go through `ProcessInput`/`CreateSession` have no acting
player. Bob's grace period expires. The outbox (`data-model.md` §4.2) drains a `player_left` under a
persisted sequence. The game's `onPlayerLeft` throws (a genuinely likely hook to get wrong — the
harness spec says so itself at `test-harness.md:129-130`). Under all three documents above, the input
is dropped and *nobody is told*, because the only specified recipient is an acting player who does not
exist here. The game's state now permanently believes Bob is present; the remaining players sit
waiting for a turn belonging to someone who left twenty minutes ago; the platform UI has already shown
`GAME_PLAYER_LEFT` (websocket.md:295-310, emitted at that input's sequence) so the humans and the game
backend now disagree about the roster with no mechanism to reconcile them.

The counter does eventually save it — the outbox re-drives, three consecutive failures, `SESSION_FAILED`
— but only if F2 is resolved in the direction where a replayed failure still reports `FAILED`. Under
the other resolution the replay returns `OK`, the counter *resets*, and the game is wedged forever.

**Suggested resolution:** the protocol doc's GAME-I3 table (§ *What happens to the input that failed*)
owns it, since that table exists precisely to enumerate this. Add a row: *"Which client is told?
`action` → the acting player, `ACTION_REJECTED`. `player_joined`/`player_left` → nobody individually;
the failure is session-wide and, because the game's roster is now divergent from the platform's, it is
**not** droppable — it terminates the session immediately with `SESSION_FAILED(GAME_ERROR)` rather than
counting toward the limit."* Update FR-FAIL-001 to scope its "notifies the acting player" clause to
action inputs.

---

### F8 — GAP — NFR-REL-001 was not carried through the FR-FAIL-001 reconciliation

**Where:** `docs/requirements/game-contracts.md:172` and `:84`,
`docs/specs/gdk-api/backend-gdk-api.md:540` and `:541`,
`docs/requirements/platform-architecture.md:185`

**Quotes:**

> "NFR-REL-001 | Reliability | If the game BE fails to respond to an input (crash, timeout, malformed output), **the platform terminates the game session and notifies all participants** | Graceful degradation | Must" (game-contracts.md:172)

> "| Exceptions terminate | A thrown exception fails the input; **after the retry limit** the session terminates (**NFR-REL-001**). | `HANDLER_EXCEPTION` |" (backend-gdk-api:540)

> "it does not count toward **the consecutive-failure limit (NFR-REL-001)**" (game-contracts.md:84, FR-RESP-005)

> "*(This requirement previously terminated the session on the first failure, contradicting FR-FAIL-003's 'after 3 consecutive failures' …)*" (platform-architecture:185)

**Blocks:** nothing directly — but it is the requirement an implementer greps for when writing
`SessionFailureHandler`, and it says the wrong thing.

**Scenario:** The brief asked me to verify the FR-FAIL-001 / FR-FAIL-003 reconciliation. **The
reconciliation itself is coherent**: FR-FAIL-001 (platform-architecture:185) now drops-and-counts,
FR-FAIL-003 sets the limit at 3 consecutive, the protocol doc's GAME-I3 table answers all four
sub-questions, `websocket.md:379-383` and `flow 03:159` agree. The defect is that the fix was applied
to `platform-architecture.md` only. `game-contracts.md` NFR-REL-001 still carries the original
terminate-on-first-failure text — and it is a **Must** in the document that game developers are told is
their integration specification (`game-contracts.md:40`). Two specs then cite it as if it had been
amended: `backend-gdk-api.md:540` reads NFR-REL-001 as "after the retry limit", and FR-RESP-005 at
`game-contracts.md:84` calls it "the consecutive-failure limit (NFR-REL-001)" — a limit NFR-REL-001
does not contain. An implementer who resolves the FR-FAIL-001 vs. NFR-REL-001 conflict by taking the
more conservative Must ships terminate-on-first-throw, which is precisely the defect the reconciliation
removed. `websocket.md:336` also cites NFR-REL-001 as the source of `SESSION_FAILED`'s
"could not be recovered" reason, which is a third reading again.

**Suggested resolution:** `game-contracts.md` owns it. Rewrite NFR-REL-001 to: *"If the game BE fails
to process an input, the platform drops that input and notifies the affected client; after
`platform-architecture.md` FR-FAIL-003's consecutive-failure limit the session is terminated and all
participants are notified."* Add the same struck-through parenthetical FR-FAIL-001 carries, so the
next reader knows it was deliberately changed.

---

### F9 — GAP — Nothing denies guest thread creation, and one document says something does

**Where:** `docs/specs/game-host/game-host-internals.md:198-216` (§4 table) and `:236-246` (§4.2 builder),
`docs/specs/gdk-api/test-harness.md:57-59` and `:174`,
`docs/reviews/2026-07-02-mvp-readiness/espresso-spike-results.md:25`,
`docs/requirements/game-contracts.md:156` (FR-PROC-003)

**Quotes:**

> ```
> Context.newBuilder("java")
>    .allowNativeAccess(true)
>    .option("java.JavaHome", …)
>    .option("java.ExitHost", "false")
>    .option("java.Classpath", …)
>    .allowHostAccess(HostAccess.NONE)
>    .allowHostClassLoading(false)
>    .allowCreateProcess(false)
>    .allowEnvironmentAccess(EnvironmentAccess.NONE)
>    .build();
> ``` (game-host-internals:236-246 — no `allowCreateThread`)

> "The host builder used the strictest polyglot lockdown: `allowHostAccess(NONE)`, `allowHostClassLoading(false)`, **`allowCreateThread(false)`**, `allowCreateProcess(false)`, `allowIO(IOAccess.NONE)`, `allowEnvironmentAccess(NONE)`." (spike results:25)

> "A game that calls `System.exit`, opens a socket, reads a file or **spawns a thread** will succeed locally and be **blocked by the Game Host's context configuration**" (test-harness.md:57-59)

> "| **Sandbox restrictions** | File, network, **thread** and `System.exit` calls succeed locally, **fail in the Game Host** (§2) |" (test-harness.md:174)

**Blocks:** `EspressoContextFactory.build(ContextKey)` — literally the builder chain an implementer
copy-pastes from §4.2.

**Scenario:** The §4 requirement→mechanism table (:206-216) is presented as "the authoritative mapping
the spec commits to" and has a row for every FR-CTX Must. There is no row for thread creation, and
FR-PROC-003 ("No game-initiated communication … All autonomous game behavior … must be managed
internally by the game BE, triggered by subsequent inputs", game-contracts.md:156) has no realization
row in §17's traceability table either. The polyglot default for `allowCreateThread` is `false`, so an
implementer who copies §4.2 verbatim probably gets the right behaviour by accident — but one who reads
the §4 table as exhaustive ("these are the controls; everything else is the container's job") and
adds `allowAllAccess`-style permissiveness while debugging a boot failure gets a guest that can spawn
threads. A spawned guest thread outlives the invocation, is not covered by the per-session
single-flight lock (§6.2), is not stopped by `Context.interrupt` in any way the spec describes, and
will still be running when the next session's handler is invoked in the same context — which breaks
the "hooks need not be thread-safe across sessions" promise at `backend-gdk-api.md:535`.

Meanwhile `test-harness.md` states twice, as a load-bearing reassurance to developers, that threads
"fail in the Game Host". Under ADR-0006 this is another trusted-code fail-open that is not labelled as
one.

**Suggested resolution:** `game-host-internals.md` §4 owns it. Add `.allowCreateThread(false)` to the
§4.2 builder (matching the spike configuration exactly, which is what "spike-locked" should mean) and
add a row to the §4 table: *"FR-PROC-003 no autonomous execution | Espresso | `allowCreateThread(false)`
| ✅ spike configuration"*. Then §17 gains its missing FR-PROC-003 entry.

---

### F10 — GAP — Host-JVM heap sizing against the cgroup limit is unspecified

**Where:** `docs/specs/game-host/game-host-internals.md:212`, `:218-222`, `:689-706` (§15),
`:507-508`, `docs/requirements/platform-architecture.md:87` (FR-CTX-007)

**Quotes:**

> "| **FR-CTX-007 per-context memory cap** | **Container** | pod cgroup memory limit (a *pod-wide* cap, not per-context …) | ❌ Espresso/CE lacks it |" (game-host-internals:212)

> "a runaway game trips the pod limit → **the pod restarts** → sessions recover from Redis, §9" (game-host-internals:219-220)

> "**Context crash / OOM (FR-FAIL-007, NFR-REL-001):** a context crash affects only its own sessions; other contexts continue. … Surfaced as `GAME_FAILURE_KIND_CONTEXT_CRASH`." (game-host-internals:506-508)

> §15 config table (:692-706) — lists handler timeout, escalation grace, idle timer, memory-pressure
> threshold, cache size, message ceiling, Redis window, heartbeat, retry limit, artifact backend,
> `java.JavaHome`. **No JVM heap setting.**

**Blocks:** the Game Host `Dockerfile` / Helm values — `-XX:MaxRAMPercentage` or `-Xmx` relative to
`resources.limits.memory`.

**Scenario:** This is the "allocates unboundedly" half of the brief's scenario 3, and the spec gives
two incompatible outcomes without saying which mechanism produces which. A guest allocating in a loop
consumes host-JVM heap (Espresso guest heaps are host heap). Two things can happen and the difference
is entirely a JVM flag nobody has specified:

- If `-Xmx` is set below the cgroup limit, the host JVM throws `OutOfMemoryError` inside the guest
  invocation. That is recoverable: it surfaces as a `PolyglotException`, maps to `CONTEXT_CRASH` per
  §12, other contexts survive (FR-FAIL-007, NFR-REL-001), and the room sees `SESSION_FAILED` after
  three. This is what §9.3's "Context crash / OOM" paragraph describes.
- If `-Xmx` is unset or ≥ the cgroup limit, the kernel OOM-killer takes the whole pod. Every session
  on the pod dies, not just the culprit's context — directly violating NFR-REL-001's "blast radius:
  one game version" — and recovery is the 30s lease-expiry path of §9.3. This is what §4's MVP
  consequence note describes ("the pod restarts").

Both are written as if they were the specified behaviour. The §15 configuration surface, which claims
"All tunable via env/config, never hard-coded", has no row for the one setting that decides between
them. There is also no memory-pressure interaction stated: §6.3's LRU eviction fires at "host memory
exceeds a configurable threshold" (default 80%), but 80% *of what* — the cgroup limit or the JVM heap
— is not said, and those differ by whatever the JVM's non-heap footprint is.

**Suggested resolution:** `game-host-internals.md` §15 owns it. Add two rows: `JVM max heap` (default
`-XX:MaxRAMPercentage=70`, explicitly *below* the cgroup limit so guest OOM is a recoverable
`CONTEXT_CRASH` and not a pod kill) and state that §6.3's pressure threshold is measured against the
JVM heap, not the cgroup. Then reword §4's MVP-consequence note so pod restart is the *backstop* for a
leak the JVM cap misses, not the primary FR-CTX-007 mechanism.

---

### F11 — DRIFT — The harness tells developers the sandbox blocks what the spike proved it does not

**Where:** `docs/specs/gdk-api/test-harness.md:57-59`,
`docs/specs/game-host/game-host-internals.md:210-211` and `:248-251`,
`docs/requirements/game-contracts.md:185` (CON-005),
`docs/reviews/2026-07-02-mvp-readiness/espresso-spike-results.md:40-41`

**Quotes:**

> "A game that calls `System.exit`, opens a socket, reads a file or spawns a thread will succeed locally and be **blocked by the Game Host's context configuration** (`../game-host/game-host-internals.md` **§7**)." (test-harness.md:57-59)

> "| **FR-CTX-004 no filesystem** | **Container** | … | **❌ Espresso leaks — container required** |" (game-host-internals:210)

> "`IOAccess.NONE` / `sandbox.MaxHeapMemory` are **not** relied upon as enforcement — the spike proved they do not interpose Espresso's native `java.io`/`java.net`" (game-host-internals:248-249)

> "| **FR-CTX-004 no filesystem** | ❌ **LEAK** | Guest read `/etc/passwd` and returned `root:x:0:0:...`. `IOAccess.NONE` did **not** block it. |" (spike results:40)

**Blocks:** the harness's startup warning text (`HarnessSandboxAuditor`), and — more importantly — a
developer's mental model of what the platform guarantees.

**Scenario:** Two errors in one sentence. First, the section pointer: §7 of `game-host-internals.md` is
"Game code loading & guest classpath"; the isolation mapping is §4. Second, and substantively: the
context configuration blocks `System.exit` (verified) and does not block filesystem or network
(verified LEAK, twice, on both CE and Oracle). Those come from the **container**, and per ADR-0001 the
local MVP has no gVisor and per the same §4.1 the network denial is a Kubernetes `NetworkPolicy` that
does not exist when a developer runs the stack in Docker Compose. So a developer reads
`test-harness.md`, ships a game that reads a config file, and finds it works in local K8s too.

This matters more than a normal cross-reference slip because `test-harness.md` §1 makes truthfulness
its stated design constraint — "A rule the harness enforces differently from the platform is worse
than a rule it does not enforce, because it teaches the developer something false" (:31-32) — and this
sentence is the document teaching something false.

**Suggested resolution:** `test-harness.md` owns it. Change §2 to: *"…will succeed locally. In
production the Game Host container blocks filesystem and network (`game-host-internals.md` §4.1 —
read-only rootfs, egress NetworkPolicy, gVisor); `System.exit` is contained by the Espresso context
itself (§4). Note that the container controls are **not** present in a local non-Kubernetes run, so
CON-005 remains a contract obligation on the author (ADR-0006)."* Fix §7 → §4, and align the §7 table
row at :174 the same way.

---

### F12 — DRIFT — Flow 03 exempts transport failures from the retry budget; both owning docs do not

**Where:** `docs/specs/flows/03-game-turn.md:159-161`,
`docs/specs/internal-grpc/orchestration-gamehost-protocol.md:245` and `:292-294`,
`docs/specs/game-host/game-host-internals.md:520-522`

**Quotes:**

> "| `DEADLINE_EXCEEDED` / `UNAVAILABLE` | Transport failure — infrastructure signal, not a game fault. Reassign or retry; **does not consume the game's retry budget** |" (flow 03:161)

> "| `DEADLINE_EXCEEDED` | Call exceeded the deadline … | **Treat as a processing failure; apply retry-limit semantics** |" (protocol doc:245)

> "incremented on any processing failure (transport **`DEADLINE_EXCEEDED`**/`RESOURCE_EXHAUSTED`, or in-band `PROCESS_STATUS_FAILED`)" (game-host-internals:520-522)

> "**Re-dispatch is the *other* path, and it also counts.** … **Those attempts count toward the same limit**" (protocol doc:292-294)

**Blocks:** the same `SessionDispatcher.onTransportFailure()` as F6.

**Scenario:** The flows INDEX tie-break ("the component document wins", `flows/INDEX.md:16-17`) makes
this formally resolvable, which is why it is DRIFT and not BLOCKER — but it is the highest-consequence
DRIFT in the slice, and the flow document is the one an implementation agent is most likely to read
first because it is the only end-to-end narrative.

Concretely, scenario 3 from the brief: a game with an infinite loop. The 30s watchdog fires
(`Context.interrupt`), the invocation ends with a `PolyglotException`, and the host returns in-band
`TIMEOUT` — so far so good. But the gRPC deadline is "the game timeout + overhead"
(protocol doc:245), and under load, or when the interrupt does not yield inside the 5s escalation
grace (§12) and the host is busy calling `Context.close(true)`, the *call* exceeds its deadline first
and Orchestration sees `DEADLINE_EXCEEDED` rather than an in-band failure. Under flow 03's rule that
never counts. The dispatcher re-dispatches, the loop runs again, deadline again, forever. The room
never sees `SESSION_FAILED`; it sees nothing at all. Under the protocol doc's rule the session dies
after three, which is the intended behaviour and the only one that terminates a runaway game.

Note flow 03:160 gets the adjacent case right ("Watchdog expires (30 s) … Treated as a processing
failure"), which is what makes :161 look deliberate rather than sloppy.

**Suggested resolution:** `flow 03` is the wrong document; fix it to match. Replace the row with:
*"`DEADLINE_EXCEEDED` — treated as a processing failure and counted (protocol doc, Error model).
`UNAVAILABLE` — reassign first; an exhausted reassignment cycle counts once (game-host-internals §9.4)."*
This also depends on F6 being resolved, since `game-host-internals.md`'s `UNAVAILABLE` rule is itself
underspecified.

---

### F13 — DRIFT — Flow 03 names an RPC and a hook signature that do not exist

**Where:** `docs/specs/flows/03-game-turn.md:70` and `:74`,
`docs/specs/internal-grpc/gamehost.proto:50`, `docs/specs/gdk-api/backend-gdk-api.md:97`

**Quotes:**

> "| 3 | Orchestration | gRPC **`SubmitInput`**`(sessionId, sequence=43, input)` |" (flow 03:70)

> "| 7 | Espresso | **`onAction(state, context, input)`** under a 30 s watchdog |" (flow 03:74)

> "rpc **ProcessInput**(ProcessInputRequest) returns (ProcessInputResponse);" (proto:50)

> "ActionResult<S> **onAction(S state, ActionContext ctx)**;" (backend-gdk-api:97)

**Blocks:** nothing structurally — but a low-effort agent generating a gRPC client stub or a GDK
fixture game from the flow narrative writes `SubmitInput` and a three-arg `onAction`, then discovers
the mismatch at compile time against generated code it did not write.

**Scenario:** The three-arg `onAction` is the more dangerous of the two, because it is *plausible* —
the action payload does have to get in somehow — and the correct answer (`ctx.action(Move.class)`,
backend-gdk-api:181) is not guessable from the flow. A fixture game written to the flow's signature
does not implement `TurnBaseGame` and fails `FR-LOAD-005`'s entry-class check with `CODE_LOAD_ERROR`,
which is a confusing symptom for a signature typo.

Related, same document: flow 02:116 writes `CreateSession(sessionId, gameId, version, roster, teams, parameters)`
— six arguments including a `roster` the proto's `CreateSessionRequest` does not have (it has
`session_id`, `context{game_id, game_version}`, `teams`, `parameters`; the roster *is* the teams).

**Suggested resolution:** `flows/03` and `flows/02` own it. `SubmitInput` → `ProcessInput`;
`onAction(state, context, input)` → `onAction(state, ctx)` with a parenthetical that the payload is
decoded via `ctx.action(Class)`; drop `roster` from the flow-02 `CreateSession` argument list.

---

### F14 — DRIFT — `NFR-REL-002` means two different things, unqualified

**Where:** `docs/requirements/game-contracts.md:173`, `docs/requirements/platform-architecture.md:223`,
`docs/specs/gdk-api/backend-gdk-api.md:536`, `docs/specs/game-host/game-host-internals.md:481`,
`docs/specs/internal-grpc/gamehost.proto:424-425`

**Quotes:**

> "NFR-REL-002 | Reliability | **Game BE processing timeout** — if the game BE does not respond within a platform-configured duration, the input is considered failed | Default: 30s | Must" (game-contracts.md:173)

> "NFR-REL-002 | Reliability | **Game Host container crashes must be detected** and affected sessions failed within a bounded time | < 30s detection | Must" (platform-architecture:223)

> "| Handler timeout | A hook must return within the configured budget (default **30 s**, NFR-REL-002). |" (backend-gdk-api:536)

> "**Game Host crash (FR-FAIL-002, NFR-REL-002 < 30 s):** the liveness lease (§11) expires …" (game-host-internals:481)

**Blocks:** nothing directly. It is a grep hazard, and both values happen to be 30 seconds, which is
what makes it easy to conflate.

**Scenario:** An implementer tuning the lease TTL greps `NFR-REL-002`, finds the handler-timeout
definition in `game-contracts.md`, and sets `lease_ttl_seconds` from the handler budget — or the
reverse. The two are coupled but not equal: the gRPC dispatch deadline is "game timeout + overhead"
(protocol doc:245, i.e. > 30s) while the lease TTL must be < 30s for NFR-REL-002-detection to hold,
so a single 30s constant fed to both makes crash detection fire during a legitimate slow turn.

The corpus already knows this hazard and handles it correctly elsewhere: the `FR-SESS-003` collision
between `platform-architecture.md` and `user-accounts.md` is explicitly qualified in **two** places
(`game-host-internals.md:344-347` and `protocol doc:110-111`). `NFR-REL-002` gets no such treatment.

**Suggested resolution:** apply the same qualifier the corpus already uses for `FR-SESS-003`. In
`game-host-internals.md` §9.3 and `backend-gdk-api.md` §9, write `game-contracts.md NFR-REL-002` and
`platform-architecture.md NFR-REL-002` explicitly, and add a one-line note in whichever document is
cited second, mirroring the FR-SESS-003 wording.

---

### F15 — DRIFT — The GDK's flagship example breaks the determinism rule on the same page

**Where:** `docs/specs/gdk-api/backend-gdk-api.md:598` and `:532`,
`docs/specs/gdk-api/test-harness.md:150-156`

**Quotes:**

> "| Pure function of inputs | A hook's output must depend only on `(state, context)`. **No mutable static state, no clocks, no randomness without a seed carried in state.** |" (backend-gdk-api:532)

> "var state = new GuessState(**new java.util.Random().nextInt(max) + 1**, 0);" (backend-gdk-api:598, inside `onInit` of the §11 "minimal example")

**Blocks:** the reference/fixture game an implementer writes first (the §16 integration test explicitly
calls for "a fixture game JAR"), and the harness's round-trip check.

**Scenario:** §11 is the copy-paste template for every first game, and NFR-DX-001's "first game in
under 2 hours" makes copying it the expected path. It seeds a `Random` from the system clock inside
`onInit`, which is a clock read and an unseeded randomness source — the two things :532 names. The
consequence is not theoretical: `CreateSession` is idempotent on the session record (§9.1 step 1) and
`onInit` is *not* re-run on replay, so today the impurity is masked. But the harness's round-trip
check (`test-harness.md:150-156`) runs `state.equals(back)` after every invocation, and the §16 unit
test for "`CreateSession` replay" has no stable expected value to assert against if the example is the
fixture. More importantly it teaches the exact anti-pattern the determinism table forbids, in the one
piece of code every developer will read.

**Suggested resolution:** `backend-gdk-api.md` §11 owns it. Either derive the secret from a seed the
platform already supplies deterministically (the parameters map, or a hash of `sessionId` if one is
exposed — it currently is not), or add the seed to `GuessState` and note in one line that the initial
seed must come from a parameter. A three-line comment pointing at §532 would also do; silently
shipping the violation is the only unacceptable option.

---

### F16 — DRIFT — Payload byte encoding is specified in one document and not in the one codegen reads

**Where:** `docs/specs/internal-grpc/gamehost.proto:180`, `:330`, `:335`, `:341`, `:356`,
`docs/specs/game-host/game-host-internals.md:148-150`

**Quotes:**

> "bytes payload = 2;      // **opaque, game-defined action payload**" (proto:180 — and identically at :330, :335, :341, :356)

> "Everything game-defined — `stateJson`, action `payloadJson`, effect payloads, `resultsPayload` — is an **opaque JSON string** the host copies verbatim into proto `bytes` (**UTF-8**)." (game-host-internals:148-150)

**Blocks:** the `Effect` envelope→proto mapper in the host shim, and the STOMP `payload` →
`ActionInput.payload` conversion in the Orchestration handler.

**Scenario:** The proto specifies the encoding for exactly two of its six `bytes` fields —
`parameters` ("Host-configured game parameters as **UTF-8 JSON**", :150) and `ResyncResponse.view`
("opaque, game-defined view payload for this viewer (**UTF-8 JSON**)", :239) — and leaves the other
four saying only "opaque". An implementer writing the inbound side has a `JsonNode` from a STOMP frame
and must choose: `mapper.writeValueAsBytes(node)` (UTF-8 JSON, correct) or some binary encoding, or
`toString().getBytes()` with the platform default charset. The last is the trap: on a JVM with a
non-UTF-8 default charset, a game payload containing a non-ASCII string (a chess piece glyph, a player
name in a game-defined payload) is mangled between the Monolith and the guest's Jackson parser, and
the symptom is an `ActionDecodeException` → `HANDLER_EXCEPTION` that looks like a game bug.

The rule *is* stated, in `game-host-internals.md` §3.3. But the proto is the artifact a codegen-driven
implementer works from, and the two fields that already carry the annotation make its absence on the
others look intentional.

**Suggested resolution:** `gamehost.proto` owns it. Append "UTF-8 JSON" to the four remaining payload
field comments (`ActionInput.payload`, `BroadcastEffect.payload`, `SendToPlayerEffect.payload`,
`SendToTeamEffect.payload`, `GameOverEffect.results_payload`), matching the wording already used on
`parameters` and `view`.

---

### F17 — NIT — `TerminateSession`'s proto comment names a caller that cannot exist and omits its normative guarantee

**Where:** `docs/specs/internal-grpc/gamehost.proto:67-70` and `:389-400`,
`docs/specs/internal-grpc/orchestration-gamehost-protocol.md:159-164`

**Quotes:**

> "// Force-terminate a session and free its local + Redis state. Used for **host kick** / room close and for permanent failure after the retry limit. (FR-SESS-005, FR-FAIL-005)" (proto:67-69)

> "// 1 reserved: was HOST_ENDED … **a host cannot kick themselves** (game-rooms.md FR-HOST-006 …), so a kicked-everyone room stays viable." (proto:392-395)

> "**`TerminateSession` is idempotent — normative.** Terminating a session the host does not hold, or has already terminated, is a **no-op success**, not an error." (protocol doc:159-160)

**Blocks:** nothing. Reported because the brief asked me to verify `TerminateSession` idempotency is
in the contract.

**Scenario:** The idempotency guarantee **is** properly normative — stated in the protocol doc at
:159-164 with its rationale (ADR-0010's re-drive), reinforced in the error-model table at :247
("`TerminateSession` returns `OK` for an unknown session"), restated in `game-host-internals.md`
:439-443, and depended upon by ADR-0010 and `data-model.md` §4's "`NOT_FOUND` response | **Success**".
Calling it twice for the same session is unambiguously a no-op success on every path. That checks out.

The two blemishes are on the proto side. (a) The RPC comment names "host kick" as a caller, but the
`reserved 1` comment forty lines below explains that a kick can never terminate a session, and
`TerminationReason` has no kick value — so a reader mapping callers to reasons finds one caller with
no reason. The four real callers are enumerated correctly in the protocol doc at :70-73. (b) The
comment does not mention idempotency at all, and a reader who only has the proto (the stated future
state: "the canonical `gamehost.proto` should move to a shared, versioned location", protocol doc:363-366)
would not know the guarantee exists.

**Suggested resolution:** `gamehost.proto` owns it. Replace "host kick / room close" with "room
closure (including grace-expiry closure), normal game end, retry-limit permanent failure, and the
reconciliation re-drive", and add one line: "**Idempotent:** terminating an unknown or already-torn-down
session returns OK, not NOT_FOUND. See the protocol doc — the ADR-0010 re-drive depends on it."

---

### F18 — NIT — Stale index and package-table entries

**Where:** `docs/specs/game-host/INDEX.md:48`, `docs/specs/gdk-api/backend-gdk-api.md:59-61`

**Quotes:**

> "the client-facing STOMP topics/envelope are the game-session WebSocket spec (GAME-B1, **planned**)." (game-host/INDEX.md:48)

> "| `io.turnbase.gdk.context` | `InitContext`, `ActionContext`, `PlayerJoinedContext`, `PlayerLeftContext`, `PlayerLeftReason` |
> | `io.turnbase.gdk.result` | `InitResult`, `ActionResult`, `PlayerJoinedResult`, `PlayerLeftResult` |" (backend-gdk-api:59-61)

**Blocks:** an implementer creating the SDK's package structure from the §2 table.

**Scenario:** (a) The game-session WebSocket spec is written — `game-host-internals.md:52` and `:576`
both link to it as existing. Only the INDEX still says "planned", which is the file a reader is
instructed to start from. (b) The §2 package-layout table omits `ResyncContext`, `ViewerRole` (both
defined in `io.turnbase.gdk.context` at :205-215) and `ViewResult` (defined in
`io.turnbase.gdk.result` at :453-462) — the entire `onResync` surface, which is the newest addition to
the API. Someone generating the module skeleton from the table produces an SDK that does not compile
against §3's `TurnBaseGame`.

Minor related: `GameParameters` is attributed to FR-GDK-011 at :254 but to FR-GDK-004 at :164, and the
§12 traceability table assigns FR-GDK-011 to "`Player`, `Team`, `GameParameters`" while
`orchestration-gamehost-protocol.md:89` uses FR-GDK-011 for `Team.name()`. Not worth chasing beyond
noting it.

**Suggested resolution:** one-line edits in each file. Drop "planned"; add the three missing types to
the package table.

---

## What checked out

Verified as consistent and implementable, with the evidence:

- **The Espresso boundary is copy-only, and all three documents that describe it agree.**
  `game-host-internals.md:112-113` ("It never touches game classes; it exchanges only **JSON strings,
  primitives, and byte arrays** with the guest"), the §3.3 call table at :136-144 (every signature is
  `String`/primitive in and `String` out), and the builder's `allowHostAccess(HostAccess.NONE)` +
  `allowHostClassLoading(false)` at :241-242. No host object is reachable from the guest and no guest
  object escapes to the host except an opaque `Value` handle to the bridge entrypoint. There is no
  shared mutable object across the trust boundary anywhere in the design. The one place a shared
  object could appear — `onResync` being handed the same state instance as `onAction` — is closed by
  canonical-state-as-JSON (§8) deserializing per invocation, and the residual risk if OQ-4's live-object
  cache is ever added is already recorded as OQ-4.

- **Scenario 1 (marshalling a game state type the platform has never seen) is fully answerable from the
  documents.** `game-host-internals.md:127-130` puts Jackson guest-side inside the bridge, so it
  reflects over classes that exist only on the guest classpath; the host handles `stateJson` as an
  opaque string; `backend-gdk-api.md` §5.1 (:296-321) states the five normative constraints on a state
  type and why each one is a Jackson-configuration consequence; `bundle-format.md` §4 checks three of
  them statically at upload and `test-harness.md` §6 executes the real round trip. The hops are:
  STOMP JSON → `ActionInput.payload` bytes → guest `payloadJson` string → `ctx.action(Class)` →
  developer type; and back: result state object → `stateJson` → Redis / host memory (never the wire,
  FR-RESP-001a). Every hop names its type. The only defect is F16's missing charset annotation.

- **Scenario 4 (double `TerminateSession`) is correct and normative, not incidental.** Covered under
  F17 above — idempotency is asserted in the protocol doc as normative with a stated reason, echoed in
  `game-host-internals.md:439-443`, carved out of the `NOT_FOUND` rule in the error-model table at
  :247, and *depended upon* by ADR-0010's indefinite re-drive and `data-model.md` §4's
  "`NOT_FOUND` response | Success" column. Additionally, the no-single-flight-lock rule
  (protocol doc:166-172, game-host-internals:446-449) and the explicit prohibition on implementing
  terminate with `Context.interrupt` (context-scoped, would hit siblings) are both stated in both
  documents identically. This is the best-specified interaction in the slice.

- **Scenario 6 (state persistence and Game Host restart) is coherent and the two sides agree.**
  What is persisted: the atomic record `{contextKey, stateJson, lastAppliedSequence, lastEffects}`
  (:355-362). When: after every successful invocation, before the `OK` (§9.1 step 5, FR-FAIL-006). By
  whom: the Game Host (§13, modulo F1's naming collision). On restart: the record is loaded from Redis
  (§9.1 step 2), the context and instance are recreated, and no history replay is needed because the
  instance is stateless. The platform side agrees requirement-for-requirement — FR-SESS-003a
  (persist), FR-SESS-003b (recover), FR-FAIL-004 ("The only state loss is an in-flight action …
  re-dispatched from the queue"), FR-FAIL-007 (context crash blast radius). The atomicity requirement
  at :371-374 is stated as a Lua-or-MULTI/EXEC MUST with the torn-write failure named. The accepted
  loss window (single in-flight action on Redis-node loss, §8.2) is stated rather than assumed. The
  session is **recoverable, not lost** — subject only to F2, which is about the *failure* path, not
  the crash path.

- **Scenario 7 (GDK 1.0 game on a host shipping 1.1) is fully specified, in `bundle-format.md` §6.**
  What is checked: `manifest.gdkApiVersion` against a closed interval. Where: three places — upload
  stage E5 (fatal, with distinguished below-range and above-range messages), monolith startup (the
  configured `turnbase.gdk.supported-range` is asserted against the guest bridge JAR's own manifest
  version and startup fails on mismatch), and room creation (422 naming the game). Why the range is
  derived rather than configured: "it is a fact about a deployed artifact" — exactly one GDK version
  is on the guest classpath. For 1.0-on-1.1 specifically the range is `[1.0.0, 1.1.z]` per
  NFR-COMPAT-001, so the game runs. §6.3 even handles the case the brief's scenario implies but does
  not ask — a range that moves past an already-live game — with the `game_version_gdk_idx` sweep as a
  deploy gate that reports and never mutates catalog state, and reasons explicitly about why mutation
  would break rollback. I found nothing to add.

- **The FR-FAIL-001 / FR-FAIL-003 reconciliation is substantively coherent.** FR-FAIL-001 now
  drops-and-counts (platform-architecture:185, with a struck-through note explaining what changed);
  FR-FAIL-003 keeps the 3-consecutive limit; the protocol doc's GAME-I3 table (:261-294) answers all
  four sub-questions explicitly and reasons about why each matters; `websocket.md:379-383` and
  `flow 03:159` carry the same story client-side. The **acting player is accounted for** on the action
  path (`ACTION_REJECTED` on `/user/queue/errors`, kind but never message, with the redaction rationale
  at protocol doc:274-278). The **failed input is accounted for** (dropped, not re-dispatched; sequence
  burned; the sparse-stream argument for why the hole is invisible). The consecutive-reset semantics
  are stated and tied to `failcount:{sessionId}`'s deletion in `terminateAndCleanup`. The three gaps
  are F2 (the record cannot represent the failure it must replay), F7 (no recipient for non-action
  inputs), and F8 (NFR-REL-001 not carried through) — none of which undo the reconciliation itself.

- **The `Resync` read-only path is airtight across four documents.** The property table at
  protocol doc:211-220 enumerates six dimensions (sequence, queue, record write, `lastAppliedSequence`,
  watermark, audience, retry-limit) and `game-host-internals.md:419-436` restates all of them
  identically; the proto comment at :52-64 says the same; `backend-gdk-api.md:541` carries the
  read-only constraint into the developer contract with the right failure scoping (fails only that
  viewer's attach, never counted). The `as_of_sequence` race-freedom argument is given in three places
  and is the same argument each time (`websocket.md:188-195`, `flow 03:133-142`, protocol doc:222-227).
  The single-flight lock is correctly shared with `ProcessInput` and correctly *not* shared with
  `TerminateSession`.

- **`gamehost.proto` and `orchestration-gamehost-protocol.md` agree field-for-field** on every message
  I diffed: `PlayerRef`/`Team`/`ContextKey`, `CreateSessionRequest` (4 fields), `ProcessInputRequest`
  (the `oneof` and its three inputs), `PlayerLeftReason` (3 values + UNSPECIFIED, matching
  `game-contracts.md` FR-IN-005 and `backend-gdk-api.md`'s enum exactly), `ResyncRequest`/`ResyncResponse`,
  `ProcessResult`, `GameFailureKind` (7 values, all 7 mapped in `game-host-internals.md` §12's table),
  the `Effect` oneof (5 variants, matching FR-EFF-001…005, the GDK's sealed hierarchy, and the §3.3
  envelope's five `type` strings), `GameOutcome`/`TeamResult`/`PlayerResult`, `TerminationReason`
  (3 values + reserved 1, with the reservation reasoned), and all four registry messages. The GDK→proto
  mapping table at `backend-gdk-api.md:556-568` is correct in both directions. The only proto/prose
  divergences I found are F3 (substantive) and F16/F17 (comment-level).

- **`FR-DELIVER-005`, `FR-DELIVER-006`, `FR-ROUTE-005`, `FR-PROC-002` and `FR-RESP-001` are uncited but
  substantively realized.** I checked each: FR-DELIVER-005's catch-up-on-attach is `websocket.md`'s
  sync flow (:153-203) plus `game-host-internals.md` §10's log-retention paragraph, including the
  "no effect journal" claim verbatim; FR-DELIVER-006's affinity is `game-host-internals.md:577-579`
  ("session affinity follows room affinity (ADR-0002)") and the ADR-0008 adoption paragraph at :494-503;
  FR-ROUTE-005 is the existence of the proto; FR-PROC-002 is FR-ROUTE-001's Redis FIFO (§9.2); FR-RESP-001
  is the GDK result types (§7). These are citation gaps, not specification gaps — worth adding to the
  §17 traceability table but not blocking.

- **`FR-SCALE-002/004/005`, `NFR-PERF-004`, `NFR-SCALE-002` are uncited and correctly so for the MVP.**
  `platform-architecture.md:13-15` scopes "Scaling & startup budgets (`FR-SCALE-*`)" to post-MVP under
  ADR-0001, and `game-host-internals.md:599-601` states the registry machinery exists but is "trivially
  satisfied" at one instance. NFR-SCALE-002 (200 concurrent titles) is a `Should` that depends on the
  per-context overhead benchmark still open as OQ-1/spike OQ-001 — appropriately deferred rather than
  missing. NFR-PERF-004 (<50ms effect delivery) genuinely has no spec home, but `flow 03:120-122`
  argues the equivalent NFR-PERF-002 budget is met by in-process fan-out, which covers it in substance.

- **`FR-OUTCOME-002` is realized but its emptiness rule is unstated.** The proto has
  `repeated PlayerResult player_results = 2` and the GDK has the matching builder method. FR-OUTCOME-002
  says the outcome "**must** include a `playerResults` array", while the validation table at
  protocol doc:308-315 requires `teamResults` non-empty and says nothing about `playerResults` presence
  — and `flow 06:33` lists only "empty `teamResults`" as a structural invalidity. A game returning
  `playerResults: []` therefore passes validation and writes a completion row with no history entries,
  which is *also* the specified behaviour for an all-guest session (`flow 06:70-74`). The two are
  indistinguishable downstream. Not worth a finding on its own — the history/statistics slice owns the
  consequence — but flagging it here since FR-OUTCOME-002 was on the brief's list.

- **ADR-0006 fail-opens are, with two exceptions, correctly labelled.** `game-host-internals.md:56-61`
  states the trust posture up front and justifies every control as "robustness against a *buggy* game
  plus defense-in-depth, *not* an adversarial boundary"; the §4 table marks each leaked control with
  ❌ and names the container as the enforcer; §12's interrupt blast-radius caveat is explicitly
  "owner-accepted … because timeouts are rare bugs in trusted code"; `game-contracts.md` CON-005 and
  `backend-gdk-api.md:533` both carry the "contract obligation, enforced at the container layer, not
  an in-JVM sandbox" wording. The two unlabelled ones are **F4** (effect recipient validation, which
  is safe only because the games are first-party, and is not marked as such — and `websocket.md:379`
  reasons about game code as untrusted in the same document) and **F9** (thread creation, where the
  harness affirmatively claims an enforcement that does not exist).
