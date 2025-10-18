from __future__ import annotations

import importlib
import importlib.util
from typing import TYPE_CHECKING

__all__ = ["Base", "Vendor", "VendorPrice", "list_active_asins"]

_SQLALCHEMY_AVAILABLE = importlib.util.find_spec("sqlalchemy") is not None

if TYPE_CHECKING:
    from .base import Base
    from .keepa import list_active_asins
    from .models_vendor import Vendor, VendorPrice


def __getattr__(name: str):
    if name not in __all__:
        raise AttributeError(name)

    if not _SQLALCHEMY_AVAILABLE:
        raise ModuleNotFoundError(
            "sqlalchemy is required to access "
            f"'packages.awa_common.{name}'. Install the database extras to use "
            "these APIs."
        )

    module_map = {
        "Base": ".base",
        "Vendor": ".models_vendor",
        "VendorPrice": ".models_vendor",
        "list_active_asins": ".keepa",
    }
    module = importlib.import_module(module_map[name], __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(list(globals().keys()) + __all__)
