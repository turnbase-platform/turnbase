# Platform Data Model — Accounts, Identity and Sessions

## Scope

The relational schema behind identity: user accounts (registered and guest), authentication methods,
sessions, profile privacy settings, and the erasure model that account deletion implements.

Sources: [`../../requirements/user-accounts.md`](../../requirements/user-accounts.md),
[`../../requirements/platform-views.md`](../../requirements/platform-views.md) (privacy surfaces),
[ADR-0004](../../decisions/0004-account-erasure-pseudonymization.md) (erasure by pseudonymization).

**Conventions** — PostgreSQL types, normative column names, `timestamptz` written with the database
clock — are those of [`data-model.md`](data-model.md) *Convention*. That document is the
authority for rooms; this one for identity. `room_participant.user_id` and `room.host_user_id`
reference `app_user(user_id)` defined here.

**The organising constraint of this document is that deletion is not one operation.** A registered
account's deletion is a *soft* delete that retains the row as a namespace tombstone (FR-ACCT-006,
FR-ACCT-009), releases the email (FR-ACCT-005), destroys the credentials, and pseudonymizes history
in a *different* table (FR-HIST-030). A guest account's deletion is a *hard* delete (FR-GUEST-005).
The two paths touch the same table with opposite intent, and most of the design below exists to keep
them from colliding.

---

## 1. `app_user`

```sql
CREATE SEQUENCE guest_serial_seq AS bigint MINVALUE 0 START WITH 0;

CREATE TABLE app_user (
  user_id              uuid PRIMARY KEY,
  kind                 text        NOT NULL,   -- REGISTERED | GUEST
  username             text        NOT NULL,
  username_skeleton    text        NOT NULL,
  email                text        NULL,
  email_source         text        NULL,       -- SELF | OAUTH
  guest_serial         bigint      NULL,

  username_changed_at  timestamptz NULL,
  email_changed_at     timestamptz NULL,

  created_at           timestamptz NOT NULL DEFAULT now(),
  deleted_at           timestamptz NULL,
  deletion_reason      text        NULL,       -- SELF_SERVICE | GUEST_EXPIRED
  purgeable_after      timestamptz NULL,

  CONSTRAINT app_user_kind_ck CHECK (kind IN ('REGISTERED','GUEST')),
  CONSTRAINT app_user_username_len_ck CHECK (char_length(username) BETWEEN 3 AND 32),
  CONSTRAINT app_user_guest_serial_ck CHECK ((kind = 'GUEST') = (guest_serial IS NOT NULL)),
  CONSTRAINT app_user_email_ck CHECK (
    kind = 'GUEST' OR deleted_at IS NOT NULL
    OR (email IS NOT NULL AND email_source IS NOT NULL)
  )
);

CREATE UNIQUE INDEX app_user_skeleton_key   ON app_user (username_skeleton);
CREATE UNIQUE INDEX app_user_id_kind_key    ON app_user (user_id, kind);
CREATE UNIQUE INDEX app_user_guest_serial_key ON app_user (guest_serial) WHERE guest_serial IS NOT NULL;
CREATE UNIQUE INDEX app_user_email_key      ON app_user (lower(email)) WHERE email IS NOT NULL;
CREATE INDEX app_user_username_trgm_idx     ON app_user USING gin (lower(username) gin_trgm_ops)
  WHERE kind = 'REGISTERED' AND deleted_at IS NULL;
CREATE INDEX app_user_guest_expiry_idx      ON app_user (created_at)
  WHERE kind = 'GUEST' AND deleted_at IS NULL;
CREATE INDEX app_user_guest_purge_idx       ON app_user (purgeable_after)
  WHERE kind = 'GUEST' AND purgeable_after IS NOT NULL;
```

### `username_skeleton` is the uniqueness column, and `username` is not

