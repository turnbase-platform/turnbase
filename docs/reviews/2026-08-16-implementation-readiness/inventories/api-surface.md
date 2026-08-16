# TurnBase API Surface Inventory

Mechanical extraction from Phase 0 specification documents. Every entry verified by line number.

---

## Table 1 — REST Endpoints

| Method | Path | Purpose (≤8 words) | Auth tier | Request body type | Success status | Source |
|--------|------|-------------------|-----------|------------------|----------------|--------|
| POST | `/api/auth/login` | Create session, revoke prior | Public | `application/json` | 201 | rest-conventions.md:64 |
| POST | `/api/auth/guest` | Mint guest account and session | Public | `application/json` | 201 | rest-conventions.md:65 |
| POST | `/api/auth/logout` | Revoke session and close connections | Authenticated | — | 204 | rest-conventions.md:66 |
| GET | `/api/auth/session` | Return current principal or 401 | Authenticated | — | 200 | rest-conventions.md:67 |
| POST | `/api/games/{gameId}/versions` | Request upload slot for bundle | Authenticated | `application/json` | 201 | file-uploads.md:22 |
| POST | `/api/games/{gameId}/versions/{uploadId}/confirm` | Confirm upload, start validation | Authenticated | — | 202 | file-uploads.md:60 |
| GET | `/api/games/{gameId}/versions/{uploadId}` | Poll validation status | Authenticated | — | 200 | file-uploads.md:97 |
| GET | `/api/notifications/stream` | Server-sent events stream | Authenticated | — | 200 | sse-notifications.md:10 |

---

## Table 2 — STOMP/WebSocket Destinations

| Direction | Destination pattern | Message/payload type name | Purpose | Source |
|-----------|---------------------|--------------------------|---------|--------|
| server→client | `/topic/room.{roomId}` | `PLAYER_JOINED`, `PLAYER_LEFT`, `PLAYER_KICKED`, `PLAYER_ROLE_CHANGED`, `HOST_TRANSFERRED`, `ROOM_CLOSED`, `GAME_STARTED`, `GAME_ENDED`, `READINESS_CHANGED`, `TEAM_ADDED`, `TEAM_REMOVED`, `TEAM_RESIZED`, `PLAYER_REASSIGNED`, `PARAMETERS_CHANGED`, `PLAYER_DISCONNECTED`, `PLAYER_RECONNECTED`, `PLAYER_LOST` | All room lifecycle, membership, team, readiness, presence | room-websocket.md:55 |
| server→client | `/topic/room.{roomId}.chat` | `CHAT_MESSAGE` | Room-channel chat (players only) | room-websocket.md:56 |
| server→client | `/topic/room.{roomId}.team.{teamId}` | `CHAT_MESSAGE` | Team-channel chat (team players only) | room-websocket.md:57 |
| server→client | `/user/queue/room-state` | `ROOM_STATE` | Unicast room snapshot | room-websocket.md:58 |
| client→server | `/app/room.{roomId}.member` | `TOGGLE_READY`, `SWITCH_TO_SPECTATOR`, `SWITCH_TO_PLAYER`, `REQUEST_ROOM_STATE` | Member commands | room-websocket.md:59 |
| client→server | `/app/room.{roomId}.host` | `KICK_PLAYER`, `ADD_TEAM`, `REMOVE_TEAM`, `RESIZE_TEAM`, `REASSIGN_PLAYER`, `ADD_AI_PLAYER`, `CHANGE_PARAMETERS`, `START_GAME`, `TRANSFER_HOST` | Host commands | room-websocket.md:60 |
| client→server | `/app/room.{roomId}.chat` | `SEND_CHAT_MESSAGE` | Send chat message | room-chat-websocket.md:21 |
| server→client | `/topic/game.{sessionId}` | `GAME_SYNC`, `GAME_EVENT`, `GAME_LOG`, `GAME_PLAYER_JOINED`, `GAME_PLAYER_LEFT`, `GAME_OVER`, `SESSION_FAILED` | Session effects and lifecycle | websocket.md:49 |
| server→client | `/topic/game.{sessionId}.team.{teamId}` | `GAME_EVENT` | Team-scoped effects | websocket.md:50 |
| server→client | `/user/queue/game` | `GAME_SYNC`, `GAME_EVENT`, `send_to_player` effects | Unicast game state and player effects | websocket.md:51 |
| client→server | `/app/game.{sessionId}.action` | `SUBMIT_ACTION` | Player action submission | websocket.md:52 |
| client→server | `/app/game.{sessionId}.sync` | `REQUEST_GAME_SYNC` | Game sync (snapshot) request | websocket.md:53 |
| server→client | `/user/queue/errors` | `ERROR` | Per-user command errors, rejections | websocket.md:54 |

