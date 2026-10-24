# Platform State Across Instances

**Status:** specified by `IMP-M18-08` (milestone M18, [ADR-0020](../../decisions/0020-platform-horizontal-scaling.md)); design in
[`load-testing-phase-b.md`](../deployment/load-testing-phase-b.md) §4.1, §4.2.

The Platform Monolith runs as two or three replicas. Room traffic is served by the room's owner
([ADR-0002](../../decisions/0002-websocket-room-affinity.md), [`room-lifecycle.md`](room-lifecycle.md) §1) and
needs nothing here. Everything else a replica keeps in memory is either **correct per instance** or has been
**fixed** so that it behaves as one instance. This document is the audit of every such map, and it specifies
the one new mechanism the fixes share.

## 1. Audit of in-memory state

"Per instance" means: the state describes something this instance alone holds (its sockets, its owned rooms,
its pooled channels), so another instance's copy is a different fact, not a stale one.

| Class (package) | Holds | Verdict |
|---|---|---|
| `NotificationEmitterRegistry` (`notification`) | Every SSE stream open on this instance, by emitter id and by user | **Correct per instance, because** a stream is a socket on this instance. **Fixed by** §2: alerts, the live push of a persisted notification, and revocation reach it from other instances. |
| `WebSocketConnectionRegistry` (`websocket`) | Every STOMP session open on this instance, by user | **Correct per instance** for closing and counting sockets here. The per-user cap of 4 was **fixed by** §3: it is counted in Redis across instances. Revocation reaches it through §2. |
| `WebSocketRateLimiter` (`websocket`) | Token buckets, violation windows and notice stamps per connection or principal | **Correct per instance, because** `rate-limiting.md` § Pod-local budgets already accepts it: these are abuse controls, and a user's frames for a room all land on the room's owner. The reconnect **lockout** and the offence counter are already in Redis. |
| `RoomOwnershipService.owned` (`room`) | The rooms this incarnation believes it owns, with epoch and version counter | **Correct per instance, because** it is the instance's half of ADR-0008's claim: Postgres and Redis hold the other half, and an instance that is not the owner cannot mutate the room (`room-lifecycle.md` §1.5). |
| `RoomSubscriptionAuthorizer` (`room`) | Which room each STOMP session on this instance subscribed to | **Correct per instance, because** it indexes this instance's sockets, and it is used to sever exactly those on ownership loss and to feed this instance's disconnect handling. |
| `ParticipantCache` (`room`) | The owner's memory of who is in a room's session | **Correct per instance, because** only the owner mutates a room and every entry is checked against the owner epoch it was read under (`IMP-M18-04`); an instance that lost the room serves a miss. |
| `GameHostChannels` (`game`) | Pooled gRPC channels keyed by Game Host address | **Correct per instance, because** a channel is a connection from this process; the addresses come from the Redis host registry every instance shares. |
| `KeyedLocks` (`common`) | Reference-counted locks for the work this instance is doing | **Correct per instance, because** every use is for a room this instance owns or a session it is serving; the cross-instance exclusion is the ownership claim, not a lock. |
| `ReconciliationMetrics` (`room`) | Gauges and counters for this instance's sweeps | **Correct per instance, because** metrics are scraped per pod and summed by the query. |
| API rate-limit tiers 1 to 5 (`common`) | Bucket4j buckets | **Not in memory.** The proxy manager is Redis-backed, so one bucket is shared by every instance. |
| ShedLock'd jobs (`@SchedulerLock`) | `guestPurge`, `roomReconciliation`, `roomPurge`, `notificationPurge`, `expiredSubjectPurge`, `uploadSlotCleanup` | **Not in memory.** The lock row is in Postgres, so a run on one instance excludes the other. The jobs that must run on every instance (lease renewal, the grace-deadline sweep) carry no lock by design. |

`TwoInstanceIT` boots two application contexts on one Postgres and one Redis and asserts the rows marked
**fixed** and the two **Not in memory** rows.

## 2. User-scoped pushes: one Redis pub/sub channel per concern

ADR-0002 rejected pub/sub for room fan-out and that stands. User-scoped pushes have no owner and are
low-volume, so they use `UserPushBus` (`common`):

- The instance that raises the push **delivers on itself first**, then publishes; every other instance runs
  its handler. A publisher ignores its own message, so nothing is delivered twice and local delivery never
  depends on Redis.
- Delivery is **best-effort**, as an alert always was: a publish that fails is logged and dropped, and a user
  with no stream on the receiving instance is skipped (`sse-notifications.md`).
- Channel `turnbase:push:{name}`; message `{"origin": "<instance>", "payload": {...}}`.

| Channel | Payload | Raised by | Receiving instance does |
|---|---|---|---|
| `alert` | `userId`, `type`, `payload` (the alert's own fields) | `AlertPublisher.publish` | Writes `event: alert` to the user's open streams, if any |
| `notification` | `userId`, `notificationId` | A persisted notification's after-commit listener | If the user has an open stream, claims the row (`delivered_at IS NULL`, the same guarded update the catch-up uses) and pushes it; exactly one instance sends a row |
| `session-revoked` | `sessionId`, `userId`, `reason` | `SessionRevokedEvent` raised locally | Re-publishes it as a `remote` `SessionRevokedEvent`; the WebSocket and SSE registries close that session's connections exactly as for a local one, and the relay does not send a `remote` event on |

## 3. The per-user WebSocket cap, cluster-wide

`rate-limiting.md` § Connection cap says at most 4 per user. `ConnectionCapLedger` (`websocket`) counts them
across instances in one Redis sorted set per user, `ws:conns:{userId}`; members are STOMP session ids, scores
are lease expiry times.

- **Admit** is one Lua script: drop lapsed members, refuse if the set holds the cap and the session is not in
  it, otherwise add it with a 90-second lease.
- **Release** removes the member on disconnect or close.
- **Renew** runs every 30 seconds and extends the lease of every connection the instance holds, so an instance
  that dies leaves a count that falls to zero within 90 seconds and a user is not locked out by a crashed pod.
- Redis unreachable: the connection is admitted against the instance's own count only. The cap is an abuse
  control, not a correctness property.
