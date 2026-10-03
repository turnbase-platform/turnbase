# Room REST API

The HTTP surface for room **membership**: creating a room, finding one, joining it, and leaving it.
Everything that happens *inside* a room — readiness, teams, parameters, kick, host transfer, start —
is STOMP and lives in [room-websocket.md](room-websocket.md).

Realizes `../../requirements/game-rooms.md` FR-CREATE-001…004, FR-JOIN-001…007, FR-JOIN-009…011,
FR-LIST-001…007, FR-LIFE-004, FR-XFER-003 and FR-HOST-002. Closes review blocker **IR-13**.

## Related

| Document | What it supplies |
|---|---|
| [rest-conventions.md](rest-conventions.md) | Status codes, the `/api/rooms/{id}` authorization predicate, the `Origin` check, self-scoped routing |
| [pagination-filtering-sorting.md](pagination-filtering-sorting.md) | The list envelope, `page`/`size`/`sort` parameters |
| [error-handling.md](error-handling.md) | RFC 9457 Problem Details and the type taxonomy |
| [room-websocket.md](room-websocket.md) | Everything a client does after it has joined |
| [../platform/room-lifecycle.md](../platform/room-lifecycle.md) | The ownership claim these endpoints run (§1.2) and the affinity hint they return (§1.7) |
| [../platform/data-model.md](../platform/data-model.md) | `room`, `room_participant`, `room_team` — the column names used below |
| [../platform/data-model-catalog.md](../platform/data-model-catalog.md) | `game`, `game_version` — the room-creation preconditions of §2, and the capability/count columns behind §3's predicate |
| [../../requirements/game-rooms.md](../../requirements/game-rooms.md) | The requirements this realizes |
| [room-invitation-rest-api.md](room-invitation-rest-api.md) | Adds one clause (§5 step 7) to this document's join endpoint — invitation resolution on acceptance |

---

## Scope: what is REST and what is STOMP

**REST covers membership; STOMP covers everything else.** The rule is worth stating as a rule,
because the boundary is not where a reader coming from the requirements document would guess:
FR-HOST-006 (kick), FR-HOST-007 (parameters), FR-READY-001…004 (readiness) and FR-TEAM-002…006
(teams) all read like resource mutations and none of them is an endpoint here.

The reason is that every one of those is a mutation of shared room state that must be **broadcast to
every participant with a version stamp**, under the room lock, by the owning instance. That is
exactly what the STOMP command handlers do (`room-websocket.md`), and duplicating any of them as a
REST route would mean two code paths taking the same lock and bumping the same counter — two
producers for one sequence, which is the invariant `room-lifecycle.md` §1.5 exists to protect.

`rest-conventions.md` already assumes this line where it writes the room predicate as
"`principal` is a participant; **host commands** additionally `room.host_user_id = principal`,
re-checked under the room lock". A host command is a STOMP frame. The REST surface has no host
commands at all.

What is left for REST is the set of operations a client performs when it is **not yet** in the room,
or is leaving it: it has no subscription to receive a broadcast on, and no room to be a participant
of. Those are: create, list, get, join, leave, and resolving an invite code.

---

## 1. Endpoints

| Method | Path | Auth | Success | Requirements |
|---|---|---|---|---|
| `POST` | `/api/rooms` | Session | `201` + `Location` | FR-CREATE-001, FR-CREATE-002, FR-CREATE-003, FR-CREATE-004 |
| `GET` | `/api/rooms` | Session | `200` | FR-LIST-001…FR-LIST-007, FR-JOIN-003 |
| `GET` | `/api/rooms/{roomId}` | Session | `200` | FR-JOIN-004, FR-XFER-003 |
| `POST` | `/api/rooms/{roomId}/participants` | Session | `201` | FR-JOIN-001, FR-JOIN-002, FR-JOIN-005, FR-JOIN-006, FR-JOIN-007 |
| `DELETE` | `/api/rooms/{roomId}/participants/me` | Session | `204` | FR-LIFE-004, FR-JOIN-009, FR-JOIN-010 |

Five endpoints. There is no `PUT`, no `PATCH` and no `DELETE /api/rooms/{roomId}` — see §8.

All five are state-changing or principal-scoped and therefore sit behind the session cookie and, for
the three non-`GET`s, behind the `Origin` check of `rest-conventions.md`. None is public.

### The affinity hint is a response header

Every response that leaves the caller expecting to open a socket — `201` from create, `201` from
join, `200` from get — carries:

