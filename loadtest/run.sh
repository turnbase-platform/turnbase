#!/usr/bin/env bash
# Starts a scenario in the background and waits for it, so no shell call outlives the ten-minute cap.
# clock.start / clock.end hold `<uptime> <wall>`: wall seconds elapsed / uptime seconds elapsed below 1 means the guest
# clock was slewed slow, and wall-clock offsets (epochs, Prometheus) drift from the k6 plan (README, Phase B).
# timeline.csv (the scaling timeline, timeline.sh) is written beside them; correctness.sh checks the run afterwards.
# Usage: loadtest/run.sh start <scenario> [VAR=value ...]   prints RUN_DIR=<dir> and returns at once
#        loadtest/run.sh wait <run-dir> [seconds=280]       exit 0 finished (prints exit-code), 124 still running
# The run directory loadtest/results/<stamp>-<scenario>/ (git-ignored) holds k6.log, summary.json (k6's
# --summary-export), samples.csv, pods.csv, redis.csv, params.txt, cluster.txt, start.epoch (launch), scenario.epoch (setup
# done = the first step starts), end.epoch and exit-code. There is no per-sample JSON stream: a 30-minute
# 1,000-pair run would emit hundreds of millions of samples; the percentiles come from summary.json and
# the series from Prometheus (k6 pushes there through remote write).
# k6's exit code 99 (a threshold crossed) is a normal finished run, never a failure of this script.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# 3 cores since Phase B (load-testing-phase-b.md §4.4: the node budget at the maxima); 2 on a VM under 12 CPUs.
cores_for_k6() { [ "$(nproc)" -ge 12 ] && echo 3 || echo 2; }

case "${1:-}" in
start)
  scenario="${2:?usage: run.sh start <scenario> [VAR=value ...]}"
  shift 2
  [ -f "loadtest/scenarios/$scenario.js" ] || { echo "no such scenario: loadtest/scenarios/$scenario.js" >&2; exit 2; }
  DIR="$ROOT/loadtest/results/$(date +%Y%m%d-%H%M%S)-$scenario"
  mkdir -p "$DIR"
  { echo "scenario=$scenario"; echo "date=$(date -u +%FT%TZ)"; echo "K6_CORES=$(cores_for_k6)"; for kv in "$@"; do echo "$kv"; done; } > "$DIR/params.txt"
  bash loadtest/preflight.sh || { echo "preflight failed; run dir $DIR" >&2; exit 1; }
  {
    echo "## docker info"; docker info --format 'CPUs={{.NCPU}} MemTotal={{.MemTotal}}'
    echo "## nodes"; kubectl get nodes -o wide; kubectl top nodes
    echo "## helm values"; helm get values turnbase
    echo "## images"; for i in platform game-host frontend; do docker image inspect "turnbase/$i:dev" --format "turnbase/$i:dev {{.Id}}"; done
    echo "## root commit"; git rev-parse HEAD
    echo "## submodules"; git submodule status
    echo "## wslconfig"; cat ~/.wslconfig 2>/dev/null || echo "wslconfig: absent"
    echo "## k6"; k6 version
  } > "$DIR/cluster.txt" 2>&1
  if ! curl -s -m 2 localhost:9090/-/ready >/dev/null; then
    nohup setsid kubectl port-forward svc/turnbase-prometheus 9090:9090 >/dev/null 2>&1 &
    for _ in $(seq 20); do curl -s -m 2 localhost:9090/-/ready >/dev/null && break; sleep 1; done
  fi
  # The counters are cumulative: zero them so a delta in this run's report excludes every earlier run.
  # LATENCY LATEST stays empty unless a threshold is set (the default of 0 disables the monitor).
  kubectl exec statefulset/turnbase-postgres -- psql -U turnbase_owner -d turnbase -Atc "select pg_stat_statements_reset()" >/dev/null 2>&1 \
    || echo "pg_stat_statements unavailable: counters not reset" | tee -a "$DIR/cluster.txt" >&2
  kubectl exec statefulset/turnbase-redis -- sh -c 'redis-cli -a "$TURNBASE_REDIS_PASSWORD" CONFIG RESETSTAT; redis-cli -a "$TURNBASE_REDIS_PASSWORD" CONFIG SET latency-monitor-threshold 100' >/dev/null 2>&1 \
    || echo "redis counters not reset" | tee -a "$DIR/cluster.txt" >&2
  echo "$(cut -d' ' -f1 /proc/uptime) $(date +%s.%N)" > "$DIR/clock.start" # monotonic, wall: the WSL 2 wall clock can be slewed
  nohup setsid bash "$0" _exec "$DIR" "$scenario" "$@" >/dev/null 2>&1 &
  date +%s > "$DIR/start.epoch"
  nohup setsid bash loadtest/sample-generator.sh "$DIR" >/dev/null 2>&1 &
  nohup setsid bash loadtest/redis-sampler.sh "$DIR" >/dev/null 2>&1 &
  nohup setsid bash loadtest/timeline.sh "$DIR" >/dev/null 2>&1 &
  if [ "$scenario" = failover ]; then nohup setsid bash loadtest/failover-driver.sh "$DIR" > "$DIR/failover.log" 2>&1 & fi
  echo "RUN_DIR=$DIR"
  ;;
