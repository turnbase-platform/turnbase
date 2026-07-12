# ADR-0007: Game frontends are served from a separate registrable domain

- **Status:** Accepted
- **Date:** 2026-07-12
- **Deciders:** Project owner
- **Source:** MVP Readiness Review 2026-07-02 — blocker GAME-B3, security gap API-5, GRMP lesson F5

## Context

No document said what origin a game's frontend bundle is served from — yet the FE GDK's entire
security model already depended on the answer (`frontend-gdk-api.md` §8 validates
`event.origin === parentOrigin`; §9 requires the shell to inject a bootstrap into the iframe before
the game's JS runs). The review flagged this as a blocker for the client half of the execution chain.

The review's suggested resolution was to serve games from `games.turnbase.io` with
`sandbox="allow-scripts allow-same-origin"`, reasoning that this is "safe because that origin holds
no credentials."

**That resolution is unsound.** `SameSite` — nominated by `user-accounts.md` CON-004 as the platform's
complete CSRF defense — is a **site** check, not an **origin** check. Two hosts sharing a registrable
domain are same-site, and `SameSite=Strict` does not restrict same-site requests. Serving games on a
subdomain of the platform domain would therefore leave **any game able to issue fully-credentialed
requests to the platform API** — delete the player's account, kick players, anything the player can
do. The origin a game is served from is not a frontend detail; it is load-bearing in the
authentication model.

The prototype (GRMP) shipped the adjacent bug twice: a client-side `?? 'TRUSTED'` fallback that
silently loaded untrusted game code same-origin, and a build-time `VITE_SANDBOX_ORIGIN` placeholder
baked into the production image.

## Decision

1. **Game frontends are served from a registrable domain distinct from the platform's** — not a
   subdomain. In production this means a second domain (the `googleusercontent.com` / `github.io`
   pattern). Locally, `turnbase.localhost` and `games.localhost` are distinct registrable domains
   under the Public Suffix List's unknown-suffix rule.
2. **One origin per game** — `{gameId}.games.<domain>` — produced from a **deploy-time** template.
   Setting the template to a constant collapses this to a single shared games origin with no contract
   change, so per-game vs. shared is a configuration value rather than an architecture.
3. **The client never constructs the game URL.** The server supplies an absolute `gameFrontendUrl`;
   the trusted game origin is `new URL(gameFrontendUrl).origin`. Nothing is baked into a frontend
   build.
4. **Isolation is identical for every game regardless of trust badge.** No trust-level branch exists
   in the iframe configuration, so no such branch can fail open.
5. **CSRF is defended in three independent layers**: the game's CSP (`connect-src 'self'` — the
   request cannot be made), a **server-side `Origin` check** on state-changing requests (CORS
   default-deny does *not* stop a CSRF write; it only blocks reading the response), and
   `SameSite=Strict`. Only the third depends on how a browser computes "site".

## Consequences

- **Positive:** the SameSite CSRF model becomes sound, and stays sound even if the site computation
  assumption is ever wrong. The GRMP-F5 bug class is eliminated by construction rather than by
  vigilance. Games get a real origin, so `localStorage` and WASM-based engines work — the platform
  stays attractive to the third-party developers it exists to serve. Per-game origins mean the return
  of untrusted third-party uploads post-MVP needs no re-architecture.
- **Cost (production only, deferred with ADR-0001):** a **second domain must be registered**, plus one
  wildcard DNS record and one wildcard TLS certificate. There is no per-game infrastructure action —
  subdomains are never registered individually.
- **Cost (local):** none in Chrome or Firefox, which resolve `*.localhost` to loopback with no
  configuration. **Safari** does not, and needs an `/etc/hosts` entry per game — a documented
  local-dev limitation, escapable by setting the origin template to a constant.
- **Constraint on future work:** the platform API may never be reachable on the games host; no
  platform cookie may ever be scoped to the games domain; and the games origin may never be added to
  a CORS allowlist or to STOMP's `setAllowedOrigins`.

## Affected documents

- `docs/specs/game-frontend/game-asset-serving.md` — the spec that realizes this ADR.
- `docs/requirements/game-contracts.md` — CON-004 restated as the origin/sandbox/CSP contract.
- `docs/requirements/game-development-experience.md` — FR-ASSET-001…009.
- `docs/specs/api-design/rest-conventions.md` — § Origin Policy and CSRF.
- `docs/specs/api-design/room-websocket.md` — `gameFrontendUrl` in `GAME_STARTED` and the room snapshot.
- `docs/specs/gdk-api/frontend-gdk-api.md` — §9 bootstrap contract, now satisfied.
- Future platform-frontend shell spec and bundle/upload-pipeline spec — both must conform.
