"""Added Otp table

Revision ID: 55b4092745e1
Revises: 4ab0107f45c9
Create Date: 2025-09-20 11:54:56.747657

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '55b4092745e1'
down_revision: Union[str, Sequence[str], None] = '4ab0107f45c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "otp",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(length=50), nullable=False),
        sa.Column("hashed_code", sa.String(length=128), nullable=False),
        sa.Column("attempts", sa.Integer, default=1, nullable=False),
        sa.Column("expires_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("otp")
