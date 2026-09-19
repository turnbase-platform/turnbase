# Admin REST API

The HTTP surface `admin-tooling.md` describes but never gives a shape to: the review queue
(FR-REV-001…006), the badge model's admin-facing half (FR-BADGE-001…004), and official-game
publication (FR-OFF-001…002). Also supplies the one mechanism no document in this corpus defines
anywhere else: **how a `game` row comes to exist in the first place** (§3).

Realizes `admin-tooling.md` FR-ADM-001…003, FR-REV-001…006, FR-OFF-001…002, NFR-AUD-001,
NFR-CRED-001.

## Related

| Document | What it supplies |
|---|---|
| [rest-conventions.md](rest-conventions.md) § *Actuator and the Management Port* | Why this surface shares a listener with actuator, and why that listener must never be publicly routable |
| [../deployment/local-environment.md](../deployment/local-environment.md) §1 | The host port map — `8081`, loopback-bound |
| [file-uploads.md](file-uploads.md) | The pre-signed-URL upload flow this document's §4 reuses verbatim for the official path |
| [../manifest/bundle-format.md](../manifest/bundle-format.md) | Phases A–G — the validation/activation pipeline §4's endpoints trigger; unchanged by this document |
| [../platform/data-model-catalog.md](../platform/data-model-catalog.md) | `game`, `game_version`, `game_review` — every column this document reads or writes |
| [error-handling.md](error-handling.md) | RFC 9457 shape; this document adds one type, `unauthenticated` reused for a missing/bad `Authorization` header |
| [../../requirements/admin-tooling.md](../../requirements/admin-tooling.md) | FR-ADM-001…003, FR-REV-001…006, FR-OFF-001…002 |

---

## 1. Why this document exists

`admin-tooling.md` states what the admin API must be able to do; nothing states its endpoints. Two
gaps, found while building `IMP-M4-05`:

**No document anywhere defines how a `game` row is created.** `file-uploads.md` step 1 is `POST
/api/games/{gameId}/versions` — it assumes `gameId` already names a row. `game-catalog.md` FR-GAME-001
("upload new game... deferred to the Game SDK specification") and
`game-development-experience.md` FR-UPLOAD-001 both defer the mechanism onward, and neither onward
reference ever lands on it. Under `ADR-0006` the MVP has exactly one path that needs this to work —
the admin's own official upload (FR-OFF-001) — so this document supplies it for that path only; the
community path (FR-GAME-001 proper) stays deferred, and is `IMP-M4-01`'s gap to close when community
uploads open, not this one's.

**This surface is not `/api/`.** `rest-conventions.md` § *Base Path* states "all REST endpoints are
served under `/api/`" with no carve-out — written before this listener existed. It is amended by that
document's own cross-reference to here: the admin API is a **second, independent listener**
(`local-environment.md` §1, `admin-tooling.md` CON-001), not a namespace sharing the public API's
port, so `/api/`'s rule is scoped to the public listener and this one uses `/admin/` on `8081`.

---

## 2. Authentication

Every route below requires **HTTP Basic** (FR-ADM-002). Credentials are the single static pair bound
from `turnbase.admin.username`/`turnbase.admin.password` (already present as `AdminProperties`,
`secrets-and-configuration.md` §1/§7) — there is no per-operator account and no session.

- Missing or malformed `Authorization` header, or a value that does not match the configured pair:
  `401`, `error-handling.md`'s `unauthenticated` type, `WWW-Authenticate: Basic realm="turnbase-admin"`.
