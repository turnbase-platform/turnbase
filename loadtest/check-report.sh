#!/usr/bin/env bash
# Checks that a load-test report is complete.
# Usage: loadtest/check-report.sh <report.md>
# Exits 1, listing the line numbers, while any line still contains the literal FILL or a required heading is
# missing; otherwise prints REPORT COMPLETE and exits 0. Run on TEMPLATE.md it must fail.
set -uo pipefail
R="${1:?usage: check-report.sh <report.md>}"
bad=0
fills="$(grep -n 'FILL' "$R" | cut -d: -f1 | tr '\n' ' ')"
if [ -n "$fills" ]; then echo "FILL left on lines: $fills"; bad=1; fi
for h in "Run" "Environment" "Thresholds" "Steps" "Result" "Server side" "Errors by code" "Findings" "Constants"; do
  grep -qE "^## [0-9]+\. $h\$" "$R" || { echo "missing heading: ## N. $h"; bad=1; }
done
for c in "single-node, laptop ceiling" "coordinated omission" "generator-bound" "SETTLE_SECONDS"; do
  grep -q "$c" "$R" || { echo "missing constant text: $c"; bad=1; }
done
grep -qE '^(Ceiling \(pairs\)|Ceiling \(games/s\)):' "$R" || { echo "missing Ceiling line"; bad=1; }
grep -q '^First to break:' "$R" || { echo "missing First to break line"; bad=1; }
[ "$bad" = 0 ] && { echo "REPORT COMPLETE"; exit 0; }
exit 1
