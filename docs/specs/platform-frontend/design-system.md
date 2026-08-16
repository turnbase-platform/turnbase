# The Platform Design System

Tokens, CSS strategy, component architecture and the packaging boundary for the platform's component
library. Realizes `../../requirements/platform-ui-library.md` in full.

Closes half of review blocker **IR-23**: ~30 requirements, 24 of them cited by no spec, and no
document anywhere in `docs/specs/` covering tokens, CSS strategy or component architecture.

**Scope.** This document owns the *library*: what a component is, how it is styled, and how
application code may use it. It does not own page layout, routing, or which component appears on
which screen — those are [`shell-architecture.md`](shell-architecture.md)'s and
`../../requirements/platform-views.md`'s. The dividing line: if the answer depends on a specific
screen, it is not here.

---

## 1. Where it lives

**`src/design-system/` inside the `turnbase-frontend` repository.** Not a submodule, not an npm
package.

```
turnbase-frontend/src/
├── design-system/
│   ├── index.ts              # the public entry point — the ONLY legal import path
│   ├── tokens/
│   │   ├── tokens.css        # every CSS custom property, on :root
│   │   └── tokens.ts         # the TypeScript mirror (scale names, not values)
│   ├── primitives/           # Stack, Grid, Box
│   ├── components/           # Button, Input, Card, …
│   ├── eslint/               # the rules of NFR-DX-004
│   └── README.md             # NFR-DX-001
└── features/                 # application code — imports from 'design-system' only
```

### The boundary is enforced by lint, not by a repository

Application code imports from `@/design-system` and nothing deeper. A deep import
(`@/design-system/components/Button/Button.styles.css`) reaches past the public API into a file that
may be renamed in any refactor, which is exactly what a package boundary exists to prevent.

```js
// eslint.config.js
'no-restricted-imports': ['error', { patterns: [{
  group: ['**/design-system/*', '!**/design-system'],
  message: 'Import from the design-system entry point, not from inside it.'
}]}]
```

The rule is one-directional, and the other direction matters more: **the design system may not import
from `features/`.** A component that reaches into application code is no longer a component — it is a
screen with a generic name, and it will break the second view that uses it. This is enforced by a
second `no-restricted-imports` pattern on `@/features/*` scoped to `design-system/**`.

### Why not a submodule — the CON-002 amendment

`platform-ui-library.md` CON-002 originally required a standalone repository published as a scoped
npm package. **That is amended** (see the requirement, now updated), and the reasoning belongs here
because this is where a reader will look for it.

A separate repository buys exactly one thing: the ability for a *second* consumer to depend on a
pinned version. There is no second consumer. Game frontends are explicitly out of scope
(`platform-ui-library.md` *Out of Scope* — "GDK UI library — deferred"), and they could not use it
anyway: they run in a sandboxed iframe on a different origin (ADR-0007) with their own bundle.

What it costs is paid on every change: a UI tweak becomes a commit and a version bump in one
repository, an npm publish, a dependency bump in another, and a submodule ref update in a third. For
a solo project that is three ceremonies per button, and the predictable outcome is that the boundary
gets bypassed rather than respected.

**The module boundary is the constraint that was actually wanted, and lint enforces it more strictly
than a package does** — an npm package cannot stop a consumer importing
`@turnbase/ui/dist/components/Button/styles.css`, but `no-restricted-imports` can.

Extraction later is a `git filter-repo` and a `package.json`, because nothing in the design below
depends on co-location: no relative import crosses the boundary, and the entry point already exists.
The cost of deferring is a day; the cost of the ceremony is every day.

---

## 2. Tokens

**CSS custom properties on `:root`, defined once in `tokens/tokens.css`.** Every visual value in the
platform comes from one of them (FR-TOK-008).

| Group | Prefix | Requirement |
|---|---|---|
| Colour | `--tb-color-*` | FR-TOK-001 |
| Typography | `--tb-font-*`, `--tb-text-*`, `--tb-leading-*`, `--tb-tracking-*` | FR-TOK-002 |
| Spacing | `--tb-space-*` | FR-TOK-003 |
| Radius | `--tb-radius` | FR-TOK-004 |
| Surface / blur | `--tb-surface-*`, `--tb-blur-*` | FR-TOK-005 |
| Elevation | `--tb-shadow-*` | FR-TOK-006 |
| Gradient | `--tb-gradient-*` | FR-TOK-007 |

### Colour (FR-TOK-001)

Three layers, and the layering is the design:

