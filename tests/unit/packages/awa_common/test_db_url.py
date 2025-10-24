import awa_common.db_url as db_url


def test_build_url_defaults_to_async(monkeypatch):
    monkeypatch.setattr(
        db_url, "build_dsn", lambda *args, **kwargs: "postgresql+psycopg://dsn"
    )
    assert db_url.build_url() == "postgresql+psycopg://dsn"
    assert db_url.build_url(async_=False) == "postgresql+psycopg://dsn"
