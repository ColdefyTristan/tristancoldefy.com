"""add MtgBulkSyncState

Revision ID: 8063482d2484
Revises: ac8a44d34c70
Create Date: 2026-03-18 15:16:24.284393

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '8063482d2484'
down_revision: Union[str, Sequence[str], None] = 'ac8a44d34c70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
