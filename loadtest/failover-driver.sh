#!/usr/bin/env bash
# Drives the kills of the `failover` scenario through kubectl (load-testing-phase-b.md §6) and writes each one to
# the scaling timeline as a `mark` row, at the moment it happens.
# Usage: loadtest/failover-driver.sh <run-dir>      (started by run.sh when the scenario is `failover`)
# Env: FAILOVER_WARMUP_S (180: after the setup, for the ramp and the settle), FAILOVER_RECOVER_S (120: pause after a
# pod is Ready again). Order: platform SIGKILL, Game Host SIGKILL, platform graceful, Game Host graceful.
# "SIGKILL" is `kubectl delete --grace-period=0 --force`: the container gets no signal handler time at all.
set -uo pipefail
DIR="${1:?usage: failover-driver.sh <run-dir>}"
WARMUP="${FAILOVER_WARMUP_S:-180}"
RECOVER="${FAILOVER_RECOVER_S:-120}"
T="$DIR/timeline.csv"
mark() { echo "$(date +%s),mark,$1,$2," >> "$T"; echo "$(date -u +%T) $1 $2"; }
until grep -q TB_SETUP_DONE "$DIR/k6.log" 2>/dev/null; do
  [ -e "$DIR/exit-code" ] && exit 0
  sleep 2
done
sleep "$WARMUP"
victim() { kubectl get pods -l "app.kubernetes.io/name=$1" --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}'; }
wait_ready() { # app, replicas: every pod Ready and the Deployment back at full strength
  local app="$1" want="$2" i
  for i in $(seq 120); do
    [ -e "$DIR/exit-code" ] && return 1
    [ "$(kubectl get deploy "turnbase-$app" -o jsonpath='{.status.readyReplicas}')" = "$want" ] \
      && [ "$(kubectl get pods -l "app.kubernetes.io/name=$app" --no-headers | wc -l)" = "$want" ] && return 0
    sleep 5
  done
  return 1
}
kill_one() { # app, mode
  local app="$1" mode="$2" pod want
  want="$(kubectl get deploy "turnbase-$app" -o jsonpath='{.spec.replicas}')"
  pod="$(victim "$app")"
  [ -n "$pod" ] || { mark "skip-$app-$mode" "no running pod"; return; }
  mark "kill-$app-$mode" "$pod"
  if [ "$mode" = sigkill ]; then kubectl delete pod "$pod" --grace-period=0 --force >/dev/null 2>&1
  else kubectl delete pod "$pod" --wait=false >/dev/null 2>&1; fi
  wait_ready "$app" "$want" && mark "recovered-$app-$mode" "$want ready" || mark "not-recovered-$app-$mode" "$want expected"
  sleep "$RECOVER"
}
kill_one platform sigkill
kill_one gamehost sigkill
kill_one platform graceful
kill_one gamehost graceful
mark failover-done ""
