"""add doku fields to mtg_card

Revision ID: e1f2a3b4c5d6
Revises: d1e2f3a4b5c6
Create Date: 2026-03-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, Sequence[str], None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("mtg_card", sa.Column("colors", ARRAY(sa.String(1)), nullable=False, server_default="{}"))
    op.add_column("mtg_card", sa.Column("type_line", sa.Text(), nullable=True))
    op.add_column("mtg_card", sa.Column("oracle_text", sa.Text(), nullable=True))
    op.add_column("mtg_card", sa.Column("power", sa.String(10), nullable=True))
    op.add_column("mtg_card", sa.Column("toughness", sa.String(10), nullable=True))
    op.add_column("mtg_card", sa.Column("edhrec_rank", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("mtg_card", "edhrec_rank")
    op.drop_column("mtg_card", "toughness")
    op.drop_column("mtg_card", "power")
    op.drop_column("mtg_card", "oracle_text")
    op.drop_column("mtg_card", "type_line")
    op.drop_column("mtg_card", "colors")
