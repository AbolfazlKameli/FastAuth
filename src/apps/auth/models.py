from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database import Base


class Otp(Base):
    __tablename__ = "otp"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(length=50), nullable=False)
    hashed_code: Mapped[str] = mapped_column(String(length=128), nullable=False)
    attempts: Mapped[int] = mapped_column(default=1, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class OtpBlacklist(Base):
    __tablename__ = "otp_blacklist"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(length=50), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class RefreshTokenBlacklist(Base):
    __tablename__ = "refresh_token_blacklist"

    id: Mapped[int] = mapped_column(primary_key=True)
    refresh: Mapped[str] = mapped_column(nullable=False)