```
X-TurnBase-Room-Instance: platform-7d9f8c-abc12
```

**A header rather than a body field, deliberately.** It is transport routing, not room state: it
names the instance that currently owns the room (`room-lifecycle.md` §1.7), it is **advisory**
(`platform-operations.md` FR-DEPLOY-002), and it is stale the moment ownership moves. Putting it in
the resource body invites a client to store it alongside the room and re-use it on the next
interaction, which is the one thing it must not be used for. A header is read by the transport layer
that immediately consumes it and is then gone.

The client passes it to the ingress on the WebSocket handshake. If the named instance is absent from
the ready endpoint set the ingress load-balances normally and the receiving instance resolves
ownership itself — the hint being wrong is an ordinary outcome, not an error.

---

## 2. `POST /api/rooms` — create

```http
POST /api/rooms
Content-Type: application/json

{
  "gameId": "3f2b…",
  "visibility": "PUBLIC",
  "spectatingEnabled": true
}
```

| Field | Rules |
|---|---|
| `gameId` | Required. Must name a game with an `ACTIVE` version the caller may see (`game-catalog.md` NFR-SEC-002 — an unlisted game is `404`, never `403`) — precisely, all three of `data-model-catalog.md` §1's room-creation preconditions: `game.deleted_at IS NULL AND game.archived_at IS NULL` (FR-GAME-013), `game.listed OR :creator = game.owner_user_id` (FR-GAME-007), and `game.badge <> 'UNVERIFIED' OR :creator = game.owner_user_id` (FR-PRV-002). Any failing predicate is `404`, matching the caller-visibility test above — the three are one "can this caller see this game" question, not three different failures |
| `visibility` | Required. `PUBLIC` \| `FRIENDS_ONLY` \| `INVITE_ONLY` (FR-CREATE-002) |
| `spectatingEnabled` | Optional, default `false`. Rejected with `422` if the game's manifest does not declare spectator support — FR-CREATE-001 makes the choice conditional on the game supporting it, so accepting it silently would let a host promise something the game cannot do |

There is no `gameVersion` field. The room pins the game's current `ACTIVE` version at creation and
records it in `room.game_version`; a client that could name a version could pin a room to a withdrawn
one.

### What happens inside the transaction

In this order, all in one transaction, before the response is written:

1. Insert `room` with `state = 'LOBBY'`, `version = 0`, and a fresh `invite_code`.
2. **Instantiate teams** — `count.min` instances for each declared template, each at
   `configured_size = size.max` (FR-TEAM-012).
3. **Auto-join the creator as host** (FR-CREATE-003): a `room_participant` row with
   `role = 'PLAYER'`, `join_order = 1`, and `room.host_user_id` set to them.
4. Auto-assign them to a team (FR-TEAM-005). All teams are empty, so this is deterministically the
   first team of the first declared template.
5. Release any room the creator already occupies (FR-JOIN-007 — §5 states the rule; creation is
   subject to it identically).
6. Claim the room (`room-lifecycle.md` §1.2). A newly inserted room is always free, so this is the
   adopt branch and cannot redirect.

**Steps 2 and 3 are ordered and the order is load-bearing.** FR-TEAM-012 says teams are instantiated
*before* the host is assigned. Reversed, there is no team to assign the host to and FR-TEAM-005 has
no defined answer.

`invite_code` is minted at creation for every room regardless of visibility, because FR-HOST-002
says all visibility types support the link. It is cryptographically random and not enumerable
(NFR-SEC-002).

### Response

```http
201 Created
Location: /api/rooms/9c1e…
X-TurnBase-Room-Instance: platform-7d9f8c-abc12
```

The body is the **full room resource** of §4, not a stub and not an id.

**The response must be sufficient to open the socket with no second call.** A `201` carrying only a
`Location` would force the client into `POST` → `GET` → `SUBSCRIBE`, and the middle call is a
round-trip whose only purpose is to fetch state the server had in hand a millisecond earlier. Worse,
the room's `version` can advance between the two, so the client would open its socket against a
snapshot it must immediately discard.

---

## 3. `GET /api/rooms` — list

Realizes FR-LIST-001 through FR-LIST-007. Pagination, `sort` and the response envelope are
[pagination-filtering-sorting.md](pagination-filtering-sorting.md)'s; only what is specific to rooms
is here.

### The inclusion predicate

FR-LIST-001 is prose in the requirements and a predicate here, because an implementer needs the
second form:

