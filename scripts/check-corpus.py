#!/usr/bin/env python3
"""Structural checks over the TurnBase documentation corpus.

Four checks, run from the repository root:

  1. links    — every relative markdown link resolves to a file that exists
  2. cites    — every document-qualified requirement ID is DEFINED in that document
  3. sections — every "`doc.md` §N" reference resolves to a real heading
  4. index    — every file under docs/ is registered in its nearest INDEX.md

Checks 2 and 3 are the ones that have historically found real defects: the
2026-08-16 round found 19 mis-qualified citations and a requirement range
naming two IDs that do not exist.

Check 2 turns on the difference between DEFINING an ID and CITING it. A
requirements document defines an ID in a table row; every other mention is a
citation. Fifty IDs collide across the corpus, so a qualifier that names a
document which merely discusses the requirement is wrong, and is worse than a
bare ID -- see docs/requirements/INDEX.md.

Exit status is 1 if any check fails, so CI and pre-flight both work:

    python3 scripts/check-corpus.py            # all checks
    python3 scripts/check-corpus.py links      # one check
"""

from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
EXTRA = ["CLAUDE.md", "STATUS.md"]

# A requirement identifier: FR-ROOM-001, NFR-SEC-003, CON-012, OQ-002, VW-JOIN-001, IR-24.
ID = r"(?:FR|NFR|CON|OQ|VW|IR)-[A-Z]+-\d+[a-z]?|(?:CON|OQ|IR)-\d+[a-z]?"

LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
# `some-doc.md` optionally followed by a §-reference, then a run of requirement IDs.
# The tail stops at a backtick, a newline or a `|`: in a table, the document and the
# requirement usually sit in different columns and are unrelated to each other.
QUALIFIED = re.compile(r"`([\w./-]+\.md)`([^`\n|]{0,200})")
IDS = re.compile(ID)
# "§5", "§5.1", "§§3-8" -- the second form appears in read-lists.
SECTION = re.compile(r"§§?\s?(\d+(?:\.\d+)*)")
HEADING = re.compile(r"^#{1,6}\s+(.*)$", re.M)


def markdown_files() -> list[str]:
    out = []
    for d, _, fs in os.walk(DOCS):
        out += [os.path.join(d, f) for f in fs if f.endswith(".md")]
    out += [os.path.join(ROOT, f) for f in EXTRA]
    return sorted(out)


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT)


def read(p: str) -> str:
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def strip_code(text: str) -> str:
    """Remove fenced code blocks. Sample JSON and SQL are not citations."""
    return re.sub(r"```.*?```", "", text, flags=re.S)


def is_review(path: str) -> bool:
    """Closed review rounds quote defective citations on purpose.

    A correction table reads "`notifications-invitations.md` FR-ALERT-006 ->
    **FR-ALERT-010**": the wrong pairing is the finding, and rewriting it would
    destroy the record. Reviews are excluded from the citation check only.
    """
    return os.path.join("docs", "reviews") in path


# --------------------------------------------------------------------------- 1

def check_links(files: list[str]) -> list[str]:
    bad = []
    for p in files:
        for m in LINK.finditer(read(p)):
            target = m.group(1).strip()
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = target.split("#")[0]
            if not target:
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(p), target))
            if not os.path.exists(resolved):
                bad.append(f"{rel(p)}: broken link -> {m.group(1)}")
    return bad


# --------------------------------------------------------------------------- 2

def definitions(path: str) -> set[str]:
    """IDs a document DEFINES: those it introduces as a table row or heading.

    Citations appear mid-sentence; definitions start a table cell or heading.
    """
    text = read(path)
    found = set()
    for line in text.splitlines():
        s = line.strip().replace("~~", "")  # a resolved OQ is struck through, not removed
        if s.startswith("|"):
            first = s.split("|")[1].strip().strip("*` ~")
            if re.fullmatch(ID, first):
                found.add(first)
        elif s.startswith("#"):
            for cand in IDS.findall(s):
                found.add(cand)
        else:
            # Open questions are declared as a bullet, bolded or bare:
            #   "- **OQ-001 — Title.** prose"   /   "- OQ-001: prose"
            m = re.match(rf"^[-*]\s+\*{{0,2}}({ID})\b", s)
            if m:
                found.add(m.group(1))
    return found


def check_cites(files: list[str]) -> list[str]:
    defs: dict[str, set[str]] = {}
    by_name: dict[str, list[str]] = {}
    for p in files:
        defs[p] = definitions(p)
        by_name.setdefault(os.path.basename(p), []).append(p)

    bad = []
    for p in files:
        if is_review(p):
            continue
        text = strip_code(read(p))
        for m in QUALIFIED.finditer(text):
            name, tail = os.path.basename(m.group(1)), m.group(2)
            # Only the run of IDs immediately following the document reference.
            head = re.match(r"[^A-Za-z]*((?:" + ID + r"|[\s,;…\.\-and]){0,200})", tail)
            cited = IDS.findall(head.group(1)) if head else []
            if not cited:
                continue
            targets = by_name.get(name)
            if not targets:
                continue  # a file outside docs/; check_links already covers existence
            known = set().union(*(defs[t] for t in targets))
            for cid in cited:
                if cid in known:
                    continue
                # Sub-duty convention (docs/specs/INDEX.md): FR-JOB-007a…e are the
                # lettered duties of FR-JOB-007 and are not defined separately.
                if cid[-1].isalpha() and cid[:-1] in known:
                    continue
                bad.append(f"{rel(p)}: `{name}` does not define {cid}")
    return bad


