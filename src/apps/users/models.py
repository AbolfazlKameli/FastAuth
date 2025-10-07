from datetime import datetime
from enum import Enum

import sqlalchemy as sa
from argon2 import PasswordHasher
from sqlalchemy.orm import mapped_column, Mapped

from src.core.configs.settings import configs
from src.infrastructure.database import Base

pwd_hasher = PasswordHasher()


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
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, default=datetime.now)

    def hash_password(self, plain_password: str) -> str:
        return pwd_hasher.hash(plain_password)

    def verify_password(self, plain_password: str) -> bool:
        if self.password.startswith(configs.UNUSABLE_PASSWORD_MARKER):
            return False
        return pwd_hasher.verify(self.password, plain_password)

    def set_password(self, plain_password: str) -> None:
        self.password = self.hash_password(plain_password)

    def set_unusable_password(self):
        self.password = configs.UNUSABLE_PASSWORD_MARKER