```
included(room, viewer) :=
      room.state <> 'CLOSED'
  AND visible(room, viewer)
  AND ( canJoin(room, viewer) OR canSpectate(room, viewer) )
```

```
visible(room, viewer) :=
      room.visibility = 'PUBLIC'
   OR (room.visibility = 'FRIENDS_ONLY' AND friends(viewer, room.host_user_id))    -- FR-LIST-006
   -- INVITE_ONLY is never visible in a listing                                     -- FR-LIST-007
```

```
canJoin(room, viewer) :=
      a non-blocked player slot is free
  AND ( room.state = 'LOBBY' OR gameVersion.supports_mid_game_join )

canSpectate(room, viewer) :=
      room.spectating_enabled
  AND gameVersion.supports_spectators
  AND spectatorCount < spectatorCapacity                                            -- NFR-SPEC-001
```

`gameVersion` is the `game_version` row named by `room.game_id`/`room.game_version`
(`data-model-catalog.md` §2 — not the *active* version, since a room pins the version it was created
against). `supports_mid_game_join` and `supports_spectators` are that document's projections of the
manifest's `capabilities.midGameJoin`/`capabilities.spectators`, computed once at validation; a room's
capabilities never change after creation because `game_version` rows are immutable once activated.

`spectatorCapacity` is the platform property `turnbase.room.spectator-capacity` (default `8`,
[`../deployment/local-environment.md`](../deployment/local-environment.md) §7.1), not a per-room or
per-game value. NFR-SPEC-001 gives hosts no control over it; the game manifest declares whether
spectating is supported, not how many spectators fit.

A room the viewer can neither join nor spectate is **excluded from the list**, not returned with both
buttons disabled. FR-LIST-001 says so, and the reason it says so is that a list of rooms you cannot
enter is not a room list.

`FRIENDS_ONLY` resolution needs a friendship lookup per row, which is why the predicate is a join
against the friendship table rather than a post-filter — filtering after pagination returns short
pages and a wrong `totalElements`.

### Filters and sorts

FR-LIST-003. All applied server-side; `pagination-filtering-sorting.md` forbids the client-side form.

| Param | Type | Maps to |
|---|---|---|
| `search` | string | Case-insensitive substring against **game name and host username simultaneously** — one parameter, `OR`ed across two columns |
| `status` | `LOBBY` \| `IN_PROGRESS`, multi-value | `room.state` |
| `minPlayers`, `maxPlayers` | integer | The stored template-derived bounds of FR-LIST-002 |
| `playerCountMin`, `playerCountMax` | integer | Current occupancy, which is a different number from the two above and is why the parameters are not named alike |
| `inviteCode` | string | §3.1 |

`sort` accepts `gameName`, `minPlayers`, `maxPlayers`, `playerCount`, `status`. Default
`createdAt,desc` — newest first, which is the only ordering a player scanning for a room to join
actually wants and which FR-LIST-003 does not specify.

`search` matching two columns from one parameter is FR-LIST-003's wording ("filters by game name and
host name simultaneously") and not a convenience: two parameters would let a client ask for a game
name that matches *and* a host name that matches, which is a query nobody wants and an index nobody
has.

### Row shape

Each element carries the FR-LIST-002 fields plus the two pre-computed action flags FR-LIST-003a
requires:

```json
{
  "roomId": "9c1e…",
  "gameId": "3f2b…",
  "gameName": "Hex Duel",
  "hostUsername": "alice",
  "state": "LOBBY",
  "playerCount": 3,
  "playerCapacity": 8,
  "minPlayers": 2,
  "maxPlayers": 8,
  "spectatingSupported": true,
  "spectatorCount": 1,
  "canJoin": true,
  "canSpectate": true
}
```

**`canJoin` and `canSpectate` are computed server-side and sent, not inferred client-side from the
counts.** FR-LIST-003a requires it, and the reason is that the client cannot compute them: blocked
slots (grace-period reservations, AI occupancy) are not derivable from `playerCount` versus
`playerCapacity`, and mid-game-join support is a manifest capability the list does not otherwise
carry.

`playerCount` is human + AI combined per FR-LIST-002. In v1 the AI term is always zero
(`room-websocket.md`), so the two are equal — the field is defined as the sum anyway so the meaning
does not change when AI arrives.

**These flags are advisory and the client must expect them to be wrong.** FR-LIST-003a says so
explicitly: a room can fill between the list load and the join, the join then fails, and the client
refreshes. This is a list, not a reservation — FR-LIST-005 refreshes only on an explicit control and
there is no polling (CON-001 puts real-time on WebSockets, and the room list is not a real-time
surface).

