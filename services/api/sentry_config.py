from awa_common.sentry import before_breadcrumb, before_send, init_sentry


def init_sentry_if_configured() -> None:
    init_sentry("api")


__all__ = ["before_send", "before_breadcrumb", "init_sentry_if_configured"]
