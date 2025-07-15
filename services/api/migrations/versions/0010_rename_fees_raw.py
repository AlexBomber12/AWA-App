from alembic import op

revision = "0010_rename_fees_raw"
down_revision = "0009_fees_raw_fix"


def upgrade():
    # Deprecated; no changes required.
    pass


def downgrade():
    op.execute("DROP TABLE IF EXISTS fees_raw")
