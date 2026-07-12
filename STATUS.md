## Last Session Summary

**Date:** 2026-07-12 (session 6)

**Wrote the game-frontend serving/origin/sandbox spec** (STATUS priority #5) —
`docs/specs/game-frontend/game-asset-serving.md`, a new spec directory. **Closes GAME-B3**, the last
execution-chain blocker, **and API-5** with it. This is the browser-side counterpart to session 4's
Game Host spec: the same platform↔game trust boundary, drawn in the client.

**The review's own suggested resolution was unsound, and that is the headline.** It proposed serving
games from `games.turnbase.io` with `allow-same-origin`, "safe because that origin holds no
credentials." But **`SameSite` is a *site* check, not an *origin* check** — a subdomain is same-site
with the platform, and `SameSite=Strict` does not restrict same-site requests. Every uploaded game
would have been able to fire fully-credentialed requests at the platform API (delete account, kick
players). The fix: games are served from a **separate registrable domain**. The serving origin is
part of the *authentication* model, not a frontend detail.

**Design decisions recorded:**
1. **One origin per game** — `{gameId}.games.<domain>` — resolved from a **deploy-time** template
   (`turnbase.game-frontend.origin-template`). Collapsing the template to a constant gives a shared
   games origin, so per-game vs. shared is a **config value, not an architecture**. Locally,
   `*.localhost` resolves to loopback with zero config in Chrome/Firefox, so this costs nothing;
   in production it is one wildcard DNS record and one wildcard cert.
2. **`sandbox="allow-scripts allow-same-origin"`** — the pair is safe *only* because the frame is
   cross-origin to the parent (the classic footgun is granting both to same-origin content). It buys
   `localStorage` (most engines throw `SecurityError` without it) and exact `event.origin` checks on
   both sides. Nothing else granted: no top-navigation, popups, forms, modals, downloads, or
   Permissions-Policy features.
3. **CSP `default-src 'none'` / `connect-src 'self'`** — a game may re-read its own already-shipped
   bundle (sprite atlases, level JSON) and reach nothing else. Plus `'wasm-unsafe-eval'`, without
   which Pixi/Phaser/Unity builds simply do not run.
4. **The bootstrap document is server-rendered** at `/play/{sessionId}` on the game origin. The parent
   cannot script into a cross-origin frame, so `window.__TURNBASE__` must arrive *in* the document,
   ahead of the game's entry script. `parentOrigin` comes from server config — never a query param.
   A `<base href>` points relative asset resolution at the bundle root.
5. **The parent's half of postMessage**, never previously written down: post only with
   `targetOrigin = gameOrigin`, never `'*'`; accept only when origin **and** `event.source` match.
   This is also the primary anti-exfiltration defense — a game that navigates its frame to `evil.com`
   simply *stops receiving messages*, since the parent still addresses `gameOrigin`.
6. **CSRF now has three independent layers**: `connect-src 'self'` (the request cannot be made), a
   **server-side `Origin` check** (new — CORS default-deny does *not* stop a CSRF write; it only
   blocks reading the response), and `SameSite=Strict`. Only the third depends on PSL "site"
   semantics, which is why the other two exist.
7. **GRMP-F5 closed by construction:** the client never builds the game URL (the server supplies an
   absolute `gameFrontendUrl`), and **isolation is identical for every game regardless of trust
   badge** — there is no trust-level branch, hence none to fail open.

**The reasoning that made the rest cheap:** the game iframe holds **zero authority**. Identity is
attached server-side and all authorization lives on the WebSocket. Compromising the frame yields
exactly what that player already had — which is why asset serving needs no auth (unguessable UUID
paths) even though frame isolation must be strict.

**Files changed:**
- `docs/specs/game-frontend/{game-asset-serving.md,INDEX.md}` — **the spec** (new directory)
- `docs/specs/INDEX.md` — new subdirectory row
- `docs/requirements/game-contracts.md` — CON-004 rewritten from prose into the origin/sandbox/CSP
  contract; spec link
- `docs/requirements/game-development-experience.md` — new FR-ASSET-001…009 section; spec link
- `docs/specs/api-design/rest-conventions.md` — new § Origin Policy and CSRF (API-5)
- `docs/specs/api-design/room-websocket.md` — `gameFrontendUrl` in `GAME_STARTED` + room snapshot
- `docs/specs/gdk-api/frontend-gdk-api.md` — §9 "shell spec not yet written" hedge replaced with the
  real mechanism; parent-side origin check cross-referenced
- `docs/specs/api-design/INDEX.md`, `docs/reviews/2026-07-02-mvp-readiness/INDEX.md`, `STATUS.md`

---

## Next Priorities

Continue the review's action plan (`docs/reviews/2026-07-02-mvp-readiness/INDEX.md`):

1. **Owner decisions** — ✅ done (ADR-0001…0005, 2026-07-10).
2. **Espresso feasibility spike** (ADR-0005) — ✅ done (2026-07-11). Outcome: untrusted Java not
   isolable in-JVM on CE → **ADR-0006** scopes MVP to official-only Java. Game Host isolation for the
   MVP = interrupt timeouts + container memory limit (no adversarial in-JVM enforcement).
3. **Game Host internals spec** — ✅ done (2026-07-11, session 4). Espresso-in-hardened-container;
   `docs/specs/game-host/game-host-internals.md`. Closed GAME-I1/I2, GAME-B2, exec-half of GAME-B1;
   reconciled GAME-M4, GAME-I5, and the I/O-denial contradiction.
4. **Game-session WebSocket spec** — ✅ done (2026-07-11, session 5). `websocket.md` § Game Session
   Protocol. Closed **GAME-B1** (client half), **I4**, **I6**. Catch-up is by read-only `resync`
   (new game-contract input), not by an effect journal.
5. **Game FE serving origin / sandbox / CSP** — ✅ done (2026-07-12, session 6).
   `docs/specs/game-frontend/game-asset-serving.md`. Closed **GAME-B3** (the last execution-chain
   blocker) and **API-5**. **All 15 review blockers in the game-execution chain are now closed.**
6. **WS abuse controls (API-1/2)** — ← **next.** `rate-limiting.md` WS message tier (chat flood,
   room-lock starvation, and now `SUBMIT_ACTION`/`REQUEST_GAME_SYNC`, all reachable by guests) +
   guest-creation bucket. The game-session spec explicitly leaves its destinations unthrottled and
   flags it. Group with `input-validation.md` (API-6) — both are abuse-surface work, one session.
7. **New specs (rescoped local-first):** local deployment & infrastructure spec (Docker Desktop K8s +
   compose per ADR-0001), data-operations spec (Postgres/Redis local, accepted game-state loss window
   — OPS-4), secrets & config spec, `input-validation.md` (API-6).
8. **Existing-doc edit checklist cluster** (review §): game-rooms/reconnection grace timers as
   persisted deadlines (GRMP-F2/F3), platform-operations reconciliation sweep (GRMP-F1) +
   Dependabot/Trivy + frontend in FR-CICD-001, rest-conventions authz/IDOR, platform-ui-library
   additions. *(Two items already done: the `left` proto reason value and the `GAME_STARTED`
   separator fix, session 5.)*
9. **Then** the previously planned queue: game bundle format + upload pipeline (must unpack into the
   `/g/{gameId}/{version}/` layout `game-asset-serving.md` §4.1 serves), test harness,
   platform-frontend shell spec (must honor the `websocket.md` relay contract and the iframe
   embedding contract in `game-asset-serving.md` §6 — sandbox attrs, `frame-src`, exact-`targetOrigin`
   postMessage).

---

## Coverage Summary

| Document | Coverage |
|----------|----------|
| `user-accounts.md` | Registration, auth, sessions, account management, profiles, guests, per-section privacy settings, block-requests toggle |
| `game-rooms.md` | Room list, creation, joining, host management, teams, readiness, lifecycle, mid-game join assignment |
| `game-catalog.md` | Catalog listing, game detail, game management, profile games tab |
| `notifications-invitations.md` | Alerts, notification center, invitations, friend request notifications |
| `reconnection-flow.md` | Disconnect detection, grace period, re-entry, kick mechanics |
| `in-room-chat.md` | Room/team channels, messaging, delivery model, late-join team chat access |
| `per-game-statistics.md` | Session counting, game detail stats, profile stats |
| `platform-views.md` | All views, navigation, redirects, auth tier gating |
| `game-development-experience.md` | GDK, game packaging, upload pipeline, local dev workflow |
| `game-contracts.md` | Platform ↔ game BE/FE protocol, effect types, structured outcome, postMessage API |
| `platform-architecture.md` | Game execution infrastructure, Game Host, Orchestration Service, sandboxing, scaling |
| `game-history.md` | Per-session history recording, win condition labels, profile history tab, privacy, deletion pseudonymization |
| `social-friends.md` | Friendship model, request lifecycle, friend cap, discovery, visibility, guest exclusion, block-requests toggle |
| `platform-operations.md` | Service topology (monolith), availability, observability stack, CI/CD pipeline, data retention |
| `onboarding-wizard.md` | First-time wizard overlay, pane structure, localStorage suppression, landing page re-entry |
| `admin-tooling.md` | Internal admin API, game badge model (Official/Verified/Unverified), review queue, private game behaviour |

**Decisions:** `docs/decisions/` — ADR-0001 (local-first platform), ADR-0002 (WS room affinity),
ADR-0003 (availability), ADR-0004 (erasure pseudonymization), ADR-0005 (sandbox / Espresso spike),
ADR-0006 (game trust model — official-only Java for MVP), ADR-0007 (game FEs on a separate
registrable domain).

---

## Open Questions Remaining in Existing Docs

| Document | Open Question |
|----------|---------------|
| `reconnection-flow.md` | Game engine response set after "player lost" event — deferred to Game SDK contracts |
| `game-history.md` | OQ-002: Pagination reuse — shared UI component vs. API pattern deferred to implementation |
| `game-contracts.md` | OQ-001: Log color annotation syntax — deferred to GDK spec |
| `game-contracts.md` | OQ-002: AI/bot player interface — deferred to future spec |
| `game-contracts.md` | OQ-003: Platform-managed timer system — deferred to future spec |
| `websocket.md` | OQ-001: Resync cost under a mass reconnect (N resyncs serialize behind one session lock) — cache the per-viewer view against `lastAppliedSequence` if it becomes a hotspot |
| `websocket.md` | OQ-002: A game whose `onResync` returns an empty spectator view leaves spectators blank until the next `broadcast` — the test harness should warn |
| `admin-tooling.md` | OQ-001: Can a developer resubmit a rejected game, or is rejection terminal? |
| `admin-tooling.md` | OQ-002: Can an operator delist a Verified or Official game post-approval? |
| `game-asset-serving.md` | OQ-001: Fullscreen — `allow=""` grants no Permissions-Policy features; whether to add `allow="fullscreen"` is a shell-spec UX call |
| `game-asset-serving.md` | OQ-002: Private-bundle exposure — bundle assets are unauthenticated; a signed-token variant is additive if genuinely private third-party bundles become a requirement post-MVP |
| `game-asset-serving.md` | OQ-003: Manifest-declared stylesheets — CSS must currently be imported from JS; deferred to the bundle spec |
