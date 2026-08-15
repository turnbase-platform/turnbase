# Game Frontend Serving, Origin & Sandbox

Implementation-level design for **how a game's frontend bundle becomes a running iframe**: the origin
it is served from, the URL scheme, the `sandbox` attributes, the Content-Security-Policy on both
sides of the frame boundary, and how the platform shell injects the FE GDK bootstrap.

This closes review blocker **GAME-B3** and security gap **API-5**
([mvp-readiness review](../../reviews/2026-07-02-mvp-readiness/INDEX.md)). The origin decision itself
is recorded as [**ADR-0007**](../../decisions/0007-game-frontend-separate-domain.md) — read that first
for the rationale; this spec is its realization.

Realizes:

- **Requirements:** `game-contracts.md` CON-002/CON-004/CON-006, NFR-SEC-004;
  `game-development-experience.md` FR-ASSET-001…009, CON-006.
- **Depends on:** [gdk-api/frontend-gdk-api.md](../gdk-api/frontend-gdk-api.md) §8 (origin
  validation) and §9 (bootstrap contract) — this spec is the other half of that contract.
- **Consumed by:** the platform-frontend shell spec (not yet written) and the bundle/upload-pipeline
  spec (not yet written). Both must conform to this document; neither may relax it.

---

## 1. Scope

**In scope:** the game serving origin and how it is configured; the routes and caching on that
origin; the server-rendered bootstrap document; the iframe embedding contract (sandbox, CSP,
postMessage rules on the *parent* side); the CSRF soundness argument; and the invariants that keep
the isolation intact.

