#!/usr/bin/env bash
# IMP-M18-13 on the cluster. (A) a load past the per-host cap brings a third Game Host Ready within NFR-ASC-001's
# 3 min, and when it ends KEDA takes the fleet back to two. (B) a graceful delete of one Game Host with 8 pairs playing
# games that outlast the drain period: the host announces draining and takes no new session, and every game finishes,
# those still on it after the drain being reassigned.
# Usage: loadtest/test/gamehost-scale.sh [A|B|both]      (default both; needs the Phase B overlay installed)
# Env: CAP_PAIRS (200: concurrent games, above 0.7 x 2 x 100), RETRY_BUDGET_MS (30000).
set -euo pipefail
cd "$(dirname "$0")/../.."
part="${1:-both}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DIR="loadtest/results/$STAMP-gamehost-scale"; mkdir -p "$DIR"
CAP_PAIRS="${CAP_PAIRS:-200}"
export RETRY_BUDGET_MS="${RETRY_BUDGET_MS:-30000}" USERS="${USERS:-2000}"
n="$(nproc)"; first=$((n - 3))
gh='app.kubernetes.io/name=gamehost'
say() { echo "[$(date -u +%T)] $*" | tee -a "$DIR/test.log"; }
ready_hosts() { kubectl get pods -l "$gh" --field-selector=status.phase=Running -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.status.containerStatuses[0].ready}{" "}{.metadata.deletionTimestamp}{"\n"}{end}' | awk '$2=="true" && $3==""{print $1}'; }
n_ready() { ready_hosts | wc -l; }
three_ready() { [ "$(n_ready)" -ge 3 ]; }
two_ready() { [ "$(n_ready)" = 2 ] && [ "$(kubectl get pods -l "$gh" --no-headers | wc -l)" = 2 ]; }
wait_for() { # <seconds> <description> <command...>
  local t="$1" d="$2"; shift 2; local end=$((SECONDS + t))
  until "$@"; do [ $SECONDS -lt $end ] || { say "TIMEOUT waiting for $d"; return 1; }; sleep 3; done
  say "reached: $d"
}
busy_host() { # the Ready Game Host pod with most sessions (registry: host:<id> address, activeSessions)
  kubectl exec statefulset/turnbase-redis -- sh -c 'r() { redis-cli -a "$TURNBASE_REDIS_PASSWORD" --no-auth-warning "$@"; }; for k in $(r --scan --pattern "host:*"); do echo $(r HGET $k address) $(r HGET $k activeSessions); done' 2>/dev/null |
    sort -k2 -n -r | while read -r addr sess; do
      ip="${addr%%:*}"; pod="$(kubectl get pods -l "$gh" -o jsonpath="{range .items[?(@.status.podIP==\"$ip\")]}{.metadata.name}{end}")"
      [ -n "$pod" ] && { echo "$pod $sess"; break; }
    done
}
warm_standby() { # the warm-hosts rule: two starts one after the other leave both hosts holding the context
  for i in 1 2; do
    k6bg "warm$i" WATCHED_PAIRS=1 DURATION_S=10 THINK_MIN_MS=800 THINK_MAX_MS=1500
    wait "$K6PID" || true
    sleep 12  # ReportContexts follows the context's creation
  done
  warm="$(kubectl exec statefulset/turnbase-redis -- sh -c 'r() { redis-cli -a "$TURNBASE_REDIS_PASSWORD" --no-auth-warning "$@"; }; for h in $(r SMEMBERS hosts); do r SCARD contexts:$h; done' 2>/dev/null | grep -c '^[1-9]')"
  say "B: $warm Game Hosts hold the game's context after two starts (warm-hosts 2)"
  [ "$warm" -ge 2 ] || { say "B FAILED: the standby was not warmed"; exit 1; }
}
k6bg() { # <name> <env...>
  local name="$1"; shift
  ( env "$@" taskset -c "$first-$((n - 1))" timeout -k 10 900 k6 run --summary-export "$DIR/$name-summary.json" loadtest/scenarios/scale-in.js > "$DIR/$name-k6.log" 2>&1; echo $? > "$DIR/$name-k6.exit" ) &
  K6PID=$!
}
follow_logs() { # <name>: every Game Host pod's log until it is gone, and the Platform pods'
  local name="$1"
  for p in $(kubectl get pods -l "$gh" -o name) $(kubectl get pods -l app.kubernetes.io/name=platform -o name); do
    [ -s "$DIR/$name-${p#pod/}.log" ] && continue
    ( kubectl logs -f "$p" > "$DIR/$name-${p#pod/}.log" 2>&1 || true ) &
  done
}
verdict() { # <name>
  local name="$1"
  wait "$K6PID" || true
  until [ -s "$DIR/$name-k6.exit" ]; do sleep 1; done  # k6 is killed after 900 s: it once hung after its summary
  local code; code="$(cat "$DIR/$name-k6.exit")"
  say "$name: k6 exit $code (0 = thresholds held); $(grep -hE 'tb_si_games_(finished|aborted|lost)|tb_si_recoveries|tb_si_budget_exceeded' "$DIR/$name-k6.log" | tr -s ' .' ' ' | tr '\n' ';')"
  [ "$code" = 0 ] || { say "$name FAILED"; return 1; }
}

wait_for 600 "two ready Game Hosts" two_ready
say "at rest: $(kubectl get scaledobject turnbase-gamehost --no-headers 2>&1)"

if [ "$part" = A ] || [ "$part" = both ]; then
  say "A: $CAP_PAIRS pairs play at once (about 2 x 100 x 0.7 = 140 sessions trips the 0.7 utilisation target)"
  follow_logs A
  t0=$SECONDS
  k6bg A WATCHED_PAIRS="$CAP_PAIRS" DURATION_S=300 THINK_MIN_MS=800 THINK_MAX_MS=1500
  until [ "$(kubectl get pods -l "$gh" --no-headers | wc -l)" -ge 3 ]; do
    [ $((SECONDS - t0)) -lt 400 ] || { say "A FAILED: no third Game Host pod"; exit 1; }
    sleep 2
  done
  say "A: third pod created $((SECONDS - t0)) s after the load started; sessions utilisation $(curl -s localhost:9090/api/v1/query --data-urlencode 'query=max(turnbase_gamehost_sessions_utilization)' 2>/dev/null | sed 's/.*"value":\[[^,]*,"\([^"]*\)".*/\1/' || true)"
  t1=$SECONDS
  wait_for 240 "three ready Game Hosts" three_ready || true
  say "A: the third Game Host was Ready $((SECONDS - t1)) s after its pod was created, $((SECONDS - t0)) s after the load started (NFR-ASC-001: 180 s from the threshold crossing)"
  follow_logs A
  say "A: pod timeline (created, scheduled, containers ready, ready): $(kubectl get pods -l "$gh" --sort-by=.metadata.creationTimestamp -o jsonpath='{range .items[-1:]}{.metadata.creationTimestamp}{" "}{.status.conditions[?(@.type=="PodScheduled")].lastTransitionTime}{" "}{.status.conditions[?(@.type=="ContainersReady")].lastTransitionTime}{" "}{.status.conditions[?(@.type=="Ready")].lastTransitionTime}{end}'); events: $(kubectl get events --field-selector involvedObject.kind=Pod --sort-by=.lastTimestamp 2>/dev/null | grep gamehost | tail -6 | tr -s ' ' | tr '\n' '|')"
  newest="$(kubectl get pods -l "$gh" --sort-by=.metadata.creationTimestamp -o name | tail -1)"
  kubectl describe "$newest" > "$DIR/A-newest-describe.txt" 2>&1 || true
  kubectl logs "$newest" --tail=60 > "$DIR/A-newest-tail.log" 2>&1 || true
  kubectl top node > "$DIR/A-top-node.txt" 2>&1 || true
  say "A: $(kubectl get scaledobject turnbase-gamehost --no-headers)"
  verdict A
  say "A: registry after the load: $(kubectl exec statefulset/turnbase-redis -- sh -c 'r() { redis-cli -a "$TURNBASE_REDIS_PASSWORD" --no-auth-warning "$@"; }; echo sessions=$(r --scan --pattern "session:*" | wc -l); for h in $(r SMEMBERS hosts); do echo $h $(r HGET host:$h activeSessions); done' 2>/dev/null | tr '\n' ' ')"
  wait_for 900 "two Game Hosts again" two_ready
  say "A: games per Game Host while at three: see the per-pod 'Drain over' lines: $(grep -h 'Drain over' "$DIR"/A-*.log | tr '\n' ';')"
fi

if [ "$part" = B ] || [ "$part" = both ]; then
  wait_for 600 "two ready Game Hosts" two_ready
  say "B: graceful delete of one of two Game Hosts with 8 watched pairs (think 3-5 s: a game outlasts the 30 s drain)"
  follow_logs B
  warm_standby
  k6bg B WATCHED_PAIRS=8 DURATION_S=200 THINK_MIN_MS=3000 THINK_MAX_MS=5000
  sleep 45
  read -r victim held <<<"$(busy_host)"
  [ -n "${victim:-}" ] || victim="$(ready_hosts | head -1)"
  say "B: deleting $victim, which holds $held sessions in the registry"
  kubectl delete pod "$victim" --wait=false
  verdict B
  vlog="$DIR/B-$victim.log"
  grep -h 'Game Host draining' "$DIR"/B-turnbase-platform-*.log | head -3 | tee -a "$DIR/test.log" || { say "B FAILED: the Platform never logged the host as draining"; exit 1; }
  grep -h 'Draining\|Drain over' "$vlog" | tee -a "$DIR/test.log"
  say "B: sessions reassigned off the drained host: $(cat "$DIR"/B-turnbase-platform-*.log | grep -c 'Reassigned sessionId' || true)"
  # No new session after the announcement: the count can only fall between "Draining" and "Drain over".
  start="$(sed -n 's/.*Draining.*activeSessions=\([0-9]*\).*/\1/p' "$vlog" | head -1)"; over="$(sed -n 's/.*Drain over.*activeSessions=\([0-9]*\).*/\1/p' "$vlog" | head -1)"
  say "B: the victim held $start sessions when it began draining and $over when the drain period ended"
  [ -n "$start" ] && [ -n "$over" ] && [ "$over" -le "$start" ] || { say "B FAILED: the session count rose while draining"; exit 1; }
fi
say "gamehost-scale test passed; $DIR"
