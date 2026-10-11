# The Platform Design System — Astryx integration

How the platform frontend consumes [Astryx](https://github.com/facebook/astryx), what we add on top,
and where the boundary between the two sits. Realizes
`../../requirements/platform-ui-library.md`.

**Astryx is the design system** ([ADR-0013](../../decisions/0013-astryx-design-system.md)) and the
**look is TurnBase's own** ([ADR-0017](../../decisions/0017-turnbase-visual-identity.md), which
reverses ADR-0013 §4). This document does not define components or Astryx's tokens — Astryx defines
those. It defines the *integration*: setup, the custom theme, the composition ladder, the rules that
remain ours, and the small set of decisions Astryx leaves to its consumer.

**Scope.** If the answer depends on a specific screen, it is not here — that is
[`shell-architecture.md`](shell-architecture.md)'s and `../../requirements/platform-views.md`'s.

> **Do not look up components here.** The inventory, props and tokens live in Astryx and are read
> with `npm run astryx -- component <Name>` or the `astryx` MCP server. A copy in this repository
> would be a snapshot that goes stale within a release — see §7.

---

## 1. Packages and versions

| Package | Role | Dependency type |
|---|---|---|
| `@astryxdesign/core` | Components, theme system, utilities | runtime |
| `@astryxdesign/theme-neutral` | The base the TurnBase theme extends (`defineTheme({extends})`) | runtime |
| `@fontsource/figtree`, `@fontsource/pixelify-sans` | Self-hosted typefaces (§2) | runtime |
| `@stylexjs/stylex` | Peer dependency of `core` | runtime |
| `@astryxdesign/cli` | Component docs, templates, swizzle, codemods | **dev** |

**Pin exact versions. No `^`, no `~`.** Astryx is Beta at `0.4.3`; a caret range on a pre-1.0
dependency accepts breaking changes by definition. Upgrades are deliberate and run through
`astryx upgrade --apply`, which ships codemods for its own breaking changes.

Not used: `@astryxdesign/lab` (unpublished), `@astryxdesign/charts` and `@astryxdesign/vega`
(canary-only, no stable release, and no v1 requirement needs a chart), `@astryxdesign/build` (only
required to compile StyleX from source, which we never do).

### Peer requirements

`react >= 19.0.0` and `react-dom >= 19.0.0`, which `CLAUDE.md` already mandates. Node 22 is what
Astryx's own CI targets and what `.nvmrc` pins.

---

## 2. Setup

Four CSS imports and two providers. **No Vite plugin, no PostCSS, no Babel config** — Astryx ships
pre-built CSS and JS, and the TurnBase theme is compiled ahead of time by the Astryx CLI.

### The stylesheets, in this order

```css
/* src/index.css */
@import '@astryxdesign/core/reset.css';        /* @layer reset */
@import '@astryxdesign/core/astryx.css';       /* @layer astryx-base  — component styles */
@import '@astryxdesign/theme-neutral/theme.css'; /* @layer astryx-theme — the base's token overrides */
@import './theme/turnbase.css';                  /* @layer astryx-theme — the TurnBase theme, built */
@import './theme/tokens.css';                    /* our own --tb-* tokens, plain CSS */
```

**The order is the cascade layer order and is not cosmetic.** Theme tokens must land after the
component styles that read them; reversing two of these produces a page that renders with Astryx's
built-in defaults and gives no error. The TurnBase theme comes after the base it extends so that it
wins; `tokens.css` adds properties and redefines none of Astryx's.

### The TurnBase theme is built, committed, and never injected at runtime

`src/theme/turnbase.theme.ts` is a `defineTheme` source (`extends: neutralTheme`) that sets the
palette as `[light, dark]` pairs, the radius scale, the shadows, the fonts and the component
overrides. `astryx theme build` compiles it to `turnbase.css`, `turnbase.js` and `turnbase.d.ts`,
which are **committed** and carry `__built: true`, so Astryx injects no `<style>` at runtime.

This is not a preference: the shell CSP is `style-src 'self'` (`shell-architecture.md` §6), and an
injected `<style>` is blocked. `npm run build` runs the theme build first, so an upgrade that renames
a theming target fails the build instead of silently dropping an override, and a unit test fails when
the committed output differs from a fresh build (drift).

