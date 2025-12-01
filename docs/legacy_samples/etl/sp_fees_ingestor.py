from __future__ import annotations

from collections.abc import Sequence

from . import sp_fees


def main(argv: Sequence[str] | None = None) -> int:
    return sp_fees.main(argv)


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