FR-AUTH-003 makes uniqueness a property of the **confusable skeleton** of the normalized, case-folded
username, not of the raw string, so that `Alice` and `Аlice` (Cyrillic `А`) cannot coexist
([`../api-design/input-validation.md`](../api-design/input-validation.md)). Storing the skeleton in
its own column and putting the unique index there is what makes that rule a database invariant
rather than a check the application must remember to perform. The raw `username` carries no
uniqueness index at all: two distinct raw strings with the same skeleton must be rejected, and a
unique index on the raw string would let exactly those through.

`username_skeleton` is computed by the application (ICU4J) at insert and at every username change. It
is **not** a generated column, because the skeleton algorithm lives in a library whose output can
change across ICU releases; a generated column would silently rewrite existing rows on an ICU upgrade
and could produce a duplicate-key failure during a migration rather than at a controllable moment.
Recomputation is therefore an explicit, auditable batch operation, not a side effect of upgrading a
dependency.

The `guest-` reserved-prefix check (FR-AUTH-013) is applied to the skeleton for the same reason.

### The unique index spans deleted rows; the email index does not

FR-ACCT-006 reserves a deleted user's username permanently, and FR-AUTH-003 says uniqueness holds
"across all active and soft-deleted accounts". `app_user_skeleton_key` is therefore a **total**
unique index — the soft-deleted row is the reservation. No separate reservation table exists, and
none should: a second table holding usernames would need the same skeleton index, and the two could
disagree.

FR-ACCT-005 releases the email on deletion, in its own words: "The email address is released and
becomes available for re-registration." Release is implemented by **setting `email` to NULL** rather
than by an index predicate that skips deleted rows, because the address is then genuinely gone rather
than merely unindexed.

`app_user_email_key` is partial on `email IS NOT NULL` for **index size, not for correctness**.
PostgreSQL treats NULLs as distinct in a unique index, so an unqualified
`CREATE UNIQUE INDEX ON app_user (lower(email))` would already admit unlimited NULL-email rows —
tombstones and guests alike. The predicate keeps the guest population, which is the majority of rows
and permanently NULL here, out of an index that can never match them. (The same NULL-distinctness
rule is load-bearing rather than incidental one document over, where it lets several erased players
share a session: [`data-model-history.md`](data-model-history.md) §2.)

It indexes `lower(email)` because FR-AUTH-004's uniqueness is case-insensitive in practice even
though FR-AUTH-002 does not say so; comparing raw would let `A@x.com` and `a@x.com` both register and
then log in ambiguously under FR-AUTH-006.

**`app_user_email_ck` states the live-registered invariant, not just a source flag.** A live
registered account must have both an address and a provenance for it (FR-AUTH-001, FR-AUTH-007); the
disjunction exempts guests, which never have either, and tombstones, whose email has just been
released. Checking only `email_source IS NOT NULL` would let an email-update bug null the address
while leaving the provenance, producing a live account that `app_user_email_key` does not index and
that FR-AUTH-006's login-by-email can never find — with nothing in the schema objecting.

**`app_user_username_trgm_idx` is partial, and the predicate is a requirement rather than a
size optimisation.** FR-SOC-002 states that guest accounts do not appear in username search results,
and FR-ACCT-009's tombstone is reachable by direct URL but must not be *discoverable* — a deleted
person's username surfacing in search is the opposite of erasure. Putting both exclusions in the
index means the search query cannot forget them: any query that drops the matching `WHERE` clause
loses the index and becomes a visible performance regression rather than a silent privacy one.

### Guest serials start at zero, which Postgres does not do by default

FR-GUEST-001 specifies `guest-<N>` where N is "a DB serial value auto-incrementing from 0". A bare
`bigserial` starts at 1, so the sequence is declared explicitly with `MINVALUE 0 START WITH 0`. The
sequence is never reset and values are never reused, which is what gives FR-GUEST-002 its guarantee
even across the hard deletion of the row that held the serial.