---

## Table 3 — WebSocket Close Codes and Connection-Level Error Signals

| Code | Name | When sent | Client expected reaction | Source |
|------|------|-----------|-------------------------|--------|
| — | `RATE_LIMIT_ABUSE` | Sustained rate-limit violation on STOMP connection | Connection closes; client backs off | room-websocket.md:682 |
| — | `TOO_MANY_CONNECTIONS` | >4 concurrent connections for one user | Connection closes; client tears down excess | room-websocket.md:682 |
| — | `RECONNECT_REQUIRED` | Owning pod is draining gracefully | Immediately re-run join flow; claim is released | room-websocket.md:686 |

---

## Table 4 — SSE Event Types

| Event name | Payload | Trigger | Source |
|------------|---------|---------|--------|
| `FRIEND_REQUEST` | `{"type":"FRIEND_REQUEST","notificationId":"uuid",...}` | Another user sent a friend request | sse-notifications.md:53 |
| `FRIEND_REQUEST_ACCEPTED` | `{"type":"FRIEND_REQUEST_ACCEPTED","notificationId":"uuid",...}` | A sent friend request was accepted | sse-notifications.md:54 |
| `FRIEND_REQUEST_DECLINED` | `{"type":"FRIEND_REQUEST_DECLINED","notificationId":"uuid",...}` | A sent friend request was declined | sse-notifications.md:55 |
| `FRIEND_ADDED` | `{"type":"FRIEND_ADDED","notificationId":"uuid",...}` | Confirmation to the acceptor | sse-notifications.md:56 |
| `ROOM_INVITATION` | `{"type":"ROOM_INVITATION","notificationId":"uuid",...}` | Host invited this user to a room | sse-notifications.md:57 |
| `GAME_APPROVED` | `{"type":"GAME_APPROVED","notificationId":"uuid",...}` | Submitted game passed review | sse-notifications.md:58 |
| `GAME_REJECTED` | `{"type":"GAME_REJECTED","notificationId":"uuid",...}` | Submitted game was rejected | sse-notifications.md:59 |
| `BUNDLE_VALIDATION_COMPLETE` | `{"type":"BUNDLE_VALIDATION_COMPLETE","notificationId":"uuid",...}` | Async bundle validation finished | sse-notifications.md:60 |
| `INVITATION_ACCEPTED` | `{"type":"INVITATION_ACCEPTED",...}` | An invitation sent by this user was accepted | sse-notifications.md:66 |
| `INVITATION_DECLINED` | `{"type":"INVITATION_DECLINED",...}` | An invitation sent by this user was declined | sse-notifications.md:67 |
| `SESSION_DISPLACED` | `{"type":"SESSION_DISPLACED",...}` | Session invalidated by login from another device | sse-notifications.md:68 |

---

## Table 5 — gRPC Services and RPCs

| Service | RPC | Request msg | Response msg | Idempotent? (as stated) | Source |
|---------|-----|-------------|--------------|------------------------|--------|
| `GameHostService` | `CreateSession` | `CreateSessionRequest` | `CreateSessionResponse` | — | gamehost.proto:45 |
| `GameHostService` | `ProcessInput` | `ProcessInputRequest` | `ProcessInputResponse` | Yes (per-session replay of cached results) | gamehost.proto:50 |
| `GameHostService` | `Resync` | `ResyncRequest` | `ResyncResponse` | Yes (read-only, re-executed each time) | gamehost.proto:65 |
| `GameHostService` | `TerminateSession` | `TerminateSessionRequest` | `TerminateSessionResponse` | Yes (idempotent by design) | gamehost.proto:70 |
| `GameHostRegistryService` | `Register` | `RegisterRequest` | `RegisterResponse` | — | gamehost.proto:82 |
| `GameHostRegistryService` | `Heartbeat` | stream `HeartbeatRequest` | stream `HeartbeatResponse` | — | gamehost.proto:89 |
| `GameHostRegistryService` | `ReportContexts` | `ReportContextsRequest` | `ReportContextsResponse` | — | gamehost.proto:94 |
| `GameHostRegistryService` | `Deregister` | `DeregisterRequest` | `DeregisterResponse` | — | gamehost.proto:97 |

---

## Table 6 — Error Codes / Problem Types

### REST API Error Types (RFC 9457 Problem Details)

