#!/usr/bin/env bash
# Feeds check-generator.sh a synthetic samples file: segment 1 well under the limit, segment 2 over it.
set -euo pipefail
cd "$(dirname "$0")/.."
syn="$(mktemp)"; trap 'rm -f "$syn"' EXIT
printf '%s\n' '1000,100,10,1.0' '1005,100,10,1.0' '1010,100,10,1.0' '1065,330,50,6.0' '1070,340,50,6.0' '1075,335,50,6.0' > "$syn"
out="$(bash check-generator.sh "$syn" 1000 60 4 5)"
echo "$out"
echo "$out" | grep -q '^segment 1: k6 mean 100% of 320% -> ok$' || { echo "FAIL: segment 1" >&2; exit 1; }
echo "$out" | grep -q '^segment 2: k6 mean 335% of 320% -> generator-bound$' || { echo "FAIL: segment 2" >&2; exit 1; }
echo "check-generator selftest OK"
