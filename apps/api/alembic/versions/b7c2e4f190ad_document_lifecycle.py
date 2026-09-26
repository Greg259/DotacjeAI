"""add document lifecycle state

Revision ID: b7c2e4f190ad
Revises: f3a8c1d7e602
Create Date: 2026-09-26 12:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b7c2e4f190ad"
down_revision: str | None = "f3a8c1d7e602"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "program_documents",
        sa.Column("state", sa.String(length=30), server_default="current", nullable=False),
    )
    op.add_column("program_documents", sa.Column("state_reason", sa.Text(), nullable=True))
    op.add_column(
        "program_documents",
        sa.Column("state_changed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("program_documents", "state_changed_at")
    op.drop_column("program_documents", "state_reason")
    op.drop_column("program_documents", "state")
