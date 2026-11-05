#!/usr/bin/env bash
# Test cost: totals per phase and the slowest classes/methods, read from existing reports.
# Does NOT run any build. Usage: scripts/test-cost.sh [--top N] [--methods] [REPO ...]   (default: all)
# Reports read: target/surefire-reports (unit), target/failsafe-reports (integration) — JUnit XML;
#   vitest JSON: test-results/vitest.json (frontend) or target/vitest.json (others), produced by
#   npx vitest run --reporter=json --outputFile=<that path>
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 -I - "$root" "$@" <<'PY'
import sys, os, json, glob
import xml.etree.ElementTree as ET
root, args = sys.argv[1], sys.argv[2:]
top, methods, repos = 10, False, []
i = 0
while i < len(args):
    a = args[i]
    if a == "--top": top = int(args[i+1]); i += 1
    elif a == "--methods": methods = True
    elif a in ("-h", "--help"): print(__doc__ if __doc__ else open(root+"/scripts/test-cost.sh").read().split("\n",1)[1].split("set -")[0]); sys.exit(0)
    else: repos.append(a.rstrip("/"))
    i += 1
if not repos:
    repos = sorted(d for d in os.listdir(root) if d.startswith("turnbase-") and os.path.isdir(os.path.join(root, d)))

def junit(d):
    classes, meths = {}, []
    for f in glob.glob(os.path.join(d, "TEST-*.xml")):
        for tc in ET.parse(f).getroot().iter("testcase"):
            t = float(tc.get("time") or 0); c = tc.get("classname") or "?"
            classes.setdefault(c, [0, 0.0]); classes[c][0] += 1; classes[c][1] += t
            meths.append((t, c + "#" + (tc.get("name") or "?")))
    return classes, meths

def vitest(p):
    classes, meths = {}, []
    for tf in json.load(open(p)).get("testResults", []):
        name = os.path.relpath(tf["name"], os.path.dirname(os.path.dirname(p))) if os.path.isabs(tf["name"]) else tf["name"]
        for a in tf.get("assertionResults", []):
            t = (a.get("duration") or 0) / 1000
            classes.setdefault(name, [0, 0.0]); classes[name][0] += 1; classes[name][1] += t
            meths.append((t, name + "#" + (a.get("title") or "?")))
        # file wall time (setup/import) is not in per-test durations
        w = (tf.get("endTime", 0) - tf.get("startTime", 0)) / 1000
        classes.setdefault(name, [0, 0.0]); classes[name].append(w)
    return classes, meths

bad = 0
for r in repos:
    d = os.path.join(root, r)
    phases = []
    for label, sub in (("unit", "surefire-reports"), ("integration", "failsafe-reports")):
        p = os.path.join(d, "target", sub)
        if glob.glob(os.path.join(p, "TEST-*.xml")): phases.append((label, junit(p)))
    for p in (os.path.join(d, "test-results", "vitest.json"), os.path.join(d, "target", "vitest.json")):
        if os.path.isfile(p): phases.append(("vitest", vitest(p))); break
    print(f"== {r}")
    if not phases:
        print(f"   NO REPORTS: none of target/surefire-reports, target/failsafe-reports, test-results/vitest.json, target/vitest.json under {r}", file=sys.stderr)
        print("   NO REPORTS (run the build first; this script never runs one)"); bad += 1; continue
    print(f"   {'phase':<12}{'classes':>8}{'tests':>7}{'seconds':>10}")
    for label, (cl, me) in phases:
        print(f"   {label:<12}{len(cl):>8}{sum(v[0] for v in cl.values()):>7}{sum(v[1] for v in cl.values()):>10.1f}")
    for label, (cl, me) in phases:
        print(f"   -- slowest classes [{label}] (sum of test times)")
        for n, v in sorted(cl.items(), key=lambda kv: -kv[1][1])[:top]:
            print(f"   {v[1]:>9.2f}s {v[0]:>4}  {n}")
        if methods:
            print(f"   -- slowest methods [{label}]")
            for t, n in sorted(me, reverse=True)[:top]: print(f"   {t:>9.2f}s       {n}")
sys.exit(1 if bad else 0)
PY
