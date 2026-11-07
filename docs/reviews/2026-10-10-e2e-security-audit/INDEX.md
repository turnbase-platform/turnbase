# End-to-End & Security Audit — 2026-10-10

A black-box run of the full local stack (`make up`, observability overlay included) immediately after
the Phase 1 build plan reached 105 of 105. It had two halves, run together:

- **End-to-end**, through real browsers: a team of Playwright drivers, **one browser context per
  user** (own cookie jar), exercising every route and the full play loop (lobby → game → results) for
  the anonymous, guest and registered tiers, plus wrong-user access, reloads, back/forward, stale
  state and multi-user races.
- **Security**, against auth, the REST surface, the STOMP WebSocket and the internal gRPC edge, with
  one question foremost: *does a caller who should be denied get denied at the edge, without being
  allowed to strain the backend first?*

It asks whether the platform is sound enough to start building the visual layer and real games on top
of. The DB held only seed data and was treated as disposable.

## Verdict

> **The play loop and the account surface work end to end for every tier. The security posture has
> two findings that must close before the platform is exposed beyond a single trusted operator, and a
> cold-start operational wedge that blocks the very first game after a boot.**
>
> Every route renders for every tier with no unintended `5xx` once the game host is warm. The game
> plays, spectators are filtered, outsiders get silence. But a registered user can upload a new
> version to **any** game — the Official reference game included (C1) — and an over-broad STOMP
> subscription can read **another user's** private queue (C2). Both were reproduced live. Neither is
> acceptable before the FE and third-party games are built on this surface.

All findings below were **reproduced against the running stack** unless marked *code-confirmed*. Each
one that needs work is owned by an `IMP-M10-*` item in
[`../../implementation/registry.md`](../../implementation/registry.md); the mapping is in the tables.

## How it was run

- **Stack:** `make up` on a clean `down -v`, images at the current submodule heads. Management ports
  (`8081`/`8082`) confirmed loopback-only; everything else via `http://turnbase.localhost:8080`.
- **E2E drivers:** Playwright over headless Chromium, each actor a separate `browser.newContext()`.
  A shared brief pinned the rules (register per-prefix users, flush rate buckets before minting, never
  mutate the repo). The game UI was driven inside its sandboxed `<iframe>`.
- **Gameplay:** `.claude/skills/run-turnbase/driver.mjs` (`game`, `drop`, `leave`) over real STOMP —
  alice and bob play, carol spectates, dave is an outsider who never joins.
- **Security probes:** throwaway Node/`curl` scripts in the session scratch directory — STOMP frames
  with hand-built destinations, `POST`s with forged headers, chunked bodies, NUL/control bytes, and a
  single benign gRPC `Heartbeat` to confirm reachability of the registry servlet through nginx.
- **Baseline:** `turnbase-frontend`'s existing suite, **52 of 52 green** on a clean run (the 6
  failures seen mid-audit were contention over shared seeded users — the suite is serial and assumes a
  sole actor; they cleared once the drivers were idle).

## Severity

- **Critical** — a cross-user or cross-tenant breach reproducible by an ordinary authenticated user.
- **High** — an auth/abuse control that can be bypassed, or an internal surface reachable from outside;
  or an operational defect that blocks the core loop.
- **Medium** — a behavioural defect, a `5xx` on hostile-but-legal input, or an information leak.
- **Low / Info** — hardening, polish, a defense-in-depth gap not independently exploitable, or a
  console-level nuisance.

## Findings

### Critical

| ID | Finding | Item | Evidence |
|---|---|---|---|
| AUD-01 | **Any registered user can upload a new version to any game.** `POST /api/games/{gameId}/versions` never checks ownership; a slot was created against the Official Tic-Tac-Toe from a non-owner session. The requirements scope all management to the owner (`game-catalog.md` FR-GAME-006/007/008), and an Official game is ownerless — so the public route must refuse every caller. Root cause was a **spec gap**: `rest-conventions.md`'s ownership predicate covered `/api/games/{id}` but not its version sub-resources, and `file-uploads.md` was silent on auth. Fixed under **IMP-GATE-96** (see below). | IMP-M10-01 | Live: non-owner `POST …/versions` → `201` + pre-signed URL against the Official game |
| AUD-02 | **An over-broad STOMP `SUBSCRIBE` reads another user's private queue.** The broker matches destinations with `AntPathMatcher`; a subscription to a wildcard/ancestor of `/queue/game-user{sessionId}` received frames addressed to a different user via `convertAndSendToUser`. Per-user queues must be bound to the subscribing principal only. | IMP-M10-02 | Live: user A subscribed a crafted destination and received a `send_to_player` effect meant for user B |

### High

