from sqlalchemy import select
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
