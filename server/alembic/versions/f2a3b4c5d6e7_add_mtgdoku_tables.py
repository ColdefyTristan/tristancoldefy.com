"""add mtgdoku tables

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-03-27 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mtgdoku_grid",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("difficulty", sa.String(10), nullable=False, index=True),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("difficulty_score", sa.Float, nullable=False),
        sa.Column("grid_data", JSONB, nullable=False),
    )

    op.create_table(
        "mtgdoku_daily_game",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("day", sa.Date, nullable=False, unique=True, index=True),
        sa.Column("easy_grid_id", sa.Integer, sa.ForeignKey("mtgdoku_grid.id", ondelete="SET NULL"), nullable=True),
        sa.Column("medium_grid_id", sa.Integer, sa.ForeignKey("mtgdoku_grid.id", ondelete="SET NULL"), nullable=True),
        sa.Column("hard_grid_id", sa.Integer, sa.ForeignKey("mtgdoku_grid.id", ondelete="SET NULL"), nullable=True),
        sa.UniqueConstraint("day", name="uq_mtgdoku_daily_game_day"),
    )

    op.create_table(
        "mtgdoku_attempt",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("day", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("finished_at", sa.DateTime, nullable=True),
        sa.Column("won_easy", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("won_medium", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("won_hard", sa.Boolean, nullable=False, server_default="false"),
        sa.UniqueConstraint("user_id", "day", name="uq_mtgdoku_attempt_user_day"),
    )
    op.create_index("ix_mtgdoku_attempt_user_day", "mtgdoku_attempt", ["user_id", "day"])
    op.create_index("ix_mtgdoku_attempt_day", "mtgdoku_attempt", ["day"])

    op.create_table(
        "mtgdoku_attempt_guess",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("attempt_id", sa.Integer, sa.ForeignKey("mtgdoku_attempt.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("difficulty", sa.String(10), nullable=False),
        sa.Column("cell_row", sa.SmallInteger, nullable=False),
        sa.Column("cell_col", sa.SmallInteger, nullable=False),
        sa.Column("oracle_id", sa.String(36), sa.ForeignKey("mtg_card.oracle_id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("is_valid", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_mtgdoku_guess_attempt_pos", "mtgdoku_attempt_guess", ["attempt_id", "position"])


def downgrade() -> None:
    op.drop_table("mtgdoku_attempt_guess")
    op.drop_table("mtgdoku_attempt")
    op.drop_table("mtgdoku_daily_game")
    op.drop_table("mtgdoku_grid")