### The providers

```tsx
import {Theme} from '@astryxdesign/core/theme';
import {LinkProvider} from '@astryxdesign/core/Link';
import {turnbaseTheme} from './theme/turnbase';
import {Link} from 'react-router';

<Theme theme={turnbaseTheme} mode={appearance}>
  <LinkProvider component={Link}>{children}</LinkProvider>
</Theme>
```

`LinkProvider` is the one that is easy to skip and expensive to skip. Without it every Astryx `Link`
and every component that renders one internally emits a plain `<a href>`, which triggers a **full
page reload** — dropping the STOMP connection, the room subscription and the in-memory session
state. It is mounted once, in the shell, and it is the reason the shell owns both providers rather
than each view importing what it needs.

### Two details that fail silently

- **`data-astryx-theme` must be on `<html>`.** Theme CSS is scoped to that attribute; without it the
  page renders with built-in defaults and looks *almost* right.
- **The theme names its fonts but does not load them.** Nothing in the stylesheets sets a document
  font. Self-host the `woff2` files via `@fontsource` — Figtree (400/600/700) for everything a person
  reads, Pixelify Sans (the weights used, no more) for the logo, display headings, big numbers and
  short labels (`platform-ui-library.md` CON-004 as amended). `shell-architecture.md` §6's CSP sets
  `font-src 'self'`, so a Google Fonts link would require widening a security directive for a
  hosting convenience.
- **`appearance` is `light | dark | system`** and is the `mode` prop above. The shell owns it: a
  small provider reads and writes `localStorage` (guarded with try/catch — a blocked store falls back
  to `system`), and the Light / Dark / Auto control lives in the shell (`shell-architecture.md` §2).
  It is never sent to the server.

---

## 3. The composition ladder

Everything the platform needs that Astryx does not ship is obtained by climbing this ladder in
order. **Stopping at the first rung that works is the rule**, not a preference.

| Rung | Mechanism | When |
|---|---|---|
| 1 | **Compose** existing components | Almost always. A `RoomCard` is a `Card` containing a `Stack` of `Text` and a `Button` |
| 2 | **`astryx swizzle <Component>`** — eject the source into our repo | The component is ~90% right and the last 10% is not reachable through props |
| 3 | **Write a new component** against Astryx tokens | Nothing close exists |

Rung 3 still consumes `--spacing-*`, `--color-*`, `--radius-*` and `--shadow-*`. A component that
introduces its own values is visually adjacent to the system rather than part of it, and the
difference shows up as two-pixel drift and slightly-wrong greys.

**Swizzling is a fork with a nice name.** A swizzled component stops receiving upstream fixes,
including accessibility ones, and `astryx upgrade` cannot codemod it. Rung 2 is legitimate and
should be recorded in the component's own file when used — one comment naming what could not be done
through props.

---

## 4. Where our code lives

```
turnbase-frontend/src/
├── theme/                   # the identity: turnbase.theme.ts + its built output, tokens.css (§2, §5)
├── ui/                      # the shared presentation layer: our own composed (rung 1) and written (rung 3) components
│   ├── index.ts             # the public entry point
│   └── <Component>/
│       ├── <Component>.tsx
│       └── <Component>.module.css
├── features/                # application code — screens, hooks, data access
│   └── <feature>/
│       ├── use<View>.ts     # the hook: loading, paging, filter and sort state → plain data + callbacks
│       └── <View>.tsx       # the presentational component: renders what the hook returns
└── index.css                # the stylesheet imports, §2
```

`ui/` holds what the identity needs and Astryx does not ship (ADR-0017 §3): pointer-effect
delegation, `Starfield`, `Logo`, the pixel-art and icon set, `PillTabs`, the directional `Pane`, and the
list-query kit (`ScrollPanel`, `FilterPanel`, `FilterButton`, `SortControl`, `PageBar`, `ListPage`), the single-purpose `CardPage` frame (sign-in, invite) and the titled `SectionCard` panel. It
is **not** a wrapper layer: application code imports `Button` from `@astryxdesign/core/Button`
directly. Wrapping every Astryx component in a pass-through of our own would re-create the
maintenance burden ADR-0013 exists to avoid, and it would put a stale prop signature between the
developer and the real documentation.

