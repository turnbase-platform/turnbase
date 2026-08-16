# Room Chat WebSocket Protocol

## Overview

This specification defines the STOMP-over-WebSocket wire format for in-room chat. It covers the `CHAT_MESSAGE` server→client event and the `SEND_CHAT_MESSAGE` client→server command for the room-wide channel and the team channel. Business rules governing chat (channel structure, spectator exclusion, no server-side history) are defined in [in-room-chat.md](../../requirements/in-room-chat.md).

## Related Documents

- [websocket.md](websocket.md) — base connection, authentication, and envelope
- [room-websocket.md](room-websocket.md) — room affinity, per-room serialization and versioning, authorization model
- [in-room-chat.md](../../requirements/in-room-chat.md) — channel management, messaging, and delivery requirements

---

## Destinations

| Destination | Direction | Authorized subscribers / senders | Purpose |
|---|---|---|---|
| `/topic/room.{roomId}.chat` | server→client | Room players only (not spectators) | Room-channel chat messages |
| `/topic/room.{roomId}.team.{teamId}` | server→client | Players assigned to that team | Team-channel chat messages |
| `/app/room.{roomId}.chat` | client→server | Room players only (not spectators) | Send a chat message |

These destinations complement the room lobby destinations defined in [room-websocket.md](room-websocket.md). Spectators may not subscribe to or send on chat destinations; the `SubscriptionInterceptor` rejects spectator subscriptions silently, and the inbound channel guard returns an error for spectator send attempts.

---

## Message Envelope and Versioning

Chat events use the `{ "type", "version", "payload" }` envelope shape of the room lobby stream
(defined in [room-websocket.md](room-websocket.md)), but **`version` is always `null` on a chat event
and chat never advances the room version counter.**

This is not an inconsistency to be tidied away. The room `version` is a gap-detection sequence: a
client that receives version *n+2* having last seen *n* knows it missed something and requests a
snapshot. That only works if every subscriber to the sequence receives every member of it. Chat does
not satisfy that: `/topic/room.{roomId}.chat` excludes spectators and
`/topic/room.{roomId}.team.{teamId}` reaches one team. If a chat message consumed a version, every
spectator would observe a permanent gap on every message sent in the room, and every off-team player
on every team message — each one triggering a `REQUEST_ROOM_STATE`, which is the most expensive
command in the protocol. An ordinary conversation in a spectated room would be a self-inflicted
resync storm.

**Chat needs no sequence of its own.** It has no ordering requirement against lobby events, no gap
semantics — FR-MSG-006 delivers once with no retry and no replay, so a missed message is *defined* as
lost rather than as a gap to repair — and `messageId` already handles duplicates. A second counter
would be state to maintain in service of a repair that must never happen.

Clients must therefore ignore `version` on `CHAT_MESSAGE` and must not update `localVersion` from it.

---

## Server→Client: `CHAT_MESSAGE`

Delivered on `/topic/room.{roomId}.chat` for room-channel messages, or on `/topic/room.{roomId}.team.{teamId}` for team-channel messages.

```json
{
  "type": "CHAT_MESSAGE",
  "version": null,
  "payload": {
    "messageId": "uuid",
    "channel": "ROOM | TEAM",
    "teamId": "uuid | null",
    "authorId": "uuid",
    "authorUsername": "string",
    "text": "string",
    "serverTimestamp": "2026-06-11T14:32:00.123Z"
  }
}
```

| Field | Description |
|---|---|
| `version` | Always `null`. Chat does not participate in room version sequencing — see *Message Envelope and Versioning*. |
| `messageId` | Server-generated UUID for deduplication. Clients should discard duplicates by `messageId`. |
| `channel` | `ROOM` for the room-wide channel; `TEAM` for the team-scoped channel. |
| `teamId` | Present when `channel == TEAM`; null otherwise. |
| `authorId` | Set by the server from the authenticated session. The client never supplies author identity (NFR-SEC-002 in in-room-chat.md). |
| `authorUsername` | Display name resolved server-side at send time. |
| `text` | Message body, at most 500 Unicode characters (FR-MSG-002 in in-room-chat.md). |
| `serverTimestamp` | ISO 8601 UTC instant assigned under the room lock. Monotonically increasing within a room, guaranteeing consistent cross-client sort order (FR-MSG-004). |

---

## Client→Server: `SEND_CHAT_MESSAGE`

```json
{
  "type": "SEND_CHAT_MESSAGE",
  "correlationId": "uuid",
  "payload": {
    "channel": "ROOM | TEAM",
    "text": "string"
  }
}
```

| Field | Description |
|---|---|
| `channel` | `ROOM` to post to the room-wide channel; `TEAM` to post to the sender's current team channel. |
| `text` | Message body. Validated server-side. |

For `channel == TEAM`, the sender's current team assignment is resolved server-side — no `teamId` is supplied by the client (NFR-SEC-001 in in-room-chat.md).

---

## Authorization

| Destination | Check | On failure |
|---|---|---|
| `/topic/room.{roomId}.chat` (subscribe) | Sender is a non-spectator player in the room | Silent drop |
| `/topic/room.{roomId}.team.{teamId}` (subscribe) | Sender is a player assigned to `teamId` | Silent drop |
| `/app/room.{roomId}.chat` (send) | Sender is a non-spectator player in the room | Error on `/user/queue/errors` |

Team channel subscription authorization prevents a player from reading another team's private chat by guessing a team ID. Team assignment is re-validated inside the handler under the room lock, matching the authoritative handler-level check pattern described in [room-websocket.md](room-websocket.md).

---

## Validation and Error Codes

Validation errors are returned on `/user/queue/errors` using the standard error envelope (defined in [room-websocket.md](room-websocket.md)):

| Code | Trigger |
|---|---|
| `SPECTATOR_CANNOT_CHAT` | Message sent by a spectator (FR-CHAN-004 in in-room-chat.md) |
| `MESSAGE_EMPTY` | `text` is empty or blank |
| `MESSAGE_TOO_LONG` | `text` exceeds 500 characters (FR-MSG-002) |
| `NO_TEAM_ASSIGNMENT` | `channel == TEAM` but sender has no team assignment |
| `TEAM_CHAT_NOT_AVAILABLE` | `channel == TEAM` but the game does not declare team support (FR-TEAM-001 in in-room-chat.md) |
| `RATE_LIMIT_EXCEEDED` | Chat frame dropped by the Tier 6 `chat` bucket ([rate-limiting.md](rate-limiting.md)) |

`text` is canonicalized (NFC, control and bidi characters rejected) and its 500-character limit is
measured in Unicode code points after normalization — see
[input-validation.md](input-validation.md). Chat is rate limited at **1 message/second, burst 5**
(Tier 6 `chat` bucket) and its frames are capped at 4 KB. Chat is the platform's only unpersisted
broadcast surface (FR-MSG-005 — no history), so a flood leaves no audit trail behind: bounding it at
the source is the only control that exists.

---

## Delivery Semantics

Chat messages are delivered once to all currently connected subscribers with no retry (FR-MSG-006 in in-room-chat.md). A message sent while a participant is temporarily disconnected is not queued or replayed on reconnect. Players who join or reconnect mid-session receive no prior messages (FR-MSG-005, FR-CHAN-003). There is no per-message acknowledgement; the client shows no delivery failure indicator.

---

## No History

The server does not persist chat messages. The `ROOM_STATE` snapshot (defined in [room-websocket.md](room-websocket.md)) does not include any chat history. This is in contrast to the game log (defined in game-contracts.md FR-LOG-004), which is persisted and replayed to reconnecting players.
