# Archive — M2 Rooms and realtime

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim by `IMP-M20-01`. Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M2-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M2-01 | Room CRUD and listing | platform | M1-06, M2-03 | DONE |
| IMP-M2-02 | STOMP endpoint, auth, subscriptions | platform | M2-01, M2-03 | DONE |
| IMP-M2-03 | Ownership claim, lease, epoch fence | platform | M1-06 | DONE |
| IMP-M2-04 | Room event versioning and fan-out | platform | M2-01, M2-03 | DONE |
| IMP-M2-05 | Join, teams, readiness | platform | M2-04 | DONE |
| IMP-M2-06 | Host management and transfer | platform | M2-05 | DONE |
| IMP-M2-07 | Disconnect, grace deadlines, sweeps | platform | M2-03 | DONE |
| IMP-M2-08 | Reconnect and resync | platform | M2-07 | DONE |
| IMP-M2-09 | Room closure and the five detach paths | platform | M2-07 | DONE |
| IMP-M2-10 | Adoption and reconciliation jobs | platform | M2-03 | DONE |
| IMP-M2-11 | In-room chat | platform | M2-05 | DONE |
| IMP-M2-12 | Room invitations | platform | M2-01, M1-09 | DONE |

---

## M2 — Rooms and realtime

The single most subtle milestone. `docs/specs/platform/room-lifecycle.md` and
`docs/specs/api-design/room-websocket.md` are the two core documents; read both in full before
starting **any** M2 item, along with ADR-0008, ADR-0009 and ADR-0010.

Walk `docs/specs/flows/02`, `04`, `05` and `07` before writing code.

Three invariants hold across every item in this milestone and are restated at the items where they
bite:

1. **The owner epoch is the fence token. The room version is not.**
2. **Commit before publish.** The version reaches Postgres before the delta reaches a client.
3. **Lock outer, transaction inner, publish after commit.** In that nesting, never another.

### IMP-M2-01 — Room CRUD and listing

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-06, IMP-M2-03

**Closed:** IMP-GATE-41 (opened and closed 2026-09-08, session 38) — this item's read-list never named
[`data-model-catalog.md`](../../specs/platform/data-model-catalog.md), although the endpoints it
determines cannot be built without it. Three separate needs land in that document and were nowhere in
the read-list: (1) `room-rest-api.md` §3's `canJoin`/`canSpectate` predicate and §3's row shape
(FR-LIST-002, FR-LIST-003a) need `game_version.min_players`, `.max_players`, `.supports_ai`,
`.supports_spectators`, `.supports_mid_game_join` — the actual queryable columns, joined via
`room.game_id`/`room.game_version` → `game_version(game_id, version)`; (2) `room-rest-api.md` §2's
create transaction said only "a game with an ACTIVE version the caller may see", but
`data-model-catalog.md` §1 *Where the write-side rules are enforced* names this as three concrete,
separately-checked preconditions on `INSERT INTO room` — `game.deleted_at IS NULL AND
game.archived_at IS NULL` (FR-GAME-013), `game.listed OR :creator = game.owner_user_id` (FR-GAME-007),
`game.badge <> 'UNVERIFIED' OR :creator = game.owner_user_id` (FR-PRV-002) — none of which
`room-rest-api.md` stated; (3) `gameName`/`hostUsername` in the list row and detail resource resolve
through `game.title` and `app_user.username` via `room.host_user_id`, both defined outside the
original read-list.

Also fixed a naming defect in the document that **was** read: `room-rest-api.md` §3 wrote
`game.capabilities.midGameJoin` and `game.capabilities.spectating` as if `game` carried a
`capabilities` object directly. It does not — `manifest-schema.md` §`capabilities` names the JSON
field `spectators`, not `spectating`, and `data-model-catalog.md` §2 projects it onto
`game_version.supports_spectators`/`.supports_mid_game_join`, not a nested object on `game` at all.
Fixed: `room-rest-api.md` §3's predicate (and §5 step 3's `IN_PROGRESS` mid-game-join check) now name
`gameVersion.supports_mid_game_join`/`.supports_spectators` and cite `data-model-catalog.md` §2; §2's
`gameId` field description now states the three room-creation preconditions explicitly; the *Related*
table gained `data-model-catalog.md`. This item's read-list gained `data-model-catalog.md` §1–§2.

**Closed:** IMP-GATE-40 (opened and closed 2026-09-08, session 37) — this item's own Done-when clause
5 requires the room-ownership claim/redirect/`503` mechanism, which `room-lifecycle.md` §1 documents
in full and which `IMP-M2-03` ("Ownership claim, lease, epoch fence") is the item that builds — but
`IMP-M2-03` depended on `IMP-M2-02`, which depended on `IMP-M2-01`. That is a cycle in substance: this
item cannot satisfy its own clause 5 without the mechanism `IMP-M2-03` owns, `IMP-M2-03` cannot start
under its old dependency until `IMP-M2-02` is done, and `IMP-M2-02` cannot start until this item is
done. Same shape as `IMP-GATE-03`/`08`/`18`/`28` — a *Done when* clause reaching past infrastructure
that does not exist yet — but here the infrastructure's own item was mis-sequenced *behind* the item
that needs it, rather than simply not yet written. `IMP-M2-04`, `IMP-M2-07` and `IMP-M2-10` already
depend on `IMP-M2-03` directly and needed no change — only the two REST/STOMP consumers were
mis-ordered relative to the mechanism they call. Fixed: `IMP-M2-03`'s *Depends on* changes to
`IMP-M1-06` (nothing in its own read-list — ADR-0008, `room-lifecycle.md` §1–§2, `data-model.md` §1,
`local-environment.md` §7.1 — needs REST or STOMP to exist first); this item's *Depends on* gains
`IMP-M2-03`; `IMP-M2-02`'s *Depends on* gains `IMP-M2-03` alongside its existing `IMP-M2-01` (its own
subscribe-time ownership re-verification, `room-lifecycle.md` §1.7, needs the same mechanism). Done-when
clause 5 below is unchanged in substance — the claim/redirect/`503` behaviour it describes is real and
still this item's to expose over REST — but it now presumes `IMP-M2-03`'s claim component exists to be
called, rather than requiring this item to build it.

