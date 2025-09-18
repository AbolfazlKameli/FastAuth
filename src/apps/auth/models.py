from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database import Base


class OtpBlacklist(Base):
    __tablename__ = "otp_blacklist"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(length=50), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=True)
