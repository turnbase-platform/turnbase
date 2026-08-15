# End-to-End Flows

Eight journeys traced across every component they touch — client, Platform Monolith, Redis,
PostgreSQL, Game Host — naming the actual endpoint, STOMP destination, gRPC call, table and
requirement at each step.

## Why this directory exists

Every other document in `docs/specs/` is organised by **component**: the room protocol, the game
protocol, the gRPC contract, the schema. That is the right organisation for maintaining a
component and the wrong one for understanding a system, because no journey a user takes is confined
to one of them. Starting a game touches a REST endpoint, two STOMP destinations, three tables, a
Redis lease, a gRPC call and an Espresso context, and until this directory existed the only way to
know that was to hold six documents open at once.

These are **documentation, not new design.** Where a step here disagrees with the component
document that owns it, the component document wins and this one is wrong. What these files add is
the ordering, the handoffs, and the state each step leaves behind.

## Files

| File | Journey |
|------|---------|
| [01-arrival-and-account.md](01-arrival-and-account.md) | Unauthenticated arrival → "Play as Guest" → the landing that follows; and the same person registering later |
| [02-room-to-game-start.md](02-room-to-game-start.md) | Create a room → a second player joins → team assignment → readiness → `START_GAME` |
| [03-game-turn.md](03-game-turn.md) | One full turn: client action → WebSocket → Orchestration → sequence → gRPC → Espresso → effects → fan-out, including spectator filtering |
| [04-disconnect-and-return.md](04-disconnect-and-return.md) | Disconnect → grace period → reconnect; and the same trace ending in expiry |
| [05-owner-loss-and-adoption.md](05-owner-loss-and-adoption.md) | The owning instance dies mid-game → adoption → clients reattach |
| [06-game-end-and-rematch.md](06-game-end-and-rematch.md) | `game_over` → history and statistics → Lobby → rematch → teardown of the first session |
| [07-room-closure.md](07-room-closure.md) | Closing a room that has a live session, on each of the five detach paths |
| [08-upload-to-play.md](08-upload-to-play.md) | Game bundle upload → validation → catalog → a room playing it |

## How to read a trace

Each step is numbered and carries the component acting, what it does, and the durable state it
leaves. **Durable state is called out explicitly** — a step that writes nothing is marked as such,
because the steps that write nothing are the ones a crash erases.

Where a flow crosses a decision recorded in an ADR, the ADR is named at the step rather than
summarised.

## What these traces found

Walking a journey end to end finds a class of defect that reading a diff does not: a rule whose
supporting state has no writer, a state nothing can leave, an ordering that only works when nothing
fails. The previous session's three worst defects were all found this way. Defects found while
writing these files were fixed in the documents that own them and are listed in each file's
*Defects surfaced* section, with the fix, rather than left as prose describing a system that does
not behave that way.
</content>
