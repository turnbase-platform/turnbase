#!/usr/bin/env bash
# Collects the server-side evidence for one run: Prometheus series, pod restarts, Redis memory.
# Usage: loadtest/snapshot.sh <run-dir> [segment_seconds]
# Needs Prometheus on localhost:9090 (run.sh keeps a port-forward). Writes prom/<name>.json (one query_range
# each, step 15 s, from scenario.epoch to end.epoch), appends restarts and Redis INFO to cluster.txt, and
# prints a markdown table of mean / max per segment. segment_seconds defaults to STEP_SECONDS in params.txt,
# else 120. A series that does not exist prints n/a and is listed under "Missing metrics:". It also appends the
# Postgres pg_stat_statements top 20 (by calls, by total_exec_time) to cluster.txt and runs census.sh with the
# label `snapshot` (census-snapshot.txt).
set -euo pipefail
DIR="${1:?usage: snapshot.sh <run-dir> [segment_seconds]}"
SEG="${2:-$(sed -n 's/^STEP_SECONDS=//p' "$DIR/params.txt" | tail -1)}"; SEG="${SEG:-120}"
START="$(cat "$DIR/scenario.epoch" 2>/dev/null || cat "$DIR/start.epoch")"
END="$(cat "$DIR/end.epoch" 2>/dev/null || date +%s)"
PROM="${PROM_URL:-http://localhost:9090}"
mkdir -p "$DIR/prom"

QUERIES='gamehost_cpu_cores|max(process_cpu_usage{job="gamehost"}) * max(system_cpu_count{job="gamehost"})
platform_cpu_cores|max(process_cpu_usage{job="platform"}) * max(system_cpu_count{job="platform"})
gamehost_heap_bytes|sum(jvm_memory_used_bytes{job="gamehost",area="heap"})
platform_heap_bytes|sum(jvm_memory_used_bytes{job="platform",area="heap"})
gamehost_threads|max(jvm_threads_live_threads{job="gamehost"})
platform_threads|max(jvm_threads_live_threads{job="platform"})
gamehost_gc_seconds_per_s|sum(rate(jvm_gc_pause_seconds_sum{job="gamehost"}[1m]))
platform_gc_seconds_per_s|sum(rate(jvm_gc_pause_seconds_sum{job="platform"}[1m]))
http_p95_seconds|histogram_quantile(0.95, sum by (le) (rate(http_server_requests_seconds_bucket{job="platform"}[1m])))
http_p99_seconds|histogram_quantile(0.99, sum by (le) (rate(http_server_requests_seconds_bucket{job="platform"}[1m])))
http_5xx_per_s|sum(rate(http_server_requests_seconds_count{job="platform",status=~"5.."}[1m]))
http_req_per_s|sum(rate(http_server_requests_seconds_count{job="platform"}[1m]))
hikari_active|max(hikaricp_connections_active{job="platform"})
hikari_pending|max(hikaricp_connections_pending{job="platform"})
ws_connections|sum(turnbase_websocket_connections_active)
rooms_active|sum(turnbase_rooms_active)
sessions_active|sum(turnbase_game_sessions_active)
up|up'

curl -s -m 5 "$PROM/-/ready" >/dev/null || { echo "Prometheus is not answering on $PROM (kubectl port-forward svc/turnbase-prometheus 9090:9090)" >&2; exit 1; }

NSEG=$(( (END - START + SEG - 1) / SEG )); [ "$NSEG" -ge 1 ] || NSEG=1
missing=()
header="| metric (mean / max) |"; sep="|---|"
for i in $(seq 1 "$NSEG"); do header+=" seg $i ($(( (i-1)*SEG ))s) |"; sep+="---|"; done
echo "$header"; echo "$sep"
while IFS='|' read -r name expr; do
  [ -n "$name" ] || continue
  curl -s -m 30 --data-urlencode "query=$expr" --data-urlencode "start=$START" --data-urlencode "end=$END" \
    --data-urlencode "step=15" "$PROM/api/v1/query_range" > "$DIR/prom/$name.json" || echo '{}' > "$DIR/prom/$name.json"
  row="$(jq -r --argjson s "$START" --argjson seg "$SEG" --argjson n "$NSEG" --arg name "$name" '
    [.data.result[]?.values[]? | [(.[0] | tonumber), (try (.[1] | tonumber) catch null)] | select(.[1] != null and (.[1] | isnan | not))] as $v
    | if ($v | length) == 0 then "MISSING"
      else "| " + $name + " |" + ([range(0; $n) as $i
          | [$v[] | select(((.[0] - $s) / $seg | floor) == $i) | .[1]] as $x
          | if ($x | length) == 0 then " n/a |"
            else " \(($x | add / length) * 1000 | round / 1000) / \($x | max * 1000 | round / 1000) |" end] | join("")) end' "$DIR/prom/$name.json")"
  if [ "$row" = "MISSING" ]; then
    missing+=("$name")
    row="| $name |$(printf ' n/a |%.0s' $(seq 1 "$NSEG"))"
  fi
  echo "$row"
done <<< "$QUERIES"
echo
echo "Missing metrics: ${missing[*]:-none}"

echo
echo "Errors by code (k6 counter at the end of the run):"
curl -s -m 30 --data-urlencode 'query=sum by (code, expected) (k6_tb_errors_total)' --data-urlencode "time=$END" "$PROM/api/v1/query" \
  | jq -r '.data.result[]? | select(.metric.code) | "  \(.metric.code) expected=\(.metric.expected): \(.value[1])"' | tee "$DIR/prom/errors-by-code.txt"

{
  echo "## restarts and last termination reason (snapshot)"
  kubectl get pods -o json | jq -r '.items[] | [.metadata.name, ([.status.containerStatuses[]?.restartCount] | add), ([.status.containerStatuses[]? | .lastState.terminated.reason // empty] | join(","))] | @tsv'
  echo "## redis INFO memory / clients"
  for sec in memory clients; do
    kubectl exec statefulset/turnbase-redis -- sh -c "redis-cli -a \"\$TURNBASE_REDIS_PASSWORD\" INFO $sec" 2>/dev/null | tr -d '\r' | grep -E '^(used_memory_human|connected_clients)' || true
  done
} | tee -a "$DIR/cluster.txt"

pgss() { # <order by column>
  kubectl exec statefulset/turnbase-postgres -- psql -U turnbase_owner -d turnbase -c \
    "select calls, round(total_exec_time::numeric, 1) as total_ms, round(mean_exec_time::numeric, 3) as mean_ms, rows,
            left(regexp_replace(query, '\s+', ' ', 'g'), 110) as query
       from pg_stat_statements order by $1 desc limit 20" 2>&1
}
{
  if kubectl exec statefulset/turnbase-postgres -- psql -U turnbase_owner -d turnbase -Atc "select 1 from pg_stat_statements limit 1" >/dev/null 2>&1; then
    echo "## pg_stat_statements top 20 by calls"; pgss calls
    echo "## pg_stat_statements top 20 by total_exec_time"; pgss total_exec_time
  else
    echo "pg_stat_statements unavailable"
  fi
} | tee -a "$DIR/cluster.txt"

bash "$(dirname "$0")/census.sh" "$DIR" snapshot