| Code | HTTP status | Meaning | Source |
|------|-------------|---------|--------|
| `validation-failed` | 400 | Bean Validation failures, malformed request body | error-handling.md:44 |
| `unauthenticated` | 401 | Missing, expired, or invalid session token | error-handling.md:45 |
| `forbidden` | 403 | Authenticated but insufficient permission | error-handling.md:46 |
| `not-found` | 404 | Resource does not exist | error-handling.md:47 |
| `conflict` | 409 | Unique constraint violations (username, email) | error-handling.md:48 |
| `gone` | 410 | Resource existed but is permanently unavailable | error-handling.md:49 |
| `payload-too-large` | 413 | Request body exceeds the 64 KB cap | error-handling.md:50 |
| `business-rule-violation` | 422 | Domain rule failures (version ordering, bundle validation) | error-handling.md:51 |
| `rate-limit-exceeded` | 429 | Too many requests | error-handling.md:52 |
| `internal-error` | 500 | Unexpected server failures | error-handling.md:53 |
| `service-unavailable` | 503 | Transient upstream failure | error-handling.md:54 |

### STOMP/WebSocket Error Codes (delivered on `/user/queue/errors`)

| Code | HTTP status | Meaning | Source |
|------|-------------|---------|--------|
| `NOT_HOST` | — | Host-only command sent by non-host | room-websocket.md:656 |
| `NOT_MEMBER` | — | Command sent by a non-member of the room | room-websocket.md:657 |
| `ROOM_NOT_LOBBY` | — | Lobby-only command sent while room is In Progress | room-websocket.md:658 |
| `TEAM_NOT_EMPTY` | — | `REMOVE_TEAM` on team with current members | room-websocket.md:659 |
| `TEAM_FULL` | — | Assignment to team already at configured capacity | room-websocket.md:660 |
| `OVER_CAPACITY` | — | Resize would reduce capacity below current member count | room-websocket.md:661 |
| `TEMPLATE_MAX_TEAMS` | — | `ADD_TEAM` would exceed `count.max` for template | room-websocket.md:662 |
| `SIZE_OUT_OF_RANGE` | — | `configuredSize` outside `[size.min, size.max]` | room-websocket.md:663 |
| `START_CONDITIONS_NOT_MET` | — | `START_GAME` when FR-TEAM-009 conditions not satisfied | room-websocket.md:664 |
| `TARGET_NOT_PLAYER` | — | `TRANSFER_HOST` targeting spectator or AI player | room-websocket.md:665 |
| `SPECTATOR_CAPACITY_FULL` | — | `SWITCH_TO_SPECTATOR` when spectator limit reached | room-websocket.md:666 |
| `SPECTATING_NOT_ENABLED` | — | `SWITCH_TO_SPECTATOR` when spectating disabled | room-websocket.md:667 |
| `PLAYER_NOT_FOUND` | — | Targeted `playerId` does not exist in room | room-websocket.md:668 |
| `AI_NOT_SUPPORTED` | — | `ADD_AI_PLAYER` when game does not support AI | room-websocket.md:669 |
| `KICKED` | — | Unicast notification to player removed by host | room-websocket.md:670 |
| `SLOT_RELEASED` | — | Reconnection lost race to grace expiry; reservation resolved | room-websocket.md:671 |
| `ROOM_UNAVAILABLE_RETRY` | — | Pod does not own room; client re-runs join flow | room-websocket.md:672 |
| `UNKNOWN_COMMAND` | — | Unrecognised `type` in command envelope | room-websocket.md:673 |
| `UNKNOWN_PARAMETER` | — | `CHANGE_PARAMETERS` with undeclared key | room-websocket.md:674 |
| `PARAMETER_TYPE_MISMATCH` | — | `CHANGE_PARAMETERS` value type mismatch | room-websocket.md:675 |
| `PARAMETER_OUT_OF_RANGE` | — | `CHANGE_PARAMETERS` value outside manifest bounds | room-websocket.md:676 |
| `VALIDATION_FAILED` | 400 | Command payload failed field validation | room-websocket.md:677 |
| `MESSAGE_TOO_LARGE` | — | Frame exceeds per-destination size cap | room-websocket.md:678 |
| `RATE_LIMIT_EXCEEDED` | 429 | Frame dropped by Tier 6 rate limiter | room-websocket.md:679 |
| `SPECTATOR_CANNOT_CHAT` | — | Message sent by spectator | room-chat-websocket.md:107 |
| `MESSAGE_EMPTY` | — | Chat `text` is empty or blank | room-chat-websocket.md:108 |
| `MESSAGE_TOO_LONG` | — | Chat `text` exceeds 500 characters | room-chat-websocket.md:109 |
| `NO_TEAM_ASSIGNMENT` | — | `channel == TEAM` but sender has no team | room-chat-websocket.md:110 |
| `TEAM_CHAT_NOT_AVAILABLE` | — | `channel == TEAM` but game does not support teams | room-chat-websocket.md:111 |

### gRPC Status Codes (infrastructure failures)

