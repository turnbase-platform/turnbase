#!/usr/bin/env bash
# Time-to-ready of one compose service (IMP-M20-17): stop it, start it, poll /actuator/health until 200.
# Usage: scripts/startup-time.sh <platform|gamehost> [runs=5]   (stack already up, from turnbase-platform/deploy/compose)
set -euo pipefail
svc="${1:?platform|gamehost}"; runs="${2:-5}"
case "$svc" in platform) port=8081 ;; gamehost) port=8082 ;; *) echo "unknown service" >&2; exit 2 ;; esac
cd "$(dirname "${BASH_SOURCE[0]}")/../turnbase-platform/deploy/compose"
ms() { date +%s%3N; }
for i in $(seq 1 "$runs"); do
  docker compose stop -t 20 "$svc" >/dev/null 2>&1
  t0=$(ms)
  docker compose start "$svc" >/dev/null 2>&1
  until curl -sf -m 1 -o /dev/null "http://127.0.0.1:$port/actuator/health"; do
    sleep 0.2; [ $(( $(ms) - t0 )) -gt 180000 ] && { echo "run $i: timeout"; exit 1; }
  done
  echo "$svc run $i: $(( $(ms) - t0 )) ms"
done
