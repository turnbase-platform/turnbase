#!/usr/bin/env bash
#
# Refresh turnbase-common's committed copy of gamehost.proto from the authoritative
# file in this repository's spec tree.
#
# The copy is a tracked file rather than a build-time artifact because
# turnbase-common must build from a standalone clone — its CI checks out the
# submodule alone, so nothing in its Maven build may read a path outside the
# repository (ADR-0012, amended by IMP-GATE-02; conventions.md §5).
#
# That buys independence at the cost of drift, and drift here is silent: both
# repositories still compile while the two services disagree on the wire. Hence
# --check, which runs in this repository's pre-push hook.
#
#   scripts/sync-proto.sh            refresh the copy
#   scripts/sync-proto.sh --check    exit 1 if the copy differs
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$REPO_ROOT/docs/specs/internal-grpc/gamehost.proto"
TARGET="$REPO_ROOT/turnbase-common/src/main/proto/turnbase/gamehost/v1/gamehost.proto"

if [[ ! -f "$SOURCE" ]]; then
  echo "sync-proto: authoritative proto missing: $SOURCE" >&2
  exit 1
fi

# A submodule that was never initialised is not a drift failure — there is simply
# nothing to compare against yet, and saying so beats a diff against /dev/null.
if [[ ! -d "$REPO_ROOT/turnbase-common/.git" && ! -f "$REPO_ROOT/turnbase-common/.git" ]]; then
  echo "sync-proto: turnbase-common is not checked out; run:" >&2
  echo "  git submodule update --init turnbase-common" >&2
  exit 1
fi

if [[ "${1:-}" == "--check" ]]; then
  if [[ ! -f "$TARGET" ]]; then
    echo "sync-proto: copy missing: ${TARGET#"$REPO_ROOT/"}" >&2
    echo "sync-proto: run scripts/sync-proto.sh" >&2
    exit 1
  fi
  if ! diff -u "$SOURCE" "$TARGET" > /dev/null; then
    echo "sync-proto: the copy has drifted from the authoritative proto." >&2
    echo >&2
    diff -u \
      --label "docs/specs/internal-grpc/gamehost.proto (authoritative)" \
      --label "turnbase-common/src/main/proto/turnbase/gamehost/v1/gamehost.proto (copy)" \
      "$SOURCE" "$TARGET" >&2 || true
    echo >&2
    echo "sync-proto: if the spec changed, run scripts/sync-proto.sh and commit the copy." >&2
    echo "sync-proto: if the copy was edited directly, that is the defect — revert it." >&2
    exit 1
  fi
  echo "sync-proto: copy matches the authoritative proto"
  exit 0
fi

mkdir -p "$(dirname "$TARGET")"
cp "$SOURCE" "$TARGET"
echo "sync-proto: refreshed ${TARGET#"$REPO_ROOT/"}"
echo "sync-proto: commit it in turnbase-common, then bump the submodule ref here."
