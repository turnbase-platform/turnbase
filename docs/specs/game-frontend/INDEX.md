# Game Frontend Specifications

How a game's frontend bundle is served, isolated, and framed by the platform — the boundary between
trusted platform code and game code in the browser.

This is the client-side counterpart to [`../game-host/`](../game-host/INDEX.md), which covers the
same boundary on the server.

## Files

| File | Topic |
|------|-------|
| [game-asset-serving.md](game-asset-serving.md) | Game FE serving origin, URL scheme, iframe `sandbox` attributes, CSP on both sides of the frame, server-rendered FE GDK bootstrap document, CSRF soundness (closes review GAME-B3 and API-5) |

## Key Decisions

- Games are served from a **different registrable domain** than the platform — not a subdomain.
  `SameSite` is a *site* check, so a subdomain would leave every game able to make credentialed
  requests against the platform API. The serving origin is part of the authentication model.
- **One origin per game** — `{gameId}.games.<domain>` — resolved from a **deploy-time** template.
  Setting the template to a constant collapses this to a shared games origin, so per-game vs. shared
  is a config value, not an architecture.
- The client **never constructs the game URL**; the server supplies an absolute `gameFrontendUrl`
  (GRMP-F5: no build-time origin baking).
- `sandbox="allow-scripts allow-same-origin"` — safe only because the frame is cross-origin to the
  parent. Nothing else is granted.
- The **iframe holds zero authority**: identity is attached server-side and authorization lives on
  the WebSocket. Compromising the frame yields what the player already had.
- **Isolation is identical for every game regardless of trust badge.** No trust-level branch exists,
  so there is none to fail open (GRMP-F5).
- CSRF is blocked by three independent layers: `connect-src 'self'`, a server-side `Origin` check,
  and `SameSite=Strict`.
