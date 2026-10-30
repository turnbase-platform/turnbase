#!/usr/bin/env bash
#
# git-land.sh — the one allowlisted entry point for the end-of-work git steps:
# commit, merge a branch into master, push, delete the branch locally and on the
# remote, sweep leftovers, and bump submodule refs. Works on the umbrella repo and
# on every submodule.
#
# Why a script: the headless loop runs with an exact-match Bash allowlist, and the
# model keeps composing `git push -q origin master | tail -2; git branch -d ...`,
# which matches nothing, or `git push --delete`, which the deny list blocks. Every
# denied compound takes its commit and merge down with it and leaves the tree half
# landed. Allowlist `Bash(scripts/git-land.sh*)` and give the model this instead.
#
# Usage: scripts/git-land.sh <command> [options] [args]
#
#   status  [--repo R | --all]        one line per repo: branch, dirty, ahead/behind, strays
#   commit  -m MSG [--add P]... [--push] [--repo R]
#                                     stage (listed paths, else everything) and commit;
#                                     --push also pushes when on master
#   land    [--branch B] [--commit MSG] [--rebase] [--keep-remote] [--repo R]
#                                     merge B (default: current) into master --ff-only,
#                                     push master, delete B locally and on origin
#   push    [--repo R]                bring master level with origin (push or ff-pull)
#   sweep   [--all | --repo R] [--dry-run]
#                                     delete branches already merged into master, locally
#                                     and on origin; report unmerged ones, never delete them
#   finish  [--dry-run]               every repo: push master if ahead, sweep, then verdict
#
#   --repo R           path relative to the umbrella root (default: the umbrella itself)
#   --ignore PATTERN   branch glob to leave alone (repeatable); also read from
#                      TURNBASE_GIT_IGNORE_BRANCHES, comma separated
#
# Guarantees: never force-pushes, never touches master's history, only deletes
# feat|fix|docs|chore/* branches that are fully merged into origin/master.
# Last line of `land`, `push`, `finish`: GIT_STATE: CLEAN | GIT_STATE: DIRTY <why>.
# Exit 0 only when that state is CLEAN (or, for commit/status, the command succeeded).

set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PREFIX_RE='^(feat|fix|docs|chore)/'

IGNORE=()
if [[ -n "${TURNBASE_GIT_IGNORE_BRANCHES:-}" ]]; then
  IFS=',' read -ra IGNORE <<<"$TURNBASE_GIT_IGNORE_BRANCHES"
fi

say() { printf '%s\n' "$*"; }
warn() { printf 'warn: %s\n' "$*" >&2; }
die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

REPO=$ROOT
REPO_NAME=turnbase
g() { git -C "$REPO" "$@"; }

use_repo() {
  local rel=${1:-.}
  [[ $rel == . ]] && rel=
  REPO=$ROOT${rel:+/$rel}
  REPO_NAME=${rel:-turnbase}
  [[ -e "$REPO/.git" ]] || die "$REPO_NAME is not a checked-out repository"
}

# Submodule paths that are actually checked out.
submodules() {
  git -C "$ROOT" config -f .gitmodules --get-regexp '^submodule\..*\.path$' 2>/dev/null |
    awk '{print $2}' | while read -r p; do [[ -e "$ROOT/$p/.git" ]] && echo "$p"; done
}

ignored() {
  local b=$1 p
  for p in "${IGNORE[@]:-}"; do
    [[ -n $p && $b == $p ]] && return 0
  done
  return 1
}

current_branch() { g rev-parse --abbrev-ref HEAD; }
remote_has() { g ls-remote --exit-code --heads origin "$1" >/dev/null 2>&1; }

# `status --porcelain` for the branch-merge decision. In the umbrella a moved submodule
# pointer is the *input* to a later bump, not a reason to refuse the merge.
dirty_lines() { g status --porcelain --ignore-submodules=all; }

