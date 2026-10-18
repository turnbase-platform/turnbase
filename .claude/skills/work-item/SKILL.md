---
name: work-item
description: Use when implementing any TurnBase IMP-* work item — starting one, resuming one, or asked to "build IMP-M0-03", "do the Flyway baseline", "pick up the next item", or "what should I work on next". Also use before writing any code in turnbase-platform, turnbase-game-host, turnbase-frontend, turnbase-sdk or turnbase-common, even when the request names a feature rather than an item ID. Triggers on work-item IDs, milestone names (M0-M6), and any TurnBase Phase 1 coding task.
---

# Working a TurnBase work item

The registry decided what to build and how you know it is finished. Your job is to execute one item
without re-deciding anything it already settled, and to leave the register honest about what happened.

## Why this has a procedure at all

Phase 1 is ~59 items across many sessions, in five repositories, executed largely by agents reading
one item at a time. Nobody holds the whole system in their head — that is the design, not a
limitation. It works only if two things stay true: **the read-list is sufficient**, and **the
register reflects reality**. Both degrade silently unless each item maintains them, which is what the
steps below are actually for.

## The loop

### 1. Find the item and check it can start

Open `docs/implementation/registry.md`. Read the item's section and its row in the register table.

**When choosing, a `PARTIAL` item comes before any `READY` one.** It is half-built, and starting
something new beside it is how an item stays half-built for good. Its `**Remaining:**` line is where
you start. Check that line against the repository before trusting it, because it is one session's
account of what exists. Session 92's said no compose stack existed when `IMP-M0-07` had built one.
A `PARTIAL` item whose *Depends on* is not all `DONE` waits like any other — `IMP-M10-01` waits on
`IMP-M11-08`.

Every ID under *Depends on* must be `DONE`. If one is not, say so and stop rather than working around
it — the dependency graph is the reason the milestones are ordered as they are, and an item built
against a missing dependency usually looks finished until the dependency lands and contradicts it.

### 2. Claim it in the register

Change the row's status `READY` (or `PARTIAL`) → `WIP (session N)`. **Commit that with your first
real change, not at the end.** A status written from memory hours later is a guess, and the
register is the only protection against two sessions picking up the same item.

### 3. Read exactly the read-list — and nothing else

The *Read first* list is the **minimum set of documents that fully determines the item**. Read all of
it, in the order given where an order is given.

`docs/implementation/conventions.md` is assumed everywhere and not repeated in read-lists — package
layout, Spotless, test suffixes, JaCoCo, branch and commit format, cross-repo pinning. So is the
submodule's own `CLAUDE.md`.

**If you find yourself needing a document the list does not name, that is a defect in the registry.**
Read what you need — but add it to the item's read-list in the same session. The list is a claim about
sufficiency, and an unrepaired gap costs every future reader the same detour you just took.

Resist reading further "for context". Breadth is what the registry exists to spare you, and a
half-remembered spec you skimmed is more dangerous than one you never opened.

### 4. Work in the right place

Check the item's **Repo** field. Branch per ADR-0012: `feat/`, `fix/`, `docs/` or `chore/` +
description, off `master`. Commits are Conventional Commits.

**Do not open a pull request** (ADR-0012, amended 2026-09-05). The branch is merged into `master`
and deleted **in the session that created it** — prefer `--ff-only`, and delete it on the remote too.
A branch that outlives its session is the thing this rule exists to prevent, so if the work is not
green by the end of the session, leave it unmerged rather than parking it as a PR.

Cross-repo changes are separate branches per repo — there is no atomic multi-repo commit. If your
item touches `turnbase-common` and a consumer, the order is in `conventions.md` §5.

### 5. Build it, tests first

Write the test that expresses the *Done when* clause before the code that satisfies it. The clauses
were written to be checkable without judgement precisely so they could be turned into assertions.

### 6. Check the *Done when* clause by clause

Not "does it work" — **does each clause hold, demonstrably**. The clause is the contract; your
impression of completeness is not. Where a clause names an exact behaviour (a status code, a header,
a response body, a specific index) assert that exact thing.

If a clause turns out to be unsatisfiable as written, that is a specification defect — see below.

### 7. Green before you merge

```bash
./mvnw spotless:apply        # or: npm run format
./mvnw verify                # unit, plus Modulith verification in the platform repo
./mvnw verify -Pintegration  # Testcontainers
```

Run `spotless:apply` **before** merging, not after CI rejects it. A bounced pipeline costs one turn
to discover and another to fix, and with no PR in front of it the bounce lands on `master`.

### 8. `DONE` means green and bumped

An item is not `DONE` because the code exists. It is `DONE` when the pipeline is green **and** the
submodule ref in the parent repo is updated. Then set the register row to `DONE` and drop the session
marker.

If the item changed anything under `docs/`, `python3 scripts/check-corpus.py` before committing.

