"""state.json: where the loop records the current session so a later start can resume it.

It lives outside the repo on purpose: the loop refuses to start on a dirty tree, so it
must not be the thing dirtying it. The fields match the original bash version.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path


class StateFile:
    def __init__(self, path: Path) -> None:
        self.path = path

    def write(self, session_id: str, iteration: int, status: str, **extra: str) -> None:
        doc = {
            "session_id": session_id,
            "iteration": iteration,
            "status": status,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            **extra,
        }
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps(doc, indent=2) + "\n")
        os.replace(tmp, self.path)

    def read(self) -> dict:
        try:
            doc = json.loads(self.path.read_text())
        except (OSError, ValueError):
            return {}
        return doc if isinstance(doc, dict) else {}
