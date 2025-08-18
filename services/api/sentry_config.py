from __future__ import annotations

import os

import sentry_sdk
from asgi_correlation_id import correlation_id
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

_SCRUB_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key"}
_SCRUB_FIELDS = {
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


def _scrub_mapping(d: dict | None) -> dict | None:
    if not isinstance(d, dict):
        return d
    red = {}
    for k, v in d.items():
        key = str(k).lower()
        if key in _SCRUB_FIELDS or key in _SCRUB_HEADERS:
            red[k] = "[redacted]"
        elif isinstance(v, dict):
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


def before_send(event, hint):
    # attach request_id tag
    rid = correlation_id.get()
    if rid:
        event.setdefault("tags", {})["request_id"] = rid
    # scrub request headers/body
    req = event.get("request") or {}
    headers = req.get("headers")
    if isinstance(headers, dict):
        req["headers"] = {
            k: ("[redacted]" if str(k).lower() in _SCRUB_HEADERS else v)
            for k, v in headers.items()
        }
    data = req.get("data")
    if isinstance(data, dict):
        req["data"] = _scrub_mapping(data)
    event["request"] = req
    # scrub extra/context/user
    if "extra" in event and isinstance(event["extra"], dict):
        event["extra"] = _scrub_mapping(event["extra"])
    if "contexts" in event and isinstance(event["contexts"], dict):
        event["contexts"] = _scrub_mapping(event["contexts"])
    if "user" in event and isinstance(event["user"], dict):
        event["user"] = _scrub_mapping(event["user"])
    return event


def init_sentry_if_configured():
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return  # disabled
    env = os.getenv("SENTRY_ENV", "local")
    release = os.getenv("SENTRY_RELEASE") or os.getenv("COMMIT_SHA")
    traces_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.05"))
    profiles_rate = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.0"))
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
