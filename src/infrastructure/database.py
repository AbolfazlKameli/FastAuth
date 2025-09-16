from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from src.core import configs

engine = create_async_engine(
    url=configs.DATABASE_URL,
    pool_size=configs.DATABASE_POOL_SIZE,
    max_overflow=configs.DATABASE_MAX_OVERFLOW,
)

SessionLocal = async_sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass
