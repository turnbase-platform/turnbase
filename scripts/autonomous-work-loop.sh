#!/usr/bin/env bash
# Runs TurnBase work items back to back in non-interactive `claude` sessions.
# The loop itself lives in scripts/autonomous_loop/ (Python, stdlib only);
# this wrapper only puts it on the path. See --help for usage and controls.
set -euo pipefail
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$SCRIPTS_DIR${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m autonomous_loop "$@"
