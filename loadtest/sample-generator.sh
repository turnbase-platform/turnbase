#!/usr/bin/env bash
# Samples the load generator and the VM while a run is going, until <run-dir>/exit-code exists.
# Usage: loadtest/sample-generator.sh <run-dir>      (started by run.sh)
# Every 5 s appends `epoch,k6_cpu_pct,vm_cpu_pct,load1` to samples.csv: k6_cpu_pct is the CPU time the newest
# k6 process used in the interval as a percentage of ONE core (3 cores reach 300); vm_cpu_pct is the busy
# share of all CPUs. Every third sample appends `epoch,pod,cpu_m,mem_mi` rows from `kubectl top pods` to pods.csv.
set -uo pipefail
DIR="${1:?usage: sample-generator.sh <run-dir>}"
TICKS="$(getconf CLK_TCK)"
INTERVAL=5

cpu_ticks() { awk '{print $14 + $15}' "/proc/$1/stat" 2>/dev/null || echo 0; }
vm_times() { awk '/^cpu /{idle=$5+$6; t=0; for (i=2;i<=NF;i++) t+=$i; print t, idle}' /proc/stat; }

prev_pid=""; prev_k6=0
read -r prev_total prev_idle < <(vm_times)
n=0
while [ ! -e "$DIR/exit-code" ]; do
  sleep "$INTERVAL"
  now="$(date +%s)"
  pid="$(pgrep -n -x k6 || true)"
  k6pct=0
  if [ -n "$pid" ]; then
    cur="$(cpu_ticks "$pid")"
    [ "$pid" = "$prev_pid" ] && k6pct="$(awk -v a="$cur" -v b="$prev_k6" -v t="$TICKS" -v i="$INTERVAL" 'BEGIN{printf "%.0f", (a-b)/t/i*100}')"
    prev_pid="$pid"; prev_k6="$cur"
  fi
  read -r total idle < <(vm_times)
  vmpct="$(awk -v t="$total" -v pt="$prev_total" -v i="$idle" -v pi="$prev_idle" 'BEGIN{d=t-pt; printf "%.0f", (d > 0 ? (d-(i-pi))/d*100 : 0)}')"
  prev_total="$total"; prev_idle="$idle"
  echo "$now,$k6pct,$vmpct,$(cut -d' ' -f1 /proc/loadavg)" >> "$DIR/samples.csv"
  n=$((n + 1))
  if [ $((n % 3)) -eq 0 ]; then
    kubectl top pods --no-headers 2>/dev/null | awk -v e="$now" '{gsub(/m$/,"",$2); gsub(/Mi$/,"",$3); print e "," $1 "," $2 "," $3}' >> "$DIR/pods.csv"
  fi
done
