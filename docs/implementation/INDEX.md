# Implementation Registry

The tracker for building TurnBase v1. One row per unit of implementable work, each pointing at the
documents that already decided how it behaves.

## What this directory is for

`docs/requirements/` says **what** the system must do. `docs/specs/` says **how** it is designed.
Neither says **what to build next, in what order, and how you know it is finished.** That is this
document.

It exists because Phase 1 is executed largely by implementation agents running at low reasoning
effort. Such an agent is good at writing code against a precise brief and bad at reconstructing
architecture from seventeen requirements documents. Every work item below therefore carries an
explicit **Read first** list — the minimum set of documents that fully determine the item — and a
**Done when** clause that is checkable without judgement.

If you are an implementation agent: find your work item, read exactly the documents it names, and
build exactly what the *Done when* clause describes. If the documents contradict each other or leave
a decision to you, **stop and escalate** — do not choose. An unrecorded choice made here is a defect
that surfaces three milestones later. Record it against the item's *Gate* field.

## Files

| File | Purpose |
|------|---------|
| [INDEX.md](INDEX.md) | This file — registry conventions, the milestone map, and how to read a work item |
| [conventions.md](conventions.md) | **Code and build conventions** — package layout, formatting, tests, coverage, git, cross-repo versions. Normative, and shared by every item |
| [registry.md](registry.md) | The register itself, and the per-item detail: read-lists, requirements satisfied, done-when clauses |

## Related

- [`../reviews/2026-08-16-implementation-readiness/INDEX.md`](../reviews/2026-08-16-implementation-readiness/INDEX.md) — the audit that qualified this corpus for implementation. All 23 of its blockers are closed; two findings raised *during* remediation (IR-24, IR-25) remain open and are documentation defects, not gates.
- [`../reviews/2026-10-01-mvp-implementation-review/INDEX.md`](../reviews/2026-10-01-mvp-implementation-review/INDEX.md) — black-box run of the MVP stack: the API and Game Host work, but the frontend room views are placeholders (MR-01) and `IMP-M6-04`/`05` are `DONE` without satisfying their `VW-*` entries.
- [`../reviews/2026-10-03-mvp-regression-review/INDEX.md`](../reviews/2026-10-03-mvp-regression-review/INDEX.md) — second black-box run after `IMP-M7-01…13`: the play loop works and 10 of 11 first-review findings are closed, but Profile/Settings/Friends return 500 (RR-01, RR-02), a forfeit writes no history (RR-03) and rooms emptied around a game end are not closed (RR-04).
- [`../specs/INDEX.md`](../specs/INDEX.md) — design specifications.
- [`../specs/flows/INDEX.md`](../specs/flows/INDEX.md) — read the relevant flow before starting any item that spans components.

---

## Conventions

### Item identifiers

`IMP-<milestone>-<nn>`, e.g. `IMP-M1-03`. Identifiers are permanent; a cancelled item is struck
through rather than renumbered, and its number is never reused.

### Status vocabulary

| Status | Meaning |
|---|---|
| `BLOCKED` | A gate is open. The item cannot start. The gate is named in the item's *Gate* field. |
| `READY` | All gates closed, all dependencies `DONE`. An agent may pick this up now. |
| `WIP` | In progress. The owning session or agent is named. |
| `PARTIAL` | Part of the item is merged, but its *Done when* clause does not hold yet. The item's `**Remaining:**` line says what is still owed. It is picked up before any `READY` item. |
| `REVIEW` | Code complete, awaiting a passing pipeline. |
| `DONE` | Merged, tests green, and — if the item touches a submodule — the submodule ref in this repo is updated. |
| `CANCELLED` | The requirement it implemented was cut. The heading is struck through and kept; the number is never reused. |

### Where status lives, and who writes it

**The register table at the top of [`registry.md`](registry.md) is the only place status is
recorded.** Item sections do not repeat it — two copies of a status is one copy that is wrong.

**Whoever works the item writes the status, at the moment the transition happens, in the same commit
as the work.** Not at the end of the session, and not from memory afterwards:

| Transition | When | Also do |
|---|---|---|
| `READY` → `WIP` | Before the first edit, not after | Append ` (session N)` to the status cell |
| `WIP` → `PARTIAL` | The session ends with work merged but the *Done when* clause not yet holding | Drop the session marker; add or replace the `**Remaining:**` line in the item's section |
| `PARTIAL` → `WIP` | Before the first edit of the session that continues it | Append ` (session N)`; keep the `**Remaining:**` line until the item is `DONE` |
| `WIP` → `REVIEW` | Code complete, merged to `master`, pipeline running | — |
| `REVIEW` → `DONE` | Pipeline green **and** the submodule ref bumped here | Drop the session marker and any `**Remaining:**` line |
| any → `BLOCKED` | The moment a gate opens | Add the `Gate:` line to the item's section |

A status is a claim about the world, so the same rule applies to it as to a *Done when* clause: do
not write `DONE` because the code exists. Write it when the pipeline is green and the ref is bumped.

**Three invariants, checked mechanically by `scripts/check-corpus.py registry`:**

1. Every ID in the register table has a section below, and every section has a table row.
2. `BLOCKED` in the table ⟺ a `Gate:` line in the section. Neither can exist without the other.
3. `PARTIAL` in the table ⟹ a `**Remaining:**` line in the section, and a `**Remaining:**` line
   exists only on a `PARTIAL`, `WIP` or `BLOCKED` item. A `DONE` item owes nothing.

The second one is what stops a gate from being carried in someone's head, and it is why the `Gate:`
line is a format rather than a note.

### Partly done items

An item often takes more than one session. Ending a session with part of it merged is normal; marking
it `DONE` early is not, because its dependents then look ready to start on work that does not exist
yet. So the session sets the item to `PARTIAL` and says, in one line in the item's section, what is
still owed:

```
**Remaining:** <what the Done when clause still lacks, concrete enough to start on>. (session <N>)
```

There is one such line per item. The next session replaces it rather than adding another, and the
line is removed when the item becomes `DONE`. The whole history belongs in commits and `STATUS.md`,
not here.

A `PARTIAL` item is picked up before any `READY` one, so that no item stays half-built while others
are started. If what is still owed cannot be built because something outside the item is missing,
that is a gap in the registry, not a reason to leave the item `PARTIAL`: open a gate (below), or add
the missing item and make this one depend on it.

### The `DONE` bar

Per `CLAUDE.md`, a submodule ref in this repo is updated **only after** that submodule's build and
tests pass. An item is not `DONE` because the code exists; it is `DONE` when the pipeline is green
and the ref is bumped.

### Gates

A **gate** is an open question or audit finding that must be resolved before the item can be built
correctly. Gates cite the audit finding ID from
[`../reviews/2026-08-16-implementation-readiness/INDEX.md`](../reviews/2026-08-16-implementation-readiness/INDEX.md)
or an `OQ-*` in a spec. An item with an open gate is `BLOCKED`, and the fix belongs in the
**specification**, not in the code.

**No item is currently gated.** A `Gate:` line appears on an item only when one is open, so its
absence means what it says. If you open one while implementing, add the line and change the status —
do not carry the gate in your head.

#### Opening a gate — the format

```
**Gate:** <ID> — <the contradiction, in one sentence>.
Opened <YYYY-MM-DD>. Fix belongs in `<document>`.
```

`<ID>` is a spec's `OQ-*` when one already covers it, or a new `IMP-GATE-<nn>` when nothing does.

**Three things happen together, or none of them count:**

1. The `Gate:` line lands in the item's section and its register row becomes `BLOCKED`.
2. **The fix goes into the specification**, in this repository — not into the code, and not into a
   comment explaining what the code assumed.
3. A line appears under *Next Priorities* in `STATUS.md`, because a gate that only exists in the
   registry is invisible to whoever reads STATUS.md at the start of the next session.

#### What is and is not a gate

A gate is **the documents disagreeing, or leaving you a decision they should have made.** It is not a
task being hard, and it is not you disagreeing with a decision the documents made clearly.

The failure this exists to prevent is silent reconciliation: two documents conflict, you pick the one
that makes the code work, and nothing records that a choice was made. That choice surfaces three
milestones later as behaviour nobody can trace to a decision — and by then both documents still
disagree, so the next person makes the opposite choice somewhere else.

**Stopping is cheap. An unrecorded choice is not.** If you are weighing whether something clears the
bar, it clears the bar.

### What every item does *not* carry

[`conventions.md`](conventions.md) holds what is true for every item: package layout, formatting,
test suffixes and their plugins, the coverage wiring, the branch and commit format, and how the
repositories depend on each other. It is **not** repeated in read-lists — assume it, the way you
assume `CLAUDE.md`. An item names it explicitly only where that item is the one *establishing* the
convention rather than following it.

If you find yourself deciding something that reads like it should be the same across all forty
platform items, the answer belongs in `conventions.md` and its absence is a defect. Do not settle it
locally.

### What every item carries

Four fields, and they mean different things:

| Field | Contract |
|---|---|
| **Read first** | The minimum document set that fully determines the item. An implementation agent should not need to read anything outside it. If you do, that is a defect in the registry — record it. |
| **Satisfies** | The requirement IDs the item implements, document-qualified. Several IDs are reused across documents with unrelated meanings, so the bare ID is ambiguous and the qualifier is not decoration. |
| **Done when** | Checkable without judgement. If two people could disagree about whether it holds, it is written wrong. |
| **Gate** | Present only when something is open. |

Items also carry short **notes** where a spec contains a trap that a correct-looking implementation
walks straight into. Those notes are not summaries — they are the parts most likely to be got wrong,
pulled forward so a low-effort reader meets them before writing code rather than after.

---

## Milestone map

Ordering follows the dependency graph rather than document order, per `STATUS.md`.

| Milestone | Theme | Rationale for its position |
|---|---|---|
| **M0** | Repositories, local stack, schema baseline | Nothing can be built or run until `docker compose up` yields a migrated, seeded database. The baseline is also the first real test of whether the six schema documents are mutually consistent. |
| **M1** | Accounts, sessions, auth | The shortest vertical slice that exercises REST, Postgres, Redis and the rate limiter. Everything downstream needs a principal. |
| **M2** | Rooms and the realtime protocol | The most thoroughly specified and most subtle machinery in the corpus. Built before the catalog so the hard part is behind the easy part. |
| **M3** | Game Host and the first official game | ADR-0006 makes the MVP official-only, so the first game is simultaneously the proof that the GDK contract works. |
| **M4** | Catalog, upload, asset serving | Depends on M3 for a bundle worth validating. |
| **M5** | History, statistics, notifications, social | The CRUD tail. Order within it is a convenience. |
| **M6** | Platform frontend | Runs **in parallel** from M1 onward, not after M5 — each vertical slice needs a UI to be exercised by hand. Listed last only because its internal ordering follows the backend's. |
| **M7** | MVP review remediation | Added after the 2026-10-01 black-box review: the room views `IMP-M6-04`/`05` left unbuilt, the backend and game defects the review found, and the acceptance suite that re-runs it. |
| **M8** | Regression review remediation and MVP view completeness | Added after the 2026-10-03 regression review: five backend/game fixes (`01…05`), one minimal working UI item per MVP view including the game room (`06…14`), the client retry (`15`) and the acceptance suite that covers all of it (`16`). |

