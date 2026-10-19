#!/usr/bin/env bash
# Counts what the services hold at one moment: threads by name prefix for both JVMs, the Game Host's heap
# histogram, and the Redis keyspace and memory.
# Usage: loadtest/census.sh <run-dir> <label>      writes <run-dir>/census-<label>.txt (and prints it)
# Labels in use: `snapshot` (snapshot.sh), `before` / `peak` / `after` (IMP-M16-10, IMP-M16-15).
# The platform image has no jcmd and its JVM is PID 1, so its threads come from /proc alone. In the Game
# Host image PID 1 is supervise.sh and the JVM is its child: /tmp/jvm.pid when the supervisor wrote it
# (IMP-M16-02), else the process whose /proc/<pid>/comm is `java`; jcmd exists there (/usr/bin/jcmd).
# A section that cannot be collected prints `<section> unavailable: <reason>` and the script carries on.
set -uo pipefail
DIR="${1:?usage: census.sh <run-dir> <label>}"
LABEL="${2:?usage: census.sh <run-dir> <label>}"
OUT="$DIR/census-$LABEL.txt"
mkdir -p "$DIR"
: > "$OUT"

# section <title> <command...>: runs the command; on failure or empty output writes the `unavailable` line.
section() {
  local title="$1"; shift
  local body rc
  body="$("$@" 2>&1)"; rc=$?
  {
    echo "## $title"
    if [ "$rc" -ne 0 ] || [ -z "$body" ]; then
      echo "$title unavailable: ${body:-no output} (exit $rc)" | head -3
    else
      echo "$body"
    fi
    echo
  } >> "$OUT"
}

# Runs inside the pod: prints the JVM's pid.
FIND_JVM='pid=""; [ -s /tmp/jvm.pid ] && pid="$(cat /tmp/jvm.pid)"
if [ -z "$pid" ] || [ ! -d "/proc/$pid" ]; then
  for p in /proc/[0-9]*; do [ "$(cat "$p/comm" 2>/dev/null)" = java ] && pid="${p#/proc/}" && break; done
fi
[ -n "$pid" ] || { echo "no JVM process found" >&2; exit 1; }'

# Thread counts by name prefix (digits stripped), most numerous first, with the total.
THREADS='cat /proc/$pid/task/*/comm | sed "s/[0-9]*//g" | sort | uniq -c | sort -rn | awk "{ n += \$1; print } END { print n \" total\" }"'

threads() { # <deployment> <jvm pid expression: "1" or FIND_JVM>
  kubectl exec "deploy/$1" -- sh -c "${2}
echo \"jvm pid: \$pid\"
$THREADS"
}

redis() { # <redis-cli command words>
  kubectl exec statefulset/turnbase-redis -- sh -c "redis-cli -a \"\$TURNBASE_REDIS_PASSWORD\" $*" 2>/dev/null | tr -d '\r'
}

section "platform threads by name prefix" threads turnbase-platform 'pid=1'
section "game host threads by name prefix" threads turnbase-gamehost "$FIND_JVM"
section "game host class histogram (top 30)" \
  kubectl exec deploy/turnbase-gamehost -- sh -c "$FIND_JVM
jcmd \$pid GC.class_histogram 2>/dev/null | grep -E '^ *(num|[0-9]+:) ' | head -31"
section "redis DBSIZE" redis DBSIZE
section "redis INFO keyspace" redis INFO keyspace
section "redis used_memory" bash -c "$(declare -f redis); redis INFO memory | grep -E '^used_memory(_human)?:'"
section "redis commandstats (keys, scan)" bash -c "$(declare -f redis); redis INFO commandstats | grep -E '^cmdstat_(keys|scan):' || echo 'cmdstat_keys, cmdstat_scan: never called'"

cat "$OUT"