Because the generated username is derived from a unique serial, no two guest usernames are the same
*string*. That is not quite the guarantee FR-GUEST-002 needs, because the enforcing index is on the
**skeleton**, and this document opens by explaining that distinct strings can share one: confusable
folding maps digits onto letters, so `guest-1` and a hypothetical `guest-l` fold together
([`../api-design/input-validation.md`](../api-design/input-validation.md)). Guest usernames are
generated from `[0-9]` only and the digit-to-letter folding is one-way — no digit folds onto another
digit — so distinct serials do yield distinct skeletons. The insert is nonetheless written to surface
a violation rather than swallow it: a unique-key failure on `app_user_skeleton_key` during guest
creation is an assertion failure, not a retryable conflict, because FR-GUEST-002 promises it cannot
happen.

A guest username can still collide with a *registered* one, which is precisely what FR-AUTH-013
prevents by reserving the prefix — and it checks the skeleton, so a lookalike prefix is rejected too.

### Guest deletion is two-phase, and the second phase is not on a timer

FR-GUEST-005 and FR-RET-002 call for guest accounts to be purged 24 hours after creation. Taken
literally against this schema, that job fails: **two** columns reference `app_user` with no `ON
DELETE` action — `room_participant.user_id` and `room.host_user_id`, the latter reachable because
FR-GUEST-006 lets guests create rooms — and closed rooms, with their participant rows, are retained
for seven days (FR-RET-006, FR-JOB-009). A guest who played 25 hours ago is still referenced, so the
delete raises a foreign-key violation, FR-JOB-003 logs it, and the job retries on the next interval
and fails again, indefinitely, for as long as any room record survives.

The fix is not a cascade. `ON DELETE CASCADE` on `room_participant.user_id` would remove a *seated*
participant from a live room with no event, no broadcast, and no state transition — the room would
simply have one fewer player than the last delta said it did. Deletion of an identity must never be
able to mutate a running game.

Guest purge is therefore two phases:

| Phase | Trigger | Query | Effect |
|---|---|---|---|
| **Revoke** | Token lifetime elapsed since creation (FR-GUEST-003, which defers the value to FR-SESS-001 — default 24 h, configurable) | `WHERE kind = 'GUEST' AND deleted_at IS NULL AND created_at < now() - :ttl`, over `app_user_guest_expiry_idx` | All `user_session` rows revoked; `deleted_at`, `deletion_reason = 'GUEST_EXPIRED'` and `purgeable_after` set. The account is inaccessible from this moment, which is what FR-GUEST-005 exists to achieve. |
| **Purge** | `purgeable_after` elapsed **and** nothing references the row | `WHERE kind = 'GUEST' AND purgeable_after < now()` over `app_user_guest_purge_idx`, `AND NOT EXISTS (… room_participant …) AND NOT EXISTS (… room WHERE host_user_id = …)` | Row hard-deleted; cascading children (§2, §3, §4) go with it. |

**Each phase needs its own index, because each has a different predicate.** `purgeable_after` is NULL
until phase one has already run, so `app_user_guest_purge_idx` cannot find phase one's candidates;
`app_user_guest_expiry_idx` does, and is partial on `deleted_at IS NULL` so it shrinks to nothing as
guests are collected rather than growing with the table.

**The referencing check covers both hard foreign keys**, not just the participant one. Today the two
are coextensive — a guest that hosts a room is also a participant in it, and participant rows are
never deleted individually — so a participant-only gate would work by accident. It is written against
both anyway, because "works by accident" is one host-transfer change away from reproducing the exact
failure this design removes.

**How long a guest row can survive its token.** Not "up to the closed-room retention window": the
bound is *room closure* + 7 days, and closure is itself unbounded — an In-Progress room with
connected players never trips the FR-JOB-007d idle sweep. A guest who plays a one-hour game is
collected about eight days after creation; one whose room runs for a week, about fifteen. That is a
real weakening of FR-RET-002's "24 hours", and `platform-operations.md` FR-RET-002 is amended to
state the actual bound rather than a number the system does not meet. What holds unconditionally at
24 hours is *inaccessibility*, which is the property the requirement exists to deliver; what is
deferred is the row.

### `email_source` records who owns the address, not where it came from

