# ADR-0002: WebSocket scaling via room affinity

- **Status:** Accepted
- **Date:** 2026-07-10
- **Deciders:** Project owner
- **Source:** MVP Readiness Review 2026-07-02 — blocker API-3, strategic decision #3

## Context

Two specs described incompatible WebSocket scaling architectures:

- `docs/specs/api-design/room-websocket.md` assumes **room affinity** — all connections for a
  room are handled by one instance.
- `docs/requirements/platform-operations.md` ("WebSocket Horizontal Scaling") assumes a
  **Redis pub/sub** model, routing effect deliveries across monolith instances by publishing to
  a channel keyed by player connection ID.

These cannot both be true. One model must be chosen and the other document amended.

## Decision

**Room affinity wins.** All WebSocket connections for a given room are pinned to a single
Platform Monolith instance (room/session affinity at the ingress, keyed by `roomId`). Effect and
event delivery for a room happen entirely within the instance that owns the room; there is **no
cross-instance Redis pub/sub fan-out** for connection delivery.

Redis remains in the architecture for **game-state persistence and crash recovery**, not for
routing WebSocket traffic between instances.

`platform-operations.md`'s "WebSocket Horizontal Scaling" section is rewritten to describe
room-affinity routing.

## Consequences

- **Positive:** in-instance ordering and consistency for a room; simpler effect delivery; no
  cross-pod race on effect ordering. Aligns cleanly with the single-node local MVP (ADR-0001) and
  is the correct model to carry into a future multi-instance deployment.
- **Negative:** requires an affinity-capable ingress (route by `roomId`) once more than one
  instance exists; a single room is bounded by one instance's capacity. Acceptable — rooms are
  small and bounded.
- Crash recovery still depends on Redis-persisted state (ADR-0001, GAME-B2); affinity does not
  remove that requirement.

## Affected documents

- `docs/requirements/platform-operations.md` — rewrite "WebSocket Horizontal Scaling" to
  room-affinity; remove the Redis pub/sub connection-routing description.
- `docs/specs/api-design/room-websocket.md` — already assumes room affinity; confirm alignment.
- Review INDEX — resolves API-3.
