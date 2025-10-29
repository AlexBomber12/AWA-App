from __future__ import annotations

from collections.abc import Sequence

from services.etl import fba_fee_ingestor


def main(argv: Sequence[str] | None = None) -> int:
    return fba_fee_ingestor.main(argv)


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
