#!/usr/bin/env bash
# Flags the steps where k6 itself was the bottleneck.
# Usage: loadtest/check-generator.sh <samples.csv> <start_epoch> <segment_seconds> <k6_cores> [settle_seconds=20]
# samples.csv rows are epoch,k6_cpu_pct,vm_cpu_pct,load1 (loadtest/sample-generator.sh). Prints one line per
# segment: `segment N: k6 mean X% of Y% -> generator-bound` or `-> ok`, where Y is 80% of the pinned cores
# (k6_cpu_pct is a share of ONE core, so 4 cores reach 400). The settle window at the start of each segment
# is ignored, as it is for the thresholds.
set -euo pipefail
[ $# -ge 4 ] || { echo "usage: $0 <samples.csv> <start_epoch> <segment_seconds> <k6_cores> [settle_seconds=20]" >&2; exit 2; }
awk -F, -v start="$2" -v seg="$3" -v cores="$4" -v settle="${5:-20}" '
  $1 >= start && $1 ~ /^[0-9]+$/ {
    off = $1 - start
    n = int(off / seg) + 1
    if (off - (n - 1) * seg < settle) next
    sum[n] += $2; cnt[n]++; if (n > last) last = n
  }
  END {
    limit = 0.8 * cores * 100
    for (i = 1; i <= last; i++) {
      if (!cnt[i]) continue
      mean = sum[i] / cnt[i]
      printf "segment %d: k6 mean %.0f%% of %.0f%% -> %s\n", i, mean, limit, (mean > limit ? "generator-bound" : "ok")
    }
  }' "$1"
