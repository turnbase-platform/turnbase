"""Runs one claude session while owning the keyboard and SIGINT/SIGTERM.

claude is started in its own session (no controlling terminal), so a Ctrl+C in the
terminal reaches only this process, which decides what it means: the first press
schedules a stop after the session, a second press within DOUBLE_PRESS_SECONDS
interrupts the session. claude writes straight to its log file; this process only
reads that file, so nothing it does can block or alter claude's output.
"""

from __future__ import annotations

import os
import selectors
import signal
import subprocess
import sys
import termios
import time
import tty
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Protocol

DOUBLE_PRESS_SECONDS = 3.0
TICK_SECONDS = 0.5


class Event(Enum):
    INT = "int"
    TERM = "term"
    ENTER = "enter"


class WaitResult(Enum):
    DONE = "done"
    STOP = "stop"
    TERM = "term"


class Outcome(Enum):
    EXITED = "exited"
    INTERRUPTED = "interrupted"
    TERMINATED = "terminated"


@dataclass(frozen=True)
class SessionResult:
    outcome: Outcome
    exit_code: int
    stop_scheduled: bool


class SessionView(Protocol):
    def on_lines(self, lines: list[str]) -> None: ...
    def on_tick(self) -> None: ...
    def on_stop_scheduled(self, scheduled: bool) -> None: ...
    def close(self) -> None: ...


def _ignore(signum, frame) -> None:
    """A Python-level handler is required for set_wakeup_fd to see the signal."""


class Controls:
    """Turns SIGINT, SIGTERM and the Enter key into events, for the loop's lifetime."""

    def __init__(self, stdin=None, clock: Callable[[], float] = time.monotonic) -> None:
        self.clock = clock
        self._stdin = stdin if stdin is not None else sys.stdin
        self._sel = selectors.DefaultSelector()
        self._key_fd: int | None = None
        self._saved_tty = None
        self._old_handlers: dict[int, object] = {}
        self._old_wakeup = -1

    def __enter__(self) -> Controls:
        self._r, self._w = os.pipe()
        os.set_blocking(self._r, False)
        os.set_blocking(self._w, False)
        self._old_wakeup = signal.set_wakeup_fd(self._w, warn_on_full_buffer=False)
        for sig in (signal.SIGINT, signal.SIGTERM):
            self._old_handlers[sig] = signal.signal(sig, _ignore)
        self._sel.register(self._r, selectors.EVENT_READ, "signal")
        fd = self._tty_fd()
        if fd is not None:
            self._saved_tty = termios.tcgetattr(fd)
            tty.setcbreak(fd)  # no echo, no line buffering; ISIG stays on so Ctrl+C still signals
            self._key_fd = fd
            self._sel.register(fd, selectors.EVENT_READ, "key")
        return self

    def __exit__(self, *exc) -> None:
        if self._saved_tty is not None and self._key_fd is not None:
            termios.tcsetattr(self._key_fd, termios.TCSADRAIN, self._saved_tty)
        signal.set_wakeup_fd(self._old_wakeup)
        for sig, handler in self._old_handlers.items():
            signal.signal(sig, handler)
        self._sel.close()
        os.close(self._r)
        os.close(self._w)

    def poll(self, timeout: float) -> list[Event]:
        events: list[Event] = []
        for key, _ in self._sel.select(timeout):
            if key.data == "signal":
                try:
                    data = os.read(self._r, 64)
                except BlockingIOError:
                    data = b""
                for signum in data:
                    if signum == signal.SIGINT:
                        events.append(Event.INT)
                    elif signum == signal.SIGTERM:
                        events.append(Event.TERM)
            else:
                try:
                    data = os.read(key.fd, 64)
                except OSError:
                    data = b""
                if not data:
                    self._sel.unregister(key.fd)
                elif b"\n" in data or b"\r" in data:
                    events.append(Event.ENTER)
        return events

    def wait(self, seconds: float, on_tick: Callable[[float], None]) -> WaitResult:
        """Waits `seconds`, calling on_tick(remaining) about twice a second."""
        deadline = self.clock() + seconds
        while True:
            remaining = deadline - self.clock()
            if remaining <= 0:
                return WaitResult.DONE
            on_tick(remaining)
            for event in self.poll(min(TICK_SECONDS, remaining)):
                if event is Event.INT:
                    return WaitResult.STOP
                if event is Event.TERM:
                    return WaitResult.TERM

    def _tty_fd(self) -> int | None:
        try:
            fd = self._stdin.fileno()
        except (AttributeError, ValueError, OSError):
            return None
        return fd if os.isatty(fd) else None


