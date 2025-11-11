from __future__ import annotations

import logging
import threading
import weakref
from collections.abc import Callable

logger = logging.getLogger(__name__)


def start_loop_lag_monitor(loop, interval_s: float = 1.0) -> Callable[[], None]:
    """Start a lightweight monitor that keeps the target loop active."""

    stop_event = threading.Event()
    loop_ref = weakref.ref(loop)

    def _thread_worker() -> None:
        while not stop_event.wait(max(interval_s, 0.1)):
            current_loop = loop_ref()
            if current_loop is None or current_loop.is_closed():
                break
            try:
                current_loop.call_soon_threadsafe(lambda: None)
            except RuntimeError:
                logger.debug("loop_lag_monitor.stop", exc_info=True)
                break
        stop_event.set()

    thread = threading.Thread(target=_thread_worker, name="loop-lag-monitor", daemon=True)
    thread.start()

    def _stop() -> None:
        stop_event.set()
        thread.join(timeout=1.0)

    return _stop


__all__ = ["start_loop_lag_monitor"]
