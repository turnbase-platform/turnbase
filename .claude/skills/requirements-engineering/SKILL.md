---
name: requirements-engineering
description: Use this skill to run an interactive requirements engineering session. Trigger whenever the user provides a description of what a system, feature, or domain should do and wants to produce structured requirements — even if they don't use the word "requirements". Also trigger on phrases like "define requirements", "let's spec out", "what should X do", "help me document X", or when the user pastes a system description and asks Claude to help structure it. When in doubt, trigger — this skill helps gather requirements before writing a single line of code.
---

# Requirements Engineering

You are facilitating an interactive requirements engineering session. The user has described a system or domain. Your job is to guide them to a complete, structured requirements document through systematic analysis and clarification.

## Process

### Phase 1 — Domain Analysis

Analyze the description and briefly present (use bullet points, keep it concise):

- **Stakeholders & user roles** — who uses or is affected by this system
- **System boundary** — what is explicitly in scope vs. out of scope (note anything ambiguous)
- **Key entities & concepts** — the core nouns and their relationships
- **Implicit assumptions** — things assumed or implied that need validation

Do not ask questions yet. Present the analysis, then immediately move to Phase 2.

### Phase 2 — Clarification Rounds (iterative)

Ask focused, grouped questions to resolve ambiguities. Rules:
- Max 6 questions per round — wait for answers before the next round
- Group related questions under a topic heading (e.g. "About authentication:", "About the game lifecycle:")
- Stop when you have enough clarity to write a complete, unambiguous spec
- If the user's answer raises new questions, include them in the next round

Cover these areas across rounds (not all in one round):
- **Functional scope** — what must the system do? What are the primary user flows?
- **Non-functional requirements** — performance, security, availability, scalability expectations
- **Constraints** — technology choices already made, compliance, external integrations
- **Edge cases & failure modes** — what should happen when things go wrong?
- **User experience** — key UX expectations, anti-patterns to avoid, accessibility needs

### Phase 3 — Requirements Specification

Once clarification is sufficient, produce the requirements document using this structure:

```markdown
# [Domain Name] Requirements

## Stakeholders
| Role | Description |
|------|-------------|
| [Role] | [What they do / need from the system] |

## Functional Requirements
| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-[CAT]-001 | [Short title] | [Clear, testable description of what the system must do] | Must / Should / Could |

## Non-Functional Requirements
| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-[CAT]-001 | Performance / Security / Scalability / Availability / Usability / ... | [What quality attribute] | [Measurable target] | Must / Should |

## Constraints
| ID | Description |
|----|-------------|
| CON-001 | [Hard constraint — technology, compliance, budget, timeline, etc.] |

## Out of Scope
- [Explicit exclusions agreed during clarification]

## Open Questions
- [Decisions or clarifications still needed — flag these, don't guess]
```

**Priority scale (MoSCoW):**
- **Must** — non-negotiable; system fails without it
- **Should** — important but not blocking launch
- **Could** — nice to have; cut if needed

**ID format:** `[DOMAIN]-[CATEGORY]-[NUMBER]` — use short category codes meaningful to the domain.

Examples: `FR-AUTH-001`, `FR-ROOM-001`, `NFR-PERF-001`, `CON-001`

**Writing good requirements:**
- Functional requirements describe *what*, not *how* — avoid implementation details
- Non-functional targets must be measurable ("respond within 200ms p95", not "fast")
- Each requirement should be independently testable — if you can't write a test for it, it's too vague
- When a requirement is complex or contentious, split it or move it to Open Questions

### Phase 4 — Review & Save

Present the full document for review. Iterate on any section until the user confirms it is complete.

Once confirmed, save to:
```
docs/requirements/[domain-name].md
```

Use lowercase kebab-case for the filename (e.g., `user-authentication.md`, `game-rooms.md`, `game-sdk.md`).

Remind the user they can use `#` in the session to have Claude incorporate learnings back into the requirements document.
