class _LazyLoadCsv:
    @staticmethod
    def main(args: list[str]):
        from . import fba_fee_ingestor as _mod

        return _mod.main() if not args else _mod.main()

load_csv = _LazyLoadCsv()

__all__ = ["load_csv"]
