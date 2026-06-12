# Platform UI Library Requirements

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
| FR-TOK-001 | Color tokens | Library defines a complete dark-theme color palette: black base background, semi-opaque surface colors, neon accent colors (pink, yellow, green, blue), text colors, border colors, and semantic state colors (error, success, warning). All values are expressed as CSS custom properties. | Must |
| FR-TOK-002 | Typography tokens | Library defines a typography scale using Figtree as the sole typeface: font sizes, font weights, line heights, and letter spacing. All text in consuming apps must use these tokens. | Must |
| FR-TOK-003 | Spacing tokens | Library defines a discrete spacing scale (e.g. 4px steps). All padding, margin, and gap values in consuming apps must reference spacing tokens. | Must |
| FR-TOK-004 | Border radius tokens | Library defines a single uniform border radius value applied consistently across all components. The value is small (targeting the 4–8px range; exact value decided in design phase). | Must |
| FR-TOK-005 | Surface/blur tokens | Library defines opacity and backdrop-blur values used for frosted-glass surfaces. These tokens are the only permitted source for blur and translucency values. | Must |
| FR-TOK-006 | Elevation/shadow tokens | Library defines shadow values that express elevation levels, used to lift card surfaces above the base background. | Must |
| FR-TOK-007 | Gradient tokens | Library defines reusable gradient definitions built from neon accent colors, suitable for use on larger surfaces and hero areas. | Should |
| FR-TOK-008 | Token-only color rule | No raw color value (hex, rgb, hsl, oklch, etc.) may appear in application code outside the token definition file. Enforced via ESLint. | Must |

### Components

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-COMP-001 | Button | Variants: primary, secondary, ghost, destructive. Supports disabled and loading states. Uses accent color tokens for emphasis. | Must |
| FR-COMP-002 | Input | Text, number, password, and search variants. Includes label, helper text, and error state. | Must |
| FR-COMP-003 | Card | Primary surface unit. Frosted-glass background (semi-opaque with backdrop blur), elevated above base background using shadow tokens, uniformly rounded. Serves as the default container for most platform views. | Must |
| FR-COMP-004 | Modal / Dialog | Overlay dialog with a frosted-glass surface. Supports a title, body slot, and action footer. Traps focus when open. | Must |
| FR-COMP-005 | Navigation | Top navigation bar and/or sidebar navigation. Supports active state indication using accent color tokens. | Must |
| FR-COMP-006 | Avatar | Displays a user image or initials fallback. Supports size variants and an online/offline status indicator. | Must |
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
| FR-THM-001 | Dark theme only | The library ships with a single dark theme. No light theme, no theme toggle, no runtime theme switching. | Must |
| FR-THM-002 | Token injection | The theme is applied by rendering a single provider component (or injecting a CSS class/attribute at the root) that sets all CSS custom properties. Consuming apps must not redefine these properties. | Must |

## Non-Functional Requirements

| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-DX-001 | Developer Experience | Every component and token is documented with usage examples and prop descriptions. | 100% of public API documented | Must |
| NFR-DX-002 | Developer Experience | Library ships TypeScript types for all components, tokens, and props. No `any` types in the public API. | 0 `any` in public API | Must |
| NFR-DX-003 | Consistency | Visual output of a given component is identical regardless of which platform view it appears in. No context-dependent style leakage. | Zero known divergences at release | Must |
| NFR-DX-004 | Enforcement | ESLint plugin (or config) is published alongside the component library and is required by consuming apps. Rules cover at minimum: raw color values, spacing values outside the scale, and font sizes outside the scale. | All rules enabled in platform repo CI | Must |
| NFR-PERF-001 | Performance | Library adds no more than 50 kB (gzipped) to a consuming app's initial bundle when tree-shaken to only the imported components. | ≤ 50 kB gzipped (tree-shaken) | Should |
| NFR-PERF-002 | Performance | Frosted-glass surfaces must not cause visible frame drops on mid-range hardware during scroll or animation. | 60 fps maintained on reference device | Should |
| NFR-VER-001 | Versioning | Library follows semantic versioning. Breaking changes (token renames, removed components, changed prop APIs) are released as major versions with a migration guide. | Semver; migration guide per major | Must |

## Constraints

| ID | Description |
|----|-------------|
| CON-001 | React 19 and TypeScript are the only supported runtime environments. The library is not required to work as plain CSS or web components. |
| CON-002 | The library lives in a standalone repository, registered as a submodule of the TurnBase orchestrator repo, and is published as a scoped npm package. |
| CON-003 | Peer dependencies: React 19, TypeScript. No runtime CSS-in-JS library that requires a Babel transform (avoids build-time coupling to consuming apps). |
| CON-004 | Figtree is the only permitted typeface. It must be loaded by the library or its setup instructions; consuming apps must not bundle a second typeface. |
| CON-005 | Dark theme only. No light-mode styles, no `prefers-color-scheme` media query support. |

## Out of Scope

- GDK (game developer kit) UI library — deferred
- Game UI components for sandboxed iframes
- Light theme or any theme switching mechanism
- Internationalization / RTL layout support
- Animation/motion system (beyond basic state transitions on existing components)
- Data fetching — table/list components receive data via props/callbacks; they do not own network calls

## Open Questions

- OQ-001: Exact border radius value (requires design mockup to validate feel)
- OQ-002: Exact neon accent color values (hex) — needs a design pass to balance vibrancy against legibility on dark backgrounds
- OQ-003: Accessibility targets — WCAG AA compliance for contrast is at risk given neon-on-dark palettes; needs explicit decision on minimum contrast ratio
- OQ-004: Should the frosted-glass blur degrade gracefully for browsers/devices that do not support `backdrop-filter`? If yes, what is the fallback surface color?
- OQ-005: Storybook or equivalent component explorer — assumed yes, but not yet required
