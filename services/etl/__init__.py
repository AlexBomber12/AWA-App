from typing import Protocol


class LoadCsvRunner(Protocol):
    @staticmethod
    def main(args: list[str]) -> tuple[int, int]: ...


class _LazyLoadCsv:
    @staticmethod
    def main(args: list[str]) -> tuple[int, int]:
        # Import on first use to avoid import-time side effects in container startup
        from etl import load_csv as _mod

        return _mod.main(args)


load_csv: LoadCsvRunner = _LazyLoadCsv()


__all__ = ["load_csv"]
