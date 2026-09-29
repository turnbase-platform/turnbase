import json
import tempfile
import unittest
from pathlib import Path

from autonomous_loop import prompts
from autonomous_loop.state import StateFile


class StateFileTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.state = StateFile(self.dir / "state.json")

    def test_write_matches_bash_fields(self):
        self.state.write("sid-1", 2, "running", log_file="/x/y.jsonl")
        doc = json.loads((self.dir / "state.json").read_text())
        self.assertEqual(
            {k: doc[k] for k in ("session_id", "iteration", "status", "log_file")},
            {"session_id": "sid-1", "iteration": 2, "status": "running", "log_file": "/x/y.jsonl"},
        )
        self.assertRegex(doc["updated_at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()), ["state.json"])

    def test_write_replaces_extra_fields(self):
        self.state.write("sid-1", 1, "running", log_file="a")
        self.state.write("sid-1", 1, "done")
        self.assertNotIn("log_file", self.state.read())

    def test_read_missing_or_invalid_is_empty(self):
        self.assertEqual(self.state.read(), {})
        (self.dir / "state.json").write_text("{not json")
        self.assertEqual(self.state.read(), {})
        (self.dir / "state.json").write_text("[1]")
        self.assertEqual(self.state.read(), {})


class PromptsTest(unittest.TestCase):
    def test_both_prompts_carry_phase_markers_and_status_contract(self):
        for prompt in (prompts.PROMPT, prompts.RESUME_PROMPT):
            with self.subTest(prompt=prompt[:30]):
                self.assertIn("LOOP_PHASE: <phase>", prompt)
                self.assertIn("starting, claiming, reading, implementing, testing,", prompt)
                self.assertTrue(prompt.endswith("LOOP_STATUS: FINISHED <all items complete>"))

    def test_prompt_openings_are_unchanged(self):
        self.assertTrue(prompts.PROMPT.startswith("Pick up the next TurnBase Phase 1 work item"))
        self.assertTrue(prompts.RESUME_PROMPT.startswith("This session was interrupted before"))


if __name__ == "__main__":
    unittest.main()
