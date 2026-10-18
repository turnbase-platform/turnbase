#!/usr/bin/env bash
# Installs or upgrades the `turnbase` Helm release with the load-test overlay on Docker Desktop.
# Usage: loadtest/install.sh [--default-limits]
#   --default-limits  last overlay is values-default-limits.yaml (the default-limits scenario; limiters on)
# Env: SEED_HOST_PATH  directory in the Kubernetes node holding <gameId>.zip. Under WSL 2 that is the
#                      /run/desktop/mnt/host/c/... form of a Windows directory; when unset the bundle is
#                      copied to C:\Users\<you>\turnbase-seed and that path is used.
# Generates a git-ignored values-local.secrets.yaml with random dummy values when it is missing.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CHART="$ROOT/turnbase-platform/deploy/helm/turnbase"
SECRETS="$CHART/values-local.secrets.yaml"
OVERLAY="$ROOT/loadtest/helm/values-loadtest.yaml"
[ "${1:-}" = "--default-limits" ] && OVERLAY="$ROOT/loadtest/helm/values-default-limits.yaml"

[ "$(kubectl config current-context)" = "docker-desktop" ] || { echo "refusing: context is not docker-desktop" >&2; exit 1; }

if [ ! -f "$SECRETS" ]; then
  ( umask 077
    r() { openssl rand -hex 16; }
    cat > "$SECRETS" <<YAML
postgres: { ownerPassword: "$(r)", appPassword: "$(r)" }
redis: { password: "$(r)" }
minio: { rootUser: "$(r)", rootPassword: "$(r)", appAccessKey: "$(r)", appSecretKey: "$(r)" }
auth:
  jwtKeySet: '{"active":{"kid":"k1","secret":"$(openssl rand -base64 32)","notBefore":"2020-01-01T00:00:00Z"},"retired":[]}'
admin: { username: "admin", password: "$(r)" }
oauth: { google: { clientId: "", clientSecret: "" } }
observability: { grafana: { adminPassword: "$(r)" } }
YAML
  )
  echo "generated dummy secrets (git-ignored)"
fi

if [ -z "${SEED_HOST_PATH:-}" ]; then
  WINUSER="$(cmd.exe /c 'echo %USERNAME%' 2>/dev/null | tr -d '\r' || true)"
  [ -n "$WINUSER" ] || { echo "set SEED_HOST_PATH (cannot find the Windows user)" >&2; exit 1; }
  SEED_SRC="$ROOT/turnbase-game-tictactoe/target/seed"
  ls "$SEED_SRC"/*.zip >/dev/null 2>&1 || { echo "no bundle in $SEED_SRC; build it (turnbase-game-tictactoe README)" >&2; exit 1; }
  mkdir -p "/mnt/c/Users/$WINUSER/turnbase-seed"
  cp "$SEED_SRC"/*.zip "/mnt/c/Users/$WINUSER/turnbase-seed/"
  SEED_HOST_PATH="/run/desktop/mnt/host/c/Users/$WINUSER/turnbase-seed"
fi

# Switching overlays changes the Deployments' pod templates. A rolling update needs a second 4-CPU platform pod
# next to the first, which the VM cannot schedule (Insufficient cpu: the upgrade then hangs until the timeout),
# so the application pods are removed first and the upgrade starts them again.
if helm status turnbase >/dev/null 2>&1; then
  kubectl scale deploy/turnbase-platform deploy/turnbase-gamehost --replicas=0
  for c in platform gamehost; do
    kubectl wait --for=delete pod -l "app.kubernetes.io/name=$c" --timeout=120s 2>/dev/null || true
  done
fi

helm upgrade --install turnbase "$CHART" \
  -f "$CHART/values-local.yaml" -f "$SECRETS" -f "$OVERLAY" \
  --set "platform.seed.bundlesHostPath=$SEED_HOST_PATH" \
  --wait --timeout 10m
# reset.sh owns restarts of a running install; this script has already removed the application pods.
