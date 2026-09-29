import contextlib
import io
import json
import os
import pty
import signal
import sys
import tempfile
import termios
import time
import unittest
from pathlib import Path
from unittest import mock

from autonomous_loop.display import Terminal
from autonomous_loop.session import (
    Controls,
    Event,
    LogFollower,
    Outcome,
    WaitResult,
    run_session,
)
from autonomous_loop.tests.helpers import FakeControls, RecordingView
from autonomous_loop.view import SessionDisplay


def _alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    try:  # a zombie still answers kill(0); count it as dead
        return os.waitpid(pid, os.WNOHANG) == (0, 0)
    except ChildProcessError:
        with open(f"/proc/{pid}/stat") as f:
            return f.read().split()[2] != "Z"


def py(code):
    return [sys.executable, "-B", "-c", code]


class LogFollowerTest(unittest.TestCase):
    def setUp(self):
        self.path = Path(tempfile.mkdtemp()) / "log.jsonl"

    def follower(self):
        f = LogFollower(self.path)
        self.addCleanup(f.close)
        return f

    def test_missing_file_yields_nothing(self):
        self.assertEqual(self.follower().read_lines(), [])

    def test_holds_partial_line_until_newline(self):
        f = self.follower()
        self.path.write_bytes(b'{"a":1}\n{"b"')
        self.assertEqual(f.read_lines(), ['{"a":1}'])
        with self.path.open("ab") as out:
            out.write(b':2}\n')
        self.assertEqual(f.read_lines(), ['{"b":2}'])
        self.assertEqual(f.read_lines(), [])

    def test_flush_returns_the_unterminated_tail(self):
        f = self.follower()
        self.path.write_bytes(b'{"a":1}\n{"b":2}')
        self.assertEqual(f.read_lines(), ['{"a":1}'])
        self.assertEqual(f.flush(), ['{"b":2}'])
        self.assertEqual(f.flush(), [])

    def test_invalid_utf8_is_replaced_not_raised(self):
        self.path.write_bytes(b"\xff\xfe bad\n")
        self.assertEqual(self.follower().read_lines(), ["�� bad"])


class ControlsTest(unittest.TestCase):
    def test_sigint_becomes_event_and_handlers_are_restored(self):
        before = signal.getsignal(signal.SIGINT)
        with Controls(stdin=io.StringIO()) as c:
            os.kill(os.getpid(), signal.SIGINT)
            self.assertIn(Event.INT, c.poll(1.0))
        self.assertIs(signal.getsignal(signal.SIGINT), before)

    def test_wait_completes(self):
        with Controls(stdin=io.StringIO()) as c:
            ticks = []
            self.assertIs(c.wait(0.2, ticks.append), WaitResult.DONE)
        self.assertTrue(ticks)

    def test_wait_stops_on_sigint_and_terminates_on_sigterm(self):
        with Controls(stdin=io.StringIO()) as c:
            os.kill(os.getpid(), signal.SIGINT)
            self.assertIs(c.wait(5, lambda r: None), WaitResult.STOP)
            os.kill(os.getpid(), signal.SIGTERM)
            self.assertIs(c.wait(5, lambda r: None), WaitResult.TERM)

    def test_enter_key_on_tty(self):
        master, slave = pty.openpty()
        with os.fdopen(slave, "rb", buffering=0) as stdin, Controls(stdin=stdin) as c:
            os.write(master, b"x\r")
            deadline = time.monotonic() + 2
            events = []
            while Event.ENTER not in events and time.monotonic() < deadline:
                events += c.poll(0.1)
            self.assertIn(Event.ENTER, events)
        os.close(master)

    def test_sighup_and_sigquit_become_term(self):
        with Controls(stdin=io.StringIO()) as c:
            for sig in (signal.SIGHUP, signal.SIGQUIT):
                os.kill(os.getpid(), sig)
                self.assertIn(Event.TERM, c.poll(1.0))

    def test_failed_enter_restores_signal_handlers(self):
        master, slave = pty.openpty()
        before = signal.getsignal(signal.SIGINT)
        with os.fdopen(slave, "rb", buffering=0) as stdin, \
                mock.patch("termios.tcgetattr", side_effect=termios.error("boom")):
            with self.assertRaises(termios.error):
                Controls(stdin=stdin).__enter__()
        self.assertIs(signal.getsignal(signal.SIGINT), before)
        self.assertEqual(signal.set_wakeup_fd(-1), -1)
        os.close(master)

    def test_tty_mode_restored(self):
        master, slave = pty.openpty()
        before = termios.tcgetattr(slave)
        with os.fdopen(slave, "rb", buffering=0, closefd=False) as stdin:
            with Controls(stdin=stdin):
                during = termios.tcgetattr(slave)
                self.assertFalse(during[3] & termios.ICANON)
                self.assertFalse(during[3] & termios.ECHO)
                self.assertTrue(during[3] & termios.ISIG)
            self.assertEqual(termios.tcgetattr(slave), before)
        os.close(slave)
        os.close(master)