### The `reservedSlot` field — VW-ROOMS-005, FR-REJOIN-002

The envelope carries one field beyond `pagination-filtering-sorting.md`'s standard shape, a sibling
of `content` and `pagination` rather than a per-row value:

```json
{
  "content": [ … ],
  "pagination": { … },
  "reservedSlot": {
    "roomId": "9c1e…",
    "gameName": "Hex Duel",
    "graceRemainingSeconds": 42
  }
}
```

`reservedSlot` is `null` when the caller holds no live grace-period reservation (`FR-GRACE-005`) in
any room, and otherwise names the room and the seconds remaining before the reservation is released.
It exists because `shell-architecture.md` §8's reconnection pinned card on `/rooms` is global —
driven by this field, not a per-row flag — and needs to appear for a room that is not itself included
in the current page: the caller's own reserved room can be filtered out by `search`/`status`, full,
or on a different page, while the reservation itself is still live.

It is computed from the caller's own `room_participant` rows independently of the `included()`
predicate above and of the request's filter/sort/page parameters — the same reservation is reported
regardless of what the rest of the response contains. Removal is not push-driven (FR-LIST-005 has no
polling and CON-001 keeps real-time on WebSockets, neither of which apply to a room the client is no
longer attached to): the field simply reflects current state as of each explicit list refresh, and
goes `null` once the reservation is consumed by rejoining, expires, or the room closes.

### 3.1 Resolving an invite code — FR-JOIN-003, FR-JOIN-004

```
GET /api/rooms?inviteCode=k7Qm2xR9
```

Returns the standard list envelope containing **exactly zero or one element**, and the element is a
full room resource (§4) rather than a list row, so the client can act on it directly.

**Never a `404`, and never its own endpoint.** A `404` on `GET /api/invites/{code}` distinguishes
"this code does not exist" from "this code exists but you cannot use it", which is precisely the
oracle NFR-SEC-002 makes the codes unguessable to prevent — an attacker with a candidate list learns
which candidates are real. An empty list is the same response for a wrong code, an expired code, and
a closed room (FR-XFER-003), which is the answer that leaks nothing.

The filter also composes: `inviteCode` bypasses the `visible()` predicate — that is the entire point
of an invite link, per FR-JOIN-003 — but **not** the `state <> 'CLOSED'` term.

FR-JOIN-004's three invalid cases are therefore: an empty list (room gone or closed), or one element
with `canJoin: false` and `canSpectate: false` (no way in). The fourth case, one element with
`canJoin: false, canSpectate: true`, is FR-JOIN-004's "presented that option" and needs no special
response shape — the flags already say it.

---

## 4. `GET /api/rooms/{roomId}`

The full room resource. Superset of a list row.

```json
{
  "roomId": "9c1e…",
  "gameId": "3f2b…",
  "gameName": "Hex Duel",
  "gameVersion": "1.4.0",
  "state": "LOBBY",
  "visibility": "PUBLIC",
  "hostUserId": "a1b2…",
  "hostUsername": "alice",
  "spectatingEnabled": true,
  "spectatorCapacity": 8,
  "spectatorCount": 1,
  "playerCount": 3,
  "playerCapacity": 8,
  "minPlayers": 2,
  "maxPlayers": 8,
  "inviteCode": "k7Qm2xR9",
  "canJoin": true,
  "canSpectate": true,
  "viewerRole": null,
  "version": 42,
  "createdAt": "2026-08-16T10:04:11Z"
}
```

`inviteCode` is present **only when the caller is the host** (FR-HOST-002 gives the host the link to
share; nobody else needs to re-derive it). `version` is the room's current event version, so a client
that opens its socket immediately after this call knows whether the first delta it receives is
contiguous. `spectatorCapacity` is the resolved value of `turnbase.room.spectator-capacity` (§3), sent
so a client can render "3 / 8 watching" without knowing the platform's configuration.

`viewerRole` is `PLAYER`, `SPECTATOR` or `null`: the caller's own current membership (a participant row
with `left_at IS NULL`; a grace-period reservation counts as `PLAYER`). It exists because opening
`/rooms/{id}` must not enrol anyone (`platform-views.md` *Room — Lobby*, `IMP-GATE-95`): the client
needs to tell a member re-entering, which is the idempotent join of §5 step 2, from a visitor who must
first choose Player or Spectator. `canJoin`/`canSpectate` cannot answer that — they are computed for
the viewer as a stranger and stay `true` for a member of a room with a free seat. Present on the full
resource only, never on a list row.

