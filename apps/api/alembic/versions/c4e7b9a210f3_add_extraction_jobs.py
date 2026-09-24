"""add extraction jobs and llm idempotency

Revision ID: c4e7b9a210f3
Revises: a8d2f6c4b901
Create Date: 2026-09-24 08:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import Text
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "c4e7b9a210f3"
down_revision: str | None = "a8d2f6c4b901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("llm_runs", sa.Column("idempotency_key", sa.String(length=64)))
    op.add_column("llm_runs", sa.Column("request_sha256", sa.String(length=64)))
    op.add_column("llm_runs", sa.Column("external_id", sa.String(length=255)))
    op.create_unique_constraint("uq_llm_runs_idempotency_key", "llm_runs", ["idempotency_key"])

    json_type = sa.JSON().with_variant(postgresql.JSONB(astext_type=Text()), "postgresql")
    op.create_table(
        "extraction_jobs",
        sa.Column("source_snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("review_task_id", sa.Uuid(), nullable=False),
        sa.Column("last_llm_run_id", sa.Uuid()),
        sa.Column("prompt_version", sa.String(length=80), nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "rules_ready",
                "awaiting_api_key",
                "blocked_by_budget",
                "ready_for_review",
                "failed",
                name="extractionstatus",
                native_enum=False,
                length=30,
            ),
            nullable=False,
        ),
        sa.Column("deterministic_data", json_type, nullable=False),
        sa.Column("candidate_data", json_type),
        sa.Column("evidence", json_type),
        sa.Column("warnings", json_type),
        sa.Column("error_message", sa.Text()),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["source_snapshot_id"], ["source_snapshots.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["review_task_id"], ["review_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["last_llm_run_id"], ["llm_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
        sa.UniqueConstraint("review_task_id"),
        sa.UniqueConstraint("source_snapshot_id", "prompt_version"),
    )
    op.create_index(
        "ix_extraction_jobs_status_created",
        "extraction_jobs",
        ["status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_extraction_jobs_status_created", table_name="extraction_jobs")
    op.drop_table("extraction_jobs")
    op.drop_constraint("uq_llm_runs_idempotency_key", "llm_runs", type_="unique")
    op.drop_column("llm_runs", "external_id")
    op.drop_column("llm_runs", "request_sha256")
    op.drop_column("llm_runs", "idempotency_key")
