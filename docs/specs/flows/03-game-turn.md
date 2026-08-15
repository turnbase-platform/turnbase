# Flow 03 — One Game Turn

Bob submits a move. It reaches guest Java inside an Espresso context and comes back as effects that
fan out to four different audiences with four different views. This is the hot path — everything
here runs on every action of every game.

**Components:** browser (platform shell + game iframe), Platform Monolith, Redis, Game Host,
Espresso guest context.

---

## The cast

| Party | Sees |
|---|---|
| Bob (acting player, Team A) | `broadcast`, his own `send_to_player`, Team A's `send_to_team` |
| Carol (Team A) | `broadcast`, her own `send_to_player`, Team A's `send_to_team` |
| Dave (Team B) | `broadcast`, his own `send_to_player`, Team B's `send_to_team` |
| Erin (spectator) | `broadcast` **only** |

---

## A. From the game iframe to the socket

| # | Actor | Action |
|---|---|---|
| 1 | Game FE | `postMessage({type:"action", payload})` to the parent shell |
| 2 | Shell | **Validates `event.origin` against the exact game origin** it computed from `gameFrontendUrl` — never `*`, never a substring match. Rejects anything else silently |
| 3 | Shell | `SEND /app/game.{sessionId}.action` `{type:"SUBMIT_ACTION", payload}` |

Step 2 is the browser-side half of the trust boundary. The game frontend is untrusted code on a
different registrable domain; the shell is the only thing between it and an authenticated socket. A
shell that accepts `*` hands every game the ability to act as its player.

The relay is deliberately thin: the shell does not interpret `payload`, and the platform does not
either — game state is opaque to it (`NFR-SEC-003`).

---

## B. Admission

| # | Component | Check | On failure |
|---|---|---|---|
| 1 | STOMP interceptor | `action` bucket: 5/s, burst 10 | Drop; on repeat, close; on persistent abuse, a Redis reconnect lockout (30 s, doubling, capped 15 m) |
| 2 | STOMP interceptor | `connection` bucket: 10/s, burst 30 — backstop over *every* frame | as above |
| 3 | Channel guard | Bob is an **active, non-spectator player of an active session** | Error on `/user/queue/errors` |
| 4 | Handler | Re-check under the session lock: session not terminated, not past `game_over` | Error |
| 5 | Handler | Input validation: envelope shape, size ceiling | `400`-equivalent error frame |

**Rate limiting here is pod-local, not Redis-backed**, and that is not an approximation. Room
affinity ([ADR-0002](../../decisions/0002-websocket-room-affinity.md)) pins every frame a user sends
about a room to that room's instance, so an in-JVM bucket keyed by principal observes that user's
*entire* frame stream for this room. It is exact. Redis would put a network round trip on the inbound
path of every action to buy nothing.

**The error emission is itself throttled** (1 per bucket per second). Without that, a client sending
1 000 frames/s draws 1 000 unicast error frames/s and the abuse control becomes the amplifier.

Spectators are rejected at step 3, by the destination's own authorization rule rather than by a check
inside the handler — `FR-DELIVER-002`'s filtering is not the only thing keeping them out.

---

## C. Sequence allocation and dispatch

| # | Component | Action | State |
|---|---|---|---|
| 1 | Orchestration | `INCR seq:{sessionId}` → `sequence = 43` | **Redis** |
| 2 | Orchestration | Enqueue the input on the session queue | **Redis** |
| 3 | Orchestration | gRPC `SubmitInput(sessionId, sequence=43, input)` | — |
| 4 | Game Host | `sequence <= lastAppliedSequence` → **replay**: return the retained result, do not re-invoke | — |
| 5 | Game Host | Otherwise acquire the session's **single-flight lock** | — |
| 6 | Game Host | GDK Host deserializes the input across the Espresso boundary | — |
| 7 | Espresso | `onAction(state, context, input)` under a 30 s watchdog (`FR-CTX-008`) | guest heap |
| 8 | Game Host | Serializes the result: new state + ordered effect list | Redis session record |
| 9 | Game Host | `lastAppliedSequence = 43`; returns the effect list | **Redis** |

**The sequence is allocated before dispatch, and that is what makes redelivery safe.** The Game Host
deduplicates on `sequence`, so a retry of step 3 with the same number is recognised as a replay
rather than applied twice. An input that acquired a fresh sequence on every attempt would be applied
twice and the replay path would never engage.

**Step 5's lock is per session, not per instance.** One game's slow turn cannot block another's, but
within a session inputs are strictly serial — which is what `FR-RESP-004`'s effect-ordering guarantee
means in practice and why `REQUEST_GAME_SYNC` is the most expensive frame a client can send: it
re-enters the guest VM under this same lock.

**State never crosses the gRPC boundary.** The Game Host returns effects; the state stays in its
Redis session record. The platform could not interpret it if it received it.

