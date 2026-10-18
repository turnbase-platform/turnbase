#!/usr/bin/env bash
# Asserts that values-default-limits.yaml differs from values-loadtest.yaml only by the `loadtest` profile
# entry and the Prometheus remote-write receiver, so the default-limits run changes nothing but the limiters.
set -euo pipefail
cd "$(dirname "$0")/../helm"
norm() { tr -d '\r' < "$1" | grep -vE '^[[:space:]]*(#|$)'; } # a Windows checkout may have CRLF
# values-loadtest.yaml without its two intended extras must equal values-default-limits.yaml.
expected="$(norm values-loadtest.yaml | grep -v 'SPRING_PROFILES_ACTIVE' | sed '/^observability:/,$d')"
actual="$(norm values-default-limits.yaml)"
if [ "$expected" != "$actual" ]; then
  echo "FAIL: the overlays differ beyond the profile and the remote-write receiver:" >&2
  diff <(echo "$expected") <(echo "$actual") >&2 || true
  exit 1
fi
grep -q 'SPRING_PROFILES_ACTIVE' values-default-limits.yaml && { echo "FAIL: default-limits still sets the profile" >&2; exit 1; }
grep -q 'remoteWriteReceiver' values-default-limits.yaml && { echo "FAIL: default-limits still enables remote write" >&2; exit 1; }
echo "overlays OK"