class LogFollower:
    """Returns complete lines appended to a file since the last call."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._file = None
        self._partial = b""

    def read_lines(self) -> list[str]:
        if self._file is None:
            try:
                self._file = open(self.path, "rb")
            except FileNotFoundError:
                return []
        chunk = self._file.read()
        if not chunk:
            return []
        *complete, self._partial = (self._partial + chunk).split(b"\n")
        return [c.decode("utf-8", "replace") for c in complete if c.strip()]

    def close(self) -> None:
        if self._file is not None:
            self._file.close()


class _Guarded:
    """Calls the view, and turns it off for good after its first exception."""

    def __init__(self, view: SessionView) -> None:
        self._view = view
        self.ok = True

    def __call__(self, method: str, *args) -> None:
        if not self.ok:
            return
        try:
            getattr(self._view, method)(*args)
        except Exception as exc:  # the display must never take the session down
            self.ok = False
            print(f"\nwarning: progress display disabled after an error: {exc!r}",
                  file=sys.stderr, flush=True)

    def stop_scheduled(self, scheduled: bool) -> None:
        self("on_stop_scheduled", scheduled)
        if not self.ok:
            text = ("Stop scheduled after this session — press Enter to cancel."
                    if scheduled else "Scheduled stop cancelled.")
            print(text, file=sys.stderr, flush=True)


def run_session(
    cmd: list[str],
    log_path: Path,
    *,
    controls,
    view: SessionView,
    cwd: Path | None = None,
    double_press_seconds: float = DOUBLE_PRESS_SECONDS,
    tick_seconds: float = TICK_SECONDS,
) -> SessionResult:
    with open(log_path, "wb") as log:
        proc = subprocess.Popen(cmd, stdout=log, stdin=subprocess.DEVNULL, cwd=cwd,
                                start_new_session=True)
    follower = LogFollower(Path(log_path))
    guarded = _Guarded(view)
    stop_scheduled = False
    last_int: float | None = None
    outcome = Outcome.EXITED
    try:
        while outcome is Outcome.EXITED:
            for event in controls.poll(tick_seconds):
                if event is Event.TERM:
                    proc.send_signal(signal.SIGTERM)
                    outcome = Outcome.TERMINATED
                    break
                if event is Event.INT:
                    now = controls.clock()
                    if stop_scheduled and last_int is not None and now - last_int < double_press_seconds:
                        proc.send_signal(signal.SIGINT)
                        outcome = Outcome.INTERRUPTED
                        break
                    last_int = now
                    if not stop_scheduled:
                        stop_scheduled = True
                        guarded.stop_scheduled(True)
                elif event is Event.ENTER and stop_scheduled:
                    stop_scheduled, last_int = False, None
                    guarded.stop_scheduled(False)
            lines = follower.read_lines()
            if lines:
                guarded("on_lines", lines)
            if outcome is Outcome.EXITED and proc.poll() is not None:
                break
            if outcome is Outcome.EXITED:
                guarded("on_tick")
        exit_code = proc.wait()
        lines = follower.read_lines()
        if lines:
            guarded("on_lines", lines)
    finally:
        follower.close()
        guarded("close")
    return SessionResult(outcome, exit_code, stop_scheduled)