# --------------------------------------------------------------------------- 3

def sections(path: str) -> set[str]:
    out = set()
    for h in HEADING.findall(read(path)):
        m = re.match(r"(\d+(?:\.\d+)*)\.?\s", h.strip())
        if m:
            out.add(m.group(1))
    return out


def check_sections(files: list[str]) -> list[str]:
    secs = {os.path.basename(p): sections(p) for p in files}
    bad = []
    for p in files:
        text = strip_code(read(p))
        for m in QUALIFIED.finditer(text):
            name, tail = os.path.basename(m.group(1)), m.group(2)
            head = re.match(r"[^A-Za-z§]*((?:§§?\s?[\d.]+|[\s,;and–—-]){0,80})", tail)
            if not head:
                continue
            if name not in secs or not secs[name]:
                continue
            for ref in SECTION.findall(head.group(1)):
                # "§5.1" is satisfied by a 5.1 heading; "§5" by 5 or any 5.x.
                if ref in secs[name]:
                    continue
                if any(s.startswith(ref + ".") for s in secs[name]):
                    continue
                # "§9.3" may address item 3 of a numbered list under a §9 that has
                # no subheadings -- game-asset-serving.md §9 Invariants is written
                # that way. A parent that exists resolves for a reader.
                if "." in ref and ref.rsplit(".", 1)[0] in secs[name]:
                    continue
                bad.append(f"{rel(p)}: `{name}` has no §{ref}")
    return bad


# --------------------------------------------------------------------------- 4

def check_index(files: list[str]) -> list[str]:
    bad = []
    for p in files:
        if not p.startswith(DOCS):
            continue
        base = os.path.basename(p)
        if base == "INDEX.md":
            continue
        d = os.path.dirname(p)
        # The nearest INDEX.md at or above this file, within docs/.
        idx = None
        while d.startswith(DOCS):
            cand = os.path.join(d, "INDEX.md")
            if os.path.exists(cand):
                idx = cand
                break
            d = os.path.dirname(d)
        if idx is None:
            bad.append(f"{rel(p)}: no INDEX.md anywhere above it")
            continue
        if base not in read(idx):
            bad.append(f"{rel(p)}: not registered in {rel(idx)}")
    return bad


# --------------------------------------------------------------------------- 5

REGISTRY = os.path.join(DOCS, "implementation", "registry.md")
ITEM = r"IMP-M\d+-\d+"
STATUSES = {"BLOCKED", "READY", "WIP", "REVIEW", "DONE", "CANCELLED"}


def check_registry(_files: list[str]) -> list[str]:
    """The two invariants of docs/implementation/INDEX.md 'Where status lives'.

    1. Every ID in the register table has a section, and every section a row.
    2. BLOCKED in the table <=> a `Gate:` line in the section.
    """
    if not os.path.exists(REGISTRY):
        return [f"{rel(REGISTRY)}: missing"]
    text = read(REGISTRY)

    rows: dict[str, str] = {}
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip().strip("*~` ") for c in s.split("|")[1:-1]]
        if len(cells) < 5 or not re.fullmatch(ITEM, cells[0]):
            continue
        status = cells[-1].split()[0].strip("*~` ") if cells[-1] else ""
        rows[cells[0]] = status

    sections_seen: dict[str, str] = {}
    for m in re.finditer(rf"^###\s+.*?({ITEM}).*?$", text, re.M):
        start = m.end()
        nxt = re.search(r"^###\s", text[start:], re.M)
        sections_seen[m.group(1)] = text[start: start + (nxt.start() if nxt else len(text))]

    bad = []
    for iid, status in sorted(rows.items()):
        if status not in STATUSES:
            bad.append(f"{rel(REGISTRY)}: {iid} has unknown status {status!r}")
        if iid not in sections_seen:
            bad.append(f"{rel(REGISTRY)}: {iid} is in the register with no section")
    for iid in sorted(sections_seen):
        if iid not in rows:
            bad.append(f"{rel(REGISTRY)}: {iid} has a section but no register row")

    for iid, body in sorted(sections_seen.items()):
        gated = re.search(r"^\*\*Gate:\*\*", body, re.M) is not None
        blocked = rows.get(iid) == "BLOCKED"
        if gated and not blocked:
            bad.append(f"{rel(REGISTRY)}: {iid} has a Gate: line but is not BLOCKED")
        if blocked and not gated:
            bad.append(f"{rel(REGISTRY)}: {iid} is BLOCKED with no Gate: line")
    return bad


# ---------------------------------------------------------------------------

CHECKS = {
    "links": ("relative links resolve", check_links),
    "cites": ("requirement citations name the defining document", check_cites),
    "sections": ("section references resolve", check_sections),
    "index": ("every document is registered in its nearest INDEX", check_index),
    "registry": ("the register table and the item sections agree", check_registry),
}


def main(argv: list[str]) -> int:
    wanted = argv[1:] or list(CHECKS)
    unknown = [w for w in wanted if w not in CHECKS]
    if unknown:
        print(f"unknown check(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"available: {', '.join(CHECKS)}", file=sys.stderr)
        return 2

    files = markdown_files()
    failed = 0
    print(f"corpus: {len(files)} markdown files\n")
    for name in wanted:
        label, fn = CHECKS[name]
        problems = fn(files)
        mark = "ok  " if not problems else "FAIL"
        print(f"[{mark}] {name:9} {label} — {len(problems)} problem(s)")
        for line in problems:
            print(f"         {line}")
        failed += len(problems)
    print()
    print("clean" if not failed else f"{failed} problem(s) found")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
