#!/usr/bin/env bash
# Pre-flip privacy and secrets gate (IMP-M21-03, D7/D8).
#
# Mirror-clones every repository into a temporary directory and fails when, in any of them:
#   secrets  gitleaks (pinned container) finds a leak over the full history;
#   scanned  gitleaks scanned zero commits (a scan through a submodule worktree reads 0 and is
#            not evidence — F3);
#   email    a commit made at or after SINCE (a date or timestamp, default 2026-11-07T14:00+01:00) has an author/committer e-mail that is not a
#            users.noreply.github.com address (GitHub's own web-flow committer is allowed);
#   tracked  a tracked file at HEAD names the owner's absolute home path or personal address.
#
# Usage: scripts/preflip-check.sh [--since DATE|TIMESTAMP] [REPO_PATH...]
# Default repositories: this one and every submodule in .gitmodules. Exit 0 only if all pass.
set -u

GITLEAKS_IMAGE="zricethezav/gitleaks:v8.28.0"
# D8: the personal address was the configured e-mail until the per-repository noreply setting
# was made on 2026-11-07 (first noreply commits 15:23+01:00; last personal ones 13:23). The
# boundary is therefore a moment, not a day: F4 counts that morning's commits as history.
SINCE="2026-11-07T14:00:00+01:00"
# Assembled from pieces so that this file does not trip its own tracked-file check.
HOME_PATH="/home/""hmazur"
PERSONAL_ADDR="huberto2000"".dom@gmail.com"

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repos=()
while [ $# -gt 0 ]; do
  case "$1" in
    --since) SINCE="$2"; shift 2 ;;
    -h|--help) sed -n '2,15p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) repos+=("$1"); shift ;;
  esac
done
if [ ${#repos[@]} -eq 0 ]; then
  repos=("$root")
  while read -r p; do repos+=("$root/$p"); done \
    < <(git -C "$root" config -f .gitmodules --get-regexp '\.path$' | awk '{print $2}')
fi

since_epoch="$(date -d "$SINCE" +%s)" || { echo "bad --since: $SINCE" >&2; exit 2; }
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
fail=0
report() { echo "FAIL [$1] $2: $3"; fail=1; }

for repo in "${repos[@]}"; do
  name="$(basename "$repo")"
  mirror="$work/$name.git"
  if ! git clone -q --mirror "$repo" "$mirror" 2>/dev/null; then
    report clone "$name" "cannot mirror-clone $repo"; continue
  fi

  # secrets + scanned
  log="$work/$name.gitleaks.log"
  docker run --rm -v "$mirror:/repo:ro" --entrypoint sh "$GITLEAKS_IMAGE" -c \
    'git config --global --add safe.directory /repo && gitleaks git --no-banner --redact --log-level info /repo' \
    >"$log" 2>&1
  rc=$?
  n="$(grep -Eo '[0-9]+ commits scanned' "$log" | grep -Eo '^[0-9]+' | tail -1)"
  if [ "$rc" -eq 1 ]; then
    report secrets "$name" "gitleaks found leaks (see below)"; grep -E 'Finding|File|RuleID' "$log" | head -20
  elif [ "$rc" -ne 0 ] && [ "${n:-0}" -ne 0 ]; then
    report secrets "$name" "gitleaks failed (exit $rc)"; tail -5 "$log"
  fi
  if [ "${n:-0}" -eq 0 ]; then
    report scanned "$name" "gitleaks scanned 0 commits"
  fi

  # email: commits dated SINCE or later
  bad="$(git -C "$mirror" log --all --format='%H %ae %ce %ct %at' 2>/dev/null | awk -v since="$since_epoch" '
    ($4 + 0 >= since || $5 + 0 >= since) {
      for (i = 2; i <= 3; i++)
        if ($i !~ /@users\.noreply\.github\.com$/ && $i != "noreply@github.com") { print substr($1,1,10), $i; break }
    }')"
  if [ -n "$bad" ]; then
    report email "$name" "commit(s) since $SINCE with a non-noreply address:"; echo "$bad" | head -10
  fi

  # tracked: files at HEAD (the mirror has no worktree, so grep the tree)
  hits="$(git -C "$mirror" grep -nIF -e "$HOME_PATH" -e "$PERSONAL_ADDR" HEAD -- . ':!scripts/preflip-check.sh' ':!scripts/test-preflip-check.sh' 2>/dev/null | head -10)"
  if [ -n "$hits" ]; then
    report tracked "$name" "tracked file names the home path or personal address:"; echo "$hits"
  fi
done

if [ "$fail" -eq 0 ]; then echo "preflip-check: PASS (${#repos[@]} repositories)"; else echo "preflip-check: FAIL"; fi
exit "$fail"
