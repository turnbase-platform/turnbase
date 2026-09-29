import json
import re
import unittest

from autonomous_loop.progress import (
    InFlight,
    Idle,
    Progress,
    apply,
    idle,
    infer_phase,
    summarize,
)

REPO = "/home/u/proj/turnbase"


def text(t):
    return json.dumps(
        {
            "type": "assistant",
            "message": {"role": "assistant", "content": [{"type": "text", "text": t}]},
            "parent_tool_use_id": None,
        }
    )


def tool(tid, name, inp):
    return json.dumps(
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [{"type": "tool_use", "id": tid, "name": name, "input": inp}],
            },
        }
    )


def result(tid):
    return json.dumps(
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {"tool_use_id": tid, "type": "tool_result", "content": "ok", "is_error": False}
                ],
            },
        }
    )


HEARTBEAT = json.dumps(
    {
        "type": "tool_progress",
        "tool_use_id": "t1-heartbeat-0",
        "tool_name": "Bash",
        "parent_tool_use_id": "t1",
        "elapsed_time_seconds": 29,
        "heartbeat": True,
    }
)
THINKING = json.dumps({"type": "system", "subtype": "thinking_tokens"})
RATE = json.dumps({"type": "rate_limit_event", "rate_limit_info": {"resetsAt": 1}})


class MarkerTest(unittest.TestCase):
    def test_marker_sets_phase_note_and_item(self):
        p = Progress.start(100.0)
        changes = apply(p, text("Claiming now.\nLOOP_PHASE: claiming IMP-M3-04"), 105.0)
        self.assertEqual(
            [(c.phase, c.note, c.reported, c.at) for c in changes],
            [("claiming", "IMP-M3-04", True, 105.0)],
        )
        self.assertEqual(
            (p.phase, p.note, p.item, p.phase_since, p.reported),
            ("claiming", "IMP-M3-04", "IMP-M3-04", 105.0, True),
        )

    def test_two_markers_in_one_message_both_apply(self):
        p = Progress.start(0.0)
        changes = apply(p, text("LOOP_PHASE: claiming IMP-M3-04\nLOOP_PHASE: reading proto"), 1.0)
        self.assertEqual([c.phase for c in changes], ["claiming", "reading"])
        self.assertEqual((p.phase, p.note, p.item), ("reading", "proto", "IMP-M3-04"))

    def test_unknown_phase_is_kept_verbatim(self):
        p = Progress.start(0.0)
        apply(p, text("LOOP_PHASE: Debugging flaky test"), 1.0)
        self.assertEqual((p.phase, p.note), ("Debugging", "flaky test"))

    def test_note_truncated_to_80(self):
        p = Progress.start(0.0)
        apply(p, text("LOOP_PHASE: testing " + "x" * 200), 1.0)
        self.assertEqual(len(p.note), 80)
        self.assertTrue(p.note.endswith("…"))

    def test_marker_not_at_line_start_is_ignored(self):
        p = Progress.start(0.0)
        self.assertEqual(apply(p, text("see LOOP_PHASE: testing"), 1.0), [])
        self.assertEqual(p.phase, "starting")
        self.assertFalse(p.reported)

    def test_same_phase_new_note_keeps_phase_since(self):
        p = Progress.start(0.0)
        apply(p, text("LOOP_PHASE: testing unit"), 10.0)
        changes = apply(p, text("LOOP_PHASE: testing integration"), 20.0)
        self.assertEqual([c.note for c in changes], ["integration"])
        self.assertEqual(p.phase_since, 10.0)

    def test_identical_marker_is_not_a_change(self):
        p = Progress.start(0.0)
        apply(p, text("LOOP_PHASE: testing unit"), 10.0)
        self.assertEqual(apply(p, text("LOOP_PHASE: testing unit"), 20.0), [])


class FallbackTest(unittest.TestCase):
    def test_rules(self):
        cases = [
            ("Skill", {"skill": "work-item"}, "claiming"),
            ("Edit", {"file_path": f"{REPO}/STATUS.md"}, "wrapping-up"),
            ("Bash", {"command": "gh run watch 123 --exit-status"}, "ci-wait"),
            ("Bash", {"command": "git merge --ff-only feat/x"}, "merging"),
            ("Bash", {"command": "git push origin master"}, "merging"),
            ("Bash", {"command": "cd turnbase-game-host && ./mvnw -q verify"}, "testing"),
            ("Bash", {"command": "npm run test"}, "testing"),
            ("Write", {"file_path": f"{REPO}/turnbase-game-host/src/Foo.java"}, "implementing"),
            ("Read", {"file_path": f"{REPO}/docs/specs/INDEX.md"}, "reading"),
            ("Bash", {"command": "ls"}, None),
            ("Read", {"file_path": f"{REPO}/turnbase-sdk/pom.xml"}, None),
        ]
        for name, inp, expected in cases:
            with self.subTest(name=name, inp=inp):
                self.assertEqual(infer_phase(name, inp), expected)

    def test_fallback_applies_before_first_marker(self):
        p = Progress.start(0.0)
        changes = apply(p, tool("t1", "Skill", {"skill": "work-item"}), 5.0)
        self.assertEqual([(c.phase, c.reported) for c in changes], [("claiming", False)])
        self.assertFalse(p.reported)

    def test_fallback_disabled_after_first_marker(self):
        p = Progress.start(0.0)
        apply(p, text("LOOP_PHASE: implementing bridge"), 1.0)
        self.assertEqual(apply(p, tool("t1", "Bash", {"command": "gh run watch 1"}), 2.0), [])
        self.assertEqual(p.phase, "implementing")


