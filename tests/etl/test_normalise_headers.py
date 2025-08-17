from __future__ import annotations

from services.etl.dialects import normalise_headers


def test_normalise_headers():
    assert normalise_headers([" Return Reason ", "Refund   Amount"]) == [
        "return reason",
        "refund amount",
    ]
