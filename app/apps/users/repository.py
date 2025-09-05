from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User


def get_all_users():
    return select(User)


async def get_user_by_id(db: AsyncSession, user_id: int):
    user = await db.get(User, user_id)
    return user
