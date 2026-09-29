"""Runs non-interactive `claude` sessions back to back, each one picking up the
next TurnBase IMP-* work item via the `work-item` skill and finishing it
end-to-end (commit, merge to master, delete branch, update STATUS.md).

DANGER: each session runs with --dangerously-skip-permissions (no human
approves any tool call, including Bash, git push, file deletion, etc.) and
is free to commit/merge into master. Only run this against a repo you can
afford to have modified unattended, and watch the first few iterations
before leaving it unattended for real. Do NOT run this on a machine/account
where `master` is pushed somewhere shared unless you intend that.

Usage:
  scripts/autonomous-work-loop.sh [--once] [--max N]
                                   [--model NAME] [--sleep SECONDS]
                                   [--repo DIR] [--stop-file PATH]
                                   [--no-resume] [--state-file PATH]
                                   [--stall-minutes N]

Stop it gracefully mid-run by creating the stop file (default:
.autonomous-loop.stop in the repo root) — it's checked between iterations,
never mid-session.

Progress
--------
* Each session shows one live status line — iteration, work item, phase,
  time in phase and the last action — and prints a permanent line whenever
  the phase changes. The agent reports phases itself with LOOP_PHASE lines;
  until the first one, the phase is guessed from its tool calls.
* The live line turns into a stall warning after --stall-minutes (default 15)
  without any activity. Logs are still written to $LOG_DIR
  (default ~/.turnbase-loop-logs), one stream-json file per session.

Controls
--------
* Ctrl+C during a session schedules a stop after that session finishes;
  Enter cancels the scheduled stop.
* A second Ctrl+C within 3 seconds interrupts the session (forwarded to
  claude as SIGINT) and exits with 130.
* Between sessions there is a --sleep second countdown (none before the
  first); Ctrl+C during it stops the loop.
* SIGTERM interrupts the session and exits with 143.

Resumability
------------
* The session id is generated up front and recorded in the state file
  BEFORE `claude` starts, so a run that is killed at any point — even
  `kill -9` before it produces a byte of output — is still resumable.
* An interrupted session (double Ctrl+C, SIGTERM) is left resumable;
  nothing is rolled back.
* On the next start the loop resumes an unfinished session instead of
  starting a fresh one, and keeps resuming it until it reports a
  LOOP_STATUS line. Pass --no-resume to force a fresh session.
* A resumed session is mid-work by definition, so a dirty tree or a
  feature branch is never a reason to refuse one. Only a fresh session
  requires a clean master.
* A session that reports LOOP_STATUS but leaves the tree dirty or off
  master is recorded as `dirty`, which is resumable: the next start asks
  that same session to finish or unwind its own work, rather than
  starting a fresh session and refusing to run on that session's leftovers.
* A 429 session limit is detected, the quota reset time is read out of the
  session transcript, and the loop sleeps until then and resumes the same
  session rather than losing the in-progress work item. Ctrl+C during that
  wait stops the loop and leaves the session resumable.

--max bounds `claude` invocations, not work items: a resumed session spends
one, so an item that needs two resumes costs three of them.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

from .display import Terminal
from .loop import Config, run
from .session import Controls


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="autonomous-work-loop.sh", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--once", action="store_true", help="run a single session")
    p.add_argument("--max", type=int, default=20, help="maximum claude invocations (default 20)")
    p.add_argument("--model", default="sonnet", help="claude model (default sonnet)")
    p.add_argument("--sleep", type=float, default=10, help="countdown between sessions (default 10)")
    p.add_argument("--repo", help="repository root (default: this script's repo)")
    p.add_argument("--stop-file", help="stop file (default: <repo>/.autonomous-loop.stop)")
    p.add_argument("--state-file", help="state file (default: $LOG_DIR/state.json)")
    p.add_argument("--no-resume", action="store_true", help="never resume an unfinished session")
    p.add_argument("--stall-minutes", type=float, default=15,
                   help="warn after this many minutes without activity (default 15)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    repo = Path(args.repo).resolve() if args.repo else Path(__file__).resolve().parents[2]
    log_dir = Path(os.environ.get("LOG_DIR") or Path.home() / ".turnbase-loop-logs")
    cfg = Config(repo_dir=repo, log_dir=log_dir, max_iterations=args.max, model=args.model,
                 sleep_seconds=args.sleep, stop_file=args.stop_file, state_file=args.state_file,
                 resume=not args.no_resume, once=args.once, stall_minutes=args.stall_minutes)

    if shutil.which(cfg.claude_bin) is None:
        print("claude CLI not found on PATH", file=sys.stderr)
        return 1
    if not cfg.settings_file.is_file():
        print(f"Loop settings file missing: {cfg.settings_file}", file=sys.stderr)
        return 1

    terminal = Terminal()
    try:
        with Controls() as controls:
            return run(cfg, controls=controls, terminal=terminal)
    except KeyboardInterrupt:
        return 130
    finally:
        terminal.clear_live()
        terminal.reset_title()


if __name__ == "__main__":
    sys.exit(main())
