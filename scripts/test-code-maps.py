#!/usr/bin/env python3
"""The code-maps check passes on the committed maps and fails on a planted rename."""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cc", os.path.join(HERE, "check-corpus.py"))
cc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cc)

MAP = os.path.join(cc.ROOT, "turnbase-platform", "ARCHITECTURE.md")


class CodeMaps(unittest.TestCase):
    def test_committed_maps_resolve(self):
        self.assertEqual(cc.check_code_maps([]), [])

    def test_planted_renames_fail(self):
        original = open(MAP, newline="").read()
        try:
            for planted, expect in [
                ("`RoomServiceRenamed`", "RoomServiceRenamed"),
                ("`RoomService.noSuchMethod`", "noSuchMethod"),
                ("`io.turnbase.platform.renamed`", "io.turnbase.platform.renamed"),
                ("`src/main/java/Gone.java`", "Gone.java"),
            ]:
                with open(MAP, "w", newline="") as f:
                    f.write(original + "\n" + planted + "\n")
                problems = cc.check_code_maps([])
                self.assertTrue(any(expect in p for p in problems), (planted, problems))
        finally:
            with open(MAP, "w", newline="") as f:
                f.write(original)


if __name__ == "__main__":
    unittest.main()
