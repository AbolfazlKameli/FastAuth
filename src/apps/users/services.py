from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.pagination import paginate
from .repository import get_all_users, get_user_by_id


async def get_all_users_paginated(db: AsyncSession, page: int, per_page: int):
    return await paginate(get_all_users(), db, page=page, per_page=per_page)


async def get_user_or_404(db: AsyncSession, user_id: int):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(detail="User not found", status_code=status.HTTP_404_NOT_FOUND)
    return user
