"""advanced eligibility and business program discovery

Revision ID: f3b8d2a76104
Revises: e2a7c8f419b5
Create Date: 2026-09-26 19:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import Text
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "f3b8d2a76104"
down_revision: str | None = "e2a7c8f419b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

json_type = sa.JSON().with_variant(postgresql.JSONB(astext_type=Text()), "postgresql")


def upgrade() -> None:
    op.add_column("programs", sa.Column("eligibility_rules", json_type, nullable=True))
    op.execute("UPDATE programs SET eligibility_rules = '[]'::jsonb")
    op.alter_column("programs", "eligibility_rules", nullable=False)

    op.add_column("property_profiles", sa.Column("annual_household_income_pln", sa.Numeric(16, 2)))
    op.add_column("property_profiles", sa.Column("household_members", sa.Integer()))
    op.add_column("property_profiles", sa.Column("project_budget_pln", sa.Numeric(16, 2)))
    op.add_column("property_profiles", sa.Column("own_contribution_pln", sa.Numeric(16, 2)))
    op.add_column("property_profiles", sa.Column("de_minimis_aid_eur", sa.Numeric(16, 2)))
    op.add_column("property_profiles", sa.Column("is_startup", sa.Boolean()))
    op.add_column("property_profiles", sa.Column("has_vc_investor", sa.Boolean()))
    op.add_column("property_profiles", sa.Column("consortium_planned", sa.Boolean()))

    op.create_table(
        "program_discoveries",
        sa.Column("index_source_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("audience_tags", json_type, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["index_source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )


def downgrade() -> None:
    op.drop_table("program_discoveries")
    op.drop_column("property_profiles", "consortium_planned")
    op.drop_column("property_profiles", "has_vc_investor")
    op.drop_column("property_profiles", "is_startup")
    op.drop_column("property_profiles", "de_minimis_aid_eur")
    op.drop_column("property_profiles", "own_contribution_pln")
    op.drop_column("property_profiles", "project_budget_pln")
    op.drop_column("property_profiles", "household_members")
    op.drop_column("property_profiles", "annual_household_income_pln")
    op.drop_column("programs", "eligibility_rules")
