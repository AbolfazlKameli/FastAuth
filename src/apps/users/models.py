from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, Mapped

from src.infrastructure.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(sa.String(length=25), unique=True)
    email: Mapped[str] = mapped_column(sa.String(length=50), unique=True)
    password: Mapped[str] = mapped_column(sa.String(length=50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, default=datetime.now)
