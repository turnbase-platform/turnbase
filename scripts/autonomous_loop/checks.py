"""Post-session checks: does the repository show what a DONE session claims?

CLAUDE.md's "Ending a Session" checklist, verified in code rather than taken on the
agent's word. `verify` returns problems (the session must fix them) and warnings
(a check that could not run, e.g. the network is down — never a reason to resume).
"""

from __future__ import annotations

import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

REGISTRY = Path("docs/implementation/registry.md")
_ITEM = re.compile(r"^IMP-[A-Z0-9]+-[0-9]+$")

# git(repo, *args) -> (exit code, stdout)
Git = Callable[..., tuple[int, str]]


def run_git(repo: Path, *args: str) -> tuple[int, str]:
    try:
        done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                              timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)
    return done.returncode, done.stdout.strip()


@dataclass
class Report:
    problems: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def branches(repo: Path, git: Git = run_git) -> tuple[set[str], bool]:
    """Every non-master branch in the repo and its submodules, locally and on origin,
    as "<repo>: local branch 'x'" / "<repo>: branch 'x' still exists on origin".

    Taken when a fresh session starts, so a session is only held to the branches it
    created itself. Repos are queried in parallel: ls-remote costs seconds each. The flag
    is False when some repo's origin could not be listed, so the snapshot is partial."""
    report = Report()
    with ThreadPoolExecutor(max_workers=8) as pool:
        for part in pool.map(lambda r: _branches(*r, git), _repos(repo, git)):
            report.problems += part.problems
            report.warnings += part.warnings
    return set(report.problems), not report.warnings


def verify(repo: Path, *, start_head: str | None, label: str, known_branches: set[str],
           git: Git = run_git) -> Report:
    report = Report()
    with ThreadPoolExecutor(max_workers=8) as pool:
        for part in pool.map(lambda r: _branches(*r, git), _repos(repo, git)):
            report.problems += [p for p in part.problems if p not in known_branches]
            report.warnings += part.warnings
    _submodule_refs(repo, git, report)
    _status_md(repo, start_head, git, report)
    _registry(repo, label, report)
    return report


def _repos(repo: Path, git: Git) -> list[tuple[str, Path]]:
    repos = [(repo.name, repo)]
    code, out = git(repo, "submodule", "status")
    if code == 0:
        for line in out.splitlines():
            parts = line[1:].split()
            if len(parts) >= 2 and not line.startswith("-"):  # "-": not initialised here
                repos.append((parts[1], repo / parts[1]))
    return repos


def _branches(name: str, path: Path, git: Git) -> Report:
    report = Report()
    code, out = git(path, "for-each-ref", "--format=%(refname:short)", "refs/heads")
    for branch in out.splitlines() if code == 0 else []:
        if branch != "master":
            report.problems.append(f"{name}: local branch '{branch}' still exists")

    code, remotes = git(path, "remote")
    if code != 0 or "origin" not in remotes.split():
        return report
    code, out = git(path, "ls-remote", "--heads", "origin")
    if code != 0:
        report.warnings.append(f"{name}: could not list branches on origin")
    else:
        for line in out.splitlines():
            ref = line.split("\t")[-1].removeprefix("refs/heads/")
            if ref and ref != "master":
                report.problems.append(f"{name}: branch '{ref}' still exists on origin")

    code, ahead = git(path, "rev-list", "--count", "origin/master..master")
    if code == 0 and ahead.isdigit() and int(ahead) > 0:
        report.problems.append(f"{name}: master is {ahead} commit(s) ahead of origin/master (not pushed)")
    return report


def _submodule_refs(repo: Path, git: Git, report: Report) -> None:
    code, out = git(repo, "submodule", "status")
    for line in out.splitlines() if code == 0 else []:
        parts = line[1:].split()
        if line.startswith("+") and len(parts) >= 2:
            report.problems.append(
                f"{parts[1]}: checked out at a commit the top repo does not record "
                "(submodule ref not updated, or not committed)")


def _status_md(repo: Path, start_head: str | None, git: Git, report: Report) -> None:
    if not start_head or not (repo / "STATUS.md").is_file():
        return
    code, out = git(repo, "diff", "--name-only", start_head, "HEAD", "--", "STATUS.md")
    if code != 0:
        report.warnings.append(f"could not compare STATUS.md with {start_head[:10]}")
    elif not out:
        report.problems.append("STATUS.md was not updated and committed during the session")


def _registry(repo: Path, label: str, report: Report) -> None:
    """Only a registry item is checked; gate items and spec-defect fixes are not rows."""
    item = label.split()[0] if label.split() else ""
    path = repo / REGISTRY
    if not _ITEM.match(item) or not path.is_file():
        return
    row = re.search(rf"^\|\s*{re.escape(item)}\s*\|.*\|\s*([^|]*?)\s*\|\s*$",
                    path.read_text(encoding="utf-8", errors="replace"), re.MULTILINE)
    if row and not row.group(1).startswith("DONE"):
        report.problems.append(f"{REGISTRY}: {item} is marked '{row.group(1)}', not DONE")
