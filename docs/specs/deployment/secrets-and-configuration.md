# Secrets and Configuration

Where credentials come from, how they reach a running process, and how the one that changes on a
schedule — the JWT signing key — rotates without logging everybody out.

Realizes review blocker **OPS-5** and `../../requirements/platform-operations.md` FR-CRED-001…005.
Scoped local-first per [ADR-0001](../../decisions/0001-local-first-mvp-platform.md); §7 states the
production escalation for each secret rather than deferring the subject wholesale.

Non-secret tunables — timeouts, intervals, retention windows, rate-limit budgets — are in
[`local-environment.md`](local-environment.md) §7. The split is deliberate: everything in that table
belongs in version control and in a `ConfigMap`, and nothing here ever does.

---

## 1. The inventory

| Secret | Consumer | Rotatable without downtime | Local source |
|---|---|---|---|
| JWT signing key | Platform Monolith | **Yes** — §3 | generated at first start into `.secrets/` |
| PostgreSQL **owner** password (`turnbase_owner`) | Provisioning only — never held by a running service | Restart of the init step | `.env` |
| PostgreSQL **application** password (`turnbase_app`) | Platform Monolith | With a two-phase change | `.env` |
| Redis password | Monolith, Game Host | With a two-phase change | `.env` |
| MinIO access key + secret | Monolith, Game Host | Yes (second key pair, then retire) | `.env` |
| Google OAuth client ID + secret | Platform Monolith | Yes (Google permits two) | `.env`, absent by default |
| Admin Basic-auth credentials | Platform Monolith | Restart | `.env` |
| Grafana admin password | Grafana | Restart | `.env` |
| Alert webhook URL (`TURNBASE_ALERT_WEBHOOK_URL`) | Alertmanager | Replace the URL | `.env`, absent by default |

Nine secrets, one of which rotates on a schedule. The rest rotate when something has gone wrong,
which is why only the first gets a mechanism and the others get a procedure.

**A Slack or email webhook URL is a bearer credential**, not a configuration value: anyone holding it
can post into the channel. It is in this table rather than in `local-environment.md` §7 for that
reason, and it is absent by default — see [`observability.md`](observability.md) §6, which states what
still works when it is unset.

**The OAuth client secret is absent by default and the platform starts anyway.** `FR-AUTH-007`'s
Google login is unavailable without it, and the login page hides the button rather than offering one
that fails. Requiring it would mean nobody can run the stack without registering an application with
Google — a hard dependency on a third party for a local-first project whose credential login
(FR-AUTH-006) is complete on its own.

---

## 2. How a secret reaches a process

Three mechanisms, one per environment, all landing in the same place: an environment variable read
by Spring's relaxed binding.

| Environment | Mechanism |
|---|---|
| IDE / bare `docker compose` | `deploy/compose/.env`, **git-ignored**, created from `.env.example` |
| Local Kubernetes | A `Secret`, created by `make secrets` from the same `.env` |
| CI | GitHub Actions secrets injected as environment variables (FR-CICD-009) |
| Production (post-MVP) | §7 |

`.env.example` is committed and contains **no values** — only keys, with a comment giving the shape
and how to obtain one. It is the checklist for a new machine, and its diff is how a new secret
becomes known to everyone rather than to the person who added it.

**No secret has a default in `application.yml`.** A missing secret must fail startup with a message
naming the key, not fall back to `changeme` and start successfully. A default that works is a
default that reaches production; this is the class of mistake that is invisible precisely because
nothing breaks.

The one exception is the JWT key in the `local` profile (§3.1), and it is an exception because it is
*generated*, not defaulted.

---

## 3. JWT signing keys

### 3.1 Algorithm and provenance

**HMAC-SHA256 (HS256)** over a 256-bit key. Asymmetric signing (RS256/EdDSA) exists to let a party
that cannot be trusted with the signing key still verify tokens; the Platform Monolith is the only
issuer and the only verifier, and the Game Host never sees a session token — it authenticates over
gRPC on the internal network and deals in session identifiers, not user credentials. A public key
nobody needs is a key management burden with no reader.

