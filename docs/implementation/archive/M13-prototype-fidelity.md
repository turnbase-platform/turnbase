# Archive — M13 Prototype fidelity

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim by `IMP-M20-01`. Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M13-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M13-01 | Fidelity method and the shared presentation kit | docs, frontend | M12-11 | DONE |
| IMP-M13-02 | Shell: floating glass nav, bottom bar, page frame, transitions | frontend | M13-01 | DONE |
| IMP-M13-03 | Landing page and the quick tour | frontend | M13-02 | DONE |
| IMP-M13-04 | Auth views and join-by-code | frontend | M13-02 | DONE |
| IMP-M13-05 | Catalog cards and game detail | frontend | M13-02 | DONE |
| IMP-M13-06 | Rooms list and the room | frontend | M13-02 | DONE |
| IMP-M13-07 | Profile, friends and settings | frontend | M13-02 | DONE |
| IMP-M13-08 | Side-by-side acceptance and the suites | frontend, docs | M13-03…07 | DONE |

---

## M13 — Prototype fidelity

Opened 2026-10-12 by an amendment to [ADR-0017](../../decisions/0017-turnbase-visual-identity.md) (§5).
The owner ran the finished M12 build and rejected it: *"The FE should be exactly the same as you
showed me in the prototypes."* M12 had ported the look (tokens, theme, glass) but re-designed the
screens — a flat top bar for the floating nav, a stripped landing, a table for the catalog cards — and
was accepted on e2e and axe alone, which cannot see a layout.

**How M13 differs from M12 — read before claiming any item:**

- **The prototype is the specification of the screens.** Layout, copy, components, motion and
  navigation are reproduced as shown. A deviation is allowed only where the corpus forbids the
  prototype's behaviour or the backend has no such data, and it is listed in ADR-0017 §5 — never
  made silently.
- **Services still are not touched.** Each screen keeps its hook; the presentational component is
  rebuilt to the prototype's markup and wired to the hook's data.
- **Acceptance is side by side.** An item is `DONE` only when a screenshot of each of its screens —
  Light and Dark, desktop and 400 px — has been compared with the prototype's and the differences
  are the ADR-0017 §5 list. e2e and axe are necessary, not sufficient.
- **The prototype dock is not ported.**

### IMP-M13-01 — Fidelity method and the shared presentation kit

**Repo:** `turnbase`, `turnbase-frontend` · **Depends on:** IMP-M12-11

**Read first:**
- `docs/decisions/0017-turnbase-visual-identity.md`
- `docs/specs/platform-frontend/design-system.md`

**Done when:**
- **ADR.** ADR-0017 §5 records the fidelity rule, the reference screenshots' location and the list of
  prototype elements that have no backing data.
- **Kit.** `src/ui/` holds what every screen reuses: `Person`, `Chip`, `Cover`, `Row`/`Stack`, the page
  head, the full icon set and the pixel-art set, each with a test.

### IMP-M13-02 — Shell: floating glass nav, bottom bar, page frame, transitions

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M13-01

**Done when:**
- The floating glass navigation pill with sliding indicator, notification popover and avatar menu
  (Profile, Settings, Replay the tour, Sign out / Leave as guest); the mobile bottom bar; the
  `.tb-main` frame (wide in a room, bare on the landing); directional pane transitions between
  sections. Route guards and navigation tiers are unchanged.

### IMP-M13-03 — Landing page and the quick tour

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M13-02

**Done when:**
- The five-screen snap landing with its jump rail, floating pieces and table card, and the five-step
  quick tour (opened after registration and from the avatar menu), as in the prototype.

### IMP-M13-04 — Auth views and join-by-code

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M13-02

**Done when:**
- Login, register, OAuth completion and join-by-code match the prototype's card layout, art and copy;
  validation and the guest path behave as before.

### IMP-M13-05 — Catalog cards and game detail

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M13-02

**Done when:**
- The catalog is the prototype's card grid and the detail page its hero, rules and rooms panels. Every
  field `game-catalog.md` FR-CAT-002 requires is shown on the card.

### IMP-M13-06 — Rooms list and the room

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M13-02

**Done when:**
- The rooms list (rows with cover, code panel, invites panel where data exists) and the room (lobby
  with teams and settings, in-game frame, result) match the prototype.

### IMP-M13-07 — Profile, friends and settings

**Repo:** `turnbase-frontend` · **Depends on:** IMP-M13-02

**Done when:**
- Profile header, Stats and History tabs, friend cards and requests, and the settings tabs match the
  prototype.

### IMP-M13-08 — Side-by-side acceptance and the suites

**Repo:** `turnbase-frontend`, `turnbase` · **Depends on:** IMP-M13-03…07

**Done when:**
- Every screen has been compared with the prototype in both appearances at both widths; `make e2e`
  and the axe sweep pass; STATUS and both `CLAUDE.md` files name M13 as closed.
