from __future__ import annotations

import os

import sentry_sdk
import structlog
from awa_common.security.pii import _breadcrumb_scrubber, _pii_scrubber
from awa_common.settings import settings
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

before_send = _pii_scrubber
before_breadcrumb = _breadcrumb_scrubber


def init_sentry_if_configured() -> None:
    dsn = (settings.SENTRY_DSN or "").strip()
    if not dsn:
        return  # disabled
    env = settings.ENV
    release = os.getenv("SENTRY_RELEASE") or os.getenv("COMMIT_SHA")
    traces_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.05"))
    profiles_rate = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.0"))
    BadDsnT: type[BaseException]
    try:
        from sentry_sdk.utils import BadDsn as _BadDsn
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
            before_send=before_send,
            before_breadcrumb=before_breadcrumb,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                CeleryIntegration(),
                LoggingIntegration(
                    level=None, event_level=None
                ),  # breadcrumbs only; no log->event promotion
            ],
            traces_sample_rate=traces_rate,
            profiles_sample_rate=profiles_rate,
        )
    except BadDsnT:
        structlog.get_logger(__name__).warning("Ignoring invalid SENTRY_DSN", exc_info=False)
    except Exception:
        structlog.get_logger(__name__).debug(
            "Sentry init failed – continuing without telemetry", exc_info=True
        )
