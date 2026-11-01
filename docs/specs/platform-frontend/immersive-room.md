# Platform Frontend — The Immersive Game Room

How the room screen behaves from the moment a game starts until the room goes back to the lobby.
Owner-specified 2026-10-27, after playing a game in the 600 px iframe the page layout gave it.
Realizes `platform-views.md` VW-RGAME-009…016 and amends VW-RGAME-001…008 and VW-RRESULT-001…005.

## 1. Intent

A game is the reason people are in the room, and a card game on a board needs the whole window.
While a game is shown the platform **gets out of the way**: the game frame fills the window and the
platform keeps one small, quiet presence — a round button — from which everything else is reachable.

**Non-goals.** The lobby is unchanged. No new server command, event or REST field: everything here is
presentation of state the room already carries. No change to the iframe's trust boundary
(`shell-architecture.md` §5): sandbox, origin checks and the relay are untouched.

## 2. Behaviour

**Scope of "game shown".** The `IN_PROGRESS` room, and the `LOBBY` room whose game is still shown
for its results (`FR-LIFE-003`). One component tree across both, as before (`shell-architecture.md`
§8): the iframe is never remounted by `GAME_ENDED`.

### 2.1 The window is the game

- The game frame fills the viewport (`100vw × 100dvh`). The navigation, the sky, the room header,
  the participant strip, the chat column and the page padding are **not rendered** (removal, not
  hiding; they leave the tab order too). The page does not scroll.
- The only platform control on screen is the **room dock** (§2.2). Two exceptions are transient
  and appear only when needed, centred at the top edge over the game: the "could not be loaded —
  retry" banner and the "connection lost — reconnecting" banner.
- Leaving the room (or the room ending) restores the normal shell.

### 2.2 The dock button

- A round button, bottom-left, 3rem, carrying the TurnBase mark, clear of the safe-area insets.
- At rest it is semitransparent so it does not compete with the game. On hover **and** keyboard
  focus it becomes opaque with a subtle animation (a lift and a soft ring). Under reduced motion
  the opacity change remains and the movement does not.
- When the connection is lost it carries a warning dot, so the state is visible with the panel shut.
- Its accessible name is "Room menu"; it is a toggle (`aria-expanded`).

### 2.3 The room panel

- Clicking the dock **smoothly expands the button into a panel** anchored at the same corner (the
  button's circle grows to the panel's rectangle; its content fades in once the box is large
  enough). Clicking the mark again, the close control, or `Escape` collapses it back the same way.
  The panel does not close on a click in the game — the game stays playable while it is open.
- Contents, top to bottom, minimal:
  1. **Room info**: game name; a state chip (*In progress* / *Match over*); visibility; spectators
     watching.
  2. **Participants** (VW-RGAME-002): each seat with its host, connection and spectator badges. For
     the host, per-participant **Transfer host** and **Kick** (VW-RGAME-004, 005).
  3. **Return to lobby**, when the match is over (VW-RRESULT-002), for every participant.
  4. **Chat card** (§2.4), for players.
  5. **Leave room** (VW-RGAME-003), last, with a confirmation: the first click turns the button
     into "Leave the room? — Stay / Leave". Nothing is sent until *Leave* is chosen.
- The panel scrolls inside itself when the window is short; it never exceeds the viewport.

### 2.4 Chat: docked and floating

- The chat card keeps its behaviour (channels, composer, FR-CHAN-004: players only). It gains an
  **Undock** control in its header.
- Undocking turns it into a **floating chat window**: a semitransparent rectangle over the game,
  with a title bar, the same log and composer, and a **Dock** (close) control. The title bar is the
  drag handle — pointer drag, and the arrow keys when it is focused. The window never leaves the
  viewport; it is re-clamped when the window is resized.
- **While the chat is floating it is not in the panel** — nothing stands in for it there. Docking
  puts it back. The floating window is independent of the panel: it stays when the panel is shut.
- The draft in the composer and the channel choice survive docking and undocking (the chat state
  is held above both views, not inside either).
- Spectators have no chat (`in-room-chat.md` FR-CHAN-004): they see no chat card and no Undock.

### 2.5 Layering and the game

The dock, the panel and the floating chat sit above the iframe and nothing else sits above them.
They never take focus from the game on their own (no autofocus on open; the chat composer takes
focus only when the user clicks into it).

## 3. Design

- **No `backdrop-filter`** (`design-system.md`): "semitransparent" is a translucent surface from the
  existing `tb-glass` tokens, not a blur.
- **Shell chrome.** `Shell` renders the nav and backdrop; the room, a descendant, must remove them.
  A small context in `shared/` (`useImmersive`) lets the room announce "the game is shown" for as
  long as it is mounted; `Shell` reads it. No store: the flag lives in `Shell`'s state and is set
  by an effect with a cleanup.
- **`GameFrame`** gains a `fill` mode; the default stays the 600 px frame for anything else.
- **Chat state** (`useChat`) moves from `ChatPanel` up to the room; `ChatView` becomes a
  presentational view of a `Chat` with three chromes: the lobby *card*, the panel's *bare* body and
  the *floating* window.
- **New units**, each with one job: `RoomDock` (button + expanding panel shell), `RoomPanel` (the
  contents), `FloatingChat` (window), `useDrag` (pointer/keyboard move, clamped). `RoomGame` composes them.
- Appearance: Light/Dark/Auto and the palette rules apply (colour literals only in `palette.ts`;
  spacing on the `--spacing-*` scale).

## 4. Testing

Component tests per unit (dock toggle and a11y, confirmation before leave, undock/dock moves the
chat and nothing else, drag clamps, host-only controls, spectators get no chat). The room's tests
assert the chrome is removed while a game is shown and restored after. A Playwright pass against
the compose stack checks the visuals in both appearances at desktop and phone width.