**Closed:** IMP-GATE-39 (opened and closed 2026-09-08, session 37) — this item's read-list never named
`docs/specs/platform/room-lifecycle.md`, although `room-rest-api.md` (this item's own read-list
document, in full) cites it repeatedly as the mechanism behind Done-when clause 5 (the room-ownership
claim behind the `503`/`Retry-After` and `X-TurnBase-Room-Instance` behaviour, §1.2/§1.7) and behind
the delegation boundary in §6 (host-leave consequences run under `room-lifecycle.md` §4, not this
item). Separately, `room-rest-api.md` §5, §3, §3.1 and §4 build FR-JOIN-007 (the single-room
constraint, entirely inside the REST join transaction), FR-XFER-003 (closed-room invisibility/404) and
FR-HOST-002 (invite-code minting, host-only exposure, resolution) in full — all three inside this
item's own endpoints — yet this item's *Satisfies* claimed none of them, while `IMP-M2-05`'s
*Satisfies*/*Done when* explicitly claimed FR-JOIN-007 ("FR-JOIN-007's one-room-at-a-time rule is
enforced server-side") and `IMP-M2-06`'s *Satisfies* claimed FR-XFER-003 and FR-HOST-002 via its
`FR-XFER-001…005`/`FR-HOST-001…003` ranges, even though neither of those items' STOMP-layer read-lists
or done-when clauses touch the REST handlers that actually build them. Fixed: this item's read-list
gains `room-lifecycle.md` §1.2 (claim), §1.3 (release), §1.4 (adoption), and §1.7 (affinity hint) —
the mechanism Done-when clause 5 requires — plus enough of §4 to know where the delegation boundary to
`IMP-M2-06` sits. This item's *Satisfies* gains FR-JOIN-007, FR-XFER-003 and FR-HOST-002, which
`room-rest-api.md` builds here in full. `IMP-M2-05`'s *Satisfies* narrows its FR-JOIN range to
`FR-JOIN-001…006, FR-JOIN-008…011` (007 moves here) and its *Done when* drops the FR-JOIN-007 clause —
the STOMP command layer never touches the single-room constraint, which the REST join transaction
enforces before any STOMP command is reachable. `IMP-M2-06`'s *Satisfies* narrows to
`FR-HOST-001, FR-HOST-003, FR-HOST-006…009, FR-XFER-001…002, FR-XFER-004…005` — FR-HOST-002 and
FR-XFER-003 are this item's, not the host-transfer STOMP layer's.

**Read first:**
- `docs/specs/platform/room-lifecycle.md` §1.2 (*Claim*), §1.3 (*Release*), §1.4 (*Adoption*), §1.7
  (*Routing*) — the contract of `IMP-M2-03`'s claim component this item's handlers call for Done-when
  clause 5 (not this item's to implement, `IMP-GATE-40`), and enough of §4 to know the host-leave
  delegation boundary in `room-rest-api.md` §6
- `docs/specs/api-design/room-rest-api.md` **in full** — the five endpoints, §3's inclusion
  predicate, §5's join contract, §7's error table
- `docs/specs/platform/data-model.md` §1 (`room`), §2 (`room_participant`), §3 (`room_team`)
- `docs/specs/platform/data-model-catalog.md` §1 (`game`), §2 (`game_version`) — the room-creation
  preconditions (FR-GAME-013, FR-GAME-007, FR-PRV-002) and the `min_players`/`max_players`/
  `supports_ai`/`supports_spectators`/`supports_mid_game_join` columns behind §3's `canJoin`/
  `canSpectate` predicate and row shape (`IMP-GATE-41`)
- `docs/requirements/game-rooms.md` FR-CREATE-001…004, FR-LIST-001…007, FR-JOIN-001…006
- `docs/specs/api-design/pagination-filtering-sorting.md`, `rest-conventions.md`
- `docs/specs/manifest/manifest-schema.md` § `capabilities`, § `teamTemplates` — the manifest JSON
  shape `data-model-catalog.md` §2 projects onto `game_version`'s capability columns, and FR-TEAM-012's
  team instantiation; no other read-list document defines it (repaired, no gate — a plain missing
  citation)

**Satisfies:** `game-rooms.md` FR-CREATE-001…004, FR-LIST-001…007, FR-JOIN-001…007, FR-XFER-003,
FR-HOST-002, FR-LIFE-004, NFR-PERF-001, NFR-SEC-001…002, NFR-USAB-001, NFR-SPEC-001;
`notifications-invitations.md` FR-LINK-001…002 (`IMP-GATE-58` — this item's own §3.1 invite-code
mint/resolve mechanism is the entire behaviour either requirement describes; neither `IMP-M2-12` nor
`IMP-M5-03`, which both claimed it, builds anything toward it); `platform-views.md` VW-ROOMS-001…005,
VW-JOIN-001…003

**Done when:**

1. `POST /api/rooms` returns `201` with a `Location` header and the full room resource.
2. Listing applies §3's predicate exactly:
   `included(room, viewer) := room.state <> 'CLOSED' AND visible(room, viewer) AND (canJoin(room, viewer) OR canSpectate(room, viewer))`.
   An Invite Only room appears to nobody (FR-LIST-007); a Friends Only room appears only to the
   host's friends (FR-LIST-006).
3. `GET /api/rooms?inviteCode=…` returns a **0-or-1 element list and never a `404`**. A `404`
   confirms or denies the existence of a code to an unauthenticated prober, which is what
   NFR-SEC-002's unguessable identifiers were bought to prevent.
4. Join is **one** endpoint discriminated by the body's `{"role":"PLAYER"|"SPECTATOR"}`; leave is
   `DELETE /api/rooms/{roomId}/participants/me`.
5. A request that lands on a pod which is neither the owner nor able to claim returns `503` with
   `Retry-After` and the `room-unavailable-retry` problem type — **not** a redirect. The affinity
   hint travels as the `X-TurnBase-Room-Instance` response header.

**REST is membership only.** Team edits, readiness, parameters, kick and start are all STOMP
(IMP-M2-05, M2-06). Adding a REST route for any of them puts a second writer outside the per-room
serialization `room-websocket.md` depends on, and the ordering guarantee is gone.

**`PLAYER_JOINED`/`PLAYER_LEFT` broadcast on the join/leave transactions above is `IMP-M2-04`'s duty,
not this item's** (`IMP-GATE-43`) — both events require the lock-scoped, version-assigning,
commit-then-publish executor that item builds, which did not exist when this item shipped.

**`canSpectate`'s capacity is `turnbase.room.spectator-capacity`** (default `8`,
`local-environment.md` §7.1) — a platform property, not a room column and not a create-request field.
Hosts choose whether a room allows spectating; they do not choose how many (NFR-SPEC-001). The wire
field `spectatorCapacity` is the resolved value, so lowering the property never evicts a seated
spectator.

---

### IMP-M2-02 — STOMP endpoint, auth, subscriptions

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-01, IMP-M2-03 (`IMP-GATE-40`: subscribe-time
ownership re-verification, `room-lifecycle.md` §1.7, needs `IMP-M2-03`'s claim component)

**Done 2026-09-09 (session 39).** New `websocket` feature package (`IMP-GATE-42`):
`WebSocketConfig` (`@EnableWebSocketMessageBroker`, STOMP at `/ws`, no SockJS, `.`-delimited
`AntPathMatcher`, 10000/10000ms heartbeats on an explicit `TaskScheduler` bean, simple broker on
`/topic`/`/queue`, `setPreservePublishOrder(true)`) → `WebSocketChannelInterceptor`, the single
`clientInboundChannel` interceptor: `CONNECT` reads the session token `SessionCookieHandshakeInterceptor`
stashed into the handshake attributes during the HTTP upgrade (the httpOnly cookie itself never
reaches a STOMP frame) and resolves it via `session.SessionService.resolve()` — a new public method
extracted from `SessionAuthenticationFilter` so the HTTP and WS paths share one token-verify-then-
session-lookup instead of duplicating it — then checks the `WebSocketRateLimiter` reconnect lockout
and `WebSocketConnectionRegistry.tryRegister()`'s connection cap (4/user); any failure throws, and
Spring's own STOMP handling turns that into a `CONNECT`-frame `ERROR` + close (`websocket.md` §
Authentication), so no bespoke frame-building was needed there. Every later frame is classified by
`WebSocketRateLimiter` into `rate-limiting.md` Tier 6's six buckets (pod-local Bucket4j `LocalBucket`s,
no Redis round trip) with the full penalty ladder — drop-and-throttled-notice, then sustained-violation
force-close via `WebSocketConnectionRegistry.closeSession()` (a manually-built STOMP `ERROR` command
message sent on `clientOutboundChannel`, which Spring's `StompSubProtocolHandler` closes the session
after relaying — verified end to end by `RoomSubscriptionAuthorizerIT`, not assumed), writing the
doubling `rate:ws-lockout:*` Redis key. `WebSocketConnectionRegistry` also exposes
`turnbase_websocket_connections_active` (`observability.md` §2, `platform-operations.md` FR-MET-002)
and subscribes to `session.SessionRevokedEvent`, closing every connection under the revoked login
session with its `revoked_reason` (`FR-SESS-010`, `IMP-GATE-28`).

`SUBSCRIBE` authorization is a pluggable seam (`websocket.SubscriptionAuthorizer`/`SubscriptionDecision`)
the channel interceptor dispatches by destination, kept out of `websocket` itself per the gate's
resolution. `room.RoomSubscriptionAuthorizer` is the one implementation today: membership
(`RoomRepository.isCurrentParticipant`, widened from `private`) gates a silent drop, then subscribe-time
ownership re-verification calls a new `RoomOwnershipService.claimWithRetry()` (the §1.7 bounded-retry
loop extracted from `RoomService.claimAndGetInstanceHeader`, now shared by REST and STOMP rather than
duplicated) — a `Redirect`/`Superseded` outcome after retries rejects with `ROOM_UNAVAILABLE_RETRY` and
`retryAfterMs` on `/user/queue/errors` (`room-websocket.md` § the "arises at two points" section),
never silently served. It also tracks which STOMP sessions are subscribed to which room (the only place
that knows the mapping, since `RoomOwnershipLostEvent` carries no session ids) and severs exactly that
room's sockets with a `ROOM_OWNERSHIP_LOST` code on `RoomOwnershipLostEvent` (`room-lifecycle.md` §1.5
layer 3/§1.6) — the subscriber `IMP-M2-03`'s own text named as still missing. Chat/team sub-topics
(`.chat`, `.team.*`) are deliberately out of `supports()`'s match — `IMP-M2-11`'s.

**Deferred, each to the item that owns it:** the room member/host `@MessageMapping` command handlers
and `ROOM_STATE` snapshot delivery (`IMP-M2-04`/`M2-05`/`M2-06`/`M2-11`) — this item's Done-when never
required them, and the Tier 6 `command`/`chat`/`snapshot` buckets already classify their destinations
so those items need no interceptor change; the game destinations and `action`/`snapshot`-for-game
classification (`IMP-M3-*`). **IMP-GATE-47** (closed the same session it opened, on `IMP-M2-11`):
`input-validation.md`'s per-destination STOMP frame-size ceiling was never built here either — this
item's own read-list never named `input-validation.md`, so `WebSocketChannelInterceptor` shipped Tier
6 classification with no companion size guard. `IMP-M2-11` adds it to the same interceptor, covering
this item's own `/app/room.*.member`/`.host` rows retroactively (no code change needed here — the
guard runs ahead of every feature's handlers) alongside chat's own row and the two game rows M3
inherits.

**Verified.** Unit: `WebSocketRateLimiterTest` (bucket classification, the drop→notify-throttle→
force-close ladder, lockout doubling), `WebSocketConnectionRegistryTest` (connection cap,
`SessionRevokedEvent` closes only matching sessions), `RoomSubscriptionAuthorizerTest` (membership,
both ownership outcomes, `RoomOwnershipLostEvent` severing, disconnect bookkeeping), `SessionServiceTest`
(the extracted `resolve()`, all five resolutions). Integration, real STOMP clients over a real port:
`WebSocketIT` (`CONNECT` with no cookie never completes a session; a valid cookie does; a non-member's
`SUBSCRIBE` produces no error and no data) and `RoomSubscriptionAuthorizerIT` (a member's `SUBSCRIBE`
on the owning pod, then a directly-published `RoomOwnershipLostEvent` actually closes that live
WebSocket with a `ROOM_OWNERSHIP_LOST` `ERROR` frame — the assumption most worth not merely asserting).
A Modulith circular-dependency trap surfaced and was fixed with two `@Lazy` injection points
(`WebSocketConfig`'s `WebSocketChannelInterceptor`, `WebSocketConnectionRegistry`'s
`clientOutboundChannel`) — both are themselves dependents of the broker infrastructure that Spring
cannot finish assembling until every `WebSocketMessageBrokerConfigurer` (including `WebSocketConfig`)
is constructed. `./mvnw verify -Pintegration` green locally (113 tests, merged JaCoCo gate met); CI
green on `turnbase-platform` `master` (`build`, 15m5s) after an unrelated fix landed in the same
session — a freshly-disclosed CRITICAL CVE (CVE-2026-75595) in `netty-handler`, pulled in transitively
by `IMP-M0-07`'s AWS SDK client, was blocking every push; pinned the whole `netty-bom` to `4.1.137.Final`.
`e2e`'s "Check out turnbase-game-host" step fails on the same un-provisioned `TURNBASE_GAME_HOST_PAT`
every prior session's accepted run also shows.

**Closed:** IMP-GATE-42 (opened and closed 2026-09-09, session 39) — `conventions.md` §1's package
table lists the monolith's features exhaustively ("the feature list is the milestone decomposition")
but named no package for the STOMP/WebSocket infrastructure this item must build — base connection
config, CONNECT authentication, the Tier 6 pod-local rate limiter, and the connection registry — even
though `websocket.md` and `room-websocket.md` make clear this infrastructure is cross-feature (it
already spans `room` here and `game` from M3 onward), the same shape `rate-limiting.md` Tiers 1–5
already resolved by living in `common`. Fixed: `conventions.md` §1 gained a `websocket/` feature
package — connection config, CONNECT auth, Tier 6 limiter, connection registry and its
`turnbase_websocket_connections_active` gauge — with per-destination `SUBSCRIBE` authorization and
`@MessageMapping` command handlers staying inside the feature they authorize (`room` here, `game`
from M3), consuming `websocket/`'s public API rather than the reverse.

**Read first:**
- `docs/specs/api-design/websocket.md` — connection, authentication, envelope, authorization
- `docs/specs/api-design/room-websocket.md` — *Room Affinity and WebSocket Routing*, *Destinations*,
  *Message Envelope*, *Authorization Model*
- `docs/decisions/0002-websocket-room-affinity.md`
- `docs/specs/api-design/rate-limiting.md` Tier 6

**Satisfies:** `platform-architecture.md` FR-ROUTE-001…005; `user-accounts.md` FR-SESS-010;
`game-rooms.md` NFR-PERF-002

**Done when:** the handshake authenticates once from the session token and no frame re-authenticates
(FR-SESS-010); a SUBSCRIBE is authorised against room membership **at subscribe time**, so an
unauthorised destination is refused rather than silently delivering nothing; Tier 6's frame limit is
enforced pod-locally, in-process — it is the one tier that does not go to Redis, because a Redis round
trip per inbound frame is the cost the limiter exists to avoid; a client connected to a pod that does
not own the room is redirected using the affinity hint rather than served across instances (ADR-0002:
**there is no cross-instance fan-out**). The STOMP session registry this item creates exposes
`turnbase_websocket_connections_active` as a `Gauge` (`observability.md` §2 names the metric;
`platform-operations.md` FR-MET-002 defines it, deferred here by `IMP-M0-10`). The registry also
subscribes to `IMP-M1-06`'s `SessionRevokedEvent`: on receipt, every connection registered under that
`sessionId` is sent a STOMP `ERROR` frame naming `revoked_reason` and then closed — this is
`FR-SESS-010`'s actual duty (`IMP-GATE-28`), narrowed out of `IMP-M1-06` because no registry existed
there to close. **It also subscribes to `IMP-M2-03`'s `RoomOwnershipLostEvent`** the same way, to sever
a room's sockets on self-eviction or a per-room ownership mismatch and mark those closures
instance-initiated — `room-lifecycle.md` §1.5 layer 3/§1.6's socket-closing half, which `IMP-M2-03`
could not build itself since no STOMP registry existed there either.

---

### IMP-M2-03 — Ownership claim, lease, epoch fence

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-06 (`IMP-GATE-40`: moved off `IMP-M2-02` —
nothing in this item's own read-list needs REST or STOMP to exist first, and both `IMP-M2-01` and
`IMP-M2-02` need this item's claim component, not the other way round)

**Done 2026-09-08 (session 37).** `room.RoomOwnershipService` — `claim()` runs §1.2's script verbatim
(`REDIRECT`=0, `ALREADY_MINE`=1, `ADOPTED`=2, matching the spec and `room-rest-api.md`'s own table
exactly, not a locally-renumbered equivalent) over `room:{roomId}:pod`/`:epoch`; `adopt()` is §1.4
steps 1–3 and 7 in one fenced `UPDATE ... WHERE owner_epoch < :epoch RETURNING version` — a guard
failure returns `Superseded` and self-evicts that room without retrying in place, matching §1.4 step
3's "abandon the adoption" instruction literally. `release()` is §1.3's compare-and-delete plus the
Postgres mirror, never resetting `owner_epoch`. `renewAndRecheck()` (`room.RoomOwnershipSchedulingConfig`,
`turnbase.room.lease.renew-interval`, no `@SchedulerLock` — every instance renews its own key, this is
not a cluster-wide job) renews via `SET ... XX` and treats a `false` reply as a proven lease lapse
(§1.5 layer 2/3), never a renewal-failure guess; it also independently re-verifies `room:{roomId}:pod`
for every locally-owned room on the same tick, so a Redis flush that steals one room's key evicts only
that room, not the whole instance. `epochOf()`/`nextVersion()` expose the two primitives every future
room-mutating item (`IMP-M2-04` onward) fences its own writes on.

**Steps 4–6 and 8 of §1.4 adoption (grace-period reservations, `connection_count` reset, session
re-dispatch, suppressed disconnect events), and §1.6's graceful-shutdown socket-closing sequence, are
not this item's** — they need `room_participant`/session infrastructure and a STOMP session registry
that do not exist yet. `RoomOwnershipLostEvent` is published on self-eviction and on a per-room
ownership mismatch with no subscriber yet, the same inversion `IMP-M1-06`'s `SessionRevokedEvent`
already established (`IMP-GATE-28`) — `IMP-M2-02`'s STOMP registry is the intended subscriber, and its
own Done-when already expects to build the disconnect-handler-skips-tagged-closes behaviour once it
exists. `IMP-M2-07`/`IMP-M2-08` own §1.4 steps 4–5 and grace-period semantics generally; Game Host
session dispatch (step 6) is M3's. Recorded as a sentence per item, not a gate — this item's own
Done-when never required them; `IMP-GATE-40`'s own text already scoped the dependency reorder to the
claim/fence mechanism, not full adoption.

**Verified.** `RoomOwnershipServiceIT` (9 tests, two full `TurnBaseApplication` contexts sharing one
Postgres/Redis, standing in for two pods — `PodIdentity` is a random-per-boot singleton so the two
naturally get distinct `podId`s): first claim adopts and stamps the room row; re-claiming is
idempotent and does not bump the epoch; a second instance is redirected while the incumbent's lease is
live and the room row is untouched; a second instance adopts once the incumbent's lease is deleted
(simulating lapse), epoch advances monotonically (2, never reset); self-eviction on lease lapse drops
every owned room and never recreates the liveness key; a per-room ownership mismatch (simulated Redis
flush) evicts only that room; a forged higher `owner_epoch` makes adoption's own guard fail and return
`Superseded`; release is graceful and never resets the epoch; `nextVersion()` assigns from the adopted
value and never goes backwards. `./mvnw verify -Pintegration` green locally (99 tests, JaCoCo merged
gate met); CI green on `turnbase-platform` `master` (`build`, 11m4s — `e2e`'s "Check out
turnbase-game-host" step fails on the same un-provisioned `TURNBASE_GAME_HOST_PAT` every prior
session's accepted run also shows).

**Read first:**
- `docs/decisions/0008-room-ownership-lifecycle.md` **in full**
- `docs/specs/platform/room-lifecycle.md` §1 (all six subsections) and §2
- `docs/specs/platform/data-model.md` §1 — `owner_epoch`, `version`
- `docs/specs/deployment/local-environment.md` §7.1
- `docs/specs/flows/05-owner-loss-and-adoption.md`

**Satisfies:** `platform-architecture.md` FR-SCALE-001…007, NFR-AVAIL-001; `platform-operations.md`
NFR-AVAIL-001; ADR-0008

**Done when:** the claim script is atomic and is **also the failure detector** — no dead-pod watcher
exists anywhere in this design. The four layers of §1 are all present: atomicity, the
`pod:{podId}:alive` liveness gate (10 s TTL, renewed every 3 s), self-eviction on lease lapse via
`SET … XX`, and the owner-epoch fence. Every ownership-fenced write carries `WHERE owner_epoch <
:myEpoch` on adoption and the epoch **equality** fence on mutation. Invariant I1 holds.

**Self-eviction triggers on lease *lapse*, not on renewal failure.** A stop-the-world pause longer
than the TTL produces no failed renewal to observe — the pod simply wakes up holding a key that
expired and was taken. A renewal-failure check misses exactly the case that matters.

**The room version is not a fence token.** It is room-scoped and both producers advance it densely
from one sequence, so a stale owner is eventually *reached* by the legitimate owner and its CAS then
matches. Use the owner epoch.

**Instance-initiated closes are tagged and the disconnect handler skips them** (§1.5 layer 3, §1.6).
A drain or a self-eviction closes sockets deliberately; treating those closes as player disconnects
starts grace deadlines for players who never went anywhere.

---

### IMP-M2-04 — Room event versioning and fan-out

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-01, IMP-M2-03

**Done 2026-09-09 (session 40).** `room.RoomEventExecutor` — a per-room `ReentrantLock`, keyed in a
`ConcurrentHashMap`, wrapping a `TransactionTemplate`-scoped mutation plus the fenced conditional
`UPDATE room SET version = …` and a post-commit `SimpMessagingTemplate.convertAndSend` to
`/topic/room.{roomId}`, all before the lock releases. Version assignment is
`RoomOwnershipService.nextVersion`'s existing in-JVM `AtomicLong` (`IMP-M2-03`), never a fresh read.
A fenced-commit failure (zero rows updated) calls the new `RoomOwnershipService.evictAfterFailedCas`
rather than retrying in place, matching `room-lifecycle.md` §2.1's "a failed CAS leaves the in-memory
room state dirty" — the next claim re-initializes from the database. A lock-acquisition timeout or a
statement timeout fails the command without evicting, per the same section.

Retrofitted REST join/leave (`IMP-GATE-43`/`44`): join's ownership claim moves before its transaction
(`RoomService.join`) so the mutation runs fenced and versioned inside the lock; a no-op join
(already a member) and a no-op leave (not a member) skip the executor's version bump and broadcast
entirely. Leave claims opportunistically and, when this instance doesn't own the room, falls back to
an unfenced update with no broadcast — the departure still commits (`204`), deferring the
announcement to the owning instance's next sweep, matching `releaseCallersCurrentRoom`'s existing
precedent for a caller's *other* room.

**Verified.** `RoomEventExecutorIT` (mechanism level): a mutation with an event assigns and commits
the next version from the counter (not a fresh `max()`), a no-event mutation never touches
`room.version`, a fenced-commit failure evicts the room and fails with `RoomUnavailableRetryException`
rather than retrying, and executing against an unclaimed room fails without mutating.
`RoomEventFanoutIT` (end to end, a real STOMP subscriber on `/topic/room.{roomId}`): a second player's
REST join broadcasts a version-1 `PLAYER_JOINED` with the correct payload, a re-join broadcasts
nothing, a REST leave broadcasts a version-2 `PLAYER_LEFT`, and a second leave broadcasts nothing.
`./mvnw verify -Pintegration` green locally (134 tests, merged JaCoCo gate met, run solitary after an
accidental concurrent double-run produced one Testcontainers-Postgres `Connection refused` flake in an
unrelated class, `JwtKeyRotationServiceIT` — confirmed non-reproducing in isolation). CI green on
`turnbase-platform` `master` (`build`, 12m).

**Closed:** IMP-GATE-43 (opened and closed 2026-09-09, session 40) — this item's own read-list
(`room-websocket.md` *Per-Room Serialization and Versioning*) states that every room mutation,
"whether REST-originated (join, leave, create) or STOMP-originated," acquires the room lock, commits
the version, and publishes the delta — and `room-rest-api.md` §5 (`IMP-M2-01`'s own read-list) says
outright that `PLAYER_JOINED` "is broadcast by the owning instance after the commit... not by this
handler synchronously," while `room-websocket.md`'s own `PLAYER_JOINED` entry says it is "Emitted
after the REST join call completes." But `IMP-M2-01` (`DONE`) built REST create/join/leave with no
lock, no version increment beyond the creation-time `0`, and no delta publish — because the
mechanism those sentences presuppose (a lock-scoped, version-assigning, commit-then-publish
executor) is exactly what this item builds, and did not exist until now. No item's *Done when*
clause named the REST retrofit explicitly, so the gap was invisible until this item's read-list was
checked against `IMP-M2-01`'s already-shipped code. Same shape as `IMP-GATE-08`/`28`: a duty that
presupposes infrastructure a later item builds. Fixed: this item's *Depends on* gains `IMP-M2-01`
(the handlers it retrofits); its read-list gains `room-rest-api.md` §5 (join) and §6 (leave); its
*Done when* gains the two explicit broadcast clauses below. Room **creation** needs no retrofit: at
insert time no pod has yet claimed the room (the Redis claim and the in-JVM epoch/version state this
item's executor relies on are both established *after* `createRoom` returns), so there is no lock to
acquire and no subscriber to publish to — `version = 0` at insert is already correct, not a mutation
awaiting a delta.

**Closed:** IMP-GATE-44 (opened and closed 2026-09-09, session 40) — `room-rest-api.md` §5 (join)
documented the Redis claim as running *after* the join transaction commits, but `room-lifecycle.md`
§2.1 and `room-websocket.md`'s own versioning section — both in this item's read-list — normatively
require "lock outer → transaction inner → publish after commit," and §2.1 says a stalled database
"blocks every operation on that room, including REST joins" — which only holds if a REST join
acquires the *same* lock a STOMP command does, before its mutation, not after. Claim-after-commit and
lock-before-transaction cannot both be true for the same endpoint. Fixed, in `room-rest-api.md`: §5's
claim moves to step 0, before the transaction — this does not reintroduce the remote-call-in-a-
transaction problem `room-lifecycle.md` §4 forbids (the claim is still outside the transaction, only
earlier), and the one cost (a validation failure after a successful claim leaves this instance owning
a room it added nobody to) is harmless. §6 (leave) gained the matching claim/lock/version/broadcast
paragraph — leave never claimed at all before this — with one deliberate asymmetry: leave's own
existing text already accepts "this handler may be executing on an instance that does not hold
\[the claim\]," so a failed claim there skips the lock/version/broadcast rather than failing the
request (`204` still holds; the departure is announced on the owning instance's next sweep instead),
where join's failed claim still fails the request as before.

**Read first:**
- `docs/specs/platform/room-lifecycle.md` §2 (*Versioning*)
- `docs/specs/api-design/room-websocket.md` — *Per-Room Serialization and Versioning*, *Server→Client
  Event Catalogue* (`PLAYER_JOINED`, `PLAYER_LEFT`), *Client Reconciliation*
- `docs/specs/api-design/room-rest-api.md` §5 (join — the `PLAYER_JOINED` broadcast this item wires
  up), §6 (leave — `PLAYER_LEFT`)
- `docs/specs/platform/data-model.md` §1 (`version`)
- `docs/decisions/0002-websocket-room-affinity.md`

**Satisfies:** `platform-architecture.md` FR-DELIVER-001…006; `game-rooms.md` NFR-PERF-002

**Done when:** the version is committed to Postgres **before** the delta is published, and is
**assigned**, never `max()`-ed. Clients discard `delta.version <= localVersion`, so a pod that
re-issues a seen version is silently and permanently wrong for every client — strictly worse than a
gap. Chat is excluded from the counter entirely (`version: null`, IMP-M2-11). The REST join
transaction of `room-rest-api.md` §5 broadcasts `PLAYER_JOINED` and the REST leave transaction of §6
broadcasts `PLAYER_LEFT`, both through this mechanism and both after their own commit — closing the
gap `IMP-M2-01` (`DONE`) left open pending this item's mechanism (`IMP-GATE-43`).

---

### IMP-M2-05 — Join, teams, readiness

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-04

**Done 2026-09-09 (session 40).** Two new STOMP `@Controller`s dispatch on the command envelope's
`type` field, since STOMP routes by destination rather than by a field inside the frame body:
`RoomMemberCommandController` (`/app/room.{roomId}.member` — the whole Member Commands table:
`TOGGLE_READY`, `SWITCH_TO_SPECTATOR`, `SWITCH_TO_PLAYER`, `REQUEST_ROOM_STATE`) and
`RoomHostCommandController` (`/app/room.{roomId}.host` — this item's own slice: `ADD_TEAM`,
`REMOVE_TEAM`, `RESIZE_TEAM`, `REASSIGN_PLAYER`, `ADD_AI_PLAYER`; `KICK_PLAYER`/
`CHANGE_PARAMETERS`/`START_GAME`/`TRANSFER_HOST` are `IMP-M2-06`'s, whose FR-HOST/FR-XFER
requirements this item's read-list never names). Every mutation runs through `RoomEventExecutor`'s
lock — the "lock outer → transaction inner → publish after commit" nesting `IMP-M2-04` built —
with a fresh `RoomCommandException` carrying one of `room-websocket.md`'s closed error codes on
every precondition failure, caught at the dispatch site (not `@MessageExceptionHandler`) so the
originating command's `correlationId` can be echoed on `/user/queue/errors`. Authorization is
handler-level and authoritative: no channel-level fast-fail exists for these destinations
(`IMP-M2-02` deferred it), so every command re-verifies membership/role/host identity itself, under
the lock — required regardless for host commands, since host identity is mutable runtime state.

`RoomRepository` gained the readiness/role-switch/team-management mutations and the `ROOM_STATE`
snapshot assembly (`Snapshot Delivery`); team template parsing now also carries the manifest's
`name` field (`manifest-schema.md` § `teamTemplates`, defaulting to `"Team"`), needed for
`TEAM_ADDED`/`ROOM_STATE` payloads and unused until this item. `ROOM_STATE.players[].connected` is
unconditionally `true`: connection/disconnect tracking is `IMP-M2-07`'s, so no present participant
can be anything but connected before that item lands — not a shortcut, an honest reflection of what
the system can track today. `PLAYER_REASSIGNED.readinessReset` is likewise unconditionally `true`:
no AI seat can ever exist (IR-12), so the human-only branch is the only one reachable.

**FR-READY-004 (readiness resets on the return to Lobby) has no code here** for the same shape of
reason as `ADD_AI_PLAYER` below: nothing in the build so far can start a game session, so nothing
can end one and return a room to Lobby. The clause is real but unreachable until `IMP-M3-*`/
`IMP-M2-06` give a room a session to return from.

**Verified end to end on real STOMP clients** (`RoomCommandControllerIT`): readiness and role-switch
preconditions and broadcasts (including the host's `ROLE_NOT_ELIGIBLE` on `TOGGLE_READY`/
`SWITCH_TO_SPECTATOR`, `IMP-GATE-45`); team management preconditions (`TEMPLATE_MAX_TEAMS`,
`SIZE_OUT_OF_RANGE`, `TEAM_NOT_EMPTY`, `OVER_CAPACITY` via `RESIZE_TEAM`, `TEAM_FULL` via
`REASSIGN_PLAYER`); `NOT_HOST` for a non-host sender; `AI_NOT_SUPPORTED`; `UNKNOWN_COMMAND`; and a
unicast, version-stamped `ROOM_STATE` snapshot. `./mvnw verify -Pintegration` green locally (141
unit + 121 integration tests, coverage checks met). **CI green on `turnbase-platform` `master`**
(`build`, 13m15s); `e2e`'s "Check out turnbase-game-host" step fails on the same un-provisioned
`TURNBASE_GAME_HOST_PAT` every prior session's accepted run also shows.

**Closed:** IMP-GATE-45 (opened and closed 2026-09-09, session 40) — the Member Commands table's
*Authorized sender* column states a role precondition for `TOGGLE_READY`/`SWITCH_TO_SPECTATOR`
(non-host human player) and `SWITCH_TO_PLAYER` (spectator), but the error-code registry — which
states its own completeness ("the registry for every WebSocket error code in the corpus") — had no
code for violating it: `NOT_HOST` is host-only-command-sent-by-non-host, the opposite direction. Fixed:
`room-websocket.md` gained `ROLE_NOT_ELIGIBLE`, a note stating the *Authorized sender* column is
server-enforced (unlike FR-JOIN-008–010's client-side-only abandonment prompts), and the error table
row.

**Read first:**
- `docs/requirements/game-rooms.md` FR-JOIN-001…011, FR-TEAM-001…012, FR-READY-001…004,
  FR-LIFE-004…006
- `docs/specs/api-design/room-websocket.md` — *Client→Server Command Catalogue* and the matching
  server events
- `docs/specs/api-design/room-rest-api.md` §5 (the REST join, which precedes every STOMP command)
- `docs/specs/platform/data-model.md` §2, §3
- `docs/specs/flows/02-room-to-game-start.md`

**Satisfies:** `game-rooms.md` FR-JOIN-001…006, FR-JOIN-008…011, FR-TEAM-001…012, FR-READY-001…004,
FR-LIFE-005…006, FR-HOST-003, NFR-SPEC-001; `platform-views.md` VW-RLOBBY-001…007, VW-RLOBBY-009…017

**`FR-HOST-003` added retroactively** (`IMP-GATE-46`, session 41, this item not reopened) — the
`ADD_AI_PLAYER` → `AI_NOT_SUPPORTED` behaviour below already satisfies it in full; `IMP-M2-06`'s
Done-when clause had duplicated the same check under its own claim.

**Done when:** auto-assignment follows FR-TEAM-005, and FR-TEAM-012's team instantiation happens
**before** the host is seated on room creation — a host assigned first has nowhere to go;
FR-TEAM-010's capacity floor is checked on **every** operation that could reduce total capacity, not
only on explicit slot removal (moving a player and removing a team both can); readiness resets on
the return to Lobby (FR-READY-004). **FR-JOIN-007 (the single-room constraint) belongs to
`IMP-M2-01`'s REST join transaction, not here** (`IMP-GATE-39`) — by the time a STOMP command is
reachable the caller already holds exactly one room's slot.

**AI is wire-present and behaviour-absent in v1** (IR-12). `ADD_AI_PLAYER` always returns
`AI_NOT_SUPPORTED`, the room snapshot's `aiPlayers` is always empty, and FR-READY-002 ("AI players are
always ready") is therefore implemented and unreachable. Implement it anyway; do not delete the
branch, and do not build an AI seat to make it reachable.

---

### IMP-M2-06 — Host management and transfer

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-05

**Done 2026-09-10 (session 41).** `RoomHostCommandController`'s switch gains `KICK_PLAYER`,
`CHANGE_PARAMETERS`, `START_GAME`, `TRANSFER_HOST`, each re-verifying host identity under
`RoomEventExecutor`'s lock like `IMP-M2-05`'s share. `CHANGE_PARAMETERS` validates every key against
the pinned game version's manifest parameter schema (`input-validation.md`'s whitelist — unknown key,
type mismatch, or out-of-range value) and persists the full merged set, not just the changed keys.
`START_GAME` evaluates FR-TEAM-009's three conditions atomically under the lock, collecting every
unmet condition into `START_CONDITIONS_NOT_MET`'s `details` rather than stopping at the first; on
success it calls a new `GameSessionStarter` port, whose only implementation
(`PendingGameSessionStarter`) is a deliberate no-op — no broadcast, no state change — since
`GAME_STARTED` requires a real `sessionId` that does not exist until `IMP-M3-05`. `KICK_PLAYER`
unicasts `KICKED` to the removed player (no `correlationId`, per `room-websocket.md`'s exact shape)
and conditionally enqueues a `player_left` game-backend input when a session is attached — currently
unreachable, since nothing before `IMP-M3-05` can attach one, the same "real but unreachable" shape
`IMP-M2-05` left for `FR-READY-004`. `TRANSFER_HOST` moves only `room.host_user_id`; the former host
keeps their player slot (FR-XFER-004).

**Verified end to end on real STOMP clients** (`RoomCommandControllerIT`, a fourth test method):
`NOT_HOST` for every command sent by a non-host; `PLAYER_NOT_FOUND` for an unknown kick target;
`PLAYER_KICKED` broadcast plus the kicked player's own unicast; `UNKNOWN_PARAMETER`/
`PARAMETER_TYPE_MISMATCH`/`PARAMETER_OUT_OF_RANGE` for each `CHANGE_PARAMETERS` whitelist rule, then
`PARAMETERS_CHANGED` carrying the full merged set; `START_CONDITIONS_NOT_MET` with a non-empty
`failedConditions` list while a non-host player is un-ready, then silence (no error, no broadcast, no
state change) once ready; `TARGET_NOT_PLAYER` for a `TRANSFER_HOST` naming a non-participant, then
`HOST_TRANSFERRED`, after which the former host's own further host commands get `NOT_HOST`.
`./mvnw verify -Pintegration` green locally (full suite: 122 tests, coverage checks met). **CI green
on `turnbase-platform` `master`** (`build`, 15m22s).

**Closed:** IMP-GATE-46 (opened and closed 2026-09-10, session 41) — this item's *Satisfies* and
*Done when* claimed five things it does not actually build, and were silent on the command surface
its own title names:

1. **FR-HOST-003 was already shipped by `IMP-M2-05`** (`RoomHostCommandController`'s `ADD_AI_PLAYER`
   returning `AI_NOT_SUPPORTED` unconditionally, verified by `RoomCommandControllerIT`) — this item's
   Done-when clause repeated a check that already passes and always will, since no dependency of this
   item changes that behaviour.
2. **FR-HDISC-001…004 is double-claimed with `IMP-M2-07`**, which already claims the identical range
   in full and is titled *Disconnect, grace deadlines, sweeps*. Worse, this item's own Done-when
   assigned itself "the sweep that closes `migration_window_expires_at`" — but `room-lifecycle.md`
   §5.1 defines that as **duty 3 of one ordered tick** alongside due expiries (duty 1), deferred tails
   (duty 2) and the outbox drain (duty 4), all squarely `IMP-M2-07`'s, which is not this item's
   dependency and has no sweep scaffolding in the codebase at all yet. Splitting duty 3 into a
   separate item is not merely awkward, it is unbuildable: there is no sweep tick for it to be a duty
   *of*.
3. **FR-XFER-002 and FR-XFER-005 are double-claimed with `IMP-M2-09`**, which builds the one
   `detachSession` method (`room-lifecycle.md` §4) that both requirements actually run through; no
   command in this item's own command set (`KICK_PLAYER`, `CHANGE_PARAMETERS`, `START_GAME`,
   `TRANSFER_HOST`) closes a room.
4. **FR-HOST-001 is double-claimed with `IMP-M2-12`** (*Room invitations*), which already owns it —
   invite-via-notification has nothing to do with a realtime host command.
5. **FR-HOST-009's happy path is unsatisfiable as written**: `room-websocket.md`'s `GAME_STARTED`
   event requires a real `sessionId` and `gameFrontendUrl`, which only exist once a game session has
   actually been created — machinery `IMP-M3-05` (*Orchestration client and session registry*) builds,
   and which is not this item's dependency. Same shape as `IMP-GATE-08`/`18`/`28`.
6. Incidentally found while resolving (3): `IMP-M2-09`'s own *Satisfies* also names **FR-XFER-003**,
   which `IMP-GATE-39` already assigned to `IMP-M2-01` in full (the REST-layer `state <> 'CLOSED'`
   listing predicate) — a second, unrelated double-claim on the same requirement. Fixed on `IMP-M2-09`
   below.

Fixed: this item's *Satisfies* narrows to `FR-HOST-006…009, FR-XFER-004` — the four commands
(`KICK_PLAYER`, `CHANGE_PARAMETERS`, `START_GAME`'s precondition/rejection half, `TRANSFER_HOST`) this
item actually builds. Its read-list drops `reconnection-flow.md`, `room-lifecycle.md` §3/§5 and
`data-model.md` §1's `migration_window_expires_at` — none of it is this item's mechanism any more.
`IMP-M2-07`'s own Done-when gains an explicit duty-3 clause (it already claimed FR-HDISC-004 in full
but never tested it — same shape as `IMP-GATE-34`). `IMP-M2-09`'s *Satisfies* drops `FR-XFER-003`.
`IMP-M2-05`'s *Satisfies* (`DONE`, not reopened) gains `FR-HOST-003` to match what it already shipped.
FR-HOST-009's success path — actually creating a session and broadcasting `GAME_STARTED` with a live
`sessionId`/`gameFrontendUrl` — is deferred to `IMP-M3-05`, which gains the clause below; this item
instead defines a narrow `GameSessionStarter` port and proves `START_GAME`'s precondition-check and
rejection path against an in-process stub, the same pattern `IMP-GATE-08` established for
`GameHostRegistryService`.

**Read first:**
- `docs/requirements/game-rooms.md` FR-HOST-006…009, FR-TEAM-009, FR-XFER-004
- `docs/specs/api-design/input-validation.md` — `CHANGE_PARAMETERS`' whitelist validation against the
  game manifest's declared parameter schema
- `docs/specs/api-design/room-websocket.md` — the Host Commands table and its four events
  (`PLAYER_KICKED`/`KICKED`, `PARAMETERS_CHANGED`, `GAME_STARTED`, `HOST_TRANSFERRED`)
- `docs/requirements/game-contracts.md` FR-IN-005 — the `player_left` input's `kicked` payload shape
  for the conditional `game_input_outbox` insert (no other read-list document defines it; repaired,
  no gate — a plain missing citation, same shape as `IMP-M2-01`'s manifest-schema.md fix)

**Satisfies:** `game-rooms.md` FR-HOST-006…009, FR-XFER-004.

**Done when:**

- `KICK_PLAYER` removes a human, AI, or spectator member in any room state; in In Progress it voids
  any active grace period on the target and enqueues a `player_left` game-backend input with
  `reason: kicked` (deferred to `IMP-M3-06`'s outbox — this item writes the row, it does not drain
  it); the kicked party receives a unicast `KICKED` error on `/user/queue/errors`.
- `CHANGE_PARAMETERS` is Lobby-only and whitelist-validated against the pinned game version's manifest
  parameter schema (`input-validation.md`): an undeclared key is `UNKNOWN_PARAMETER`, a type mismatch
  is `PARAMETER_TYPE_MISMATCH`, an out-of-range value is `PARAMETER_OUT_OF_RANGE`. Accepted changes
  broadcast and are retained verbatim across the room's return to Lobby (FR-HOST-008) — nothing here
  yet resets them, since nothing yet ends a game.
- `START_GAME` evaluates FR-TEAM-009's three conditions atomically under the room lock; any unmet
  condition rejects with `START_CONDITIONS_NOT_MET` and lists every failed condition, not just the
  first. On success it calls a new `GameSessionStarter` port; this item proves the call against an
  in-process stub implementation only — the real implementation, a live `sessionId`/`gameFrontendUrl`
  and the `GAME_STARTED` broadcast are `IMP-M3-05`'s clause, added there.
- `TRANSFER_HOST` requires the target to be a current human player (not spectator, not AI):
  `TARGET_NOT_PLAYER` otherwise. The former host retains their player slot and becomes a regular
  player (FR-XFER-004); valid in both Lobby and In Progress.
- Every handler re-verifies `principal.id == room.hostId` inside the lock, not just at the channel
  guard, since a `TRANSFER_HOST` command — including one racing this one — can change
  `room.hostId` between the two.

---

### IMP-M2-07 — Disconnect, grace deadlines, sweeps

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-03

**Done 2026-09-10 (session 43).** `room.RoomSubscriptionAuthorizer` increments
`room_participant.connection_count` on a session's first `SUBSCRIBE` to the bare room topic (the
mirror of the decrement below, and the missing piece that made the refcount design real for the
first time) and feeds a genuine `SessionDisconnectEvent` into a new `room.RoomService#onDisconnect`
— the membership map doubles as the instance-initiated-close tag (§1.5 layer 3/§1.6): `onRoomOwnershipLost`
removes a session from it *before* severing the socket, so the disconnect handler that fires
afterward correctly sees nothing to process, while a revoked or rate-limited session (which never
touches this map) is still processed as a genuine involuntary disconnect. `onDisconnect` runs
`RoomRepository#registerDisconnect` under `RoomEventExecutor`'s lock: still-connected (another tab)
is a no-op; Lobby or spectator (any state) is an immediate leave reusing `leaveRoom`; In-Progress
player opens a grace reservation (§3.1) and, if the disconnecting user was host, a second fenced
call applies FR-HDISC-001's immediate transfer to the next connected human by join order, unless
the migration window is open (FR-HDISC-004) or nobody else is connected (FR-HDISC-003, deferred).

`room.GraceDeadlineSweepJob` (`turnbase.jobs.deadline-sweep.interval`, no `@SchedulerLock` —
ownership-partitioned like `RoomOwnershipService`'s own lease renewal, ***not*** a cluster-wide job)
runs all four §5.1 duties in order: due expiries (§3.2's resolve statement, `announceInline=true`,
with §3.3 step 2's outbox insert conditional on `active_session_id IS NOT NULL`, IR-06); deferred
tails (announces a foreign instance's `EARLY_RELEASE`/`GRACE_EXPIRED`/`LEFT` resolution, then
applies FR-XFER-001 host disposition — transfer to the next connected human, or leave it for
closure to decide); elapsed migration windows (FR-HDISC-004, clearing the column and performing the
deferred transfer); and the outbox drain (not ownership-partitioned — a gRPC call needs no room
claim — allocating each row's `sequence` once and stamping `dispatched_at` only on ACK). Both
duty 1's and duty 2's closure evaluation call a new `room.RoomSessionDetacher` seam
(`IMP-GATE-49`).

**`IMP-GATE-48`'s adoption fix carried a correction found while testing it**: the mass grace-open
must not run on a room's very first-ever claim, only a genuine takeover — the claim script's own
`ADOPTED` result conflates "free" and "lease lapsed" (§1.2), but the Redis epoch counter still
distinguishes them (epoch 1 is always the first claim). Without this, a fresh room's own creator
was handed a grace reservation before their first `SUBSCRIBE` ever completed, since nothing
distinguishes "never connected" from "connection_count = 0" otherwise.

**Two latent bugs in already-shipped code, exposed by finally building the mechanism they
presuppose:** `RoomRepository#leaveRoom` (`IMP-M2-01`) stamped `lost_announced_at = null`
unconditionally rather than per `:announceInline` (§3.2), which would have made every ordinary
voluntary leave (already announced correctly at leave time) match duty 2's predicate again and
double-broadcast a spurious `PLAYER_LOST` one sweep tick later — fixed by adding the parameter
`RoomService#leave`'s two branches already needed. `releaseCallersCurrentRoom` (`IMP-M2-01`,
FR-EXPIRY-004's early release) never inserted the `player_left` outbox row game-contracts.md FR-IN-005
requires from "the acting instance" — fixed, reusing `insertPlayerLeftOutbox`.

**A discovered JDBC hazard, not a spec defect:** `UPDATE ... RETURNING team_id` mapped through
`.query(UUID.class).optional()` cannot distinguish a genuinely-unmatched row from a matched row
whose `team_id` is itself `null` — both collapse to `Optional.empty()`. `resolveExpiredReservation`
now checks `.list()` emptiness instead, the rowcount being what §3.2 actually promises as "the
entire idempotency story," never the value.

**Verified**, `GraceDeadlineSweepJobIT` (10 methods) plus `RoomOwnershipServiceIT`'s new adoption
test: Lobby/spectator disconnect is an immediate leave with no reservation; a second open tab stops
a disconnect from doing anything; an In-Progress player disconnect opens a reservation and bumps
the version once; a disconnecting host transfers immediately with another human connected and
defers with none; the sweep resolves a due expiry, inserts the outbox row only when a session is
attached, and never fires the outbox insert in a Lobby room whose reservation was forced past due;
a deferred tail announces `PLAYER_LOST` and transfers host to the next connected human; an elapsed
migration window transfers host and clears the column; adoption opens a mass reservation for every
connected player (not spectators), never resets one already running, and skips entirely on a first
claim. `./mvnw verify -Pintegration` green locally (137 tests, merged JaCoCo gate met). **CI green
on `turnbase-platform` `master`** (`build`, 13m9s — `e2e`'s "Check out turnbase-game-host" step
fails on the same un-provisioned `TURNBASE_GAME_HOST_PAT` every prior session's accepted run also
shows).

**Closed:** IMP-GATE-46's second half (`IMP-M2-06`, opened and closed 2026-09-10, session 41) — this
item's *Satisfies* already claimed `FR-HDISC-001…004` in full, but its *Done when* never tested
FR-HDISC-004 (the migration-window sweep) — the same claim-without-a-clause shape as `IMP-GATE-34`.
Fixed: the clause below gains duty 3 explicitly, and `data-model.md` §1's `migration_window_expires_at`
joins the read-list (moved here from `IMP-M2-06`, which never had a mechanism to attach it to).

**Closed:** IMP-GATE-48 (opened and closed 2026-09-10, session 43) — `room.RoomOwnershipService`
(`IMP-M2-03`, `DONE`) explicitly defers `room-lifecycle.md` §1.4 adoption steps 4–5 (opening a grace
reservation for every participant with `connection_count > 0` and no reservation already outstanding,
`COALESCE`-guarded; zeroing their `connection_count`) to "`IMP-M2-07`/`IMP-M2-08`", but neither item's
read-list named §1.4 and neither item's *Done when* tested it — the same claim-without-an-owner shape
as `IMP-GATE-47`. Without it, a mass owner-pod-loss disconnect (FR-DC-006) that this item's own
`reconnection-flow.md` FR-DC-006/007 Satisfies-range covers had no mechanism opening the reservations
it is enforcing: adoption's own comment already says "steps 4–6 and 8 ... need `room_participant`
... infrastructure" — infrastructure this item is the one to build, since it owns §3.1's
individual-disconnect grace-opening statement that step 4/5 is the mass-adoption analogue of.
`IMP-M2-08` ("Reconnect and resync") is about a client's return, not about opening reservations for
participants who were connected when the room's previous owner died — the wrong item for this duty.
Fixed: `IMP-M2-07`'s read-list gains `room-lifecycle.md` §1.4 (adoption, steps 4–5 and 7 only — step 6
stays Game Host dispatch's, M3's; step 8 needs no code, since neither this item nor `IMP-M2-03` emits
a per-player event on adoption); its *Done when* gains the explicit clause below.

**Closed:** IMP-GATE-49 (opened and closed 2026-09-10, session 43) — "the sweep tick runs all four
§5.1 duties" requires duty 1's closure evaluation (§3.3 step 4) and duty 2's closure half, both of
which call `detachSession` (§4) — but §4 is `IMP-M2-09`'s own item ("Room closure and the five detach
paths"), which **depends on `IMP-M2-07`**. Requiring it here is circular as written: `IMP-M2-09`
cannot exist yet to supply it, and this item's own read-list never named §4 either. Same shape as
`IMP-GATE-40`, one milestone over — a foundational shared primitive assigned to the item that needs it
*second*. Unlike `IMP-GATE-40`'s fix (reorder the dependency), `detachSession`'s remaining four callers
(host-leave, game-end, retry-limit-failure, reconciliation) are all `IMP-M2-09`'s or later items' own,
so moving the whole mechanism here would leave `IMP-M2-09` an empty shell. Fixed with the seam already
established for the identical shape of problem in `room.GameSessionStarter`/`PendingGameSessionStarter`
(`START_GAME`'s own downstream dependency on `IMP-M3-05`, which does not exist at `IMP-M2-05`'s build
time either): a new package-private `room.RoomSessionDetacher` interface
(`detach(roomId, sessionId, reason, nextState)`, matching §4's own signature), called by duty 1 after a
won expiry leaves no human and by duty 2 after announcing a deferred tail whose participant was the
room's last human; `room.PendingRoomSessionDetacher` is a no-op default bean, honest because no room
can reach a real `IN_PROGRESS` state with a live session before `IMP-M3-05` lands regardless — the
same reasoning `PendingGameSessionStarter`'s own doc comment already gives. `IMP-M2-09`'s read-list
gains `room-lifecycle.md` §3.3 step 4 and §5.1 duty 2 (to know it is replacing a live seam, not writing
new call sites); its *Done when* gains a clause: replace `PendingRoomSessionDetacher` with a real
`detachSession` implementation wired into the two call sites `IMP-M2-07` already built, rather than
adding its own.

**Read first:**
- `docs/decisions/0009-grace-deadline-durability.md`
- `docs/specs/platform/room-lifecycle.md` §3 **in full** (especially §3.2's resolve statement and
  §3.3's conditional outbox insert), §5.1 **in full** — all four sweep duties, including duty 3
  (elapsed migration windows), are this item's — and §1.4 steps 4–5 and 7 (`IMP-GATE-48`: adoption's
  own mass grace-opening, the `COALESCE`-guarded analogue of §3.1 for every participant left connected
  when the previous owner was lost) — and §4's `detachSession`/`terminateAndCleanup` signature only
  (`IMP-GATE-49`: the seam this item calls into, not the mechanism it builds)
- `docs/requirements/reconnection-flow.md` FR-DC-001…007, FR-GRACE-001…006, FR-EXPIRY-001…006,
  FR-KICK-001…004, FR-HDISC-001…004
- `docs/specs/platform/data-model.md` §1 — `migration_window_expires_at`; §2 — `left_at`,
  `leave_reason`, `lost_announced_at`
- `docs/specs/deployment/local-environment.md` §7.1
- `docs/specs/flows/04-disconnect-and-return.md`

**Satisfies:** `reconnection-flow.md` FR-DC-001…007, FR-GRACE-001…006, FR-EXPIRY-001…006,
FR-KICK-001…004, FR-HDISC-001…004, NFR-CONF-001…003, NFR-PERF-001…003

**Done when:** deadlines are **persisted absolute timestamps, swept** — with no in-process timer. Two
mechanisms enforcing one deadline is a dual write and a three-way race on every reconnect. The
Postgres clock is the single time authority, which removes clock skew by construction.

Grace expiry must not fire in a **Lobby** room; `reconnection-flow.md` FR-DC-007 exists to stop a
rolling deploy deleting every Lobby room, and a Lobby grace expiry re-creates that bug.

**Two details from the IR-06/IR-09 fixes are load-bearing.** §3.3's `game_input_outbox` insert is
conditional on `room.active_session_id IS NOT NULL` — a departure from a Lobby room has no session to
notify, and the unconditional insert wrote outbox rows nothing would ever drain. And §3.2's resolve
statement stamps `lost_announced_at = CASE WHEN :announceInline THEN now() ELSE NULL END`: a NULL
marks a departure that a *foreign* instance resolved and the owner still owes an announcement for.

**The single sweep tick runs all four §5.1 duties, in order, on one schedule.** Duty 3 — elapsed
migration windows (FR-HDISC-004) — clears `migration_window_expires_at` and, if the host is
disconnected or released while another human is connected, performs the FR-HDISC-001 transfer that
§3.1's own opening deliberately skipped while the window was open. `IMP-M2-03`'s adoption `UPDATE`
already persists the deadline (§1.4 step 7); this item is what closes it. Proving duty 3 requires no
mechanism from any other item — the deadline is a plain column already written.

**`IMP-GATE-48`: adoption itself (§1.4 steps 4–5) opens the mass grace reservation.** When a room is
adopted after owner-pod loss, every participant with `connection_count > 0` and no reservation already
outstanding gets a grace period at `now() + graceSeconds`, `COALESCE`-guarded so a reservation already
running from an earlier individual disconnect is never reset; their `connection_count` is zeroed in the
same step, since their connections died with the previous owner (FR-DC-006). This is `§3.1`'s statement
applied to every eligible participant in one pass rather than one row, called from
`RoomOwnershipService#adopt` inside the same fenced transaction that already sets `owner_epoch`, not
from the sweep — the mass disconnect is observed at the moment of adoption, not on the next tick.

**`IMP-GATE-49`: duty 1 and duty 2's closure evaluation go through a `RoomSessionDetacher` seam.**
Duty 1, after a won expiry (§3.3) leaves no `PLAYER` with `left_at IS NULL`, and duty 2, after
announcing a deferred tail whose departed participant was the room's last human, both call
`detacher.detach(roomId, sessionId, reason, "CLOSED")`. `room.PendingRoomSessionDetacher` — the only
bean until `IMP-M2-09` — is a no-op, matching `GameSessionStarter`/`PendingGameSessionStarter`'s
precedent: no room can carry a real `active_session_id` before `IMP-M3-05` either, so a stub here
costs nothing today and the call site is proven to exist and fire under the right condition, which is
what this item's own tests assert.

---

### IMP-M2-08 — Reconnect and resync

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-07

**Closed:** IMP-GATE-52 (opened and closed 2026-09-13, session 44, found verifying this item's CI
run, fixed in `local-environment.md` §1 — an `IMP-M0-07`/`M0-08` document — and in
`turnbase-platform`'s compose file, Helm chart and Testcontainers pins, none of which this item
otherwise touches) — `local-environment.md` §1 pins `minio/minio` and `minio/mc` with no registry
host, which every consumer (this repo's `docker-compose.yml`, its Helm chart's `values.yaml`, and
`PostgresIntegrationTest`/`ArtifactBucketReadinessCheckIT`'s Testcontainers pins) resolved as
`docker.io/minio/…` — correct when written, but MinIO stopped publishing to Docker Hub some time
after IR-01/IR-13 were verified, so every one of those pulls now fails
`pull access denied ... repository does not exist`, hard-failing `./mvnw verify -Pintegration` (and,
by the same mechanism, `make e2e` and a fresh `docker compose up`) regardless of which item is being
worked. Confirmed byte-identical on MinIO's current registry before touching anything:
`quay.io/minio/minio:RELEASE.2025-09-07T16-13-09Z` and `quay.io/minio/mc:RELEASE.2025-08-13T08-35-41Z`
both resolve to the exact digests already cached locally under the old, now-dead Docker Hub
reference. Fixed: `local-environment.md` §1's table and its `minio-init` YAML snippet, both
`docker-compose.yml` image lines, both `values.yaml` image lines, and both Testcontainers
`DockerImageName.parse(...)` calls now pin `quay.io/minio/minio`/`quay.io/minio/mc` — same tags, same
digests, new host. Testcontainers' `MinIOContainer` validates the image name against the bare
`minio/minio` repository regardless of host, so both Java pins also add
`.asCompatibleSubstituteFor("minio/minio")` — found only by actually running the fix, not by reading.
No `dependabot.yml` entry named the old host (Docker ecosystem entries key on the bare image name,
`conventions.md` §6), so none needed updating.

**Closed:** IMP-GATE-50 (opened and closed 2026-09-13, session 44) — `data-model.md` §2 states
`room_participant` keeps one row per `(room_id, user_id)` for a user's entire history in a room (never
deleted, `left_at` marks release), but `room-rest-api.md` §5 step 6 said "Insert" unconditionally —
the two cannot both hold the moment a caller re-joins a room they previously departed (voluntary
leave, kick, or grace expiry: exactly this item's own "ordinary join after expiry" clause), since the
row already exists and a plain `INSERT` violates the primary key. Fixed: `data-model.md` §2 and
`room-rest-api.md` §5 step 6 both now specify `INSERT ... ON CONFLICT (room_id, user_id) DO UPDATE`,
reinitializing the row, for exactly the departed-row case.

**Closed:** IMP-GATE-51 (opened and closed 2026-09-13, session 44) — this item's *Satisfies* claimed
`reconnection-flow.md` FR-REJOIN-001…008 in full, but no *Done when* clause tested FR-REJOIN-007 (a
reconnection attempt that loses the race to its own grace expiry must be told plainly, not silently
dropped or failed generically), and no document said which call path emits `room-websocket.md`'s
already-registered `SLOT_RELEASED` error code or under what predicate. Fixed, building on
`IMP-GATE-50`'s row-reuse guarantee: `room-websocket.md`'s Authorization Model now specifies the
predicate (`left_at IS NOT NULL AND leave_reason = 'GRACE_EXPIRED'` on the caller's own
`room_participant` row) and the call site (`SUBSCRIBE` to `/topic/room.{roomId}`, rejecting with
`SLOT_RELEASED` instead of the default silent drop); this item's *Done when* gained the clause below.

**Read first:**
- `docs/requirements/reconnection-flow.md` FR-REJOIN-001…008, NFR-PERF-001…003
- `docs/specs/api-design/room-websocket.md` — *Snapshot Delivery*, *Client Reconciliation*, *
  Authorization Model* (`IMP-GATE-51`)
- `docs/specs/platform/room-lifecycle.md` §2, §3.2
- `docs/specs/platform/data-model.md` §2 (`IMP-GATE-50`)
- `docs/specs/api-design/room-rest-api.md` §5 step 6 (`IMP-GATE-50`)
- `docs/specs/flows/04-disconnect-and-return.md`

**Satisfies:** `reconnection-flow.md` FR-REJOIN-001…008, NFR-PERF-001…003; `game-rooms.md`
FR-JOIN-011

**Done when:** a reconnecting client receives a **snapshot carrying its version**, then deltas from
that version onward — there is no merge path and no partial replay; the server never re-announces a
departure whose `lost_announced_at` is already set; a rejoin inside the grace window restores the
participant's seat and team rather than re-seating them (FR-REJOIN-*, FR-JOIN-011); a rejoin after
expiry is an ordinary join and is subject to every capacity rule; a rejoin that loses the race to its
own grace expiry receives `SLOT_RELEASED` on `SUBSCRIBE` rather than a silent drop (FR-REJOIN-007,
`IMP-GATE-51`).

**Verified.** Code merged to `turnbase-platform master` at `7948aea`, `IMP-GATE-52`'s MinIO re-pin
merged on top at `417ecf9`. `./mvnw verify -Pintegration` green locally, including 4 new
`RoomReconnectIT` methods and 4 new `RoomControllerIT` methods covering every Done-when clause
(snapshot-then-delta, no re-announce of an already-`lost_announced_at` departure, grace-window seat
restoration, post-expiry ordinary join, `IMP-GATE-51`'s `SLOT_RELEASED` race). CI green on
`turnbase-platform master`'s `build` job (run `34749048422`, 18m23s — the two prior runs on `7948aea`
failed only on `IMP-GATE-52`'s pre-fix pull error, not on this item's code). `e2e` failed in the same
run, but past a point it has never reached before: MinIO itself now pulls and starts correctly in the
real compose stack (confirming `IMP-GATE-52` fixes the live stack, not just Testcontainers), and the
job instead died on `lstat /target: no such file or directory` inside the e2e smoke test's own Docker
build context — unrelated to `IMP-M2-08` or `IMP-GATE-52`, and **a different failure than the
`TURNBASE_GAME_HOST_PAT`/checkout error every prior session's accepted run showed**. Not investigated
or gated here (out of this item's scope); next session should expect this new failure mode, not the
old one, when `e2e` is looked at.

---

### IMP-M2-09 — Room closure and the five detach paths

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-07

**Closed: IMP-GATE-53** (opened and closed 2026-09-13, session 45) — this item's own *Done when*
required wiring all three of its remaining `detachSession` callers (host-leave with no humans, normal
game end, retry-limit permanent failure) alongside the two `IMP-M2-07` already wired — but two of the
three have no trigger anywhere in this item's dependency closure. Normal game end (FR-LIFE-002) and
retry-limit permanent failure (FR-FAIL-003/005) both originate in the Orchestration Service —
`platform-architecture.md` FR-FAIL-005 states the Orchestration Service itself "notifies the Room
Service" on permanent failure, and flow 06's game-end trigger is the same actor — which is
`IMP-M3-05` (*Orchestration client and session registry*) and its dependents, none of which this item
depends on or which exist yet: `grep` across `src/main/java` for any game-end or retry-limit call site
turned up nothing, matching `PendingGameSessionStarter`'s own note that no room can carry a real
`active_session_id` before `IMP-M3-05` lands. Unsatisfiable as written — same shape as
`IMP-GATE-08`/`18`/`28`/`46`. Fixed: this item's *Done when* narrows to the mechanism plus the one
caller actually reachable now — host-leave with no humans, wired into `RoomService#leave`'s
already-claimed branch (the REST/voluntary path; the two non-owning arrivals, account deletion and
guest cleanup, already flow through `IMP-M2-07`'s existing deferred-tail duty 2 once the real detacher
lands, per `room-lifecycle.md` §4's own text, and need no new call site here). The other two callers
move to their natural owners: `IMP-M3-08` (*Session teardown as a durable to-do*, already reading
`room-lifecycle.md` §4 and `flows/06-game-end-and-rematch.md`) gains the normal-game-end wiring clause
and `IMP-M2-09` in *Depends on*; `IMP-M3-09` (*Game failure handling*) gains the retry-limit-failure
wiring clause, `room-lifecycle.md` §4 and `flows/07-room-closure.md` in its read-list, and `IMP-M2-09`
in *Depends on*. Both already claim the relevant requirement IDs (`FR-XFER-005` and `FR-FAIL-003/005`
respectively) in their existing *Satisfies*, so neither gains a new claim, only a Done-when clause
naming the call site.

**Closed:** IMP-GATE-46's third half (`IMP-M2-06`, opened and closed 2026-09-10, session 41) — this
item's *Satisfies* named `FR-XFER-003`, which `IMP-GATE-39` already assigned to `IMP-M2-01` in full
(the REST-layer `state <> 'CLOSED'` listing/lookup predicate) — a second, independent double-claim on
the same requirement, found while resolving `IMP-M2-06`'s own overlapping claims. Fixed: narrowed
below to the two requirements this item actually builds.

**Closed:** IMP-GATE-49's other half (`IMP-M2-07`, opened and closed 2026-09-10, session 43) —
`IMP-M2-07`'s own Done-when needed `detachSession` for its sweep's closure evaluation before this item
(`detachSession`'s owner) could exist, since this item depends on `IMP-M2-07`. Fixed there with a
`RoomSessionDetacher` seam (`GameSessionStarter`/`PendingGameSessionStarter`'s precedent); this item's
own read-list gains `room-lifecycle.md` §3.3 step 4 and §5.1 duty 2, and its *Done when* gains the
clause below the SQL block: replace the seam, wired into the two call sites already built, rather than
adding new ones.

**Read first:**
- `docs/specs/platform/room-lifecycle.md` §4 **in full** — the five paths and the fenced step 3 — and
  §3.3 step 4, §5.1 duty 2 (`IMP-GATE-49`: the two call sites this item's real implementation replaces
  a stub at, not writes fresh)
- `docs/specs/flows/07-room-closure.md`
- `docs/decisions/0010-session-teardown-ordering.md`
- `docs/specs/platform/data-model.md` §1 (`closed_at`, `closed_reason`), §4
- `docs/requirements/notifications-invitations.md` FR-INV-008

**Satisfies:** `game-rooms.md` FR-LIFE-007, FR-XFER-002, FR-XFER-005;
`notifications-invitations.md` FR-INV-008

**Done when:** `detachSession` step 3 is a single fenced, version-bumping `UPDATE`:

```sql
UPDATE room
   SET state = :nextState, active_session_id = NULL,
       version = :expected + 1,
       closed_at    = CASE WHEN :nextState = 'CLOSED' THEN now() END,
       closed_reason = CASE WHEN :nextState = 'CLOSED' THEN :reason END
 WHERE room_id = :roomId AND version = :expected AND owner_epoch = :myEpoch;
```

Without the `owner_epoch` fence a stale owner closes a live room. Without the version bump every
client discards the resulting `ROOM_CLOSED` as stale, and the room is closed on the server and open
on every screen.

`notifications-invitations.md` FR-INV-008's deletion of invitations happens **at closure**, not by
the FK cascade that fires seven days later at purge.

**Step 0 defers rather than closing eagerly.** A closure this instance does not own is left as
`lost_announced_at IS NULL` for §5.1 duty 2 to discharge — the same deferred tail an account erasure
uses (IMP-M1-08).

**`IMP-GATE-49`: this item's real `detachSession` replaces `room.PendingRoomSessionDetacher`.**
`IMP-M2-07`'s sweep duty 1 (§3.3 step 4) and duty 2 (closure half) already call
`RoomSessionDetacher#detach` at the moment each condition is met; this item swaps the no-op bean for
one implementing the transaction above and adds nothing at `IMP-M2-07`'s two call sites.

**`IMP-GATE-53` narrowed this item's own third caller to host-leave with no humans** (FR-XFER-002),
wired into `RoomService#leave`'s already-claimed branch: when the departing user is the room's host
and no other human participant remains (`left_at IS NULL AND role = 'PLAYER'`, the same predicate
§3.3 step 4 uses), close immediately with `NO_PLAYERS_REMAINING` instead of an ordinary
`PLAYER_LEFT`. The unclaimed branch is unchanged — it already commits the departure with
`lost_announced_at` left null and returns, exactly `room-lifecycle.md` §4's "a caller that cannot
claim defers through the existing deferred-tail mechanism" — no new closure logic belongs there; the
owning instance's duty 2 evaluates closure (including the host disposition) on its next tick, using
this item's real detacher. Normal game end and retry-limit permanent failure are `IMP-M3-08` and
`IMP-M3-09`'s own callers respectively (`IMP-GATE-53`).

---

### IMP-M2-10 — Adoption and reconciliation jobs

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-03

**Done 2026-09-13 (session 49).** `ReconciliationJob` (`@SchedulerLock`, 60s) runs all five FR-JOB-007
duties in the specified order, `FOR UPDATE SKIP LOCKED`, each idempotent and exposing FR-JOB-011's
per-duty candidate/repair/skip counts: (a) owed teardowns re-driven via `SessionTerminatorImpl` →
`RoomRepository.recordSessionTeardownFailure` (10s-doubling-to-5min backoff), which also resolves the
session 48 open question about `SessionTerminator` being `void` — there is still no Game Host gRPC
client, so every call honestly takes the failure branch and records it, rather than silently
succeeding; (b) orphaned Redis session-key families (age > 10 min) deleted, two-strike via the new
`orphaned_session_flag` table (`IMP-GATE-56`); (c) In-Progress-no-session fails back to Lobby via
`GAME_ENDED (readinessReset: true)`, never closes (`IMP-GATE-55`); (d) idle Lobby rooms close
`IDLE_TIMEOUT`; (e) unowned-room adoption via `RoomOwnershipService.claim()`, exempt from both
FR-JOB-008 guards. Duties (c)/(d) share `room.reconcile_flagged_at`; startup suppression (120s
default) gates (b)/(c)/(d) only, matching `flows/05-owner-loss-and-adoption.md` §D. `RoomPurgeJob`
(FR-JOB-009, daily) purges Closed rooms past retention, cascading participant/team/invite rows.
`ReconciliationMetrics` exposes `turnbase.reconcile.candidates{duty}`,
`turnbase.reconcile.repairs.total{duty,result}`, `turnbase.rooms.in_progress_without_session`,
`turnbase.teardown.owed` and `turnbase.job.aborted.total{job,reason}`. `PodIdentity` gained
`bootAt()` for the suppression guard. Migration `V202609131400__add_orphaned_session_flag.sql`,
`FlywayBaselineIT` updated. `./mvnw verify` and `./mvnw verify -Pintegration` both green locally;
**CI green on `master`** at `852d415`. Landed directly on `master` (branch
`feat/imp-m2-10-reconciliation`, ff-merged and deleted same session as ADR-0012 requires) —
found already merged into the submodule when this session picked the item back up, with only the
parent repo's submodule ref and this registry/STATUS.md bookkeeping left outstanding; both are
caught up now.

**Closed:** IMP-GATE-56 (opened and closed 2026-09-13, session 48) — `room-lifecycle.md` §5.4's
two-strike guard (FR-JOB-008b) names exactly one persistence mechanism, `room.reconcile_flagged_at`,
and states that duties (b)/(c)/(d) all take the guard. But `room.reconcile_flagged_at` lives on the
`room` row, while duty (b)'s candidates are session IDs recovered from a Redis key family, qualified
as orphaned precisely when "the room no longer exists **or** is closed" (`room-lifecycle.md` §5.2) —
the "no longer exists" branch has no room row to stamp a flag on, and even the "closed" branch has no
stable one-to-one room since a room's `active_session_id` is cleared at the same detach that makes the
session's artifacts orphan candidates. No document supplied a persistence mechanism duty (b) could
actually use. Fixed: new `data-model.md` §4.3, `orphaned_session_flag` — a session-scoped table with
the same insert/consult/clear lifecycle as `room.reconcile_flagged_at`, holding no foreign key to
`room` or `session_teardown` since the absence of both is exactly the case it exists to cover;
`room-lifecycle.md` §5.4 guard 2 now names it explicitly for duty (b) and scopes
`room.reconcile_flagged_at` to duties (c)/(d) alone, which is what the surrounding prose already
assumed.

**Closed:** IMP-GATE-55 (opened and closed 2026-09-13, session 47) — `game-rooms.md` FR-LIFE-007 and
`room-websocket.md`'s `ROOM_CLOSED` reason table said an In-Progress room whose session state is gone
is **closed** with `SESSION_UNRECOVERABLE`; `platform-operations.md` FR-JOB-007(c) and
`room-lifecycle.md` §5.2 (this item's own read-list) say it **fails back to Lobby, not closed**
instead — a flat disagreement on first reading. That reading turned out to be incomplete:
`flows/07-room-closure.md` § Caller 5 — a document this item's read-list never named, though it is the
one place all five `detachSession` callers are enumerated together — already reconciles the two sides
with "fail back to Lobby; `SESSION_UNRECOVERABLE` only if that also fails." That reconciliation is
itself hollow: `detachSession`'s shared skeleton (same document)
has exactly two non-success outcomes for any caller — a claim redirect, deferred to the next tick, and
step 2's idempotent no-op when another caller already detached — and neither is a "failure" this duty
could close on. No document, including flow 07, names a third outcome. `SESSION_UNRECOVERABLE` has no
producer under the mechanism as specified anywhere in the corpus. Fixed: `room-lifecycle.md` §5.2's
duty (c) row and prose state explicitly that this duty has no closure branch, citing the skeleton's two
non-success outcomes; `flows/07-room-closure.md`'s Caller 5 table and prose drop the
"`SESSION_UNRECOVERABLE` only if that also fails" hedge; `game-rooms.md` FR-LIFE-007 narrows to the
idle-Lobby-closure case alone, stating the unrecoverable-session case fails back to Lobby instead;
`room-websocket.md`'s `ROOM_CLOSED` reason table and `data-model.md`'s closure-reasons table both drop
`SESSION_UNRECOVERABLE` (five closure paths become four). Separately, duty (c)'s "notify participants"
cited `platform-architecture.md` FR-FAIL-005, which names no wire event, but the behaviour it
describes — room back in Lobby, readiness reset — is verbatim `room-websocket.md`'s existing
`GAME_ENDED` contract; that section and flow 07 both gain FR-JOB-007c as `GAME_ENDED`'s second trigger,
same payload shape, rather than a new event type. This item's read-list gains
`flows/07-room-closure.md` § Caller 5 (below) so the next reader of duty (c) has the full mechanism in
one place rather than reconstructing it from `room-lifecycle.md` alone. This item's *Done when* clause
already said "fails back to Lobby, not closed, with no history entry," so it is unchanged by the fix
except to name the event to publish, which was genuinely undetermined before this gate closed.

**Closed:** IMP-GATE-54 (opened and closed 2026-09-13, session 46) — this item's *Done when* required
"the three reconciliation duties," but `platform-operations.md` FR-JOB-007 has always defined **five**
lettered duties (a–e: owed-teardown re-drive, orphaned-artifact deletion, In-Progress-no-session
fail-back, idle-Lobby closure, unowned-room adoption), matching `room-lifecycle.md` §5.2's five-row
table exactly — no reading of either document yields three. Separately, this item's *Satisfies*
claimed the full `FR-JOB-001…013` range verbatim, identical to `IMP-M5-04`'s claim of the same full
range, even though `FR-JOB-001` (guest cleanup) is already built and unclaimed by `IMP-M1-05`,
`FR-JOB-006` (deadline sweep) is already built and unclaimed by `IMP-M2-07`, and `FR-JOB-012` (upload
slot sweep) belongs to `IMP-M4-03`'s manifest/upload domain, which this item's read-list never touches
— same shape as `IMP-GATE-08`/`18`/`28`/`30`/`46`. Fixed: the *Done when* clause below enumerates all
five duties; *Satisfies* narrows to `FR-JOB-007…011` (reconciliation, its safety guards, the room
purge `room-lifecycle.md` §5.3 also assigns here, repair idempotency, and reconciliation
observability — a contiguous, verifiable range) plus `NFR-JOB-002` (the adoption recoverability
bound; `NFR-JOB-001` is FR-JOB-006's bound, `IMP-M2-07`'s already-shipped concern); read-list corrected
to name the real duty count and add §6 for FR-JOB-011's metric names. `IMP-M5-04`'s matching over-claim
is narrowed in its own section below. `FR-JOB-001`/`006` staying unclaimed by their actual builders
(`IMP-M1-05`/`IMP-M2-07`, both `DONE`) is a pre-existing gap, not reopened here — noted in `STATUS.md`
instead of touching finished items' sections.

**Read first:**
- `docs/specs/platform/room-lifecycle.md` §5 **in full** — §5.1 (already built by `IMP-M2-07`; read
  for context, not to rebuild) plus this item's own §5.2 (the five reconciliation duties), §5.3
  (closed-room purge) and §5.4 (safety preconditions) — and §6 (metric names for FR-JOB-011)
- `docs/requirements/platform-operations.md` FR-JOB-007…011, NFR-JOB-002
- `docs/decisions/0008-room-ownership-lifecycle.md`
- `docs/specs/deployment/local-environment.md` §7.2
- `docs/specs/flows/05-owner-loss-and-adoption.md`
- `docs/specs/flows/07-room-closure.md` § Caller 5 — duty (c)/(d)'s shared `detachSession` mechanism,
  and why duty (c) has no closure branch (`IMP-GATE-55`)
- `docs/specs/game-host/game-host-internals.md` §13 — duty (b)'s six session-key-family names
  (`session:`/`routing:`/`queue:`/`seq:`/`delivered:`/`failcount:{sessionId}`) and their shared
  24h-refreshed-on-write TTL, the only place either is stated; not previously in this item's read-list
  despite `room-lifecycle.md`'s own Scope section naming this document as out of scope for *game
  execution*, which the key inventory is not.

**Satisfies:** `platform-operations.md` FR-JOB-007…011, NFR-JOB-002

**Done when:** all **five** FR-JOB-007 reconciliation duties run, `FOR UPDATE SKIP LOCKED`, each
idempotent (FR-JOB-010 — a repair whose guard no longer holds is a no-op) and each exposing
FR-JOB-011's per-duty candidate/repair/skip counts: (a) owed teardowns are re-driven via
`terminateAndCleanup`; (b) orphaned Redis session-key families older than 10 minutes are deleted; (c)
an In-Progress room with no session **fails back to Lobby, not closed**, with no history entry,
broadcasting `GAME_ENDED` (`readinessReset: true`) as its FR-JOB-007c trigger (`IMP-GATE-55`); (d)
an idle Lobby room (zero connected participants, past the idle window) closes `IDLE_TIMEOUT`; (e) an
unowned room is claimed and adopted. The adopt duty (e) alone is exempt from both FR-JOB-008 guards
(120 s startup suppression, two-consecutive-runs), which would otherwise block adoption for 120 s
after every restart. The closed-room purge (FR-JOB-009, §5.3) deletes rooms Closed past the retention
window, cascading to participant, team and invite rows — **orphaned participant rows are handled by
this cascade, not by a duty of their own**, distinct from duty (b)'s orphaned Redis *artifacts*, which
is a real duty.

**Duty 2 is the deferred tail.** It announces departures whose `lost_announced_at` is NULL and then
evaluates closure, and it is the mechanism three other items rely on (M1-08, M2-07, M2-09). Its
`leave_reason` filter is a backstop, not the primary control — the primary control is that every
inline path stamps `lost_announced_at` itself (IR-09).

The per-duty reconciliation counters these jobs increment fire the `ReconciliationRepairsPersist`
alert (`observability.md` §6 sketches the rule; `platform-operations.md` FR-ALERT-006 defines it,
deferred here by `IMP-M0-10`) — repairs applied on more than 3 consecutive runs, or a room
detected-but-unrepaired for more than 10 minutes.

---

### IMP-M2-11 — In-room chat

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-05

**Done 2026-09-10 (session 42).** New `chat` feature package (ADR-0014's own listing, kept separate
from `room` despite sharing its `room.*` wire prefix). `ChatController`'s `SEND_CHAT_MESSAGE` on
`/app/room.{roomId}.chat` resolves the sender's role/team through a new public `room.RoomChatPort` —
a deliberate cross-feature API (ADR-0014 §3) rather than reaching into `room`'s package-private
`RoomRepository`/`RoomEventExecutor`. `resolveSenderForSend` runs under a new `RoomEventExecutor
.withLock` (lock + fresh ownership check, no transaction, no version bump, no publish — `execute`'s
CAS/publish machinery is specific to the bare room topic), giving the "team assignment re-validated
under the room lock" requirement real mutual exclusion against a racing `REASSIGN_PLAYER` and a
monotonic `serverTimestamp`. `ChatSubscriptionAuthorizer` governs the `.chat`/`.team.{teamId}`
sub-topics `room.RoomSubscriptionAuthorizer` always excluded, using the lighter unlocked
`currentMembership` read (mirroring `room`'s own bare-topic check) since the doc's Authorization table
names only silent-drop, never `ROOM_UNAVAILABLE_RETRY`, for chat subscriptions. Text is canonicalized
via the existing `common.Canonicalizer` (NFC, forbidden-code-point rejection doubling as chat's "no
control characters at all") before the 1–500-code-point check.

**Closed:** IMP-GATE-47 (opened and closed 2026-09-10, session 42) — `input-validation.md`'s Size
limits table assigns the whole per-destination STOMP frame-size ceiling (8 KB
`/app/room.*.member`/`.host`, 4 KB `/app/room.*.chat`, 256 KB `/app/game.*.action`, 1 KB
`/app/game.*.sync`) to "the same `ChannelInterceptor` as the Tier 6 rate limits," but no work item's
read-list or Done-when ever required building it — `IMP-M2-02` built that exact interceptor
(`WebSocketChannelInterceptor`, `DONE`) without `input-validation.md` in its read-list, so it shipped
Tier 6 bucket classification alone; `IMP-M2-05`/`M2-06` (also `DONE`) never named the document either.
A registry omission, not a wording conflict between two specs. Fixed: this item builds the guard —
see the size-limit Done-when clause below and the deferral note added to `IMP-M2-02`'s section above.
The guard is generic (destination → byte ceiling, mirroring Tier 6's own `classify()`), so it covers
`IMP-M2-05`/`M2-06`'s already-shipped member/host destinations with no code change to either, and
pre-registers the two game rows for `IMP-M3-01`/`M3-06` to inherit rather than re-decide.

**Read first:**
- `docs/requirements/in-room-chat.md` in full
- `docs/specs/api-design/room-chat-websocket.md` in full
- `docs/specs/api-design/input-validation.md` § *Output encoding*, § *Size limits*
- `docs/specs/api-design/rate-limiting.md` Tier 6

**Satisfies:** `in-room-chat.md` FR-MSG-001…006, FR-CHAN-001…004, FR-TEAM-001…004,
FR-SWITCH-001…002, NFR-SEC-001…003, NFR-PERF-001; `game-rooms.md` FR-TEAM-011

**Done when:** chat frames carry `version: null` and **never advance the room version counter**
(IR-08); the channel a message lands on is derived from the sender's current team **server-side**,
never read from the frame; a message missed while disconnected is **lost, not gapped** (FR-MSG-006) —
there is no chat history, no catch-up and no second sequence number; bodies are escaped at render and
no HTML string is ever constructed; a spectator's send is rejected `SPECTATOR_CANNOT_CHAT`, an empty
or oversized `text` is rejected `MESSAGE_EMPTY`/`MESSAGE_TOO_LONG` at the 500-code-point limit
measured after NFC, a `TEAM` send with no team assignment is `NO_TEAM_ASSIGNMENT`, and one against a
game with no team support is `TEAM_CHAT_NOT_AVAILABLE` (FR-MSG-002, NFR-SEC-001…003); `authorId`/
`authorUsername` are resolved server-side from the authenticated principal, never from the frame
(NFR-SEC-002); `WebSocketChannelInterceptor` gains a generic per-destination frame-size guard —
`/app/room.*.chat` at 4 KB, `/app/room.*.member`/`.host` at 8 KB, `/app/game.*.action` at 256 KB,
`/app/game.*.sync` at 1 KB — checked from the raw frame's byte length before Tier 6 consumption
(`input-validation.md`'s pipeline: Size precedes Authorize), rejecting with `MESSAGE_TOO_LARGE`
(`ACTION_TOO_LARGE` for the action row, per the table) on `/user/queue/errors`, interceptor-dropped so
it carries no `correlationId`.

**Verified end to end on real STOMP clients** (`ChatControllerIT`): room-channel broadcast reaches
every player, excludes a subscribed spectator entirely (silent drop, no error), and leaves
`room.version` unchanged across the send; every documented validation/business error code fires from
the right sender; a team message reaches only players sharing that team and nothing arrives on the
off-team topic; a game with no team templates rejects `TEAM_CHAT_NOT_AVAILABLE`; a 6 KB frame is
rejected `MESSAGE_TOO_LARGE` with no `correlationId` key, at the interceptor, before the 500-code-point
business check ever runs. `./mvnw verify -Pintegration` green locally (116 tests plus this item's 4,
coverage checks met). **CI green on `turnbase-platform` `master`.**

**Giving chat a version number is the tempting mistake.** Two writers on one counter means a client
that filters chat sees a permanent gap in the room stream and resyncs forever.

---

### IMP-M2-12 — Room invitations

**Repo:** `turnbase-platform` · **Depends on:** IMP-M2-01, IMP-M1-09

**Closed:** IMP-GATE-57 (opened and closed 2026-09-13, session 50) — superseded by `IMP-GATE-58`
below, whose own fix removes the clause this one corrected: the invite-*link* Done-when clause turned
out not to belong to this item at all. Kept for the record — the correction it made
(`room-rest-api.md` §3.1's no-way-in case returns a room resource, not "not found") is still true, it
now just lives entirely in `IMP-M2-01`'s own section instead.

**Closed:** IMP-GATE-58 (opened and closed 2026-09-13, session 50) — three findings from reading this
item's own read-list before writing code, all the same root cause: the item was scoped before
`IMP-M2-01`/`IMP-M2-05` existed and was never revisited once they shipped.

1. **Double-claim, `game-rooms.md`.** `FR-HOST-002`, `FR-JOIN-003…004`, `NFR-SEC-002` are `IMP-M2-01`'s
   (its own *Satisfies*, `IMP-GATE-39`) — the invite **link** (mint, host-only exposure, `GET
   /api/rooms?inviteCode=…` resolution) is fully built and shipped there, verified by reading
   `RoomController`/`RoomService`/`RoomRepository` directly rather than assuming. `FR-JOIN-006` and
   `FR-JOIN-008` are `IMP-M2-05`'s (its own *Satisfies*), also shipped. Same shape as
   `IMP-GATE-08`/`18`/`28`/`30`/`32`/`34`. This item built none of the five and should never have
   claimed them.
2. **Double-claim, `FR-LINK-001…002`.** Claimed by *both* this item and `IMP-M5-03`, and neither
   builds anything for it — it describes exactly the invite-link mechanism `IMP-M2-01` already ships
   (`data-model-notifications.md` §2: "**this is not the invite link** ... the shareable join link is
   `room.invite_code`... unrelated objects"). Reassigned to `IMP-M2-01`, whose section gains it.
3. **No document defined this item's actual REST surface** — same shape as `IMP-GATE-31`/`33`/`35`/`37`.
   `room-rest-api.md` §8 explicitly defers FR-HOST-001's notification invites elsewhere ("belong to
   `notifications-invitations.md`, not here"), but that document is requirements prose with no
   endpoints, and nothing else supplied them. Also undefined: whether "accept" is its own endpoint or
   resolves through the existing join call, and what happens to a pending invitation when that join
   *fails* (FR-INV-005) — `data-model-notifications.md` §2 says accepting deletes the row but not at
   what moment. Fixed: new
   [`docs/specs/api-design/room-invitation-rest-api.md`](../../specs/api-design/room-invitation-rest-api.md)
   — `POST /api/rooms/{roomId}/invitations` (send) and `DELETE …/invitations/me` (decline); acceptance
   is `room-rest-api.md` §5's existing join endpoint, which gains one clause (step 7): a *successful*
   join deletes the caller's pending invitation to that room and alerts its inviter; a *failed* join
   leaves it untouched, so a rejected join doesn't cost the player their invitation. `rest-conventions.md`'s
   Authorization table gains both predicates; `room-rest-api.md` §8's cross-reference and Related table
   updated to point at the new document instead of the requirements doc.

This item's *Satisfies* narrows to what it actually builds: `notifications-invitations.md`
FR-INV-001…009 and `game-rooms.md` FR-HOST-001. `IMP-M2-01`'s *Satisfies* gains `FR-LINK-001…002`;
`IMP-M5-03`'s drops them.

**Read first:**
- `docs/requirements/notifications-invitations.md` FR-INV-001…009 (FR-LINK-001…002 is `IMP-M2-01`'s
  now — read there if the invite-link mechanism itself is in question, not here)
- `docs/specs/platform/data-model-notifications.md` §1 (`notification`), §2 (`room_invitation`)
- `docs/specs/api-design/room-invitation-rest-api.md` **in full** — the two endpoints this item builds
  and the join-endpoint clause it adds to `IMP-M2-01`'s shipped code
- `docs/specs/api-design/sse-notifications.md` § *Notification types*, § *Alert types* — the
  `ROOM_INVITATION` notification and `INVITATION_ACCEPTED`/`INVITATION_DECLINED` alert payload shapes
  this item writes/publishes
- `docs/requirements/game-rooms.md` FR-HOST-001

**Satisfies:** `notifications-invitations.md` FR-INV-001…009; `game-rooms.md` FR-HOST-001

**Done when:** `POST /api/rooms/{roomId}/invitations` is host-only, friends-only (FR-INV-002, a direct
`friendship` check matching `RoomRepository#isVisible`'s existing precedent), and writes a
`ROOM_INVITATION` notification
(`room-invitation-rest-api.md` §2); `DELETE …/invitations/me` deletes the caller's own pending row
idempotently and alerts the inviter only when a row actually existed (§3); a successful join at
`IMP-M2-01`'s join endpoint deletes the caller's pending invitation to that room and alerts its
inviter, while a failed join leaves it pending (§4); invitations are removed **at closure** by
`IMP-M2-09`'s `detachSession`, not by this item and not by the purge cascade (FR-INV-008); no alert
delivery mechanism exists yet (`IMP-M5-03` is not a dependency and is not `DONE`) — this item defines
an `AlertPublisher`-shaped seam with a no-op implementation for now, matching the
`SessionTerminator`/`PendingSessionTerminator` precedent (`IMP-M2-09`), swapped for a real one when
`IMP-M5-03` lands.

---
