# Platform Frontend — Shell Architecture

The React 19 / TypeScript application at the platform origin. Its two load-bearing responsibilities
are the WebSocket relay to the game iframe
([`../api-design/websocket.md`](../api-design/websocket.md) § *Platform-shell relay contract*) and
the iframe embedding contract
([`../game-frontend/game-asset-serving.md`](../game-frontend/game-asset-serving.md) §6). Everything
else is an ordinary single-page application, and this document spends its length on the parts that
are not.

Realizes `../../requirements/platform-views.md`, and consumes
[`../../requirements/platform-ui-library.md`](../../requirements/platform-ui-library.md) rather than
restating it.

---

## 1. The one-sentence description

**The shell is the only thing standing between untrusted game code and an authenticated WebSocket.**
Every other decision below follows from that.

---

## 2. Structure

```
src/
├── app/          routes, layouts, the auth-tier gate, the providers
├── features/     one directory per domain: auth, rooms, catalog, profile,
│                 friends, notifications, game
├── shared/       api client, WebSocket client, hooks, types
├── ui/           our own composed and swizzled components — usually near-empty
└── index.css     the three Astryx stylesheet imports, in cascade-layer order
```

Feature-first, not layer-first. A layer-first tree (`components/`, `hooks/`, `services/`) puts the
three files that change together for one feature in three directories, and every change becomes a
three-directory diff.

**Components come from Astryx** ([ADR-0013](../../decisions/0013-astryx-design-system.md)).
Application code imports them directly — `import {Button} from '@astryxdesign/core/Button'` — and
does **not** go through a local wrapper. A pass-through that "just wraps" a library component is how
a design system dies: it becomes a stale prop signature between the developer and the real
documentation. `className` is the supported override, and it appends rather than substitutes.

`ui/` holds only what Astryx does not ship, obtained by climbing
[`design-system.md`](design-system.md) §3's ladder — compose, then swizzle, then write. It is
expected to stay small, and `no-restricted-imports` keeps `features/` out of it in both directions.

### Stack

| Concern | Choice | Note |
|---|---|---|
| Build | Vite | CLAUDE.md |
| Routing | React Router | File-based routing buys little for ~15 routes |
| Server state | TanStack Query | Caching, invalidation and request dedup for the REST surface |
| Realtime | `@stomp/stompjs` | Not wrapped in Query — see §4 |
| Client state | React context + `useReducer` | There is no global client state worth a store; room and game state are server-owned |
| Forms | React Hook Form + Zod | Zod schemas mirror the server's validation, and are the client half of `input-validation.md` |
| Components | Astryx (`@astryxdesign/core`) | ADR-0013. Pre-built CSS — no Vite plugin, no PostCSS, no Babel config |

### The two providers

The shell mounts both, once, at the root — nothing else in the application does:

```tsx
<Theme theme={neutralTheme}>            {/* Astryx tokens; data-astryx-theme on <html> */}
  <LinkProvider component={Link}>       {/* react-router's Link */}
    …
  </LinkProvider>
</Theme>
```

`LinkProvider` is not optional decoration. Without it every Astryx `Link` — including the ones
components render internally — emits a plain `<a href>` and triggers a **full page reload**, which
drops the STOMP connection, the room subscription and every piece of in-memory session state. It
belongs in the shell because the shell is the only place that knows about the router.

**No Redux, no Zustand, no Jotai.** The state that matters is the room and the session, both of
which are authoritative on the server and arrive as events. A client store holding a second copy is
the same divergence class the room `version` exists to prevent, moved into the browser.

---

## 3. Auth tiers and routing

`platform-views.md` defines three tiers and a redirect table; the shell implements it as one route
guard, and there is one rule about it:

**The guard is UX, not security.** `CON-002` of `platform-views.md` says view-level access is backed
by server-side token validation and client-side hiding is supplemental. So the guard exists to avoid
rendering a page that will 401, never to protect anything.

| Situation | Behaviour | Source |
|---|---|---|
| Unauth hits an auth-required route | `/login?redirect=<path>` | VW-REDIR-002 |
| Guest hits a registered-only route | 403 page, "requires a registered account" | VW-REDIR-003 |
| Authenticated hits `/login` or `/register` | `/rooms` | VW-REDIR-001 |
| Any 401 from any request | Clear the cached principal, redirect to `/login?redirect=<current>` | VW-REDIR-007 |

