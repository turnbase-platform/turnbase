#!/usr/bin/env python3
"""The code-refs check passes on the committed sources and fails on a planted bad reference."""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cc", os.path.join(HERE, "check-corpus.py"))
cc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cc)

SRC = os.path.join(cc.ROOT, "turnbase-platform", "src", "main", "java", "io", "turnbase",
                   "platform", "account", "LoginService.java")


class CodeRefs(unittest.TestCase):
    def test_committed_sources_resolve(self):
        self.assertEqual(cc.check_code_refs(cc.markdown_files()), [])

    def test_planted_references_fail(self):
        original = open(SRC, newline="").read()
        try:
            for planted, expect in [
                ("// see no-such-spec.md for the rule", "no-such-spec.md"),
                ("// see room-lifecycle.md §99 for the rule", "no §99"),
                ("// see `room-lifecycle.md` §1.1/§77", "no §77"),
            ]:
                with open(SRC, "w", newline="") as f:
                    f.write(original + "\n" + planted + "\n")
                problems = cc.check_code_refs(cc.markdown_files())
                self.assertTrue(any(expect in p for p in problems), (planted, problems))
        finally:
            with open(SRC, "w", newline="") as f:
                f.write(original)


if __name__ == "__main__":
    unittest.main()
