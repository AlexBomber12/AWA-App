from importlib import import_module
import sys

__all__ = ["dsn"]

dsn = import_module("packages.awa_common.dsn")
sys.modules[__name__ + ".dsn"] = dsn
