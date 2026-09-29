import base64
import re
import subprocess
import unittest

from autonomous_loop.notify import Notifier, toast_command


def script_of(argv):
    return base64.b64decode(argv[argv.index("-EncodedCommand") + 1]).decode("utf-16-le")


class ToastCommandTest(unittest.TestCase):
    def test_non_ascii_survives_encoding(self):
        argv = toast_command("TurnBase loop", "iter 1 · IMP-M3-05 · BLOCKED")
        self.assertEqual(argv[:4], ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand"])
        self.assertIn("<text>iter 1 · IMP-M3-05 · BLOCKED</text>", script_of(argv))

    def test_body_cannot_break_out_of_xml_or_the_powershell_string(self):
        script = script_of(toast_command("t", "<b>it's</b> & \"x\""))
        loaded = re.search(r"LoadXml\('(.*)'\)", script).group(1)
        self.assertIn("&lt;b&gt;it''s&lt;/b&gt; &amp; \"x\"", loaded)
        # every quote inside the single-quoted string is doubled
        self.assertNotRegex(loaded.replace("''", ""), "'")


class NotifierTest(unittest.TestCase):
    def setUp(self):
        self.bells, self.runs = [], []

    def notifier(self, **kw):
        kw.setdefault("powershell", "/mnt/c/ps.exe")
        kw.setdefault("run", lambda argv, **_: self.runs.append(argv))
        return Notifier(bell=lambda: self.bells.append(1), **kw)

    def test_bell_and_toast(self):
        n = self.notifier()
        n("TurnBase loop", "blocked")
        n.flush()
        self.assertEqual(len(self.bells), 1)
        self.assertEqual(self.runs[0][0], "/mnt/c/ps.exe")

    def test_disabled_does_nothing(self):
        n = self.notifier(enabled=False)
        n("t", "b")
        n.flush()
        self.assertEqual((self.bells, self.runs), ([], []))

    def test_without_powershell_only_the_bell(self):
        n = self.notifier(powershell="")
        n("t", "b")
        n.flush()
        self.assertEqual((len(self.bells), self.runs), (1, []))

    def test_failed_toast_stops_trying_but_keeps_ringing(self):
        calls = []

        def broken(argv, **_):
            calls.append(argv)
            raise OSError("interop disabled")

        n = self.notifier(run=broken)
        n("t", "1")
        n.flush()
        n("t", "2")
        n.flush()
        self.assertEqual((len(calls), len(self.bells)), (1, 2))

    def test_timeout_is_swallowed(self):
        def slow(argv, **_):
            raise subprocess.TimeoutExpired(argv, 30)

        n = self.notifier(run=slow)
        n("t", "b")
        n.flush()
        self.assertEqual(len(self.bells), 1)


if __name__ == "__main__":
    unittest.main()
