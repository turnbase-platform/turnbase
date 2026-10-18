#!/usr/bin/env bash
# Checks that the cluster, tools, images and install are ready for a load-test run.
# Usage: loadtest/preflight.sh [--cluster-only]     (env: BASE_URL, default http://turnbase.localhost)
# Runs every check, prints one `PREFLIGHT FAIL: <what>` line per failure, then `PREFLIGHT OK` (exit 0)
# or exits 1. --cluster-only skips the install checks (5 to 7), for use before the first install.
set -uo pipefail

BASE_URL="${BASE_URL:-http://turnbase.localhost}"
CLUSTER_ONLY=0
[ "${1:-}" = "--cluster-only" ] && CLUSTER_ONLY=1
failed=0
fail() { echo "PREFLIGHT FAIL: $*"; failed=1; }

ctx="$(kubectl config current-context 2>/dev/null || true)"
[ "$ctx" = "docker-desktop" ] || fail "kubectl context is '${ctx:-none}', expected docker-desktop"

ready="$(kubectl get nodes docker-desktop --no-headers 2>/dev/null | awk '{print $2}')"
[ "$ready" = "Ready" ] || fail "node docker-desktop is '${ready:-absent}', expected Ready (kubectl get nodes docker-desktop)"

helm version --short >/dev/null 2>&1 || fail "helm version"
k6 version >/dev/null 2>&1 || fail "k6 version"

for img in turnbase/platform:dev turnbase/game-host:dev turnbase/frontend:dev; do
  docker image inspect "$img" >/dev/null 2>&1 || fail "docker image $img is missing (docker build -t $img <component>)"
done

if [ "$CLUSTER_ONLY" = 1 ]; then
  echo "PREFLIGHT NOTE: --cluster-only, install checks (helm status, pods, URL) skipped"
else
  st="$(helm status turnbase -o json 2>/dev/null | jq -r '.info.status' 2>/dev/null || true)"
  [ "$st" = "deployed" ] || fail "helm release turnbase is '${st:-absent}', expected deployed"

  # READY column n/m with n<m, or a phase other than Running/Completed, is a failure.
  bad="$(kubectl get pods --no-headers 2>/dev/null | awk '{split($2,a,"/"); if ($3!="Completed" && ($3!="Running" || a[1]!=a[2])) print $1 " (" $2 " " $3 ")"}')"
  [ -z "$bad" ] || fail "pods not ready: $(echo "$bad" | tr '\n' ' ')"

  code="$(curl -s -o /dev/null -m 5 -w '%{http_code}' "$BASE_URL/api/games" 2>/dev/null || true)"
  { [ -n "$code" ] && [ "$code" != "000" ]; } || fail "no HTTP answer from $BASE_URL/api/games"
fi

[ "$failed" = 0 ] && { echo "PREFLIGHT OK"; exit 0; }
exit 1
