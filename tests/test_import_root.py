import importlib

MODULES = [
    "db",
    "services.etl.helium_fees",
    "services.etl.keepa_ingestor",
    "services.etl.keepa_etl",
    "services.etl.sp_fees",
]


def test_import_canonical_modules() -> None:
    for mod in MODULES:
        importlib.import_module(mod)
