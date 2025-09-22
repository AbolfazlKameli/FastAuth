"""Added OtpBlacklist table.

Revision ID: 4ab0107f45c9
Revises: 7987e99f38a2
Create Date: 2025-09-18 18:03:53.748595

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '4ab0107f45c9'
down_revision: Union[str, Sequence[str], None] = '7987e99f38a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "otp_blacklist",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(length=50), nullable=False),
        sa.Column("expires_at", sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("otp_blacklist")
