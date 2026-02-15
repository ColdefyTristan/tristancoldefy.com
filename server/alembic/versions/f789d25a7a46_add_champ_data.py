"""add champ_data

Revision ID: f789d25a7a46
Revises: 9e265b3c3aa8
Create Date: 2026-02-11 23:24:25.814838
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f789d25a7a46"
down_revision: Union[str, Sequence[str], None] = "9e265b3c3aa8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "champ_data",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("skin_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "family_mastery",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("mobility", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("randomness", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cc_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("icon_url", sa.String(), nullable=False),
        sa.Column("mean_hex", sa.String(), nullable=False),
        sa.Column("mean_hue", sa.Integer(), nullable=False),
        sa.Column(
            "is_champ_of_the_day", sa.Boolean(), nullable=False, server_default="False"
        ),
        sa.PrimaryKeyConstraint("name"),
    )
    op.create_index(op.f("ix_champ_data_name"), "champ_data", ["name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_champ_data_name"), table_name="champ_data")
    op.drop_table("champ_data")
