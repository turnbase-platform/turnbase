"""SessionDisplay: the SessionView that draws progress on the terminal."""

from __future__ import annotations

import time
from typing import Callable

from .display import DIM, YELLOW, Terminal, clock, phase_segments, status_segments, title_text
from .progress import Progress, apply


class SessionDisplay:
    def __init__(self, terminal: Terminal, *, iteration: int, max_iterations: int, resumed: bool,
                 stall_seconds: float, clock: Callable[[], float] = time.time) -> None:
        self._t = terminal
        self._iteration = iteration
        self._max = max_iterations
        self._stall = stall_seconds
        self._clock = clock
        self._stop = False
        self._title: str | None = None
        self.progress = Progress.start(clock(), resumed)

    def on_lines(self, lines: list[str]) -> None:
        now = self._clock()
        for line in lines:
            for change in apply(self.progress, line, now):
                self._t.print(phase_segments(change))
        self.on_tick()

    def on_tick(self) -> None:
        self._t.live(status_segments(self.progress, iteration=self._iteration,
                                     max_iterations=self._max, now=self._clock(),
                                     stop_scheduled=self._stop, stall_seconds=self._stall))
        title = title_text(self.progress)
        if title != self._title:
            self._t.title(title)
            self._title = title

    def on_stop_scheduled(self, scheduled: bool) -> None:
        self._stop = scheduled
        text = ("⏹ stop scheduled after this session — Enter to cancel" if scheduled
                else "▶ scheduled stop cancelled — the loop will continue")
        self._t.print([(f"  {clock(self._clock())}  ", DIM), (text, YELLOW)])
        self.on_tick()

    def close(self) -> None:
        self._t.clear_live()
        self._t.reset_title()
