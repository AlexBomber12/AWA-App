from alembic import op  # type: ignore[attr-defined]
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("asin", sa.Text(), primary_key=True),
        sa.Column("title", sa.Text()),
        sa.Column("brand", sa.Text()),
        sa.Column("category", sa.Text()),
        sa.Column("weight_kg", sa.Numeric()),
    )
    op.create_table(
        "offers",
        sa.Column("asin", sa.Text(), sa.ForeignKey("products.asin")),
        sa.Column("seller_sku", sa.Text()),
        sa.Column("price_cents", sa.Integer()),
        sa.Column("captured_at", sa.TIMESTAMP(timezone=True)),
    )
    op.create_table(
        "fees_raw",
        sa.Column("asin", sa.Text(), primary_key=True),
        sa.Column("fulf_fee", sa.Numeric()),
        sa.Column("referral_fee", sa.Numeric()),
        sa.Column("storage_fee", sa.Numeric()),
        sa.Column("captured_at", sa.TIMESTAMP(timezone=True)),
    )
    op.create_table(
        "etl_log",
        sa.Column("job", sa.Text()),
        sa.Column(
            "run_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")
        ),
        sa.Column("row_cnt", sa.Integer()),
    )
    op.execute(
        """CREATE VIEW roi_view as\n"
        "   select p.asin,\n"
        "          max(o.price_cents)/100.0 - f.fulf_fee - f.referral_fee - f.storage_fee as roi_eur\n"
        "   from products p\n"
        "   join offers   o on o.asin = p.asin\n"
        "   join fees_raw f on f.asin = p.asin\n"
        "   group by p.asin, f.fulf_fee, f.referral_fee, f.storage_fee;\n"
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS roi_view")
    op.drop_table("etl_log")
    op.drop_table("fees_raw")
    op.drop_table("offers")
    op.drop_table("products")
