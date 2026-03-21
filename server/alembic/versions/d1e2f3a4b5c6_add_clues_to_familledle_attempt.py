"""add clues and clue_points to familledle_attempt

Revision ID: d1e2f3a4b5c6
Revises: c3d4e5f6a7b8, ff325c6b49d3, ecf4b405cab3
Create Date: 2026-03-21 00:00:03.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = ("c3d4e5f6a7b8", "ff325c6b49d3", "ecf4b405cab3")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "familledle_attempt",
        sa.Column(
            "clues",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "familledle_attempt",
        sa.Column("clue_points", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )


def downgrade() -> None:
    op.drop_column("familledle_attempt", "clue_points")
    op.drop_column("familledle_attempt", "clues")
