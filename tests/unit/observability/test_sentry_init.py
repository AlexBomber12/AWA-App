import sys
import types

import awa_common.sentry as sentry_module


def test_init_sentry_empty_dsn(monkeypatch):
    monkeypatch.setattr(sentry_module, "_INITIALISED", False)
    monkeypatch.setattr(sentry_module.settings, "SENTRY_DSN", "")
    sentry_module.init_sentry("api")


def test_init_sentry_handles_bad_dsn(monkeypatch):
    monkeypatch.setattr(sentry_module, "_INITIALISED", False)
    monkeypatch.setattr(sentry_module.settings, "SENTRY_DSN", "http://example.com")

    class BadDsn(Exception):
        pass

    def boom(**kwargs):
        raise BadDsn("invalid")

    fake_sdk = types.SimpleNamespace(
        init=boom,
        utils=types.SimpleNamespace(BadDsn=BadDsn),
    )
    monkeypatch.setitem(sys.modules, "sentry_sdk", fake_sdk)
    sentry_module.init_sentry("api")
