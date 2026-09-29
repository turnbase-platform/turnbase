"""Turns claude's stream-json output into a live picture of one session.

Pure: no I/O and no clock. Callers pass each output line with the time it was read.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

PHASES = (
    "starting",
    "claiming",
    "reading",
    "implementing",
    "testing",
    "ci-wait",
    "merging",
    "wrapping-up",
)
NOTE_MAX = 80
# After this long without a marker, tool calls may move the phase again (shown as inferred).
STALE_MARKER_SECONDS = 600.0
SUMMARY_MAX = 60

_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_MARKER = re.compile(r"^LOOP_PHASE:[ \t]+(\S+)[ \t]*(.*?)[ \t]*$", re.MULTILINE)
# The same marker echoed inside a Bash command, e.g. `echo "LOOP_PHASE: testing verify"; ./mvnw …`.
_COMMAND_MARKER = re.compile(r"LOOP_PHASE:[ \t]+([a-z-]+)[ \t]*([^\"'`;&|\n]*)")
_ITEM = re.compile(r"\bIMP-[A-Z0-9]+-[0-9]+\b")
_CLAIM = re.compile(r"\bclaim\b[^\n]*?\b(IMP-[A-Z0-9]+-[0-9]+)\b")
_SUBMODULE = re.compile(r"/turnbase-(?:common|sdk|platform|game-host|frontend)/")
_GIT_MERGE = re.compile(r"\bgit\s+(?:merge|push)\b")
_TESTS = re.compile(r"mvnw|\bmvn\s|\bnpm\s+(?:run\s+)?test\b|\bvitest\b|\bpytest\b")
# A Bash command matching this may legitimately run for a long time without output.
LONG_WAIT = re.compile(r"gh run watch|mvnw|\bmvn\s|\bnpm\b|\bgradle")


@dataclass(frozen=True)
class PhaseChange:
    at: float
    phase: str
    note: str
    reported: bool  # True when the agent said so, False when inferred from a tool call


@dataclass(frozen=True)
class InFlight:
    command: str
    started_at: float


@dataclass(frozen=True)
class Idle:
    kind: str  # "stall" or "running"
    seconds: float


@dataclass
class Progress:
    started_at: float
    resumed: bool = False
    phase: str = "starting"
    note: str = ""
    phase_since: float = 0.0
    reported: bool = False
    marker_at: float | None = None
    item: str | None = None
    last_action: str | None = None
    last_action_at: float | None = None
    last_activity_at: float = 0.0
    in_flight: dict[str, InFlight] = field(default_factory=dict)

    @classmethod
    def start(cls, now: float, resumed: bool = False) -> Progress:
        return cls(started_at=now, resumed=resumed, phase_since=now, last_activity_at=now)


def apply(p: Progress, line: str, now: float) -> list[PhaseChange]:
    """Updates `p` from one stream-json line; returns the phase changes it caused."""
    try:
        event = json.loads(line)
    except ValueError:
        return []
    if not isinstance(event, dict) or event.get("type") not in ("assistant", "user"):
        return []
    kind = event["type"]
    p.last_activity_at = now
    message = event.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, list):
        return []
    changes: list[PhaseChange] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        btype = block.get("type")
        if kind == "assistant" and btype == "text" and isinstance(block.get("text"), str):
            changes += _markers(p, block["text"], now)
        elif kind == "assistant" and btype == "tool_use":
            changes += _tool_use(p, block, now)
        elif kind == "user" and btype == "tool_result":
            tid = block.get("tool_use_id")
            if isinstance(tid, str):
                p.in_flight.pop(tid, None)
    return changes


def infer_phase(name: str, inp: dict) -> str | None:
    path = inp.get("file_path") if isinstance(inp.get("file_path"), str) else ""
    command = inp.get("command") if isinstance(inp.get("command"), str) else ""
    if name == "Skill" and "work-item" in str(inp.get("skill", "")):
        return "claiming"
    if name in ("Edit", "Write") and os.path.basename(path) == "STATUS.md":
        return "wrapping-up"
    if name == "Bash":
        if "gh run watch" in command:
            return "ci-wait"
        if _GIT_MERGE.search(command):
            return "merging"
        if _TESTS.search(command):
            return "testing"
    if name in ("Edit", "Write") and _SUBMODULE.search(path):
        return "implementing"
    if name == "Read" and "/docs/" in path:
        return "reading"
    return None


def summarize(name: str, inp: dict) -> str:
    if name == "Bash":
        text = inp.get("description") or inp.get("command") or "Bash"
    elif isinstance(inp.get("file_path"), str):
        text = f"{name} {os.path.basename(inp['file_path'])}"
    elif name == "Skill" and inp.get("skill"):
        text = f"Skill {inp['skill']}"
    elif inp.get("description"):
        text = f"{name} {inp['description']}"
    else:
        text = name
    return _truncate(_printable(" ".join(str(text).split())), SUMMARY_MAX)


def idle(p: Progress, now: float, threshold: float) -> Idle | None:
    """None while the session is active; otherwise a stall, or a known long wait."""
    quiet = now - p.last_activity_at
    if quiet < threshold:
        return None
    waits = [f for f in p.in_flight.values() if LONG_WAIT.search(f.command)]
    if waits:
        return Idle("running", now - min(f.started_at for f in waits))
    return Idle("stall", quiet)


def _markers(p: Progress, text: str, now: float) -> list[PhaseChange]:
    return [c for m in _MARKER.finditer(text) for c in _marker(p, m.group(1), m.group(2), now)]


def _command_markers(p: Progress, command: str, now: float) -> list[PhaseChange]:
    """Agents sometimes echo the marker from a command instead of writing it as text.
    Only known phases count here, so a grep for the marker text is not taken for one."""
    return [c for m in _COMMAND_MARKER.finditer(command) if m.group(1) in PHASES
            for c in _marker(p, m.group(1), m.group(2), now)]


def _marker(p: Progress, phase: str, note: str, now: float) -> list[PhaseChange]:
    note = _truncate(_printable(note.strip()), NOTE_MAX)
    p.reported, p.marker_at = True, now
    item = _ITEM.search(note)
    if item:
        p.item = item.group(0)
    return _set_phase(p, _printable(phase), note, now, reported=True)


def _tool_use(p: Progress, block: dict, now: float) -> list[PhaseChange]:
    name = block.get("name") if isinstance(block.get("name"), str) else "?"
    inp = block.get("input") if isinstance(block.get("input"), dict) else {}
    command = inp.get("command") if name == "Bash" and isinstance(inp.get("command"), str) else ""
    if isinstance(block.get("id"), str):
        p.in_flight[block["id"]] = InFlight(command, now)
    p.last_action, p.last_action_at = summarize(name, inp), now
    if p.item is None and command:
        claim = _CLAIM.search(command)
        if claim:
            p.item = claim.group(1)
    if command:
        reported = _command_markers(p, command, now)
        if reported:
            return reported
    if p.reported and p.marker_at is not None and now - p.marker_at < STALE_MARKER_SECONDS:
        return []
    guess = infer_phase(name, inp)
    if guess is None or guess == p.phase:
        return []
    return _set_phase(p, guess, "", now, reported=False)


def _set_phase(p: Progress, phase: str, note: str, now: float, *, reported: bool) -> list[PhaseChange]:
    if phase == p.phase and note == p.note:
        return []
    if phase != p.phase:
        p.phase_since = now
    p.phase, p.note = phase, note
    return [PhaseChange(now, phase, note, reported)]


def _printable(text: str) -> str:
    """Agent text is drawn on the terminal: no escape sequences, bells or tabs."""
    return _CONTROL.sub(" ", text)


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"
