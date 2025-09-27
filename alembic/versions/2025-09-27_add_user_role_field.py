"""Add user role field

Revision ID: 51ae9dbd7cdb
Revises: c3405d6e693e
Create Date: 2025-09-27 17:18:19.638879

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '51ae9dbd7cdb'
down_revision: Union[str, Sequence[str], None] = 'c3405d6e693e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE TYPE user_roles_enum AS ENUM ('admin', 'user')")
    op.add_column(
        "users",
        sa.Column("role", sa.Enum(name="user_roles_enum"), default="user", nullable=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "role")
    op.execute("DROP TYPE user_roles_enum")
