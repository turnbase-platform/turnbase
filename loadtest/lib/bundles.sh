#!/usr/bin/env bash
# Builds test-only copies of the Tic-Tac-Toe seed bundle for the `contexts` scenario, one per game id.
# Usage: loadtest/lib/bundles.sh <count> [out-dir]      (default out-dir: loadtest/results/contexts-bundles)
# Each copy is <fresh UUID>.zip (the file name's stem is the game id, local-environment.md §6) with the
# manifest `title` suffixed " <k>" and `version` set to 1.0.<k>. Prints the ids, comma separated, on stdout
# (the value of CONTEXT_IDS). Copy the zips into the seed directory and reset to have the seeder load them.
set -euo pipefail
N="${1:?count}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${2:-$ROOT/loadtest/results/contexts-bundles}"
SRC="$(ls "$ROOT"/turnbase-game-tictactoe/target/seed/*.zip | head -1)"
mkdir -p "$OUT"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
ids=()
for k in $(seq 1 "$N"); do
  id="$(uuidgen | tr 'A-Z' 'a-z')"
  d="$WORK/$k"; mkdir -p "$d"
  unzip -q "$SRC" -d "$d"
  jq --arg k "$k" '.title = .title + " " + $k | .version = "1.0." + $k' "$d/manifest.json" > "$d/manifest.new"
  mv "$d/manifest.new" "$d/manifest.json"
  ( cd "$d" && zip -q -X -r "$OUT/$id.zip" manifest.json INFO.md backend frontend )
  ids+=("$id")
done
( IFS=,; echo "${ids[*]}" )
