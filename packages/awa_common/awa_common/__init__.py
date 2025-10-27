import sys
from importlib import import_module
from pathlib import Path

__all__ = ["dsn"]

_pkg_root = Path(__file__).resolve().parents[1]
if str(_pkg_root) not in __path__:
    __path__.append(str(_pkg_root))
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

dsn = import_module("awa_common.dsn")
sys.modules[__name__ + ".dsn"] = dsn
