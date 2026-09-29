"""Stand-in for the claude CLI in loop tests.

FAKE_CLAUDE_DIR holds one scenario per invocation (0.json, 1.json, ...), a call
counter, calls.jsonl (argv of each call) and signals.log (signals received).
Scenario keys, all optional:
  events: list of stream-json objects to emit      delay: seconds between events
  replay_file: path of a real .jsonl log to emit    hold: seconds to sleep before the result
  status: LOOP_STATUS payload, e.g. "DONE IMP-X-01" result: literal result text (overrides status)
  is_error, api_error_status: copied into the result event
  exit: process exit code                           touch / remove: paths to create / delete
  stderr: text written to stderr at the end
  resets_at: epoch written to the transcript in FAKE_CLAUDE_TRANSCRIPT_DIR
"""

import json
import os
import signal
import sys
import time
from pathlib import Path

d = Path(os.environ["FAKE_CLAUDE_DIR"])
counter = d / "count"
n = int(counter.read_text()) if counter.exists() else 0
counter.write_text(str(n + 1))
scenario_file = d / f"{n}.json"
scenario = json.loads(scenario_file.read_text()) if scenario_file.exists() else {"status": "DONE fake"}

argv = sys.argv[1:]
with (d / "calls.jsonl").open("a") as f:
    f.write(json.dumps({"argv": argv}) + "\n")


def on_signal(signum, _frame):
    with (d / "signals.log").open("a") as f:
        f.write(f"{n} {signal.Signals(signum).name}\n")
    sys.exit(128 + signum)


signal.signal(signal.SIGINT, on_signal)
signal.signal(signal.SIGTERM, on_signal)


def emit(raw):
    sys.stdout.write(raw.rstrip("\n") + "\n")
    sys.stdout.flush()


emit(json.dumps({"type": "system", "subtype": "init", "session_id": "fake"}))
for obj in scenario.get("events", []):
    emit(json.dumps(obj))
    time.sleep(scenario.get("delay", 0.0))
if "replay_file" in scenario:
    for raw in open(scenario["replay_file"], encoding="utf-8"):
        if '"type":"result"' not in raw:
            emit(raw)
            time.sleep(scenario.get("delay", 0.0))
time.sleep(scenario.get("hold", 0.0))

for path in scenario.get("touch", []):
    Path(path).write_text("dirty\n")
for path in scenario.get("remove", []):
    Path(path).unlink(missing_ok=True)

if "resets_at" in scenario:
    sid = argv[argv.index("--session-id" if "--session-id" in argv else "--resume") + 1]
    tdir = Path(os.environ["FAKE_CLAUDE_TRANSCRIPT_DIR"])
    tdir.mkdir(parents=True, exist_ok=True)
    (tdir / f"{sid}.jsonl").write_text('{"error":{"resetsAt":%d}}\n' % scenario["resets_at"])

if "result" in scenario:
    text = scenario["result"]
elif scenario.get("status"):
    text = f"work done\nLOOP_STATUS: {scenario['status']}"
else:
    text = "work done"
result = {"type": "result", "subtype": "success", "is_error": scenario.get("is_error", False),
          "result": text}
if "api_error_status" in scenario:
    result["api_error_status"] = scenario["api_error_status"]
emit(json.dumps(result))
if "stderr" in scenario:
    sys.stderr.write(scenario["stderr"] + "\n")
sys.exit(scenario.get("exit", 0))