**The `redirect` parameter is validated as an internal path before use** (`NFR-SEC-001`,
VW-REDIR-005/006). Concretely: it must start with a single `/` and not `//`, must not parse as an
absolute URL, and is resolved against the platform origin before navigation. `//evil.com` is a
protocol-relative URL that a naive "starts with /" check accepts, and it is the whole of this
vulnerability.

**Gated elements are removed from the DOM, never disabled** (`NFR-USAB-001`).

---

## 4. The WebSocket client

One STOMP connection per browser tab, at `/ws`, opened after the principal is known and reused for
every room and game subscription (`websocket.md`).

| Concern | Behaviour |
|---|---|
| Heartbeats | 10 s / 10 s, negotiated at `CONNECT`. The client must actually send them, or the server reads it as gone within ~20 s and opens a grace period on a live player |
| Reconnect | Exponential backoff with jitter, 1 s → 30 s. Jitter is not decoration: a rolling deploy disconnects every client at once, and un-jittered backoff reconnects them all in the same millisecond |
| Resubscribe | On reconnect the client re-subscribes and then re-syncs. It does **not** assume its subscriptions survived |
| Errors | `/user/queue/errors` is subscribed once, globally, and routed to the alert system |

### Room state: the `version` contract

Every room event carries a monotonic `version`. The client:

1. Applies an event with `version == local + 1`.
2. **Discards** an event with `version <= local` — a duplicate.
3. On `version > local + 1`, a gap: **requests a snapshot**, does not guess.

The room stream is dense — every room event reaches every subscriber — so a gap is real information.

### Game state: no gap detection, ever

The game stream is the opposite and the client must treat it so. `sequence` is an ordering and dedup
key **only**. A `send_to_player` addressed to another player consumes a sequence this client will
never see, and so does another team's `send_to_team`; holes are normal and carry no information.

**A client that requested a snapshot on a "missing" game sequence would re-enter the guest VM under
the session's single-flight lock, once per hole, on every turn** — a self-inflicted denial of service
that looks like careful engineering. Recovery on the game stream is triggered by *reconnection*,
never by a gap.

### The attach order is mandatory

```
1. learn sessionId          (GAME_STARTED, or ROOM_STATE for a room already In Progress)
2. SUBSCRIBE /topic/game.{sessionId}, /user/queue/game, and the team topic
   ── and buffer everything from this moment ──
3. SEND REQUEST_GAME_SYNC
4. on GAME_SYNC: discard buffered sequence <= asOfSequence, apply the rest in
   (sequence, index) order, then go live
```

Subscribing *after* the sync request opens a window in which a message is in neither the snapshot nor
the buffer, and it is lost silently. Steps 2 and 3 are not reorderable.

---

## 5. The game iframe — the trust boundary

This is the part of the shell that has security consequences.

```tsx
<iframe
  src={gameFrontendUrl}
  sandbox="allow-scripts allow-same-origin"
  allow=""
  referrerPolicy="no-referrer"
/>
```

| Rule | Why |
|---|---|
| `src` is the server-supplied **absolute** `gameFrontendUrl` from `GAME_STARTED` | The client never assembles it and never derives the game origin from a build-time constant |
| `trustedGameOrigin = new URL(gameFrontendUrl).origin`, computed once | The origin the server chose is the only one that is correct; ADR-0007's whole isolation argument rests on it |
| `sandbox="allow-scripts allow-same-origin"` — **normative value owned by [`../game-frontend/game-asset-serving.md`](../game-frontend/game-asset-serving.md) §6.1** | The well-known footgun is granting both to a *same-origin* frame, which lets it remove its own sandbox. This frame is cross-origin by construction (ADR-0007 puts game frontends on a separate **registrable domain**), so the pair grants the game a real origin of its own and nothing more. **`allow-scripts` alone would break the relay outright:** an opaque origin makes `event.origin` the string `"null"`, so the origin check below drops every message the game sends, and the game silently receives nothing. It also costs the game `localStorage` and `IndexedDB`. |
| No `allow-popups`, `allow-top-navigation`, `allow-modals`, `allow-forms` | A game has no legitimate need to navigate the platform away or open a window |

### Inbound `postMessage` — three checks, all mandatory

```ts
function onMessage(e: MessageEvent) {
  if (e.origin !== trustedGameOrigin) return;   // 1
  if (e.source !== iframeRef.current?.contentWindow) return;   // 2
  const msg = GameMessage.safeParse(e.data);    // 3
  if (!msg.success) return;
  relay(msg.data);
}
```

1. **Origin equality.** Never `startsWith`, never a regex, never `'*'`. `https://evil-turnbase.io`
   passes a `startsWith('https://turnbase')` check.
