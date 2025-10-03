"""Add is_active field to user table.

Revision ID: ef862e4f19d9
Revises: 5b5a84f07d20
Create Date: 2025-10-03 09:52:13.415369

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ef862e4f19d9'
down_revision: Union[str, Sequence[str], None] = '5b5a84f07d20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean, nullable=False, default=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "is_active")
