"""add document availability monitoring

Revision ID: e7f2a1c8d904
Revises: c4e7b9a210f3
Create Date: 2026-09-24 11:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e7f2a1c8d904"
down_revision: str | None = "c4e7b9a210f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "program_documents",
        sa.Column("last_checked_at", sa.DateTime(timezone=True)),
    )
    op.add_column("program_documents", sa.Column("last_http_status", sa.Integer()))
    op.add_column("program_documents", sa.Column("last_error_message", sa.Text()))
    op.add_column(
        "program_documents",
        sa.Column("is_available", sa.Boolean(), server_default="true", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("program_documents", "is_available")
    op.drop_column("program_documents", "last_error_message")
    op.drop_column("program_documents", "last_http_status")
    op.drop_column("program_documents", "last_checked_at")
