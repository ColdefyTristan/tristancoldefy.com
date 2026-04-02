"""rename familledle tables to riftdle

Revision ID: i5j6k7l8m9o0
Revises: h4i5j6k7l8m9
Create Date: 2026-04-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "i5j6k7l8m9o0"
down_revision: Union[str, None] = "h4i5j6k7l8m9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename tables
    op.rename_table("familledle_attempt", "riftdle_attempt")
    op.rename_table("familledle_attempt_guess", "riftdle_attempt_guess")
    op.rename_table("familledle_daily_game", "riftdle_daily_game")

    # Rename unique constraints
    op.execute(
        "ALTER TABLE riftdle_attempt "
        "RENAME CONSTRAINT uq_familledle_attempt_user_day TO uq_riftdle_attempt_user_day"
    )
    op.execute(
        "ALTER TABLE riftdle_daily_game "
        "RENAME CONSTRAINT uq_familledle_daily_game_day TO uq_riftdle_daily_game_day"
    )

    # Rename indexes
    op.execute("ALTER INDEX ix_familledle_attempt_user_day RENAME TO ix_riftdle_attempt_user_day")
    op.execute("ALTER INDEX ix_familledle_attempt_day RENAME TO ix_riftdle_attempt_day")


def downgrade() -> None:
    # Rename indexes back
    op.execute("ALTER INDEX ix_riftdle_attempt_user_day RENAME TO ix_familledle_attempt_user_day")
    op.execute("ALTER INDEX ix_riftdle_attempt_day RENAME TO ix_familledle_attempt_day")

    # Rename unique constraints back
    op.execute(
        "ALTER TABLE riftdle_daily_game "
        "RENAME CONSTRAINT uq_riftdle_daily_game_day TO uq_familledle_daily_game_day"
    )
    op.execute(
        "ALTER TABLE riftdle_attempt "
        "RENAME CONSTRAINT uq_riftdle_attempt_user_day TO uq_familledle_attempt_user_day"
    )

    # Rename tables back
    op.rename_table("riftdle_daily_game", "familledle_daily_game")
    op.rename_table("riftdle_attempt_guess", "familledle_attempt_guess")
    op.rename_table("riftdle_attempt", "familledle_attempt")