| Environment | Where the key comes from |
|---|---|
| `local` | Generated on first start into `.secrets/jwt-keys.json` (git-ignored) and reused thereafter, so a restart does not log the developer out |
| `test`, `e2e` | Generated per run, in memory. Deterministic sessions across runs are not wanted |
| Kubernetes / production | Supplied; startup fails if absent |

Generating rather than defaulting is what keeps the local profile convenient without shipping a key.
A committed development key is a key that will one day be a production key.

### 3.2 The key set, and why there is more than one

The monolith holds a **key set**, not a key:

```json
{
  "active":  { "kid": "k3", "secret": "…", "notBefore": "2026-08-09T10:00:00Z" },
  "retired": [ { "kid": "k2", "secret": "…", "retiredAt": "2026-08-09T10:00:00Z" } ]
}
```

New tokens are signed with `active`. Verification accepts `active` **or** any key in `retired`. The
token's `kid` header selects the key, and `user_session.key_id`
([`../platform/data-model-accounts.md`](../platform/data-model-accounts.md) §3) records the same
value on the server side.

Without the retired set, rotation is a mass logout: every token signed by the previous key fails
verification the instant the new one is installed, and every player in a live game is disconnected at
once. With it, rotation is invisible.

### 3.3 Rotation

Three steps, and the middle one is the only one that takes time.

1. **Promote.** A new key becomes `active`; the previous `active` moves to `retired`. New logins are
   signed with the new key; existing tokens keep verifying.
2. **Wait out the session lifetime.** After `turnbase.auth.session-ttl` (24 h by default) no
   unexpired token can still be signed by the retired key, because token lifetime does not extend
   with activity (FR-SESS-001).
3. **Retire.** The old key is removed from the set. Any session still naming it is revoked with
   `revoked_reason = 'KEY_ROTATED'`, which is why that value exists.

Step 3 normally revokes nothing. It is written as a revocation rather than as a deletion because the
alternative — silently dropping a key and letting the affected tokens fail signature verification —
produces a 401 indistinguishable from a forged token, both for the user and in the logs.

**An emergency rotation skips step 2.** A compromised key is retired immediately, every session it
signed is revoked, and everyone signs in again. The graceful path exists so that the *routine* case
is not indistinguishable from the emergency one.

### 3.4 Rotation and live connections

This is the part that interacts with the rest of the platform, and it is the reason rotation belongs
in a spec rather than a runbook.

WebSocket and SSE connections authenticate **once**, at handshake, and then persist — a STOMP
connection in an active game may live for hours. Revoking a session row does nothing to a socket
already open, so `user-accounts.md` FR-SESS-010 requires revocation to close the connections it
invalidates.

Three consequences:

- **Graceful rotation closes nothing.** Steps 1 and 2 revoke no sessions, so no connection is
  touched. This is the whole point of the retired set.
- **Emergency rotation is a mass disconnect**, and it lands on live games. Every affected player's
  connection closes, which is an involuntary disconnect (`reconnection-flow.md` FR-DC-001) and opens
  a grace period for each. They can only return by signing in again, so the practical bound on
  recovery is how fast a person can type a password against `turnbase.room.grace-period`'s 60
  seconds. Most will not make it, and the honest statement is that an emergency key rotation
  forfeits in-progress games. It is the correct trade against a leaked signing key; it should not be
  discovered during one.
- **The close must be a close, not a rejection of the next frame.** A connection whose session is
  revoked but which is never written to again would otherwise stay open indefinitely, holding a
  reserved slot and receiving broadcasts. The revocation path pushes a
  `SESSION_INVALIDATED` frame and closes, which is `user-accounts.md` FR-SESS-010 and the same
  mechanism FR-SESS-003's displacement uses.

### 3.5 Claims

```json
{ "sub": "<user_id>", "jti": "<session_id>", "kid": "k3", "iat": …, "exp": … }
```

No username, no email, no role, no privacy settings. Everything but identity is read from the
database on the request, because a claim is a cached copy that cannot be invalidated: a username in
the token would survive an FR-ACCT-002 rename for up to 24 hours, and a role claim would survive its
own revocation.

`jti` is the session identifier and is what makes the token stateful. The signature check is a
cheap gate; the authoritative test is that `user_session` has a live row
([`../platform/data-model-accounts.md`](../platform/data-model-accounts.md) §3), which is what
FR-SESS-003's "immediately invalidated" requires and what no self-contained token can provide.