**No participant list, no team list.** Both are in `ROOM_STATE` on the socket
(`room-websocket.md`), which is delivered under the room lock with a version stamp. Returning them
here would produce an unversioned copy of versioned state, and a client that rendered from it would
be showing a roster it can never reconcile against the deltas that follow.

**A closed room is `404`, not `410`.** FR-XFER-003 makes a closed room inaccessible and unfindable;
`410 Gone` announces that it existed. `rest-conventions.md` reserves `410` for the expired upload
slot, where the caller created the resource and is owed the distinction. Here the caller may be
anybody holding a stale link.

A room the caller cannot see under the `visible()` predicate of §3 is likewise `404` — with the
single exception that possession of the room id is *not* possession of the invite code, so this is
not a way in. `403` would confirm the room exists to someone who was not told it does.

---

## 5. `POST /api/rooms/{roomId}/participants` — join

```http
POST /api/rooms/9c1e…/participants
Content-Type: application/json

{ "role": "PLAYER" }
```

`role` is `PLAYER` (FR-JOIN-001, FR-JOIN-002, FR-JOIN-006) or `SPECTATOR` (FR-JOIN-005). Required —
there is no default, because guessing wrong seats a player as a spectator or consumes the last
player slot for someone who wanted to watch, and neither is recoverable without a second call.

**One endpoint with a role, not two endpoints.** FR-JOIN-006 requires join-as-player and
join-as-spectator to be presented as two distinct actions on the *same* room, and FR-LIST-003a
pre-computes their availability as two flags on one row. Two endpoints would model them as two
resources, and the natural response to "the room filled while you were deciding" — *you cannot join
but you can still spectate* — would have to be expressed as an error on one endpoint pointing at the
other.

`?inviteCode=` may be appended. It relaxes the visibility check (FR-JOIN-003) and nothing else; every
capacity, state and blocked-slot rule below applies unchanged.

### Evaluation order

**Claim first, then the locked transaction** (`IMP-GATE-44`). The room's ownership claim
(`room-lifecycle.md` §1.2) and the `ReentrantLock` it establishes wrap everything below, matching
`room-lifecycle.md` §2.1's normative "lock outer → transaction inner → publish after commit" nesting
and `room-websocket.md`'s "every room mutation... whether REST-originated (join, leave, create) or
STOMP-originated... acquires the room's ReentrantLock." §2.1 says a stalled database "blocks every
operation on that room, **including REST joins**" — which only holds if a REST join shares the STOMP
commands' lock, so it must be acquired before, not after, the mutation. Claiming first rather than
last does not reintroduce the remote-call-inside-a-transaction problem `room-lifecycle.md` §4 forbids
(the claim is still outside the transaction, only earlier); the one cost is that a join which fails
validation *after* a successful claim leaves this instance owning a room it added no participant to,
which is harmless — some other human is already a member, or the claim was a no-op re-confirmation of
this instance's existing tenure.

0. **Claim** the room (`room-lifecycle.md` §1.2) and acquire its `ReentrantLock`. A claim that fails
   after retry is `503` with `Retry-After` and the affinity header is not set — nothing below runs.
1. **Visibility** — `visible(room, caller)` from §3, or a valid `inviteCode`. Failure: `404`.
2. **Not already a participant** — an existing row with `left_at IS NULL` is a no-op success, not an
   error (`201` with the current resource). A double-submitted join is a client retrying, not a
   conflict. Nothing below runs: no version bump, no broadcast, because nothing changed.
3. **State** — `CLOSED` is `404` (FR-XFER-003). `IN_PROGRESS` with `role: PLAYER` additionally
   requires `gameVersion.supports_mid_game_join` (§3's `gameVersion`, `data-model-catalog.md` §2;
   FR-JOIN-006).
4. **Capacity.** For `PLAYER`: a free, **non-blocked** slot must exist. A slot is blocked when it is
   occupied by an AI player or held by a live grace-period reservation (`game-rooms.md` Definitions);
   a reservation that has expired is not blocked, which is what makes FR-JOIN-006's
   "becomes unblocked mid-session" work with no extra mechanism. For `SPECTATOR`:
   `spectatorCount < spectatorCapacity`, where the capacity is `turnbase.room.spectator-capacity`
   (NFR-SPEC-001).
