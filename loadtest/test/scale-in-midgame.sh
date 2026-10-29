#!/usr/bin/env bash
# IMP-M18-10 on the cluster: eight pairs play through (A) an HPA scale-in from three Platform pods to two and
# (B) a graceful delete of one of two pods. Pass = k6's thresholds hold (no started game lost, no ROOM_UNAVAILABLE_RETRY
# outliving RETRY_BUDGET_MS) and the log lines show the survivor adopting rooms the victim released.
# Usage: loadtest/test/scale-in-midgame.sh [A|B|both]      (default both; needs the Phase B overlay installed)
# Env: LOAD_PAIRS (128) the plain pairs that push the HPA to three pods in A; RETRY_BUDGET_MS (30000).
set -euo pipefail
cd "$(dirname "$0")/../.."
part="${1:-both}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DIR="loadtest/results/$STAMP-scale-in"; mkdir -p "$DIR"
LOAD_PAIRS="${LOAD_PAIRS:-128}"
export RETRY_BUDGET_MS="${RETRY_BUDGET_MS:-30000}" USERS="${USERS:-2000}"
n="$(nproc)"; first=$((n - 3))
sel='app.kubernetes.io/name=platform'
say() { echo "[$(date -u +%T)] $*" | tee -a "$DIR/test.log"; }
replicas() { kubectl get hpa turnbase-platform -o jsonpath='{.status.currentReplicas}'; }
ready_pods() { kubectl get pods -l "$sel" --field-selector=status.phase=Running -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.status.containerStatuses[0].ready}{"\n"}{end}' | awk '$2=="true"{print $1}'; }
wait_for() { # <seconds> <description> <command...>
  local t="$1" d="$2"; shift 2; local end=$((SECONDS + t))
  until "$@"; do [ $SECONDS -lt $end ] || { say "TIMEOUT waiting for $d"; return 1; }; sleep 5; done
  say "reached: $d"
}
two_ready() { [ "$(replicas)" = 2 ] && [ "$(ready_pods | wc -l)" = 2 ]; }
three() { [ "$(replicas)" = 3 ]; }
k6bg() { # <name> <env...>: runs k6 pinned to the last three cores, returns its pid in $K6PID
  local name="$1"; shift
  ( env "$@" taskset -c "$first-$((n - 1))" k6 run --summary-export "$DIR/$name-summary.json" loadtest/scenarios/scale-in.js > "$DIR/$name-k6.log" 2>&1; echo $? > "$DIR/$name-k6.exit" ) &
  K6PID=$!
}
collect_logs() { # follow every Platform pod's log into $DIR/<name>-<pod>.log until the pod is gone
  local name="$1"
  for p in $(kubectl get pods -l "$sel" -o name); do
    [ -e "$DIR/$name-${p#pod/}.log" ] && continue
    ( kubectl logs -f "$p" > "$DIR/$name-${p#pod/}.log" 2>&1 || true ) &
  done
}
verdict() { # <name>
  local name="$1"
  wait "$K6PID" || true
  local code; code="$(cat "$DIR/$name-k6.exit")"
  say "$name: k6 exit $code (0 = thresholds held); $(grep -hE 'tb_si_games_(finished|aborted|lost)|tb_si_recoveries|tb_si_budget_exceeded' "$DIR/$name-k6.log" | tr -s ' .' ' ' | tr '\n' ';')"
  [ "$code" = 0 ] || { say "$name FAILED"; return 1; }
}
adopted_check() { # <name> : at least one room a pod released is adopted by another pod
  local name="$1" ok=1
  grep -h "drain released room" "$DIR/$name"-*.log | sed 's/.*drain released room \([0-9a-f-]*\).*/\1/' | sort -u > "$DIR/$name-released.txt" || true
  say "$name: rooms released by draining pods: $(wc -l < "$DIR/$name-released.txt")"
  [ -s "$DIR/$name-released.txt" ] || { say "$name FAILED: no drain log lines"; return 1; }
  local hits=0
  while read -r id; do
    grep -qh "adopted room $id" "$DIR/$name"-*.log && hits=$((hits + 1))
  done < "$DIR/$name-released.txt"
  say "$name: released rooms adopted afterwards by a survivor: $hits"
  [ "$hits" -gt 0 ] || ok=0
  [ "$ok" = 1 ] || { say "$name FAILED: no released room was adopted"; return 1; }
}

wait_for 300 "two ready Platform pods" two_ready

if [ "$part" = A ] || [ "$part" = both ]; then
  say "A: scale-in 3 -> 2 with 8 watched pairs; load $LOAD_PAIRS pairs push the HPA to three first"
  collect_logs A
  k6bg A WATCHED_PAIRS=8 DURATION_S=480 LOAD_PAIRS="$LOAD_PAIRS" LOAD_HOLD_S=150
  wait_for 300 "HPA at three replicas" three
  collect_logs A # the third pod
  say "A: $(kubectl get hpa turnbase-platform --no-headers)"
  wait_for 420 "HPA back at two replicas" two_ready
  sleep 20
  verdict A
  say "A: rooms released by the scaled-in pod: $(cat "$DIR"/A-*.log | grep -c 'drain released room' || true) (the pod the HPA removes may own none)"
fi

if [ "$part" = B ] || [ "$part" = both ]; then
  wait_for 300 "two ready Platform pods" two_ready
  say "B: graceful delete of one of two pods with 8 watched pairs"
  collect_logs B
  k6bg B WATCHED_PAIRS=8 DURATION_S=120
  sleep 40
  victim="$(ready_pods | head -1)"
  say "B: deleting $victim"
  kubectl delete pod "$victim" --wait=false
  verdict B; adopted_check B
fi
say "scale-in test passed; $DIR"
