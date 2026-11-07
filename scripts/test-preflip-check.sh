#!/usr/bin/env bash
# Test for preflip-check.sh (IMP-M21-03): a clean throwaway repository passes, and one planted
# finding of each kind (secret, zero commits, late e-mail, tracked home path, tracked address)
# makes it exit non-zero with the matching tag.
set -u
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
check="$here/preflip-check.sh"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
export GIT_CONFIG_GLOBAL=/dev/null
ok="62445143+JayHubPL@users.noreply.github.com"
failures=0

mk() { # name [file content] [email] [date]
  local d="$tmp/$1"; mkdir -p "$d"; git -C "$d" init -q -b master
  if [ -n "${2:-}" ]; then printf '%s\n' "$3" >"$d/$2"; git -C "$d" add -A; fi
  echo "$d"
}
commit() { # dir email date
  GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL="$2" GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL="$2" \
  GIT_AUTHOR_DATE="$3" GIT_COMMITTER_DATE="$3" git -C "$1" commit -q -m t
}
expect() { # label dir want_rc want_tag
  local out rc
  out="$("$check" --since 2026-11-07 "$2" 2>&1)"; rc=$?
  if [ "$rc" -ne "$3" ] || { [ -n "$4" ] && ! grep -q "FAIL \[$4\]" <<<"$out"; }; then
    echo "NOT OK $1 (rc=$rc, want $3 $4)"; echo "$out"; failures=$((failures+1))
  else echo "ok $1"; fi
}

d="$(mk clean a.txt hello)"; commit "$d" "$ok" "2026-11-08T10:00:00Z"
expect "clean passes" "$d" 0 ""

# The fake credentials are assembled at run time so that this file is not itself a finding.
key="AKIA""QYLPMN5HHHFPZAM2"; sec="wJalrXUtnFEMI/K7MDENG/bPxRfiCYzK3mQ7vTx2"
d="$(mk secret a.txt "aws_key = $key
aws_secret = \"$sec\"")"; commit "$d" "$ok" "2026-11-08T10:00:00Z"
expect "planted secret fails" "$d" 1 secrets

d="$(mk empty)"
expect "zero commits fails" "$d" 1 scanned

d="$(mk email a.txt hello)"; commit "$d" "someone@example.com" "2026-11-08T10:00:00Z"
expect "late non-noreply e-mail fails" "$d" 1 email

d="$(mk oldemail a.txt hello)"; commit "$d" "someone@example.com" "2026-10-01T10:00:00Z"
expect "early e-mail is history, passes" "$d" 0 ""

d="$(mk path a.txt "see /home/""hmazur/proj")"; commit "$d" "$ok" "2026-11-08T10:00:00Z"
expect "tracked home path fails" "$d" 1 tracked

d="$(mk addr a.txt "mail huberto2000"".dom@gmail.com")"; commit "$d" "$ok" "2026-11-08T10:00:00Z"
expect "tracked personal address fails" "$d" 1 tracked

[ "$failures" -eq 0 ] && echo "all ok" || { echo "$failures failed"; exit 1; }
