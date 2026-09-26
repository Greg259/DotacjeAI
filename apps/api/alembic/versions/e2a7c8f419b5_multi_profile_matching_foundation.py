"""multi profile matching foundation

Revision ID: e2a7c8f419b5
Revises: d9f4a2c68130
Create Date: 2026-09-26 17:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import Text
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e2a7c8f419b5"
down_revision: str | None = "d9f4a2c68130"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "property_profiles",
        sa.Column(
            "profile_kind",
            sa.Enum("property", "business", name="profilekind", native_enum=False, length=20),
            server_default="property",
            nullable=False,
        ),
    )
    op.alter_column("property_profiles", "property_type", nullable=True)
    op.alter_column("property_profiles", "building_state", nullable=True)
    op.alter_column("property_profiles", "current_heat_source", nullable=True)
    op.add_column("property_profiles", sa.Column("business_name", sa.String(255)))
    op.add_column(
        "property_profiles",
        sa.Column(
            "business_size",
            sa.Enum(
                "micro",
                "small",
                "medium",
                "large",
                name="businesssize",
                native_enum=False,
                length=20,
            ),
        ),
    )
    op.add_column(
        "property_profiles",
        sa.Column(
            "legal_form",
            sa.Enum(
                "sole_proprietorship",
                "company",
                "cooperative",
                "ngo",
                "research_organization",
                "other",
                name="businesslegalform",
                native_enum=False,
                length=40,
            ),
        ),
    )
    op.add_column("property_profiles", sa.Column("established_year", sa.Integer()))
    op.add_column("property_profiles", sa.Column("employee_count", sa.Integer()))
    op.add_column("property_profiles", sa.Column("annual_turnover_pln", sa.Numeric(16, 2)))
    op.add_column(
        "property_profiles",
        sa.Column(
            "industry_codes",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=Text()), "postgresql"),
            nullable=True,
        ),
    )
    op.execute("UPDATE property_profiles SET industry_codes = '[]'::jsonb")
    op.alter_column("property_profiles", "industry_codes", nullable=False)
    op.create_table(
        "program_business_sizes",
        sa.Column("program_id", sa.Uuid(), nullable=False),
        sa.Column(
            "business_size",
            sa.Enum(
                "micro",
                "small",
                "medium",
                "large",
                name="businesssize",
                native_enum=False,
                length=20,
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("program_id", "business_size"),
    )


def downgrade() -> None:
    op.drop_table("program_business_sizes")
    op.drop_column("property_profiles", "industry_codes")
    op.drop_column("property_profiles", "annual_turnover_pln")
    op.drop_column("property_profiles", "employee_count")
    op.drop_column("property_profiles", "established_year")
    op.drop_column("property_profiles", "legal_form")
    op.drop_column("property_profiles", "business_size")
    op.drop_column("property_profiles", "business_name")
    op.alter_column("property_profiles", "current_heat_source", nullable=False)
    op.alter_column("property_profiles", "building_state", nullable=False)
    op.alter_column("property_profiles", "property_type", nullable=False)
    op.drop_column("property_profiles", "profile_kind")
