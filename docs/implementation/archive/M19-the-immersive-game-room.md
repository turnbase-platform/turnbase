# Archive — M19 The immersive game room

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim by `IMP-M20-01`. Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M19-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M19-01 | The immersive game room: full-window game, room dock and panel, floating chat | frontend, docs | — | DONE |

---

## M19 — The immersive game room

Opened 2026-10-27 by the owner while playtesting 7 Wonders Duel on the platform: the iframe was a 600 px
strip inside the page layout and the game was barely playable. The design is
[`immersive-room.md`](../../specs/platform-frontend/immersive-room.md); it is presentation only — no server change.

### IMP-M19-01 — The immersive game room

**Repo:** `turnbase-frontend`, `turnbase` · **Depends on:** — (owner-specified; built on the 7WD worktree branch)

**Read first:** `immersive-room.md`; `platform-views.md` *Room — In Progress* and *Post-Game Results*;
`shell-architecture.md` §5 and §8; `design-system.md`; `in-room-chat.md` FR-CHAN-004.

**Done when:**
- While a game is shown the iframe fills the window and the shell's navigation, sky, room header and page
  padding are removed (VW-RGAME-009); the lobby is unchanged.
- The room dock and its expanding panel behave as `immersive-room.md` §2.2–2.3, including Leave Room with
  confirmation, the host's transfer/kick, and Return to lobby once the match is over (VW-RGAME-010…012).
- The chat can be undocked into a movable semitransparent window and docked again; while floating it is absent
  from the panel; the draft survives (VW-RGAME-013…016).
- Component and room tests, lint, typecheck and `npm test` green; the visuals checked in both appearances at
  desktop and phone width.

---
