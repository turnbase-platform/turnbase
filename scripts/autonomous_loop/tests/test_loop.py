import io
import json
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
        self.notes = []
        return run(self.fx.config(**cfg), controls=self.controls,
                   terminal=Terminal(self.out, tty=False, color=False),
                   notify=lambda title, body: self.notes.append(body))

    # --- outcomes -------------------------------------------------------------

    def test_done_then_finished(self):
        self.fx.scenarios({"status": "DONE IMP-A-01"}, {"status": "FINISHED all"})
        self.assertEqual(self.run_loop(max_iterations=5), 0)
        calls = self.fx.calls()
        self.assertEqual(len(calls), 2)
        self.assertEqual(session_id(calls[0])[0], "--session-id")
        prompt = calls[0][calls[0].index("-p") + 1]
        self.assertIn("LOOP_PHASE: <phase>", prompt)
        self.assertIn("not inside a command or\ntool call", prompt)
        self.assertIn("--dangerously-skip-permissions", calls[0])
        self.assertEqual(self.fx.state()["status"], "finished")
        self.assertIn("LOOP_STATUS: DONE IMP-A-01", self.out.getvalue())

    def test_skip_ci_wait_flag_adds_the_policy_to_the_prompt(self):
        self.fx.scenarios({"status": "FINISHED all"})
        self.run_loop(max_iterations=1, skip_ci_wait=True)
        prompt = self.fx.calls()[0][self.fx.calls()[0].index("-p") + 1]
        self.assertIn("do NOT wait for CI", prompt)
        self.assertIn("**CI wait:** required", prompt)

    def test_prompt_has_no_ci_policy_by_default_and_partial_respects_depends_on(self):
        self.fx.scenarios({"status": "FINISHED all"})
        self.run_loop(max_iterations=1)
        prompt = self.fx.calls()[0][self.fx.calls()[0].index("-p") + 1]
        self.assertNotIn("do NOT wait for CI", prompt)
        self.assertIn("every ID in its\n`Depends on` is DONE", prompt)

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

    # --- summary, history and notifications ---------------------------------------

    def test_summary_line_and_history(self):
        tool = {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "ls"}}]}}
        self.fx.scenarios({"status": "DONE IMP-A-01", "cost": 4.2619, "events": [tool]})
        self.assertEqual(self.run_loop(max_iterations=1), 0)
        self.assertIn("LOOP_STATUS: DONE IMP-A-01 · 0s · $4.26 · 1 tool call", self.out.getvalue())
        [entry] = [json.loads(l) for l in (self.fx.logs / "history.jsonl").read_text().splitlines()]
        self.assertEqual((entry["status"], entry["reported"], entry["cost_usd"], entry["tool_calls"]),
                         ("done", "LOOP_STATUS: DONE IMP-A-01", 4.2619, 1))
        self.assertIn("starting", entry["phases"])

    def test_history_records_sessions_without_a_status_line(self):
        self.fx.scenarios({"exit": 2})
        self.run_loop()
        [entry] = [json.loads(l) for l in (self.fx.logs / "history.jsonl").read_text().splitlines()]
        self.assertEqual((entry["status"], entry["reported"], entry["cost_usd"]), ("interrupted", None, None))

    def test_done_is_not_announced_blocked_is(self):
        self.fx.scenarios({"status": "DONE a"}, {"status": "BLOCKED needs a secret"})
        self.run_loop(max_iterations=3)
        self.assertEqual(self.notes, ["BLOCKED needs a secret"])

    def test_halts_and_max_iterations_are_announced(self):
        self.fx.scenarios({"exit": 2, "stderr": "Invalid API key"})
        self.run_loop()
        self.assertEqual(self.notes, ["claude exited with code 2: Invalid API key — loop halted."])
        self.fx.scenarios({"status": "DONE a"})
        (self.fx.fake / "count").unlink()
        self.run_loop(max_iterations=1)
        self.assertEqual(self.notes, ["Loop stopped: reached max iterations (1)."])

    # --- post-session checks ------------------------------------------------------------

    def with_status_md(self):
        (self.fx.repo / "STATUS.md").write_text("session 1\n")
        self.fx.git("add", "STATUS.md")
        self.fx.git("commit", "-q", "-m", "status")

    def test_failed_check_resumes_the_session_with_the_failures(self):
        self.with_status_md()
        self.fx.scenarios({"status": "DONE a"},
                          {"status": "DONE a", "commit": {"STATUS.md": "session 2\n"}})
        self.assertEqual(self.run_loop(max_iterations=2), 0)
        first, second = self.fx.calls()
        self.assertEqual(session_id(second), ("--resume", session_id(first)[1]))
        prompt = second[second.index("-p") + 1]
        self.assertIn("- STATUS.md was not updated and committed during the session", prompt)
        self.assertEqual(self.fx.state()["status"], "done")
        self.assertIn("Resuming the session to fix them.", self.out.getvalue())
        self.assertEqual(self.notes, ["Loop stopped: reached max iterations (2)."])

    def test_check_still_failing_after_resume_halts(self):
        self.with_status_md()
        self.fx.scenarios({"status": "DONE a"}, {"status": "DONE a"})
        self.assertEqual(self.run_loop(max_iterations=5), 1)
        self.assertEqual(len(self.fx.calls()), 2)
        state = self.fx.state()
        self.assertEqual((state["status"], state["problems"]),
                         ("unverified", ["STATUS.md was not updated and committed during the session"]))
        self.assertEqual(len(self.notes), 1)
        self.assertIn("post-session checks still failing", self.notes[0])

    def test_unverified_session_is_resumed_on_the_next_run(self):
        self.with_status_md()
        self.fx.scenarios({"status": "DONE a"}, {"status": "DONE a"},
                          {"status": "DONE a", "commit": {"STATUS.md": "fixed\n"}})
        self.assertEqual(self.run_loop(max_iterations=5), 1)
        self.assertEqual(self.run_loop(max_iterations=1), 0)
        third = self.fx.calls()[2]
        self.assertIn("post-session checks", third[third.index("-p") + 1])
        self.assertEqual(self.fx.state()["status"], "done")

    def test_no_verify_skips_checks(self):
        self.with_status_md()
        self.fx.scenarios({"status": "DONE a"})
        self.assertEqual(self.run_loop(max_iterations=1, verify=False), 0)
        self.assertEqual(self.fx.state()["status"], "done")

    # --- partly done items ------------------------------------------------------------

    def prompt(self, call):
        return call[call.index("-p") + 1]

    def test_partial_item_is_continued_by_the_next_fresh_session(self):
        self.fx.scenarios({"status": "PARTIAL IMP-A-01 e2e checks owed"}, {"status": "DONE IMP-A-01"},
                          {"status": "DONE IMP-A-02"})
        self.assertEqual(self.run_loop(max_iterations=3), 0)
        first, second, third = self.fx.calls()
        self.assertEqual(session_id(second)[0], "--session-id")
        self.assertIn("left IMP-A-01 PARTIAL. Continue IMP-A-01", self.prompt(second))
        self.assertNotIn("Continue IMP-A-01", self.prompt(third))
        self.assertIn("◐ LOOP_STATUS: PARTIAL IMP-A-01 e2e checks owed", self.out.getvalue())
        self.assertIn("IMP-A-01 left PARTIAL — the next session continues it.", self.out.getvalue())
        history = [json.loads(l) for l in (self.fx.logs / "history.jsonl").read_text().splitlines()]
        self.assertEqual([(e["status"], e["item"]) for e in history],
                         [("partial", "IMP-A-01"), ("done", None), ("done", None)])
        self.assertEqual(self.notes, ["Loop stopped: reached max iterations (3)."])

    def test_partial_streak_halts_across_runs(self):
        self.fx.scenarios(*[{"status": "PARTIAL IMP-A-01 more owed"}] * 3)
        self.assertEqual(self.run_loop(max_iterations=2), 0)
        self.assertEqual(self.run_loop(max_iterations=5), 0)
        calls = self.fx.calls()
        self.assertEqual(len(calls), 3)
        self.assertIn("Continue IMP-A-01", self.prompt(calls[2]))
        self.assertEqual(self.notes, ["IMP-A-01: PARTIAL 3 sessions in a row — loop halted."])
        self.assertEqual(self.fx.state()["status"], "partial")

    def test_another_item_in_between_resets_the_streak(self):
        self.fx.scenarios({"status": "PARTIAL IMP-A-01 x"}, {"status": "PARTIAL IMP-A-01 x"},
                          {"status": "PARTIAL IMP-B-01 y"}, {"status": "PARTIAL IMP-A-01 x"})
        self.assertEqual(self.run_loop(max_iterations=4), 0)
        self.assertEqual(self.notes, ["Loop stopped: reached max iterations (4)."])

    def test_partial_failing_checks_resumes_with_a_partial_prompt(self):
        self.with_status_md()
        self.fx.scenarios({"status": "PARTIAL IMP-A-01 x"},
                          {"status": "PARTIAL IMP-A-01 x", "commit": {"STATUS.md": "session 2\n"}})
        self.assertEqual(self.run_loop(max_iterations=2), 0)
        first, second = self.fx.calls()
        self.assertEqual(session_id(second), ("--resume", session_id(first)[1]))
        self.assertIn("You reported LOOP_STATUS: PARTIAL", self.prompt(second))
        self.assertEqual(self.fx.state()["status"], "partial")

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
