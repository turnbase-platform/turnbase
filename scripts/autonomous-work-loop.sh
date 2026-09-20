#!/usr/bin/env bash
# Runs non-interactive `claude` sessions back to back, each one picking up the
# next TurnBase IMP-* work item via the `work-item` skill and finishing it
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
#   scripts/autonomous-work-loop.sh [--once] [--max N]
#                                    [--model NAME] [--sleep SECONDS]
#                                    [--repo DIR] [--stop-file PATH]
#                                    [--no-resume] [--state-file PATH]
#
# Stop it gracefully mid-run by creating the stop file (default:
# .autonomous-loop.stop in the repo root) — it's checked between iterations,
# never mid-session.
#
# Resumability
# ------------
# * The session id is generated up front and recorded in the state file
#   BEFORE `claude` starts, so a run that is killed at any point — even
#   `kill -9` before it produces a byte of output — is still resumable.
# * SIGINT/SIGTERM are forwarded to the running `claude` child and the loop
#   then stops without starting another iteration. The session is left
#   resumable; nothing is rolled back.
# * On the next start the loop resumes an unfinished session instead of
#   starting a fresh one, and keeps resuming it until it reports a
#   LOOP_STATUS line. Pass --no-resume to force a fresh session.
# * A 429 session limit is detected, the quota reset time is read out of the
#   session transcript, and the loop sleeps until then and resumes the same
#   session rather than losing the in-progress work item.
#
# --max bounds `claude` invocations, not work items: a resumed session spends
# one, so an item that needs two resumes costs three of them.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAX_ITERATIONS=20
MODEL="sonnet"
SLEEP_SECONDS=10
STOP_FILE=""
STATE_FILE=""
ONCE=0
RESUME=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --once) ONCE=1; shift ;;
    --max) MAX_ITERATIONS="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --sleep) SLEEP_SECONDS="$2"; shift 2 ;;
    --repo) REPO_DIR="$2"; shift 2 ;;
    --stop-file) STOP_FILE="$2"; shift 2 ;;
    --state-file) STATE_FILE="$2"; shift 2 ;;
    --no-resume) RESUME=0; shift ;;
    -h|--help) grep '^#' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

[[ -z "$STOP_FILE" ]] && STOP_FILE="$REPO_DIR/.autonomous-loop.stop"
LOG_DIR="${LOG_DIR:-$HOME/.turnbase-loop-logs}"
mkdir -p "$LOG_DIR"
# The state file lives outside the repo on purpose: the loop refuses to start
# on a dirty tree, so it must not be the thing dirtying it.
[[ -z "$STATE_FILE" ]] && STATE_FILE="$LOG_DIR/state.json"

SETTINGS_FILE="$REPO_DIR/scripts/autonomous-loop.settings.json"

[[ $ONCE -eq 1 ]] && MAX_ITERATIONS=1

command -v claude >/dev/null || { echo "claude CLI not found on PATH" >&2; exit 1; }
command -v jq >/dev/null || { echo "jq is required (apt/brew install jq)" >&2; exit 1; }
[[ -f "$SETTINGS_FILE" ]] || { echo "Loop settings file missing: $SETTINGS_FILE" >&2; exit 1; }

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

This is a single non-interactive turn: there is no later turn in which to
"check back". If you push a submodule commit and need CI to go green before
bumping its ref at the top level, block on it synchronously in one tool call
(e.g. `gh run watch <run-id> --exit-status`) and then finish the rest of the
checklist in the same turn — never end your turn planning to check CI, or
anything else, "once it completes".

End your final message with exactly one line, and nothing after it, in one of
these three exact forms:
LOOP_STATUS: DONE <item-id-or-short-label>
LOOP_STATUS: BLOCKED <one-line reason>
LOOP_STATUS: FINISHED <all items complete>'

RESUME_PROMPT='This session was interrupted before it reported a LOOP_STATUS line — it was
killed, cut off by a session limit, or it stopped early. Nothing has been
rolled back for you.

First re-establish where you actually are: check `git status`, the current
branch, whether your work item was committed/merged, and whether any CI run
you were waiting on has since finished. Do not assume the work is unstarted
and do not redo work that is already committed.

Then either finish the item end-to-end (full "Ending a Session" checklist
from CLAUDE.md) or, if it cannot be finished safely, unwind it cleanly so the
tree is left clean and on master.

Same rule as before: block synchronously on anything you need (e.g.
`gh run watch <run-id> --exit-status`) rather than ending your turn planning
to check back later.

End your final message with exactly one line, and nothing after it, in one of
these three exact forms:
LOOP_STATUS: DONE <item-id-or-short-label>
LOOP_STATUS: BLOCKED <one-line reason>
LOOP_STATUS: FINISHED <all items complete>'

now_iso() { date -u +%Y-%m-%dT%H:%M:%SZ; }

