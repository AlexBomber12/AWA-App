from alembic import op
import sqlalchemy as sa

revision = "0011_load_log_table"
down_revision = "0010_rename_fees_raw"
branch_labels = depends_on = None


def upgrade() -> None:
    op.create_table(
        "load_log",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("target_table", sa.Text, nullable=False),
        sa.Column("inserted_rows", sa.Integer),
        sa.Column("status", sa.Text, nullable=False, server_default="pending"),
        sa.Column(
            "inserted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("load_log")