---

## 4. Datastore credentials

### PostgreSQL

Two roles, and the split is the point:

| Role | Used by | Privileges |
|---|---|---|
| `turnbase_app` | The application at runtime and Flyway | `CONNECT`, `USAGE` on the schema, DML on all tables, DDL |
| `turnbase_owner` | Provisioning only | Owns the database; `CREATE EXTENSION` |

`turnbase_app` holds DDL because migrations run in-process at startup
([ADR-0011](../../decisions/0011-schema-migrations.md) §1) — separating them would mean a migration
job with its own credentials, which ADR-0011 §3 records as the escalation if migrations ever become
long enough to warrant it. What `turnbase_app` does **not** hold is superuser, which is why
`CREATE EXTENSION` is a provisioning step and the baseline migration only asserts the result
([`schema-migrations.md`](schema-migrations.md) §5).

Rotating the password is two-phase, because the application cannot be holding a connection with the
old one when it disappears: create a second role or set a new password with the old still valid,
restart the application, then invalidate the old. With one instance this is a restart; with a rolling
deploy the overlap means both passwords must work briefly, which PostgreSQL does not support on a
single role — hence "second role" as the general answer.

**Where the split is actually made.** `postgres:16-alpine` runs every `*.sql` and `*.sh` in
`/docker-entrypoint-initdb.d` once, on an empty data directory, as the superuser named by
`POSTGRES_USER`. That is the only hook, and it is where the two roles are created:

```sql
-- deploy/compose/initdb/01-roles.sql
CREATE ROLE turnbase_app LOGIN PASSWORD :'app_password';
GRANT CONNECT ON DATABASE turnbase TO turnbase_app;
GRANT USAGE, CREATE ON SCHEMA public TO turnbase_app;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

`POSTGRES_USER` is therefore `turnbase_owner`, **not** `turnbase_app` — the container's own user is
the superuser by construction, so naming the application role there would hand it superuser and
violate FR-CRED-005 with nothing appearing to be wrong. The application connects as `turnbase_app`
with `TURNBASE_DB_APP_PASSWORD`; `turnbase_owner`'s password reaches the init step and nothing else.

`GRANT ... CREATE ON SCHEMA public` is what lets Flyway run in-process under the application role
(ADR-0011 §1). `CREATE EXTENSION` stays with the owner because it needs superuser, and the baseline
migration only *asserts* the extension's presence ([`schema-migrations.md`](schema-migrations.md) §5).

**This runs on an empty data directory only.** A volume that already holds a database skips
`initdb` entirely, so a developer who adds a role after first start must apply it by hand or
`make reset-db`. Under Kubernetes the equivalent is a `Job` with the same SQL, guarded by
`IF NOT EXISTS`, because a `StatefulSet`'s PVC survives `helm upgrade`.

### Redis

`requirepass`, one password, shared by the monolith and the Game Host. Redis ACLs would let the two
services hold different credentials with different key-prefix permissions, which is worth doing when
the two are separately trusted; they are both first-party services on an internal network, and the
Game Host already has broader capabilities than key access through the gRPC seam.

**No TLS between services.** `platform-operations.md` puts service mesh and internal TLS out of
scope; NFR-SEC-002's "TLS 1.2+ on all endpoints" is a client-facing requirement, and its extension
inward is a production concern (§7).

### MinIO / S3

Access key and secret, held by both services. The Game Host needs read access to fetch bundles; the
monolith needs write access to issue pre-signed upload URLs
([`../api-design/file-uploads.md`](../api-design/file-uploads.md)). A single credential does both
locally; the production escalation is two IAM roles, one read-only.

The bucket itself is **not** a secret and is therefore in
[`local-environment.md`](local-environment.md) §7.9, not here. It is created by the init step in §5 of
that document, using the same root credentials; the application's own credential needs only object
read/write on it.

**A pre-signed URL is itself a bearer credential** with the lifetime of
`turnbase.uploads.slot-ttl`. It appears in a `201` response body and therefore in any client that
logs responses, which is one of the specific reasons for §6's rule about response logging.

---

## 5. OAuth client secret

Registered with Google, stored as `TURNBASE_OAUTH_GOOGLE_CLIENT_SECRET`. The client **ID** is not a
secret and appears in the authorization redirect; the secret is used only in the server-side token
exchange and never leaves the monolith.

The redirect URI is registered per environment and must match exactly — `http://turnbase.localhost:8080/auth/callback`
locally. This is worth stating because `localhost` and `turnbase.localhost` are different URIs to
Google, and the platform origin is deliberately the latter
([`../game-frontend/game-asset-serving.md`](../game-frontend/game-asset-serving.md) §3), so the
obvious registration is the wrong one.