# Sandbox mount points (character devices at the repo root) make `git add -A` fail
# with exit 128. Filter by file type, exactly as .claude/hooks/git-sandbox-rewrite.sh
# does — that hook rewrites the Bash tool's command, not a script's own git calls.
stage_all() {
  g add -u || return 1
  g ls-files -o --exclude-standard -z | while IFS= read -r -d '' f; do
    if [[ -c "$REPO/$f" || -b "$REPO/$f" || -p "$REPO/$f" || -S "$REPO/$f" ]]; then continue; fi
    g add -- "$f" || exit 1
  done
}

# Fast-forward local master to origin/master, or push local commits. Leaves HEAD on master.
sync_master() {
  g fetch -q --prune origin || die "$REPO_NAME: fetch failed"
  [[ $(current_branch) == master ]] || g checkout -q master || die "$REPO_NAME: cannot check out master"
  local ahead behind
  read -r behind ahead < <(g rev-list --left-right --count origin/master...master)
  if ((behind > 0 && ahead > 0)); then
    die "$REPO_NAME: master and origin/master have diverged ($ahead ahead, $behind behind); needs a human"
  fi
  if ((behind > 0)); then
    g merge -q --ff-only origin/master || die "$REPO_NAME: could not fast-forward master"
  fi
  if ((ahead > 0)); then
    if ! g push -q origin master; then
      # Remote moved between fetch and push: one retry on a clean fast-forward, never a force.
      g fetch -q origin
      g merge -q --ff-only origin/master 2>/dev/null || die "$REPO_NAME: push rejected and master cannot fast-forward"
      g push -q origin master || die "$REPO_NAME: push to origin/master failed"
    fi
    say "pushed    $REPO_NAME master ($ahead commit(s))"
  fi
}

delete_branch() { # <name> — only called for branches proven merged into master
  local b=$1 where=$2 # where: local|remote|both
  if [[ $DRY == 1 ]]; then
    say "would delete $REPO_NAME $b ($where)"
    return
  fi
  if [[ $where != remote ]] && g show-ref -q --verify "refs/heads/$b"; then
    # -d judges against the upstream, which can lag behind after a squash-free ff merge
    # to a different base; we already proved it is an ancestor of master, so -D is safe.
    g branch -q -d "$b" 2>/dev/null || g branch -q -D "$b" || warn "$REPO_NAME: could not delete local $b"
  fi
  if [[ $where != local && $KEEP_REMOTE == 0 ]] && remote_has "$b"; then
    g push -q origin --delete "$b" || warn "$REPO_NAME: could not delete origin/$b"
  fi
  say "deleted   $REPO_NAME $b"
}

is_merged() { g merge-base --is-ancestor "$1" master 2>/dev/null; }

