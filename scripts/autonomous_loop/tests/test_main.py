import contextlib
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from autonomous_loop.__main__ import main, parse_args
from autonomous_loop.tests.helpers import LoopFixture

WRAPPER = Path(__file__).resolve().parents[2] / "autonomous-work-loop.sh"


class MainTest(unittest.TestCase):
    def test_flags_parse_like_bash(self):
        a = parse_args(["--once", "--max", "3", "--model", "opus", "--sleep", "2.5", "--repo", "/r",
                        "--stop-file", "/s", "--state-file", "/t", "--no-resume",
                        "--stall-minutes", "4"])
        self.assertEqual((a.once, a.max, a.model, a.sleep, a.repo, a.stop_file, a.state_file,
                          a.no_resume, a.stall_minutes),
                         (True, 3, "opus", 2.5, "/r", "/s", "/t", True, 4.0))
        d = parse_args([])
        self.assertEqual((d.once, d.max, d.model, d.sleep, d.no_resume, d.stall_minutes),
                         (False, 20, "sonnet", 10.0, False, 15.0))
        self.assertEqual((d.no_notify, d.no_verify), (False, False))
        b = parse_args(["--no-notify", "--no-verify"])
        self.assertEqual((b.no_notify, b.no_verify), (True, True))

    def run_main(self, env, *argv):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, env), contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_missing_claude_exits_1_before_touching_terminal(self):
        fx = LoopFixture(Path(tempfile.mkdtemp()))
        code, out, err = self.run_main({"PATH": "", "LOG_DIR": str(fx.logs)}, "--repo", str(fx.repo))
        self.assertEqual((code, out), (1, ""))
        self.assertIn("claude CLI not found on PATH", err)

    def test_missing_settings_exits_1(self):
        fx = LoopFixture(Path(tempfile.mkdtemp()))
        (fx.repo / "scripts" / "autonomous-loop.settings.json").unlink()
        code, out, err = self.run_main({"PATH": f"{fx.bin}:{os.environ['PATH']}",
                                        "LOG_DIR": str(fx.logs)}, "--repo", str(fx.repo))
        self.assertEqual((code, out), (1, ""))
        self.assertIn("Loop settings file missing:", err)

    def test_wrapper_help(self):
        r = subprocess.run(["bash", str(WRAPPER), "--help"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Ctrl+C", r.stdout)
        self.assertIn("--stall-minutes", r.stdout)


if __name__ == "__main__":
    unittest.main()
