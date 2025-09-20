"""Added unique constraint to email field

Revision ID: e4915cca4728
Revises: 55b4092745e1
Create Date: 2025-09-20 12:52:05.002926

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e4915cca4728'
down_revision: Union[str, Sequence[str], None] = '55b4092745e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint("uq_email", "otp_blacklist", ["email"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_email", "otp_blacklist", type_="unique")
