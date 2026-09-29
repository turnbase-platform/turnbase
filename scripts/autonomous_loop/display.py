"""Renders loop progress as terminal text.

Everything above `Terminal` is pure. A line is a list of `Segment`s — (text, SGR
parameters) — so it can be truncated to the terminal width before colour codes
are added.
"""

from __future__ import annotations

import os
import shutil
import sys
import time

from .progress import PhaseChange, Progress, idle

Segment = tuple[str, str]

RESET = "\x1b[0m"
BOLD, DIM = "1", "2"
RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN = "31", "32", "33", "34", "35", "36"
PHASE_COLORS = {
    "starting": DIM,
    "claiming": CYAN,
    "reading": CYAN,
    "implementing": BLUE,
    "testing": MAGENTA,
    "ci-wait": MAGENTA,
    "merging": GREEN,
    "wrapping-up": GREEN,
}
_SEP: Segment = (" · ", DIM)


def fmt_duration(seconds: float) -> str:
    s = max(0, int(seconds))
    if s < 60:
        return f"{s}s"
    m = s // 60
    if m < 60:
        return f"{m}m"
    return f"{m // 60}h{m % 60:02d}m"


def clock(ts: float) -> str:
    return time.strftime("%H:%M:%S", time.localtime(ts))


def render(segments: list[Segment], *, color: bool, width: int | None = None) -> str:
    out = []
    room = width
    for text, sgr in segments:
        if room is not None:
            if room <= 0:
                break
            if len(text) > room:
                text = text[: room - 1] + "…"
            room -= len(text)
        out.append(f"\x1b[{sgr}m{text}{RESET}" if color and sgr else text)
    return "".join(out)


def status_segments(
    p: Progress,
    *,
    iteration: int,
    max_iterations: int,
    now: float,
    stop_scheduled: bool,
    stall_seconds: float,
) -> list[Segment]:
    color = PHASE_COLORS.get(p.phase, DIM)
    label = p.phase + (" (resumed)" if p.resumed and p.phase == "starting" else "")
    segs: list[Segment] = [("● ", color), (f"iter {iteration}/{max_iterations}", "")]
    segs += [_SEP, (p.item, BOLD) if p.item else ("no item yet", DIM)]
    segs += [_SEP, (label, color)]
    if p.note:
        segs.append((f' ("{p.note}")', ""))
    segs += [_SEP, (f"{fmt_duration(now - p.phase_since)} in phase", "")]
    # Warnings go before "last:" so a narrow terminal truncates the least important part.
    quiet = idle(p, now, stall_seconds)
    if quiet is not None and quiet.kind == "stall":
        segs += [_SEP, (f"⚠ no activity {fmt_duration(quiet.seconds)}", f"{BOLD};{RED}")]
    elif quiet is not None:
        segs += [_SEP, (f"running {fmt_duration(quiet.seconds)}", MAGENTA)]
    if stop_scheduled:
        segs += [_SEP, ("⏹ stop after session — Enter to cancel", YELLOW)]
    if p.last_action is not None and p.last_action_at is not None:
        ago = fmt_duration(now - p.last_action_at)
        segs += [_SEP, (f"last: {p.last_action}, {ago} ago", DIM)]
    return segs


def phase_segments(change: PhaseChange) -> list[Segment]:
    segs: list[Segment] = [
        (f"  {clock(change.at)}  ", DIM),
        (change.phase.ljust(13), PHASE_COLORS.get(change.phase, DIM)),
    ]
    if change.note:
        segs.append((f" {change.note}", ""))
    elif not change.reported:
        segs.append((" (inferred)", DIM))
    return segs


def title_text(p: Progress) -> str:
    return f"{p.item or 'loop'} · {p.phase}"


class Terminal:
    """Permanent lines, one live bottom line (TTY only) and the window title."""

    def __init__(self, stream=None, *, tty: bool | None = None, color: bool | None = None,
                 width: int | None = None) -> None:
        self.stream = stream if stream is not None else sys.stdout
        self.tty = self.stream.isatty() if tty is None else tty
        env_ok = "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb"
        self.color = (self.tty and env_ok) if color is None else color
        self._width = width
        self._live: list[Segment] | None = None
        self._titled = False

    def print(self, line: str | list[Segment]) -> None:
        segs = [(line, "")] if isinstance(line, str) else line
        self._clear()
        self._write(render(segs, color=self.color) + "\n")
        if self._live is not None:
            self._draw()

    def live(self, segments: list[Segment]) -> None:
        if not self.tty:
            return
        self._live = segments
        self._draw()

    def clear_live(self) -> None:
        self._clear()
        self._live = None

    def title(self, text: str) -> None:
        if self.tty:
            self._write(f"\x1b]0;{text}\x07")
            self._titled = True

    def reset_title(self) -> None:
        if self._titled:
            self._write("\x1b]0;\x07")
            self._titled = False

    def bell(self) -> None:
        if self.tty:
            self._write("\a")

    def _width_now(self) -> int:
        return self._width or shutil.get_terminal_size((100, 24)).columns

    def _draw(self) -> None:
        # One column spare: writing into the last column makes some terminals wrap.
        text = render(self._live or [], color=self.color, width=self._width_now() - 1)
        self._write("\r\x1b[2K" + text)

    def _clear(self) -> None:
        if self.tty and self._live is not None:
            self._write("\r\x1b[2K")

    def _write(self, text: str) -> None:
        try:
            self.stream.write(text)
            self.stream.flush()
        except BrokenPipeError:
            pass
