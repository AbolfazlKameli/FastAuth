"""Drop password length constraint users table.

Revision ID: c3405d6e693e
Revises: e4915cca4728
Create Date: 2025-09-21 20:44:36.067974

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c3405d6e693e'
down_revision: Union[str, Sequence[str], None] = 'e4915cca4728'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "users", "password",
        existing_type=sa.VARCHAR(length=50),
        type_=sa.String()
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "users", "password",
        existing_type=sa.String(),
        type_=sa.VARCHAR(length=50),
    )
