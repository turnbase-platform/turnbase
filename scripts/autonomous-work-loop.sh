#!/usr/bin/env bash
# Runs fresh, non-interactive `claude` sessions back to back, each one picking up
# the next TurnBase IMP-* work item via the `work-item` skill and finishing it
# end-to-end (commit, merge to master, delete branch, update STATUS.md).
#
# DANGER: each session runs with --dangerously-skip-permissions (no human
# approves any tool call, including Bash, git push, file deletion, etc.) and
# is free to commit/merge into master. Only run this against a repo you can
# afford to have modified unattended, and watch the first few iterations
# before leaving it unattended for real. Do NOT run this on a machine/account
# where `master` is pushed somewhere shared unless you intend that.
#
# Usage:
#   scripts/autonomous-work-loop.sh [--once] [--max N] [--budget USD]
#                                    [--model NAME] [--sleep SECONDS]
#                                    [--repo DIR] [--stop-file PATH]
#
# Stop it gracefully mid-run by creating the stop file (default:
# .autonomous-loop.stop in the repo root) — it's checked between iterations,
# never mid-session.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAX_ITERATIONS=20
MAX_BUDGET_USD=10
MODEL="sonnet"
SLEEP_SECONDS=10
STOP_FILE=""
ONCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --once) ONCE=1; shift ;;
    --max) MAX_ITERATIONS="$2"; shift 2 ;;
    --budget) MAX_BUDGET_USD="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --sleep) SLEEP_SECONDS="$2"; shift 2 ;;
    --repo) REPO_DIR="$2"; shift 2 ;;
    --stop-file) STOP_FILE="$2"; shift 2 ;;
    -h|--help) grep '^#' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

[[ -z "$STOP_FILE" ]] && STOP_FILE="$REPO_DIR/.autonomous-loop.stop"
LOG_DIR="${LOG_DIR:-$HOME/.turnbase-loop-logs}"
mkdir -p "$LOG_DIR"

[[ $ONCE -eq 1 ]] && MAX_ITERATIONS=1

command -v claude >/dev/null || { echo "claude CLI not found on PATH" >&2; exit 1; }
command -v jq >/dev/null || { echo "jq is required (apt/brew install jq)" >&2; exit 1; }

cd "$REPO_DIR"

PROMPT='Pick up the next TurnBase Phase 1 work item and implement it, following the
`work-item` skill exactly (claim it, read exactly its read-list, build to the
"Done when" clause). If a specification defect blocks you, use the
`spec-defect` skill instead of guessing — filing/fixing the defect is a valid
unit of work for this session.

Do exactly ONE item (or one spec-defect fix) this session, then stop — do not
chain a second item. Before finishing: run the full "Ending a Session"
checklist from CLAUDE.md (STATUS.md replaced, corpus check clean if docs
changed, submodule refs updated only if build+tests pass, everything
committed, every branch created this session merged into master and deleted
locally, nothing left uncommitted or unmerged).

If the working tree was not clean, or not on master, when you started: stop
immediately without changing anything and report that instead.

End your final message with exactly one line, and nothing after it, in one of
these three exact forms:
LOOP_STATUS: DONE <item-id-or-short-label>
LOOP_STATUS: BLOCKED <one-line reason>
LOOP_STATUS: FINISHED <all items complete>'

iteration=0
while [[ $iteration -lt $MAX_ITERATIONS ]]; do
  iteration=$((iteration + 1))

  if [[ -f "$STOP_FILE" ]]; then
    echo "Stop file present ($STOP_FILE) — halting before iteration $iteration." >&2
    rm -f "$STOP_FILE"
    exit 0
  fi

  if [[ -n "$(git -C "$REPO_DIR" status --porcelain)" ]]; then
    echo "Working tree not clean before iteration $iteration — refusing to start. Inspect manually." >&2
    exit 1
  fi
  branch="$(git -C "$REPO_DIR" rev-parse --abbrev-ref HEAD)"
  if [[ "$branch" != "master" ]]; then
    echo "Not on master before iteration $iteration (on '$branch') — refusing to start." >&2
    exit 1
  fi

  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  out_file="$LOG_DIR/${ts}-iter${iteration}.json"

  echo "[$ts] iteration $iteration/$MAX_ITERATIONS — starting fresh session (log: $out_file)"

  set +e
  claude -p "$PROMPT" \
    --model "$MODEL" \
    --output-format json \
    --dangerously-skip-permissions \
    --max-budget-usd "$MAX_BUDGET_USD" \
    > "$out_file"
  claude_exit=$?
  set -e

  if [[ $claude_exit -ne 0 ]]; then
    echo "claude exited with code $claude_exit on iteration $iteration — see $out_file. Halting." >&2
    exit 1
  fi

  result_text="$(jq -r '.result // empty' "$out_file" 2>/dev/null || true)"
  status_line="$(printf '%s\n' "$result_text" | grep '^LOOP_STATUS:' | tail -n1 || true)"

  if [[ -z "$status_line" ]]; then
    echo "No LOOP_STATUS line found in iteration $iteration output — see $out_file. Halting for manual review." >&2
    exit 1
  fi
  echo "  -> $status_line"

  if [[ -n "$(git -C "$REPO_DIR" status --porcelain)" ]] || \
     [[ "$(git -C "$REPO_DIR" rev-parse --abbrev-ref HEAD)" != "master" ]]; then
    echo "Tree not clean / not on master after iteration $iteration despite report — halting for manual review." >&2
    exit 1
  fi

  case "$status_line" in
    "LOOP_STATUS: BLOCKED"*)
      echo "Session reported BLOCKED — halting loop for manual review." >&2
      exit 0
      ;;
    "LOOP_STATUS: FINISHED"*)
      echo "Session reported FINISHED — all work items complete. Stopping loop."
      exit 0
      ;;
    "LOOP_STATUS: DONE"*)
      : # continue to next iteration
      ;;
    *)
      echo "Unrecognized LOOP_STATUS value: '$status_line' — halting for manual review." >&2
      exit 1
      ;;
  esac

  [[ $ONCE -eq 1 ]] && exit 0
  sleep "$SLEEP_SECONDS"
done

echo "Reached max iterations ($MAX_ITERATIONS). Stopping."
