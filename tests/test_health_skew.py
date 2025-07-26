from services.api.routes import health


def test_health_allows_reasonable_skew() -> None:
    assert health.MAX_SKEW >= 60
