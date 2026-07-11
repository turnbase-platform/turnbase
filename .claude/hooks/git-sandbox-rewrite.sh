#!/usr/bin/env bash
# PreToolUse(Bash): rewrite git commands that choke on the Claude Code sandbox's
# /dev/null mount points at the repo root (.bash_profile, .mcp.json, .claude/agents, ...).
# Those are character devices, and git refuses them:
#
#   git add -A    -> can only add regular files, symbolic links or git-directories (128)
#   git stash -u  -> unsupported file type                                         (1)
#
# Filtering by file TYPE rather than by path is the whole point: a .gitignore rule would
# hide a REAL .mcp.json or .vscode/ along with the phantom. git clean is left alone: it is
# destructive, already removes the real files, and fails loudly.
set -uo pipefail

SAFE_ADD='{ git add -u && git ls-files -o --exclude-standard -z | { rc=0; while IFS= read -r -d "" f; do if [ -c "$f" ] || [ -b "$f" ] || [ -p "$f" ] || [ -S "$f" ]; then continue; fi; git add -- "$f" || rc=1; done; exit $rc; }; }'
SAFE_STASH='{ _ex=(); while IFS= read -r -d "" f; do if [ -c "$f" ] || [ -b "$f" ] || [ -p "$f" ] || [ -S "$f" ]; then _ex+=(":(exclude)$f"); fi; done < <(git ls-files -o --exclude-standard -z); git stash push -u -- . "${_ex[@]}"; }'

payload=$(cat)
cmd=$(printf '%s' "$payload" | jq -r '.tool_input.command // ""')

# Match only in command position (start, or after ; && || | & ( {) so a mere mention --
# echo "git add -A", a commit message, a heredoc body -- is left verbatim. Under-matching
# is deliberate: a miss fails loudly, an over-eager rewrite silently corrupts text.
# Stash matches bare flags only, or a trailing `-m "msg"` would be dropped.
RE_ADD='(^|[;&|(){}])[[:space:]]*git[[:space:]]+add[[:space:]]+(-[A-Za-z]*A[A-Za-z]*|--all|\.)([[:space:]]|$)'
RE_STASH='(^|[;&|(){}])[[:space:]]*git[[:space:]]+stash([[:space:]]+push)?[[:space:]]+(-u|--include-untracked|-a|--all)[[:space:]]*($|[;&|)}])'

printf '%s' "$cmd" | grep -Eq "$RE_ADD" || printf '%s' "$cmd" | grep -Eq "$RE_STASH" || exit 0

new=$(jq -rn --arg c "$cmd" --arg a "$SAFE_ADD" --arg s "$SAFE_STASH" '
  $c
  | sub("(?<pre>^|[;&|(){}])(?<sp>\\s*)git\\s+add\\s+(-[A-Za-z]*A[A-Za-z]*|--all|\\.)(?=\\s|$)";
        .pre + .sp + $a; "g")
  | sub("(?<pre>^|[;&|(){}])(?<sp>\\s*)git\\s+stash(\\s+push)?\\s+(-u|--include-untracked|-a|--all)(?=\\s*($|[;&|)}]))";
        .pre + .sp + $s; "g")')

# grep anchors ^ per line, jq's sub per string; they disagree on an indented occurrence in
# a heredoc body. jq is right there, so claim nothing when nothing actually changed.
[ "$new" = "$cmd" ] && exit 0

jq -n --arg c "$new" '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    updatedInput: { command: $c },
    additionalContext: "Rewrote git to skip the sandbox mount points at the repo root (character devices git cannot stage). Real files are handled normally."
  }
}'