| ID | Finding | Item | Evidence |
|---|---|---|---|
| AUD-03 | **An unauthorized room join writes permanent Redis keys before the membership check fails** — the join path claims/stamps Redis state ahead of the authorization decision, so a caller who is ultimately refused still strains and pollutes the store. Deny at the edge, before any write. | IMP-M10-03 | Live: repeated refused joins left residual keys in Redis |
| AUD-04 | **The login lockout can be bypassed by parallel requests.** The failure counter is read-modify-written non-atomically; N simultaneous bad logins each see a sub-threshold count, so more than the Tier-1 limit (5) land before the lockout trips. | IMP-M10-04 | Live: concurrent bad logins exceeded the 5-failure lockout |
| AUD-05 | **The rate limiter trusts a client `X-Forwarded-For`.** The client-IP derivation reads a forwardable header, so an attacker sets their own bucket key (evasion) or spoofs a victim's (shared-bucket denial). Only the trusted edge hop may set the IP. | IMP-M10-05 | Live: varying `X-Forwarded-For` moved requests between buckets |
| AUD-06 | **The internal gRPC registry is reachable through the public edge.** `GameHostRegistryService` shares the monolith's `:8080` HTTP listener and is unauthenticated at the app layer *because reachability is meant to be the control* (loopback/cluster-internal). The frontend nginx `default_server` proxies its path, so a benign `Heartbeat` from outside returned `grpc-status: 0`. The reachability assumption the spec relies on is broken. | IMP-M10-06 | Live: `POST` to the registry path via nginx → `grpc-status: 0` |
| AUD-07 | **A chunked request body bypasses the body-size limit.** The limit is enforced on `Content-Length`; a `Transfer-Encoding: chunked` body is not capped the same way. Edge-mitigated today but should be enforced in-app. | IMP-M10-07 | Code-confirmed; chunked `POST` not rejected at the documented limit |
| AUD-08 | **The Game Host wedges on its first Espresso context after a cold boot.** The first `START_GAME` after `make up` fails `NO_HOST_AVAILABLE` / `GAME_START_FAILED`; `docker compose restart gamehost` clears it and every subsequent game works. Blocks the core loop for the first game of every fresh stack. Known gotcha (STATUS session 163), still unfixed. | IMP-M10-08 | Live: first game after cold `up` failed; worked after a gamehost restart |

### Medium

| ID | Finding | Item | Evidence |
|---|---|---|---|
| AUD-09 | **A NUL byte in `?search` returns `500`.** `GET /api/games?search=a%00b` reaches a `LIKE` query and throws. Hostile-but-legal input should be rejected or sanitized, not `5xx`. | IMP-M10-09 | Live: `curl --path-as-is '…/api/games?search=a%00b'` → `500` |
| AUD-10 | **Login response time reveals whether a username exists.** The password hash runs only when the user is found, so a present vs. absent username is distinguishable by latency — an enumeration oracle. | IMP-M10-10 | Live: measurable timing split present/absent username |
| AUD-11 | **Friends, rooms and notification lists do not refresh live in some views.** A relationship or room-state change made by another actor is not reflected until a manual reload (SOC-01, GAME-04, SOC-02). *Rooms list excluded (IMP-GATE-98): FR-LIST-005 makes it explicit-refresh only.* | IMP-M10-11 | Live: two-context races left one client stale |
| AUD-12 | **Email change and account deletion require no re-authentication.** A hijacked session can change the email or delete the account outright; combined with the 30-day username/email change lockout, the damage is durable (AUTH-02, SEC-S-15). | IMP-M10-12 | Live: `PATCH`/`DELETE` on `/api/users/me` succeeded with session only |
| AUD-13 | **A send blocked by a recipient's privacy setting fails silently.** A friend request to a user who has disabled incoming requests (`social-friends.md` FR-SOC-021) returns success to the sender rather than the rejection the requirement demands; the sender believes it went through (SOC-03). | IMP-M10-13 | Live: request to a blocking user acked, never created |
| AUD-14 | **In-memory lock and limiter maps are unbounded.** Per-key entries (room locks, WS limiter buckets) accumulate without eviction — a slow memory leak under churn (SEC-S-08/09). | IMP-M10-14 | Code-confirmed: maps grow per distinct key, no eviction |
| AUD-15 | **Catalog/room search does not escape `LIKE` wildcards.** `%` and `_` in `?search` are interpreted, so a user can craft a match-everything or probe query against the listing. | IMP-M10-15 | Live: `?search=%` matched all rows |

### Low / Info