---

## D. Fan-out

The game returns, in order:

```
[0] broadcast          "Bob played the 7 of hearts"
[1] send_to_player     → Bob   (his new hand)
[2] send_to_team       → Team A (a shared signal)
[3] log                "Bob plays 7♥"
```

| index | Destination | Reaches |
|---|---|---|
| 0 | `/topic/game.{sessionId}` | Bob, Carol, Dave, **Erin** |
| 1 | `/user/queue/game` | Bob |
| 2 | `/topic/game.{sessionId}.team.{teamA}` | Bob, Carol |
| 3 | `/topic/game.{sessionId}` as `GAME_LOG` | everyone including Erin |

Every message carries `sequence: 43` and its `index`. `(sequence, index)` is a unique, totally
ordered key — the client's dedup key and the wire form of the backend's ordering guarantee.

**Spectator filtering is structural, not a filter.** `FR-DELIVER-002` says spectators receive only
`broadcast`-derived events, and the destinations enforce it: Erin cannot subscribe to
`/topic/game.{sessionId}.team.*` (the channel guard requires a team assignment, which she has none
of), and `/user/queue/game` resolves from her own principal, so a `send_to_player` addressed to Bob
is not deliverable to her by construction. There is no per-message spectator check to forget.

**Fan-out is in-process.** Every subscriber for this session is on this instance, because room
affinity put them there. No pub/sub, no cross-instance hop — which is what makes `NFR-PERF-002`'s
50 ms budget a serialization cost rather than a network one.

**The game log is the only non-plain-text render surface in the platform**, and its content is
composed by game code — the one place "React escapes by default" does not save us. It renders through
a Markdown renderer with raw HTML disabled, no links and no autolinking. Accepted residual: a
username containing Markdown metacharacters can corrupt log *formatting*, never markup.

---

## E. What the client does with it

Erin's iframe was reloaded 200 ms ago and she is mid-sync. Her client:

1. Subscribed **first**, so sequence 43 is already in her buffer.
2. Receives `GAME_SYNC` with `asOfSequence: 42`.
3. Discards buffered messages `<= 42`, applies 43 on top, continues live.

**This is why the subscribe-then-sync order is mandatory and not merely tidy.** Any effect at or
below `asOfSequence` is already reflected in the view the backend just computed. Any effect above it
went out after she was subscribed, so she has it. There is no window in which a message is neither in
the snapshot nor delivered — at start, on reconnect, and on late join identically.

**There is no gap detection on the game stream, and clients must not attempt it.** The stream is
deliberately sparse: a `send_to_player` addressed to Bob consumes a sequence Erin will never see, and
so does Team A's `send_to_team`. Holes are normal and carry no information. A client that requested a
snapshot on a "missing" sequence would re-enter the guest VM under the session lock, once per hole,
on every turn — a self-inflicted denial of service that looks like correctness.

This is the opposite of the room stream, where `version` is dense because every room event reaches
every subscriber and a gap really is a gap.

---

## F. When the turn fails

| Failure | Handling |
|---|---|
| Game throws | Counts toward the retry limit (3, `FR-FAIL-003`). Exhausted → session fails gracefully (`FR-FAIL-005`), room to Lobby, `SESSION_FAILED` to clients |
| Watchdog expires (30 s) | Interrupt, then `close(true)` after a 5 s escalation grace. Treated as a processing failure |
| `DEADLINE_EXCEEDED` / `UNAVAILABLE` | Transport failure — infrastructure signal, not a game fault. Reassign or retry; does **not** consume the game's retry budget |
| Redis unreachable > 60 s | Affected sessions failed gracefully |

The split between *processing* failures (the game's fault, budgeted) and *transport* failures (ours,
not budgeted) is what stops a Game Host restart from burning a healthy game's retry allowance and
killing it.

**A failed action produces no history entry.** History is written only on `game_over`
(`game-history.md` `FR-HIST-001`/`CON-001`), and a session that fails back to Lobby produces none —
neither an entry nor a session-completion row, so the per-game counter does not move either.

---

## Defects surfaced

| Defect | Fix |
|---|---|
| `ghe_placement_ck` would abort the entire recording transaction on a malformed outcome, and `game_over` is terminal (`FR-EFF-006`) so there is no retry that can succeed — the session would vanish from history *and* statistics over one bad integer | Outcome validated at the effect boundary; the completion row and counter are still written, history entries are skipped, an ERROR names the game. The CHECK becomes a backstop ([history §2](../platform/data-model-history.md)) |

Found by asking what happens when a *game* is wrong rather than when the platform is. The retry and
watchdog machinery is thorough about a game that throws or hangs, and had nothing for a game that
returns successfully with a structurally invalid outcome — the one failure mode that reaches
Postgres.
</content>