5. **Release the caller's current room** — FR-JOIN-007, below.
6. **Insert or reuse** the `room_participant` row with the next `join_order`, for `PLAYER`
   auto-assign a team (FR-TEAM-005 in Lobby, FR-TEAM-011 in progress). Reuse — `INSERT ... ON
   CONFLICT (room_id, user_id) DO UPDATE`, per `data-model.md` §2's row-state note (`IMP-GATE-50`) —
   applies when the caller previously departed this exact room, since `room_participant`'s row is
   never deleted and the primary key would otherwise collide; a plain `INSERT` is only ever reached
   for a caller with no row here at all. Either way, inside the same transaction, fenced by step 0's
   epoch, assign and commit the room's next `version` (`room-websocket.md` *Per-Room Serialization and
   Versioning*). Set the affinity header from step 0's claim.
7. **Resolve the caller's pending invitation to this room, if any** — delete it, and if one was
   deleted, publish an `INVITATION_ACCEPTED` alert to its inviter. No-op when the caller has none
   (joined via the link, the room list, or an invitation to a different room). Full detail —
   including why a *failed* join (steps 1–4) must leave the invitation untouched instead — is
   [`room-invitation-rest-api.md`](room-invitation-rest-api.md) §4, which owns FR-INV-004…006.

Steps 1–7 are one transaction, run while step 0's lock is still held. `PLAYER_JOINED` is broadcast on
`/topic/room.{roomId}` after the transaction commits and before the lock is released — commit before
publish, `room-lifecycle.md` §2.1. A no-op join (step 2) never reaches step 6 or 7 and never
broadcasts.

### FR-JOIN-007: the single-room constraint

**Enforced server-side, inside the join transaction, with no confirmation round-trip.** The caller's
existing membership — an occupied slot, or a grace-period reservation in an In Progress room — is
released as part of step 5: `left_at = now()`, `leave_reason = 'LEFT'` for an occupied slot or
`'EARLY_RELEASE'` for a voided reservation (FR-EXPIRY-004), and `lost_announced_at` left null when
this instance does not own the old room, so its owner announces the departure on its next sweep
(`room-lifecycle.md` §5.1 duty 2).

The released room is named in the response so the client can reconcile its own view:

```json
{
  "room": { … the §4 resource … },
  "releasedRoom": { "roomId": "4d8a…", "reason": "EARLY_RELEASE" }
}
```

`releasedRoom` is `null` when the caller was in no other room.

**The abandonment prompts are client-side only.** FR-JOIN-008, FR-JOIN-009 and FR-JOIN-010 describe
when the *client* must confirm before calling this endpoint — in an active game, or when ready in a
lobby, but not when unready in a lobby. The server never asks and never waits: it is told to join,
and joining releases the old room.

This is not the server ignoring a requirement. A server-side confirmation means a request that opens
a transaction, returns "are you sure?", and waits for a second call before committing — holding a
room lock across a human decision, on a path that runs while another player may be waiting for the
game to start. The client has all the state the prompt needs (it knows it is in a game; it knows it
is ready) and none of the locks.

The consequence to accept honestly: a client that skips the prompt still abandons the game. The
prompt is a courtesy to the user, not a control on the operation, and FR-JOIN-007's "takes
precedence over an outstanding slot reservation" is the requirements document saying the same thing.

---

## 6. `DELETE /api/rooms/{roomId}/participants/me` — leave