**Each view is a hook and a presentational component.** The hook owns the network-facing state (it
calls the existing API modules, reducers and sockets, unchanged) and returns plain data and
callbacks; the component takes them as props and renders. A presentational component imports no API
module, so it is testable with literals and the look can change without touching a request.

### The import boundary

Two `no-restricted-imports` rules, both retained from the pre-Astryx design:

```js
// eslint.config.js
'no-restricted-imports': ['error', {patterns: [
  {group: ['**/ui/*', '!**/ui'],
   message: 'Import from the ui entry point, not from inside it.'},
  {group: ['@/features/*'],           // scoped to ui/** via an override
   message: 'ui/ may not import from features/.'},
]}]
```

The second direction is the one that matters: **`ui/` may not import from `features/`.** A shared
component that reaches into application code is a screen with a generic name, and it breaks on its
second use.

**No page-level or screen-specific components in `ui/`.** No `RoomLobbyPanel`. Those live in
`features/`, composed from Astryx plus `ui/`.

---

## 5. Styling our own code

**CSS Modules, one `.module.css` per component, consuming Astryx tokens.** Vite supports them with
no plugin.

This survives ADR-0013 unchanged, because **Astryx has no styling lock-in**: it authors its own
styles with StyleX but ships them pre-built, and documents `className` override with "Tailwind, CSS
modules, or plain CSS". We never compile StyleX; it is a peer dependency of `core` and an
implementation detail of a package we consume.

`platform-ui-library.md` CON-003 excluded runtime CSS-in-JS and still does, for our code. The
alternatives lose for the same reasons as before: runtime CSS-in-JS delays first paint on a shell
that gates every view; vanilla-extract adds a Vite plugin for a type-safety win we do not need;
Tailwind would add a second scale competing with Astryx's tokens.

```css
/* RoomCard.module.css — composing, not restyling */
.meta {
  display: flex;
  gap: var(--spacing-2);
  color: var(--color-text-secondary);
}
```

**Overrides append, never substitute.** Astryx components take `className`; passing one adds to the
component's own classes rather than replacing them. Use it for layout concerns — a margin, a grid
placement — and not to redesign a control in place. A `Button` that no longer looks like a `Button`
should have been rung 2 or rung 3.

### Token names come from Astryx

`--spacing-1` is the 4px base unit, so `--spacing-4` is 16px. Radius is
`--radius-inner` / `--radius-element` / `--radius-container`; elevation is `--shadow-low` / `-med` /
`-high`; text is `--color-text-primary` / `-secondary`; surfaces are `--color-background-surface` /
`-card` / `-body`. **`astryx docs tokens` is the reference** — this paragraph is orientation, not a
list to code against.

### Our own tokens: `--tb-*`

Brand colours Astryx has no family for (the cyan / magenta / amber accents), the glow, sheen and
spotlight recipes, the pixel-art palette and the motion dials are `--tb-*` custom properties in
the theme source, as `light-dark()` values built from the `[light, dark]` pairs in
`src/theme/palette.ts`; the motion dials and other non-colour ones are in `src/theme/tokens.css`. They
are **additions beside Astryx's tokens, never redefinitions of one** (FR-THM-002), and they are the only parallel names the platform defines. Own
CSS reads `--spacing-*`, `--color-*`, `--radius-*`, `--shadow-*` and `--tb-*`, nothing else.

### Enforcement (FR-TOK-008)

Astryx supplies the tokens; nothing stops our own code from bypassing them with a literal. Local
ESLint rules close that gap. Colours are written once, in `src/theme/palette.ts`; the rules are
unchanged and no hand-written file is exempt (ADR-0017 §2.5).

| Rule | Forbids | Escape |
|---|---|---|
| `no-raw-color-css`, `no-raw-color-tsx` | Any hex, `rgb()`, `hsl()`, `oklch()` color literal in a `.css` or `.tsx` file | none — `palette.ts` is a `.ts` file outside the `.tsx` rule; the generated `turnbase.{css,js,d.ts}` build is ignored by lint |
| `no-raw-spacing-css` | A `px`/`rem` length on `padding`, `margin`, `gap`, or `inset` in a `.css` file | none |

