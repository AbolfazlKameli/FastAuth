from datetime import datetime
from enum import Enum

import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, Mapped

from src.infrastructure.database import Base


class UserRoles(Enum):
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(sa.String(length=25), unique=True)
    email: Mapped[str] = mapped_column(sa.String(length=50), unique=True)
    role: Mapped[UserRoles] = mapped_column(
        sa.Enum(UserRoles, name="user_roles_enum"),
        default=UserRoles.user.value,
        nullable=False
    )
    password: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, default=datetime.now)
