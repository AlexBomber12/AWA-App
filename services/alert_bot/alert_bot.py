from __future__ import annotations

import structlog
from asgiref.sync import async_to_sync

from awa_common.logging import configure_logging

from .worker import AlertConfigurationError, evaluate_alert_rules

configure_logging(service="alert_bot")
_logger = structlog.get_logger(__name__).bind(component="alert_bot")
_evaluate_sync = async_to_sync(evaluate_alert_rules)


def main() -> int:
    """Run a single alert evaluation cycle for manual invocations."""

    try:
        result = _evaluate_sync()
    except AlertConfigurationError as exc:
        _logger.error("alerts.run.invalid_config", error=str(exc))
        return 1
    _logger.info("alerts.run.completed", result=result)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual utility
    raise SystemExit(main())
