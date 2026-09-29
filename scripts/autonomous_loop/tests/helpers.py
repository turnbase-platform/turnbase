"""Shared test doubles for the loop tests."""

import json
import subprocess
import sys
import time
from pathlib import Path

from autonomous_loop.loop import Config, transcript_path
from autonomous_loop.session import WaitResult


class FakeControls:
    """Scripted stand-in for session.Controls.

    `events` maps a poll index to the events that poll returns. The fake clock
    advances by `clock_step` on every poll; `wait` returns at once and records
    the requested duration in `waits`.
    """

    def __init__(self, events=None, clock_step=0.0, wait_results=None):
        self._events = dict(events or {})
        self._polls = 0
        self._now = 0.0
        self._step = clock_step
        self._wait_results = list(wait_results or [])
        self.waits = []

    def clock(self):
        return self._now

    def poll(self, timeout):
        time.sleep(min(timeout, 0.02))
        events = self._events.pop(self._polls, [])
        self._polls += 1
        self._now += self._step
        return list(events)

    def wait(self, seconds, on_tick):
        self.waits.append(seconds)
        on_tick(seconds)
        return self._wait_results.pop(0) if self._wait_results else WaitResult.DONE


class RecordingView:
    def __init__(self, fail_on=None):
        self.fail_on = fail_on
        self.failed = False
        self.called_after_failure = False
        self.lines, self.stops, self.ticks, self.closed = [], [], 0, False

    def _hit(self, name):
        if self.failed:
            self.called_after_failure = True
        if name == self.fail_on:
            self.failed = True
            raise RuntimeError("boom")

    def on_lines(self, lines):
        self._hit("on_lines")
        self.lines += lines

    def on_tick(self):
        self._hit("on_tick")
        self.ticks += 1

    def on_stop_scheduled(self, scheduled):
        self._hit("on_stop_scheduled")
        self.stops.append(scheduled)

    def close(self):
        self._hit("close")
        self.closed = True


FAKE_CLAUDE = Path(__file__).with_name("fake_claude.py")


class LoopFixture:
    """A throwaway git repo on master, a fake `claude`, and log/transcript dirs."""

    def __init__(self, root: Path):
        self.root = root
        self.repo, self.logs = root / "repo", root / "logs"
        self.fake, self.bin, self.projects = root / "fake", root / "bin", root / "projects"
        for d in (self.repo / "scripts", self.fake, self.bin, self.projects):
            d.mkdir(parents=True)
        (self.repo / "scripts" / "autonomous-loop.settings.json").write_text("{}\n")
        self.git("init", "-q", "-b", "master")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "init")
        shim = self.bin / "claude"
        shim.write_text(f'#!/bin/sh\nexec "{sys.executable}" -B "{FAKE_CLAUDE}" "$@"\n')
        shim.chmod(0o755)

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=t",
                        "-c", "user.email=t@example.com", "-c", "core.hooksPath=/dev/null", *args],
                       check=True, capture_output=True)

    def scenarios(self, *items):
        for i, s in enumerate(items):
            (self.fake / f"{i}.json").write_text(json.dumps(s))

    def config(self, **kw):
        kw.setdefault("sleep_seconds", 0)
        return Config(repo_dir=self.repo, log_dir=self.logs, claude_bin=str(self.bin / "claude"),
                      claude_projects_dir=self.projects, **kw)

    def env(self):
        return {"FAKE_CLAUDE_DIR": str(self.fake),
                "FAKE_CLAUDE_TRANSCRIPT_DIR": str(transcript_path(self.config(), "x").parent)}

    def calls(self):
        path = self.fake / "calls.jsonl"
        return [json.loads(l)["argv"] for l in path.read_text().splitlines()] if path.exists() else []

    def signals(self):
        path = self.fake / "signals.log"
        return path.read_text() if path.exists() else ""

    def state(self):
        return json.loads((self.logs / "state.json").read_text())


def session_id(argv):
    flag = "--session-id" if "--session-id" in argv else "--resume"
    return flag, argv[argv.index(flag) + 1]
