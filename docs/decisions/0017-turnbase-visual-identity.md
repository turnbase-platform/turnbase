# ADR-0017: The platform takes a TurnBase visual identity on top of Astryx

- **Status:** Accepted
- **Date:** 2026-10-11
- **Deciders:** Project owner
- **Amends:** [ADR-0013](0013-astryx-design-system.md) §4 *The aesthetic changes, and that is
  accepted* — reversed. ADR-0013 §1–3 and §5 stand: Astryx still owns components, the compose →
  swizzle → write ladder still governs, and the inventory is still not transcribed here.
- **Amends:** `platform-ui-library.md` FR-TOK-001, FR-TOK-005, FR-TOK-007, FR-TOK-008, FR-THM-001,
  CON-004, CON-005 and the *Out of Scope* motion and theme-switching lines
- **Relates to:** [ADR-0007](0007-game-frontend-separate-domain.md) (the shell CSP is unchanged),
  [ADR-0012](0012-repo-strategy-polyrepo-submodules.md)
- **Executed by:** milestone **M12** in [`registry.md`](../implementation/registry.md)
  (`IMP-M12-01…11`)

## Context

ADR-0013 took Astryx's muted `theme-neutral` because "functional and minimalistic" was the brief and
because answering the neon questions (OQ-002, OQ-004) would have meant overriding the library on day
one. It also left the door open: *"A custom theme via `defineTheme` remains available later — a
theme is a set of CSS custom property overrides, so this is reversible without touching component
code."*

Phase 1 has since produced a working application whose look is the stock theme. On 2026-10-11 a
clickable prototype of the intended identity — a deep-space arcade with FTL touches — was built and
reviewed to approval as a private Claude Artifact (no repository file; the prototype was throwaway
and is not archived). The owner approved the look and asked for it to replace the stock theme across
every view, keeping the services and the BE integration as they are.

The prototype is an *evidence* of the look, not code to port. It ran on static data, injected its
theme with a runtime `<style>`, loaded its font from Google Fonts and used global CSS with raw
values. Four of those are incompatible with this repository's own rules, so this ADR also settles
how the look is delivered.

## Decision

**The look is delivered as a custom Astryx theme plus a small, tested `src/ui/` layer. Services,
reducers, sockets and API modules are not restyled and not rewritten.**

### 1. The identity

| | Decision |
|---|---|
| Direction | Deep-space arcade. Dark: near-black indigo with cyan, magenta and amber accents. Light ("starlight"): cool lavender-white with deeper accents of the same hues |
| Type | **Pixelify Sans** for the logo, display headings, big numbers and short labels only. **Figtree** for everything a person reads. Forms, tables, chat and rules never use the pixel face |
| Surfaces | Fake glass: tint, sheen, a cursor spotlight and a lit edge. **No `backdrop-filter`** — the cost ADR-0013 §4 removed stays removed |
| Radius | Container 18 px, control 12 px, avatar and overflow buttons full circles. Controls are 44 px tall |
| Motion | Cursor spotlight and tilt, a reactive starfield, directional page transitions. All of it honours `prefers-reduced-motion`, and none of it carries meaning |
| Appearance | Light, Dark and Auto, persisted in the browser |

### 2. Delivery

1. **A built theme, never runtime injection.** The shell CSP is `style-src 'self'`
   (`shell-architecture.md` §6), which blocks an injected `<style>`. The theme is a `defineTheme`
   source in `src/theme/`; `astryx theme build` compiles it to a static `.css` and `.js` that are
   **committed**, exactly as the proto is (`conventions.md` §5). A test fails when the committed
   output has drifted from the source. Components import the `__built` theme; no runtime style
   engine runs.
2. **Own tokens are plain CSS.** The `--tb-*` tokens (brand colours, glow, sheen, spotlight,
   pixel-art palette, motion dials) live in `src/theme/tokens.css` as `light-dark()` values. They are
   *additions* beside Astryx's, never redefinitions of an Astryx property (FR-THM-002 stands).
3. **Fonts are self-hosted.** `@fontsource/pixelify-sans` joins `@fontsource/figtree`, at exact pins
   and at only the weights used. `font-src 'self'` is not widened.
4. **Own CSS stays CSS Modules**, one per component, consuming `--spacing-*`, `--color-*`,
   `--radius-*` and `--tb-*`. The prototype's global stylesheet is not carried over.
