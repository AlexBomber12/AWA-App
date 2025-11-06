from __future__ import annotations

from copy import deepcopy
from typing import Any

from asgi_correlation_id import correlation_id

from awa_common.security.pii import _breadcrumb_scrubber, _pii_scrubber


def test_pii_scrubber_masks_headers_and_payload():
    original_event = {
        "message": "Contact user@example.com or 555-123-4567",
        "request": {
            "headers": {
                "Authorization": "Bearer SECRET",
                "Cookie": "a=b",
                "X-Request-ID": "req-123",
            },
            "data": {
                "email": "user@example.com",
                "notes": "Call me at 555-999-0000",
                "keep": "safe",
            },
        },
        "extra": {"phone": "555-000-1111", "keep": "safe"},
        "user": {"email": "user@example.com", "id": "42"},
    }
    event = deepcopy(original_event)
    scrubbed = _pii_scrubber(event, None)
    assert scrubbed is not event
    assert scrubbed["tags"]["request_id"] == "req-123"
    headers = scrubbed["request"]["headers"]
    assert headers["Authorization"] == "***"
    assert headers["Cookie"] == "***"
    assert headers["X-Request-ID"] == "req-123"
    data = scrubbed["request"]["data"]
    assert data["email"] == "***"
    assert data["notes"].count("***") >= 1
    assert data["keep"] == "safe"
    assert scrubbed["extra"]["phone"] == "***"
    assert scrubbed["extra"]["keep"] == "safe"
    assert scrubbed["user"]["email"] == "***"
    assert "user@example.com" in original_event["message"]
    assert "***" in scrubbed["message"]


def test_breadcrumb_scrubber_masks_sensitive_strings():
    crumb = {
        "message": "Dial 555-765-4321 for support",
        "data": {"email": "agent@example.com", "status": "ok"},
    }
    scrubbed = _breadcrumb_scrubber(crumb, None)
    assert scrubbed["message"] == "Dial *** for support"
    assert scrubbed["data"]["email"] == "***"
    assert scrubbed["data"]["status"] == "ok"


def test_pii_scrubber_handles_headers_lists_and_bytes():
    event = {
        "message": "Email qa@example.com",
        "request": {
            "headers": [
                ("Authorization", "secret"),
                ("X-Api-Key", "key"),
                ("X-Request-ID", "req-456"),
            ],
            "data": {
                "payload": [b"abc@example.com", "  keep  "],
                "nested": {"token": "tok"},
            },
            "query_string": {"phone": "555-444-3333"},
        },
        "logentry": {"message": "Contact 555-101-2020"},
        "contexts": {"session": {"email": "nested@example.com"}},
    }
    token = correlation_id.set("corr-789")
    try:
        scrubbed = _pii_scrubber(event, None)
    finally:
        correlation_id.reset(token)
    headers = dict(scrubbed["request"]["headers"])
    assert headers["Authorization"] == "***"
    assert headers["X-Api-Key"] == "***"
    assert headers["X-Request-ID"] == "req-456"
    data = scrubbed["request"]["data"]
    assert data["payload"][0] == "***"
    assert data["payload"][1] == "  keep  "
    assert data["nested"]["token"] == "***"
    assert scrubbed["request"]["query_string"]["phone"] == "***"
    assert scrubbed["logentry"]["message"] == "Contact ***"
    assert scrubbed["contexts"]["session"]["email"] == "***"
    assert scrubbed["tags"]["request_id"] == "req-456"


class BadBytes(bytes):
    def decode(self, *args: Any, **kwargs: Any) -> str:  # type: ignore[override]
        raise UnicodeError("boom")


def test_pii_scrubber_handles_tuple_and_bad_bytes():
    event = {
        "request": {
            "headers": 123,
            "data": {
                "tuple": ("user@example.com",),
                "bytes": BadBytes(b"binary"),
                "count": 5,
            },
        },
        "message": "Call 555-222-3333",
        "extra": [{"email": "list@example.com"}],
    }
    scrubbed = _pii_scrubber(event, None)
    data = scrubbed["request"]["data"]
    assert data["tuple"][0] == "***"
    assert data["bytes"] == "***"
    assert data["count"] == 5
    assert scrubbed["request"]["headers"] == 123
    assert scrubbed["message"] == "Call ***"
    assert scrubbed["extra"][0]["email"] == "***"


def test_pii_scrubber_uses_correlation_id_when_header_missing():
    token = correlation_id.set("corr-xyz")
    try:
        event = {"request": {"headers": {}}, "message": "hello"}
        scrubbed = _pii_scrubber(event, None)
        assert scrubbed["tags"]["request_id"] == "corr-xyz"
    finally:
        correlation_id.reset(token)