class RunSessionTest(unittest.TestCase):
    def setUp(self):
        self.log = Path(tempfile.mkdtemp()) / "s.jsonl"

    def run_it(self, code, controls=None, view=None):
        view = view or RecordingView()
        result = run_session(py(code), self.log, controls=controls or FakeControls(), view=view)
        return result, view

    def test_streams_lines_to_view_and_returns_exit_code(self):
        result, view = self.run_it("print('{\"a\":1}'); print('{\"b\":2}'); raise SystemExit(3)")
        self.assertEqual((result.outcome, result.exit_code, result.stop_scheduled),
                         (Outcome.EXITED, 3, False))
        self.assertEqual(view.lines, ['{"a":1}', '{"b":2}'])
        self.assertTrue(view.closed)
        self.assertEqual(self.log.read_text(), '{"a":1}\n{"b":2}\n')

    def test_child_is_detached_from_terminal_and_stdin(self):
        code = ("import os, sys, json; "
                "print(json.dumps([os.getsid(0) == os.getpid(), sys.stdin.read() == '']))")
        _, view = self.run_it(code)
        self.assertEqual(json.loads(view.lines[0]), [True, True])

    def test_single_int_schedules_stop_and_session_finishes(self):
        result, view = self.run_it("import time; time.sleep(0.6)", FakeControls({3: [Event.INT]}))
        self.assertEqual((result.outcome, result.exit_code, result.stop_scheduled),
                         (Outcome.EXITED, 0, True))
        self.assertEqual(view.stops, [True])

    def test_double_int_within_window_interrupts(self):
        code = ("import signal, sys, time\n"
                "signal.signal(signal.SIGINT, lambda *a: sys.exit(130))\n"
                "print('{}', flush=True)\n"
                "time.sleep(30)")
        started = time.monotonic()
        result, _ = self.run_it(code, FakeControls({15: [Event.INT, Event.INT]}))
        self.assertEqual((result.outcome, result.exit_code), (Outcome.INTERRUPTED, 130))
        self.assertLess(time.monotonic() - started, 10)

    def test_late_second_int_only_reschedules(self):
        result, view = self.run_it("import time; time.sleep(0.6)",
                                   FakeControls({3: [Event.INT], 4: [Event.INT]}, clock_step=4.0))
        self.assertEqual((result.outcome, result.stop_scheduled), (Outcome.EXITED, True))
        self.assertEqual(view.stops, [True])

    def test_enter_cancels_scheduled_stop(self):
        result, view = self.run_it("import time; time.sleep(0.6)",
                                   FakeControls({3: [Event.INT], 5: [Event.ENTER]}))
        self.assertFalse(result.stop_scheduled)
        self.assertEqual(view.stops, [True, False])

    def test_enter_without_scheduled_stop_is_ignored(self):
        result, view = self.run_it("import time; time.sleep(0.3)", FakeControls({2: [Event.ENTER]}))
        self.assertEqual(view.stops, [])

    def test_final_unterminated_line_reaches_view(self):
        _, view = self.run_it("import sys; sys.stdout.write('{\"a\":1}')")
        self.assertEqual(view.lines, ['{"a":1}'])

    def test_stderr_goes_to_a_sibling_file(self):
        self.run_it("import sys; sys.stderr.write('oops\\n')")
        self.assertEqual(Path(str(self.log) + ".stderr").read_text(), "oops\n")

    def test_interrupt_reaches_the_whole_process_group(self):
        pidfile = self.log.with_name("grandchild.pid")
        code = ("import subprocess, sys, time\n"
                f"p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
                f"open({str(pidfile)!r}, 'w').write(str(p.pid))\n"
                "print('{}', flush=True)\n"
                "time.sleep(60)")
        result, _ = self.run_it(code, FakeControls({15: [Event.INT, Event.INT]}))
        self.assertEqual(result.outcome, Outcome.INTERRUPTED)
        grandchild = int(pidfile.read_text())
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and _alive(grandchild):
            time.sleep(0.05)
        self.assertFalse(_alive(grandchild))

    def test_child_that_ignores_sigint_is_killed_after_grace(self):
        code = ("import signal, time\n"
                "signal.signal(signal.SIGINT, signal.SIG_IGN)\n"
                "print('{}', flush=True)\n"
                "time.sleep(60)")
        started = time.monotonic()
        result = run_session(py(code), self.log, controls=FakeControls({15: [Event.INT, Event.INT]}),
                             view=RecordingView(), kill_grace_seconds=0.5)
        self.assertEqual((result.outcome, result.exit_code), (Outcome.INTERRUPTED, -signal.SIGKILL))
        self.assertLess(time.monotonic() - started, 10)

    def test_exception_in_poll_does_not_orphan_child(self):
        class Boom(FakeControls):
            def poll(self, timeout):
                if self._polls == 10:
                    raise RuntimeError("poll failed")
                return super().poll(timeout)
        pidfile = self.log.with_name("child.pid")
        code = f"import os, time\nopen({str(pidfile)!r}, 'w').write(str(os.getpid()))\ntime.sleep(60)"
        with self.assertRaises(RuntimeError):
            run_session(py(code), self.log, controls=Boom(), view=RecordingView(),
                        kill_grace_seconds=0.5)
        self.assertFalse(_alive(int(pidfile.read_text())))

    def test_term_terminates_child(self):
        code = "import time\nprint('{}', flush=True)\ntime.sleep(30)"
        result, _ = self.run_it(code, FakeControls({5: [Event.TERM]}))
        self.assertEqual(result.outcome, Outcome.TERMINATED)
        self.assertEqual(result.exit_code, -signal.SIGTERM)

    def test_view_exception_disables_view_but_not_session(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            result, view = self.run_it("import time; print('{}'); time.sleep(0.3)",
                                       view=RecordingView(fail_on="on_tick"))
        self.assertEqual((result.outcome, result.exit_code), (Outcome.EXITED, 0))
        self.assertFalse(view.called_after_failure)
        self.assertIn("progress display disabled", err.getvalue())


class SessionDisplayTest(unittest.TestCase):
    def test_phase_change_prints_line_and_live_status(self):
        out = io.StringIO()
        now = [1000.0]
        d = SessionDisplay(Terminal(out, tty=True, color=False, width=200), iteration=1,
                           max_iterations=3, resumed=False, stall_seconds=900,
                           clock=lambda: now[0])
        text = {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "LOOP_PHASE: claiming IMP-M3-04"}]}}
        d.on_lines([json.dumps(text)])
        d.on_stop_scheduled(True)
        d.close()
        shown = out.getvalue()
        self.assertIn("claiming      IMP-M3-04\n", shown)
        self.assertIn("● iter 1/3 · IMP-M3-04 · claiming (\"IMP-M3-04\") · 0s in phase", shown)
        self.assertIn("\x1b]0;IMP-M3-04 · claiming\x07", shown)
        self.assertIn("stop scheduled after this session — Enter to cancel\n", shown)
        self.assertTrue(shown.endswith("\x1b]0;\x07"))


if __name__ == "__main__":
    unittest.main()
