"""Add refresh token blacklist table.

Revision ID: 5b5a84f07d20
Revises: 51ae9dbd7cdb
Create Date: 2025-09-28 18:52:56.945657

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '5b5a84f07d20'
down_revision: Union[str, Sequence[str], None] = '51ae9dbd7cdb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "refresh_token_blacklist",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("refresh", sa.String, nullable=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("refresh_token_blacklist")
