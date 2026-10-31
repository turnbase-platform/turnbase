#!/usr/bin/env bash
# The scaling timeline (IMP-M18-14, load-testing-phase-b.md §6): samples the replica counts of every Deployment, the
# HPAs' desired and current replicas and the platform / Game Host pods every 5 s, until <run-dir>/exit-code exists.
# Usage: loadtest/timeline.sh <run-dir>      (started by run.sh)
# Writes <run-dir>/timeline.csv with the header `epoch,kind,name,a,b`:
#   deploy,<name>,<desired>,<ready>        every tick
#   hpa,<name>,<desired>,<current>         every tick (the KEDA ScaledObject's HPA is in this list)
#   pod,<name>,<state>,<startTime>         when a pod appears or its state changes; state is
#                                          Pending|Running|Ready|Terminating (a deletionTimestamp is set)
#   mark,<label>,<detail>,                 written by failover-driver.sh (the kills), at the moment they happen
set -uo pipefail
DIR="${1:?usage: timeline.sh <run-dir>}"
OUT="$DIR/timeline.csv"
PREV="$(mktemp)"
trap 'rm -f "$PREV"' EXIT
echo "epoch,kind,name,a,b" > "$OUT"
while [ ! -e "$DIR/exit-code" ]; do
  now="$(date +%s)"
  kubectl get deploy -o json 2>/dev/null | jq -r --arg e "$now" \
    '.items[] | select(.metadata.name | test("platform|gamehost")) | [$e, "deploy", .metadata.name, (.spec.replicas // 0), (.status.readyReplicas // 0)] | join(",")' >> "$OUT"
  kubectl get hpa -o json 2>/dev/null | jq -r --arg e "$now" \
    '.items[] | [$e, "hpa", .metadata.name, (.status.desiredReplicas // 0), (.status.currentReplicas // 0)] | join(",")' >> "$OUT"
  kubectl get pods -o json 2>/dev/null | jq -r \
    '.items[] | select(.metadata.labels["app.kubernetes.io/name"] | IN("platform", "gamehost")) |
      [.metadata.name,
       (if .metadata.deletionTimestamp then "Terminating"
        elif .status.phase != "Running" then (.status.phase // "Pending")
        elif ([.status.conditions[]? | select(.type == "Ready" and .status == "True")] | length) > 0 then "Ready"
        else "Running" end),
       (.status.startTime // "")] | join(",")' | sort > "$PREV.new"
  comm -13 "$PREV" "$PREV.new" | awk -F, -v e="$now" '{print e ",pod," $1 "," $2 "," $3}' >> "$OUT"
  mv "$PREV.new" "$PREV"
  sleep 5
done
