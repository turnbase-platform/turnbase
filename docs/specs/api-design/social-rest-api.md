# Social REST API

The HTTP surface for the friend graph: sending, resolving and listing friend requests, the friend
list itself, and username search. There is no WebSocket component — every mutation here is a single
request/response with no shared, versioned state to broadcast, unlike a room.

Realizes `../../requirements/social-friends.md` FR-SOC-001…021 and
`../../requirements/notifications-invitations.md` FR-FREQ-001…006 (the request/notification coupling
only — delivery is `sse-notifications.md`'s). Closes **`IMP-GATE-34`**'s missing-route half: the
predicate table in [rest-conventions.md](rest-conventions.md) has named
`/api/friend-requests/{id}`'s ownership rule since that document was written, but no document ever
defined the endpoints themselves.

## Related

| Document | What it supplies |
|---|---|
| [rest-conventions.md](rest-conventions.md) | Status codes, the `/api/friend-requests/{id}` and `/api/users/me/**` predicates, the `Origin` check |
| [pagination-filtering-sorting.md](pagination-filtering-sorting.md) | The list envelope, `page`/`size`/`sort` parameters |
| [error-handling.md](error-handling.md) | RFC 9457 Problem Details and the type taxonomy |
| [../platform/data-model-social.md](../platform/data-model-social.md) | `friendship`, `friend_request` — the canonical ordering, the cap, the guest-exclusion FK |
| [../platform/data-model-notifications.md](../platform/data-model-notifications.md) | `notification` — the subject foreign keys and the four `FRIEND_REQUEST*`/`FRIEND_ADDED` types this surface writes |
| [../../requirements/social-friends.md](../../requirements/social-friends.md) | The requirements this realizes |
| [../../requirements/notifications-invitations.md](../../requirements/notifications-invitations.md) | FR-FREQ-001…006 |

---

## 1. Endpoints

| Method | Path | Auth | Success | Requirements |
|---|---|---|---|---|
| `GET` | `/api/users?search=` | Session, registered | `200` | FR-SOC-002 |
| `POST` | `/api/friend-requests` | Session, registered | `201` | FR-SOC-001…004 |
| `GET` | `/api/friend-requests` | Session, registered | `200` | FR-SOC-013…015 |
| `POST` | `/api/friend-requests/{id}/accept` | Session, registered | `200` | FR-SOC-006 |
| `DELETE` | `/api/friend-requests/{id}` | Session, registered | `204` | FR-SOC-005, FR-SOC-007 |
| `GET` | `/api/users/{username}/friends` | Public, privacy-resolved | `200` | FR-SOC-010, FR-SOC-013 |
| `DELETE` | `/api/users/me/friends/{userId}` | Session, registered | `204` | FR-SOC-011 |

Seven endpoints, none of them WebSocket. `POST /api/friend-requests/{id}/accept` is the one
non-noun path in the API — see §4's note.

**"Session, registered" throughout** means the guest check of `account.ProfileService`'s
`requireRegistered` (FR-SOC-020, FR-GUEST-007): a guest principal gets `403`, the same shape every
other `/api/users/me/**` mutation already uses for the identical reason. Guests have no `friendship`
or `friend_request` row reachable under any code path (the composite FK), so this is enforcement, not
merely UX.

---

## 2. `GET /api/users?search=` — username prefix search

```
GET /api/users?search=ali
```

`search` is required and matched case-insensitively as a **prefix** against `username`, using
`app_user_username_trgm_idx` (`data-model-social.md` §5). Only `kind = 'REGISTERED'` rows are
eligible (FR-SOC-002 — "Guest accounts do not appear in search results"). A private profile appears
in results (FR-SOC-002 second sentence); only its content is hidden, not its existence, matching
`GET /api/users/{username}`'s own resolution in `user-accounts.md`.

Standard list envelope (`pagination-filtering-sorting.md`); default sort `username,asc`; no other
sort field is whitelisted.

```json
{
  "content": [
    { "userId": "a1b2…", "username": "alice", "profilePrivate": false, "canSendRequest": true }
  ],
  "pagination": { "page": 1, "size": 25, "totalElements": 1, "totalPages": 1 }
}
```

**`canSendRequest` is computed server-side and is the only signal FR-SOC-021 exposes.** It is `false`
for the caller's own row, an existing friend, a pending outgoing or incoming request either way, *and*
a recipient with `block_friend_requests` enabled — four unrelated reasons collapsed into one boolean
on purpose. A client (or an attacker scripting the endpoint) cannot distinguish "already friends" from
"has requests blocked" from this field alone, which is what "rejected without disclosing that a block
exists" (this item's own *Done when*) means for the surface a user actually browses.

---

## 3. `POST /api/friend-requests` — send

```http
POST /api/friend-requests
Content-Type: application/json

{ "recipientUsername": "alice" }
```

One endpoint for both FR-SOC-001 (sent from a profile) and FR-SOC-002 (sent from search) — the
request body is identical either way, and the platform has no way to distinguish the two UI entry
points and no reason to.

### Evaluation order, inside one transaction

1. Resolve `recipientUsername` to a `REGISTERED`, non-deleted user. Miss → `404`.
2. Self-request → `422`.
3. Already friends, or a pending request already exists in **either** direction other than the
   reverse case below → `409` (`friendship`/`friend_request_pair_key` — FR-SOC-003).
4. **Reverse request already pending** (recipient already sent the caller one) — FR-SOC-004: delete
   the opposite `friend_request` row, insert `friendship` in canonical order, write
   `FRIEND_REQUEST_ACCEPTED` to the original sender and `FRIEND_ADDED` to the caller. No new
   `friend_request` row is ever written for this case (`data-model-social.md` §2).
5. Caller is at the friend cap (FR-SOC-009 first sentence) → `422`. **Not checked** in the step 4
   path — FR-SOC-004's auto-accept is not the "acceptance" FR-SOC-009 conditions the block on, which
   speaks only of the recipient's *manual* accept; a caller who is already at cap chose to send this
   request, and the platform completing an existing mutual match is not a new friendship the cap
   exists to slow down.
6. Recipient has `block_friend_requests` enabled → `422`, generic message, identical in shape to
   step 5's — see §2's `canSendRequest` note.
7. Otherwise: insert `friend_request` with `expires_at = now() + turnbase.retention.friend-request`,
   write a `FRIEND_REQUEST` notification to the recipient with `friend_request_id` set (FR-FREQ-001).

### Response

Both outcomes are `201` — a new fact was created in the graph either way, and neither is a retry of
the other.

```json
{ "outcome": "REQUEST_SENT", "friendRequest": { "requestId": "9c1e…", "recipientUsername": "alice", "createdAt": "…", "expiresAt": "…" } }
```

```http
201 Created
Location: /api/friend-requests/9c1e…
```

```json
{ "outcome": "FRIENDS", "friend": { "userId": "a1b2…", "username": "alice" } }
```

The `FRIENDS` outcome carries no `Location` — there is no addressable resource at that address; the
friendship is reached through §6, keyed by the other party's id, not a request id that no longer
exists.

---

## 4. `POST /api/friend-requests/{id}/accept` — accept

FR-SOC-006. Recipient only. Deletes the request, inserts `friendship` in canonical order, writes
`FRIEND_REQUEST_ACCEPTED` to the sender and `FRIEND_ADDED` to the caller — the same three writes as
§3 step 4, because accepting one side of a pending pair and having it auto-resolve from the other
side are the same terminal state reached two ways.

**Why a verb, not a noun.** Accept is not a partial update of the request (it does not survive the
call — `data-model-social.md` §2 keeps only pending rows) and not a delete (a delete alone is
FR-SOC-007/FR-SOC-005 below, with the opposite notification effect). Modelling it as `PATCH
{"status":"ACCEPTED"}` would need a `status` field on a resource that is never read back with one;
the request either exists (pending) or it does not.

Recipient at the friend cap (FR-SOC-009 second sentence — "the recipient cannot accept them while at
cap") → `422`. Not the sender's cap: FR-SOC-009 blocks *the recipient's* accept, and by construction
the sender was under cap when they sent it.

### Response

`200`, not `201` — the friendship is not newly reachable at this URL, it has no URL of its own (§6).

```json
{ "friend": { "userId": "f3a1…", "username": "bob" } }
```

### Errors

Unknown `id` → `404`. `principal` is the sender, not the recipient (`rest-conventions.md`'s
"`action must match the side`") → `403`.

---

## 5. `DELETE /api/friend-requests/{id}` — cancel or decline

One endpoint, two FRs, discriminated entirely by which side of the request the caller is on —
`rest-conventions.md`'s ownership predicate already states this: "`principal ∈ {sender, recipient}`,
and the action must match the side."

| Caller is | Effect | Notification |
|---|---|---|
| the sender | Cancel (FR-SOC-005) | none — "the recipient's pending notification is removed" (the `friend_request_id` FK cascade, `data-model-notifications.md` §1) |
| the recipient | Decline (FR-SOC-007) | `FRIEND_REQUEST_DECLINED` to the sender (FR-FREQ-004); the decliner gets none |

Both delete the `friend_request` row in the same transaction as the notification write (FR-FREQ-006).

### Idempotency

`204` whether or not a matching row exists — `rest-conventions.md`'s general `DELETE` rule ("the
caller's desired state holds"), same as room leave. A row that existed but was already resolved
(accepted, expired, or resolved by the other side a moment earlier) is indistinguishable from one
that never did, and both end in the caller having no such pending request, which is what they asked
for.

**Only a row that exists and names neither the caller as sender nor as recipient is `403`.** That is
the one case this endpoint can still get wrong — acting on someone else's request — and
`rest-conventions.md` names it explicitly.

---

## 6. `GET /api/users/{username}/friends` — friend list content

The Friends section's content (FR-SOC-013 "Friends" tab), served under the profile it belongs to,
the same way `GET /api/users/{username}` (`user-accounts.md`, `IMP-M1-07`) is.

**Privacy resolution is identical to the profile endpoint's, not a second copy of it.** The profile
response's `visibleSections` already says whether `"friends"` is in the set for this
`(username, viewer)` pair (FR-SOC-017…019, with FR-SOC-017's `FRIENDS_ONLY` third value resolved by
this item — see §8). This endpoint re-runs the identical check rather than trusting the client to
have read the other response first — a direct call here is exactly as answerable as one that reads
the profile first. When the section is not visible, the response is `200` with an empty `content`
array, not `403`/`404` — a distinguishable error here would only repeat what `visibleSections`
already discloses (NFR-SOC-SEC-001), and an empty list is one less shape for the client to branch on.

The owner sees the full list regardless of their own `friendsVisibility` setting (FR-SOC-018).

Standard list envelope; default and only sort is `username,asc` (FR-SOC-010, case-insensitive).

```json
{
  "content": [ { "userId": "f3a1…", "username": "bob" } ],
  "pagination": { "page": 1, "size": 25, "totalElements": 1, "totalPages": 1 }
}
```

Unknown username → `404`, matching the profile endpoint.

---

## 7. `DELETE /api/users/me/friends/{userId}` — unfriend

FR-SOC-011. `204`, idempotent — deleting a friendship that does not exist (never existed, or the
other party already removed it) also returns `204`, for the same reason as §5.

`{userId}`, not `{username}` — the only place in this surface addressed by id rather than username,
because the friend list content (§6) already hands the client the id, and a second lookup by name
would be a wasted round trip for an action the client can only reach from that list.

---

## 8. Extends `GET /api/users/{username}` — `relationshipState`

`user-accounts.md`/`IMP-M1-07` defined the profile envelope without a field for "how does the caller
relate to this profile" because nothing before this item could answer it. FR-SOC-016 needs it — the
profile button reads Friends / Request sent / Request received / (nothing, for a stranger) — so this
item adds one field to `ProfileResponse`, present only for a registered, non-owner viewer of a
registered profile (`@JsonInclude(NON_NULL)`, matching every other conditional field there):

```json
{ "relationshipState": "NONE" | "FRIENDS" | "REQUEST_SENT" | "REQUEST_RECEIVED" }
```

This is also the mechanism that closes the obligation `IMP-M1-07` left this item: `visibleSections`
now includes `"friends"` under `FRIENDS_ONLY` exactly when `relationshipState = "FRIENDS"` would
apply, both computed from the same canonically-ordered `friendship` lookup in the same request.

---

## 9. Errors

`rest-conventions.md`'s status codes with `error-handling.md`'s Problem Details shape.

| Condition | Status | `type` slug | Requirement |
|---|---|---|---|
| Malformed body, missing `recipientUsername` | `400` | `validation-failed` | — |
| No session | `401` | `unauthenticated` | — |
| Guest principal on any endpoint in this document | `403` | `forbidden` | FR-SOC-020, FR-GUEST-007 |
| `id` names a request naming neither side as the caller | `403` | `forbidden` | `rest-conventions.md` |
| Accept called by the sender, not the recipient | `403` | `forbidden` | FR-SOC-006 |
| `recipientUsername` / `{username}` does not resolve to a live, registered user | `404` | `not-found` | — |
| Unknown `{id}` on accept | `404` | `not-found` | — |
| Sending to self | `422` | `business-rule-violation` | FR-SOC-003 |
| Sender at cap (send only, not the auto-accept path) | `422` | `business-rule-violation` | FR-SOC-009 |
| Recipient at cap (accept only) | `422` | `business-rule-violation` | FR-SOC-009 |
| Recipient has blocked requests | `422` | `business-rule-violation` | FR-SOC-021 |
| Already friends, or a non-reverse duplicate pending request | `409` | — | FR-SOC-003 |
| Rate limit | `429` | `rate-limit-exceeded` | `rate-limiting.md` |

`403` and `404` are never interchanged as a disclosure control on this surface the way
`game-catalog.md` NFR-SEC-002 does for private games — every username here is already known to the
caller (they searched it or are on its profile page), so hiding existence buys nothing FR-SOC-002
hasn't already given away.

---

## 10. What is deliberately absent

- **No `GET /api/friend-requests/{id}`.** Nothing reads a single pending request in isolation; the
  Pending tab is the list (§1), and accept/decline act on an id the list already supplied.
- **No `PATCH /api/friend-requests/{id}`.** §4 explains why accept is a verb rather than a status
  field.
- **No friendship resource or id.** A friendship is the unordered pair; it is reached by the other
  party's `userId` (§6, §7), never by an id of its own — there is nothing else it would need to be
  addressed by.
- **No block/unblock endpoint.** FR-SOC-021's toggle is `user_privacy_settings.block_friend_requests`,
  already reachable through `PATCH /api/users/me/privacy` (`IMP-M1-07`). Adding a second route here
  would give the same column two ways to change it.

---

## 11. Requirements traceability

| Requirement | Realized by |
|---|---|
| FR-SOC-001/002 | §3 — one endpoint for both entry points |
| FR-SOC-003 | §3 steps 2–3; `friend_request_pair_key` |
| FR-SOC-004 | §3 step 4 |
| FR-SOC-005 | §5, sender side |
| FR-SOC-006 | §4 |
| FR-SOC-007 | §5, recipient side |
| FR-SOC-008 | No endpoint — taking no action needs none |
| FR-SOC-009 | §3 step 5, §4 |
| FR-SOC-010 | §6 default sort |
| FR-SOC-011 | §7 |
| FR-SOC-013…015 | §1 `GET /api/friend-requests`, §6 |
| FR-SOC-016 | §8 `relationshipState` |
| FR-SOC-017…019 | §6, §8 |
| FR-SOC-020 | §1 "Session, registered" |
| FR-SOC-021 | §2 `canSendRequest`, §3 step 6 |
| FR-FREQ-001 | §3 step 7 |
| FR-FREQ-003 | §3 step 4, §4 |
| FR-FREQ-004 | §5 |
| FR-FREQ-006 | §5 same-transaction delete; FK cascade for cancel |