```css
:root {
  /* 1. Primitives — the only place a raw colour value appears anywhere */
  --tb-black:        #08080a;
  --tb-neon-pink:    /* OQ-002 */;
  --tb-neon-yellow:  /* OQ-002 */;
  --tb-neon-green:   /* OQ-002 */;
  --tb-neon-blue:    /* OQ-002 */;

  /* 2. Semantic — what application code and components actually use */
  --tb-color-bg:            var(--tb-black);
  --tb-color-surface:       rgb(255 255 255 / 6%);
  --tb-color-surface-raised:rgb(255 255 255 / 10%);
  --tb-color-border:        rgb(255 255 255 / 12%);
  --tb-color-text:          rgb(255 255 255 / 92%);
  --tb-color-text-muted:    rgb(255 255 255 / 60%);
  --tb-color-accent:        var(--tb-neon-blue);
  --tb-color-error:         /* OQ-002 */;
  --tb-color-success:       var(--tb-neon-green);
  --tb-color-warning:       var(--tb-neon-yellow);
}
```

**Components reference the semantic layer only, never a primitive.** A component that uses
`--tb-neon-pink` directly has hardcoded a decision — that *this* thing is pink — into a place where
the intent was "this thing is an accent". Rebalancing the palette then means finding every such site
by eye. The indirection costs one line per token and is the difference between a palette that can be
changed and one that cannot.

Values marked OQ-002 are open in the requirements and are left open here rather than guessed:
inventing hex values in a spec produces numbers that get implemented and never revisited.

### Typography (FR-TOK-002), spacing (FR-TOK-003), radius (FR-TOK-004)

```css
--tb-font-sans: 'Figtree', system-ui, sans-serif;   /* CON-004 — the only typeface */

--tb-text-xs: 0.75rem;  --tb-text-sm: 0.875rem;  --tb-text-base: 1rem;
--tb-text-lg: 1.125rem; --tb-text-xl: 1.5rem;    --tb-text-2xl: 2rem;

--tb-space-1: 4px;  --tb-space-2: 8px;   --tb-space-3: 12px;  --tb-space-4: 16px;
--tb-space-6: 24px; --tb-space-8: 32px;  --tb-space-12: 48px; --tb-space-16: 64px;

--tb-radius: 6px;   /* OQ-001 names the 4–8px range; 6px is the midpoint, revisit on mockup */
```

The spacing scale is **4px steps with gaps** — there is no `--tb-space-5`. A dense scale is not a
scale: if every value is available, the constraint does nothing and layouts drift by two pixels at a
time. The named gaps are the point.

FR-TOK-004 requires **one** radius, not a scale. Every rounded thing in the platform is rounded the
same amount, which is a strong visual signature obtained for free.

Figtree is loaded by the design system as a self-hosted `woff2` with `font-display: swap`, not from a
CDN. `shell-architecture.md` §6's CSP sets `font-src 'self'`, and a CDN font would require widening
it — trading a security directive for a hosting convenience.

### Surface and elevation (FR-TOK-005, FR-TOK-006)

```css
--tb-blur-surface: 12px;
--tb-shadow-1: 0 1px 2px rgb(0 0 0 / 40%);
--tb-shadow-2: 0 4px 16px rgb(0 0 0 / 45%);
--tb-shadow-3: 0 12px 40px rgb(0 0 0 / 55%);
```

**Frosted glass is `background: var(--tb-color-surface)` plus `backdrop-filter: blur(var(--tb-blur-surface))`,
and it is applied by the `Card` component only** (FR-COMP-003). Not by a utility class and not by
application code. `backdrop-filter` is the most expensive property in the platform's stylesheet —
NFR-PERF-002 requires 60 fps on mid-range hardware during scroll — and a rule applied in one place
can be measured, capped and, if necessary, disabled. Scattered across application code it cannot.

OQ-004 asks whether the blur degrades gracefully. **It does, and the mechanism costs nothing:**
`--tb-color-surface` is a semi-opaque fill that stands alone, so a browser without `backdrop-filter`
renders a flat translucent surface rather than an unreadable one. `@supports (backdrop-filter: blur(1px))`
adds the blur; the fallback is the base declaration. That resolves OQ-004 as *yes, with the existing
surface colour* and needs no second token.

### Gradients (FR-TOK-007)

```css
--tb-gradient-hero: linear-gradient(135deg, var(--tb-neon-blue), var(--tb-neon-pink));
```

Composed from the accent primitives so a palette change propagates. Gradients are for hero areas and
large surfaces; a gradient on a small control reads as a rendering artifact.

### Theming (FR-THM-001, FR-THM-002)

