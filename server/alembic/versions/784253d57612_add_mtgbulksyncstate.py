"""add MtgBulkSyncState

Revision ID: 784253d57612
Revises: 8063482d2484
Create Date: 2026-03-18 15:23:18.777742

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '784253d57612'
down_revision: Union[str, Sequence[str], None] = '8063482d2484'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