FR-AUTH-008 makes an OAuth-derived email immutable, and FR-AUTH-012 keeps it immutable even after a
password method is added. A flag on the *auth method* would therefore be the wrong place: the
constraint survives the addition — and the removal — of methods. `email_source = 'OAUTH'` on the user
row is the single fact both requirements test, and FR-ACCT-003's update path is gated on it directly.

### `app_user_id_kind_key` is redundant, and exists for one reason

`user_id` is already the primary key, so a unique index on `(user_id, kind)` adds no uniqueness. It
exists purely as a **foreign-key target**: it lets the social tables reference
`(user_id, kind)` and pin `kind = 'REGISTERED'` with a local `CHECK`, which turns FR-SOC-020 /
FR-GUEST-007 — "guests cannot have friends" — into a constraint the database will not let the
application violate. See [`data-model-social.md`](data-model-social.md) §1.

`kind` is immutable in the current requirements: there is no guest-to-registered upgrade path, so
nothing ever updates the referenced column and the `ON UPDATE CASCADE` on those constraints can never
fire. It is declared for documentation rather than for effect — if a conversion path is ever added,
the cascade is the behaviour that would be wanted, and its absence would be discovered as an update
that fails rather than as a decision somebody made.

### Rolling windows need one timestamp, not a history

FR-ACCT-002 and FR-ACCT-003 permit one change per rolling 30-day window. "At most once per window"
is decided entirely by the most recent change, so `username_changed_at` / `email_changed_at` suffice
and no audit table is needed. Both are NULL until the first change, which correctly makes the first
change always permitted.

---

## 2. `user_auth_method`

```sql
CREATE TABLE user_auth_method (
  auth_method_id   uuid PRIMARY KEY,
  user_id          uuid        NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
  method           text        NOT NULL,   -- PASSWORD | GOOGLE
  password_hash    text        NULL,       -- PHC-encoded Argon2id string
  provider_subject text        NULL,       -- OAuth 'sub' claim
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT user_auth_method_shape_ck CHECK (
    (method = 'PASSWORD' AND password_hash IS NOT NULL AND provider_subject IS NULL)
 OR (method = 'GOOGLE'   AND password_hash IS NULL     AND provider_subject IS NOT NULL)
  )
);

CREATE UNIQUE INDEX user_auth_method_per_user_key ON user_auth_method (user_id, method);
CREATE UNIQUE INDEX user_auth_method_subject_key
  ON user_auth_method (method, provider_subject) WHERE provider_subject IS NOT NULL;
```

**No salt column.** NFR-SEC-001 requires a unique random salt per user; the PHC string format Argon2id
emits (`$argon2id$v=19$m=...,t=...,p=...$<salt>$<hash>`) carries the salt *and* the cost parameters
inline. A separate column would be a second copy of a value the verifier reads from the hash anyway,
and the inline parameters are what makes a cost increase a rehash-on-next-login rather than a
migration.

**`UNIQUE (user_id, method)`** caps a user at one password and one Google identity. FR-AUTH-009 speaks
of "multiple authentication methods", which the two-row model satisfies; nothing in the requirements
contemplates two Google accounts on one user, and permitting it would make FR-AUTH-008's "the email
is bound to the OAuth provider" ambiguous about which provider.

**`UNIQUE (method, provider_subject)`** keys the OAuth identity, not the email. Google's `sub` is
stable across the user changing their Google email; the email is not. Keying on email would let one
Google identity attach to two TurnBase accounts after a rename, and would make an OAuth login into an
email lookup — which is the shape of the account-takeover this index exists to prevent.

**FR-AUTH-011 (at least one method) is not a database constraint.** It is a predicate over the *count*
of child rows, which PostgreSQL cannot express declaratively. It is enforced in the application as a
guarded delete (`DELETE ... WHERE ... AND (SELECT count(*) FROM user_auth_method WHERE user_id = ...) > 1`)
executed in the same transaction as the read, so a concurrent double-removal cannot strand an account
with zero methods. Guest accounts have zero rows here by design (FR-GUEST-004), so the rule reads
"every **registered** account has at least one".

