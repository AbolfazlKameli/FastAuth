from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import OtpBlacklist, Otp


async def get_active_blacklist_by_email(db: AsyncSession, email: str, current_time: datetime) -> OtpBlacklist | None:
    stmt = (
        select(OtpBlacklist)
        .where(
            (OtpBlacklist.email == email) &
            (
                    (OtpBlacklist.expires_at >= current_time) |
                    (OtpBlacklist.expires_at.is_(None))
            )
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_otp_by_email(db: AsyncSession, email: str) -> Otp | None:
    stmt = select(Otp).where(Otp.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
