"""Added User table

Revision ID: 7987e99f38a2
Revises: 
Create Date: 2025-09-18 14:19:36.351336

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '7987e99f38a2'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('username', sa.String(length=25), nullable=False, unique=True),
        sa.Column('email', sa.String(length=50), nullable=False, unique=True),
        sa.Column('password', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('users')