**OAuth email collision.** `app_user_email_key` makes it impossible for a first-time Google login to
create a second account on an email that an existing credential account already holds — the insert
raises a unique violation. What the platform does in response (link, refuse, or prompt) is a
requirements question, and is answered by `user-accounts.md` FR-AUTH-016. The schema deliberately
forces the question rather than silently permitting a duplicate.

---

## 3. `user_session`

```sql
CREATE TABLE user_session (
  session_id      uuid PRIMARY KEY,
  user_id         uuid        NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
  issued_at       timestamptz NOT NULL DEFAULT now(),
  expires_at      timestamptz NOT NULL,
  revoked_at      timestamptz NULL,
  revoked_reason  text        NULL,   -- DISPLACED | LOGOUT | ACCOUNT_DELETED | GUEST_EXPIRED | KEY_ROTATED
  key_id          text        NOT NULL,
  user_agent_hash text        NULL
);

CREATE UNIQUE INDEX user_session_active_key ON user_session (user_id) WHERE revoked_at IS NULL;
CREATE INDEX user_session_expiry_idx ON user_session (expires_at) WHERE revoked_at IS NULL;
```

**The partial unique index is FR-SESS-002.** "Only one active session per account" is stated as a
requirement and is here made unfalsifiable: at most one non-revoked row can exist per user. Login is
therefore `UPDATE ... SET revoked_at = now(), revoked_reason = 'DISPLACED' WHERE user_id = :u AND revoked_at IS NULL`
followed by an `INSERT`, in one transaction. If two logins race, one insert loses on the unique index
and retries; neither can leave two live sessions behind. FR-SESS-003 falls out of the same statement,
and FR-SESS-004's error message is `revoked_reason`.

Note what the predicate is **not**: it is not `revoked_at IS NULL AND expires_at > now()`, because
`now()` is not immutable and cannot appear in an index predicate. Expiry is therefore evaluated at
read time and the expired-but-unrevoked row continues to occupy the slot until the next login revokes
it. This is correct — an expired session is not usable — and it means `user_session_expiry_idx` exists
only so a housekeeping job can tidy, not so authentication can function.

**Postgres is authoritative for revocation; the cookie is not self-sufficient.** The session cookie
carries a signed token whose `jti` is `session_id` (`user-accounts.md` CON-004,
[`secrets-and-configuration.md`](../deployment/secrets-and-configuration.md) §3). A signature check
alone cannot satisfy FR-SESS-003, which requires an *immediate* invalidation that a stateless token
by construction cannot express. Every authenticated request therefore resolves `session_id` against
this table. Caching that lookup in Redis is permitted only with a TTL short enough that the cache
cannot outlive the meaning of "immediately", and is **not** enabled for the MVP: Redis is a single
non-HA instance with an accepted loss window (ADR-0001), and a cache of *validity* fails open — a
Redis restart would resurrect every displaced session.

**`key_id`** names the JWT signing key the token was issued under, so a key retirement can revoke
exactly the sessions it invalidates rather than all of them
([`../deployment/secrets-and-configuration.md`](../deployment/secrets-and-configuration.md) §3.3).
`revoked_reason = 'KEY_ROTATED'` is the resulting reason.

**Session revocation must reach live connections.** WebSocket and SSE connections authenticate once,
at handshake, and then persist; revoking the row does nothing to a socket already open. The closing
of those connections is a behaviour, not a column, and is specified in `user-accounts.md`
FR-SESS-010 and [`../api-design/websocket.md`](../api-design/websocket.md).

> The identifier is FR-SESS-**010**, not the next free number. `FR-SESS-005` is already taken —
> `platform-architecture.md` defines it as the Game Host discarding session state on `game_over`.
> Requirement IDs are numbered per document, so the same string already means two unrelated things in
> two places for `FR-SESS-003`; the session-management block skips to 010 rather than add a third
> collision. See STATUS.md item 9.

---

## 4. `user_privacy_settings`