- There is no `403` on this surface — Basic auth is all-or-nothing (CON-001's "all operators have full
  access", *Out of Scope* "fine-grained admin role tiers"); a valid credential can do everything below.
- Credentials are never echoed in a response, a log line, or a stack trace (NFR-CRED-001) — the
  `GlobalExceptionHandler` catch-all already logs at `warn` without the request body; this surface adds
  no exception path that would include the `Authorization` header.

Every mutating route (§4's create/confirm, §5's approve/reject) writes one structured log entry —
`action`, `gameId`, timestamp — before returning (NFR-AUD-001). The Basic-auth principal is a shared
credential, not a person (`admin-tooling.md` CON-002), so the log entry names the action, not an
operator identity finer than "the admin credential."

---

## 3. `POST /admin/games` — create an Official game

The missing mechanism (§1). Creates the `game` row an official upload's first version needs to exist
(`game_version.game_id`'s `NOT NULL` foreign key, `data-model-catalog.md` §2) before §4 can run.

```http
POST /admin/games
```

No request body. `data-model-catalog.md` §1's own rule — "the manifest's values are used only when
the `game` row is created, on the first successful activation" — means `title`/`short_description`
are placeholders here, overwritten unconditionally the moment the first version activates (§4); there
is nothing for the admin to supply yet that the manifest won't immediately replace.

Inserts one row:

```sql
insert into game (game_id, owner_user_id, title, short_description, badge, listed)
values (:gameId, null, '', '', 'OFFICIAL', true)
```

`owner_user_id IS NULL` and `badge = 'OFFICIAL'` together satisfy `game_official_ownerless_ck`
(§1's equivalence, `data-model-catalog.md` §1). `listed = true` immediately, rather than waiting for
an approval step that official games never take (FR-OFF-002) — the row is invisible regardless until
`active_version_id IS NOT NULL` (`game_public_idx`'s predicate), which nothing sets until §4's first
activation, so setting it now creates no premature visibility.

**Response — `201 Created`:**

```json
{ "gameId": "3fa85f64-5717-4562-b3fc-2c963f66afa6" }
```

`Location: /admin/games/{gameId}`.

---

## 4. Official upload — admin-scoped mirror of `file-uploads.md`

```http
POST /admin/games/{gameId}/versions
Content-Type: application/json

{ "version": "1.0.0", "bundleSize": 42000000 }
```

```http
POST /admin/games/{gameId}/versions/{uploadId}/confirm
```

```http
GET /admin/games/{gameId}/versions/{uploadId}
```

**Identical, field for field, to `file-uploads.md` steps 1, 2, 3 and 4** — same request/response
bodies (`CreateVersionResponse`'s `uploadId`/`uploadUrl`/`expiresAt`), the same pre-signed-PUT step 2
direct to storage, the same synchronous stage-A/B1 `422`s and asynchronous Phase C-G outcome, the same
`bundle-format.md` Phases A–G in full. Nothing about validation, activation, or the version state
machine changes for an admin-created game — a bundle that fails F1 fails identically whether the game
is Official or (once community uploads open) Unverified.

**What differs is auth and what activation does *not* do.** These three routes sit on the admin
listener behind Basic auth (§2) rather than a player session, because the caller creating an Official
game's version has no session to hold — and, per `bundle-format.md` §3.2 stage E4, this is the path
that makes `runtime: "jvm"` legal at all (`ADR-0006`): E4 checks two things, only one of which existed
before this document — `game.badge = 'OFFICIAL' AND game.owner_user_id IS NULL` (`IMP-M4-03`, already
built) **and** that the request arrived through this section's routes, not the public
`/api/games/{gameId}/versions` ones. The second half has no mechanism to check *except* which listener
served the request — there is no shared session, token, or header the public and admin routes both
see — so E4 is satisfied by these routes existing on the admin listener at all, never by inspecting
anything in the request itself.

Activation (`bundle-format.md` §3.2 Phase G, `data-model-catalog.md` §2's badge-transition table) is
unchanged: `OFFICIAL` stays `OFFICIAL`, no `game_review` row is ever written by this pipeline for any
badge (nothing in it writes one today — §5's rows come only from a submission action this document
does not define, `admin-tooling.md` FR-PRV-004, which belongs to whichever item eventually builds
community submission). **This is FR-OFF-002 in full**: an Official game was never eligible to enter
the queue on this path, because nothing on this path ever inserts into it.

---

## 5. Review queue

### 5.1 `GET /admin/games` — list pending

```http
GET /admin/games
```

`game_review` rows with `decided_at IS NULL`, oldest `submitted_at` first (FR-REV-002,
`game_review_queue_idx`).

```json
{
  "items": [
    {
      "gameId": "…", "title": "…", "developerUsername": "alice",
      "submittedAt": "2026-09-19T10:00:00Z"
    }
  ]
}
```

No pagination — `pagination-filtering-sorting.md` is for the public catalog's scale; the queue is
every currently-undecided community submission, which `ADR-0006`'s MVP holds at exactly zero.

### 5.2 `GET /admin/games/{gameId}` — full detail

FR-REV-003: "full details of any game" — not scoped to pending ones, since an operator inspects a
game's history after a decision too.

```json
{
  "gameId": "…", "title": "…", "shortDescription": "…",
  "developerUsername": null,
  "badge": "OFFICIAL", "listed": true,
  "activeVersion": { "version": "1.0.0", "activatedAt": "…" },
  "openReview": null
}
```

`developerUsername: null` for an ownerless (Official) game (`data-model-catalog.md` §1's null-owner
rendering rule, reused here rather than invented fresh). `openReview` carries the undecided
`game_review` row's `submittedAt` when one exists, `null` otherwise. Unknown `gameId`: `404`.

### 5.3 `POST /admin/games/{gameId}/approve`

FR-REV-004. Requires an open review (`game_review_open_key`'s undecided row) for this game — none:
`404`. Otherwise, one transaction:

1. `game_review`: `decided_at = now()`, `decision = 'APPROVED'`, `decided_by = 'admin'`.
2. `game`: `badge = 'VERIFIED'`, `listed = true` (`data-model-catalog.md` §1 — approval realizes the
   owner's publish intent, not just the badge).
3. A platform notification to the developer (`sse-notifications.md`'s type table — this document does
   not add a new type; the existing notification-write precedent is a direct-SQL insert,
   `room.RoomInvitationRepository`'s established shape).

`204`.

### 5.4 `POST /admin/games/{gameId}/reject`

```json
{ "reason": "Backend crashes on more than two players." }
```

FR-REV-005/006. Same open-review precondition as §5.3; missing `reason` (blank or absent): `422`,
`business-rule-violation`. Otherwise: `decision = 'REJECTED'`, `rejection_reason` stored verbatim,
`decided_by = 'admin'`; `game.badge`/`game.listed` **untouched** — rejection is non-destructive
(FR-REV-006), the game stays exactly as private as it was the moment before the decision. A platform
notification carrying `reason` is sent to the developer (FR-REV-005). `204`.

---

## 6. Errors

Beyond the standard set (§2's `401`): `404` (§4's unknown `gameId` inherited from `file-uploads.md`;
§5.2's unknown `gameId`; §5.3/§5.4's no-open-review), `422` (§5.4's missing `reason`, plus everything
`file-uploads.md`/`bundle-format.md` already define for §4's routes, unchanged).

## 7. What is deliberately absent

- **No `DELETE`/edit on a game from this surface.** `admin-tooling.md` *Out of Scope*: no game content
  scanning, no resubmission workflow (OQ-001), no delisting of an already-public game (OQ-002).
- **No submission endpoint.** `POST /admin/games/{gameId}/approve`/`reject` consume a `game_review` row
  this document never produces; FR-PRV-004 (the owner's submit action) is public-listener, session-
  authenticated, and belongs with whichever item builds it — out of place on a Basic-auth surface.
- **No browser panel** (FR-ADM-003) — every route here is `curl`-shaped JSON, on purpose.

## 8. Requirements traceability

| Requirement | Realized by |
|---|---|
| FR-ADM-001…003 | §2, `local-environment.md` §1 (this document adds no new port/bind decision) |
| FR-REV-001…003 | §5.1, §5.2 (the pending state itself is `data-model-catalog.md` §4's `game_review` insert — this document has no producer for it; see §7) |
| FR-REV-004…006 | §5.3, §5.4 |
| FR-OFF-001…002 | §3, §4 |
| NFR-AUD-001 | §2's audit-log clause |
| NFR-CRED-001 | §2 |
