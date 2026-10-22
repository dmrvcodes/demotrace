"""Which stage a job is in, how long each stage took, and which stage failed.

Stages can nest ("transcribe" runs inside "prepare"); durations are exclusive, so the parent's time
does not include the child's.
"""

import time
from collections.abc import Iterator
from contextlib import contextmanager


class StageTracker:
    def __init__(self) -> None:
        self.durations: dict[str, float] = {}
        self.failed: str | None = None  # the innermost stage that raised
        self._stack: list[tuple[str, float]] = []

    @property
    def current(self) -> str | None:
        return self._stack[-1][0] if self._stack else None

    def _close_top(self) -> None:
        name, started = self._stack[-1]
        self.durations[name] = round(self.durations.get(name, 0.0) + time.monotonic() - started, 2)

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        if self._stack:
            self._close_top()  # pause the parent
        self._stack.append((name, time.monotonic()))
        try:
            yield
        except BaseException:
            if self.failed is None:
                self.failed = name
            raise
        finally:
            self._close_top()
            self._stack.pop()
            if self._stack:  # resume the parent
                self._stack[-1] = (self._stack[-1][0], time.monotonic())


@contextmanager
def _untracked(name: str) -> Iterator[None]:
    yield


def stage_of(tracker: StageTracker | None):
    return tracker.stage if tracker is not None else _untracked
