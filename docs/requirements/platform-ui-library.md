# Platform UI Library Requirements

> **Satisfied by Astryx, not by platform code**
> ([ADR-0013](../decisions/0013-astryx-design-system.md), 2026-08-17). The library is
> [Astryx](https://github.com/facebook/astryx), Meta's open-source design system: 150+ accessible
> components, seven themes, MIT, React 19+. The requirements below still state **what the platform
> needs**; the obligation they create is to *use* Astryx correctly rather than to rebuild it.
>
> Requirements marked **Astryx** in the Description column are met by the library as shipped. The
> neon-and-frosted-glass aesthetic those requirements originally described is **superseded** — v1
> takes Astryx's muted `theme-neutral` direction, which is what "functional and minimalistic" asked
> for. Amended requirements say so inline.

## Related API Specifications

- [design-system.md](../specs/platform-frontend/design-system.md) — the Astryx integration: setup, the composition ladder, the import boundary, what remains ours (implements FR-TOK-*, FR-COMP-*, FR-LYT-*, FR-THM-*, NFR-DX-*, CON-001…005)
- [shell-architecture.md](../specs/platform-frontend/shell-architecture.md) — the application that consumes the library: routing, auth tiers, page layout

## Stakeholders

| Role | Description |
|------|-------------|
| Platform frontend engineers | Primary consumers; build TurnBase platform UI using library components and tokens |
| AI coding agents | Primary code authors; library must be strictly enforceable by automated tooling |
| End users (players) | Experience the visual output; expect a consistent, polished interface |
| TurnBase maintainers | Own and evolve the library; manage versioning and breaking changes |

## Functional Requirements

### Design Tokens

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-TOK-001 | Color tokens | **Astryx, amended.** A complete token palette expressed as CSS custom properties: backgrounds, surfaces, text, borders and semantic state colors. **The neon accent palette is dropped** — `theme-neutral` is muted by design, and ADR-0013 takes that direction. Astryx's `--color-*` families supply this. | Must |
| FR-TOK-002 | Typography tokens | **Astryx.** A typography scale in CSS custom properties. `theme-neutral` names Figtree, satisfying CON-004 — but does not load it; the application self-hosts the webfont (`design-system.md` §2). | Must |
| FR-TOK-003 | Spacing tokens | **Astryx.** `--spacing-*`, with `--spacing-1` as the 4px base unit. All padding, margin and gap values in application code reference these. | Must |
| FR-TOK-004 | Border radius tokens | **Astryx, amended.** A radius scale — `--radius-inner` / `--radius-element` / `--radius-container` — rather than the single uniform value originally required. Astryx applies it consistently, which is the property that was actually wanted. Closes OQ-001. | Must |
| FR-TOK-005 | Surface tokens | **Astryx, amended.** `--color-background-surface` / `-card` / `-body`. **The frosted-glass requirement is withdrawn**: `theme-neutral` uses opaque surfaces and elevation, and `backdrop-filter` was the platform's single most expensive style declaration. Closes OQ-004, which asked how the blur should degrade — there is no blur. | Must |
| FR-TOK-006 | Elevation/shadow tokens | **Astryx.** `--shadow-low` / `-med` / `-high`, exposed on `Card` as an `elevation` prop. | Must |
| ~~FR-TOK-007~~ | ~~Gradient tokens~~ | **Withdrawn.** Gradients were defined as compositions of the neon accents that FR-TOK-001 no longer has. Astryx ships no gradient tokens and a hero gradient is a screen-level decision, not a library one. | — |
| FR-TOK-008 | Token-only color rule | No raw color value (hex, rgb, hsl, oklch, etc.) may appear in application code. **There is no longer a token definition file to exempt** — every value comes from Astryx — so the rule needs no path allow-list. Enforced via ESLint. | Must |

### Components

**Every requirement in this section is satisfied by Astryx** (ADR-0013). It ships 150+ components;
these fourteen are the ones the platform's views are known to need, and the descriptions below record
*why* each is needed and what behaviour the platform depends on. Look up the actual API with
`npm run astryx -- component <Name>` or the `astryx` MCP server — **not** here. Where Astryx has no
equivalent, `design-system.md` §3's ladder applies: compose, then swizzle, then write.

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-COMP-001 | Button | Variants: primary, secondary, ghost, destructive. Supports disabled and loading states. Uses accent color tokens for emphasis. | Must |
| FR-COMP-002 | Input | Text, number, password, and search variants. Includes label, helper text, and error state. | Must |
| FR-COMP-003 | Card | Primary surface unit. **Amended with FR-TOK-005** — an opaque surface token, elevated above the base background via the `elevation` prop, uniformly rounded. No frosted glass. Serves as the default container for most platform views. | Must |
| FR-COMP-004 | Modal / Dialog | Overlay dialog. **Amended with FR-TOK-005** — an opaque surface, not frosted glass. Supports a title, body slot and action footer. Traps focus when open. | Must |
| FR-COMP-005 | Navigation | Top navigation bar and/or sidebar navigation. Supports active state indication using accent color tokens. | Must |
| FR-COMP-006 | Avatar | Displays a user's **initials** on a colour derived deterministically from their user ID. Supports size variants. **No image and no presence indicator.** As originally written this component required both, and the platform has neither: `user-accounts.md` puts user-provided personal information including avatars out of scope, so there is no image to display, and `social-friends.md` puts online/offline presence indicators out of scope, so there is no state to indicate. Both are additive if those decisions change. | Must |
| FR-COMP-011 | Tabs | Horizontal tab list with a panel per tab, active state from accent tokens, keyboard-navigable. Required by four surfaces that all exist today: the profile's History / Friends / Uploaded Games sections (`game-history.md` FR-HIST-020, `social-friends.md` FR-SOC-013, `game-catalog.md` FR-UPROF-001), the game detail page's statistics tab (`platform-views.md` VW-GDET-002), the Friends section's Friends / Pending split (FR-SOC-013), and the room chat's room / team channel switch (`platform-views.md` VW-RLOBBY-016). | Must |
| FR-COMP-012 | Select | Single-select dropdown with label, helper text and error state, matching Input. Required by catalog sorting (`game-catalog.md` FR-CAT-007), room visibility at creation, and the `enum` parameter type a game may declare (`manifest-schema.md` parameter types). | Must |
| FR-COMP-013 | Switch and Checkbox | Two components, not one: a **Switch** for a setting that takes effect immediately (profile privacy and the four per-section toggles, `platform-views.md` VW-SET-006/006a; block-incoming-requests, `user-accounts.md` FR-PROF-008; spectating-enabled at room creation) and a **Checkbox** for a value submitted with a form. They are distinguished because the Switch implies its change is already saved and the Checkbox implies it is not — a distinction users read from the control, and getting it wrong makes a settings page feel broken. | Must |
| FR-COMP-014 | Badge | Small inline status marker. Two uses with different shapes: a **labelled** badge for the Official / Verified game markers, which `game-catalog.md` NFR-USAB-002 requires to be visually distinct from each other and identifiable in both the catalog listing and the detail page; and a **count** badge for the unread notification total on the nav bell (`notifications-invitations.md` FR-NOTIF-002, `platform-views.md` VW-NAV-005). | Must |
| FR-COMP-007 | Notification / Toast | Transient feedback messages. Variants: info, success, warning, error. Auto-dismiss with configurable duration. | Must |
| FR-COMP-008 | Table | Displays tabular data with column headers. Supports server-driven pagination, column-level filtering, and column-level sorting. Consumers provide data and callback handlers; the component owns the controls UI only. | Must |
| FR-COMP-009 | Card List | Displays a list of items where each item is rendered as a Card. Supports the same server-driven pagination, filtering, and sorting controls as the Table component. Separate component type from Table. | Must |
| FR-COMP-010 | className escape hatch | Every component accepts a `className` prop. The provided class name is appended to the component's own class list and never replaces it. This is the only supported override mechanism. | Must |

### Layout Primitives

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-LYT-001 | Stack | Arranges children in a vertical or horizontal sequence with a gap from the spacing token scale. Direction and spacing are props. | Must |
| FR-LYT-002 | Grid | Arranges children in a responsive CSS grid. Supports configurable column count and gap from the spacing scale. | Must |
| FR-LYT-003 | Box | Generic container that applies padding, margin, and/or background from design tokens via props. Used when Stack/Grid are not appropriate. | Must |

### Theming

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-THM-001 | Single theme | **Astryx, amended.** The platform ships `theme-neutral` in **dark mode**, with no in-app toggle and no runtime switching. Astryx supports light/dark; the platform selects one. The original wording forbade a light theme *existing*, which is not ours to forbid in a third-party library. | Must |
| FR-THM-002 | Token injection | **Astryx.** `<Theme theme={neutralTheme}>` at the root plus `data-astryx-theme` on `<html>`. Application code must not redefine these properties. | Must |

## Non-Functional Requirements

| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-DX-001 | Developer Experience | Every component and token is documented with usage examples and prop descriptions. | 100% of public API documented | Must |
| NFR-DX-002 | Developer Experience | Library ships TypeScript types for all components, tokens, and props. No `any` types in the public API. | 0 `any` in public API | Must |
| NFR-DX-003 | Consistency | Visual output of a given component is identical regardless of which platform view it appears in. No context-dependent style leakage. | Zero known divergences at release | Must |
| NFR-DX-004 | Enforcement | ESLint plugin (or config) is published alongside the component library and is required by consuming apps. Rules cover at minimum: raw color values, spacing values outside the scale, and font sizes outside the scale. | All rules enabled in platform repo CI | Must |
| NFR-PERF-001 | Performance | Library adds no more than 50 kB (gzipped) to a consuming app's initial bundle when tree-shaken to only the imported components. | ≤ 50 kB gzipped (tree-shaken) | Should |
| NFR-PERF-002 | Performance | Scrolling and animation hold 60 fps on mid-range hardware. **The frosted-glass clause is withdrawn with FR-TOK-005** — the expensive declaration it guarded no longer exists. | 60 fps maintained on reference device | Should |
| NFR-VER-001 | Versioning | Library follows semantic versioning. Breaking changes (token renames, removed components, changed prop APIs) are released as major versions with a migration guide. | Semver; migration guide per major | Must |

## Constraints

| ID | Description |
|----|-------------|
| CON-001 | React 19 and TypeScript are the only supported runtime environments. The library is not required to work as plain CSS or web components. |
| CON-002 | **Amended twice.** The component library is [Astryx](https://github.com/facebook/astryx), an external MIT-licensed npm dependency (ADR-0013) — so the original requirement for a self-contained module in its own repository is moot for components. What remains ours is a small `src/ui/` module inside `turnbase-frontend` holding only *composed* and *swizzled* components, with a single public entry point, no dependency on application code, and an ESLint rule enforcing the boundary in both directions. See [`../specs/platform-frontend/design-system.md`](../specs/platform-frontend/design-system.md) §4. |
| CON-003 | **Narrowed.** Peer dependencies: React 19, TypeScript. No runtime CSS-in-JS **in platform code** — our own components use CSS Modules. Astryx authors its styles with StyleX but ships them **pre-built**: no Vite plugin, no PostCSS, no Babel transform is added to this project's build. |
| CON-004 | Figtree is the only permitted typeface. `theme-neutral` names it in `--font-family-body` but does not load it, so the application self-hosts the `woff2` (`design-system.md` §2 — a CDN font would require widening `font-src` in the CSP). No second typeface is bundled. |
| CON-005 | The platform renders in dark mode only and does not follow the OS preference. This is now `<Theme>` configuration rather than CSS we write; no `prefers-color-scheme` media query appears in platform code. |

## Out of Scope

- GDK (game developer kit) UI library — deferred
- Game UI components for sandboxed iframes
- A light theme or any in-app theme switching mechanism. Astryx supports light/dark; the platform selects dark and does not expose a toggle (CON-005)
- Internationalization / RTL layout support
- Animation/motion system (beyond basic state transitions on existing components)
- Data fetching — table/list components receive data via props/callbacks; they do not own network calls

## Open Questions

**None remain open.** Three were dropped by ADR-0013 rather than answered — all three asked the
platform to make a visual decision that Astryx has already made, and answering them would have meant
overriding the library on day one.

- ~~OQ-001~~ Exact border radius — **dropped.** Astryx ships a radius scale (`--radius-inner` / `-element` / `-container`); there is no single value to pick.
- ~~OQ-002~~ Exact neon accent hex values — **dropped.** There is no neon palette. `theme-neutral` is muted, and FR-TOK-001 is amended to match.
- ~~OQ-003~~ Accessibility target — **resolved: WCAG AA is a hard floor** for body text, with no exceptions (`design-system.md` §6). This one survives ADR-0013 unchanged, and the muted palette makes it materially easier to hold than neon-on-near-black would have.
- ~~OQ-004~~ `backdrop-filter` fallback — **dropped.** No frosted glass, so nothing to degrade.
- ~~OQ-005~~ Storybook — **deferred, not declined** (`design-system.md` §8). Astryx ships one at `facebook.github.io/astryx`, and `src/ui/` is too small to warrant a second.
