# Profile REST API

The HTTP surface for `GET /api/users/{username}` — the public, privacy-resolved profile envelope
every profile-reading view composes against. `IMP-M1-07` shipped this route in `account.
ProfileController`/`ProfileService` (session 32); no document has specified its response shape until
now, despite `social-rest-api.md` §9, `catalog-rest-api.md` §3 and `history-rest-api.md` all treating
it as an established contract they merely extend or reference (**`IMP-GATE-82`**).

Realizes `../../requirements/user-accounts.md` FR-PROF-001…008, FR-ACCT-009…010, FR-GUEST-010.

## Related

| Document | What it supplies |
|---|---|
| [rest-conventions.md](rest-conventions.md) | Status codes, the optional-auth "public, privacy-resolved" pattern, `GET /api/users/me`'s distinct account representation |
| [error-handling.md](error-handling.md) | RFC 9457 Problem Details and the type taxonomy |
| [social-rest-api.md](social-rest-api.md) §9 | The `relationshipState` field this document's registered-non-owner case carries |
| [catalog-rest-api.md](catalog-rest-api.md) §3 | The `owner` filter the uploaded-games profile section drives from this envelope's `username` |
| [../../requirements/user-accounts.md](../../requirements/user-accounts.md) | FR-PROF-001…008, FR-ACCT-009…010, FR-GUEST-010 |

---

## 1. Endpoint

| Method | Path | Auth | Success | Requirements |
|---|---|---|---|---|
| `GET` | `/api/users/{username}` | Public, privacy-resolved | `200` | FR-PROF-001…008, FR-ACCT-009…010, FR-GUEST-010 |

Exempt from session authentication (`user-accounts.md` NFR-SEC-006) — an unauthenticated caller
receives the same route, resolved as if it had no viewer identity. Unknown username → `404`.

---

## 2. Response envelope

One shape, `@JsonInclude(NON_NULL)` — the fields present vary by case below rather than the client
unwrapping a variant:

```json
{
  "username": "string, always present",
  "userId": "uuid, present only for the registered-user cases (§2.3, §2.4)",
  "deleted": "true, present only for the soft-deleted case (§2.1) — otherwise absent, never false",
  "kind": "\"REGISTERED\", present only for the registered-user cases (§2.3, §2.4)",
  "profilePrivate": "boolean, present only for the registered-user cases (§2.3, §2.4)",
  "visibleSections": "array of strings, present only for the registered-user cases (§2.3, §2.4)",
  "relationshipState": "\"NONE\" | \"FRIENDS\" | \"REQUEST_SENT\" | \"REQUEST_RECEIVED\", present only for a registered, non-owner viewer of a registered profile (§2.4)"
}
```

`visibleSections` names only the sections the viewer may see — a hidden section is an absent array
entry, not a `false` the client is trusted to respect. Its members are drawn from:

```
"gameHistory" | "statistics" | "friends" | "uploadedGames"
```

### 2.1 Soft-deleted account — FR-ACCT-009

Checked before `kind`, so a purged guest gets it too.

```json
{ "username": "alice", "deleted": true }
```

### 2.2 Guest profile — FR-GUEST-010 / FR-PROF-002

"Only the username… regardless of who is viewing it," including the guest viewing themselves.

```json
{ "username": "guest-4f2a" }
```

### 2.3 Registered profile, owner viewing — FR-PROF-007

The viewer's `userId` equals the row's. Every section is visible regardless of privacy settings —
`visibleSections` is always the full set, and `relationshipState` is never populated for oneself:

```json
{
  "username": "alice",
  "userId": "3f2b6b0a-...",
  "kind": "REGISTERED",
  "profilePrivate": true,
  "visibleSections": ["gameHistory", "statistics", "friends", "uploadedGames"]
}
```

### 2.4 Registered profile, non-owner viewing

`profilePrivate: true` → `visibleSections` is empty and no other section content is disclosed:

```json
{
  "username": "alice",
  "userId": "3f2b6b0a-...",
  "kind": "REGISTERED",
  "profilePrivate": true,
  "visibleSections": []
}
```

`profilePrivate: false` → `visibleSections` names the non-`HIDDEN` sections. A registered, non-owner
viewer additionally gets `relationshipState` (`social-rest-api.md` §9); an unauthenticated viewer does
not, and the `friends` section resolves as visible only when the setting is `PUBLIC` or (for an
authenticated viewer) `FRIENDS_ONLY` and `relationshipState = "FRIENDS"`:

```json
{
  "username": "alice",
  "userId": "3f2b6b0a-...",
  "kind": "REGISTERED",
  "profilePrivate": false,
  "visibleSections": ["gameHistory", "statistics", "uploadedGames"],
  "relationshipState": "NONE"
}
```

---

## 3. Errors

`rest-conventions.md`'s status codes with `error-handling.md`'s Problem Details shape.

| Condition | Status | `type` slug |
|---|---|---|
| `{username}` does not resolve to any user row (registered or guest, live or soft-deleted) | `404` | `not-found` |

---

## 4. Requirements traceability

| Requirement | Covered by |
|---|---|
| FR-PROF-001…006, FR-PROF-008 | §2.3, §2.4 — privacy-resolved section visibility |
| FR-PROF-007 | §2.3 — owner exemption from their own privacy settings |
| FR-ACCT-009 | §2.1 — soft-deleted placeholder |
| FR-GUEST-010 | §2.2 — guest username-only view |
