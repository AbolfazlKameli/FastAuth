from datetime import datetime
from random import randint

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.users.models import User
from src.apps.users.repository import get_user_by_email, create_user
from src.apps.utils import get_or_create
from src.core.configs.settings import configs
from .models import Otp, OtpBlacklist
from .repository import get_active_blacklist_by_email

hasher = PasswordHasher()
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def check_blacklist_for_user(db: AsyncSession, email: str) -> str | None:
    now = datetime.now()

    blacklist = await get_active_blacklist_by_email(db, email, now)
    response: str | None = None

    if blacklist and blacklist.expires_at is not None:
        expiration_date_time = blacklist.expires_at.strftime("%Y-%m-%d %H:%M:%S")
        response = f"You have benn blocked until {expiration_date_time}"

    if blacklist and blacklist.expires_at is None:
        response = "You have been permanently blocked. if you believe this is a mistake, please contact support."

    return response


async def handle_user_blacklist(db: AsyncSession, email: str) -> str:
    await get_or_create(db, OtpBlacklist, email=email)
    return "Too many requests. Your email has been added to the blacklist."


async def check_email_exists(db: AsyncSession, email: str) -> bool:
    user = await get_user_by_email(db, email)
    return user is not None


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


async def refresh_otp_code(db: AsyncSession, otp: Otp, hashed_otp: str, expires_at: datetime):
    otp.hashed_code = hashed_otp
    otp.expires_at = expires_at
    otp.attempts += 1
    db.add(otp)
    await db.commit()


def is_otp_valid(otp_code: str, otp_obj: Otp) -> bool:
    now = datetime.now()

    if otp_obj is None or otp_obj.expires_at < now:
        return False

    try:
        hasher.verify(otp_obj.hashed_code, otp_code)
    except VerifyMismatchError:
        return False

    return True


def hash_password(password: str):
    return password_context.hash(password)


async def register_user(db: AsyncSession, email: str, username: str, password: str) -> User:
    hashed_password = hash_password(password)
    user = User(email=email, username=username, password=hashed_password)
    try:
        user = await create_user(db, user)
    except IntegrityError:
        await db.rollback()
        raise ValueError("Duplicate entry or constraint violated")
    except SQLAlchemyError as e:
        await db.rollback()
        raise RuntimeError(f"Database error: {e}")
    return user


async def delete_otp(db: AsyncSession, otp: Otp):
    await db.delete(otp)
    await db.commit()
