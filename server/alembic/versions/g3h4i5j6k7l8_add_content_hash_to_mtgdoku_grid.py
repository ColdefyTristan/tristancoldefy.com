"""add content_hash to mtgdoku_grid

Revision ID: g3h4i5j6k7l8
Revises: f2a3b4c5d6e7
Create Date: 2026-03-27 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "g3h4i5j6k7l8"
down_revision: Union[str, None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Les lignes existantes n'ont pas de hash valide — on vide la table.
    # MtgDokuDailyGame référence ces grilles avec ON DELETE SET NULL, donc pas de violation FK.
    op.execute("DELETE FROM mtgdoku_daily_game")
    op.execute("DELETE FROM mtgdoku_grid")

    op.add_column(
        "mtgdoku_grid",
        sa.Column("content_hash", sa.String(32), nullable=False, server_default=""),
    )
    op.create_unique_constraint("uq_mtgdoku_grid_content_hash", "mtgdoku_grid", ["content_hash"])
    op.alter_column("mtgdoku_grid", "content_hash", server_default=None)


def downgrade() -> None:
    op.drop_constraint("uq_mtgdoku_grid_content_hash", "mtgdoku_grid", type_="unique")
    op.drop_column("mtgdoku_grid", "content_hash")
