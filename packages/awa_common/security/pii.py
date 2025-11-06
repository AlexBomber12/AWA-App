from __future__ import annotations

import copy
import re
from typing import Any, Mapping, MutableMapping, Sequence, cast

from asgi_correlation_id import correlation_id

_PII_HEADERS = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-amz-security-token",
}

_PII_KEYS = {
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

_EMAIL_RE = re.compile(r"(?i)[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}")
_PHONE_RE = re.compile(r"(?x)\b(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b")


def _mask_string(value: str) -> str:
    masked = _EMAIL_RE.sub("***", value)
    masked = _PHONE_RE.sub("***", masked)
    return masked


def _scrub_value(value: Any, key_hint: str | None = None) -> Any:
    if isinstance(value, Mapping):
        return {k: _scrub_value(v, _normalize_key(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub_value(item, key_hint) for item in value]
    if isinstance(value, tuple):
        return tuple(_scrub_value(item, key_hint) for item in value)
    if isinstance(value, bytes):
        try:
            return _mask_string(value.decode("utf-8", errors="ignore"))
        except Exception:
            return "***"
    if isinstance(value, str):
        if key_hint and key_hint in _PII_KEYS:
            return "***"
        return _mask_string(value)
    return value


def _normalize_key(key: Any) -> str:
    return str(key).lower()


def _scrub_headers(headers: Any) -> Any:
    if isinstance(headers, Mapping):
        return {
            key: ("***" if _normalize_key(key) in _PII_HEADERS else _scrub_value(value))
            for key, value in headers.items()
        }
    if isinstance(headers, list):
        cleaned = []
        for key, value in headers:
            if _normalize_key(key) in _PII_HEADERS:
                cleaned.append((key, "***"))
            else:
                cleaned.append((key, _scrub_value(value)))
        return cleaned
    return headers


def _scrub_mapping_payload(payload: Any) -> Any:
    if isinstance(payload, Mapping):
        return {key: _scrub_value(value, _normalize_key(key)) for key, value in payload.items()}
    if isinstance(payload, list):
        return [_scrub_mapping_payload(item) for item in payload]
    if isinstance(payload, tuple):
        return tuple(_scrub_mapping_payload(item) for item in payload)
    if isinstance(payload, str):
        return _mask_string(payload)
    if isinstance(payload, bytes):
        try:
            return _mask_string(payload.decode("utf-8", errors="ignore"))
        except Exception:
            return "***"
    return payload


def _attach_request_id(event: MutableMapping[str, Any]) -> None:
    request = event.get("request") or {}
    headers = request.get("headers")
    rid: str | None = None
    if isinstance(headers, Mapping):
        for key, value in headers.items():
            if _normalize_key(key) == "x-request-id":
                rid = value
                break
    elif isinstance(headers, Sequence):
        for key, value in headers:
            if _normalize_key(key) == "x-request-id":
                rid = value
                break
    if not rid:
        rid = correlation_id.get()
    if rid:
        event.setdefault("tags", {})["request_id"] = rid


def _pii_scrubber(
    event: Mapping[str, Any], _hint: Any | None = None
) -> MutableMapping[str, Any] | None:
    event_copy = cast(MutableMapping[str, Any], copy.deepcopy(event))
    _attach_request_id(event_copy)
    request = event_copy.get("request")
    if isinstance(request, MutableMapping):
        headers = request.get("headers")
        if headers is not None:
            request["headers"] = _scrub_headers(headers)
        data = request.get("data")
        if data is not None:
            request["data"] = _scrub_mapping_payload(data)
        query = request.get("query_string")
        if query is not None:
            request["query_string"] = _scrub_mapping_payload(query)

    message = event_copy.get("message")
    if isinstance(message, str):
        event_copy["message"] = _mask_string(message)

    if "logentry" in event_copy and isinstance(event_copy["logentry"], MutableMapping):
        text = event_copy["logentry"].get("message")
        if isinstance(text, str):
            event_copy["logentry"]["message"] = _mask_string(text)

    for key in ("extra", "contexts", "user"):
        value = event_copy.get(key)
        if value is not None:
            event_copy[key] = _scrub_mapping_payload(value)

    return event_copy


def _breadcrumb_scrubber(
    breadcrumb: Mapping[str, Any], _hint: Any | None = None
) -> MutableMapping[str, Any] | None:
    crumb_copy = cast(MutableMapping[str, Any], copy.deepcopy(breadcrumb))
    message = crumb_copy.get("message")
    if isinstance(message, str):
        crumb_copy["message"] = _mask_string(message)
    data = crumb_copy.get("data")
    if data is not None:
        crumb_copy["data"] = _scrub_mapping_payload(data)
    return crumb_copy


__all__ = ["_pii_scrubber", "_breadcrumb_scrubber"]