```sql
CREATE TABLE user_privacy_settings (
  user_id                uuid PRIMARY KEY REFERENCES app_user(user_id) ON DELETE CASCADE,
  profile_private        boolean NOT NULL DEFAULT false,
  history_visibility     text    NOT NULL DEFAULT 'PUBLIC',
  stats_visibility       text    NOT NULL DEFAULT 'PUBLIC',
  games_visibility       text    NOT NULL DEFAULT 'PUBLIC',
  friends_visibility     text    NOT NULL DEFAULT 'PUBLIC',
  block_friend_requests  boolean NOT NULL DEFAULT false,
  updated_at             timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT ups_history_ck CHECK (history_visibility IN ('PUBLIC','HIDDEN')),
  CONSTRAINT ups_stats_ck   CHECK (stats_visibility   IN ('PUBLIC','HIDDEN')),
  CONSTRAINT ups_games_ck   CHECK (games_visibility   IN ('PUBLIC','HIDDEN')),
  CONSTRAINT ups_friends_ck CHECK (friends_visibility IN ('PUBLIC','FRIENDS_ONLY','HIDDEN'))
);
```

**A row exists only for registered users.** Guest profiles display the username and nothing else
(FR-GUEST-010, FR-PROF-002) — not "everything hidden", but *no sections at all*. A guest row here
would be six columns that no read path consults, and it would make "is this profile configurable"
a value test rather than an existence test.

**Three sections are two-valued and one is three-valued, and that asymmetry is in the requirements,
not in this design.** FR-PROF-006 offers history, statistics, friends and uploaded games as
hide/show; FR-SOC-017 gives the friends section a third level, **Friends Only**. Modelling all four
as `text` over the same vocabulary rather than three booleans plus one enum means widening any
section later is a `CHECK` change and nothing else. It also makes the read path uniform: one
resolution function over four identically-shaped values.

**`profile_private` dominates.** FR-PROF-005 and FR-SOC-019 both state that a private profile hides
everything *regardless* of per-section settings, so the per-section values are not cleared when
privacy is switched on — they are ignored, and restored intact when it is switched off. VW-SET-006a
hides the per-section toggles in that state rather than resetting them, which is only coherent
because the values persist.

**`block_friend_requests` lives here, and there is no block table.** FR-PROF-008 / FR-SOC-021 is a
single global toggle: it blocks *all* incoming friend requests, not requests from a named person.
Per-user blocking is explicitly out of scope in `social-friends.md`. A `user_block` table would be
the natural place to look for this feature and would be empty forever, so it is not created; see
[`data-model-social.md`](data-model-social.md) §4.

---

## 5. Erasure — what account deletion actually writes

FR-ACCT-004 promises an irreversible deletion; ADR-0004 requires that history survive it. Those are
reconciled by making deletion a *scatter* of different operations over different tables, in one
transaction:

