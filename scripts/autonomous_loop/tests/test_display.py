import io
import os
import time
import unittest
from unittest import mock

from autonomous_loop.display import (
    DIM,
    RED,
    Terminal,
    clock,
    fmt_duration,
    phase_segments,
    render,
    status_segments,
    title_text,
)
from autonomous_loop.progress import InFlight, PhaseChange, Progress


class DurationTest(unittest.TestCase):
    def test_formats(self):
        cases = [(0, "0s"), (40, "40s"), (59.9, "59s"), (60, "1m"), (840, "14m"),
                 (3599, "59m"), (3600, "1h00m"), (4320, "1h12m"), (-5, "0s")]
        for seconds, expected in cases:
            with self.subTest(seconds=seconds):
                self.assertEqual(fmt_duration(seconds), expected)


class RenderTest(unittest.TestCase):
    def test_plain_when_no_color(self):
        self.assertEqual(render([("a", RED), ("b", "")], color=False), "ab")

    def test_sgr_when_color(self):
        self.assertEqual(render([("a", RED), ("b", "")], color=True), "\x1b[31ma\x1b[0mb")

    def test_truncates_to_width_with_ellipsis(self):
        self.assertEqual(render([("abc", ""), ("def", RED)], color=False, width=5), "abcd…")

    def test_exact_width_is_untouched(self):
        self.assertEqual(render([("abc", ""), ("def", "")], color=False, width=6), "abcdef")


class StatusLineTest(unittest.TestCase):
    def progress(self):
        p = Progress.start(1000.0)
        p.item, p.phase, p.note = "IMP-M3-04", "testing", "fixing flaky WS test"
        p.phase_since = 1000.0
        p.last_action, p.last_action_at = "./mvnw verify", 1800.0
        p.last_activity_at = 1800.0
        return p

    def plain(self, p, now=1840.0, stop=False):
        return render(
            status_segments(p, iteration=3, max_iterations=20, now=now,
                            stop_scheduled=stop, stall_seconds=900),
            color=False,
        )

    def test_format_matches_spec(self):
        self.assertEqual(
            self.plain(self.progress()),
            '● iter 3/20 · IMP-M3-04 · testing ("fixing flaky WS test") · 14m in phase'
            " · last: ./mvnw verify, 40s ago",
        )

    def test_no_item_yet_and_resumed_start(self):
        p = Progress.start(0.0, resumed=True)
        self.assertEqual(self.plain(p, now=5.0),
                         "● iter 3/20 · no item yet · starting (resumed) · 5s in phase")

    def test_stall_warning_precedes_last_action(self):
        p = self.progress()
        p.last_activity_at = 1840.0 - 960
        self.assertIn("· ⚠ no activity 16m · last:", self.plain(p))

    def test_running_long_wait(self):
        p = self.progress()
        p.last_activity_at = 1840.0 - 960
        p.in_flight["t"] = InFlight("gh run watch 1", 1840.0 - 720)
        self.assertIn("· running 12m · last:", self.plain(p))

    def test_stop_scheduled_segment(self):
        self.assertIn("· ⏹ stop after session — Enter to cancel · last:",
                      self.plain(self.progress(), stop=True))

    def test_unknown_phase_is_dim(self):
        p = self.progress()
        p.phase = "debugging"
        segs = status_segments(p, iteration=1, max_iterations=1, now=1840.0,
                               stop_scheduled=False, stall_seconds=900)
        self.assertIn(("debugging", DIM), segs)


class PhaseLineTest(unittest.TestCase):
    def test_reported(self):
        at = time.mktime((2026, 9, 27, 19, 41, 3, 0, 0, -1))
        line = render(phase_segments(PhaseChange(at, "claiming", "IMP-M3-04", True)), color=False)
        self.assertEqual(line, "  19:41:03  " + "claiming".ljust(13) + " IMP-M3-04")

    def test_inferred_is_marked(self):
        line = render(phase_segments(PhaseChange(0.0, "testing", "", False)), color=False)
        self.assertTrue(line.endswith("testing".ljust(13) + " (inferred)"))

    def test_title(self):
        p = Progress.start(0.0)
        self.assertEqual(title_text(p), "loop · starting")
        p.item, p.phase = "IMP-M3-04", "testing"
        self.assertEqual(title_text(p), "IMP-M3-04 · testing")


class TerminalTest(unittest.TestCase):
    def test_print_clears_and_redraws_live_line(self):
        out = io.StringIO()
        t = Terminal(out, tty=True, color=False, width=80)
        t.live([("x", "")])
        t.print("hello")
        self.assertEqual(out.getvalue(),
                         "\r\x1b[2Kx" + "\r\x1b[2K" + "hello\n" + "\r\x1b[2Kx")

    def test_non_tty_prints_only_permanent_lines(self):
        out = io.StringIO()
        t = Terminal(out, tty=False)
        t.live([("x", "")])
        t.title("t")
        t.print([("hello", RED)])
        t.clear_live()
        t.reset_title()
        self.assertEqual(out.getvalue(), "hello\n")

    def test_live_truncated_to_width(self):
        out = io.StringIO()
        Terminal(out, tty=True, color=False, width=10).live([("x" * 50, "")])
        self.assertEqual(out.getvalue(), "\r\x1b[2K" + "x" * 8 + "…")

    def test_title_and_reset(self):
        out = io.StringIO()
        t = Terminal(out, tty=True, color=False)
        t.title("IMP · testing")
        t.reset_title()
        self.assertEqual(out.getvalue(), "\x1b]0;IMP · testing\x07\x1b]0;\x07")

    def test_no_color_env_disables_color(self):
        with mock.patch.dict(os.environ, {"NO_COLOR": "1"}):
            self.assertFalse(Terminal(io.StringIO(), tty=True).color)
        with mock.patch.dict(os.environ, {"TERM": "dumb"}):
            self.assertFalse(Terminal(io.StringIO(), tty=True).color)

    def test_clock_format(self):
        at = time.mktime((2026, 9, 27, 7, 5, 9, 0, 0, -1))
        self.assertEqual(clock(at), "07:05:09")


if __name__ == "__main__":
    unittest.main()