| ID | Finding | Item | Evidence / note |
|---|---|---|---|
| AUD-16 | **Denial copy misstates the reason.** A refused action shows a generic or misleading message rather than the real cause. *Not a spec defect:* `error-handling.md` leaves Problem Detail `detail` free-form by design, so this is an implementation/copy fix. | IMP-M10-16 | Live: observed on a refused room action |
| AUD-17 | **Unknown routes return HTTP `200` (soft 404).** The SPA serves its shell with a `200` for a non-existent path; the 404 *view* renders but the status is wrong for crawlers and clients. | IMP-M10-17 | Live: `GET /nope` → `200` |
| AUD-18 | **No security response headers, and nginx serves any `Host`.** The `default_server` answers unknown hosts, and responses carry none of the standard hardening headers outside the shell CSP. | IMP-M10-18 | Live: arbitrary `Host:` served; headers absent |
| AUD-19 | **The session cookie is not `Secure` / not `__Host-` prefixed.** Acceptable on the local `http` stack but must be set under TLS. | IMP-M10-19 | Code-confirmed |
| AUD-20 | **The actuator `loggers` write endpoint is exposed on the management port.** A write there changes log levels at runtime; it should be read-only or disabled. | IMP-M10-20 | Live on `:8081` loopback |
| AUD-21 | **The object store uses its root credential for the application.** The platform and the MinIO console share the root account; the app should use a scoped service credential. | IMP-M10-21 | Config-confirmed (dev compose) |
| AUD-22 | **The Espresso sandbox leans on the container boundary.** Guest isolation is sound in-process, but several of its guarantees are backstopped by the container rather than the JVM; worth documenting as a defense-in-depth dependency. | IMP-M10-22 | Note (see `espresso-spike-results.md`) |
| AUD-23 | **The SDK game frame `postMessage`s to a detached parent.** On *Return to lobby* / remount, the SDK posts to `window.parent` after the frame has no parent, logging an origin-mismatch warning on every game (same site as CA-10). | IMP-M10-23 | Live: console warning on every game |
| AUD-24 | **The anonymous session probe logs a `401` as a console error.** The shell's probe for an existing session logs an expected `401` as an error, polluting the console and the suite tripwire. | IMP-M10-24 | Live: `401` console error for anonymous visitor |

## Reproduced but no action needed

- **Join-by-code bypasses room visibility (SOC-05).** *Working as specified.* `room-rest-api.md`'s
  `reachable()` note states that a valid `inviteCode` relaxes the access predicate **on join**, and
  `game-rooms.md` FR-HOST-002 requires the invite link to work for every visibility type. A deliberate,
  documented decision — not a defect. (A suite assertion that pins the documented behaviour would be
  welcome but is not a remediation.)
- **STOMP `SEND` authorization (SEC-S-03).** Refuted live: the per-destination handlers enforce
  authorization on send; the interceptor-level check is defense-in-depth only and its absence is not
  independently exploitable.
- **Chat message over 500 chars.** The server rejects it correctly; only the client-side cap is
  missing, which is cosmetic and folded into the view-polish work, not a security issue.
- **Game-frame same-site model.** The exact-origin `postMessage` rule holds; the cross-site iframe is
  by construction (see `game-frontend/`), consistent with the `SameSite=Strict` design.

## IMP-GATE-96 — upload route ownership (opened and closed 2026-10-10)

AUD-01 was a specification defect, not merely a code bug. `rest-conventions.md`'s *Authorization and
Ownership* table stated `game.owner_user_id = principal` for `/api/games/{id}` mutations, but neither
that row nor `file-uploads.md` (the document an implementer of the upload route actually reads) said
the predicate governs the `…/versions`, `…/versions/{uploadId}` and `…/versions/{uploadId}/confirm`
sub-resources — two individually-correct documents with a gap between them, which is exactly what the
live upload against the Official game walked through.

**Fixed in the same session:**
- `file-uploads.md` gained an *Authorization* section: all three version routes are owner-scoped via
  the `rest-conventions.md` predicate, resolved before any slot is created; an Official (ownerless)
  game is refused on the public route and moves only through `admin-rest-api.md` §4.
- `rest-conventions.md`'s `/api/games/{id}` (mutate) row now names the version sub-resources explicitly
  and spells out the ownerless-Official consequence.

`IMP-M10-01` builds the enforcement from the corrected spec.

## Run-hygiene notes

- The stack was left running. The seed DB was used as scratch, as permitted.
- Test artifacts left behind for a follow-up decision (DB manipulation was permitted but not part of
  M10): stray version-upload slots (e.g. `9.9.9`, `PENDING`/`FAILED`, none activated) on the Official
  Tic-Tac-Toe from the AUD-01 repro, and the modified test account `au8rovgfic`. Clean at the next
  `down -v`; no production data exists.
- All security probes lived in the session scratch directory. One stray `probe.mjs` in the home directory
  created in error by an e2e driver was removed; the repo was verified clean.