| Code | Meaning | Orchestration action | Source |
|------|---------|----------------------|--------|
| `UNAVAILABLE` | Host unreachable / crashed | Reassign and re-dispatch from queue | orchestration-gamehost-protocol.md:244 |
| `DEADLINE_EXCEEDED` | Call exceeded deadline | Treat as processing failure; apply retry-limit | orchestration-gamehost-protocol.md:245 |
| `RESOURCE_EXHAUSTED` | Message exceeded size ceiling | Fail the session | orchestration-gamehost-protocol.md:246 |
| `NOT_FOUND` | Session unknown, no Redis state | Permanently fail the session | orchestration-gamehost-protocol.md:247 |
| `FAILED_PRECONDITION` | Context could not be loaded | Fail the session | orchestration-gamehost-protocol.md:248 |

### gRPC In-Band Game Failures

| Code | Meaning | Source |
|------|---------|--------|
| `PROCESS_STATUS_OK` | Handler ran successfully or idempotent replay | gamehost.proto:288 |
| `PROCESS_STATUS_FAILED` | Game code failed; see `GameFailure` | gamehost.proto:291 |
| `GAME_FAILURE_KIND_HANDLER_EXCEPTION` | Game code threw exception | gamehost.proto:305 |
| `GAME_FAILURE_KIND_TIMEOUT` | Exceeded CPU/time budget | gamehost.proto:306 |
| `GAME_FAILURE_KIND_MALFORMED_OUTPUT` | Invalid effects/state from handler | gamehost.proto:307 |
| `GAME_FAILURE_KIND_STATE_TOO_LARGE` | Serialized state exceeds limit | gamehost.proto:308 |
| `GAME_FAILURE_KIND_CONTEXT_CRASH` | Context OOM/crash | gamehost.proto:309 |
| `GAME_FAILURE_KIND_CODE_LOAD_ERROR` | Entry class missing or not `TurnBaseGame` | gamehost.proto:310 |

---

## Collisions and Duplicates Observed

### 1. `RATE_LIMIT_EXCEEDED` — Three contexts, one code

**REST API (HTTP error):**
- Code: `rate-limit-exceeded`
- Type URI: `.../errors/rate-limit-exceeded`
- HTTP status: 429
- Source: error-handling.md:52

**STOMP error code (WebSocket, `/user/queue/errors`):**
- Code: `RATE_LIMIT_EXCEEDED`
- Context: Tier 6 rate limiter dropped frame
- Source: room-websocket.md:679

**STOMP error code (Chat, `/user/queue/errors`):**
- Code: `RATE_LIMIT_EXCEEDED`
- Context: Chat frame dropped by Tier 6 `chat` bucket
- Source: room-chat-websocket.md:112

**Observation:** Same conceptual error (rate limit), expressed as lowercase slug in REST (REST convention), uppercase constant in STOMP. No contradiction; contexts differ (HTTP vs WebSocket). Consolidation would be semantic only.

### 2. `VALIDATION_FAILED` — REST and STOMP

**REST API:**
- Code: `validation-failed`
- HTTP status: 400
- Meaning: Bean Validation failures, malformed request body
- Source: error-handling.md:44

**STOMP:**
- Code: `VALIDATION_FAILED`
- Meaning: Command payload failed field validation
- Source: room-websocket.md:677

**Observation:** Same semantic error in different transports (REST vs STOMP). Consistent naming (REST uses kebab-case, STOMP uses UPPER_CASE). No contradiction.

### 3. `MESSAGE_TOO_LARGE` — Two sources in STOMP

**Room WebSocket:**
- Code: `MESSAGE_TOO_LARGE`
- Meaning: Frame exceeds per-destination size cap
- Source: room-websocket.md:678

**Room Chat WebSocket:**
- Code: `MESSAGE_TOO_LARGE`
- Source: Not explicitly listed; mentioned indirectly in room-chat-websocket.md:115 ("frames are capped at 4 KB")

**Observation:** Same error code, likely same application in both contexts (room commands vs chat messages). No contradiction; both reference [input-validation.md](../../../specs/api-design/input-validation.md) for size limits.

---

## Summary

- **Table 1 (REST endpoints):** 8 rows
- **Table 2 (STOMP destinations):** 12 rows
- **Table 3 (WebSocket close codes):** 3 rows
- **Table 4 (SSE event types):** 11 rows
- **Table 5 (gRPC services/RPCs):** 8 rows
- **Table 6 (Error codes):** 50 rows
  - REST API: 11
  - STOMP/WebSocket: 24
  - gRPC status: 5
  - gRPC game failures: 8

**Collisions found:** 3 (all semantic, no contradictions)
1. `RATE_LIMIT_EXCEEDED` — REST/STOMP context split
2. `VALIDATION_FAILED` — REST/STOMP context split
3. `MESSAGE_TOO_LARGE` — Room and Chat STOMP contexts