`204 No Content`. Idempotent: leaving a room the caller is not in is also `204`
(`rest-conventions.md` — the caller's desired state holds).

**`/me`, never a user id in the path.** `rest-conventions.md`'s self-scoped rule is explicit that no
user id is ever accepted in a path for a self-scoped operation, and leaving is self-scoped. Removing
*another* participant is FR-HOST-006's kick, which is a host command and therefore a STOMP frame — a
`DELETE /api/rooms/{id}/participants/{userId}` would be a second, unversioned path to the same
mutation, reachable by anyone who can guess a user id.

This endpoint is a **confirmed voluntary departure** in the sense of FR-LIFE-004: the slot is
released immediately with **no** grace period and no reservation, and during In Progress the game
engine is notified at once with reason `left`. A dropped WebSocket is not this — that is an
involuntary disconnect and opens a grace period (`reconnection-flow.md` FR-DC-005). The distinction
is the whole reason leaving is an explicit call rather than "close the socket".

FR-JOIN-009 and FR-JOIN-010's prompts apply here for the same reason and with the same division as
in §5: the client confirms, the server acts.

**When the leaver is the host**, this handler does not implement the consequences. It records the
departure and delegates to [room-lifecycle.md](../platform/room-lifecycle.md) §4, which applies
FR-XFER-001's transfer to the next human by join order, or FR-XFER-002's immediate closure when no
other human remains — including evicting spectators, who do not count toward viability. That code
runs under the room claim; this handler may be executing on an instance that does not hold it.

**Claimed, locked and versioned the same way as join, when the claim succeeds** (`IMP-GATE-44`). This
handler attempts the room's ownership claim (`room-lifecycle.md` §1.2) before the update below; on
success it acquires the `ReentrantLock` the same as §5's step 0, and the update runs inside one
transaction fenced by that claim's epoch, assigning the room's next `version`
(`room-websocket.md` *Per-Room Serialization and Versioning*) on an actual departure. `PLAYER_LEFT` is
broadcast on `/topic/room.{roomId}` after the commit, before the lock is released. A no-op departure
(the caller held no slot) updates zero rows and skips the version bump and broadcast, the same as
join's step 2. **Unlike join, a failed claim here does not fail the request**: the note above already
accepts this handler running without the claim, so a failed claim only skips the lock/version/
broadcast — the update still runs unfenced and still returns `204` (the caller's desired state holds),
and `lost_announced_at` stays `null`, deferring the announcement to the owning instance's next sweep
(`room-lifecycle.md` §5.1 duty 2), the same fallback `releaseCallersCurrentRoom` already relies on for
a caller's *other* room (§5, FR-JOIN-007).

---

## 7. Errors

`rest-conventions.md`'s status codes with `error-handling.md`'s Problem Details shape.

| Condition | Status | `type` slug | Requirement |
|---|---|---|---|
| Malformed body, unknown `visibility`, missing `role` | `400` | `validation-failed` | — |
| No session | `401` | `unauthenticated` | — |
| Room not visible to caller, closed, or does not exist | `404` | `not-found` | FR-XFER-003, FR-LIST-006/007 |
| Game does not exist or is unlisted to the caller | `404` | `not-found` | `game-catalog.md` NFR-SEC-002 |
| No player slot free, or all free slots blocked | `422` | `business-rule-violation` | FR-JOIN-001, FR-JOIN-006 |
| Spectator capacity reached | `422` | `business-rule-violation` | FR-JOIN-005, NFR-SPEC-001 |
| Spectating requested but not supported by the game or not enabled for the room | `422` | `business-rule-violation` | FR-JOIN-005 |
| `role: PLAYER` on an In Progress room with no mid-game join support | `422` | `business-rule-violation` | FR-JOIN-006 |
| `spectatingEnabled: true` for a game that does not support it | `422` | `business-rule-violation` | FR-CREATE-001 |
| Rate limit | `429` | `rate-limit-exceeded` | `rate-limiting.md` |
| Room owned by a live instance that could not be reached | `503` + `Retry-After` | `room-unavailable-retry` | `room-lifecycle.md` §1.7 |

**`422`, not `409`, for every capacity failure.** `rest-conventions.md` scopes `409` to unique
constraint violations. A full room is a business rule about state, not a collision, and the client's
response differs: a `409` invites a retry with different input, whereas a full room needs a refreshed
list.

### The `503` retry, and why it shares a name with the STOMP code

When the claim of `room-lifecycle.md` §1.2 returns result `0` — the room is owned by an instance
whose liveness lease is still live — the handler retries internally for a few hundred milliseconds
and then gives up:

```http
503 Service Unavailable
Retry-After: 2
Content-Type: application/problem+json

{
  "type": "https://turnbase.io/errors/room-unavailable-retry",
  "title": "Room Temporarily Unavailable",
  "status": 503,
  "detail": "The room's owning instance is not currently reachable. Retry shortly.",
  "instance": "/api/rooms/9c1e…/participants",
  "retryAfterMs": 2000
}
```

**The same condition arises on `SUBSCRIBE` and is reported there as the STOMP error code
`ROOM_UNAVAILABLE_RETRY`** (`room-websocket.md`). One concept, two carriers, one name. A client that
learns "back off and re-run the join flow" learns it once; giving the REST case a generic
`service-unavailable` would make the two look like unrelated failures and invite a client to treat
the HTTP one as terminal.

`retryAfterMs` duplicates `Retry-After` at millisecond resolution because the bound here is a few
hundred milliseconds to a couple of seconds and `Retry-After` is integer seconds. The header is for
proxies and generic clients; the extension field is for the platform frontend.

**This is a `503`, not a `409` or a `423`.** Nothing about the request is wrong and nothing about the
room's state conflicts — a transient routing condition means the server cannot serve it *yet*, which
is what `503` means, and `rest-conventions.md` already lists it for transient upstream failure.

---

## 8. What is deliberately absent

- **No `PUT` or `PATCH /api/rooms/{roomId}`.** The game is locked at creation (FR-CREATE-004: the
  host must leave and create a new room to switch games), and every other room field a host can
  change — parameters (FR-HOST-007), teams (FR-TEAM-002…004) — is a STOMP command. There is nothing
  left for an update route to update. FR-HOST-008's preservation of parameters across a rematch is a
  server-side lifecycle behaviour with no client call at all.
- **No `DELETE /api/rooms/{roomId}`.** A host does not delete a room; they leave it, and FR-XFER-002
  decides whether that closes it. Exposing closure as its own verb would give the host a way to evict
  players that bypasses FR-XFER-001's transfer.
- **No participant-list endpoint.** `ROOM_STATE` carries it, versioned (§4).
- **No readiness, team, kick, parameter or start routes.** Scope, above.
- **No invite-*resource*.** FR-HOST-002's link is `{platformOrigin}/join/{inviteCode}`, a frontend
  route that resolves through `GET /api/rooms?inviteCode=` (§3.1). FR-HOST-001's *notification*
  invites are a different mechanism, specified in
  [`room-invitation-rest-api.md`](room-invitation-rest-api.md) — accepting one resolves to an ordinary
  join at this endpoint (§5), which that document adds one clause to.
- **No rejoin endpoint.** Re-entering a room the caller still holds a slot in is `POST
  …/participants`, which returns `201` and the current resource for an existing participant (§5 step
  2). FR-JOIN-011's reconnection alert is a client-side affordance over that same call.

---

## 9. Requirements traceability

| Requirement | Realized by |
|---|---|
| FR-CREATE-001 | §2 request body — game, visibility, conditional spectating |
| FR-CREATE-002 | §2 `visibility` enum |
| FR-CREATE-003 | §2 transaction step 3 |
| FR-CREATE-004 | §8 — no update route; `gameId` is not writable after creation |
| FR-LIST-001 | §3 `included()` |
| FR-LIST-002 | §3 row shape |
| FR-LIST-003 | §3 filters and sorts |
| FR-LIST-003a | §3 `canJoin` / `canSpectate` |
| FR-LIST-004 | §3 via `pagination-filtering-sorting.md` |
| FR-LIST-005 | §3 — explicit refresh, no polling |
| FR-LIST-006 | §3 `visible()` friends term |
| FR-LIST-007 | §3 `visible()` — `INVITE_ONLY` never listed |
| FR-JOIN-001 | §5 |
| FR-JOIN-002 | §5 step 1 with the friends term |
| FR-JOIN-003 | §3.1, §5 `?inviteCode=` |
| FR-JOIN-004 | §3.1 — empty list, or flags on the single element |
| FR-JOIN-005 | §5 `role: SPECTATOR`, step 4 |
| FR-JOIN-006 | §5 steps 3–4, one endpoint with a role |
| FR-JOIN-007 | §5 — released inside the join transaction; `releasedRoom` in the response |
| FR-JOIN-008, FR-JOIN-009, FR-JOIN-010 | §5, §6 — client-side prompts over these calls |
| FR-JOIN-011 | §8 — no separate endpoint; the alert covers the ordinary join |
| FR-HOST-002 | §2 `invite_code` minted for every room; §3.1 resolution; §4 host-only exposure |
| FR-TEAM-005, FR-TEAM-011, FR-TEAM-012 | §2 steps 2–4; §5 step 6 |
| FR-LIFE-004 | §6 |
| FR-XFER-001, FR-XFER-002 | §6 — delegated to `room-lifecycle.md` §4 |
| FR-XFER-003 | §3 `included()`, §3.1, §4 `404` |
| NFR-SEC-001 | Every predicate in §3 and §5 is evaluated server-side under the room lock |
| NFR-SEC-002 | §2 invite-code generation; §3.1 — an empty list rather than a `404` oracle |
| NFR-USAB-001 | §3 via the pagination envelope |
| FR-DEPLOY-002 (`platform-operations.md`) | §1 `X-TurnBase-Room-Instance` as an advisory hint |
