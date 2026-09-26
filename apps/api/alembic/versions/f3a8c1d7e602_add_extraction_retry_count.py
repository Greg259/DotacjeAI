"""add extraction retry count

Revision ID: f3a8c1d7e602
Revises: e7f2a1c8d904
Create Date: 2026-09-26 10:15:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f3a8c1d7e602"
down_revision: str | None = "e7f2a1c8d904"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "extraction_jobs",
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("extraction_jobs", "retry_count")