class ItemTest(unittest.TestCase):
    def test_item_from_claim_commit_when_no_marker(self):
        p = Progress.start(0.0)
        apply(p, tool("t1", "Bash", {"command": 'git commit -m "chore: claim IMP-M3-04 (session 89)"'}), 1.0)
        self.assertEqual(p.item, "IMP-M3-04")

    def test_marker_item_wins_over_later_claim_command(self):
        p = Progress.start(0.0)
        apply(p, text("LOOP_PHASE: claiming IMP-A1-01"), 1.0)
        apply(p, tool("t1", "Bash", {"command": 'git commit -m "chore: claim IMP-B2-02"'}), 2.0)
        self.assertEqual(p.item, "IMP-A1-01")


class LastActionTest(unittest.TestCase):
    def test_summaries(self):
        cases = [
            ("Bash", {"command": "./mvnw verify", "description": "Run unit tests"}, "Run unit tests"),
            ("Bash", {"command": "./mvnw verify"}, "./mvnw verify"),
            ("Bash", {"command": "echo a\n  && echo b"}, "echo a && echo b"),
            ("Bash", {"command": "x" * 100}, "x" * 59 + "…"),
            ("Read", {"file_path": f"{REPO}/docs/implementation/registry.md"}, "Read registry.md"),
            ("Skill", {"skill": "work-item"}, "Skill work-item"),
            ("Agent", {"description": "Explore specs"}, "Agent Explore specs"),
            ("TodoWrite", {}, "TodoWrite"),
        ]
        for name, inp, expected in cases:
            with self.subTest(name=name, inp=inp):
                self.assertEqual(summarize(name, inp), expected)

    def test_apply_records_last_action_and_time(self):
        p = Progress.start(0.0)
        apply(p, tool("t1", "Read", {"file_path": "/a/b.md"}), 7.0)
        self.assertEqual((p.last_action, p.last_action_at), ("Read b.md", 7.0))


class IdleTest(unittest.TestCase):
    def test_quiet_below_threshold_is_none(self):
        p = Progress.start(0.0)
        self.assertIsNone(idle(p, 899.0, 900.0))

    def test_stall_after_threshold(self):
        p = Progress.start(0.0)
        apply(p, text("hi"), 10.0)
        self.assertEqual(idle(p, 910.0, 900.0), Idle("stall", 900.0))

    def test_heartbeats_thinking_and_rate_events_are_not_activity(self):
        p = Progress.start(0.0)
        apply(p, tool("t1", "Bash", {"command": "sleep 5000"}), 10.0)
        for line in (HEARTBEAT, THINKING, RATE):
            apply(p, line, 500.0)
        self.assertEqual(p.last_activity_at, 10.0)
        self.assertEqual(idle(p, 910.0, 900.0), Idle("stall", 900.0))

    def test_long_wait_in_flight_shows_running(self):
        p = Progress.start(0.0)
        apply(p, tool("t1", "Bash", {"command": "gh run watch 9 --exit-status"}), 10.0)
        self.assertEqual(idle(p, 1000.0, 900.0), Idle("running", 990.0))

    def test_finished_long_wait_is_no_longer_exempt(self):
        p = Progress.start(0.0)
        apply(p, tool("t1", "Bash", {"command": "gh run watch 9"}), 10.0)
        apply(p, result("t1"), 20.0)
        self.assertEqual(p.in_flight, {})
        self.assertEqual(idle(p, 920.0, 900.0), Idle("stall", 900.0))

    def test_in_flight_records_bash_command(self):
        p = Progress.start(0.0)
        apply(p, tool("t1", "Bash", {"command": "./mvnw verify"}), 3.0)
        self.assertEqual(p.in_flight, {"t1": InFlight("./mvnw verify", 3.0)})


class RobustnessTest(unittest.TestCase):
    def test_garbage_is_ignored(self):
        bad = [
            "",
            "not json",
            "[]",
            '"str"',
            '{"type":"assistant"}',
            '{"type":"assistant","message":{"content":"plain"}}',
            '{"type":"assistant","message":{"content":[1,null]}}',
            '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash","input":"x"}]}}',
            '{"type":"assistant","message":{"content":[{"type":"text","text":null}]}}',
            '{"type":"user","message":{"content":[{"type":"tool_result"}]}}',
            '{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":[]}]}}',
            '{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":{}}]}}',
        ]
        p = Progress.start(0.0)
        for line in bad:
            with self.subTest(line=line):
                apply(p, line, 1.0)
        self.assertEqual(p.phase, "starting")

    def test_control_characters_never_reach_the_terminal(self):
        p = Progress.start(0.0)
        text = {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "LOOP_PHASE: read\x1bing IMP-A-01\tnote\x07"},
            {"type": "tool_use", "id": "t", "name": "Bash",
             "input": {"command": "ls", "description": "list\x1b[2Jfiles"}}]}}
        changes = apply(p, json.dumps(text), 1.0)
        for s in (changes[0].phase, changes[0].note, p.last_action):
            self.assertIsNone(re.search(r"[\x00-\x1f\x7f]", s), repr(s))


if __name__ == "__main__":
    unittest.main()
