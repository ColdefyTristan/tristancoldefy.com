"""add tech_article table

Revision ID: j6k7l8m9o0p1
Revises: i5j6k7l8m9o0
Create Date: 2026-04-10 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "j6k7l8m9o0p1"
down_revision: Union[str, None] = "i5j6k7l8m9o0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tech_article",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tech_article_url", "tech_article", ["url"], unique=True)
    op.create_index("ix_tech_article_source", "tech_article", ["source"], unique=False)
    op.create_index("ix_tech_article_published_at", "tech_article", ["published_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tech_article_published_at", table_name="tech_article")
    op.drop_index("ix_tech_article_source", table_name="tech_article")
    op.drop_index("ix_tech_article_url", table_name="tech_article")
    op.drop_table("tech_article")
