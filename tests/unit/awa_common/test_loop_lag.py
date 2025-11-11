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