**Out of scope:** the shell's UI and layout (frontend shell spec); how the ZIP is unpacked into the
artifact store (bundle/upload-pipeline spec); the postMessage message catalogue itself
(frontend-gdk-api.md §10); the game-session WebSocket protocol
([websocket.md](../api-design/websocket.md#game-session-protocol)).

---

## 2. Threat model — what the isolation is actually for

Two facts frame every decision below.

**The game iframe holds zero authority.** Player identity is attached server-side (FR-FA-002) and
every authorization decision lives on the platform's WebSocket, which the iframe cannot reach. An
attacker who fully controls the game frame gains exactly what that player already had: the ability
to send that player's own actions and see that player's own events. This is why asset *serving* can
be simple even though frame *isolation* must be strict.

**The one thing worth stealing is the session cookie's authority.** The cookie is
`httpOnly`/`Secure`/`SameSite=Strict` (`user-accounts.md` CON-004), so game JS cannot read it. But
`SameSite` is a **site** check, not an **origin** check: two hosts sharing a registrable domain are
same-site, and `SameSite=Strict` does not restrict same-site requests. Serving games from
`games.turnbase.io` while the platform sits on `turnbase.io` would therefore leave every game able to
fire fully-credentialed requests at the platform API — delete the player's account, kick players,
anything. **The serving origin is not a detail of the frontend; it is a load-bearing part of the
authentication model.**

That is the gap this spec closes. The `SameSite` defense is preserved by putting games on a
different **registrable domain**, and then made redundant twice over (§8).

---

## 3. Origin architecture

Two hostnames. The platform holds the session cookie; the games origin holds nothing.

| | Local (MVP — ADR-0001) | Production (deferred) |
|---|---|---|
| Platform | `http://turnbase.localhost:8080` | `https://turnbase.<domain>` |
| Games | `http://{gameId}.games.localhost:8080` | `https://{gameId}.games.<games-domain>` |

**The games domain MUST be a different registrable domain from the platform domain** — not merely a
different subdomain. In production this means a second domain (the `googleusercontent.com` /
`github.io` pattern). Locally, `turnbase.localhost` and `games.localhost` are different registrable
domains under the Public Suffix List's unknown-suffix rule (`localhost` is not in the PSL, so it is
treated as the effective TLD), which makes them cross-site.

**Why `.localhost` and not `/etc/hosts`:** Chrome and Firefox resolve every name under `.localhost`
to loopback with **zero configuration**, so `{uuid}.games.localhost` works out of the box. A UUID is
a valid DNS label (36 chars, hex and hyphens, ≤63). Safari does not do this and requires an
`/etc/hosts` entry per game — documented as a known local-dev limitation, not a design constraint.
`http://*.localhost` is a [secure context](https://w3c.github.io/webappsec-secure-contexts/), so
WebCrypto, WASM and service workers behave as they would under HTTPS.

**Production DNS/TLS cost, when it comes:** one wildcard record (`*.games.<games-domain>` → ingress)
and one wildcard certificate (Let's Encrypt issues these via DNS-01). Subdomains are never
registered individually; there is no per-game infrastructure action, ever.

### 3.1 Configuration — deploy-time, never build-time

```properties
turnbase.platform.origin              = http://turnbase.localhost:8080
turnbase.game-frontend.origin-template = http://{gameId}.games.localhost:8080
```

`{gameId}` is the only supported placeholder. **Setting the template to a constant** (e.g.
`http://games.localhost:8080`) collapses per-game origins into one shared games origin — every other
part of this spec is unchanged. Per-game vs. shared origin is therefore a **configuration value, not
an architecture**, and can be flipped without touching a contract. The MVP default is per-game.

The frontend **never constructs this URL**. The server resolves the template and hands the client an
absolute `gameFrontendUrl` (§7). The shell's trusted game origin is `new URL(gameFrontendUrl).origin`
— nothing else. This is the direct fix for **GRMP-F5**, whose failure mode was a build-time
`VITE_SANDBOX_ORIGIN` placeholder shipped into a production image: with the client performing no
origin construction, there is nothing to bake in and nothing to get wrong.

---

## 4. Serving

The **Platform Monolith** serves the games hostname as a virtual host, reading unpacked bundles from
the artifact store (MinIO locally; see [file-uploads.md](../api-design/file-uploads.md)). No new
deployable, no CDN — consistent with ADR-0001. A single request filter classifies every request by
`Host`:

| Host | May reach | Everything else |
|------|-----------|-----------------|
| platform origin | the platform API, the platform frontend | `/play/**` and `/g/**` → **404** |
| a game origin | `/play/{sessionId}` and `/g/{gameId}/{version}/**` | **404** — the API is *not* reachable on the games host |

Enforcing this in one filter is what makes the invariants of §9 auditable rather than aspirational.

### 4.1 Routes

| Route | Response | Cache-Control |
|-------|----------|---------------|
| `GET /play/{sessionId}` | Server-rendered bootstrap document (§5) | `no-store` |
| `GET /g/{gameId}/{version}/**` | Static bundle assets, verbatim from the artifact store | `public, max-age=31536000, immutable` |

Assets are immutable because the path is version-pinned. All game responses carry
`X-Content-Type-Options: nosniff` and the CSP of §6.

**Version pinning.** The game version is resolved once, when the session is created, and stored on
the session record. `/play/{sessionId}` serves *that* version. A game republished mid-session cannot
swap the code under a live game, and a reconnecting player is guaranteed the same bundle their
opponents are running.

**Validation.** `/play/{sessionId}` resolves the session → `(gameId, version)` and **cross-checks the
`gameId` against the one in the `Host` header**, 404ing on mismatch. This prevents game A's origin
from serving game B's code, which would silently defeat the per-game origin isolation.

### 4.2 Assets are unauthenticated, so not every archive entry may be published

The games origin receives **no cookies** — that is the entire point of §3, not an oversight — so the
asset handler cannot know who is asking. Anything reachable under `/g/{gameId}/{version}/` is
reachable by **anyone**, and the path is not even a secret: `gameId` is in the hostname and the
current version is a public catalog column (`game-catalog.md` FR-CAT-002), so both components are
derivable from a catalog page.

That is sound for JavaScript, CSS and sprites — **the secret is the game *state***, delivered over
the platform's WebSocket under two-layer authorization (NFR-SEC-002), and someone who fetches a
bundle acquires only the ability to render a game they cannot join.

**It is not sound for the whole archive.** §5's `<base href="/g/{gameId}/{version}/">` plus an
archive-relative `frontend.entryPoint` means the served tree must preserve archive-relative paths —
which reads as "unpack the archive and serve it". Do that literally and
`GET /g/{gameId}/{version}/backend/chess.jar` returns the **backend** to any anonymous caller. For
the MVP that is the platform's own game code; post-MVP it is every third-party developer's
proprietary JAR, handed to anyone who loads their game once.

**Publication is therefore filtered.** The unpack step writes the archive-relative tree, and the
asset route refuses a deny list rooted in what a browser can never legitimately need:

| Never published | Why |
|---|---|
| `manifest.json` | Platform metadata; already served through the catalog API in the form clients should read |
| `backend.path` (the value from the manifest) | The backend artifact. Fetched by the Game Host from the artifact store, never over HTTP |
| `*.jar`, `*.war`, `*.class` anywhere in the tree | The deny list must not depend on the developer declaring the path correctly |
| `infoDoc` | Rendered through the catalog's sanitizing Markdown path (`FR-GDET-004`), not served raw |

A deny list is the conservative shape here rather than the right one, and the difference is worth
stating: the correct model is an **allow list** rooted at a manifest-declared `frontend.root`, so
publication is opt-in and a new backend artifact type cannot be published by default. That needs a
manifest field, which makes it a bundle-format change —
[`../manifest/bundle-format.md`](../manifest/bundle-format.md) §5.2 carries it, together with
OQ-003 below.

Combined with ADR-0006 (official games only for the MVP), the residual private-bundle exposure is
theoretical today and cheap to harden later (§12, OQ-002) without changing any contract here.

---

## 5. The bootstrap document

`frontend-gdk-api.md` §9 requires `window.__TURNBASE__` to exist **before the game's JS executes**,
and §8 requires the trusted parent origin to come from the shell rather than from message traffic.
The parent cannot script into a cross-origin frame, so the document must arrive from the server with
the bootstrap already in it. That is the only reason this route is server-rendered.

```html
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <base href="/g/{gameId}/{version}/">
    <script nonce="{nonce}">
      window.__TURNBASE__ = { parentOrigin: "{platformOrigin}", sessionId: "{sessionId}" };
    </script>
  </head>
  <body>
    <script type="module" src="{manifest.frontend.entryPoint}"></script>
  </body>
</html>
```

- **`parentOrigin` comes from server configuration.** Never from a query parameter, never from the
  build, never from a header the client controls. Everything in `frontend-gdk-api.md` §8 rests on
  this value being trustworthy; a game that could choose its own `parentOrigin` could accept messages
  from anyone.
- **`<base href>` is load-bearing.** The document is served from `/play/{sessionId}`, but the bundle
  lives under `/g/{gameId}/{version}/`. Without a base URL, every relative reference inside the
  game's build output (`./assets/atlas.png`) would resolve against `/play/` and 404. The base tag
  points relative resolution at the bundle root, which is also why CSP uses `base-uri 'self'` rather
  than `'none'`.
- **`nonce`** is fresh per response and appears in `script-src`. It is the only way inline script runs
  in this document.
- The body is left empty; games mount into `document.body`. The manifest declares a single JS entry
  point (FR-MANIFEST-009), so **stylesheets must be imported from JS** (or injected at runtime —
  `style-src` permits inline styles). If bundles later need to declare stylesheets, that is a
  manifest change and belongs to the bundle spec.

The **test harness** satisfies this same contract by serving an equivalent document from its own
local origin, or via the `parentOrigin` constructor override already defined in
`frontend-gdk-api.md` §3.

---

## 6. The iframe

### 6.1 Embedding attributes (platform shell)

```html
<iframe src="{gameFrontendUrl}"
        sandbox="allow-scripts allow-same-origin"
        allow=""
        referrerpolicy="no-referrer"></iframe>
```

**`allow-scripts allow-same-origin` is safe here — and only here.** The well-known footgun is
granting both to a *same-origin* frame, which lets the frame reach into its embedder and remove its
own sandbox. This frame is cross-origin to the parent by construction (§3), so the pair grants the
game a real origin of its own — its per-game origin — and nothing more. That real origin is what lets
the game use `localStorage`/`IndexedDB` (which most engines touch, and which throws `SecurityError`
in an opaque origin) and what makes `event.origin` an exact, checkable value on both sides of the
frame boundary.

Nothing else is granted. In particular **not** `allow-top-navigation` (cannot navigate the platform
away), **not** `allow-popups`, **not** `allow-forms`, **not** `allow-modals`, **not**
`allow-downloads`. `allow=""` grants no Permissions-Policy features: no camera, microphone,
geolocation, or fullscreen.

### 6.2 The parent's half of postMessage

`frontend-gdk-api.md` §8 specifies the *game's* side. The platform's side has never been written down;
it is specified here and is mandatory.

- **Outbound:** every message to the frame is posted with `targetOrigin = gameOrigin` — the exact
  origin derived from `gameFrontendUrl`. **Never `'*'`.**
- **Inbound:** a message is accepted only if `event.origin === gameOrigin` **and**
  `event.source === frameElement.contentWindow`. Anything else is dropped silently.

The exact-`targetOrigin` rule is not hygiene; it is the primary defense against exfiltration by
self-navigation. If a malicious game navigates its own frame to `evil.com`, the frame's origin
changes — and the parent's subsequent `postMessage` calls, addressed to `gameOrigin`, are **simply
not delivered**. The attack fails by construction, without relying on any CSP behavior.

### 6.3 The platform shell's own CSP

The shell document that embeds the frame MUST pin `frame-src` to the games origin:

```
frame-src http://*.games.localhost:8080;
```

This blocks the frame from navigating itself anywhere else at all, closing the exfiltration channel a
second time, in a second layer. (The rest of the shell's CSP belongs to the frontend shell spec.)

### 6.4 CSP on game responses

Sent on both routes of §4.1:

```
Content-Security-Policy:
  default-src   'none';
  script-src    'self' 'wasm-unsafe-eval' 'nonce-{nonce}';
  style-src     'self' 'unsafe-inline';
  img-src       'self' data: blob:;
  media-src     'self' data: blob:;
  font-src      'self' data:;
  connect-src   'self';
  worker-src    'self' blob:;
  frame-src     'none';
  form-action   'none';
  base-uri      'self';
  frame-ancestors {platformOrigin};
```

| Directive | Why |
|-----------|-----|
| `connect-src 'self'` | The game may re-read **its own already-shipped bundle** (sprite atlases, level JSON, i18n files — routine in engine builds) and nothing else. It cannot reach the platform API, cannot phone home, cannot exfiltrate. This is the operative reading of CON-004's "no direct network access": no *external* network access. With per-game origins, `'self'` is exactly that game's own bundle. |
| `'wasm-unsafe-eval'` | Pixi, Phaser and Unity/WASM builds do not run without it. Excluding it would make the platform hostile to the third-party developers it exists to attract, while buying nothing: WASM in a frame with `connect-src 'self'` and no credentials has nowhere to go. |
| `'unsafe-inline'` styles | CSS-in-JS injects `<style>` tags. Contained: the game origin holds no credentials and no platform DOM, so style injection there is an attack on the attacker's own frame. |
| `frame-ancestors` | Only the platform may frame a game. Prevents third-party sites embedding TurnBase games. |
| `form-action 'none'`, `frame-src 'none'` | No form-based exfiltration, no nested frames. |
| `base-uri 'self'` | Permits the `<base>` of §5 while confining it to the game's own origin. |

---

## 7. Session integration

The client receives the game's absolute URL from the server; it never assembles one. Two carriers,
both in [room-websocket.md](../api-design/room-websocket.md):

- **`GAME_STARTED`** — `payload.gameFrontendUrl`, alongside `sessionId`.
- **Room snapshot** (`ROOM_STATE`) — `gameFrontendUrl`, non-null exactly when `sessionId` is non-null
  (`state == IN_PROGRESS`), so a reconnecting or late-joining client can construct the frame without
  an extra round-trip.

The shell derives its trusted game origin from that URL and uses it for the checks in §6.2.

---

## 8. Why CSRF is impossible — three independent layers

`user-accounts.md` CON-004 nominates `SameSite=Strict` as the complete CSRF defense. Review gap
**API-5** observed that this is only sound if untrusted game JS never runs same-site with the cookie.
It now holds, and holds redundantly:

1. **`connect-src 'self'`** (§6.4 below) — the game cannot issue a request to the platform *at all*.
   The browser blocks it before it leaves the frame. Depends on nothing but CSP.
2. **Server-side `Origin` check** — the platform rejects any state-changing request (`POST`, `PUT`,
   `PATCH`, `DELETE`) whose `Origin` header is present and is not the platform origin. See
   [rest-conventions.md](../api-design/rest-conventions.md#origin-policy-and-csrf). Note this is
   *not* what CORS gives you: CORS default-deny blocks the attacker from **reading the response**,
   while the state-changing request still lands. An explicit server-side check is the actual defense.
3. **`SameSite=Strict`** — games are cross-site (§3), so the browser withholds the cookie.

Only layer 3 depends on how a browser computes "site" for a name outside the Public Suffix List.
Layers 1 and 2 do not, which is why they are here.

---

## 9. Invariants

These are the statements that get quietly violated a year later. They are requirements, not advice.

1. **The games domain serves game bundles and nothing else.** No platform content, no platform API,
   no health endpoints. Enforced by the `Host` filter of §4.
2. **No platform cookie is ever scoped to the games domain**, and the games origin **never** appears
   in a CORS allowlist, in STOMP's `setAllowedOrigins`, or in any server-side trust list.
3. **The sandbox is identical for every game — official, verified, or unverified.** There is **no
   trust-level branch** in the iframe configuration. GRMP's vulnerability (GRMP-F5) was a
   client-side `?? 'TRUSTED'` fallback that silently loaded untrusted code same-origin; the way to
   fail closed is to have no branch that can fail open. A game's badge affects catalog presentation,
   never its isolation.
4. **The game origin is deploy-time configuration.** It is never compiled into a frontend bundle and
   never derived from a client-supplied value.
5. **The parent never posts with `targetOrigin: '*'`** and never trusts a message on origin alone
   (§6.2).

---

## 10. Failure modes

| Situation | Behavior |
|-----------|----------|
| Session unknown / ended | `/play/{sessionId}` → 404. The shell shows a load error; the session is unaffected. |
| `gameId` in `Host` ≠ session's game | 404. Never serve game B's code from game A's origin. |
| Bundle asset missing from the artifact store | 404 for that asset. The game FE fails to load. |
| Iframe fails to load entirely | **The session is not terminated.** A client-side failure kills only that client's attach — the same principle the game-session protocol applies to a failed `resync`. Other players continue; the affected player may reload. |
| Browser without `.localhost` resolution (Safari) | Local-dev only. Documented `/etc/hosts` workaround, or set `origin-template` to a constant (§3.1). |

---

## 11. Requirements traceability

| Requirement | Realized by |
|-------------|-------------|
| FR-ASSET-001 (distinct registrable domain) | §3 |
| FR-ASSET-002 (per-game origin, template) | §3, §3.1 |
| FR-ASSET-003 (server-rendered bootstrap) | §5 |
| FR-ASSET-004 (sandbox attributes) | §6.1 |
| FR-ASSET-005 (CSP on game responses) | §6.4 |
| FR-ASSET-006 (uniform isolation, no trust branch) | §9.3 |
| FR-ASSET-007 (version pinning at session start) | §4.1 |
| FR-ASSET-008 (deploy-time origin, server-supplied URL) | §3.1, §7 |
| FR-ASSET-009 (host isolation of routes) | §4 |
| game-contracts CON-004 (sandboxed, no network, no cookies, no parent navigation) | §6.1, §6.4 |
| game-contracts CON-006 / GDE CON-006 (platform-controlled HTML shell) | §5 |
| game-contracts NFR-SEC-004 (postMessage origin validation) | §6.2 |
| FR-FEGDK-006 (FE GDK origin validation) | §5 (`parentOrigin` supply), frontend-gdk-api §8 |
| user-accounts CON-004 (SameSite CSRF model) | §8 |

---

## 12. Open questions

- **OQ-001 — Fullscreen.** `allow=""` grants no Permissions-Policy features, so a game cannot go
  fullscreen. Some games will want it. Adding `allow="fullscreen"` is safe (fullscreen is
  user-gesture gated) but is a UX decision for the shell spec.
- **OQ-002 — Private-bundle exposure.** Bundle assets are unauthenticated (§4.2). If genuinely
  private third-party bundles become a requirement post-MVP, the fix is a short-lived signed token on
  `/play/{sessionId}` plus signed asset URLs — additive, and it changes no contract in this spec.
- **OQ-003 — Manifest-declared stylesheets.** The manifest declares one JS entry point; CSS must be
  imported from JS. If real games need `<link>`ed stylesheets, the manifest gains a `frontend.styles`
  array and §5 emits them. Deferred to the bundle spec.
