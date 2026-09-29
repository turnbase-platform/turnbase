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

from .display import BOLD, DIM, GREEN, RED, YELLOW, Segment, Terminal, fmt_duration
from .prompts import PROMPT, RESUME_PROMPT
from .session import Outcome, SessionResult, WaitResult, run_session
from .state import StateFile
from .view import SessionDisplay

RESUMABLE = {"running", "interrupted", "rate_limited", "dirty"}
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

    def __post_init__(self) -> None:
        self.repo_dir, self.log_dir = Path(self.repo_dir), Path(self.log_dir)
        self.stop_file = Path(self.stop_file or self.repo_dir / ".autonomous-loop.stop")
        self.state_file = Path(self.state_file or self.log_dir / "state.json")
        if self.once:
            self.max_iterations = 1

    @property
    def settings_file(self) -> Path:
        return self.repo_dir / "scripts" / "autonomous-loop.settings.json"


def command(cfg: Config, sid: str, resumed: bool) -> list[str]:
    return [cfg.claude_bin, "-p", RESUME_PROMPT if resumed else PROMPT,
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


def run(cfg: Config, *, controls, terminal: Terminal, now: Callable[[], float] = time.time) -> int:
    return _Loop(cfg, controls, terminal, now).run()


class _Loop:
    def __init__(self, cfg: Config, controls, terminal: Terminal, now: Callable[[], float]) -> None:
        self.cfg, self.controls, self.t, self.now = cfg, controls, terminal, now
        cfg.log_dir.mkdir(parents=True, exist_ok=True)
        self.state = StateFile(cfg.state_file)

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

            sid, resumed = self._choose_session()
            if not resumed:
                refusal = self._fresh_refusal(i)
                if refusal:
                    self._say(refusal, RED)
                    return EXIT_FAIL

            ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(self.now()))
            out_file = cfg.log_dir / f"{ts}-iter{i}.jsonl"
            self.t.print([(f"[{ts}] ", DIM), (f"▶ iteration {i}/{cfg.max_iterations}", BOLD),
                          (f" — {'resume' if resumed else 'fresh'} session {sid} ", ""),
                          (f"(log: {out_file})", DIM)])
            # Recorded before the run so a hard kill still leaves a resumable id behind.
            self.state.write(sid, i, "running", log_file=str(out_file))

            view = SessionDisplay(self.t, iteration=i, max_iterations=cfg.max_iterations,
                                  resumed=resumed, stall_seconds=cfg.stall_minutes * 60,
                                  clock=self.now)
            started = self.now()
            result = run_session(command(cfg, sid, resumed), out_file, controls=self.controls,
                                 view=view, cwd=cfg.repo_dir)
            sessions += 1
            code = self._after_session(i, sid, out_file, result, self.now() - started)
            if code is not None:
                return code

        self._say(f"Reached max iterations ({cfg.max_iterations}). Stopping.")
        return EXIT_OK

    # --- before a session -----------------------------------------------------------

    def _choose_session(self) -> tuple[str, bool]:
        if self.cfg.resume:
            prev = self.state.read()
            sid = prev.get("session_id")
            if prev.get("status") in RESUMABLE and isinstance(sid, str) and sid:
                return sid, True
        return str(uuid.uuid4()), False

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
                       elapsed: float) -> int | None:
        """Returns the loop's exit code, or None to go on to the next iteration."""
        if result.outcome is not Outcome.EXITED:
            name = "SIGINT" if result.outcome is Outcome.INTERRUPTED else "SIGTERM"
            self._say(f"Received {name} — forwarded to claude; stopping the loop.", YELLOW)
            self.state.write(sid, i, "interrupted")
            self._say(f"Session {sid} left resumable.")
            self._say(f"Re-run this script to continue it, or: claude --resume {sid}")
            return EXIT_INT if result.outcome is Outcome.INTERRUPTED else EXIT_TERM

        event = result_event(out_file)
        text = event.get("result")
        text = text if isinstance(text, str) else ""

        if str(event.get("api_error_status", "")) == "429" or _LIMIT_TEXT.search(text):
            resets_at = quota_reset_epoch(transcript_path(self.cfg, sid))
            self._say(f"  → session limit reached: {text.strip() or '429'}", YELLOW)
            self.state.write(sid, i, "rate_limited",
                             resets_at=str(resets_at) if resets_at is not None else "")
            if result.stop_scheduled:
                return self._operator_stop()
            waited = self._wait_for_quota(resets_at)
            return None if waited is WaitResult.DONE else self._stopped(waited)

        if result.exit_code != 0:
            self._say(f"claude exited with code {result.exit_code} on iteration {i} — see {out_file}.", RED)
            return self._halt_resumable(sid, i)
        if event.get("is_error") is True:
            self._say(f"claude reported an error on iteration {i} — see {out_file}.", RED)
            return self._halt_resumable(sid, i)

        status_lines = [l for l in text.splitlines() if l.startswith("LOOP_STATUS:")]
        if not status_lines:
            # The Stop hook should make this unreachable; if it happens anyway the
            # session is unfinished, not failed, so leave it resumable.
            self._say(f"No LOOP_STATUS line in iteration {i} — treating the session as unfinished.", YELLOW)
            self.state.write(sid, i, "interrupted")
            return self._operator_stop() if result.stop_scheduled else None
        status_line = status_lines[-1].rstrip()
        self.t.print(self._outcome_segments(status_line, elapsed))

        if self._git("status", "--porcelain") or self._git("rev-parse", "--abbrev-ref", "HEAD") != "master":
            # The session owns whatever it left behind, and a fresh one would refuse to start on it.
            self._say(f"Tree not clean / not on master after iteration {i} despite report — halting.", RED)
            self.state.write(sid, i, "dirty", reported=status_line)
            self._say("Session left resumable; re-run to have it finish or unwind its work, "
                      "or pass --no-resume after cleaning up by hand.")
            return EXIT_FAIL

        if status_line.startswith("LOOP_STATUS: BLOCKED"):
            self.state.write(sid, i, "blocked")
            self._say("Session reported BLOCKED — halting loop for manual review.", YELLOW)
            return EXIT_OK
        if status_line.startswith("LOOP_STATUS: FINISHED"):
            self.state.write(sid, i, "finished")
            self._say("Session reported FINISHED — all work items complete. Stopping loop.", GREEN)
            return EXIT_OK
        if not status_line.startswith("LOOP_STATUS: DONE"):
            self.state.write(sid, i, "failed")
            self._say(f"Unrecognized LOOP_STATUS value: '{status_line}' — halting for manual review.", RED)
            return EXIT_FAIL
        self.state.write(sid, i, "done")
        return self._operator_stop() if result.stop_scheduled else None

    def _halt_resumable(self, sid: str, i: int) -> int:
        self.state.write(sid, i, "interrupted")
        self._say("Session left resumable; re-run to continue it. Halting.")
        return EXIT_FAIL

    @staticmethod
    def _outcome_segments(status_line: str, elapsed: float) -> list[Segment]:
        if status_line.startswith(("LOOP_STATUS: DONE", "LOOP_STATUS: FINISHED")):
            mark, color = "✔", GREEN
        elif status_line.startswith("LOOP_STATUS: BLOCKED"):
            mark, color = "■", YELLOW
        else:
            mark, color = "✖", RED
        return [(f"  {mark} ", color), (status_line, BOLD), (f" · {fmt_duration(elapsed)}", DIM)]

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

    def _say(self, text: str, sgr: str = "") -> None:
        self.t.print([(text, sgr)])

    def _git(self, *args: str) -> str:
        return subprocess.run(["git", "-C", str(self.cfg.repo_dir), *args], check=True,
                              capture_output=True, text=True).stdout.strip()
