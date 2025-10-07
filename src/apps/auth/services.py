from datetime import datetime, timedelta
from random import randint
from typing import Literal, Annotated

import pytz
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, status
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.tasks import send_otp_code_email
from src.apps.users.models import User, UserRoles
from src.apps.users.repository import get_user_by_email, create_user, get_user_by_id
from src.apps.utils import get_or_create
from src.core.configs.settings import configs
from src.dependencies import db_dependency
from .models import Otp, OtpBlacklist
from .repository import get_active_blacklist_by_email

hasher = PasswordHasher()


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication scheme.")

            try:
                decode_access_token(credentials.credentials)
            except JWTError as e:
                raise e

            return credentials.credentials
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials.")


oauth_schema = JWTBearer()

oauth = OAuth()

oauth.register(
    name='google',
    client_id=configs.CLIENT_ID,
    client_secret=configs.CLIENT_SECRET,
    access_token_url=configs.TOKEN_URI,
    access_token_params=None,
    authorize_url=configs.AUTH_URI,
    authorize_params=None,
    client_kwargs={'scope': [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
    ]},
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration"
)


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
    expires_at = datetime.now(tz=pytz.timezone(configs.TIMEZONE)) + configs.OTP_EXPIRATION_TIME

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


async def generate_and_send_otp(db: AsyncSession, email: str):
    otp_obj, otp_code, hashed_code, is_new, expires_at = await generate_otp(db, email)

    if not is_new and otp_obj.attempts >= configs.OTP_MAX_ATTEMPTS:
        message = await handle_user_blacklist(db, email)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=message)

    if not is_new:
        await refresh_otp_code(db, otp_obj, hashed_code, expires_at)

    send_otp_code_email.delay(email, otp_code)


def is_otp_valid(otp_code: str, otp_obj: Otp) -> bool:
    now = datetime.now()

    if otp_obj is None or otp_obj.expires_at < now:
        return False

    try:
        hasher.verify(otp_obj.hashed_code, otp_code)
    except VerifyMismatchError:
        return False

    return True


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)

    if user is None:
        return None

    if not user.is_active:
        return None

    if not user.verify_password(password):
        return None

    return user


def create_jwt_token(
        user_id: int,
        email: str,
        token_type: Literal["access", "refresh"],
        expires_at: timedelta = timedelta(minutes=15)
) -> str:
    payload = {"user_id": user_id, "email": email, "token_type": token_type}
    exp = datetime.now(tz=pytz.timezone("Asia/Tehran")) + expires_at
    payload.update({"exp": exp})
    return jwt.encode(payload, configs.SECRET_KEY, algorithm="HS256")


async def register_user(db: AsyncSession, email: str, username: str, password: str | None = None) -> User:
    user = User(email=email, username=username)

    if password is None:
        user.set_unusable_password()
    elif password is not None:
        user.set_password(password)

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


def decode_access_token(token: Annotated[str, Depends(oauth_schema)]):
    try:
        payload = jwt.decode(token, configs.SECRET_KEY, algorithms=["HS256"])
        user_id: int = payload.get("user_id")
        token_type: str = payload.get("token_type")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, Invalid token.",
            )

        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, invalid token type."
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed, invalid or expired token.",
        )

    return user_id


def decode_refresh_token(token: str):
    try:
        payload = jwt.decode(token, configs.SECRET_KEY, algorithms=["HS256"])
        user_id: int = payload.get("user_id")
        token_type: str = payload.get("token_type")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, Invalid token.",
            )

        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, invalid token type."
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed, invalid or expired token.",
        )

    return user_id


async def get_authenticated_user(db: db_dependency, user_id: Annotated[int, Depends(decode_access_token)]):
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed, invalid user.",
        )
    return user


async def get_admin_user(user: Annotated[User, Depends(get_authenticated_user)]):
    if user.role.value != UserRoles.admin.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this resource",
        )
    return user


async def get_active_user(user: Annotated[User, Depends(get_authenticated_user)]):
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive account.",
        )
    return user
