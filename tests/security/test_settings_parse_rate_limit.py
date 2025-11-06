from __future__ import annotations

import pytest

from packages.awa_common.settings import parse_rate_limit


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("10/second", (10, 1)),
        ("30 / MIN", (30, 60)),
        ("5/ m", (5, 60)),
        ("7/sec", (7, 1)),
    ],
)
def test_parse_rate_limit_accepts_valid_formats(value: str, expected: tuple[int, int]) -> None:
    assert parse_rate_limit(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        "abc",
        "10/hour",
        "0/min",
        "-5/min",
        "5",
    ],
)
def test_parse_rate_limit_rejects_invalid_inputs(value: str) -> None:
    with pytest.raises(ValueError):
        parse_rate_limit(value)
