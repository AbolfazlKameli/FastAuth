from typing import Annotated

from fastapi import Depends
from redis import asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache.redis_handler import redis_fastapi
from .db.database import SessionLocal


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


async def get_redis() -> redis.Redis:
    return redis_fastapi


db_dependency = Annotated[AsyncSession, Depends(get_db)]
redis_dependency = Annotated[redis.Redis, Depends(get_redis)]
