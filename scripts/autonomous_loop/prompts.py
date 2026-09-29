"""Prompts for loop sessions. Both end with the LOOP_STATUS contract the Stop hook enforces."""

_PHASES = """At each change of phase, put one line in your message text of the form
LOOP_PHASE: <phase> <optional short note>
where <phase> is one of: starting, claiming, reading, implementing, testing,
ci-wait, merging, wrapping-up. When claiming, put the item id in the note
(e.g. `LOOP_PHASE: claiming IMP-M3-04`). Keep notes under 80 characters.
Write each marker as plain text in your message, not inside a command or
tool call, and report every phase you enter, including implementing and
testing. These lines are progress markers for the operator only; they never
replace the final LOOP_STATUS line."""

_STATUS = """PARTIAL means work on the item landed (merged, pushed, ref bumped) but its
"Done when" clause does not hold yet: the register row says PARTIAL and the
item's section has a `**Remaining:**` line, as `work-item` describes. The
next session continues it. Never write DONE for an item that is not DONE.

End your final message with exactly one line, and nothing after it, in one of
these four exact forms:
LOOP_STATUS: DONE <item-id-or-short-label>
LOOP_STATUS: PARTIAL <item-id> <what is still owed, in a few words>
LOOP_STATUS: BLOCKED <one-line reason>
LOOP_STATUS: FINISHED <all items complete>"""

PROMPT = f"""Pick up the next TurnBase Phase 1 work item and implement it, following the
`work-item` skill exactly (claim it, read exactly its read-list, build to the
"Done when" clause). A PARTIAL item in the register comes before any READY
one: continue it from its `**Remaining:**` line. If a specification defect
blocks you, use the `spec-defect` skill instead of guessing — filing/fixing the defect is a valid
unit of work for this session.

Do exactly ONE item (or one spec-defect fix) this session, then stop — do not
chain a second item. Before finishing: run the full "Ending a Session"
checklist from CLAUDE.md (STATUS.md replaced, corpus check clean if docs
changed, submodule refs updated only if build+tests pass, everything
committed, every branch created this session merged into master and deleted
locally, nothing left uncommitted or unmerged).

If the working tree was not clean, or not on master, when you started: stop
immediately without changing anything and report that instead.

This is a single non-interactive turn: there is no later turn in which to
"check back". If you push a submodule commit and need CI to go green before
bumping its ref at the top level, block on it synchronously in one tool call
(e.g. `gh run watch <run-id> --exit-status`) and then finish the rest of the
checklist in the same turn — never end your turn planning to check CI, or
anything else, "once it completes".

{_PHASES}

{_STATUS}"""

def continue_prompt(item: str) -> str:
    """A fresh session after one that reported PARTIAL: the same item comes next."""
    return PROMPT.replace("Pick up the next TurnBase Phase 1 work item", f"""The previous session
left {item} PARTIAL. Continue {item} — not a different item —""", 1)


RESUME_PROMPT = f"""This session was interrupted before it reported a LOOP_STATUS line — it was
killed, cut off by a session limit, or it stopped early. Nothing has been
rolled back for you.

First re-establish where you actually are: check `git status`, the current
branch, whether your work item was committed/merged, and whether any CI run
you were waiting on has since finished. Do not assume the work is unstarted
and do not redo work that is already committed.

A dirty working tree or a feature branch is expected here — it is your own
in-progress work. The original instruction to stop if the tree was not
clean applied only when this session first started; it does not apply to
this resume.

Then either finish the item end-to-end (full "Ending a Session" checklist
from CLAUDE.md) or, if it cannot be finished safely, unwind it cleanly so the
tree is left clean and on master.

Same rule as before: block synchronously on anything you need (e.g.
`gh run watch <run-id> --exit-status`) rather than ending your turn planning
to check back later.

{_PHASES}

{_STATUS}"""


def verify_prompt(problems: list[str], reported: str = "DONE") -> str:
    """Resumes a session whose DONE or PARTIAL the repository does not bear out."""
    listed = "\n".join(f"- {p}" for p in problems)
    return f"""You reported LOOP_STATUS: {reported}, but the loop's post-session checks of the
repository found the "Ending a Session" checklist from CLAUDE.md incomplete:

{listed}

Fix each of these now. If the item is in fact only partly done, do not mark it
DONE: set its register row to PARTIAL, put a `**Remaining:**` line in its
section saying what is still owed, record what landed in STATUS.md, commit and
push that, and report PARTIAL. Do not delete a branch you did not create. Block
synchronously on anything you need, as before.

{_PHASES}

{_STATUS}"""