2. **Source identity.** Origin alone is insufficient: any frame or popup on the game origin can post
   to this window, and with per-game origins that includes *another game* the user has open in a
   different tab.
3. **Shape validation.** The payload is untrusted input from untrusted code and is parsed, not cast.

Outbound posts always target `trustedGameOrigin` explicitly. `postMessage(data, '*')` broadcasts game
state — including one player's private view — to whatever happens to be in the frame.

### The relay is thin, and stays thin

The shell translates between two message formats and does not interpret payloads:

| From game | To server |
|---|---|
| `{type: 'action', payload}` | `SEND /app/game.{sessionId}.action` |
| `{type: 'ready'}` | Triggers the shell to post the `init` context |

| From server | To game |
|---|---|
| `GAME_EVENT`, `GAME_SYNC` | `{type: 'game_event', payload}` |
| `GAME_PLAYER_JOINED/LEFT`, `GAME_OVER` | corresponding message |

**The shell never adds player identity to an outbound action.** `FR-FA-002` and `NFR-SEC-001` make
the acting player the server's determination from the STOMP principal; a client-supplied identity
field is ignored server-side, and adding one here would imply otherwise.

### Bootstrap

`window.__TURNBASE__` must exist before the game's JS runs
(`frontend-gdk-api.md` §9). The shell cannot script into a cross-origin frame, which is exactly why
`/play/{sessionId}` is server-rendered with the bootstrap already in it. **The shell's only
obligation is to not try** — no `contentWindow` access, no injected script, no `srcdoc`.

The ready handshake: the game posts `ready`, the shell responds with the `init` context. Until
`ready` arrives the shell buffers; a game that never sends it gets a visible timeout rather than a
blank frame.

---

## 6. Content-Security-Policy

The shell document is served from the platform origin, which holds the session cookie. This is the
policy [`../game-frontend/game-asset-serving.md`](../game-frontend/game-asset-serving.md) §6.3
delegates here; that document owns `frame-src` and this one owns everything else.

**Who emits it (`IMP-GATE-74`).** The Frontend container's nginx — the listener at the platform
origin ([`../deployment/local-environment.md`](../deployment/local-environment.md) §1) — with
`add_header ... always` on the shell document response. It is a template rendered at container start
because `frame-src`'s value is deployment configuration. The monolith does not serve the shell.

```
default-src 'self';
script-src 'self';
style-src 'self';
img-src 'self' data: https:;
font-src 'self';
connect-src 'self';
frame-src <owned by game-asset-serving.md §6.3 — derived at start, not written here>;
frame-ancestors 'none';
form-action 'self';
base-uri 'none';
object-src 'none';
```

Sent as a response header on the shell document, not as a `<meta>` tag: a header applies to the
response that carries it and cannot be displaced by injected markup earlier in the document.

| Directive | Why this value |
|---|---|
| `script-src 'self'` | No `'unsafe-inline'` and no `'unsafe-eval'`. Vite emits external modules in production, so neither is needed — and if a future dependency demands one, that is a dependency decision, not a CSP relaxation |
| `img-src ... https:` | Info-document images (`game-catalog.md` FR-GDET-004, [`../api-design/input-validation.md`](../api-design/input-validation.md)) come from arbitrary hosts. `data:` covers inline icons. This is the one deliberately wide directive, and it is wide for content that renders as an `<img>` and nothing else |
| `connect-src 'self'` | REST, STOMP and SSE are all same-origin. **The games origin is never added** — the shell talks to game frontends through `postMessage`, never over the network |
| `frame-src` | Owned by `game-asset-serving.md` §6.3, including how its value is derived. Pinned to the games origin, which blocks the frame from navigating itself off-origin and closes the exfiltration channel a second time |
| `frame-ancestors 'none'` | The platform is never embedded. This replaces `X-Frame-Options`, which is not sent |
| `base-uri 'none'` | An injected `<base>` retargets every relative URL in the document — including the script tags — which turns a single injection into full script control |
| `object-src 'none'` | Nothing on the platform uses a plugin element |

**No `nonce` and no hash allow-list**, because there is no inline script to permit. Adding a nonce
mechanism before there is anything to nonce creates the exact affordance — "put the nonce on it" —
that inline script bans exist to remove.

**The games origin has its own, stricter policy** (`../game-frontend/game-asset-serving.md` §6.4).
The two are separate documents for separate origins and must not be merged; the whole point of
ADR-0007 is that they are different security contexts.

