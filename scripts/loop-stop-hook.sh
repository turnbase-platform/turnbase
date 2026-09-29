#!/usr/bin/env bash
# Stop hook for the autonomous work loop (scripts/autonomous-work-loop.sh → scripts/autonomous_loop/).
#
# The loop requires every automated session to end with a LOOP_STATUS line;
# without one it cannot tell a finished work item from a session that stopped
# early. Twice the model has ended its turn mid-CI-wait with no such line, so
# this hook refuses the stop and tells it to finish.
#
# Scoped to automation runs only by being registered in
# scripts/autonomous-loop.settings.json, which the loop passes via --settings.
# Interactive sessions never load it.
#
# Blocks with exit 2; the reason on stderr is what the model is expected to
# act on. After MAX_BLOCKS consecutive refusals for one session it gives up
# and lets the turn end — Claude Code documents no cap of its own, and the
# loop treats a status-less session as unfinished and resumes it anyway.

set -euo pipefail

MAX_BLOCKS="${LOOP_STOP_HOOK_MAX_BLOCKS:-3}"

command -v jq >/dev/null || exit 0

input="$(cat)"
last_message="$(jq -r '.last_assistant_message // empty' <<<"$input" 2>/dev/null || true)"
session_id="$(jq -r '.session_id // empty' <<<"$input" 2>/dev/null || true)"
stop_hook_active="$(jq -r '.stop_hook_active // false' <<<"$input" 2>/dev/null || echo false)"

guard_dir="${TMPDIR:-/tmp}/turnbase-loop-stop-guard"
mkdir -p "$guard_dir" 2>/dev/null || true
counter_file="$guard_dir/${session_id:-unknown}"

# stop_hook_active is false on the first stop of a chain and true once this
# hook has already blocked one, so it marks where a fresh chain begins and
# keeps a stale count from an earlier one out of this decision.
[[ "$stop_hook_active" == "true" ]] || rm -f "$counter_file" 2>/dev/null || true

allow_stop() {
  rm -f "$counter_file" 2>/dev/null || true
  exit 0
}

# Nothing to inspect — don't strand the session.
[[ -n "$last_message" ]] || allow_stop

last_line="$(printf '%s\n' "$last_message" | sed '/^[[:space:]]*$/d' | tail -n1)"

if [[ "$last_line" =~ ^LOOP_STATUS:[[:space:]]+(DONE|BLOCKED|FINISHED)([[:space:]]|$) ]]; then
  allow_stop
fi

blocks=0
[[ -f "$counter_file" ]] && blocks="$(cat "$counter_file" 2>/dev/null || echo 0)"
[[ "$blocks" =~ ^[0-9]+$ ]] || blocks=0
blocks=$((blocks + 1))
printf '%s' "$blocks" > "$counter_file" 2>/dev/null || true

if [[ "$blocks" -gt "$MAX_BLOCKS" ]]; then
  allow_stop
fi

cat >&2 <<EOF
Your final message does not end with a LOOP_STATUS line, so this session
cannot be closed out. Do not stop yet.

If work is still outstanding — a CI run you were waiting on, an unmerged
branch, an unfinished checklist — finish it now, blocking synchronously on
anything you need (e.g. \`gh run watch <run-id> --exit-status\`) rather than
planning to check back later. If the work is genuinely complete, or you are
blocked and cannot proceed, say so with the appropriate status.

Then end your final message with exactly one line, and nothing after it:
LOOP_STATUS: DONE <item-id-or-short-label>
LOOP_STATUS: BLOCKED <one-line reason>
LOOP_STATUS: FINISHED <all items complete>

(refusal $blocks of $MAX_BLOCKS; after that the turn is allowed to end and the
loop will resume the session instead)
EOF
exit 2
