"""Add timezone to otp blacklist model.

Revision ID: cf923dbe481d
Revises: a9990f6e9bbb
Create Date: 2025-10-07 17:17:21.979226

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf923dbe481d'
down_revision: Union[str, Sequence[str], None] = 'a9990f6e9bbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "otp_blacklist",
        "expires_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "otp_blacklist",
        "expires_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime()
    )