`tokens.css` is imported once, at the application root, and sets the properties on `:root`. **There
is no `ThemeProvider` component**, because there is nothing to provide: FR-THM-001 ships one dark
theme with no toggle and no runtime switching, so a React context would be a subscription to a value
that never changes — re-render machinery for a constant. FR-THM-002 permits "a CSS class/attribute at
the root" and that is the form taken.

CON-005 means no `prefers-color-scheme` block anywhere. `color-scheme: dark` is set on `:root` so
that form controls and scrollbars the platform does not style still render dark.

### Enforcement (FR-TOK-008, NFR-DX-004)

Shipped in `design-system/eslint/`, enabled in the frontend's CI (`platform-operations.md`
FR-CICD-011):

| Rule | Forbids | Escape |
|---|---|---|
| `no-raw-color` | Any hex, `rgb()`, `hsl()`, `oklch()` literal in a `.css` or `.tsx` file | `tokens.css` only, by path allow-list |
| `no-raw-spacing` | A `px`/`rem` length on `padding`, `margin`, `gap`, `inset` | none |
| `no-raw-font-size` | A `font-size` literal | none |

**Two of the three have no escape hatch, deliberately.** An escape hatch on a lint rule is used the
first time the rule is inconvenient, which is the first time it is doing its job. `no-raw-color`
needs one only because the token file must contain the values it defines, and that is a path
allow-list rather than an inline disable comment — a path cannot spread.

---

## 3. CSS strategy: CSS Modules

**CSS Modules, one `.module.css` per component, consuming custom properties.** Vite supports them
with no plugin.

The alternatives and why they lose:

| Option | Why not |
|---|---|
| Runtime CSS-in-JS (styled-components, Emotion) | **Excluded by CON-003** — and independently by first paint: styles are injected during render, so the shell's first meaningful paint waits on JavaScript. The shell gates every view (`shell-architecture.md`), so this cost is paid once per session by every user |
| Zero-runtime CSS-in-JS (vanilla-extract) | Genuinely good, and the close call. It gives typed styles and a compile-time guarantee that a token exists. It loses on **one** point: it is a build-time dependency with its own Vite plugin and its own failure modes, bought for a type-safety win that `no-raw-*` lint already delivers most of. CSS Modules are the boring option and the boring option has no plugin to break |
| Tailwind | Its scale would compete with the token scale, and FR-TOK-008 requires one source. Reconciling the two is more configuration than writing the CSS |
| Plain global CSS | NFR-DX-003 requires no context-dependent style leakage. Module scoping is exactly that guarantee, mechanically |

```css
/* Button.module.css */
.button {
  font-family: var(--tb-font-sans);
  padding: var(--tb-space-2) var(--tb-space-4);
  border-radius: var(--tb-radius);
  border: 1px solid var(--tb-color-border);
}
.primary { background: var(--tb-color-accent); color: var(--tb-black); }
.ghost   { background: transparent; border-color: transparent; }
```

Variants are **classes composed by the component**, not props interpolated into a style string. This
is what makes the CSS statically analysable — `no-raw-color` can read a `.css` file, and it cannot
read a template literal assembled at runtime.

---

## 4. Component inventory

Every component ships: a named export from `index.ts`, a props interface with no `any`
(NFR-DX-002), a `className` prop (FR-COMP-010), and a README entry with a usage example
(NFR-DX-001).

### Layout primitives

| Component | Props | Requirement |
|---|---|---|
| `Stack` | `direction: 'row' \| 'column'`, `gap: SpaceToken`, `align`, `justify` | FR-LYT-001 |
| `Grid` | `columns: number \| ResponsiveColumns`, `gap: SpaceToken` | FR-LYT-002 |
| `Box` | `padding`, `margin`, `background` — each a token name, never a raw value | FR-LYT-003 |

`SpaceToken` is a TypeScript union of the scale's names (`'1' | '2' | '3' | '4' | '6' | '8' | '12' | '16'`),
so `gap="5"` is a compile error. This is the type system doing what `no-raw-spacing` does for CSS, on
the JSX side.

### Components

