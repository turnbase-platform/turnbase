"""Shared test doubles for the loop tests."""

import time

from autonomous_loop.session import WaitResult


class FakeControls:
    """Scripted stand-in for session.Controls.

    `events` maps a poll index to the events that poll returns. The fake clock
    advances by `clock_step` on every poll; `wait` returns at once and records
    the requested duration in `waits`.
    """

    def __init__(self, events=None, clock_step=0.0, wait_results=None):
        self._events = dict(events or {})
        self._polls = 0
        self._now = 0.0
        self._step = clock_step
        self._wait_results = list(wait_results or [])
        self.waits = []

    def clock(self):
        return self._now

    def poll(self, timeout):
        time.sleep(min(timeout, 0.02))
        events = self._events.pop(self._polls, [])
        self._polls += 1
        self._now += self._step
        return list(events)

    def wait(self, seconds, on_tick):
        self.waits.append(seconds)
        on_tick(seconds)
        return self._wait_results.pop(0) if self._wait_results else WaitResult.DONE


class RecordingView:
    def __init__(self, fail_on=None):
        self.fail_on = fail_on
        self.failed = False
        self.called_after_failure = False
        self.lines, self.stops, self.ticks, self.closed = [], [], 0, False

    def _hit(self, name):
        if self.failed:
            self.called_after_failure = True
        if name == self.fail_on:
            self.failed = True
            raise RuntimeError("boom")

    def on_lines(self, lines):
        self._hit("on_lines")
        self.lines += lines

    def on_tick(self):
        self._hit("on_tick")
        self.ticks += 1

    def on_stop_scheduled(self, scheduled):
        self._hit("on_stop_scheduled")
        self.stops.append(scheduled)

    def close(self):
        self._hit("close")
        self.closed = True
