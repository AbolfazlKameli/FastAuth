from datetime import datetime
from enum import Enum

import sqlalchemy as sa
from passlib.context import CryptContext
from sqlalchemy.orm import mapped_column, Mapped

from src.infrastructure.database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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

    def hash_password(self, plain_password: str) -> str:
        return pwd_context.hash(plain_password)

    def verify_password(self, plain_password: str) -> bool:
        return pwd_context.verify(plain_password, self.password)

    def set_password(self, plain_password: str) -> None:
        self.password = self.hash_password(plain_password)
