from __future__ import annotations

import argparse
import io
from pathlib import Path

import pandas as pd
import psycopg2

from packages.awa_common.dsn import build_dsn

COPY_SQL = "COPY returns_raw (asin, qty, fee_eur, processed_at) FROM STDIN CSV HEADER"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    args = parser.parse_args(argv)

    df = pd.read_csv(args.csv)
    df = df.rename(
        columns={
            "ASIN": "asin",
            "Qty": "qty",
            "Refund Amount": "fee_eur",
            "Return Date": "processed_at",
        }
    )
    buf = io.StringIO()
    df[["asin", "qty", "fee_eur", "processed_at"]].to_csv(buf, index=False)
    buf.seek(0)

    dsn = build_dsn(sync=True)
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE returns_raw")
        conn.execute(COPY_SQL, buf)
    return len(df)


if __name__ == "__main__":
    main()
