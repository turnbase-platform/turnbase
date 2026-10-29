# `OQ-5`: eager and lazy reassignment, measured (IMP-M18-12)

**Verdict:** lazy wins by the decision rule. Neither mode had a correctness failure of its own, both meet NFR-REL-002 in every scenario, so the tie goes to lazy (`load-testing-phase-b.md` §5.2). Eager's sweep and switch were removed. The suite stays and runs against lazy.

## Method

`HostFailureReassignmentIT` (`turnbase-platform`, integration profile) boots the real Platform with Redis, Postgres and MinIO in Testcontainers and several in-process fake Game Hosts that model the host contract: a sequence at or below `lastAppliedSequence` is a replay, and the session record outlives the host. Heartbeat 500 ms, lease TTL 1.5 s, dispatch deadline 2 s. The same ten scenarios ran against `turnbase.orchestration.reassignment=lazy` (the existing `GameInputService.reassign` on the first failing input) and `=eager` (a sweep every 500 ms that moved every session routed to a host with an expired lease, under the session's submit lock and only while still routed to that host).

Correctness per scenario: the sequences delivered are exactly 1..n in order (none lost, none twice); the sequences the hosts applied are exactly 1..n in order; the session is routed to a live host at the end; the session failure listener never fired. "kill→done" is the time from the kill to the last accepted input, so for the idle scenarios it is dominated by the wait before the next input. gRPC calls are those that reached a live fake host. Redis commands are the server's `total_commands_processed` delta across the scenario, including the test's own heartbeats (the same in both modes), so compare modes, not absolutes. Timer and deadline inputs use the same dispatch path as player inputs; the "timer pending" scenario is an input arriving after the lease TTL, not a separate timer implementation.

## Results

| mode | scenario | failures | kill→done ms | gRPC calls | Redis cmds |
|---|---|---|---|---|---|
| lazy | killed mid-move, input not applied | 0 | 148 | 3 | 46 |
| lazy | killed mid-move, input applied | 0 | 241 | 3 | 44 |
| lazy | idle kill, next input after 1 s | 0 | 1127 | 2 | 50 |
| lazy | idle kill, next input after the lease TTL | 0 | 2128 | 2 | 57 |
| lazy | idle kill, next input after reassignment | 0 | 5127 | 2 | 83 |
| lazy | kill with a timer pending (timer input after the TTL) | 0 | 2625 | 2 | 62 |
| lazy | zombie: lease expired, host still answers, then returns | 0 | 3555 | 4 | 85 |
| lazy | two hosts killed in succession | 0 | 122 | 3 | 72 |
| lazy | planned drain, then the host leaves | 0 | 1624 | 3 | 67 |
| lazy | concurrent inputs for one session during reassignment | 0 | 165 | 9 | 90 |
| eager | killed mid-move, input not applied | 0 | 228 | 3 | 44 |
| eager | killed mid-move, input applied | 0 | 223 | 3 | 48 |
| eager | idle kill, next input after 1 s | 0 | 1120 | 2 | 57 |
| eager | idle kill, next input after the lease TTL | 0 | 2011 | 2 | 72 |
| eager | idle kill, next input after reassignment | 0 | 5011 | 2 | 117 |
| eager | kill with a timer pending (timer input after the TTL) | 0 | 2512 | 2 | 79 |
| eager | zombie: lease expired, host still answers, then returns | 0 | 3543 | 4 | 123 |
| eager | two hosts killed in succession | 0 | 118 | 3 | 76 |
| eager | planned drain, then the host leaves | 0 | 1512 | 3 | 90 |
| eager | concurrent inputs for one session during reassignment | 0 | 150 | 9 | 90 |

("Two hosts killed in succession" is the run after the fix below. Before it, both modes failed that scenario identically: lost input, game aborted.)

## A defect common to both modes, fixed here

With two hosts killed within one lease TTL, `reassign` excluded only the host that had just failed. The earlier dead host still held a live lease, so it was selected again; the two ping-ponged until `failcount:` reached the retry limit and the game was aborted, which the spec says must survive (`orchestration-gamehost-protocol.md` *Error model*: `UNAVAILABLE` counts only if reassignment cannot make progress). The fix is local: `reassign` now quarantines the failed host for the lease TTL (`HostRegistry.quarantine(instanceId, ttl)`), so selection skips it until its lease would have expired anyway.

## Reading the numbers

- Every scenario passes in both modes, including the zombie (a host answering gRPC after its lease lapsed) and the concurrent-input case. Where the session is reassigned does not change what is applied, because the host-side replay by `sequence` and the `delivered:` watermark carry exactly-once in both.
- Time to the next accepted input after a dead host is 120-230 ms from the moment an input is dispatched, in both modes. Eager does not shorten it: an input for an already-reassigned session still has to be restored on the new host, which is the cost either way.
- Eager makes more Redis calls (a `SCAN` of `routing:*` plus a `GET` per key every interval, whether or not any host died); in the idle scenarios 57-117 commands against 50-83 for lazy. At the Phase B scale that is a scan over the order of thousands of keys every interval for no benefit measured here.
- Not measured: scale (thousands of sessions per dead host), and a real Espresso restore. Neither is expected to change the rule, since both modes restore the same way.

## Decision

Lazy. `game-host-internals.md` §9.3 and §18 `OQ-5` are amended; `EagerReassignment` and its switch are removed.