verify_state() { # prints the verdict line, returns 0 when clean
  local why=() ahead behind n
  [[ $(current_branch) == master ]] || why+=("on $(current_branch)")
  [[ -z $(dirty_lines) ]] || why+=("uncommitted changes")
  g fetch -q --prune origin 2>/dev/null
  read -r behind ahead < <(g rev-list --left-right --count origin/master...master 2>/dev/null || echo "0 0")
  ((ahead > 0)) && why+=("$ahead unpushed commit(s)")
  ((behind > 0)) && why+=("$behind behind origin")
  n=0
  while IFS= read -r b; do ignored "$b" || n=$((n + 1)); done < <(g for-each-ref --format='%(refname:short)' refs/heads | grep -v '^master$')
  ((n > 0)) && why+=("$n local branch(es) left")
  if ((${#why[@]})); then
    say "GIT_STATE: DIRTY $REPO_NAME: ${why[*]}"
    return 1
  fi
  say "GIT_STATE: CLEAN $REPO_NAME @ $(g rev-parse --short master)"
}

# ---------------------------------------------------------------- commands

cmd_commit() {
  [[ -n $MSG ]] || die "commit needs -m MSG"
  if ((${#ADD[@]})); then
    g add -- "${ADD[@]}" || die "$REPO_NAME: git add failed"
  else
    stage_all || die "$REPO_NAME: staging failed"
  fi
  if g diff --cached --quiet; then
    say "nothing to commit in $REPO_NAME"
  else
    g commit -q -m "$MSG" || die "$REPO_NAME: commit failed"
    say "committed $REPO_NAME $(current_branch) @ $(g rev-parse --short HEAD)"
  fi
  if [[ $PUSH == 1 ]]; then
    [[ $(current_branch) == master ]] || die "--push only applies on master; use 'land' for a branch"
    sync_master
  fi
}

cmd_land() {
  local b=${BRANCH:-$(current_branch)}
  if [[ $b == master ]]; then
    [[ -z $MSG ]] || cmd_commit
    sync_master
    verify_state
    return
  fi
  [[ $b =~ $PREFIX_RE ]] || die "$REPO_NAME: refusing to land '$b' (only feat|fix|docs|chore/*)"
  ignored "$b" && die "$REPO_NAME: '$b' is on the ignore list"

  if [[ -n $MSG && $(current_branch) == "$b" ]]; then cmd_commit; fi
  [[ -z $(dirty_lines) ]] || die "$REPO_NAME: uncommitted changes (pass --commit MSG, or commit first):
$(dirty_lines)"

  g fetch -q --prune origin || die "$REPO_NAME: fetch failed"
  if g show-ref -q --verify "refs/heads/$b"; then
    g checkout -q master || die "$REPO_NAME: cannot check out master"
    sync_master
    if is_merged "$b"; then
      : # already contained in master
    elif g merge-base --is-ancestor master "$b"; then
      g merge -q --ff-only "$b" || die "$REPO_NAME: ff merge of $b failed"
    elif [[ $REBASE == 1 ]]; then
      g checkout -q "$b" && g rebase -q master || {
        g rebase --abort 2>/dev/null
        g checkout -q master
        die "$REPO_NAME: rebase of $b onto master conflicts; needs a human"
      }
      g checkout -q master && g merge -q --ff-only "$b" || die "$REPO_NAME: ff merge after rebase failed"
    else
      die "$REPO_NAME: $b is not a fast-forward of master (master moved); re-run with --rebase"
    fi
    sync_master
    is_merged "$b" && delete_branch "$b" both
  elif remote_has "$b"; then
    g checkout -q master 2>/dev/null
    sync_master
    if g merge-base --is-ancestor "origin/$b" master; then delete_branch "$b" remote; else
      warn "$REPO_NAME: origin/$b is not merged and has no local copy; left alone"
    fi
  else
    sync_master
    say "no branch $b in $REPO_NAME (already gone)"
  fi
  verify_state
}

cmd_push() {
  sync_master
  verify_state
}

sweep_repo() {
  g fetch -q --prune origin || {
    warn "$REPO_NAME: fetch failed, skipping"
    return 1
  }
  local cur b rc=0
  cur=$(current_branch)
  [[ $cur == master ]] || {
    warn "$REPO_NAME: on '$cur', not master; sweep skips the current branch"
  }
  while IFS= read -r b; do
    [[ $b == master || $b == "$cur" ]] && continue
    ignored "$b" && {
      say "ignored   $REPO_NAME $b"
      continue
    }
    [[ $b =~ $PREFIX_RE ]] || {
      warn "$REPO_NAME: local branch '$b' has an unexpected name; left alone"
      continue
    }
    if is_merged "$b"; then
      delete_branch "$b" both
    else
      warn "$REPO_NAME: $b is NOT merged into master; left alone"
      rc=1
    fi
  done < <(g for-each-ref --format='%(refname:short)' refs/heads)
  while IFS= read -r b; do
    b=${b#origin/}
    [[ $b == master || $b == HEAD || -z $b ]] && continue
    ignored "$b" && continue
    [[ $b =~ $PREFIX_RE ]] || continue
    if g merge-base --is-ancestor "origin/$b" master; then
      delete_branch "$b" remote
    else
      warn "$REPO_NAME: origin/$b is NOT merged into master; left alone"
      rc=1
    fi
  done < <(g for-each-ref --format='%(refname:short)' refs/remotes/origin | grep -v '^origin$')
  local st
  st=$(g stash list | wc -l)
  ((st > 0)) && warn "$REPO_NAME: $st stash entr(y/ies) present"
  return $rc
}

cmd_sweep() {
  local rc=0 r
  if [[ $ALL == 1 ]]; then
    for r in $(submodules) .; do
      use_repo "$r"
      sweep_repo || rc=1
    done
  else
    sweep_repo || rc=1
  fi
  return $rc
}

status_repo() {
  local ahead behind dirty strays
  g fetch -q --prune origin 2>/dev/null
  read -r behind ahead < <(g rev-list --left-right --count origin/master...master 2>/dev/null || echo "? ?")
  dirty=$(dirty_lines | wc -l)
  strays=$(g for-each-ref --format='%(refname:short)' refs/heads | grep -v '^master$' | paste -sd, -)
  say "$REPO_NAME: on $(current_branch), dirty=$dirty, ahead=$ahead, behind=$behind, branches=[${strays}], stash=$(g stash list | wc -l)"
}

cmd_status() {
  local r
  if [[ $ALL == 1 ]]; then
    for r in $(submodules) .; do
      use_repo "$r"
      status_repo
    done
  else
    status_repo
  fi
  git -C "$ROOT" submodule status 2>/dev/null | grep '^[+-U]' |
    sed 's/^+/pointer drift (submodule HEAD != recorded ref): /; s/^-/not checked out: /; s/^U/merge conflict: /' || true
}

cmd_finish() {
  local rc=0 r
  for r in $(submodules) .; do
    use_repo "$r"
    if [[ $(current_branch) != master ]]; then
      say "SKIP      $REPO_NAME is on '$(current_branch)', not master"
      rc=1
      continue
    fi
    if [[ -n $(dirty_lines) ]]; then
      say "SKIP      $REPO_NAME has uncommitted changes"
      rc=1
      continue
    fi
    [[ $DRY == 1 ]] || sync_master
    sweep_repo || rc=1
  done
  local drift
  drift=$(git -C "$ROOT" submodule status | grep -c '^+')
  ((drift > 0)) && {
    say "NOTE      $drift submodule pointer(s) differ from the recorded ref — bump with: commit --add <sub> ..."
    rc=1
  }
  for r in $(submodules) .; do
    use_repo "$r"
    verify_state || rc=1
  done
  return $rc
}

# ---------------------------------------------------------------- args

CMD=${1:-}
[[ -n $CMD ]] && shift
MSG='' BRANCH='' ADD=() PUSH=0 REBASE=0 KEEP_REMOTE=0 DRY=0 ALL=0 REPO_ARG=.
while (($#)); do
  case $1 in
    --repo) REPO_ARG=${2:?--repo needs a path}; shift 2 ;;
    --branch) BRANCH=${2:?}; shift 2 ;;
    -m | --message | --commit) MSG=${2:?}; shift 2 ;;
    --add) ADD+=("${2:?}"); shift 2 ;;
    --ignore) IGNORE+=("${2:?}"); shift 2 ;;
    --push) PUSH=1; shift ;;
    --rebase) REBASE=1; shift ;;
    --keep-remote) KEEP_REMOTE=1; shift ;;
    --dry-run) DRY=1; shift ;;
    --all) ALL=1; shift ;;
    *) die "unknown argument: $1" ;;
  esac
done
REPO_ARG=${REPO_ARG%/}
use_repo "$REPO_ARG"

case $CMD in
  status) cmd_status ;;
  commit) cmd_commit ;;
  land) cmd_land ;;
  push) cmd_push ;;
  sweep) cmd_sweep ;;
  finish) cmd_finish ;;
  *) sed -n '2,/^set -uo/p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//' | head -n -2; exit 2 ;;
esac
