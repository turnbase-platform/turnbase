#!/usr/bin/env bash
# Samples the Redis keyspace and memory while a run is going, until <run-dir>/exit-code exists.
# Usage: loadtest/redis-sampler.sh <run-dir>      (started by run.sh start)
# Every 30 s appends `timestamp,dbsize,used_memory` to redis.csv (UTC ISO timestamp, key count, bytes). The
# header is written first and a sample is taken at once, so a short run still has a row.
set -uo pipefail
DIR="${1:?usage: redis-sampler.sh <run-dir>}"
INTERVAL=30

rcli() { kubectl exec statefulset/turnbase-redis -- sh -c "redis-cli -a \"\$TURNBASE_REDIS_PASSWORD\" $*" 2>/dev/null | tr -d '\r'; }

echo "timestamp,dbsize,used_memory" > "$DIR/redis.csv"
while true; do
  now="$(date -u +%FT%TZ)"
  size="$(rcli DBSIZE)"
  mem="$(rcli INFO memory | sed -n 's/^used_memory://p')"
  echo "$now,${size:-},${mem:-}" >> "$DIR/redis.csv"
  [ -e "$DIR/exit-code" ] && break
  sleep "$INTERVAL"
  [ -e "$DIR/exit-code" ] && break
done
