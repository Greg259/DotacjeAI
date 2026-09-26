"""user accounts and property profiles

Revision ID: d9f4a2c68130
Revises: b7c2e4f190ad
Create Date: 2026-09-26 14:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d9f4a2c68130"
down_revision: str | None = "b7c2e4f190ad"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("user", "editor", "admin", name="userrole", native_enum=False, length=20),
            server_default="user",
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("terms_version", sa.String(length=40), nullable=False),
        sa.Column("accepted_terms_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_privacy_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "user_sessions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("csrf_token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_sessions_token_hash", "user_sessions", ["token_hash"], unique=True)
    op.create_index(
        "ix_user_sessions_user_expires",
        "user_sessions",
        ["user_id", "expires_at"],
        unique=False,
    )
    op.create_table(
        "property_profiles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "beneficiary_type",
            sa.Enum(
                "natural_person",
                "owner",
                "co_owner",
                "tenant",
                "housing_community",
                name="beneficiarytype",
                native_enum=False,
                length=40,
            ),
            nullable=False,
        ),
        sa.Column(
            "property_type",
            sa.Enum(
                "single_family_house",
                "apartment",
                "housing_community",
                "new_house",
                "existing_building",
                name="propertytype",
                native_enum=False,
                length=40,
            ),
            nullable=False,
        ),
        sa.Column(
            "building_state",
            sa.Enum("new", "existing", name="buildingstate", native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column(
            "current_heat_source",
            sa.Enum(
                "coal",
                "biomass",
                "gas",
                "electric",
                "district_heating",
                "heat_pump",
                "other",
                "none",
                name="heatsource",
                native_enum=False,
                length=30,
            ),
            nullable=False,
        ),
        sa.Column("year_built", sa.Integer(), nullable=True),
        sa.Column("heated_area_m2", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name"),
    )
    op.create_table(
        "profile_investment_categories",
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column(
            "investment_category",
            sa.Enum(
                "photovoltaics",
                "energy_storage",
                "heat_storage",
                "heat_pump",
                "domestic_hot_water",
                "micro_wind",
                "thermal_modernization",
                "heat_source_replacement",
                name="investmentcategory",
                native_enum=False,
                length=40,
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["profile_id"], ["property_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("profile_id", "investment_category"),
    )


def downgrade() -> None:
    op.drop_table("profile_investment_categories")
    op.drop_table("property_profiles")
    op.drop_index("ix_user_sessions_user_expires", table_name="user_sessions")
    op.drop_index("ix_user_sessions_token_hash", table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_table("users")