new_session_id() {
  if command -v uuidgen >/dev/null; then
    uuidgen
  else
    cat /proc/sys/kernel/random/uuid
  fi
}

# Claude Code stores transcripts under a directory name derived from the cwd
# by replacing every non-alphanumeric character with a dash.
transcript_path() {
  local sid="$1" encoded
  encoded="$(printf '%s' "$REPO_DIR" | sed 's/[^a-zA-Z0-9]/-/g')"
  printf '%s\n' "$HOME/.claude/projects/$encoded/$sid.jsonl"
}

write_state() {
  local sid="$1" iter="$2" status="$3" extra="${4:-{\}}"
  jq -n \
    --arg sid "$sid" \
    --arg status "$status" \
    --arg updated "$(now_iso)" \
    --argjson iter "$iter" \
    --argjson extra "$extra" \
    '{session_id:$sid, iteration:$iter, status:$status, updated_at:$updated} + $extra' \
    > "$STATE_FILE"
}

state_field() {
  [[ -f "$STATE_FILE" ]] || return 0
  jq -r --arg f "$1" '.[$f] // empty' "$STATE_FILE" 2>/dev/null || true
}

CLAUDE_PID=""
CURRENT_SESSION_ID=""
CURRENT_ITERATION=0

forward_signal() {
  local sig="$1"
  trap - INT TERM
  echo >&2
  echo "Received SIG$sig — forwarding to claude and stopping the loop." >&2
  if [[ -n "$CLAUDE_PID" ]] && kill -0 "$CLAUDE_PID" 2>/dev/null; then
    kill -"$sig" "$CLAUDE_PID" 2>/dev/null || true
    wait "$CLAUDE_PID" 2>/dev/null || true
  fi
  if [[ -n "$CURRENT_SESSION_ID" ]]; then
    write_state "$CURRENT_SESSION_ID" "$CURRENT_ITERATION" interrupted
    echo "Session $CURRENT_SESSION_ID left resumable." >&2
    echo "Re-run this script to continue it, or: claude --resume $CURRENT_SESSION_ID" >&2
  fi
  if [[ "$sig" == "INT" ]]; then exit 130; else exit 143; fi
}
trap 'forward_signal INT' INT
trap 'forward_signal TERM' TERM

# sleep in the background so INT/TERM are handled while we wait
interruptible_sleep() {
  local secs="$1" pid
  [[ "$secs" -gt 0 ]] || return 0
  sleep "$secs" &
  pid=$!
  wait "$pid" 2>/dev/null || true
}

run_claude() {
  local out_file="$1"; shift
  claude_exit=0
  claude "$@" > "$out_file" &
  CLAUDE_PID=$!
  wait "$CLAUDE_PID" || claude_exit=$?
  CLAUDE_PID=""
}

# The last `result` event of a stream-json run carries the same object the old
# --output-format json produced.
result_event() {
  [[ -s "$1" ]] || return 0
  jq -c 'select(.type == "result")' "$1" 2>/dev/null | tail -n1 || true
}

quota_reset_epoch() {
  local sid="$1" tp
  tp="$(transcript_path "$sid")"
  [[ -f "$tp" ]] || return 0
  grep -o '"resetsAt":[0-9]\+' "$tp" 2>/dev/null | tail -n1 | cut -d: -f2 || true
}

wait_for_quota_reset() {
  local resets_at="$1" now delta
  now="$(date +%s)"
  if [[ -n "$resets_at" ]] && [[ "$resets_at" =~ ^[0-9]+$ ]] && [[ "$resets_at" -gt "$now" ]]; then
    delta=$(( resets_at - now + 30 ))
    echo "  quota resets at $(date -d "@$resets_at" '+%Y-%m-%d %H:%M:%S %Z') — sleeping ${delta}s." >&2
  else
    delta=900
    echo "  no usable reset time in the transcript — sleeping ${delta}s before retrying." >&2
  fi
  interruptible_sleep "$delta"
}

