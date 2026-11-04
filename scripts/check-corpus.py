#!/usr/bin/env python3
"""Structural checks over the TurnBase documentation corpus.

Eight checks, run from the repository root:

  1. links    — every relative markdown link resolves to a file that exists
  2. cites    — every document-qualified requirement ID is DEFINED in that document
  3. sections — every "`doc.md` §N" reference resolves to a real heading
  4. index    — every file under docs/ is registered in its nearest INDEX.md
  5. registry — register rows and item sections agree (registry.md and archive/)
  6. items    — every cited IMP-Mn-nn identifier resolves to a section
  7. counts   — every count CLAUDE.md states (requirement documents, work items,
                repositories, submodules) equals the number on disk
  8. code-maps — every class, package and path named in an ARCHITECTURE.md (the
                umbrella's and each service's) resolves in the code it maps

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
EXTRA = ["CLAUDE.md", "STATUS.md", "ARCHITECTURE.md"]

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
ARCHIVE = os.path.join(DOCS, "implementation", "archive")
ITEM = r"IMP-M\d+-\d+"
STATUSES = {"BLOCKED", "READY", "WIP", "PARTIAL", "REVIEW", "DONE", "CANCELLED"}


def check_registry(_files: list[str]) -> list[str]:
    """The three invariants of docs/implementation/INDEX.md 'Where status lives'.

    1. Every ID in the register table has a section, and every section a row.
    2. BLOCKED in the table <=> a `Gate:` line in the section.
    3. PARTIAL in the table => a `Remaining:` line in the section, which only a
       PARTIAL, WIP or BLOCKED item may carry.
    """
    if not os.path.exists(REGISTRY):
        return [f"{rel(REGISTRY)}: missing"]
    rows, sections_seen, bad = registry_items()
    return bad + _registry_invariants(rows, sections_seen)


def registry_items() -> tuple[dict[str, str], dict[str, str], list[str]]:
    """Rows and sections of the register AND of every archive file (IMP-M20-01).

    Closed milestones live verbatim in docs/implementation/archive/; an item's
    row and its section must be in the same file, so a half-moved item fails.
    """
    rows: dict[str, str] = {}
    sections_seen: dict[str, str] = {}
    bad: list[str] = []
    files = [REGISTRY] + sorted(
        os.path.join(ARCHIVE, f) for f in os.listdir(ARCHIVE) if f.endswith(".md")
    ) if os.path.isdir(ARCHIVE) else [REGISTRY]
    for f in files:
        r, s = _parse_registry(f)
        for iid in r:
            if iid in rows:
                bad.append(f"{rel(f)}: {iid} has a register row in more than one file")
        for iid in s:
            if iid in sections_seen:
                bad.append(f"{rel(f)}: {iid} has a section in more than one file")
        for iid in set(r) ^ set(s):
            if f != REGISTRY or iid in r:
                bad.append(f"{rel(f)}: {iid} has a {'row' if iid in r else 'section'} but not a {'section' if iid in r else 'row'} in the same file")
        rows.update(r)
        sections_seen.update(s)
    return rows, sections_seen, bad


def _parse_registry(path: str) -> tuple[dict[str, str], dict[str, str]]:
    text = read(path)
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
    return rows, sections_seen


def _registry_invariants(rows: dict[str, str], sections_seen: dict[str, str]) -> list[str]:
    bad = []
    for iid, status in sorted(rows.items()):
        if status not in STATUSES:
            bad.append(f"registry: {iid} has unknown status {status!r}")

    for iid, body in sorted(sections_seen.items()):
        gated = re.search(r"^\*\*Gate:\*\*", body, re.M) is not None
        blocked = rows.get(iid) == "BLOCKED"
        if gated and not blocked:
            bad.append(f"registry: {iid} has a Gate: line but is not BLOCKED")
        if blocked and not gated:
            bad.append(f"registry: {iid} is BLOCKED with no Gate: line")
        remaining = re.search(r"^\*\*Remaining:\*\*", body, re.M) is not None
        if rows.get(iid) == "PARTIAL" and not remaining:
            bad.append(f"registry: {iid} is PARTIAL with no Remaining: line")
        if remaining and rows.get(iid) not in ("PARTIAL", "WIP", "BLOCKED"):
            bad.append(f"registry: {iid} has a Remaining: line but is {rows.get(iid)}")
    return bad


def check_items(files: list[str]) -> list[str]:
    """Every IMP-Mn-nn cited anywhere resolves to a section in the register or an archive."""
    _, sections_seen, _ = registry_items()
    bad = []
    for p in files:
        for n, line in enumerate(read(p).splitlines(), 1):
            for m in re.finditer(rf"(?<![\w-])({ITEM})(?![\w-])", line):
                if m.group(1) not in sections_seen:
                    bad.append(f"{rel(p)}:{n}: {m.group(1)} has no section in the register or an archive")
    return bad


WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen "
    "fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}
COUNT = re.compile(
    r"\b(\d+|" + "|".join(WORDS) + r")\s+"
    r"(requirement documents|per-feature documents|work items|repositories|submodules)\b", re.I)


def actual_counts() -> dict[str, int]:
    reqs = os.path.join(DOCS, "requirements")
    rows, _, _ = registry_items()
    gm = read(os.path.join(ROOT, ".gitmodules"))
    mods = len(re.findall(r"^\[submodule ", gm, re.M))
    return {
        "requirement documents": len([f for f in os.listdir(reqs) if f.endswith(".md") and f != "INDEX.md"]),
        "work items": len(rows),
        "submodules": mods,
        "repositories": mods + 1,  # the submodules plus this umbrella repository
    }


def check_counts(_files: list[str]) -> list[str]:
    """Every number CLAUDE.md states about the corpus equals what is on disk."""
    actual = actual_counts()
    bad = []
    for n, line in enumerate(read(os.path.join(ROOT, "CLAUDE.md")).splitlines(), 1):
        for m in COUNT.finditer(line):
            said = m.group(1).lower()
            said_n = int(said) if said.isdigit() else WORDS[said]
            noun = m.group(2).lower().replace("per-feature", "requirement")
            if said_n != actual[noun]:
                bad.append(f"CLAUDE.md:{n}: states {said_n} {noun}, found {actual[noun]}")
    return bad


# ---------------------------------------------------------------------------
# code-maps: ARCHITECTURE.md files name code; the names must resolve.
#
# A backticked token in a map is checked when it has one of these shapes:
#   io.turnbase.x.y            a Java package -> a directory under src/main/java (or test)
#   Name / Name.method         a class or component (also useFoo) -> a file Name.<ext>
#                              somewhere in the repository; `.method` must occur in it
#   a/b/c.ext, a/b/            a path relative to the repository root
#   file.ext                   a file of that name somewhere in the repository
# Everything else (endpoints, STOMP destinations, `rpc X`, prose) is not checked.

MAP_REPOS = ["", "turnbase-platform", "turnbase-game-host", "turnbase-frontend", "turnbase-sdk"]
MAP_SKIP_DIRS = {"node_modules", "target", "dist", "coverage", ".git", "test-results", "build"}
MAP_EXT = r"(?:java|ts|tsx|css|xml|proto|md|yml|yaml|json|sh|py|sql|properties|mjs|js)"
MAP_CLASS = re.compile(r"^((?:[A-Z]|use[A-Z])[A-Za-z0-9]*)(?:\.([a-z][A-Za-z0-9]*))?$")
MAP_PACKAGE = re.compile(r"^io\.turnbase(?:\.[a-z][a-z0-9]*)+$")
MAP_FILE = re.compile(r"^[\w./@-]*[\w-]\." + MAP_EXT + r"$")
MAP_PATH_DIR = re.compile(r"^[\w.@-]+(?:/[\w.@-]+)*/$")
MAP_CODE_EXT = (".java", ".ts", ".tsx", ".js", ".mjs")


def map_index(base: str) -> tuple[dict[str, list[str]], set[str], set[str]]:
    """basename-without-ext -> files, all basenames, all relative dir paths under base."""
    stems: dict[str, list[str]] = {}
    names: set[str] = set()
    dirs: set[str] = set()
    for d, subs, fs in os.walk(base):
        subs[:] = [x for x in subs if x not in MAP_SKIP_DIRS]
        dirs.add(os.path.relpath(d, base).replace(os.sep, "/"))
        for f in fs:
            names.add(f)
            stems.setdefault(f.split(".")[0], []).append(os.path.join(d, f))
    return stems, names, dirs


def code_files(base: str, stems: dict[str, list[str]]) -> list[str]:
    return [f for fs in stems.values() for f in fs if f.endswith(MAP_CODE_EXT)]


def check_code_maps(_files: list[str]) -> list[str]:
    bad = []
    for repo in MAP_REPOS:
        base = os.path.join(ROOT, repo) if repo else ROOT
        label = (repo + "/" if repo else "") + "ARCHITECTURE.md"
        path = os.path.join(base, "ARCHITECTURE.md")
        if not os.path.isfile(path):
            bad.append(f"{label}: missing (every service and the umbrella carry a code map)")
            continue
        stems, names, dirs = map_index(base)
        # The umbrella map names no code of its own: its tokens resolve in the umbrella tree.
        for n, line in enumerate(read(path).splitlines(), 1):
            for tok in re.findall(r"`([^`\s]+)`", line):
                tok = tok.rstrip(".,;:")
                if MAP_PACKAGE.match(tok):
                    rel = tok.replace(".", "/")
                    if not any(d.endswith(rel) for d in dirs):
                        bad.append(f"{label}:{n}: package `{tok}` has no directory")
                elif MAP_PATH_DIR.match(tok) and tok.startswith(("docs/", "scripts/")):
                    if not os.path.isdir(os.path.join(ROOT, tok)):  # umbrella paths, from any map
                        bad.append(f"{label}:{n}: path `{tok}` does not exist")
                elif MAP_PATH_DIR.match(tok):
                    if tok.rstrip("/") not in dirs:
                        bad.append(f"{label}:{n}: path `{tok}` does not exist")
                elif MAP_FILE.match(tok):
                    if "/" in tok:
                        if not os.path.exists(os.path.join(base, tok)):
                            bad.append(f"{label}:{n}: path `{tok}` does not exist")
                    elif tok not in names:
                        bad.append(f"{label}:{n}: file `{tok}` not found")
                else:
                    m = MAP_CLASS.match(tok)
                    if not m:
                        continue
                    cands = [f for f in stems.get(m.group(1), []) if f.endswith(MAP_CODE_EXT)]
                    if not cands:  # declared inside a file named otherwise (gameRelay.ts: class GameRelay)
                        decl = re.compile(r"\b(?:class|interface|enum|record|type|function|const)\s+"
                                          + re.escape(m.group(1)) + r"\b")
                        cands = [f for f in code_files(base, stems) if decl.search(read(f))]
                    if not cands:
                        bad.append(f"{label}:{n}: `{tok}` — no class or component {m.group(1)}")
                    elif m.group(2) and not any(
                            re.search(r"\b" + re.escape(m.group(2)) + r"\b", read(f)) for f in cands):
                        bad.append(f"{label}:{n}: `{tok}` — {m.group(1)} has no member {m.group(2)}")
    return bad


# ---------------------------------------------------------------------------

CHECKS = {
    "links": ("relative links resolve", check_links),
    "cites": ("requirement citations name the defining document", check_cites),
    "sections": ("section references resolve", check_sections),
    "index": ("every document is registered in its nearest INDEX", check_index),
    "registry": ("the register table and the item sections agree, archives included", check_registry),
    "items": ("every cited IMP-* identifier resolves to a section", check_items),
    "counts": ("counts stated in CLAUDE.md match the disk", check_counts),
    "code-maps": ("ARCHITECTURE.md maps name code that exists", check_code_maps),
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
        print(f"[{mark}] {name:10} {label} — {len(problems)} problem(s)")
        for line in problems:
            print(f"         {line}")
        failed += len(problems)
    print()
    print("clean" if not failed else f"{failed} problem(s) found")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
