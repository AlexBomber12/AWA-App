from alembic import op  # type: ignore

revision = "0002_create_roi_view"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE VIEW roi_view AS
          SELECT
            p.asin,
            max(o.price_cents) / 100.0
            - f.fulf_fee
            - f.referral_fee
            - f.storage_fee AS roi_eur
          FROM products p
          JOIN offers   o ON o.asin = p.asin
          JOIN fees_raw f ON f.asin = p.asin
          GROUP BY
            p.asin,
            f.fulf_fee,
            f.referral_fee,
            f.storage_fee;
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS roi_view;")