iteration=0
while [[ $iteration -lt $MAX_ITERATIONS ]]; do
  iteration=$((iteration + 1))
  CURRENT_ITERATION=$iteration

  if [[ -f "$STOP_FILE" ]]; then
    echo "Stop file present ($STOP_FILE) — halting before iteration $iteration." >&2
    rm -f "$STOP_FILE"
    exit 0
  fi

  mode="fresh"
  session_id=""
  if [[ $RESUME -eq 1 ]]; then
    prev_status="$(state_field status)"
    prev_session="$(state_field session_id)"
    case "$prev_status" in
      running|interrupted|rate_limited)
        if [[ -n "$prev_session" ]]; then
          mode="resume"
          session_id="$prev_session"
        fi
        ;;
    esac
  fi

  if [[ "$mode" == "fresh" ]]; then
    # These preconditions describe a fresh session's contract. A resumed
    # session is mid-work by definition, so they are deliberately skipped.
    if [[ -n "$(git -C "$REPO_DIR" status --porcelain)" ]]; then
      echo "Working tree not clean before iteration $iteration — refusing to start. Inspect manually." >&2
      exit 1
    fi
    branch="$(git -C "$REPO_DIR" rev-parse --abbrev-ref HEAD)"
    if [[ "$branch" != "master" ]]; then
      echo "Not on master before iteration $iteration (on '$branch') — refusing to start." >&2
      exit 1
    fi
    session_id="$(new_session_id)"
  fi

  CURRENT_SESSION_ID="$session_id"
  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  out_file="$LOG_DIR/${ts}-iter${iteration}.jsonl"

  echo "[$ts] iteration $iteration/$MAX_ITERATIONS — $mode session $session_id (log: $out_file)"

  # Recorded before the run so a hard kill still leaves a resumable id behind.
  write_state "$session_id" "$iteration" running "$(jq -n --arg lf "$out_file" '{log_file:$lf}')"

  common_args=(
    --model "$MODEL"
    --output-format stream-json
    --verbose
    --dangerously-skip-permissions
    --settings "$SETTINGS_FILE"
  )
  if [[ "$mode" == "resume" ]]; then
    run_claude "$out_file" -p "$RESUME_PROMPT" --resume "$session_id" "${common_args[@]}"
  else
    run_claude "$out_file" -p "$PROMPT" --session-id "$session_id" "${common_args[@]}"
  fi

  event="$(result_event "$out_file")"
  is_error="false"
  api_error_status=""
  result_text=""
  if [[ -n "$event" ]]; then
    is_error="$(jq -r '.is_error // false' <<<"$event")"
    api_error_status="$(jq -r '.api_error_status // empty' <<<"$event")"
    result_text="$(jq -r '.result // empty' <<<"$event")"
  fi

  if [[ "$api_error_status" == "429" ]] || \
     grep -qiE "hit your (session|weekly|monthly) limit" <<<"$result_text"; then
    resets_at="$(quota_reset_epoch "$session_id")"
    echo "  -> session limit reached: ${result_text:-429}" >&2
    write_state "$session_id" "$iteration" rate_limited \
      "$(jq -n --arg r "${resets_at:-}" '{resets_at:$r}')"
    wait_for_quota_reset "$resets_at"
    continue
  fi

  if [[ $claude_exit -ne 0 ]]; then
    echo "claude exited with code $claude_exit on iteration $iteration — see $out_file." >&2
    write_state "$session_id" "$iteration" interrupted
    echo "Session left resumable; re-run to continue it. Halting." >&2
    exit 1
  fi

  if [[ "$is_error" == "true" ]]; then
    echo "claude reported an error on iteration $iteration — see $out_file." >&2
    write_state "$session_id" "$iteration" interrupted
    echo "Session left resumable; re-run to continue it. Halting." >&2
    exit 1
  fi

  status_line="$(printf '%s\n' "$result_text" | grep '^LOOP_STATUS:' | tail -n1 || true)"

  if [[ -z "$status_line" ]]; then
    # The Stop hook should make this unreachable; if it happens anyway the
    # session is unfinished, not failed, so leave it resumable.
    echo "No LOOP_STATUS line in iteration $iteration — treating the session as unfinished." >&2
    write_state "$session_id" "$iteration" interrupted
    interruptible_sleep "$SLEEP_SECONDS"
    continue
  fi
  echo "  -> $status_line"

  if [[ -n "$(git -C "$REPO_DIR" status --porcelain)" ]] || \
     [[ "$(git -C "$REPO_DIR" rev-parse --abbrev-ref HEAD)" != "master" ]]; then
    echo "Tree not clean / not on master after iteration $iteration despite report — halting for manual review." >&2
    write_state "$session_id" "$iteration" failed
    exit 1
  fi

  case "$status_line" in
    "LOOP_STATUS: BLOCKED"*)
      write_state "$session_id" "$iteration" blocked
      echo "Session reported BLOCKED — halting loop for manual review." >&2
      exit 0
      ;;
    "LOOP_STATUS: FINISHED"*)
      write_state "$session_id" "$iteration" finished
      echo "Session reported FINISHED — all work items complete. Stopping loop."
      exit 0
      ;;
    "LOOP_STATUS: DONE"*)
      write_state "$session_id" "$iteration" done
      ;;
    *)
      write_state "$session_id" "$iteration" failed
      echo "Unrecognized LOOP_STATUS value: '$status_line' — halting for manual review." >&2
      exit 1
      ;;
  esac

  [[ $ONCE -eq 1 ]] && exit 0
  interruptible_sleep "$SLEEP_SECONDS"
done

echo "Reached max iterations ($MAX_ITERATIONS). Stopping."
