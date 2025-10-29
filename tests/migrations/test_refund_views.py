from __future__ import annotations

from datetime import date

import pytest
from alembic.config import CommandLine
from sqlalchemy import text


@pytest.mark.integration
def test_refund_views(db_engine) -> None:
    cli = CommandLine(prog="alembic")

    def run(*args: str) -> None:
        opts = cli.parser.parse_args(["-c", "services/api/alembic.ini", *args])
        cli.run_cmd(opts)

    run("upgrade", "head")

    with db_engine.begin() as conn:
        conn.execute(text("SELECT * FROM v_refunds_txn LIMIT 0"))
        conn.execute(text("SELECT * FROM v_refunds_summary LIMIT 0"))
        conn.execute(
            text(
                "INSERT INTO returns_raw (id, asin, qty, refund_amount, return_date) VALUES (1, 'A1', 1, 5.0, '2024-01-01')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO reimbursements_raw (id, asin, amount, reimb_date) VALUES (1, 'A1', 2.0, '2024-01-02')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO returns_raw (id, asin, qty, refund_amount, return_date) VALUES (2, 'A2', 1, 3.0, '2024-01-01')"
            )
        )

    with db_engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT asin, order_id, refund_amount::float, currency, refunded_at::date, source
                FROM v_refunds_txn
                ORDER BY asin, refunded_at
                """
            )
        ).fetchall()
        assert rows == [
            ("A1", None, 5.0, "USD", date(2024, 1, 1), "return"),
            ("A1", None, -2.0, "USD", date(2024, 1, 2), "reimbursement"),
            ("A2", None, 3.0, "USD", date(2024, 1, 1), "return"),
        ]

        summary = conn.execute(
            text(
                """
                SELECT asin, date, refund_amount::float
                FROM v_refunds_summary
                ORDER BY asin, date
                """
            )
        ).fetchall()
        assert summary == [
            ("A1", date(2024, 1, 1), 5.0),
            ("A1", date(2024, 1, 2), -2.0),
            ("A2", date(2024, 1, 1), 3.0),
        ]

    run("downgrade", "-1")
    run("upgrade", "head")
    with db_engine.connect() as conn:
        conn.execute(text("SELECT * FROM v_refunds_txn LIMIT 0"))
