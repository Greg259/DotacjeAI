"""user source suggestions

Revision ID: g4c9e3b87215
Revises: f3b8d2a76104
Create Date: 2026-09-26 19:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "g4c9e3b87215"
down_revision: str | None = "f3b8d2a76104"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "source_suggestions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid()),
        sa.Column("title", sa.String(255)),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("note", sa.String(1000)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reviewer_note", sa.String(1000)),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "url"),
    )


def downgrade() -> None:
    op.drop_table("source_suggestions")
