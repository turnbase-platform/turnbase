"""The iteration loop: one `claude -p` session per TurnBase work item, back to back.

Behaviour matches the original bash loop (see the --help text in __main__), plus a
countdown between sessions and the operator stop: the first Ctrl+C during a session
schedules a stop after it, a second one within three seconds interrupts it.
"""

from __future__ import annotations

import json
import math
import re
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import checks
from .display import BOLD, DIM, GREEN, RED, YELLOW, Segment, Terminal, fmt_duration
from .progress import Progress, phase_totals
from .prompts import PROMPT, RESUME_PROMPT, continue_prompt, verify_prompt, with_ci_policy
from .session import Outcome, SessionResult, WaitResult, run_session
from .state import StateFile
from .view import SessionDisplay

RESUMABLE = {"running", "interrupted", "rate_limited", "dirty", "unverified"}
# A session whose DONE fails the post-session checks is resumed this many times, then the loop halts.
VERIFY_RETRIES = 1
# The same item reported PARTIAL this many sessions in a row halts the loop: it is not converging.
PARTIAL_LIMIT = 3
TITLE = "TurnBase loop"
EXIT_OK, EXIT_FAIL, EXIT_INT, EXIT_TERM = 0, 1, 130, 143
_LIMIT_TEXT = re.compile(r"hit your (?:session|weekly|monthly) limit", re.IGNORECASE)
_RESETS_AT = re.compile(r'"resetsAt":\s*(\d+)')


@dataclass
class Config:
    repo_dir: Path
    log_dir: Path
    max_iterations: int = 20
    model: str = "sonnet"
    sleep_seconds: float = 10
    stop_file: Path | None = None
    state_file: Path | None = None
    resume: bool = True
    once: bool = False
    stall_minutes: float = 15.0
    claude_bin: str = "claude"
    claude_projects_dir: Path = field(default_factory=lambda: Path.home() / ".claude" / "projects")
    quota_grace_seconds: float = 30
    quota_fallback_seconds: float = 900
    skip_ci_wait: bool = False  # --skip-ci-wait: local verification instead of blocking on CI
    verify: bool = True  # post-session checks after DONE (see checks.py)

    def __post_init__(self) -> None:
        self.repo_dir, self.log_dir = Path(self.repo_dir), Path(self.log_dir)
        self.stop_file = Path(self.stop_file or self.repo_dir / ".autonomous-loop.stop")
        self.state_file = Path(self.state_file or self.log_dir / "state.json")
        if self.once:
            self.max_iterations = 1

    @property
    def settings_file(self) -> Path:
        return self.repo_dir / "scripts" / "autonomous-loop.settings.json"


def command(cfg: Config, sid: str, resumed: bool, prompt: str | None = None) -> list[str]:
    return [cfg.claude_bin, "-p",
            with_ci_policy(prompt or (RESUME_PROMPT if resumed else PROMPT), cfg.skip_ci_wait),
            "--resume" if resumed else "--session-id", sid,
            "--model", cfg.model, "--output-format", "stream-json", "--verbose",
            "--dangerously-skip-permissions", "--settings", str(cfg.settings_file)]


def transcript_path(cfg: Config, sid: str) -> Path:
    """Claude Code names a project's transcript directory after its cwd, every
    non-alphanumeric character replaced by a dash."""
    return cfg.claude_projects_dir / re.sub(r"[^a-zA-Z0-9]", "-", str(cfg.repo_dir)) / f"{sid}.jsonl"


def result_event(path: Path) -> dict:
    """The last `result` event of a stream-json log, or {}."""
    found: dict = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if '"result"' not in line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                if isinstance(obj, dict) and obj.get("type") == "result":
                    found = obj
    except OSError:
        pass
    return found