The OAuth `state` parameter carries the post-login redirect destination (`platform-views.md`
VW-OAUTHCOMP). It is signed with the JWT key and short-lived, because it is attacker-influenceable
input that comes back as a redirect target — VW-REDIR-006 and NFR-SEC-001 require the destination to
be validated as an internal path regardless, and signing it means a tampered `state` is rejected
before that check rather than relying on it.

---

## 6. What must never be written down

`platform-operations.md` FR-OBS-005 forbids passwords, tokens, session secrets and PII beyond user
IDs in logs. Four rules make that concrete, because the general statement is not actionable at a code
review:

1. **Never log a whole HTTP request or response body** on the auth endpoints. A "log the request for
   debugging" line on `/api/auth/login` logs plaintext passwords, and it is added by someone
   debugging a login problem — the exact moment the logging looks justified.
2. **Never log a `Set-Cookie` or `Authorization` header.** The header allow-list is explicit; a
   deny-list acquires a hole the first time a header is renamed.
3. **`toString()` on a configuration properties class must not print its own fields.** Spring logs
   bean state in several diagnostic paths, and a `@ConfigurationProperties` record holding a password
   will print it from a stack trace nobody wrote.
4. **A pre-signed URL is a credential** (§4) and is truncated at the query string in every log line.

`admin-tooling.md` NFR-CRED-001 already requires this for admin credentials specifically. The rules
above are the general form; the admin credential is not special.

**Secrets in metrics and traces, too.** OpenTelemetry's JDBC and HTTP instrumentation captures
connection strings and URLs by default, and a JDBC URL commonly carries `?password=`. The exporter is
configured to drop `db.connection_string` and to sanitize query strings on outbound HTTP spans.

---

## 7. Production escalation

Not built (ADR-0001 §4). Recorded so the local design is not shaped in a way that forecloses it:

| Concern | Local | Production |
|---|---|---|
| Secret storage | `.env` file, git-ignored | External Secrets Operator against a managed secret store, projected into the same `Secret` the chart already reads |
| JWT key rotation | Manual promote/retire against a file | The same three steps, scheduled; the key set moves to the secret store |
| Postgres credentials | Static password | Short-lived credentials issued per instance |
| Redis | `requirepass` | ACL per service, TLS |
| Internal TLS | None | mTLS, at which point NFR-SEC-002 extends inward |
| Admin API | Basic auth on a loopback-bound port | Unchanged; the port is the control (FR-ADM-001, NFR-SEC-001) |

**Nothing in the local design has to be undone to get there**, because every secret already arrives as
an environment variable projected from a `Secret` the Helm chart reads. What changes is what fills
that `Secret`.

The one place the MVP is *knowingly* below a production bar is the admin credential:
`admin-tooling.md` CON-002 makes it a static shared string with no rotation, and
[`../platform/data-model-catalog.md`](../platform/data-model-catalog.md) OQ-002 records the
consequence — `game_review.decided_by` identifies a credential, not a person, so the review audit
trail is only as good as there being exactly one operator.

---

## 8. Requirements traceability

| Requirement | Realized by |
|---|---|
| FR-CRED-001…005 (platform-operations) | §1–§6 |
| FR-SESS-001/003/004 | §3.5 `jti`, database-authoritative revocation |
| FR-SESS-010 | §3.4 |
| FR-AUTH-007 | §5 |
| FR-OBS-005 | §6 |
| FR-CICD-009 | §2 (GitHub Actions secrets) |
| FR-ADM-002, NFR-CRED-001 | §1, §6, §7 |
| NFR-SEC-002 | §4 (client-facing today; inward is §7) |
| ADR-0011 §1/§6 | §4 role split |
