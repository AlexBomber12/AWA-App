import importlib

MODULES = [
    "services.etl.healthcheck",
    "services.etl.dialects.schemas",
    "services.fees_h10.client",
    "services.fees_h10.worker",
]


def test_import_canonical_modules() -> None:
    for mod in MODULES:
        importlib.import_module(mod)
