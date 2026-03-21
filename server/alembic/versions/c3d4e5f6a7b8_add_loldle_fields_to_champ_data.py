"""add genre, ressource, portee, annee_sortie, role, espece, region to champ_data

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-21 00:00:02.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("champ_data", sa.Column("genre", sa.String(), nullable=True))
    op.add_column("champ_data", sa.Column("ressource", sa.String(), nullable=True))
    op.add_column("champ_data", sa.Column("portee", sa.String(), nullable=True))
    op.add_column("champ_data", sa.Column("annee_sortie", sa.String(), nullable=True))
    op.add_column(
        "champ_data",
        sa.Column(
            "role",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "champ_data",
        sa.Column(
            "espece",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "champ_data",
        sa.Column(
            "region",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("champ_data", "region")
    op.drop_column("champ_data", "espece")
    op.drop_column("champ_data", "role")
    op.drop_column("champ_data", "annee_sortie")
    op.drop_column("champ_data", "portee")
    op.drop_column("champ_data", "ressource")
    op.drop_column("champ_data", "genre")
