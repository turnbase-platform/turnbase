---
name: spec-defect
description: Use the moment two TurnBase specification documents disagree, or a spec leaves a decision to the implementer, or a "Done when" clause cannot be satisfied as written, or an implementation needs a value/name/rule that no document supplies. Especially use when tempted to pick whichever reading makes the code work, reconcile a contradiction in code, note an inconsistency and carry on, or infer a config key or column that no spec names. Triggers on contradictory specs, missing definitions, unsatisfiable acceptance criteria, and anything underspecified found while implementing.
---

# A specification defect is not an implementation problem

When the documents contradict each other or leave you a decision they should have made, the fix goes
in the **specification**, in the parent repository — then the code follows from it.

## Why stopping is the cheap option

The tempting move is to resolve it sensibly and keep going. You are on an item, the conflict is
small, one reading obviously works better, and stopping feels like ceremony.

Here is what that costs. The contradiction is still in the corpus. Nothing recorded that a choice was
made or why. Three milestones later another item hits the same two documents and resolves it the
*other* way — equally sensibly. Now two subsystems disagree, both were built as specified, and
neither can be called the bug. Someone spends a day discovering that the specification was ambiguous
all along.

That day is the thing you are avoiding. Writing the gate takes ten minutes.

**This corpus has already been through it.** The 2026-08-16 audit found 23 blockers, and its worst
findings were not wrong statements — they were places where two individually correct documents
combined into something impossible. Those are cheap to fix in a document and expensive to discover in
running code.

## Is it a gate?

**Yes — the documents are at fault:**
- Two documents state incompatible things about the same behaviour.
- A document leaves a decision to you that will be visible in behaviour or in a data shape.
- You need a name, value, key or column that no document supplies.
- A *Done when* clause cannot be satisfied as written.
- An item's read-list is missing a document the item genuinely requires. *(Repair the list; that one
  usually needs no gate.)*

**No — this is ordinary work:**
- The item is hard, large, or tedious.
- You disagree with a decision the documents made clearly. Then it is a decision to reopen with the
  owner, not a defect. Say so plainly rather than routing it through a gate.
- Two documents use different words for the same thing and mean the same thing.

**If you are weighing whether it clears the bar, it clears the bar.** The cost of an unnecessary gate
is a paragraph someone reads and closes. The cost of a missed one is above.

## Opening it — three things, together

None of them counts alone.

### 1. The `Gate:` line, in the item's section in `registry.md`

```
**Gate:** <ID> — <the contradiction, in one sentence>.
Opened <YYYY-MM-DD>. Fix belongs in `<document>`.
```

`<ID>` is an existing `OQ-*` where one already covers it, otherwise a new `IMP-GATE-<nn>`.

Set the item's row in the register table to `BLOCKED`. `scripts/check-corpus.py registry` enforces
that these two agree, so a half-opened gate fails the check.

### 2. The fix, in the specification

Not in the code. Not in a comment recording what the code assumed. **In the document**, in the parent
repository, where the next reader will meet it before writing anything.

Which document owns it is usually obvious from which one is wrong. When both are, the one that
*defines* the requirement wins — `docs/requirements/INDEX.md` is the lookup, and a wrong qualifier is
worse than a bare ID.

Fix the general case, not just the instance you hit. If the flagship example violates a rule stated
sixty lines above it, ask whether the rule is satisfiable at all — sometimes the example is right and
the rule is impossible, and correcting only the example leaves everyone else the same trap.

### 3. A line in `STATUS.md`, under *Next Priorities*

A gate recorded only in the registry is invisible to whoever reads `STATUS.md` at the start of the
next session — which is everyone, every time.

## Closing it

When the specification is fixed: remove the `Gate:` line, return the row to `READY`, and add a
`**Closed:**` line saying where the fix landed. Then the item can proceed.

If you fixed the spec in the same session you opened the gate, still write both. The record of *why
the document says what it says* is the durable part, and it is worth more than the ten minutes.

## What good looks like

**Situation:** `IMP-M0-06`, transcribing the Flyway baseline. Two schema documents describe the same
table's primary key with different auto-increment idioms.

**Wrong:** pick `bigint GENERATED ALWAYS AS IDENTITY` because it is the better choice, write the
migration, move on. It *is* the better choice — and nothing now records that the other document still
says otherwise, so the next person to read that document writes `bigserial` somewhere else.

**Right:** stop. `Gate:` on `IMP-M0-06`, row to `BLOCKED`, line in `STATUS.md`. Then fix the schema
documents so they state one idiom — checking whether any *other* table in either document has the
same split, because if two documents disagreed once they usually disagree more than once. Close the
gate, then write the migration from documents that agree.

The migration is identical either way. The difference is entirely in what the corpus says afterwards.

## Related

- `docs/implementation/INDEX.md` — status vocabulary, the `Gate:` format, what is and is not a gate
- `docs/requirements/INDEX.md` — which document *defines* which requirement prefix
- `scripts/check-corpus.py` — run after editing any document
- `work-item` skill — the surrounding cadence
