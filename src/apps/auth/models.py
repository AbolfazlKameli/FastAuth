from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database import Base


class Otp(Base):
    __tablename__ = "otp"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(length=50), nullable=False)
    hashed_code: Mapped[str] = mapped_column(String(length=128), nullable=False)
    attempts: Mapped[int] = mapped_column(default=1, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)


class OtpBlacklist(Base):
    __tablename__ = "otp_blacklist"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(length=50), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=True)
