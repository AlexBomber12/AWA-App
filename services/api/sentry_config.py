from __future__ import annotations

import logging
import os
from typing import Any, Mapping

import sentry_sdk
from asgi_correlation_id import correlation_id
from awa_common.settings import settings
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.types import Event, Hint

_SCRUB_HEADERS: set[str] = {"authorization", "cookie", "set-cookie", "x-api-key"}
_SCRUB_FIELDS: set[str] = {
    "password",
    "pass",
    "pwd",
    "email",
    "phone",
    "token",
    "secret",
    "api_key",
    "apikey",
    "authorization",
}


def _is_truthy(v: str | None) -> bool:
    return (v or "").strip().lower() in {"1", "true", "yes", "y"}


def _scrub_mapping(d: Mapping[str, Any]) -> dict[str, Any]:
    red: dict[str, Any] = {}
    for k, v in d.items():
        key = str(k).lower()
        if key in _SCRUB_FIELDS or key in _SCRUB_HEADERS:
            red[k] = "[redacted]"
        elif isinstance(v, Mapping):
            red[k] = _scrub_mapping(v)
        elif isinstance(v, list):
            red[k] = [
                (
                    "[redacted]"
                    if isinstance(x, (str, bytes)) and key in _SCRUB_FIELDS
                    else x
                )
                for x in v
            ]
        else:
            red[k] = v
    return red


def before_send(event: Event, _hint: Hint) -> Event | None:
    # attach request_id tag
    req: dict[str, Any] = event.get("request") or {}
    headers = req.get("headers")
    rid: str | None = None
    if isinstance(headers, Mapping):
        rid = headers.get("x-request-id")
    elif isinstance(headers, list):
        for k, v in headers:
            if str(k).lower() == "x-request-id":
                rid = v
                break
    if not rid:
        rid = correlation_id.get()
    if rid:
        event.setdefault("tags", {})["request_id"] = rid
    # scrub request headers/body
    if isinstance(headers, Mapping):
        req["headers"] = {
            k: ("[redacted]" if str(k).lower() in _SCRUB_HEADERS else v)
            for k, v in headers.items()
        }
    elif isinstance(headers, list):
        req["headers"] = [
            (k, "[redacted]" if str(k).lower() in _SCRUB_HEADERS else v)
            for k, v in headers
        ]
    data = req.get("data")
    if isinstance(data, Mapping):
        req["data"] = _scrub_mapping(data)
    event["request"] = req
    # scrub extra/context/user
    if "extra" in event and isinstance(event["extra"], Mapping):
        event["extra"] = _scrub_mapping(event["extra"])
    if "contexts" in event and isinstance(event["contexts"], Mapping):
        event["contexts"] = _scrub_mapping(event["contexts"])
    if "user" in event and isinstance(event["user"], Mapping):
        event["user"] = _scrub_mapping(event["user"])
    return event


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
        logging.getLogger(__name__).warning(
            "Ignoring invalid SENTRY_DSN", exc_info=False
        )
    except Exception:
        logging.getLogger(__name__).debug(
            "Sentry init failed – continuing without telemetry", exc_info=True
        )
