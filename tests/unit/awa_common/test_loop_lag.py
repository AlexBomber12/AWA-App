from __future__ import annotations

import asyncio
import time

from packages.awa_common.loop_lag import start_loop_lag_monitor


def test_loop_lag_monitor_start_stop() -> None:
    loop = asyncio.new_event_loop()
    try:
        stopper = start_loop_lag_monitor(loop, interval_s=0.01)
        time.sleep(0.05)
        stopper()
    finally:
        loop.close()


def test_loop_lag_monitor_handles_closed_loop() -> None:
    loop = asyncio.new_event_loop()
    stopper = start_loop_lag_monitor(loop, interval_s=0.01)
    loop.close()
    stopper()


def test_loop_lag_monitor_handles_runtime_error(monkeypatch):
    class DummyLoop:
        def __init__(self):
            self.closed = False

        def is_closed(self):
            return self.closed

        def call_soon_threadsafe(self, _cb):
            raise RuntimeError("boom")

    dummy = DummyLoop()
    stopper = start_loop_lag_monitor(dummy, interval_s=0.01)
    time.sleep(0.02)
    stopper()
