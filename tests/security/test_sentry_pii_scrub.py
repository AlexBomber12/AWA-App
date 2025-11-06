from __future__ import annotations

from copy import deepcopy

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