**There is no inline disable**, and nothing outside `src/theme/palette.ts` may define a colour. Spacing has no exemption at all: a length that is off the
`--spacing-*` scale is rounded to it, because a view that needs a value the scale lacks has found a
design question, not a lint problem.

Both are local rules — no third-party package defines them. No `@astryxdesign/eslint-plugin` or
equivalent exists (checked against the npm registry, not assumed); NFR-DX-004's "the library ships an
ESLint plugin" is Astryx's own inventory obligation for *its* tokens and components, not a substitute
for policing raw values in *ours*.

The pre-Astryx design also enforced a third rule, `no-raw-font-size`. That one is dropped, not carried
forward: typography (`FR-TOK-002`) is fully Astryx-owned now, or comes from a rung-3 component's own
props against `--spacing-*`/type tokens — there is no first-party surface left where our code sets a
raw `font-size`.

---

## 6. What remains ours

Astryx supplies capability; three things it cannot decide for us.

### Accessibility floor

Astryx ships accessible components, which raises the baseline but does not discharge the obligation —
an accessible component can be composed into an inaccessible screen.

| Rule | Owner |
|---|---|
| **WCAG AA is a hard floor**: 4.5:1 body text, 3:1 large text and UI boundaries | Every screen |
| Colour is never the only carrier of meaning | Every screen |
| Every interactive element is keyboard-reachable with a visible focus ring | Astryx by default; ours not to remove |
| Composed components preserve label/description wiring (`<label for>`, `aria-describedby`, `aria-invalid`) | Rungs 2 and 3 |

The AA floor is the resolution of `platform-ui-library.md` OQ-003 and it survives both ADRs. ADR-0017
makes it harder to meet — neon accents on near-black are where OQ-002 worried about contrast — so it
is **enforced, not asserted**: a unit test computes the contrast of every text/background token pair
in both appearances, and the axe sweep runs in both. Accent colours used as *text* take the
appearance's AA-passing variant; the saturated variants are for fills, glows and large display type.

### Theme selection

**The TurnBase theme** (§2), in Light, Dark or Auto (`platform-ui-library.md` FR-THM-001 as amended).
Appearance is Astryx's `<Theme mode>`, not a hand-rolled `prefers-color-scheme` block; CON-005 as
amended keeps that rule. Auto is `mode="system"` and is the default.

The decorative effects (pointer spotlight and tilt, the starfield, directional page transitions) are
all switched off by `prefers-reduced-motion` and by the user's Reduced-motion setting, carry no
meaning, and the starfield pauses while the tab is hidden (NFR-PERF-002).

### Version discipline

Exact pins (§1), deliberate upgrades through `astryx upgrade --apply`, and a swizzle inventory that
someone can read before an upgrade to know what will not be codemodded.

---

## 7. Working with Astryx as an agent

The CLI is the documentation. It is a dev dependency, so add the script `package.json` needs for
reliable resolution:

```json
"scripts": { "astryx": "node node_modules/@astryxdesign/cli/bin/astryx.mjs" }
```

| Command | Use |
|---|---|
| `npm run astryx -- component --list` | What exists |
| `npm run astryx -- component Button` | Full API: props, variants, examples, theming |
| `npm run astryx -- docs tokens` | The token reference |
| `npm run astryx -- docs theme` | `Theme`, `defineTheme`, light/dark |
| `npm run astryx -- template --list` | Page and block templates |
| `npm run astryx -- swizzle Button` | Rung 2 |
| `npm run astryx -- upgrade --apply` | Codemods between versions |

`npm run astryx -- init` writes an Astryx component index into `CLAUDE.md` so an agent discovers
components instead of guessing them. **It edits `CLAUDE.md`** — run it deliberately and review the
diff, per this repository's own rule that a generated block in a hand-written file is a merge
conflict waiting to happen.

The `astryx` MCP server (`.mcp.json`, `gitmcp.io/facebook/astryx`) serves the same documentation
without a local install and is the faster path when the frontend is not checked out.

---

## 8. What is deliberately absent