| Component | Variants and states | Requirement |
|---|---|---|
| `Button` | `primary` \| `secondary` \| `ghost` \| `destructive`; `disabled`, `loading` | FR-COMP-001 |
| `Input` | `text` \| `number` \| `password` \| `search`; label, helper text, error state | FR-COMP-002 |
| `Card` | The frosted-glass surface (§2). The default container for most views | FR-COMP-003 |
| `Modal` | Title, body slot, action footer. Focus trap (§6) | FR-COMP-004 |
| `Navigation` | Top bar and sidebar; active state from `--tb-color-accent` | FR-COMP-005 |
| `Avatar` | Initials on a colour derived from the user id; size variants. **No image, no presence dot** | FR-COMP-006 |
| `Toast` | `info` \| `success` \| `warning` \| `error`; auto-dismiss with configurable duration | FR-COMP-007 |
| `Table` | Column headers; server-driven pagination, filtering, sorting controls | FR-COMP-008 |
| `CardList` | Same controls as `Table`, items rendered as `Card`s | FR-COMP-009 |
| `Tabs` | Horizontal tab list, one panel per tab, keyboard-navigable | FR-COMP-011 |
| `Select` | Single-select with label, helper text, error state — matches `Input` | FR-COMP-012 |
| `Switch` | A setting that takes effect immediately | FR-COMP-013 |
| `Checkbox` | A value submitted with a form | FR-COMP-013 |
| `Badge` | `label` variant (Official / Verified) and `count` variant (unread bell) | FR-COMP-014 |

Three of these carry a rule that is easy to lose:

- **`Avatar` has no image slot and no presence indicator** (FR-COMP-006). The platform has neither:
  `user-accounts.md` puts user-provided avatars out of scope and `social-friends.md` puts presence out
  of scope. Adding the props "for later" invites a caller to pass a URL that renders nothing.
- **`Switch` and `Checkbox` are two components** (FR-COMP-013), because the control tells the user
  whether their change is already saved. A Switch that needs a Save button, or a Checkbox that
  persists on click, makes a settings page feel broken in a way users cannot articulate.
- **`Table` and `CardList` own the controls, never the data** (FR-COMP-008/009, and
  `platform-ui-library.md` *Out of Scope*: "data fetching"). They take a page of rows and callbacks;
  they do not know what a page is. Every list in the platform is server-paginated
  ([`../api-design/pagination-filtering-sorting.md`](../api-design/pagination-filtering-sorting.md)),
  and a component that fetched would have to know that envelope — coupling the library to the API.

`FR-COMP-010`'s `className` is **appended, never substituted**:

```tsx
<button className={cx(styles.button, styles[variant], className)} …>
```

Substituting would strip the component's own styles and produce a component that looks like whatever
the last caller decided, which is NFR-DX-003's divergence by another route. Append-only means an
override can add and cannot subtract — enough for a margin, not enough to redesign a button in place.

---

## 5. Composition rules

Two tiers. Primitives (`Stack`, `Grid`, `Box`) may contain anything. Components may contain
primitives and other components, with three restrictions:

| Rule | Why |
|---|---|
| A `Card` may not contain a `Card` | Nested frosted glass compounds the blur and the translucency; the inner surface reads as a rendering bug |
| A `Modal` may not contain a `Modal` | One focus trap at a time. A second trap makes the first unescapable |
| `Table` and `CardList` may not contain each other | They are the two presentations of one list, not composable layers |

Everything else composes. In particular the library ships **no page-level or screen-specific
components** — no `RoomCard`, no `GameTile`. Those live in `features/` and are built from `Card` plus
primitives. A `RoomCard` in the design system is a screen with a generic name (§1), and it is the
exact thing the import boundary exists to keep out.

Spacing between components is the **parent's** responsibility, via `Stack`'s `gap`. No component
carries an outer margin. A component with a built-in margin cannot be placed anywhere its author did
not anticipate, and the workaround is always a negative margin somewhere else.

---

## 6. Accessibility baseline

The library, not the application, owns these — an accessible component used correctly is accessible
everywhere, and NFR-DX-003 already requires context-independence.

| Rule | Applies to |
|---|---|
| Every interactive element is reachable and operable by keyboard | All |
| Visible focus ring, from `--tb-color-accent`, never `outline: none` without a replacement | All |
| `Modal` traps focus while open, restores it to the trigger on close, closes on `Escape` | FR-COMP-004 |
| `Tabs` implements the WAI-ARIA tabs pattern: arrow keys move, `Home`/`End` jump, one tab stop for the list | FR-COMP-011 |
| `Input`/`Select` label is a real `<label for>`; error text is `aria-describedby` and the control is `aria-invalid` | FR-COMP-002/012 |
| `Toast` renders into an `aria-live="polite"` region — `assertive` for the `error` variant only | FR-COMP-007 |
| `Badge`'s count variant carries an accessible label ("3 unread notifications"), not a bare number | FR-COMP-014 |
| Colour is never the only carrier of meaning | All — a neon palette makes this easy to violate |

### Contrast, and OQ-003

`platform-ui-library.md` OQ-003 records that WCAG AA contrast is **at risk** with neon-on-dark and
asks for an explicit decision. **The decision taken here: WCAG AA (4.5:1 body text, 3:1 large text
and UI boundaries) is a hard floor, and the palette is adjusted to meet it rather than the other way
round.**

