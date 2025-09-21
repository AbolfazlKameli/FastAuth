from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User


def get_all_users():
    return select(User)


async def get_user_by_id(db: AsyncSession, user_id: int):
    user = await db.get(User, user_id)
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    stmt = await db.execute(select(User).where(User.email == email))
    return stmt.scalar_one_or_none()


async def user_exists_with_email_or_username(db: AsyncSession, email: str, username: str) -> bool:
    email_stmt = await db.execute(select(exists(User)).where(User.email == email))
    email_result = email_stmt.scalar()

    username_stmt = await db.execute(select(exists(User)).where(User.username == username))
    username_result = username_stmt.scalar()

    return email_result or username_result
