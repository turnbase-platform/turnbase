#!/usr/bin/env bash
# Platform CPU per move for a single-level `parallelism` run (IMP-M16-13).
# Usage: loadtest/cpu-per-move.sh <run-dir>
# Needs prom/platform_cpu_cores.json and prom/gamehost_cpu_cores.json (snapshot.sh) and steps.csv (steps-table.sh).
# The window is the measured part of the step: scenario.epoch + SETTLE_SECONDS .. scenario.epoch + STEP_SECONDS.
# Prints moves per second (count(tb_move_rtt) / (STEP - SETTLE)), the window's mean platform and Game Host cores,
# and platform CPU milliseconds per move (cores * 1000 / moves per second).
set -euo pipefail
DIR="${1:?usage: cpu-per-move.sh <run-dir>}"
param() { sed -n "s/^$1=//p" "$DIR/params.txt" | tail -1; }
STEP="$(param STEP_SECONDS)"; SETTLE="$(param SETTLE_SECONDS)"; START="$(cat "$DIR/scenario.epoch")"
moves="$(awk -F, '$2=="tb_move_rtt"{print $3}' "$DIR/steps.csv" | head -1)"
mean() { # <series file>
  jq -r --argjson lo "$((START + SETTLE))" --argjson hi "$((START + STEP))" \
    '[.data.result[0].values[] | select(.[0] >= $lo and .[0] <= $hi) | .[1] | tonumber] | add / length' "$DIR/prom/$1.json"
}
pc="$(mean platform_cpu_cores)"; gc="$(mean gamehost_cpu_cores)"
awk -v m="$moves" -v w="$((STEP - SETTLE))" -v p="$pc" -v g="$gc" 'BEGIN {
  r = m / w
  printf "moves=%d window=%ds moves_per_s=%.1f platform_cores=%.3f gamehost_cores=%.3f platform_cpu_ms_per_move=%.3f\n", m, w, r, p, g, p * 1000 / r }'
