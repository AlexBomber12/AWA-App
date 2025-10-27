import importlib

import awa_common.config as config


def test_config_reloads_with_expected_dsns(monkeypatch):
    from awa_common import dsn

    monkeypatch.setattr(dsn, "build_dsn", lambda **kwargs: "dsn-value")
    reloaded = importlib.reload(config)
    assert reloaded.ASYNC_DSN == "dsn-value"
    assert reloaded.SYNC_DSN == "dsn-value"
    importlib.reload(config)
