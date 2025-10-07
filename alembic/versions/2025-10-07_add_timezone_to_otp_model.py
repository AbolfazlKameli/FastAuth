"""Add timezone to otp model.

Revision ID: a9990f6e9bbb
Revises: a544967c7cb3
Create Date: 2025-10-07 17:16:12.685002

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9990f6e9bbb'
down_revision: Union[str, Sequence[str], None] = 'a544967c7cb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "otp",
        "expires_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "otp",
        "expires_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime()
    )
