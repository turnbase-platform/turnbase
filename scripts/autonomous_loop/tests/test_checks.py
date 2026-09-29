import subprocess
import tempfile
import unittest
from pathlib import Path

from autonomous_loop.checks import branches, verify

REGISTRY_ROW = "| IMP-M3-05 | Orchestration client | platform | M3-04 | {} |\n"


class Repo:
    """A clone of a bare origin, on master, with STATUS.md and a registry."""

    def __init__(self, root: Path):
        self.origin, self.path = root / "origin.git", root / "turnbase"
        self.run(root, "init", "-q", "--bare", "-b", "master", str(self.origin))
        self.run(root, "clone", "-q", str(self.origin), str(self.path))
        self.write("STATUS.md", "session 1\n")
        self.write("docs/implementation/registry.md", REGISTRY_ROW.format("READY"))
        self.commit("init")
        self.git("push", "-q", "origin", "master")

    @staticmethod
    def run(cwd, *args):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com",
                               "-c", "core.hooksPath=/dev/null", *args], cwd=cwd, check=True,
                              capture_output=True, text=True).stdout.strip()

    def git(self, *args):
        return self.run(self.path, *args)

    def write(self, rel, text):
        f = self.path / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)

    def commit(self, msg):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)

    def head(self):
        return self.git("rev-parse", "HEAD")


class VerifyTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo(Path(tempfile.mkdtemp()))
        self.start = self.repo.head()
        self.known, _ = branches(self.repo.path)

    def verify(self, label="IMP-M3-05"):
        return verify(self.repo.path, start_head=self.start, label=label, known_branches=self.known)

    def finish_properly(self):
        self.repo.write("STATUS.md", "session 2\n")
        self.repo.write("docs/implementation/registry.md", REGISTRY_ROW.format("DONE"))
        self.repo.commit("done")
        self.repo.git("push", "-q", "origin", "master")

    def test_a_properly_finished_session_passes(self):
        self.finish_properly()
        report = self.verify()
        self.assertEqual((report.problems, report.warnings), ([], []))

    def test_status_md_not_committed(self):
        self.finish_properly()
        self.start = self.repo.head()
        self.assertEqual(self.verify("IMP-GATE-88").problems,
                         ["STATUS.md was not updated and committed during the session"])

    def test_registry_row_not_done(self):
        self.repo.write("STATUS.md", "session 2\n")
        self.repo.commit("status")
        self.repo.git("push", "-q", "origin", "master")
        self.assertEqual(self.verify().problems,
                         ["docs/implementation/registry.md: IMP-M3-05 is marked 'READY', not DONE"])

    def test_labels_that_are_not_registry_rows_are_not_checked(self):
        self.repo.write("STATUS.md", "session 2\n")
        self.repo.commit("status")
        self.repo.git("push", "-q", "origin", "master")
        for label in ("IMP-GATE-88 spec fix", "IMP-M9-99", "spec-defect fix", ""):
            self.assertEqual(self.verify(label).problems, [], label)

    def test_unpushed_master(self):
        self.finish_properly()
        self.repo.write("x.txt", "x")
        self.repo.commit("local only")
        self.assertEqual(self.verify().problems,
                         ["turnbase: master is 1 commit(s) ahead of origin/master (not pushed)"])

    def test_new_branches_flagged_old_ones_ignored(self):
        self.repo.git("branch", "old")
        self.repo.git("push", "-q", "origin", "old")
        self.known, _ = branches(self.repo.path)
        self.repo.git("branch", "feat/new")
        self.repo.git("push", "-q", "origin", "feat/new")
        self.finish_properly()
        self.assertEqual(sorted(self.verify().problems),
                         ["turnbase: branch 'feat/new' still exists on origin",
                          "turnbase: local branch 'feat/new' still exists"])

    def test_unreachable_origin_is_a_warning_not_a_problem(self):
        self.finish_properly()
        self.repo.git("remote", "set-url", "origin", str(self.repo.origin) + "-gone")
        report = self.verify()
        self.assertEqual(report.problems, [])
        self.assertEqual(report.warnings, ["turnbase: could not list branches on origin"])


    def test_snapshot_is_incomplete_when_origin_is_unreachable(self):
        self.assertTrue(branches(self.repo.path)[1])
        self.repo.git("remote", "set-url", "origin", str(self.repo.origin) + "-gone")
        self.assertFalse(branches(self.repo.path)[1])


class SubmoduleTest(unittest.TestCase):
    def test_submodule_not_at_recorded_commit(self):
        def git(path, *args):
            if args[:2] == ("submodule", "status"):
                return 0, (" 57a102a turnbase-common (heads/master)\n"
                           "+7d28802 turnbase-platform (heads/master)\n"
                           "-6d05ac4 turnbase-sdk")
            return 0, ""

        report = verify(Path("/r/turnbase"), start_head=None, label="", known_branches=set(), git=git)
        self.assertEqual(len(report.problems), 1)
        self.assertTrue(report.problems[0].startswith("turnbase-platform: checked out at a commit"))

    def test_submodules_are_checked_for_branches_but_uninitialised_ones_skipped(self):
        seen = []

        def git(path, *args):
            if args[:2] == ("submodule", "status"):
                return 0, " 57a102a turnbase-common (heads/master)\n-6d05ac4 turnbase-sdk"
            if args[0] == "for-each-ref":
                seen.append(path.name)
                return 0, "master\nfeat/x" if path.name == "turnbase-common" else "master"
            return 0, ""

        report = verify(Path("/r/turnbase"), start_head=None, label="", known_branches=set(), git=git)
        self.assertEqual(sorted(seen), ["turnbase", "turnbase-common"])
        self.assertEqual(report.problems, ["turnbase-common: local branch 'feat/x' still exists"])


if __name__ == "__main__":
    unittest.main()
