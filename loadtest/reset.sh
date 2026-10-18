#!/usr/bin/env bash
# Returns the stack to its just-installed state: empty Postgres schema, flushed Redis, fresh JVMs.
# Usage: loadtest/reset.sh      (no arguments; the Helm release `turnbase` must exist)
# Every service is scaled to zero before the stores are touched: a live Game Host would re-register its
# lease and a live platform would re-create rows. Prometheus is left running (its history is the
# evidence for earlier runs). Flyway recreates the tables when the platform starts; users must be
# re-provisioned afterwards (scenarios/provision.js).
set -euo pipefail

[ "$(kubectl config current-context)" = "docker-desktop" ] || { echo "refusing: context is not docker-desktop" >&2; exit 1; }

kubectl scale deploy/turnbase-frontend deploy/turnbase-platform deploy/turnbase-gamehost --replicas=0
for c in frontend platform gamehost; do
  kubectl wait --for=delete pod -l "app.kubernetes.io/name=$c" --timeout=120s 2>/dev/null || true
done

kubectl exec statefulset/turnbase-postgres -- psql -v ON_ERROR_STOP=1 -U turnbase_owner -d turnbase -c \
  "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT USAGE, CREATE ON SCHEMA public TO turnbase_app; CREATE EXTENSION IF NOT EXISTS pgcrypto; CREATE EXTENSION IF NOT EXISTS pg_trgm; CREATE EXTENSION IF NOT EXISTS btree_gin;"
kubectl exec statefulset/turnbase-redis -- sh -c 'redis-cli -a "$TURNBASE_REDIS_PASSWORD" FLUSHALL' 2>/dev/null

# Platform first (it runs Flyway and seeds). The Game Host boot wedges about one time in five and the
# supervisor restarts it, so allow two rounds.
kubectl scale deploy/turnbase-platform --replicas=1
kubectl rollout status deploy/turnbase-platform --timeout=300s
kubectl scale deploy/turnbase-gamehost --replicas=1
kubectl rollout status deploy/turnbase-gamehost --timeout=300s || kubectl rollout status deploy/turnbase-gamehost --timeout=300s
kubectl scale deploy/turnbase-frontend --replicas=1
kubectl rollout status deploy/turnbase-frontend --timeout=300s
echo "RESET OK"
