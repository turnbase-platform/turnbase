# Onboarding Wizard Requirements

> **Post-MVP — not in v1 scope.** Cut during the 2026-08-16 implementation-readiness remediation
> (IR-23). The onboarding wizard is first-run polish on a platform whose v1 audience is its author,
> and it was the only one of the four structural gaps in that review that could be dropped without
> weakening the demonstration the project exists to make. The requirements below are retained
> unchanged and are the starting point whenever it is scheduled; nothing in v1 depends on them.
>
> **Nothing else in the corpus references this document**, which is what made the cut cheap — with
> one exception, now resolved: FR-ONB-004 required a landing-page CTA that `platform-views.md` never
> had, and that CTA is not being added.

## Stakeholders

| Role | Description |
|------|-------------|
| Anonymous visitor (guest) | Arrives on the platform without an account; sees onboarding once per browser |
| New registered user | Just completed sign-in for the first time; sees onboarding automatically |
| Returning user | Has already seen onboarding; never sees it automatically again |
| Platform team | Maintains onboarding content and pane structure |

---

## Functional Requirements

### Triggering

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-ONB-001 | Auto-show for guests | The wizard is shown automatically to anonymous (guest) visitors on their first visit. "First visit" is determined by the absence of a localStorage flag. | Post-MVP |
| FR-ONB-002 | Auto-show after first sign-in | The wizard is shown automatically the first time a registered user signs in. "First sign-in" is determined by the absence of a localStorage flag set at sign-in time. | Post-MVP |
| FR-ONB-003 | Suppress repeat auto-show | Once a user (guest or registered) has seen or dismissed the wizard, it is never shown automatically again. Suppression is tracked via localStorage for both guests and registered users. The onboarding is a UI/UX concern and does not require server-side state. | Post-MVP |
| FR-ONB-004 | Landing page trigger | The platform landing page provides a clearly labelled CTA (e.g. "See what TurnBase offers") that opens the same onboarding wizard on demand, regardless of prior completion. | Post-MVP |

### Wizard Structure & Navigation

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-ONB-005 | Multi-step wizard overlay | The wizard is rendered as a modal overlay on top of the platform UI, with a semi-transparent backdrop. It does not navigate away from the current page. | Post-MVP |
| FR-ONB-006 | Pane count | The wizard contains between 3 and 5 panes. The exact split is defined during UI design, following the suggested pane structure below. | Post-MVP |
| FR-ONB-007 | Forward navigation | Each pane has a "Next" button advancing to the following pane. The last pane has a "Get started" or equivalent completion CTA that closes the overlay with no further navigation. | Post-MVP |
| FR-ONB-008 | Backward navigation | Each pane (except the first) has a "Back" button returning to the previous pane. | Post-MVP |
| FR-ONB-009 | Progress indicator | A visual indicator (e.g. step dots or "2 of 4") is shown on every pane to communicate position within the flow. | Post-MVP |
| FR-ONB-010 | Skip / dismiss | A "Skip" or close (×) control is visible on every pane. Activating it immediately closes the wizard and records it as seen via localStorage. | Post-MVP |

### Pane Content

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-ONB-011 | Illustrated panes | Each pane contains a static illustrated mockup of the relevant platform area and a short text description (headline + 1–2 sentences). | Post-MVP |
| FR-ONB-012 | Pane topics | The panes collectively cover the following topics: platform overview; game catalog and joining a room; creating a room; friend system; game development / SDK. The grouping and exact titles are defined during UI design. | Post-MVP |
| FR-ONB-013 | Animated illustrations | Pane illustrations may use subtle animation (e.g. Lottie or CSS animation) to better convey the feature. | Post-MVP |

### Suggested Pane Structure (design reference)

| # | Working Title | Topics covered |
|---|---------------|----------------|
| 1 | Welcome to TurnBase | Platform overview, value proposition |
| 2 | Find & join a game | Game catalog, browsing, joining a room, watching live games |
| 3 | Create a room | Room creation, inviting players |
| 4 | Play with friends | Friend system, friend list, invitations |
| 5 | Build your own game | SDK overview, developer opportunity |

---

## Non-Functional Requirements

| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-ONB-001 | Usability | The wizard must be fully functional and readable on both desktop and mobile viewports. | Works at 375 px width and above | Post-MVP |
| NFR-ONB-002 | Accessibility | The wizard must be keyboard-navigable and compatible with screen readers (ARIA roles on modal, focus trap while open, focus restored on close). | WCAG 2.1 AA | Post-MVP |
| NFR-ONB-003 | Performance | Pane assets (illustrations) must not block the initial page render. They should be lazy-loaded or bundled separately. | No visible layout shift on open; assets load within 500 ms on a 10 Mbps connection | Post-MVP |

---

## Constraints

| ID | Description |
|----|-------------|
| CON-001 | Frontend is React 19 + TypeScript; the wizard must be implemented within this stack. |
| CON-002 | All onboarding state (seen/unseen) is stored client-side in localStorage. Users who clear browser storage will see the wizard again — this is accepted behaviour. |
| CON-003 | No in-app re-trigger from a Help menu or settings page. The landing page CTA is the only re-entry point for users who want to review the onboarding again. |

---

## Out of Scope

- Animated / Lottie illustrations (deferred as a polish goal)
- Re-trigger from a Help menu or settings page
- Personalised onboarding flows per user type or role
- Server-side tracking of onboarding completion
- A/B testing or analytics on pane completion rates (may be added later)