**`report-uri` is deliberately absent for the MVP.** There is no collection endpoint and a
report-only header nobody reads is worse than none — it reads as monitored. When observability lands
([`../deployment/observability.md`](../deployment/observability.md)), a `report-to` group is the
natural addition.

---

## 7. Notifications and alerts

Two classes, two behaviours — `notifications-invitations.md` FR-ALERT-010 and
[`../api-design/sse-notifications.md`](../api-design/sse-notifications.md):

| Class | SSE event | Rendering | Persistence |
|---|---|---|---|
| **Alert** | `event: alert` | Toast, auto-dismiss, queued sequentially (FR-ALERT-003/004) | None; lost if the tab is closed, by design |
| **Notification** | `event: notification` | Bell badge + notification center | Server-side; unread count from the API |

One `EventSource` per tab, at `/api/notifications/stream`. On error the browser reconnects
automatically; the shell does not implement its own backoff for it.

**The unread badge reads the API, not the stream.** The stream is an accelerator and its delivery is
at-least-once at best — SSE has no acknowledgement — so a count maintained by incrementing on each
pushed event drifts. The count comes from the server, refreshed on panel open and on each pushed
notification.

`SESSION_DISPLACED` is an alert and is terminal: show it, then redirect to `/login`. The stream and
the WebSocket are both about to be closed by the server (`FR-SESS-010`).

---

## 8. Two views worth specifying

**The room view is one component across three states.** `platform-views.md` presents Lobby, In
Progress and Post-Game Results as three sections, but the third is not a server state at all — the
room is already `LOBBY` and the results view is a client-side overlay over a still-mounted iframe
(`FR-LIFE-003`). Implementing it as a third route would unmount the iframe and destroy the results
the player is reading.

So: one route, one mounted iframe, and an overlay. `GAME_ENDED` sets an overlay flag; **Return to
Lobby** clears it and unmounts.

**Entry enrols only members.** The room view's first call is `GET /api/rooms/{id}`. If `viewerRole` is
set it re-enters through the idempotent join; if it is `null` the view renders the join prompt and
`POST …/participants` is sent only from a button (`platform-views.md` *Room — Lobby*, Entry; a link
preview or prefetch must not take a seat).

**The reconnection card is global, not room-scoped.** `VW-ROOMS-005` and `FR-REJOIN-002` pin a card
to `/rooms` for as long as the player holds a reserved slot — which they see *while not in the room*.
It is driven by a field on the rooms list response, not by a WebSocket subscription to a room the
client is no longer attached to.

---

## 9. Testing

| Layer | Tool | Scope |
|---|---|---|
| Unit | Vitest + Testing Library | Component behaviour, hooks, the reducers |
| Contract | Vitest + MSW | The API client against fixtures generated from the OpenAPI document |
| Relay | Vitest with a fake `MessageEvent` | **Every rejection path of §5** — wrong origin, wrong source, malformed payload |

The third is small and non-negotiable. The relay's rejection paths are the platform's browser-side
trust boundary, they are three `if` statements, and a regression in any of them is invisible in
manual testing because the happy path is unaffected.

There is no browser-based e2e tier here: `platform-operations.md` FR-CICD-005 puts end-to-end
coverage on HTTP and WebSocket clients rather than a browser.

---

## 10. What is deliberately absent

- **No SSR, no Next.js.** Every meaningful view requires a session; the two that do not (catalog,
  profile) are not worth a second runtime.
- **No client-side state store.** §2.
- **No service worker or offline mode.** The platform is useless offline.
- **No i18n.** Out of scope in `platform-ui-library.md`.
- **No light theme.** `FR-THM-001`, and CON-005 rules out even `prefers-color-scheme`.
- **No route-level code splitting for the MVP.** The bundle is small; the game iframe is the heavy
  thing and it is already a separate document on a separate origin.

---

## 11. Requirements traceability

| Requirement | Realized by |
|---|---|
| `platform-views.md` VW-* | §3 routing and the auth gate; §8 |
| VW-REDIR-005/006, NFR-SEC-001 | §3 redirect validation |
| NFR-USAB-001 | §3 — removal, not disabling |
| `websocket.md` relay contract | §4, §5 |
| `game-asset-serving.md` §6 embedding | §5 iframe attributes |
| `frontend-gdk-api.md` §8/§9 | §5 origin checks and the bootstrap obligation |
| FR-ALERT-001…006, FR-NOTIF-001/002 | §7 |
| FR-LIFE-003, VW-RRESULT-* | §8 room view |
| FR-REJOIN-002, VW-ROOMS-005 | §8 reconnection card |
| `platform-ui-library.md` | §2 — consumed, never re-implemented |
