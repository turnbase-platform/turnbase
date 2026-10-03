# In-Room Chat Requirements

## Related API Specifications

- [room-chat-websocket.md](../specs/api-design/room-chat-websocket.md) — Chat WebSocket wire format: `CHAT_MESSAGE` event, `SEND_CHAT_MESSAGE` command, spectator exclusion enforcement
- [room-websocket.md](../specs/api-design/room-websocket.md) — Room affinity, versioning model, and authorization pattern shared with chat
- [rate-limiting.md](../specs/api-design/rate-limiting.md) — Tier 6 `chat` bucket: 1 message/second, burst 5. Chat is unpersisted (FR-MSG-005), so a flood leaves no audit trail — bounding it at the source is the only control there is
- [input-validation.md](../specs/api-design/input-validation.md) — `text` canonicalization; the 500-character limit (FR-MSG-002) is measured in Unicode code points after NFC

## Stakeholders

| Role | Description |
|------|-------------|
| Player | Authenticated room participant; can send and receive messages in available channels |
| Host | Player with room ownership; no additional chat-specific powers beyond those in game-rooms.md |
| Spectator | Room observer; excluded from all chat channels (no read, no write) |
| Game | Declares whether team support is enabled and provides team structure metadata |

---

## Functional Requirements

### Channel Management

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-CHAN-001 | Room channel always present | A room-wide chat channel exists for the entire lifetime of the room, across all states (Lobby, In Progress, post-game). | Must |
| FR-CHAN-002 | Team channel conditional | A team chat channel exists only when the game declares team support and the player has been assigned to a team. Every manifest declares at least one `teamTemplates` entry (FR-MANIFEST-002), so "declares team support" means a team can hold more than one player: the client offers the channel when some team's `configuredSize` is above 1 (`IMP-M8-10`). | Must |
| FR-CHAN-003 | Client-side chat log | Chat messages are not persisted on the server. Messages are delivered as events over WebSocket; the platform client maintains a local message log for the duration of the player's session in the room. No history is available to players who join or reconnect mid-session (see FR-MSG-005, FR-MSG-006). | Must |
| FR-CHAN-004 | Spectators excluded | Spectators have no access to any chat channel — they cannot read or write messages. | Must |

### Messaging

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-MSG-001 | Send message | A player can send a text message to their currently active write channel. | Must |
| FR-MSG-002 | Message content | Messages are Unicode text with a maximum length of 500 characters. Empty messages are rejected. | Must |
| FR-MSG-003 | Message display format | Each rendered message includes: a channel identifier tag (`[Room]` or `[Team]`), the author's username, and the message text. | Must |
| FR-MSG-004 | Unified chronological view | All messages from the room channel and the player's team channel are displayed in a single unified view, sorted ascending by server-assigned timestamp. | Must |
| FR-MSG-005 | No server-side history | The platform does not persist chat messages. Players who join or reconnect mid-session receive no prior messages. | Must |
| FR-MSG-006 | Fire-and-forget delivery | The server delivers each message once to all currently connected recipients with no retry. If a recipient is not connected at delivery time, the message is not queued or replayed. The client receives no per-message delivery confirmation and shows no failure indicator. Messages sent while a player is disconnected are not replayed on reconnect. | Must |

### Channel Switching

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-SWITCH-001 | Active write channel | A player writes to one channel at a time: either the room channel or their team channel (if available). | Must |
| FR-SWITCH-002 | Switch write channel | A player can switch their active write channel at any time. | Must |

### Team Chat

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-TEAM-001 | Team channel requires game support | The team channel is only instantiated when the game declares team support via its metadata. | Must |
| FR-TEAM-002 | Team-scoped delivery | Team messages are delivered only to players assigned to the same team. A player not yet assigned to a team cannot send or receive team messages. | Must |
| FR-TEAM-003 | Team assignment in lobby | Team membership is established in the lobby. Players are auto-assigned to a team on join; the host may reassign players at any time. Mid-game joining players are auto-assigned by the platform using the same spread algorithm as lobby join (game-rooms.md FR-TEAM-011); they gain team chat access immediately upon assignment. | Must |
| FR-TEAM-004 | Team chat availability | When available, team chat is accessible across all room states (Lobby, In Progress, post-game). | Must |

---

## Non-Functional Requirements

| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-PERF-001 | Performance | Message delivery latency from send to receipt by all connected recipients | < 300ms p95 end-to-end | Should |
| NFR-SEC-001 | Security | Team channel membership and message routing enforced server-side; client cannot self-assign to a team or spoof channel | No client-side trust | Must |
| NFR-SEC-002 | Security | Message author identity validated server-side on every message; no client-supplied author field trusted | No impersonation | Must |
| NFR-SEC-003 | Security | Message length enforced server-side; oversized messages rejected with an error | 500 char max | Must |

---

## Constraints

| ID | Description |
|----|-------------|
| CON-001 | All chat communication must use WebSockets — no polling |
| CON-002 | Backend: Java 21, Spring Boot 3.5+ |
| CON-003 | Frontend: React 19, TypeScript |
| CON-004 | Team structure metadata (team count, min/max size, assignment rules) is declared by the game; the platform treats it as opaque configuration |

---

## Out of Scope

- Direct messages between players outside of rooms
- Global or public chat channels outside of rooms
- Spectator participation in any chat channel
- Per-player muting or local message suppression
- Server-side message history, pagination, or search
- Message deletion or editing
- Content moderation beyond host kick (see game-rooms.md)
- Word/profanity filtering

---

## Open Questions

*All open questions resolved.*

- **OQ-001 (resolved)** — Mid-game joining players are auto-assigned by the platform to the team with the fewest current human players, respecting template `size.max` constraints (game-rooms.md FR-TEAM-011). They gain team chat access immediately.
- **OQ-002 (resolved)** — Team structure metadata is the `teamTemplates` array declared in the game manifest (game-development-experience.md FR-MANIFEST-002), structured as defined in game-rooms.md FR-TEAM section (`name`, `size.min`, `size.max`, `count.min`, `count.max`). The platform treats this as its authoritative source for team configuration.