| Table | Operation | Requirement |
|---|---|---|
| `app_user` | `deleted_at = now()`, `email = NULL`, `email_source = NULL`; `username` and `username_skeleton` **retained** | FR-ACCT-005, FR-ACCT-006, FR-ACCT-009 |
| `user_auth_method` | all rows deleted | FR-ACCT-004 (irreversibility) |
| `user_session` | all rows revoked, `ACCOUNT_DELETED` | FR-ACCT-004 |
| `user_privacy_settings` | row deleted | no profile remains to configure |
| `friendship`, `friend_request` | all rows deleted, both directions | FR-SOC-012, FR-ACCT-005 |
| `room_invitation` | all rows deleted, **both** as inviter and as invitee | FR-ACCT-005 (amended), FR-INV-002 |
| `notification` | all rows deleted (own), plus the subject cascade from the two rows above | FR-ACCT-005 (amended) |
| `room_participant` | every non-closed room the user occupies is left as a **confirmed voluntary departure** | FR-LIFE-004, FR-DC-005 |
| `room` | rooms hosted with no other human remaining are **owed** a closure with `closed_reason = 'ACCOUNT_DELETED'`; otherwise a host transfer is owed. Neither happens in this transaction — see below | FR-XFER-002, FR-LIFE-004 |
| `game_review` | any open review withdrawn: `decided_at = now()`, `decision = 'WITHDRAWN'` | §4 of [catalog](data-model-catalog.md#4-game_review) |
| `game_history_entry` | `user_id = NULL`, `subject_token` assigned | FR-HIST-030, ADR-0004 |
| `game` (owned) | `archived_at = now()` | FR-ACCT-007 |
| `game.completed_session_count` | untouched | FR-ACCT-008, FR-STATS-004 |

**Nothing here happens by cascade, and that is the trap this table exists to avoid.** A registered
deletion is a *soft* delete, so every `ON DELETE CASCADE` in the corpus — on `friendship`,
`friend_request`, `room_invitation`, `notification` — is inert on this path. Each row above is an
explicit statement. Four of them were missing from the first draft of this document precisely because
the cascades made them look automatic:

- **`game_review`.** `game_review_open_key` and `game_review_queue_idx` are partial on
  `decided_at IS NULL`, so an undecided submission stays in FR-REV-002's admin queue forever, for an
  archived game whose owner no longer exists and to whom FR-REV-004/005's decision notification
  cannot be delivered. `WITHDRAWN` is a third decision value for exactly this, and it is a decision
  rather than a deletion so the queue's history stays intact.
- **`room_invitation`, both legs.** An invitation the departing user *sent* would otherwise stay
  pending with a live actionable notification in the recipient's bell, and accepting it would route
  them into a room hosted by a deleted account.
- **`room_participant` and `room`.** The erasure transaction writes the *durable* half only: each
  non-closed room the user occupies gets `left_at = now()`, `leave_reason = 'LEFT'` and
  `lost_announced_at = NULL`. It does **not** close rooms, transfer hosts or broadcast, because it
  runs on whichever instance received the REST call and that instance almost certainly does not own
  those rooms — under ADR-0002 a non-owner's `ROOM_CLOSED` reaches nobody. The owning instance's next
  deadline-sweep tick ([`room-lifecycle.md`](room-lifecycle.md) §5.1 duty 2) performs the
  announcement, the FR-XFER-001 transfer and the FR-XFER-002 closure, under the claim.
  `data-model.md`'s `closed_reason = 'ACCOUNT_DELETED'` therefore still has account deletion as its
  only producer; what changed is *which actor* writes it, and when. The bound is one sweep interval.

The erasure is one transaction, and the room work inside it is now only the participant departures —
a conditional update per room, which cannot fail on lock contention the way a closure could. It is
still ordered **last** so that a retry re-runs only the idempotent operations above it: each is a
conditional update or a delete whose second execution matches zero rows. The closure and host-transfer
work that used to sit here is deliberately outside the transaction, deferred to the room's owner; a
retry of the erasure re-commits the same participant rows and produces no second tail, because
`left_at IS NULL` no longer holds.

**The username is kept on the account row but stripped from history, and that is not a
contradiction.** FR-ACCT-006 retains the username as a *namespace reservation* and FR-ACCT-009 renders
it on a tombstone page that states the account no longer exists. ADR-0004 strips it from history so
that a retained history row is no longer *linkable* to a person. The two hold together only because
history stops referencing `user_id` at the same moment; if it kept the foreign key, the tombstone
would re-link every row it was supposed to sever. That is why the erasure of history is a nulling of
the reference and not merely a display rule — see
[`data-model-history.md`](data-model-history.md) §2.

**The pseudonym is random, not derived.** A token computed as `HMAC(user_id, pepper)` is
*reversible by enumeration*: the user-id space is small enough to brute-force offline given the pepper,
so anyone holding a database dump and the key can re-link every erased row. ADR-0004 requires
non-reversibility, and the only construction that provides it is one that discards the input — a
fresh random token minted at deletion, written to every one of that user's entries in the same
`UPDATE`, and stored nowhere else. It is stable (one token per erasure, shared across that person's
rows) and unlinkable (no key exists that maps it back).

**Deletion cannot cascade to history**, and the schema enforces that: `game_history_entry.user_id` is
nullable with no `ON DELETE` action, so a *hard* delete of an `app_user` row would raise a
foreign-key violation rather than quietly destroying opponents' records. Registered accounts are
never hard-deleted, and guests never have history (FR-HIST-003), so the constraint should never fire
— which is exactly the property wanted from a constraint whose job is to catch a future mistake.

---

## 6. What is deliberately absent

- **No `user_block` table.** Per-user blocking is out of scope (`social-friends.md`); the only block
  in the requirements is the global `block_friend_requests` toggle above.
- **No login-failure or lockout table.** NFR-SEC-003's IP lockout and NFR-SEC-007's minting throttle
  are Redis counters ([`../api-design/rate-limiting.md`](../api-design/rate-limiting.md) Tiers 1 and
  5). They are IP-keyed, pre-authentication, and lossy by design: losing them fails *closed enough*
  (an attacker gets a fresh budget, not a bypassed password), so they do not justify a relational
  table or the write amplification on every failed login.
- **No password-reset token table.** `user-accounts.md` CON-003 defers password reset until email
  infrastructure exists.
- **No `pending_oauth_registration` table.** The token that carries a first-time Google user from
  `/auth/callback` to `/auth/complete-registration` (VW-OAUTHCOMP-001) is short-lived and its loss
  costs the user one repeat of the OAuth round trip, so it lives in Redis with a TTL. Nothing
  downstream depends on it having existed.
- **No separate `guest_account` table.** A guest is an `app_user` with `kind = 'GUEST'` and a serial.
  Splitting it would fork every foreign key in the corpus — `room_participant`, `notification`,
  `game_session_completion` — into two nullable columns, to model a role that differs by a handful of
  permission checks.
- **No `avatar` or display-name column.** `user-accounts.md` puts user-provided personal information
  out of scope; ADR-0004 nonetheless names avatar and display name among the PII to strip, which is
  forward-looking rather than a description of today's schema.
- **No email verification state.** `user-accounts.md` CON-002: no mail is sent, so there is nothing
  to record.
- **No `CHECK` for the username charset.** `app_user_username_len_ck` covers FR-AUTH-014's 3–32
  bound, which is a cheap and total guard, but the charset half of that requirement — letters,
  combining marks, digits, `_` and `-`, first character a letter or digit, single script — is an ICU
  property, not a regular expression, and belongs with the skeleton computation in
  [`../api-design/input-validation.md`](../api-design/input-validation.md). The line between what is
  enforced here and what is enforced there is whether PostgreSQL can decide it without a library.

---

## 7. Requirements traceability

| Requirement | Realized by |
|---|---|
| FR-AUTH-001/004 | `app_user.email`, `app_user_email_key` |
| FR-AUTH-003/013/015 | `app_user.username_skeleton`, `app_user_skeleton_key` |
| FR-AUTH-014 (length half only) | `app_user_username_len_ck`; charset in `input-validation.md` |
| FR-AUTH-007…012 | `user_auth_method`, `app_user.email_source` |
| FR-AUTH-016 | `app_user_email_key` forces the collision to surface |
| FR-SESS-001…004 | `user_session`, `user_session_active_key`, `revoked_reason` |
| FR-SESS-010 | `revoked_at` is the trigger; the connection close is behavioural (§3) |
| FR-SOC-002 (guest/tombstone exclusion) | `app_user_username_trgm_idx` partial predicate |
| FR-ACCT-001 | `app_user.user_id` |
| FR-ACCT-002/003 | `username_changed_at`, `email_changed_at` |
| FR-ACCT-004…009 | §5 erasure table |
| FR-PROF-003…008 | `user_privacy_settings` |
| FR-GUEST-001/002 | `guest_serial_seq`, `app_user_guest_serial_key` |
| FR-GUEST-003/005 | `user_session.expires_at`, `app_user.purgeable_after`, §1 two-phase purge |
| NFR-SEC-001 | `user_auth_method.password_hash` (PHC Argon2id) |
| ADR-0004 | §5 random-token pseudonymization |
