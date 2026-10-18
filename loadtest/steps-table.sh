#!/usr/bin/env bash
# Writes steps.csv next to a run's summary.json: one row per step-tagged metric.
# Usage: loadtest/steps-table.sh <summary.json>        (summary.json is k6 --summary-export output)
# Columns: segment,metric,count,p95,p99,rate,pass. Trends fill count, p95 and p99 (ms); tb_op_failed fills
# count (operations) and rate (share failed); counters fill count. `pass` is true when none of the metric's
# thresholds failed. The `warmup` window carries no thresholds and never appears. Sorted by step, numerically.
set -euo pipefail
SUM="${1:?usage: steps-table.sh <summary.json>}"
OUT="$(dirname "$SUM")/steps.csv"
{
  echo "segment,metric,count,p95,p99,rate,pass"
  jq -r '
    def r: if type == "number" then (. * 1000 | round / 1000) else . end;
    def ok: (.thresholds // {}) | [.[]] | any | not;      # exported value is true for a FAILED threshold
    .metrics | to_entries[]
    | select(.key | test("^tb_[a-z_]+\\{step:"))
    | (.key | capture("^(?<name>tb_[a-z_]+)\\{step:(?<step>[^,}]+)(?:,(?<rest>[^}]*))?\\}$")) as $k
    | .value as $v
    | [$k.step, ($k.name + (if $k.rest then "{" + $k.rest + "}" else "" end)),
       ($v.count // (($v.passes // 0) + ($v.fails // 0)) // ""),
       (($v["p(95)"] // "") | r), (($v["p(99)"] // "") | r),
       (if $v.fails != null then ($v.value | r) else "" end), ($v | ok)] | @tsv' "$SUM" \
  | sort -t$'\t' -k1,1V -k2,2 | tr '\t' ','
} > "$OUT"
cat "$OUT"
