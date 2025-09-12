import importlib

MODULES = ["db", "helium_fees"]


def test_import_root_modules() -> None:
    for mod in MODULES:
        importlib.import_module(mod)