**Only if your session prompt contains a `CI policy for this run` paragraph** (the loop's `--skip-ci-wait`; no such paragraph means the flag is off, whatever STATUS.md or the registry say about earlier sessions) do not `gh run watch`: `DONE`
means the *Done when* clause holds from local `spotless:apply`, `verify` and `verify -Pintegration`,
`master` is pushed and the ref bumped. Two item-level lines override that, and the item's section is
authoritative: `**CI wait:** required` means wait for the pipeline anyway, and `**Build on exit:** may
be red` (M11 only, ADR-0016 §4) means the item may leave the named part of the build failing — still
merge, push and bump, and say in STATUS.md what is red.

### 9. Or `PARTIAL`: when the session ends before the item does

One session often cannot build a whole item. That is fine, and it is not `DONE`. Marking it `DONE`
would make every dependent look ready to start on work that does not exist. When the clause does not
hold by the end of the session:

1. Merge what is green, exactly as for `DONE`: pipeline green, ref bumped, branches deleted. Leave
   anything that is not green unmerged and unpushed.
2. Set the register row to `PARTIAL` and drop the session marker.
3. Write, or replace, the one `**Remaining:**` line in the item's section: what the *Done when*
   clause still lacks, concretely enough that the next session can start on it without
   re-deriving it. Format in `INDEX.md` *Partly done items*.
4. Record it in `STATUS.md` like any other session, and report `LOOP_STATUS: PARTIAL <item> <what is
   owed>` when running under the loop.

Do not leave the item `READY` with a prose note instead. A `READY` row says nothing is owed, and a
note is invisible to whoever picks by status.

**If something outside the item stops what is still owed from being built,** do not end on
`PARTIAL`: nothing a later session can do would change the outcome. That is a registry defect.
Examples are a missing environment, a clause another item also claims, or a caller only a later item
builds. Use `spec-defect`: either open a gate (`BLOCKED`), or move the remainder to the item that
owns it, rewire *Depends on*, and mark this one `DONE` if its own clause now holds. First check that
the missing thing really is missing. `IMP-M0-07`'s compose stack was reported absent while it
existed.

When the item finally becomes `DONE`, delete its `**Remaining:**` line.

## Live-environment and measurement items

Some sections carry an `**Environment:**` line (the M15 load-testing items). It overrides the
defaults above where it speaks, and nowhere else.

- **Preflight first.** Run the preflight the line names before anything else. A failed check on the
  cluster (Docker, the `docker-desktop` context, a Ready node, Helm, ingress) is `BLOCKED`, naming the
  failed command, but only after you run that command again live and it still fails. A
  git-ignored secrets file that is missing is generated from its `*.example`; that is setup, not a
  blocker, and neither is a missing local image (build it).
- **Long commands.** One shell call is capped at ten minutes and the loop warns after fifteen without
  output. A command expected to take more than eight minutes runs in the background, and you poll its
  output at most every five minutes, emitting a `LOOP_PHASE` line each time. Never end the turn to
  "check back".
- **Umbrella-only items** (**Repo:** `turnbase`, "nothing to bump") have no submodule, so there is no
  ref to bump and no pipeline to wait for: the umbrella repository has no CI workflow. `DONE` means the
  *Done when* clause holds, `check-corpus.py` is clean, and `master` is pushed. Do not `gh run watch`. An item that also lists a component repository (`IMP-M15-07` changes the chart in
  `turnbase-platform`) is not umbrella-only: that part follows §8 as usual.
- **Measurement items** (a section that says "measurement only") record what the system does. No code,
  chart or overlay change, whatever the numbers are, and a bad number is a result, not a failure. A
  finding goes into the run's report and into the list the section names, and does not become a new
  registry item. The item is `DONE` when the reports exist and are complete, not when the system passes.
- **Owner-reserved decisions.** When a section says to *record* a conflict rather than resolve it,
  write the open question where the section says (an `OQ-*` entry in the owning document's *Open
  questions*). That is not a `Gate:` line and the row does not become `BLOCKED`. Do not choose a side.

## When the documents fail you

Two documents contradict each other, or the item leaves you a decision that should have been made —
**stop and open a gate.** Do not pick whichever reading makes the code work.

**REQUIRED: use the `spec-defect` skill.** It is a short procedure and it exists because the failure
mode here is quiet: you resolve the conflict sensibly, nothing records that a choice was made, and
the contradiction is still there for the next person to resolve the other way.

## Things that look like progress and are not

| Tempting | Why it costs more than it saves |
|---|---|
| Reading adjacent specs "to understand the context" | The read-list is the determining set. Extra reading dilutes it and encourages inventing consistency the corpus does not have. |
| Writing the status at the end of the session | You will write what you remember, not what happened. Unclaimed `WIP` is how two sessions collide. |
| Marking `DONE` with a green local build | The bar is the pipeline and the ref bump. A local pass says nothing about a clean machine. |
| Fixing a spec inconsistency quietly in code | The next item hits the same inconsistency and fixes it the other way. Now two subsystems disagree and neither is wrong. |
| Adding a REST route "just for this" in M2 | A second writer outside the per-room serialization destroys the ordering guarantee the whole milestone rests on. |
| Skipping `spotless:apply` because the diff is small | Format failures are the cheapest possible CI failure and the most annoying to round-trip. |
| Leaving an unfinished item `READY` with a note, or calling it `DONE` | `READY` hides the leftovers from whoever picks by status, and `DONE` unblocks dependents early. Use `PARTIAL` with a `**Remaining:**` line. |
| Leaving the branch unmerged "to finish next session" | That is exactly how eight PRs and eleven dead branches accumulated by 2026-09-05. Merge it or leave it unpushed. |

## Quick reference

| | |
|---|---|
| Registry | `docs/implementation/registry.md` — items; `INDEX.md` — status vocabulary, gate format |
| Conventions | `docs/implementation/conventions.md` — assumed, never in a read-list |
| Corpus checks | `python3 scripts/check-corpus.py` after any `docs/` change |
| Branch / commits | ADR-0012 — `feat/…` off `master`, Conventional Commits, **no PRs**; merge and delete in-session |
| Blocked | `spec-defect` skill |