The consequence is concrete and worth stating before it is discovered in review: saturated neon on
near-black usually *passes* for large text and *fails* for body text, so the neon accents are for
emphasis, borders, active states and headings — not for paragraphs. Body text is
`--tb-color-text` (white at 92%), which passes comfortably.

This constrains OQ-002's palette pass: each accent must be checked against `--tb-color-bg` at its
intended sizes, and an accent that cannot reach 4.5:1 at body size is not thereby rejected — it is
restricted to the uses where 3:1 applies. That is a usable rule for a design pass; "aim for AA" is
not.

`--tb-color-text-muted` at 60% is the value most at risk and is the one to verify first.

---

## 7. What is deliberately absent

- **No `ThemeProvider`.** §2 — one theme, no toggle.
- **No animation system.** `platform-ui-library.md` *Out of Scope*. Components have state
  transitions; there is no motion token scale and no orchestration library.
- **No i18n or RTL.** Out of scope. No component hardcodes `left`/`right` where `inline-start`/
  `inline-end` would do, because that costs nothing today and is the whole of RTL readiness.
- **No icon set decision.** Not required by any requirement. Whatever is chosen is imported by the
  components that need it and is not re-exported — an icon set re-exported from the design system
  becomes API the library must version (NFR-VER-001).
- **No Storybook, for now.** OQ-005 assumes it without requiring it. NFR-DX-001's documentation
  obligation is met by the README with usage examples; Storybook is a build target, a dependency tree
  and a deployment, and it is additive whenever the component count makes a browsable explorer worth
  it. Recorded as deferred rather than declined.
- **No published npm package and no version number.** §1. NFR-VER-001's semver and migration-guide
  obligation applies from the moment there is a second consumer; with one consumer in one repository,
  a breaking change is a refactor the compiler catches.

---

## 8. Requirements traceability

| Requirement | Realized by |
|---|---|
| FR-TOK-001 | §2 — three-layer colour, primitives → semantic |
| FR-TOK-002 | §2 — type scale, Figtree via CON-004 |
| FR-TOK-003 | §2 — 4px scale with deliberate gaps |
| FR-TOK-004 | §2 — one `--tb-radius` |
| FR-TOK-005 | §2 — surface and blur tokens, applied by `Card` only |
| FR-TOK-006 | §2 — three shadow levels |
| FR-TOK-007 | §2 — gradients composed from accent primitives |
| FR-TOK-008 | §2 — `no-raw-color`, path-allow-listed to `tokens.css` |
| FR-COMP-001…014 | §4 inventory |
| FR-COMP-010 | §4 — `className` appended via `cx`, never substituted |
| FR-LYT-001…003 | §4 — `Stack`, `Grid`, `Box` with `SpaceToken`-typed props |
| FR-THM-001 | §2 — one dark theme; `color-scheme: dark` |
| FR-THM-002 | §2 — `:root` custom properties, no provider component |
| NFR-DX-001 | §4 — README entry with usage example per component |
| NFR-DX-002 | §4 — typed props, no `any`; `SpaceToken` unions |
| NFR-DX-003 | §3 — CSS Modules scope styles mechanically; §5 — no outer margins |
| NFR-DX-004 | §2 — the three lint rules, enabled in CI per `platform-operations.md` FR-CICD-011 |
| NFR-PERF-001 | §3 — CSS Modules and named exports are tree-shakeable; no runtime style engine |
| NFR-PERF-002 | §2 — `backdrop-filter` confined to `Card`, so it can be measured and capped |
| NFR-VER-001 | §7 — applies from the second consumer; §1 states the extraction path |
| CON-001 | §3, §4 — React 19 + TypeScript only |
| CON-002 | **Amended** — §1: an internal module with a lint-enforced boundary, not a submodule |
| CON-003 | §3 — CSS Modules; no runtime CSS-in-JS, no Babel transform |
| CON-004 | §2 — Figtree only, self-hosted for the CSP |
| CON-005 | §2 — no `prefers-color-scheme` anywhere |
| OQ-001 | §2 — `6px`, the midpoint of the stated range, pending a mockup |
| OQ-002 | §2 — **left open**; the palette pass is constrained by OQ-003's resolution |
| OQ-003 | §6 — **resolved**: WCAG AA is a hard floor; neon is for emphasis, not body text |
| OQ-004 | §2 — **resolved**: the semi-opaque surface colour is the fallback; no second token |
| OQ-005 | §7 — deferred, not declined |
