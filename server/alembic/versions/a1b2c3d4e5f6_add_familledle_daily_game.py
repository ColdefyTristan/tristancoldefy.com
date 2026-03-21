"""add familledle_daily_game, remove is_champ_of_the_day

Revision ID: a1b2c3d4e5f6
Revises: ecf4b405cab3
Create Date: 2026-03-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "ecf4b405cab3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Créer la table familledle_daily_game
    op.create_table(
        "familledle_daily_game",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("champ_name", sa.String(), nullable=False),
        sa.Column("row_columns", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("winner_count", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["champ_name"], ["champ_data.name"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("day", name="uq_familledle_daily_game_day"),
    )
    op.create_index("ix_familledle_daily_game_day", "familledle_daily_game", ["day"], unique=True)

    # Supprimer la colonne is_champ_of_the_day de champ_data
    op.drop_column("champ_data", "is_champ_of_the_day")


def downgrade() -> None:
    # Restaurer is_champ_of_the_day
    op.add_column(
        "champ_data",
        sa.Column("is_champ_of_the_day", sa.Boolean(), nullable=False, server_default="false"),
    )

    # Supprimer la table familledle_daily_game
    op.drop_index("ix_familledle_daily_game_day", table_name="familledle_daily_game")
    op.drop_table("familledle_daily_game")
