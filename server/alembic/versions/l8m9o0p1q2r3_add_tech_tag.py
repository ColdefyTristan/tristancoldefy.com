"""add tech_tag table

Revision ID: l8m9o0p1q2r3
Revises: k7l8m9o0p1q2
Create Date: 2026-04-12 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "l8m9o0p1q2r3"
down_revision: Union[str, None] = "k7l8m9o0p1q2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tech_tag",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tech_tag_name", "tech_tag", ["name"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_tech_tag_name", table_name="tech_tag")
    op.drop_table("tech_tag")
