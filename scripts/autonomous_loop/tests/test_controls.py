"""End-to-end control tests: the real loop on a pseudo-terminal, driven by keystrokes."""

import json
import os
import pty
import re
import signal
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

from autonomous_loop.tests.helpers import LoopFixture

SCRIPTS = Path(__file__).resolve().parents[2]
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07")
MARKER = {"type": "assistant", "message": {"content": [
    {"type": "text", "text": "LOOP_PHASE: claiming IMP-T-01"}]}}


class PtyLoop:
    def __init__(self, fx: LoopFixture, *args: str):
        env = {k: v for k, v in os.environ.items() if k != "NO_COLOR"}
        env.update(fx.env(), PATH=f"{fx.bin}:{os.environ['PATH']}", LOG_DIR=str(fx.logs),
                   PYTHONPATH=str(SCRIPTS), HOME=str(fx.root), PYTHONDONTWRITEBYTECODE="1",
                   COLUMNS="200")
        argv = [sys.executable, "-B", "-m", "autonomous_loop", "--repo", str(fx.repo), *args]
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.execve(sys.executable, argv, env)
        self._raw = b""
        self._lock = threading.Lock()
        self._reader = threading.Thread(target=self._read, daemon=True)
        self._reader.start()

    def _read(self):
        while True:
            try:
                data = os.read(self.fd, 4096)
            except OSError:
                return
            if not data:
                return
            with self._lock:
                self._raw += data

    @property
    def text(self) -> str:
        with self._lock:
            return ANSI.sub("", self._raw.decode("utf-8", "replace"))

    def expect(self, needle: str, timeout: float = 15):
        deadline = time.monotonic() + timeout
        while needle not in self.text:
            if time.monotonic() > deadline:
                raise AssertionError(f"{needle!r} not seen in:\n{self.text}")
            time.sleep(0.05)

    def send(self, data: bytes):
        os.write(self.fd, data)

    def wait(self, timeout: float = 30) -> int:
        deadline = time.monotonic() + timeout
        while True:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
            if pid:
                break
            if time.monotonic() > deadline:
                os.kill(self.pid, signal.SIGKILL)
                os.waitpid(self.pid, 0)
                raise AssertionError(f"loop did not exit:\n{self.text}")
            time.sleep(0.05)
        self._reader.join(2)
        os.close(self.fd)
        return os.waitstatus_to_exitcode(status)


class ControlsTest(unittest.TestCase):
    def setUp(self):
        self.fx = LoopFixture(Path(tempfile.mkdtemp()))

    def start(self, *scenarios, args=("--max", "2", "--sleep", "1")):
        self.fx.scenarios(*scenarios)
        return PtyLoop(self.fx, *args)

    def session(self, hold):
        return {"events": [MARKER], "hold": hold, "status": "DONE IMP-T-01"}

    def test_single_ctrl_c_finishes_session_then_stops(self):
        loop = self.start(self.session(3))
        loop.expect("claiming")
        loop.send(b"\x03")
        loop.expect("stop scheduled after this session")
        self.assertEqual(loop.wait(), 0, loop.text)
        self.assertIn("Stopped at operator request.", loop.text)
        self.assertEqual(len(self.fx.calls()), 1)
        self.assertEqual(self.fx.signals(), "")
        self.assertEqual(self.fx.state()["status"], "done")

    def test_double_ctrl_c_interrupts_and_exits_130(self):
        loop = self.start(self.session(20))
        loop.expect("claiming")
        loop.send(b"\x03")
        loop.expect("stop scheduled")
        loop.send(b"\x03")
        self.assertEqual(loop.wait(), 130, loop.text)
        self.assertIn("0 SIGINT", self.fx.signals())
        self.assertEqual(self.fx.state()["status"], "interrupted")

    def test_late_second_ctrl_c_only_keeps_the_stop_scheduled(self):
        loop = self.start(self.session(6))
        loop.expect("claiming")
        loop.send(b"\x03")
        loop.expect("stop scheduled")
        time.sleep(3.5)
        loop.send(b"\x03")
        self.assertEqual(loop.wait(), 0, loop.text)
        self.assertEqual(self.fx.signals(), "")
        self.assertEqual(len(self.fx.calls()), 1)

    def test_enter_cancels_scheduled_stop(self):
        loop = self.start(self.session(3))
        loop.expect("claiming")
        loop.send(b"\x03")
        loop.expect("stop scheduled")
        loop.send(b"\r")
        loop.expect("scheduled stop cancelled")
        loop.expect("next session in")
        self.assertEqual(loop.wait(), 0, loop.text)
        self.assertIn("Reached max iterations (2)", loop.text)
        self.assertEqual(len(self.fx.calls()), 2)

    def test_ctrl_c_during_countdown_stops(self):
        loop = self.start({"status": "DONE a"}, args=("--max", "2", "--sleep", "10"))
        loop.expect("next session in")
        loop.send(b"\x03")
        self.assertEqual(loop.wait(), 0, loop.text)
        self.assertEqual(len(self.fx.calls()), 1)

    def test_sigterm_exits_143(self):
        loop = self.start(self.session(20))
        loop.expect("claiming")
        os.kill(loop.pid, signal.SIGTERM)
        self.assertEqual(loop.wait(), 143, loop.text)
        self.assertIn("0 SIGTERM", self.fx.signals())

    def test_live_line_shows_item_and_phase(self):
        loop = self.start(self.session(2), args=("--once",))
        loop.expect("● iter 1/1 · IMP-T-01 · claiming")
        self.assertEqual(loop.wait(), 0, loop.text)


if __name__ == "__main__":
    unittest.main()
