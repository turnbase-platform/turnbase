import io
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from autonomous_loop.display import Terminal
from autonomous_loop.loop import run
from autonomous_loop.session import Event, WaitResult
from autonomous_loop.state import StateFile
from autonomous_loop.tests.helpers import FakeControls, LoopFixture, session_id


class LoopTest(unittest.TestCase):
    def setUp(self):
        self.fx = LoopFixture(Path(tempfile.mkdtemp()))
        patcher = mock.patch.dict(os.environ, self.fx.env())
        patcher.start()
        self.addCleanup(patcher.stop)
        self.out = io.StringIO()

    def run_loop(self, controls=None, **cfg):
        self.controls = controls or FakeControls()
        return run(self.fx.config(**cfg), controls=self.controls,
                   terminal=Terminal(self.out, tty=False, color=False))

    # --- outcomes -------------------------------------------------------------

    def test_done_then_finished(self):
        self.fx.scenarios({"status": "DONE IMP-A-01"}, {"status": "FINISHED all"})
        self.assertEqual(self.run_loop(max_iterations=5), 0)
        calls = self.fx.calls()
        self.assertEqual(len(calls), 2)
        self.assertEqual(session_id(calls[0])[0], "--session-id")
        self.assertIn("LOOP_PHASE: <phase>", calls[0][calls[0].index("-p") + 1])
        self.assertIn("--dangerously-skip-permissions", calls[0])
        self.assertEqual(self.fx.state()["status"], "finished")
        self.assertIn("LOOP_STATUS: DONE IMP-A-01", self.out.getvalue())

    def test_countdown_between_sessions_but_not_before_first(self):
        self.fx.scenarios({"status": "DONE a"}, {"status": "DONE b"})
        self.assertEqual(self.run_loop(max_iterations=2, sleep_seconds=10), 0)
        self.assertEqual(self.controls.waits, [10])
        self.assertIn("Reached max iterations (2). Stopping.", self.out.getvalue())

    def test_blocked_halts_with_zero(self):
        self.fx.scenarios({"status": "BLOCKED needs a secret"})
        self.assertEqual(self.run_loop(max_iterations=3), 0)
        self.assertEqual((len(self.fx.calls()), self.fx.state()["status"]), (1, "blocked"))

    def test_unrecognised_status_fails(self):
        self.fx.scenarios({"status": "MAYBE"})
        self.assertEqual(self.run_loop(), 1)
        self.assertEqual(self.fx.state()["status"], "failed")

    def test_nonzero_exit_leaves_session_resumable(self):
        self.fx.scenarios({"exit": 2}, {"status": "DONE a"})
        self.assertEqual(self.run_loop(), 1)
        self.assertEqual(self.fx.state()["status"], "interrupted")
        self.assertEqual(self.run_loop(max_iterations=1), 0)
        first, second = self.fx.calls()
        self.assertEqual(session_id(second), ("--resume", session_id(first)[1]))

    def test_nonzero_exit_shows_claude_stderr(self):
        self.fx.scenarios({"exit": 2, "stderr": "Invalid API key"})
        self.assertEqual(self.run_loop(), 1)
        self.assertIn("Invalid API key", self.out.getvalue())

    def test_is_error_leaves_session_resumable(self):
        self.fx.scenarios({"is_error": True, "status": "DONE a"})
        self.assertEqual(self.run_loop(), 1)
        self.assertEqual(self.fx.state()["status"], "interrupted")

    def test_missing_status_line_resumes_same_session(self):
        self.fx.scenarios({"result": "stopped early"}, {"status": "DONE a"})
        self.assertEqual(self.run_loop(max_iterations=2), 0)
        first, second = self.fx.calls()
        self.assertEqual(session_id(second), ("--resume", session_id(first)[1]))

    # --- preconditions and dirty tree ----------------------------------------

    def test_dirty_after_report_is_resumable(self):
        dirty = str(self.fx.repo / "leftover.txt")
        self.fx.scenarios({"status": "DONE a", "touch": [dirty]},
                          {"status": "DONE a", "remove": [dirty]})
        self.assertEqual(self.run_loop(), 1)
        self.assertEqual(self.fx.state()["status"], "dirty")
        self.assertEqual(self.fx.state()["reported"], "LOOP_STATUS: DONE a")
        self.assertEqual(self.run_loop(max_iterations=1), 0)
        self.assertEqual(session_id(self.fx.calls()[1])[0], "--resume")

    def test_fresh_session_refuses_dirty_tree(self):
        (self.fx.repo / "stray.txt").write_text("x")
        self.assertEqual(self.run_loop(), 1)
        self.assertEqual(self.fx.calls(), [])
        self.assertIn("Working tree not clean before iteration 1", self.out.getvalue())

    def test_fresh_session_refuses_other_branch(self):
        self.fx.git("checkout", "-q", "-b", "feat/x")
        self.assertEqual(self.run_loop(), 1)
        self.assertIn("Not on master before iteration 1 (on 'feat/x')", self.out.getvalue())

    def test_no_resume_starts_fresh(self):
        self.fx.logs.mkdir()
        StateFile(self.fx.logs / "state.json").write("old-sid", 1, "interrupted")
        self.fx.scenarios({"status": "DONE a"})
        self.assertEqual(self.run_loop(resume=False, max_iterations=1), 0)
        flag, sid = session_id(self.fx.calls()[0])
        self.assertEqual(flag, "--session-id")
        self.assertNotEqual(sid, "old-sid")

    def test_stop_file_halts_before_iteration(self):
        cfg_stop = self.fx.repo / ".autonomous-loop.stop"
        cfg_stop.write_text("")
        self.assertEqual(self.run_loop(), 0)
        self.assertEqual(self.fx.calls(), [])
        self.assertFalse(cfg_stop.exists())

    # --- rate limits ------------------------------------------------------------

    def test_rate_limit_waits_until_reset_then_resumes(self):
        resets = int(time.time()) + 100
        self.fx.scenarios({"api_error_status": 429, "result": "limit", "resets_at": resets},
                          {"status": "DONE a"})
        self.assertEqual(self.run_loop(max_iterations=2, sleep_seconds=10), 0)
        self.assertTrue(120 < self.controls.waits[0] <= 131, self.controls.waits)
        self.assertEqual(self.controls.waits[1:], [10])
        first, second = self.fx.calls()
        self.assertEqual(session_id(second), ("--resume", session_id(first)[1]))

    def test_rate_limit_text_without_reset_uses_fallback(self):
        self.fx.scenarios({"result": "You've hit your session limit"}, {"status": "DONE a"})
        self.assertEqual(self.run_loop(max_iterations=2), 0)
        self.assertEqual(self.controls.waits, [900])

    def test_ctrl_c_during_rate_limit_wait_stops_and_stays_resumable(self):
        self.fx.scenarios({"api_error_status": 429, "result": "limit"})
        code = self.run_loop(FakeControls(wait_results=[WaitResult.STOP]), max_iterations=3)
        self.assertEqual(code, 0)
        self.assertEqual(self.fx.state()["status"], "rate_limited")
        self.assertIn("Stopped at operator request.", self.out.getvalue())

    # --- operator controls --------------------------------------------------------

    def test_scheduled_stop_finishes_session_then_exits(self):
        self.fx.scenarios({"status": "DONE a", "hold": 0.5}, {"status": "DONE b"})
        code = self.run_loop(FakeControls({5: [Event.INT]}), max_iterations=2, sleep_seconds=10)
        self.assertEqual(code, 0)
        self.assertEqual(len(self.fx.calls()), 1)
        self.assertEqual(self.fx.state()["status"], "done")
        self.assertEqual(self.controls.waits, [])
        self.assertIn("Stopped at operator request.", self.out.getvalue())

    def test_double_ctrl_c_interrupts_and_exits_130(self):
        self.fx.scenarios({"status": "DONE a", "hold": 10})
        code = self.run_loop(FakeControls({25: [Event.INT, Event.INT]}), max_iterations=2)
        self.assertEqual(code, 130)
        self.assertEqual(self.fx.state()["status"], "interrupted")
        self.assertIn("0 SIGINT", self.fx.signals())

    def test_sigterm_exits_143(self):
        self.fx.scenarios({"status": "DONE a", "hold": 10})
        code = self.run_loop(FakeControls({25: [Event.TERM]}))
        self.assertEqual(code, 143)
        self.assertEqual(self.fx.state()["status"], "interrupted")
        self.assertIn("0 SIGTERM", self.fx.signals())

    def test_scheduled_stop_beats_rate_limit_wait(self):
        self.fx.scenarios({"api_error_status": 429, "result": "limit", "hold": 0.5})
        code = self.run_loop(FakeControls({5: [Event.INT]}), max_iterations=3)
        self.assertEqual(code, 0)
        self.assertEqual(self.fx.state()["status"], "rate_limited")
        self.assertEqual(self.controls.waits, [])

    def test_ctrl_c_during_countdown_stops_before_next_session(self):
        self.fx.scenarios({"status": "DONE a"}, {"status": "DONE b"})
        code = self.run_loop(FakeControls(wait_results=[WaitResult.STOP]),
                             max_iterations=2, sleep_seconds=10)
        self.assertEqual(code, 0)
        self.assertEqual(len(self.fx.calls()), 1)
        self.assertEqual(self.fx.state()["status"], "done")

    def test_log_is_byte_identical_to_claude_output(self):
        self.fx.scenarios({"status": "DONE a", "events": [{"type": "assistant", "x": "é"}]})
        self.run_loop(max_iterations=1)
        # state.json drops log_file after the final "done" write, as the bash version did.
        log = next(self.fx.logs.glob("*-iter1.jsonl"))
        lines = log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[1], '{"type": "assistant", "x": "\\u00e9"}')


if __name__ == "__main__":
    unittest.main()
