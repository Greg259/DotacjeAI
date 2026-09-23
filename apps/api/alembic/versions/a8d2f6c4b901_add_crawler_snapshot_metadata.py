"""add crawler snapshot metadata

Revision ID: a8d2f6c4b901
Revises: 4167552a1c92
Create Date: 2026-09-23 20:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a8d2f6c4b901"
down_revision: str | None = "4167552a1c92"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("sources", sa.Column("last_success_at", sa.DateTime(timezone=True)))
    op.add_column("sources", sa.Column("last_error_at", sa.DateTime(timezone=True)))
    op.add_column("sources", sa.Column("last_error_message", sa.Text()))
    op.add_column(
        "source_snapshots",
        sa.Column("normalized_sha256", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "source_snapshots",
        sa.Column("size_bytes", sa.Integer(), nullable=True),
    )
    op.add_column(
        "source_snapshots",
        sa.Column("diff_path", sa.Text(), nullable=True),
    )
    op.execute(
        "UPDATE source_snapshots SET normalized_sha256 = sha256 "
        "WHERE normalized_sha256 IS NULL"
    )
    op.execute("UPDATE source_snapshots SET size_bytes = 0 WHERE size_bytes IS NULL")
    op.alter_column("source_snapshots", "normalized_sha256", nullable=False)
    op.alter_column("source_snapshots", "size_bytes", nullable=False)


def downgrade() -> None:
    op.drop_column("source_snapshots", "diff_path")
    op.drop_column("source_snapshots", "size_bytes")
    op.drop_column("source_snapshots", "normalized_sha256")
    op.drop_column("sources", "last_error_message")
    op.drop_column("sources", "last_error_at")
    op.drop_column("sources", "last_success_at")