- **No wrapper layer.** §4 — application code imports Astryx directly.
- **No parallel token scale.** §5 — Astryx's tokens plus the `--tb-*` additions, nothing that redefines one.
- **No `backdrop-filter`.** Glass is faked (ADR-0017 §1); the cost ADR-0013 removed stays removed.
- **No presence indicators.** Online/offline status is out of scope (`social-friends.md`), so an avatar is Astryx `Avatar` with `name` and never `status`.
- **No charts.** §1 — canary-only packages, and no v1 requirement needs one.
- **No general animation system.** `platform-ui-library.md` *Out of Scope* as amended: a fixed set of decorative effects, nothing configurable.
- **No i18n or RTL.** Out of scope. Our own CSS still prefers `inline-start`/`inline-end` over
  `left`/`right` where it costs nothing.
- **No Storybook of our own.** Astryx has one at `facebook.github.io/astryx`; `ui/` is too small to
  warrant a second. OQ-005 stays deferred rather than declined.
- **No published npm package.** `platform-ui-library.md` CON-002, amended twice now — there is no
  second consumer, and `ui/` is now small enough that the question barely arises.

---

## 9. Requirements traceability

`platform-ui-library.md`. "Astryx" means the requirement is satisfied by the library rather than by
platform code — the obligation is to *use* it, not to rebuild it.

| Requirement | Realized by |
|---|---|
| FR-TOK-001…006 | **Astryx**, set by the TurnBase theme (§2) — tokens; §5 names the families and points at `astryx docs tokens` |
| FR-TOK-007 | §5 — gradient/glow recipes as `--tb-*` tokens (reinstated, ADR-0017) |
| FR-TOK-008 (raw-value ban) | §5 *Enforcement* — `no-raw-color-*`/`no-raw-spacing-css`, our own lint rules; colours defined only in `src/theme/palette.ts` |
| FR-COMP-001…009, 011…014 | **Astryx** — 150+ components; §7 is the lookup path |
| FR-COMP-010 (`className`) | **Astryx** — supported on components; §5 append-not-substitute |
| FR-LYT-001…003 | **Astryx** — `Stack`, `Layout` and the layout primitives |
| FR-THM-001 | §2, §6 — the TurnBase theme via `<Theme mode>`; Light / Dark / Auto |
| FR-THM-002 | **Astryx** — `data-astryx-theme` on `<html>`; §2 |
| NFR-DX-001 | §7 — the CLI and MCP server are the documentation |
| NFR-DX-002 | **Astryx** — full TypeScript; typed props on rung-3 components |
| NFR-DX-003 | §5 — CSS Modules scope our styles mechanically; Astryx's are pre-scoped |
| NFR-DX-004 | §4 — the two import-boundary rules |
| NFR-PERF-001 | **Astryx** — pre-built CSS, no runtime style engine, per-component import paths |
| NFR-PERF-002 | §6, §8 — no `backdrop-filter`; effects are reduced-motion-aware and the starfield pauses when hidden |
| NFR-VER-001 | §1, §6 — exact pins and codemod-driven upgrades |
| CON-001 | React 19 + TypeScript — also Astryx's own peer requirement |
| CON-002 | **Amended (2nd time)** — §4: a small `ui/` module, not a package, not a submodule |
| CON-003 | **Narrowed** — §5: no runtime CSS-in-JS *in our code*. Astryx's StyleX is pre-built and never compiled here |
| CON-004 | §2 — Figtree and Pixelify Sans, named by the theme, self-hosted for the CSP |
| CON-005 | §6 — appearance is `Theme` configuration, not `prefers-color-scheme` |
| OQ-001 (radius) | **Dropped** — Astryx's `--radius-*` scale replaces the single-radius question |
| OQ-002 (neon hex) | **Resolved by ADR-0017** — the palette is the theme source (§2); the values live in `src/theme/` |
| OQ-003 (contrast) | §6 — **resolved**: WCAG AA is a hard floor, enforced by a token-pair test and the axe sweep in both appearances |
| OQ-004 (blur fallback) | **Dropped** — no frosted glass to degrade |
| OQ-005 (Storybook) | §8 — deferred; Astryx ships one |