def quota_reset_epoch(path: Path) -> int | None:
    try:
        matches = _RESETS_AT.findall(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return None
    return int(matches[-1]) if matches else None


def _tail(path: Path, lines: int = 10) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return [l for l in text.splitlines() if l.strip()][-lines:]


def _cost(event: dict) -> float | None:
    cost = event.get("total_cost_usd")
    return round(float(cost), 4) if isinstance(cost, (int, float)) and not isinstance(cost, bool) else None


def outcome_segments(status_line: str, elapsed: float, cost: float | None,
                     tool_calls: int) -> list[Segment]:
    if status_line.startswith(("LOOP_STATUS: DONE", "LOOP_STATUS: FINISHED")):
        mark, color = "✔", GREEN
    elif status_line.startswith("LOOP_STATUS: PARTIAL"):
        mark, color = "◐", YELLOW
    elif status_line.startswith("LOOP_STATUS: BLOCKED"):
        mark, color = "■", YELLOW
    else:
        mark, color = "✖", RED
    tail = fmt_duration(elapsed) + (f" · ${cost:.2f}" if cost is not None else "")
    tail += f" · {tool_calls} tool call{'s' if tool_calls != 1 else ''}"
    return [(f"  {mark} ", color), (status_line, BOLD), (f" · {tail}", DIM)]


def run(cfg: Config, *, controls, terminal: Terminal, now: Callable[[], float] = time.time,
        notify: Callable[[str, str], None] | None = None) -> int:
    return _Loop(cfg, controls, terminal, now, notify or (lambda title, body: None)).run()


class _Loop:
    def __init__(self, cfg: Config, controls, terminal: Terminal, now: Callable[[], float],
                 notify: Callable[[str, str], None]) -> None:
        self.cfg, self.controls, self.t, self.now, self.notify = cfg, controls, terminal, now, notify
        cfg.log_dir.mkdir(parents=True, exist_ok=True)
        self.state = StateFile(cfg.state_file)
        # Carried through every state write for the session: what the post-session checks
        # compare against (HEAD and the branches that already existed when it started).
        self.session_facts: dict = {}
        self.verify_attempts: dict[str, int] = {}
        self.status_line = ""
        self.reported_item: str | None = None

    def run(self) -> int:
        cfg = self.cfg
        sessions = 0
        for i in range(1, cfg.max_iterations + 1):
            if sessions and cfg.sleep_seconds > 0:
                waited = self._countdown(cfg.sleep_seconds)
                if waited is not WaitResult.DONE:
                    return self._stopped(waited)

            if cfg.stop_file.exists():
                self._say(f"Stop file present ({cfg.stop_file}) — halting before iteration {i}.")
                cfg.stop_file.unlink(missing_ok=True)
                return EXIT_OK

            sid, resumed, prompt = self._choose_session()
            if not resumed:
                refusal = self._fresh_refusal(i)
                if refusal:
                    self._say(refusal, RED)
                    self.notify(TITLE, f"Refused to start iteration {i}: {refusal}")
                    return EXIT_FAIL
                self.session_facts = self._facts_at_start()

            ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(self.now()))
            out_file = cfg.log_dir / f"{ts}-iter{i}.jsonl"
            self.t.print([(f"[{ts}] ", DIM), (f"▶ iteration {i}/{cfg.max_iterations}", BOLD),
                          (f" — {'resume' if resumed else 'fresh'} session {sid} ", ""),
                          (f"(log: {out_file})", DIM)])
            # Recorded before the run so a hard kill still leaves a resumable id behind.
            self._write(sid, i, "running", log_file=str(out_file))

            view = SessionDisplay(self.t, iteration=i, max_iterations=cfg.max_iterations,
                                  resumed=resumed, stall_seconds=cfg.stall_minutes * 60,
                                  clock=self.now, notify=self.notify)
            started = self.now()
            result = run_session(command(cfg, sid, resumed, prompt), out_file, controls=self.controls,
                                 view=view, cwd=cfg.repo_dir)
            sessions += 1
            self.status_line, self.reported_item = "", None
            code = self._after_session(i, sid, out_file, result, view.progress, started)
            self._record_history(i, sid, out_file, view.progress, started)
            if code is not None:
                return code

        self._say(f"Reached max iterations ({cfg.max_iterations}). Stopping.")
        self.notify(TITLE, f"Loop stopped: reached max iterations ({cfg.max_iterations}).")
        return EXIT_OK

    # --- before a session -----------------------------------------------------------

    def _choose_session(self) -> tuple[str, bool, str | None]:
        """(session id, resumed?, prompt override)."""
        if self.cfg.resume:
            prev = self.state.read()
            sid = prev.get("session_id")
            if prev.get("status") in RESUMABLE and isinstance(sid, str) and sid:
                self.session_facts = {k: prev[k] for k in ("start_head", "known_branches") if k in prev}
                problems = prev.get("problems")
                if prev.get("status") == "unverified" and isinstance(problems, list) and problems:
                    reported = "PARTIAL" if str(prev.get("reported", "")).startswith(
                        "LOOP_STATUS: PARTIAL") else "DONE"
                    return sid, True, verify_prompt([str(p) for p in problems], reported)
                return sid, True, None
        self.session_facts = {}
        item, _ = self._partial_streak()
        return str(uuid.uuid4()), False, continue_prompt(item) if item else None

    def _facts_at_start(self) -> dict:
        if not self.cfg.verify:
            return {}
        facts: dict = {"start_head": self._git("rev-parse", "HEAD")}
        known, complete = checks.branches(self.cfg.repo_dir)
        if complete:  # a partial snapshot would make old remote branches look new
            facts["known_branches"] = sorted(known)
        return facts

    def _fresh_refusal(self, i: int) -> str | None:
        """A fresh session's contract is a clean master; a resumed one is mid-work by
        definition, so these checks are deliberately skipped for it."""
        if self._git("status", "--porcelain"):
            return f"Working tree not clean before iteration {i} — refusing to start. Inspect manually."
        branch = self._git("rev-parse", "--abbrev-ref", "HEAD")
        if branch != "master":
            return f"Not on master before iteration {i} (on '{branch}') — refusing to start."
        return None

    # --- after a session ------------------------------------------------------------

    def _after_session(self, i: int, sid: str, out_file: Path, result: SessionResult,
                       progress: Progress, started: float) -> int | None:
        """Returns the loop's exit code, or None to go on to the next iteration."""
        if result.outcome is not Outcome.EXITED:
            name = "SIGINT" if result.outcome is Outcome.INTERRUPTED else "SIGTERM"
            self._say(f"Received {name} — forwarded to claude; stopping the loop.", YELLOW)
            self._write(sid, i, "interrupted")
            self._say(f"Session {sid} left resumable.")
            self._say(f"Re-run this script to continue it, or: claude --resume {sid}")
            return EXIT_INT if result.outcome is Outcome.INTERRUPTED else EXIT_TERM

        event = result_event(out_file)
        text = event.get("result")
        text = text if isinstance(text, str) else ""

        if str(event.get("api_error_status", "")) == "429" or _LIMIT_TEXT.search(text):
            resets_at = quota_reset_epoch(transcript_path(self.cfg, sid))
            self._say(f"  → session limit reached: {text.strip() or '429'}", YELLOW)
            self._write(sid, i, "rate_limited",
                        resets_at=str(resets_at) if resets_at is not None else "")
            if result.stop_scheduled:
                return self._operator_stop()
            until = (f"until {time.strftime('%H:%M', time.localtime(resets_at))}"
                     if resets_at is not None and resets_at > self.now() else "before retrying")
            self.notify(TITLE, f"Session limit reached — waiting {until}.")
            waited = self._wait_for_quota(resets_at)
            return None if waited is WaitResult.DONE else self._stopped(waited)

        if result.exit_code != 0:
            self._say(f"claude exited with code {result.exit_code} on iteration {i} — see {out_file}.", RED)
            tail = _tail(Path(f"{out_file}.stderr"))
            for line in tail:
                self._say(f"  {line}", DIM)
            self.notify(TITLE, f"claude exited with code {result.exit_code}"
                        + (f": {tail[-1]}" if tail else "") + " — loop halted.")
            return self._halt_resumable(sid, i)
        if event.get("is_error") is True:
            self._say(f"claude reported an error on iteration {i} — see {out_file}.", RED)
            self.notify(TITLE, f"claude reported an error on iteration {i} — loop halted.")
            return self._halt_resumable(sid, i)

        status_lines = [l for l in text.splitlines() if l.startswith("LOOP_STATUS:")]
        if not status_lines:
            # The Stop hook should make this unreachable; if it happens anyway the
            # session is unfinished, not failed, so leave it resumable.
            self._say(f"No LOOP_STATUS line in iteration {i} — treating the session as unfinished.", YELLOW)
            self._write(sid, i, "interrupted")
            return self._operator_stop() if result.stop_scheduled else None
        status_line = self.status_line = status_lines[-1].rstrip()
        self._print_summary(status_line, event, progress, started)

        if self._git("status", "--porcelain") or self._git("rev-parse", "--abbrev-ref", "HEAD") != "master":
            # The session owns whatever it left behind, and a fresh one would refuse to start on it.
            self._say(f"Tree not clean / not on master after iteration {i} despite report — halting.", RED)
            self._write(sid, i, "dirty", reported=status_line)
            self._say("Session left resumable; re-run to have it finish or unwind its work, "
                      "or pass --no-resume after cleaning up by hand.")
            self.notify(TITLE, f"Tree not clean or not on master after iteration {i} — loop halted.")
            return EXIT_FAIL

        label = status_line.split(":", 1)[1].strip()
        if status_line.startswith("LOOP_STATUS: BLOCKED"):
            self._write(sid, i, "blocked")
            self._say("Session reported BLOCKED — halting loop for manual review.", YELLOW)
            self.notify(TITLE, label)
            return EXIT_OK
        if status_line.startswith("LOOP_STATUS: FINISHED"):
            self._write(sid, i, "finished")
            self._say("Session reported FINISHED — all work items complete. Stopping loop.", GREEN)
            self.notify(TITLE, "All work items complete — loop finished.")
            return EXIT_OK
        if status_line.startswith("LOOP_STATUS: PARTIAL"):
            return self._after_partial(i, sid, label.removeprefix("PARTIAL").strip(), result.stop_scheduled)
        if not status_line.startswith("LOOP_STATUS: DONE"):
            self._write(sid, i, "failed")
            self._say(f"Unrecognized LOOP_STATUS value: '{status_line}' — halting for manual review.", RED)
            self.notify(TITLE, f"Unrecognized status '{label}' — loop halted.")
            return EXIT_FAIL
        if self.cfg.verify:
            passed, code = self._verify(i, sid, label.removeprefix("DONE").strip(), result.stop_scheduled)
            if not passed:
                return code
        self._write(sid, i, "done")
        return self._operator_stop() if result.stop_scheduled else None

    def _after_partial(self, i: int, sid: str, label: str, stop_scheduled: bool) -> int | None:
        """The item landed in part: the next fresh session is told to continue it, unless it
        has now come back PARTIAL PARTIAL_LIMIT times in a row."""
        item = self.reported_item = label.split()[0] if label.split() else label
        if self.cfg.verify:
            passed, code = self._verify(i, sid, label, stop_scheduled, partial=True)
            if not passed:
                return code
        self._write(sid, i, "partial", item=item)
        last, streak = self._partial_streak()
        streak = streak + 1 if last == item else 1
        if streak >= PARTIAL_LIMIT:
            self._say(f"{item} reported PARTIAL {streak} sessions in a row — halting for manual review.",
                      YELLOW)
            self.notify(TITLE, f"{item}: PARTIAL {streak} sessions in a row — loop halted.")
            return EXIT_OK
        self._say(f"{item} left PARTIAL — the next session continues it.", YELLOW)
        return self._operator_stop() if stop_scheduled else None

    def _partial_streak(self) -> tuple[str | None, int]:
        """(item, n): the last finished session reported `item` PARTIAL, as did the n-1 before
        it. Resumes of one session (interrupted, rate-limited, unverified) are not finishes."""
        try:
            lines = (self.cfg.log_dir / "history.jsonl").read_text(encoding="utf-8").splitlines()
        except OSError:
            return None, 0
        item, streak = None, 0
        for line in reversed(lines):
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            status = entry.get("status") if isinstance(entry, dict) else None
            if status in RESUMABLE or status is None:
                continue
            if status != "partial" or not entry.get("item") or item not in (None, entry["item"]):
                break
            item, streak = entry["item"], streak + 1
        return item, streak

    def _verify(self, i: int, sid: str, label: str, stop_scheduled: bool,
                partial: bool = False) -> tuple[bool, int | None]:
        """(passed, what _after_session returns if not): a failing session is resumed to
        fix what the checks found, and the loop halts once that has already been tried."""
        known = self.session_facts.get("known_branches")
        if known is None:
            # No snapshot (an older session, or origin was unreachable when it started):
            # every branch that exists now counts as pre-existing, so none is flagged.
            self._say("  branch check skipped: no complete snapshot from the session's start", DIM)
            known, _ = checks.branches(self.cfg.repo_dir)
        report = checks.verify(self.cfg.repo_dir, start_head=self.session_facts.get("start_head"),
                               label=label, known_branches=set(known), partial=partial)
        for warning in report.warnings:
            self._say(f"  check skipped: {warning}", DIM)
        if not report.problems:
            self.verify_attempts.pop(sid, None)
            return True, None
        self._say("Post-session checks failed:", RED)
        for problem in report.problems:
            self._say(f"  ✖ {problem}", RED)
        self._write(sid, i, "unverified", problems=report.problems, reported=self.status_line)
        attempts = self.verify_attempts[sid] = self.verify_attempts.get(sid, 0) + 1
        if attempts > VERIFY_RETRIES:
            self._say("Still failing after the session was asked to fix them — halting. "
                      "Re-run to try again, or fix by hand and pass --no-resume.", RED)
            self.notify(TITLE, f"{label}: post-session checks still failing — loop halted. "
                        + report.problems[0])
            return False, EXIT_FAIL
        if stop_scheduled:
            return False, self._operator_stop()
        self._say("Resuming the session to fix them.", YELLOW)
        return False, None

    def _halt_resumable(self, sid: str, i: int) -> int:
        self._write(sid, i, "interrupted")
        self._say("Session left resumable; re-run to continue it. Halting.")
        return EXIT_FAIL

    def _print_summary(self, status_line: str, event: dict, progress: Progress, started: float) -> None:
        now = self.now()
        self.t.print(outcome_segments(status_line, now - started, _cost(event), progress.tool_calls))
        phases = [f"{ph} {fmt_duration(sec)}" for ph, sec in phase_totals(progress, now).items()
                  if sec >= 1]
        if phases:
            self.t.print([("    " + " · ".join(phases), DIM)])

    def _record_history(self, i: int, sid: str, out_file: Path, progress: Progress,
                        started: float) -> None:
        """One JSON line per session in <log dir>/history.jsonl, for looking back across items."""
        now = self.now()
        entry = {
            "ended_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
            "iteration": i, "session_id": sid, "item": self.reported_item or progress.item,
            "status": self.state.read().get("status"), "reported": self.status_line or None,
            "seconds": round(now - started), "cost_usd": _cost(result_event(out_file)),
            "tool_calls": progress.tool_calls,
            "phases": {ph: round(sec) for ph, sec in phase_totals(progress, now).items()},
            "log": str(out_file),
        }
        try:
            with open(self.cfg.log_dir / "history.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError:
            pass

    # --- waiting and stopping ------------------------------------------------------------

    def _operator_stop(self) -> int:
        self._say("Stopped at operator request.", YELLOW)
        return EXIT_OK

    def _stopped(self, waited: WaitResult) -> int:
        if waited is WaitResult.TERM:
            self._say("Received SIGTERM — stopping the loop.", YELLOW)
            return EXIT_TERM
        return self._operator_stop()

    def _countdown(self, seconds: float) -> WaitResult:
        if not self.t.tty:
            self._say(f"Next session in {fmt_duration(seconds)} — Ctrl+C to stop.", DIM)
        try:
            return self.controls.wait(seconds, lambda left: self.t.live(
                [("○ ", DIM), (f"next session in {math.ceil(left)}s", BOLD),
                 (" — Ctrl+C to stop", DIM)]))
        finally:
            self.t.clear_live()

    def _wait_for_quota(self, resets_at: int | None) -> WaitResult:
        t = self.now()
        if resets_at is not None and resets_at > t:
            delta = resets_at - t + self.cfg.quota_grace_seconds
            until = time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(resets_at))
            self._say(f"  quota resets at {until} — sleeping {int(delta)}s.", YELLOW)
        else:
            delta = self.cfg.quota_fallback_seconds
            self._say(f"  no usable reset time in the transcript — sleeping {int(delta)}s before retrying.",
                      YELLOW)
        end = t + delta
        try:
            return self.controls.wait(delta, lambda left: self.t.live(
                [("◔ ", YELLOW),
                 (f"rate-limited until {time.strftime('%H:%M', time.localtime(end))}", BOLD),
                 (f" ({fmt_duration(left)} left) — Ctrl+C to stop", DIM)]))
        finally:
            self.t.clear_live()

    # --- helpers --------------------------------------------------------------------

    def _write(self, sid: str, i: int, status: str, **extra) -> None:
        self.state.write(sid, i, status, **self.session_facts, **extra)

    def _say(self, text: str, sgr: str = "") -> None:
        self.t.print([(text, sgr)])

    def _git(self, *args: str) -> str:
        return subprocess.run(["git", "-C", str(self.cfg.repo_dir), *args], check=True,
                              capture_output=True, text=True).stdout.strip()
