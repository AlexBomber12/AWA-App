from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from typing import Any

import structlog

from awa_common.security.pii import _breadcrumb_scrubber, _pii_scrubber
from awa_common.settings import settings

logger = structlog.get_logger(__name__)
_INITIALISED = False


def before_send(event: Mapping[str, Any], hint: Mapping[str, Any] | None = None):
    sanitized = _pii_scrubber(event, hint or {})
    if sanitized is None:
        return None
    return dict(sanitized)


def before_breadcrumb(breadcrumb: Mapping[str, Any], hint: Mapping[str, Any] | None = None):
    sanitized = _breadcrumb_scrubber(breadcrumb, hint or {})
    if sanitized is None:
        return None
    return dict(sanitized)


def init_sentry(service: str) -> None:
    """
    Initialise Sentry with shared settings. Missing or invalid DSNs are logged but never raise.
    """

    global _INITIALISED
    dsn = (getattr(settings, "SENTRY_DSN", None) or "").strip()
    if not dsn:
        logger.warning("sentry.disabled", service=service)
        return
    if _INITIALISED:
        return

    try:
        import sentry_sdk
    except ImportError:  # pragma: no cover - optional dependency
        logger.warning("sentry.unavailable", reason="sdk_missing", service=service)
        return

    integrations: list[Any] = _load_integrations(
        [
            ("sentry_sdk.integrations.celery", "CeleryIntegration"),
            ("sentry_sdk.integrations.logging", "LoggingIntegration"),
            ("sentry_sdk.integrations.stdlib", "StdlibIntegration"),
            ("sentry_sdk.integrations.fastapi", "FastApiIntegration"),
            ("sentry_sdk.integrations.sqlalchemy", "SqlalchemyIntegration"),
        ]
    )
    for idx, integration in enumerate(integrations):
        if integration.__class__.__name__ == "LoggingIntegration":
            try:
                integration.level = None
                integration.event_level = None
            except Exception:
                integrations[idx] = integration

    env = getattr(settings, "ENV", "local")
    release = getattr(settings, "VERSION", None) or os.getenv("SENTRY_RELEASE") or os.getenv("COMMIT_SHA")
    traces_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.05"))
    profiles_rate = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.0"))

    BadDsnT: type[BaseException]
    try:
        from sentry_sdk.utils import BadDsn as _BadDsn  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover
        BadDsnT = Exception
    else:
        BadDsnT = _BadDsn

    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=env,
            release=release,
            send_default_pii=False,
            integrations=integrations,
            before_send=before_send,
            before_breadcrumb=before_breadcrumb,
            traces_sample_rate=traces_rate,
            profiles_sample_rate=profiles_rate,
        )
    except BadDsnT:
        logger.warning("sentry.invalid_dsn", exc_info=False)
        return
    except Exception:
        logger.warning("sentry.init_failed", exc_info=True)
        return

    _INITIALISED = True
    logger.info("sentry.initialised", service=service, env=env)


def _load_integrations(paths: Sequence[tuple[str, str]]) -> list[Any]:
    integrations: list[Any] = []
    for module_path, attr in paths:
        try:
            module = __import__(module_path, fromlist=[attr])
            factory = getattr(module, attr, None)
        except Exception:
            continue
        if factory is None:
            continue
        try:
            integrations.append(factory())
        except Exception:
            continue
    return integrations


__all__ = ["before_send", "before_breadcrumb", "init_sentry"]
