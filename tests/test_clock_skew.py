from services.api.routes import health


def test_skew_threshold() -> None:
    assert health.MAX_SKEW == 30
