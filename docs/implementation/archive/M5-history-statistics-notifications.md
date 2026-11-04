# Archive — M5 History, statistics, notifications

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim by `IMP-M20-01`. Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M5-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M5-01 | Game history recording and query API | platform | M3-09 | DONE |
| IMP-M5-02 | Per-game statistics | platform | M5-01 | DONE |
| IMP-M5-03 | Notifications and the SSE stream | platform | M1-06, M1-07 | DONE |
| IMP-M5-04 | Retention purge jobs | platform | M5-01, M5-03 | DONE |

---

## M5 — History, statistics, notifications

### IMP-M5-01 — Game history recording and query API

**Repo:** `turnbase-platform` · **Depends on:** IMP-M3-09

**Closed:** IMP-GATE-81 (opened and closed 2026-09-27, session 81) — this item's own *Satisfies*
claimed FR-HIST-020…030 (the Profile History Tab's display, search and pagination behaviour) in full,
but no document gave it a REST surface to build against — `data-model-history.md` §2's own three
indexes (`ghe_user_recent_idx`, `ghe_user_name_trgm_idx`) exist specifically to answer this tab, yet
nothing exposed them over HTTP — and this item's own *Done when* clause never tested any of
FR-HIST-020…030, only the recording transaction. `IMP-M6-06` claims the identical range on the
frontend side but had no dependency on this item and no endpoint to render. Same shape as
`IMP-GATE-80`. Fixed: new `docs/specs/api-design/history-rest-api.md` —
`GET /api/users/{username}/history`, privacy-resolved the same way `social-rest-api.md` §7 resolves
the friends tab, searchable and paginated per FR-HIST-025…026; registered in that directory's
`INDEX.md` and in `game-history.md`'s new *Related API Specifications* section. This item retitled
from *Game history recording* to name the read side it was already claiming; its read-list and
*Done when* gained the new document.

**Read first:**
- `docs/requirements/game-history.md` FR-HIST-001…006, FR-HIST-010…013, FR-HIST-020…030
- `docs/specs/platform/data-model-history.md` §1 (`game_session_completion`), §2
  (`game_history_entry`)
- `docs/requirements/game-contracts.md` FR-OUTCOME-001…004
- `docs/specs/flows/06-game-end-and-rematch.md`
- `docs/specs/api-design/history-rest-api.md` (`IMP-GATE-81`) — the read endpoint this item also
  builds

**Satisfies:** `game-history.md` FR-HIST-001…006, FR-HIST-010…013, FR-HIST-020…030,
NFR-HIST-001…003; `game-contracts.md` FR-OUTCOME-001, FR-OUTCOME-004

**Done when:** a malformed outcome from game code cannot abort the whole recording transaction with
no retry path (`ghe_placement_ck`); `GET /api/users/{username}/history` implements
`history-rest-api.md` in full — the `visibleSections` privacy re-check, `search`, pagination, and the
server-computed `outcomeLabel`/`gameLinkable` fields — since that document, not this clause, is what
makes FR-HIST-020…030 checkable.

**Game code produces the outcome, so the outcome is untrusted input.** Validate it before it reaches
a `CHECK` constraint; a constraint violation here rolls back a completed game's entire record and
there is nothing left to retry from.

---

### IMP-M5-02 — Per-game statistics

**Repo:** `turnbase-platform` · **Depends on:** IMP-M5-01

**Read first:**
- `docs/requirements/per-game-statistics.md` FR-STATS-001…004, FR-STATS-010…012, FR-STATS-020…027
- `docs/specs/api-design/statistics-rest-api.md` (`IMP-GATE-90`) — the two read surfaces
- `docs/specs/platform/data-model-history.md` §3 — *The per-game counter and its writer*
- `docs/requirements/user-accounts.md` FR-GUEST-009, FR-ACCT-008

**Closed:** IMP-GATE-90 (opened and closed 2026-09-30, session 99) — the item claims FR-STATS-010…012
and FR-STATS-020…027, but no document defined a route or response field for either:
`catalog-rest-api.md` §6 excluded per-game statistics from game detail, and `profile-rest-api.md` has
no statistics content. `IMP-M5-01` already shipped the single counter writer, so what is left is
the two reads. Fixed: new `statistics-rest-api.md` — `completedSessionCount` on `GET
/api/games/{gameId}` (also added to `catalog-rest-api.md` §4/§6) and `GET
/api/users/{username}/statistics` (`totalPlayed`, `mostPlayedGame`), privacy-resolved like `/history`
with a zero-state `200`. Registered in `api-design/INDEX.md` and `per-game-statistics.md`.

**Satisfies:** `per-game-statistics.md` FR-STATS-001…004, FR-STATS-010…012, FR-STATS-020…027,
NFR-STATS-001…003; `user-accounts.md` FR-GUEST-009, FR-ACCT-008

**Done when:** the counter has exactly **one** writer — the one `data-model-history.md` §3 names. Two
writers race and the count drifts silently, with no error and no way to detect it after the fact.
Guests accumulate no statistics (FR-GUEST-009). Removing a deleted user's statistics leaves every
other player's aggregates unchanged (FR-ACCT-008).

---

### IMP-M5-03 — Notifications and the SSE stream

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-06, IMP-M1-07

**`IMP-GATE-34` narrowed this item's *Satisfies*** (closed 2026-09-08, session 34, on `IMP-M1-09`):
FR-FREQ-001…006 dropped — this item delivers whatever rows land in `notification` over SSE and
enforces the generic retention/alert rules, but never writes a `friend_request`-linked row itself;
`IMP-M1-09` does, and now carries the claim. FR-FREQ-001…006 stays in this item's read-list: the type
table (`data-model-notifications.md` §3) is still the wire contract the SSE stream serves.

**`IMP-GATE-58` narrowed this item's *Satisfies*** (closed 2026-09-13, session 50, on `IMP-M2-12`):
`FR-LINK-001…002` dropped — double-claimed with `IMP-M2-12`, and neither item builds anything for it;
`IMP-M2-01`'s already-shipped invite-code mechanism is the entire behaviour, and now carries the claim.

**Closed:** IMP-GATE-59 (opened and closed 2026-09-14, session 51) — this item's *Satisfies* claims
FR-NOTIF-001…009 in full (notification center access, unread badge, read/unread state, mark-all-read,
delete, retention, real-time and offline delivery, pagination), but no document in the corpus ever
defined the notification center's REST surface — `sse-notifications.md` specifies only the stream
(`GET /api/notifications/stream`), and `rest-conventions.md`'s Authorization table already assumed
`GET /api/notifications` and `/api/notifications/{id}` exist (the ownership predicate, the
principal-scoped collection rule) without any document ever naming their methods, request/response
shapes, or status codes. `room-invitation-rest-api.md` §6 independently assumed the same endpoint as
where a received `ROOM_INVITATION` is read, confirming the gap is real rather than a document this
item merely hadn't read yet. Same shape as `IMP-GATE-31`/`33`/`35`/`37`/`57`/`58`. This item's own
read-list never named `rest-conventions.md` or `pagination-filtering-sorting.md` either, despite both
supplying conventions the missing surface would have to follow. Fixed: new
[`docs/specs/api-design/notification-rest-api.md`](../../specs/api-design/notification-rest-api.md) —
five endpoints (`GET /api/notifications` list, `GET .../unread-count`, `PATCH .../{id}` mark read,
`POST .../read-all`, `DELETE .../{id}`); registered in that directory's `INDEX.md`;
`room-invitation-rest-api.md` §6 and its Related table now cite it instead of a bare requirement ID.
Read-list corrected below.

**Done 2026-09-14 (session 52).** `notification.NotificationController` builds the five
`notification-rest-api.md` endpoints exactly (`GET /api/notifications`, `GET .../unread-count`, `PATCH
.../{id}`, `POST .../read-all`, `DELETE .../{id}`), each scoped by the `rest-conventions.md` ownership
predicate (`WHERE user_id = :principal`, `404` on mismatch) via `NotificationRepository`'s direct SQL
against `notification` — this package's own table, so no cross-schema read is needed the way
`room.RoomInvitationRepository` needed one. `notification.NotificationStreamController` builds `GET
/api/notifications/stream`; `notification.NotificationEmitterRegistry` is the SSE counterpart of
`websocket.WebSocketConnectionRegistry` — same two-index shape (connections by emitter id, a secondary
index by user id), the `sse-notifications.md` § Keepalive comment on a 30s `@Scheduled` tick, and an
`@EventListener` on `session.SessionRevokedEvent` that sends the matching session's stream one final
`event: alert` naming `revoked_reason` and closes it (`FR-SESS-010`, `IMP-GATE-28` — the SSE half
`IMP-M2-02` already closed for STOMP). Offline catch-up (`delivered_at IS NULL`, oldest `event_seq`
first, stamped as sent) is `NotificationRepository#markUndeliveredAsDelivered`. `AlertPublisher`'s real
implementation, `SseAlertPublisher`, replaces `PendingAlertPublisher` (deleted) and routes through the
same registry — `room.RoomInvitationService`'s existing `alertPublisher.publish(...)` call for
`INVITATION_ACCEPTED`/`INVITATION_DECLINED` now actually reaches a connected host with no change on
that side.

**Live push of a newly created notification to an already-open stream is deliberately not built here.**
`room.RoomInvitationRepository` and `social.SocialRepository` write `notification` rows by direct SQL,
with no dispatch call of any kind — unlike alerts, no placeholder port for this existed for them to
call, and this item's own *Done when* clause names only the offline-catch-up path and the
revocation-close behaviour, not a live-push guarantee for an already-connected client. A user who is
already on the stream when another feature writes a row sees it only at their next panel open or badge
refresh (`unread-count`), not pushed instantly — `sse-notifications.md`'s "at-least-once at best... the
notification center is the backstop" reasoning covers exactly this gap, but closing it for existing
producers would mean editing two other already-`DONE` items' repositories, which this item's *Done
when* does not ask for. Left as a scope note rather than a gate: nothing here contradicts another
document or leaves an unmade decision, and the *Done when* clause is satisfiable exactly as written.

**Verified.** `NotificationEmitterRegistryTest` (unit, mocked `SseEmitter` — the
`WebSocketConnectionRegistryTest` pattern): alert routing by user id, silent drop for an offline user,
session-scoped close-with-final-alert on `SessionRevokedEvent`, keepalive. `NotificationControllerIT`
(integration, real Postgres): all five endpoints including ownership `404`s, the guarded one-way
`read_at` transition and its `422` on `{"read":false}`, mark-all-read and delete scoped to the
principal, delete idempotency; the stream test connects with the JDK `HttpClient`, asserts the exact
`event: notification` / `id:` / flattened-payload frame shape `sse-notifications.md`'s wire example
specifies for a row inserted before connecting, and confirms `delivered_at` is stamped.
`./mvnw verify -Pintegration` green locally (162 unit + all integration tests, JaCoCo merged gate met).

**Read first:**
- `docs/requirements/notifications-invitations.md` FR-NOTIF-001…009, FR-ALERT-001…005, FR-ALERT-010,
  FR-FREQ-001…006
- `docs/specs/platform/data-model-notifications.md` §1 (`notification`), §3 (types), **§4 — alerts
  have no table, and three current "notifications" are alerts**
- `docs/specs/api-design/sse-notifications.md` **in full**
- `docs/specs/api-design/notification-rest-api.md` **in full** — the five REST endpoints this item
  builds
- `docs/specs/api-design/rest-conventions.md` § *Authorization and Ownership* — the
  `/api/notifications/{id}` ownership predicate and the principal-scoped collection rule
- `docs/specs/api-design/pagination-filtering-sorting.md` — the envelope and total-ordering rule
  `notification-rest-api.md` §2's list endpoint follows
- `docs/requirements/platform-operations.md` FR-JOB-013, FR-RET-001…006

**Satisfies:** `notifications-invitations.md` FR-NOTIF-001…009, FR-ALERT-001…005, FR-ALERT-010,
NFR-PERF-001, NFR-SCALE-001, NFR-SEC-001; `user-accounts.md`
FR-SESS-010; `platform-views.md` VW-NOTIF-001…004

**Done when:** the five `notification-rest-api.md` endpoints exist, each enforcing the
`rest-conventions.md` ownership predicate and returning the exact status codes and bodies that
document specifies; the retention purge is indexed **partially on having no subject**, so it can never
remove an actionable message out from under a live object; and no notification is permanently
unpurgeable because its subject never expires. The SSE connection registry subscribes to
`IMP-M1-06`'s `SessionRevokedEvent`: on receipt, the matching session's stream sends a final `event:
alert` naming `revoked_reason` and then closes — the SSE half of `FR-SESS-010`'s duty (`IMP-GATE-28`),
narrowed out of `IMP-M1-06` because no stream registry existed there to close.

**Persisted notifications and transient alerts are two classes, not one with a flag** (§4). Three
things the requirements call notifications are alerts and must never get a table row — writing them
to `notification` makes them re-deliverable on reconnect, which is the opposite of what a transient
alert is for.

---

### IMP-M5-04 — Retention purge jobs

**Repo:** `turnbase-platform` · **Depends on:** IMP-M5-01, IMP-M5-03

**Narrowed by IMP-GATE-54** (`IMP-M2-10`, opened and closed 2026-09-13, session 46) — this item's
*Satisfies* claimed the full `FR-JOB-001…013` range verbatim, identical to `IMP-M2-10`'s claim of the
same full range, but this item's read-list touches only the notification/history retention domain:
`FR-JOB-001` (guest cleanup) is `IMP-M1-05`'s, `FR-JOB-006…011` (deadline sweep and room
reconciliation/purge) are `IMP-M2-07`'s/`IMP-M2-10`'s, and `FR-JOB-012` (upload slot sweep) is
`IMP-M4-03`'s — none of those documents appear here. Fixed: narrowed to `FR-JOB-002` (notification
purge, `data-model-notifications.md`) and `FR-JOB-013` (already named explicitly below); `NFR-JOB-001…002`
dropped (both are `IMP-M2-07`'s/`IMP-M2-10`'s recoverability bounds, not a retention-window property).

**Read first:**
- `docs/requirements/platform-operations.md` FR-RET-001…006, FR-JOB-002, FR-JOB-013
- `docs/specs/platform/data-model-history.md` §4 (erasure), `data-model-notifications.md` §1
- `docs/specs/deployment/local-environment.md` §7.2 (job scheduling), §7.3 (retention windows)

**Satisfies:** `platform-operations.md` FR-RET-001…006, FR-JOB-002, FR-JOB-013;
`game-history.md` NFR-HIST-003

**Done when:** every retention window comes from the §7.3 configuration keys and none is hard-coded;
the FR-JOB-013 expiry purge exists, is named, and is the **only** mechanism that ever removes an
actionable notification (IR-20); every job honours the FR-JOB-008 startup suppression **except** the
adopt duty, which IMP-M2-10 exempts; a purge that would remove a row a live object still references
cannot run — the partial index of IMP-M5-03 is the guard, not a code check.

---