_exec)
  DIR="$2"; scenario="$3"; shift 3
  ulimit -n "$(ulimit -Hn)" 2>/dev/null # 1,024 sockets is not enough for 2,000 players
  n="$(nproc)"; cores="$(cores_for_k6)"; first=$((n - cores))
  args=()
  # failover.js reuses scale-in.js, whose defaults are four minutes; a failover run is four kills with recoveries.
  if [ "$scenario" = failover ]; then args+=(-e DURATION_S=1500 -e LOAD_HOLD_S=1440); fi
  for kv in "$@"; do args+=(-e "$kv"); done
  out=()
  # Remote write only when the Prometheus of this install accepts it (the default-limits overlay has no receiver).
  # `localhost:9090` can be answered by a foreign listener on 127.0.0.1 (k6 then fails every push with a malformed
  # HTTP status) while the port-forward holds ::1: use whichever address answers as Prometheus.
  prom=""
  for a in 127.0.0.1 '[::1]'; do
    if curl -s -m 2 "http://$a:9090/api/v1/status/flags" | jq -e '.data["web.enable-remote-write-receiver"] == "true"' >/dev/null 2>&1; then prom="$a"; break; fi
  done
  [ -n "$prom" ] && out=(-o experimental-prometheus-rw)
  K6_PROMETHEUS_RW_SERVER_URL="http://${prom:-localhost}:9090/api/v1/write" \
  K6_PROMETHEUS_RW_TREND_STATS='p(50),p(95),p(99),max,count' K6_PROMETHEUS_RW_PUSH_INTERVAL=5s \
    taskset -c "$first-$((n - 1))" k6 run "${out[@]}" --summary-export "$DIR/summary.json" "${args[@]}" \
    "loadtest/scenarios/$scenario.js" > "$DIR/k6.log" 2>&1
  code=$?
  echo "$(cut -d' ' -f1 /proc/uptime) $(date +%s.%N)" > "$DIR/clock.end"
  date +%s > "$DIR/end.epoch"
  ms="$(grep -o 'TB_SETUP_DONE [0-9]*' "$DIR/k6.log" | head -1 | cut -d' ' -f2)"
  if [ -n "$ms" ]; then echo $((ms / 1000)) > "$DIR/scenario.epoch"; else cp "$DIR/start.epoch" "$DIR/scenario.epoch"; fi
  echo "$code" > "$DIR/exit-code"
  ;;
wait)
  DIR="${2:?usage: run.sh wait <run-dir> [seconds=280]}"
  budget="${3:-280}"
  waited=0
  while [ ! -e "$DIR/exit-code" ] && [ "$waited" -lt "$budget" ]; do sleep 5; waited=$((waited + 5)); done
  last="$(tr '\r' '\n' < "$DIR/k6.log" 2>/dev/null | grep -v '^\s*$' | tail -1)"
  echo "last: $last"
  if [ -e "$DIR/exit-code" ]; then echo "exit-code: $(cat "$DIR/exit-code")"; exit 0; fi
  exit 124
  ;;
*)
  echo "usage: run.sh start <scenario> [VAR=value ...] | run.sh wait <run-dir> [seconds]" >&2
  exit 2
  ;;
esac
