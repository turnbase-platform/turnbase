#!/usr/bin/env bash
#
# Refresh turnbase-platform's committed copy of manifest.schema.json from the
# authoritative file in this repository's spec tree.
#
# The copy is a tracked file rather than a build-time artifact for the same
# reason as gamehost.proto's copy in turnbase-common: turnbase-platform must
# build from a standalone clone — its CI checks out the submodule alone, so
# nothing in its Maven build may read a path outside the repository
# (conventions.md §5, IMP-GATE-60).
#
# That buys independence at the cost of drift, and drift here is silent: the
# platform upload validator and the (future) SDK test harness would validate
# the same manifest.json differently while both still compile. Hence --check.
#
# Unlike sync-proto.sh, --check does not yet run in the parent's pre-push
# hook: no copy exists until IMP-M4-02 creates one, and a hard check against a
# copy nobody has built yet would fail every push for an unrelated reason.
# IMP-M4-02 wires the pre-push entry in the same change that creates the
# first copy (conventions.md §5).
#
#   scripts/sync-manifest-schema.sh            refresh the copy
#   scripts/sync-manifest-schema.sh --check    exit 1 if an existing copy differs
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$REPO_ROOT/docs/specs/manifest/manifest.schema.json"
TARGET="$REPO_ROOT/turnbase-platform/src/main/resources/manifest/manifest.schema.json"

if [[ ! -f "$SOURCE" ]]; then
  echo "sync-manifest-schema: authoritative schema missing: $SOURCE" >&2
  exit 1
fi

# A submodule that was never initialised is not a drift failure — there is
# simply nothing to compare against yet, and saying so beats a diff against
# /dev/null.
if [[ ! -d "$REPO_ROOT/turnbase-platform/.git" && ! -f "$REPO_ROOT/turnbase-platform/.git" ]]; then
  echo "sync-manifest-schema: turnbase-platform is not checked out; run:" >&2
  echo "  git submodule update --init turnbase-platform" >&2
  exit 1
fi

if [[ "${1:-}" == "--check" ]]; then
  if [[ ! -f "$TARGET" ]]; then
    echo "sync-manifest-schema: no copy yet (${TARGET#"$REPO_ROOT/"}) — nothing to check until IMP-M4-02 creates one"
    exit 0
  fi
  # --strip-trailing-cr belt-and-braces: both files are pinned to LF by .gitattributes
  # on each side, but a clone made before those landed, or a contributor who bypassed
  # them, would otherwise fail this check on every line of an identical file.
  if ! diff -u --strip-trailing-cr "$SOURCE" "$TARGET" > /dev/null; then
    echo "sync-manifest-schema: the copy has drifted from the authoritative schema." >&2
    echo >&2
    diff -u --strip-trailing-cr \
      --label "docs/specs/manifest/manifest.schema.json (authoritative)" \
      --label "turnbase-platform/src/main/resources/manifest/manifest.schema.json (copy)" \
      "$SOURCE" "$TARGET" >&2 || true
    echo >&2
    echo "sync-manifest-schema: if the spec changed, run scripts/sync-manifest-schema.sh and commit the copy." >&2
    echo "sync-manifest-schema: if the copy was edited directly, that is the defect — revert it." >&2
    exit 1
  fi
  echo "sync-manifest-schema: copy matches the authoritative schema"
  exit 0
fi

mkdir -p "$(dirname "$TARGET")"
cp "$SOURCE" "$TARGET"
echo "sync-manifest-schema: refreshed ${TARGET#"$REPO_ROOT/"}"
echo "sync-manifest-schema: commit it in turnbase-platform, then bump the submodule ref here."
