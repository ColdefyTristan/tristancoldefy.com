"""add summarized and interest_score to tech_article

Revision ID: m9o0p1q2r3s4
Revises: l8m9o0p1q2r3
Create Date: 2026-04-12 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "m9o0p1q2r3s4"
down_revision: Union[str, None] = "l8m9o0p1q2r3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tech_article", sa.Column("summarized", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("tech_article", sa.Column("interest_score", sa.Integer(), nullable=True))
    op.create_index("ix_tech_article_summarized", "tech_article", ["summarized"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tech_article_summarized", table_name="tech_article")
    op.drop_column("tech_article", "summarized")
    op.drop_column("tech_article", "interest_score")
