#!/usr/bin/env bash
# Measures how often a freshly started Game Host wedges on its first real guest boot (IMP-M16-03).
# Usage: loadtest/boot-wedge-repro.sh <cycles> <pairs> [--dry-run]
#   <pairs> is 1 for the baseline and 4 for contention (four contexts boot at once).
# Each cycle: delete the Game Host pod; wait for a differently named pod to be Ready; run the smoke
# scenario with PAIRS=<pairs> (the first real boot happens through the platform with the Tic-Tac-Toe
# bundle); save the new pod's logs and count both wedge modes in them:
#   mode A = supervisor lines "killing it" (silent liveness probes: the whole-JVM stall),
#   mode B = the BootWatchdog line "Guest boot wedged" (a stuck guest thread in a live JVM).
# Output: loadtest/results/<stamp>-boot-wedge/boot-wedge.csv with
#   cycle,pairs,pod,mode_a,mode_b,smoke_exit,seconds_to_first_game
# plus gamehost-NN.log (and gamehost-NN.previous.log when the container restarted). A cycle whose pod does
# not become Ready in 300 s is written with smoke_exit=ready_timeout and the next cycle goes on.
# --dry-run prints the commands of one cycle and runs none of them.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

CYCLES="${1:?usage: boot-wedge-repro.sh <cycles> <pairs> [--dry-run]}"
PAIRS="${2:?usage: boot-wedge-repro.sh <cycles> <pairs> [--dry-run]}"
DRY=0
[ "${3:-}" = "--dry-run" ] && DRY=1

SELECTOR="app.kubernetes.io/name=gamehost,app.kubernetes.io/instance=turnbase"

if [ "$DRY" = 1 ]; then
  cat <<EOF
# one cycle (of $CYCLES) with PAIRS=$PAIRS; nothing is run
old=\$(kubectl get pods -l $SELECTOR -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod -l $SELECTOR --wait=true
until a pod named differently from \$old exists:  kubectl get pods -l $SELECTOR -o jsonpath='{.items[0].metadata.name}'
kubectl wait --for=condition=Ready pod/<new> --timeout=300s      # on timeout: smoke_exit=ready_timeout, next cycle
bash loadtest/run.sh start smoke PAIRS=$PAIRS                    # prints RUN_DIR=...
bash loadtest/run.sh wait <run-dir> 280                          # repeated until it exits 0
kubectl logs --timestamps <new> > <run-dir>/gamehost-NN.log
kubectl logs --timestamps --previous <new> > <run-dir>/gamehost-NN.previous.log   # only if the container restarted
grep -c 'killing it' (mode A) ; grep -c 'Guest boot wedged' (mode B)
append: cycle,$PAIRS,<new>,<mode_a>,<mode_b>,<smoke exit-code>,<tb_game_start{cold:true}.max / 1000 from summary.json>
EOF
  exit 0
fi

bash loadtest/preflight.sh || { echo "preflight failed" >&2; exit 1; }
OUT="$ROOT/loadtest/results/$(date +%Y%m%d-%H%M%S)-boot-wedge"
mkdir -p "$OUT"
echo "cycle,pairs,pod,mode_a,mode_b,smoke_exit,seconds_to_first_game" > "$OUT/boot-wedge.csv"
echo "RUN_DIR=$OUT"

current_pod() { kubectl get pods -l "$SELECTOR" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null | tr ' ' '\n' | grep -v '^$' | head -1; }
count() { grep -c "$1" "$2" 2>/dev/null || true; }

for cycle in $(seq "$CYCLES"); do
  nn="$(printf '%02d' "$cycle")"
  old="$(current_pod)"
  kubectl delete pod -l "$SELECTOR" --wait=true >/dev/null
  new=""
  for _ in $(seq 120); do
    new="$(current_pod)"
    [ -n "$new" ] && [ "$new" != "$old" ] && break
    new=""; sleep 1
  done
  smoke_exit="" ; first=""
  if [ -z "$new" ] || ! kubectl wait --for=condition=Ready "pod/$new" --timeout=300s >/dev/null 2>&1; then
    smoke_exit="ready_timeout"
  else
    start_out="$(bash loadtest/run.sh start smoke "PAIRS=$PAIRS" 2>&1)"
    dir="$(printf '%s\n' "$start_out" | sed -n 's/^RUN_DIR=//p')"
    if [ -z "$dir" ]; then
      smoke_exit="start_failed"
    else
      for _ in 1 2 3 4; do bash loadtest/run.sh wait "$dir" 280 >/dev/null && break; done
      smoke_exit="$(cat "$dir/exit-code" 2>/dev/null || echo running)"
      ms="$(jq -r '.metrics["tb_game_start{cold:true}"].max // empty' "$dir/summary.json" 2>/dev/null)"
      [ -n "$ms" ] && first="$(awk -v ms="$ms" 'BEGIN{printf "%.1f", ms/1000}')"
      echo "$cycle $dir" >> "$OUT/smoke-dirs.txt"
    fi
  fi
  if [ -n "$new" ]; then
    kubectl logs --timestamps "$new" > "$OUT/gamehost-$nn.log" 2>&1
    kubectl logs --timestamps --previous "$new" > "$OUT/gamehost-$nn.previous.log" 2>/dev/null || rm -f "$OUT/gamehost-$nn.previous.log"
  fi
  logs=("$OUT/gamehost-$nn.log"); [ -f "$OUT/gamehost-$nn.previous.log" ] && logs+=("$OUT/gamehost-$nn.previous.log")
  mode_a=0; mode_b=0
  for f in "${logs[@]}"; do
    [ -f "$f" ] || continue
    mode_a=$((mode_a + $(count 'killing it' "$f"))); mode_b=$((mode_b + $(count 'Guest boot wedged' "$f")))
  done
  echo "$cycle,$PAIRS,${new:-none},$mode_a,$mode_b,$smoke_exit,$first" | tee -a "$OUT/boot-wedge.csv"
done

awk -F, 'NR>1{n++; if($4>0)a++; if($5>0)b++; if($4>0||$5>0||$6=="ready_timeout")w++} END{printf "cycles=%d mode_a=%d mode_b=%d wedged_or_timeout=%d\n", n,a,b,w}' "$OUT/boot-wedge.csv" | tee "$OUT/summary.txt"
