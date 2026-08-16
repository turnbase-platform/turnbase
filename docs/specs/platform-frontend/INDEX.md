# Platform Frontend

Design specifications for the **platform's own** React 19 / TypeScript application — the shell at the
platform origin that renders every view and hosts the game iframe.

Not to be confused with [game-frontend/](../game-frontend/INDEX.md), which covers how a *game's*
frontend is served and sandboxed. The two meet at exactly one seam: the iframe and the `postMessage`
relay across it.

## Scope

Application structure and stack choices; the auth-tier route gate; the STOMP client and its two very
different reconciliation contracts (dense room `version`, sparse game `sequence`); the iframe
embedding and message-relay trust boundary; alert-versus-notification rendering; and the two views
whose structure is not obvious from the requirements.

Out of scope: visual design and component implementation, which belong to
[`../../requirements/platform-ui-library.md`](../../requirements/platform-ui-library.md) and the
separately published component library.

## Files

| File | Topic |
|------|-------|
| [design-system.md](design-system.md) | Tokens, CSS strategy, component inventory, composition rules, accessibility baseline and the import boundary for the platform component library |
| [shell-architecture.md](shell-architecture.md) | Structure and stack, routing and auth tiers, the WebSocket client, the game-iframe trust boundary, the platform origin's Content-Security-Policy, notifications and alerts, room and results views, testing |

## Key Decisions

- **The shell is the only thing between untrusted game code and an authenticated WebSocket.** Every other decision follows from that, and the three inbound `postMessage` checks — origin equality, source identity, shape validation — are the platform's browser-side trust boundary.
- **The trusted game origin comes from the server**, computed once from the absolute `gameFrontendUrl` in `GAME_STARTED`. Never assembled client-side, never a build-time constant, never matched with `startsWith`.
- **`sandbox="allow-scripts"` without `allow-same-origin`.** Together they return the frame to its own origin and undo the sandbox completely.
- **Gap detection on the room stream, never on the game stream.** The room `version` is dense so a gap is real; the game `sequence` is deliberately sparse, and a client that snapshotted on a hole would re-enter the guest VM under the session lock once per hole, on every turn.
- **Subscribe before you sync.** Reversing the two opens a window in which a message is in neither the snapshot nor the buffer, and it is lost silently.
- **No client-side state store.** Room and game state are server-authoritative and arrive as events; a second copy in the browser is the divergence class the room `version` exists to prevent, relocated.
- **The route guard is UX, not security** (`platform-views.md` CON-002). It avoids rendering a page that will 401; it protects nothing.
- **One room route across three visual states.** The post-game results view is not a server state — the room is already in Lobby — so a separate route would unmount the iframe and destroy the results the player is reading.
