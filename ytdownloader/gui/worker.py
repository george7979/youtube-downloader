"""Thread → UI bridge: background work whose callbacks run on the Tk main loop."""

from __future__ import annotations

import queue
import sys
import threading
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class UiQueue:
    def __init__(self, root, interval_ms: int = 80):
        self._root = root
        self._interval_ms = interval_ms
        self._queue: queue.SimpleQueue[Callable[[], None]] = queue.SimpleQueue()
        self._after_id: str | None = None
        self._closed = False
        self._schedule()

    def post(self, fn: Callable[[], None]) -> None:
        """Thread-safe; `fn` runs on the Tk main loop at the next tick."""
        self._queue.put(fn)

    def run_bg(
        self,
        work: Callable[[], T],
        on_ok: Callable[[T], None],
        on_err: Callable[[Exception], None],
    ) -> None:
        def target() -> None:
            try:
                result = work()
            except Exception as exc:  # noqa: BLE001 - every failure goes to on_err
                self.post(lambda err=exc: on_err(err))  # `exc` is unbound after except
            else:
                self.post(lambda: on_ok(result))

        threading.Thread(target=target, daemon=True).start()

    def close(self) -> None:
        self._closed = True
        if self._after_id is not None:
            try:
                self._root.after_cancel(self._after_id)
            except Exception:  # noqa: BLE001 - root may already be gone
                pass
            self._after_id = None

    def _schedule(self) -> None:
        if not self._closed:
            self._after_id = self._root.after(self._interval_ms, self._drain)

    def _drain(self) -> None:
        try:
            while True:
                try:
                    fn = self._queue.get_nowait()
                except queue.Empty:
                    break
                try:
                    fn()
                except Exception:  # noqa: BLE001 - report, keep the loop alive
                    self._root.report_callback_exception(*sys.exc_info())
        finally:
            self._schedule()