5. **The raw-value lint rules keep their shape and gain one exemption.** `no-raw-color-*` (FR-TOK-008)
   exempts `src/theme/**` — the token definition file the rule was waiting for, which ADR-0013
   had removed because Astryx supplied every value. `no-raw-spacing-css` has **no** exemption; the
   prototype's off-grid lengths (10, 14 px) are rounded to the `--spacing-*` scale.

### 3. Structure

- **`src/ui/`** grows from near-empty to the shared presentation layer: the pointer-effect
  delegation, `Starfield`, `Logo`, the pixel-art and icon set, `Person` (initials avatar),
  `PillTabs`, and the list-query kit — `ScrollPanel`, `FilterPanel`, `FilterButton`, `SortControl`,
  `PageBar`. ADR-0013 §2's ladder still applies to *Astryx* components: `ui/` composes and, where
  Astryx ships nothing, writes; it does not wrap an Astryx component to rename it. The two import
  rules in `design-system.md` §4 stand — entered through `ui/index.ts` only, and `ui/` imports nothing
  from `features/`.
- **Each view is split into a hook and a presentational component.** The hook owns loading, paging,
  filter and sort state and returns plain data and callbacks; the component renders them. This is the
  separation `platform-ui-library.md` already states for lists ("they do not own network calls"),
  applied to the pages. It is also what makes the views testable without a network and what lets the
  identity change again without touching a request.
- **List queries follow `pagination-filtering-sorting.md`**: offset paging with a 1-based `page`, `size` ≤ 100,
  `sort=field,dir`, and filters server-side only. `PageBar` and `SortControl` are controlled
  components over those parameters; they never slice or sort a fetched page.

### 4. What the prototype showed that the platform does not have

Ported views follow the specification, not the prototype's sample data:

- **No presence.** `social-friends.md` puts online/offline indicators out of scope, so the Friends
  view is one list, not Online / In a game / Offline groups, and `Person` has no status dot.
- **No invented endpoints.** The prototype's "Invites" column in Rooms shows only what a real
  notification or API already carries; where none exists the column is not built.
- **The prototype dock is not product.** The session switcher and "sample data" labels are dropped;
  the Light / Dark / Auto control is kept and moves into the shell (§1).

## Consequences

### What gets easier

- One source for the identity: a view that needs a colour, a radius or a glow reads a token.
- Hooks make the views thin. A later redesign touches `ui/` and the components, not the data layer.
- `theme build` output is static CSS, so first paint carries the component overrides and the CSP stays
  as it is.

### What gets harder, or riskier

- **Custom theme over a Beta library.** Component overrides name Astryx's theming targets
  (`astryx theme targets`); an upgrade can rename one. Mitigation: the exact pins and
  `astryx upgrade --apply` stay, and the theme build is part of `npm run build`, so a missing target
  fails loudly instead of silently.
- **Contrast.** The neon-on-dark palette is exactly what OQ-003 worried about. The WCAG AA floor
  (`design-system.md` §6) is unchanged and is enforced: the axe sweep in the acceptance suite runs in
  both appearances, and a unit test computes the contrast of every text/background token pair.
- **Motion budget.** NFR-PERF-002 (60 fps) now applies to something real. The starfield is one
  canvas, paused when the tab is hidden and static under `prefers-reduced-motion`.
- **Two appearances double the visual surface** the acceptance suite covers.

### Cascade

| Document | Change |
|---|---|
| `platform-ui-library.md` | FR-TOK-001, 005, 007 amended or reinstated; FR-TOK-008 gains the theme-file exemption; FR-THM-001, CON-004, CON-005 and the *Out of Scope* lines amended; a banner points here |
| `design-system.md` | §2 stylesheets and providers, §4 layout of `ui/` and `theme/`, §5 tokens and the `--tb-*` prefix, §6 theme selection, §8 absent items |
| `shell-architecture.md` | Fonts (`font-src 'self'` unchanged; two families); the appearance control |
| `registry.md` | M12, `IMP-M12-01…11` |
| `CLAUDE.md` | Tech-stack *Design system* row |
| `turnbase-frontend/CLAUDE.md` | Theme build and the `src/ui/` / `src/theme/` layout |

### Why this is an ADR

It reverses the decision ADR-0013 §4 recorded as "accepted", and it overrides seven requirement IDs
that a reader would otherwise take as current. It also sets four rules (built theme, own tokens in
CSS, self-hosted fonts, the one lint exemption) that every later view has to follow.
