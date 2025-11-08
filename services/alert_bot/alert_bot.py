from __future__ import annotations

import structlog
from asgiref.sync import async_to_sync

from awa_common.logging import configure_logging

from .worker import evaluate_alert_rules, revalidate_telegram

configure_logging(service="alert_bot")
_logger = structlog.get_logger(__name__).bind(component="alert_bot")
_evaluate_sync = async_to_sync(evaluate_alert_rules)


def main() -> int:
    """Run a single alert evaluation cycle for manual invocations."""

    revalidate_telegram(force_log=True)
    result = _evaluate_sync()
    _logger.info("alerts.run.completed", result=result)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual utility
    raise SystemExit(main())
