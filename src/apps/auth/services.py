from datetime import datetime
from random import randint

from argon2 import PasswordHasher
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.utils import get_or_create
from src.core.configs.settings import configs
from .models import Otp

hasher = PasswordHasher()


async def generate_otp(db: AsyncSession, email: str) -> (Otp, str, str, bool, datetime):
    expires_at = datetime.now() + configs.OTP_SETTINGS.OTP_EXPIRATION_TIME

    otp_code = str(randint(100_000, 999_999))
    hashed_code = hasher.hash(otp_code)

    obj, is_new = await get_or_create(
        db,
        Otp,
        {"hashed_code": hashed_code, "expires_at": expires_at},
        email=email
    )

    return obj, otp_code, hashed_code, is_new, expires_at
