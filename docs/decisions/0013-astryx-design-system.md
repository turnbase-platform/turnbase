# ADR-0013: Astryx supersedes the in-house design system

- **Status:** Accepted — §4 (*The aesthetic changes*) **superseded by [ADR-0017](0017-turnbase-visual-identity.md)** (2026-10-11); §1–3 and §5 stand
- **Date:** 2026-08-17
- **Deciders:** Project owner
- **Supersedes:** the component-library half of
  [`../specs/platform-frontend/design-system.md`](../specs/platform-frontend/design-system.md),
  written 2026-08-16 to close review blocker IR-23

## Context

IR-23 found that `platform-ui-library.md` — roughly thirty requirements covering tokens, a component
inventory, layout primitives and theming — had **no implementing specification anywhere**. It was
closed the day before this ADR by writing `design-system.md`: our own tokens, our own CSS Modules
convention, our own seventeen components, and a lint-enforced module boundary inside
`turnbase-frontend`.

That specification is sound and would work. It is also **seventeen components we would have to build,
document, test for accessibility, and maintain** — on a project whose stated purpose is to
demonstrate architecture, not to demonstrate that we can write a `Tabs` component with correct
arrow-key handling.

[Astryx](https://github.com/facebook/astryx) is Meta's open-source design system, released publicly
in 2026 after eight years of internal use across 13,000+ apps. It ships 150+ accessible components,
seven themes, light/dark, page templates and a CLI. MIT licensed. React 19+.

Two properties made it worth reversing a one-day-old decision rather than noting it as an
alternative:

1. **It is designed for agent-driven development.** The CLI, docs and component API are built as one
   surface so "a person and an AI assistant build the same way, from the same reference". `astryx
   init` writes a component index into `CLAUDE.md`. Phase 1 of this project is explicitly executed by
   implementation agents at low reasoning effort — a library whose documentation is a queryable tool
   rather than a website is worth more here than it would be on a human-only team.
2. **It imposes nothing on our own code.** Astryx authors its styles with StyleX, but ships
   **pre-built CSS**: no Vite plugin, no PostCSS, no Babel config. Overrides are plain `className`,
   explicitly supported against CSS Modules. The styling decision `design-system.md` made — CSS
   Modules, no runtime CSS-in-JS — therefore survives intact for everything we write ourselves.

## Decision

**Adopt `@astryxdesign/core` as the platform frontend's component library. `design-system.md` is
rewritten as an integration specification rather than a construction one.**

### 1. Astryx owns components, tokens and theming

`platform-ui-library.md`'s `FR-COMP-*`, `FR-TOK-*`, `FR-LYT-*` and `FR-THM-*` are satisfied by the
library rather than by our code. We do not re-implement a `Button`, and we do not define a parallel
token scale that would have to be reconciled with Astryx's on every screen.

### 2. We own composition, and only composition

Anything the platform needs that Astryx does not ship is built **by composing Astryx primitives**,
in the application, using Astryx tokens. Three escape hatches exist and are ranked:

1. Compose existing components. Almost always sufficient.
2. `astryx swizzle <Component>` — ejects the component's source into our repo to own outright. For
   when a component is 90% right.
3. Write a new component from scratch against Astryx tokens. Last resort, and it must still consume
   `--spacing-*`, `--color-*`, `--radius-*` so it is visually part of the system.

### 3. We do not transcribe Astryx's inventory into this corpus

The component list, prop signatures and token names live in Astryx and are read through
`astryx component <Name>` or the MCP server. **Copying them here would create a snapshot that is
wrong within a release** — the same failure that made this project delete 1,794 lines of
machine-extracted inventories on 2026-08-16.

### 4. The aesthetic changes, and that is accepted

> **Superseded 2026-10-11 by [ADR-0017](0017-turnbase-visual-identity.md).** The custom theme this section
> called "available later" is now taken. Kept as written because it is why the stock theme exists.

`platform-ui-library.md` describes neon accents on near-black with frosted-glass surfaces and
gradients (FR-TOK-005, FR-TOK-007, OQ-002). Astryx's `theme-neutral` is muted and minimal. **We take
the muted direction**, which is what "functional and minimalistic" asked for. The neon-specific
requirements are amended rather than carried as requirements the implementation knowingly violates.

A custom theme via `defineTheme` remains available later — a theme is a set of CSS custom property
overrides, so this is reversible without touching component code.

## Consequences

### What gets easier

- Seventeen components, their accessibility behaviour and their documentation stop being our work.
- Dark mode, focus management, ARIA patterns and keyboard navigation arrive tested.
- `IMP-M6-01` changes from *build a component library* to *install, theme, and set the boundary* —
  the single largest scope reduction available in M6.
- Page templates (`astryx template dashboard`) give M6's views a starting structure.

### What gets harder, or riskier

- **Astryx is Beta at v0.4.3.** A pre-1.0 dependency can break under us. Mitigation: pin exact
  versions in `package.json` (no `^`), and use `astryx upgrade --apply` codemods on deliberate
  upgrades rather than drifting.
- **A third-party library now sits on the critical path of every view.** If Astryx lacks something,
  we compose or swizzle rather than fork — §2's ladder exists so that decision is made the same way
  every time.
- **Two styling systems coexist** — StyleX inside Astryx's pre-built CSS, CSS Modules in ours. This
  is fine precisely because Astryx's is pre-built: we never compile StyleX, and the boundary is the
  package edge rather than a convention anyone has to remember.
- **`@astryxdesign/charts` and `/vega` are canary-only** with no stable release, and their own
  readiness audit marks several components "needs work". No v1 requirement needs a chart; if
  `per-game-statistics.md` ever wants one, that is a separate decision.

### Cascade

| Document | Change |
|---|---|
| `platform-ui-library.md` | CON-002 amended again; CON-003 narrowed to our own code; FR-TOK/FR-COMP/FR-LYT/FR-THM satisfied by Astryx; the neon and frosted-glass requirements amended; OQ-001…005 resolved or dropped |
| `design-system.md` | Rewritten as an integration spec |
| `shell-architecture.md` | `<Theme>` and `<LinkProvider>` at the root; CSP must allow the webfont |
| `registry.md` | `IMP-M0-05`, `IMP-M6-01`, `IMP-M6-02` |
| `CLAUDE.md` | Tech-stack row; `astryx init` writes a component index into it |

### Why this is an ADR

It reverses a decision recorded one day earlier, in a document that a future reader would otherwise
take as current. It also amends the same constraint (CON-002) for the second time in two days. Both
are exactly the kind of thing that gets silently re-litigated six months later by someone reading
`design-system.md` and wondering why the corpus describes a component library that does not exist.
