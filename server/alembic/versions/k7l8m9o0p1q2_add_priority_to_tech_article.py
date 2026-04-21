"""add priority to tech_article

Revision ID: k7l8m9o0p1q2
Revises: j6k7l8m9o0p1
Create Date: 2026-04-10 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "k7l8m9o0p1q2"
down_revision: Union[str, None] = "j6k7l8m9o0p1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tech_article", sa.Column("priority", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("tech_article", "priority")
