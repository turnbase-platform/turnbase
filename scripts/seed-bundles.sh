#!/usr/bin/env bash
#
# Builds every official game and gathers the bundles the platform's seeder uploads into one
# directory, target/seed-bundles/<gameId>.zip (local-environment.md §6): Tic-Tac-Toe and
# 7 Wonders Duel. Compose and the Helm chart mount this directory.
#
#   scripts/seed-bundles.sh               # build both games, then gather
#   scripts/seed-bundles.sh --no-build    # gather the bundles already packaged
#
# Needs JDK 21, Node, zip, and both game submodules checked out.
set -euo pipefail
cd "$(dirname "$0")/.."

GAMES=(turnbase-game-tictactoe turnbase-game-7wonders-duel)
OUT=target/seed-bundles

if [ "${1:-}" != "--no-build" ]; then
  "${JAVA_HOME:+$JAVA_HOME/bin/}java" -version 2>&1 | grep -q 'version "21' \
    || { echo "JAVA_HOME must point at a JDK 21" >&2; exit 1; }
  for g in "${GAMES[@]}"; do
    [ -f "$g/package.json" ] || { echo "$g is not checked out (git submodule update --init $g)" >&2; exit 1; }
    (cd "$g" && ./mvnw -q package && npm ci --silent && npm run --silent build && ./scripts/package.sh)
  done
fi

rm -rf "$OUT"; mkdir -p "$OUT"
for g in "${GAMES[@]}"; do
  ls "$g"/target/seed/*.zip >/dev/null 2>&1 || { echo "no bundle in $g/target/seed (run without --no-build)" >&2; exit 1; }
  cp "$g"/target/seed/*.zip "$OUT/"
done
ls "$OUT"
