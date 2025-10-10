from typing import AsyncGenerator
from datetime import datetime, timedelta

import pytest_asyncio
import pytz
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from argon2 import PasswordHasher

from src.apps.auth.services import create_jwt_token
from src.apps.auth.models import Otp
from src.apps.users.models import User
from src.core.configs.settings import configs
from src.dependencies import get_db
from src.infrastructure.database import Base
from src.main import app

hasher = PasswordHasher()

engine = create_async_engine(url=configs.DATABASE_URL)

AsyncTestSessionLocal = async_sessionmaker(bind=engine)


@pytest_asyncio.fixture(scope="session")
async def overrides_get_db() -> AsyncSession:
    async with AsyncTestSessionLocal() as db:
        yield db


@pytest_asyncio.fixture(scope="module", autouse=True)
async def override_dependencies(overrides_get_db):
    app.dependency_overrides[get_db] = lambda: overrides_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def tear_up_and_down_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def generate_test_user(overrides_get_db):
    existing = await overrides_get_db.scalar(
        select(User).where(User.email == "testuser@gmail.com")
    )
    if existing is not None:
        await overrides_get_db.delete(existing)
        await overrides_get_db.commit()

    user = User(username="testuser", email="testuser@gmail.com")
    user.set_password("testuserpassword")
    overrides_get_db.add(user)
    await overrides_get_db.commit()
    await overrides_get_db.refresh(user)

    yield user

    await overrides_get_db.delete(user)
    await overrides_get_db.commit()


@pytest_asyncio.fixture(scope="function")
async def generate_test_otp(overrides_get_db):
    hashed_otp = hasher.hash("123456")
    now = datetime.now()

    existing = await overrides_get_db.scalar(
        select(Otp).where(Otp.email == "testuser@gmail.com")
    )
    if existing is not None:
        await overrides_get_db.delete(existing)
        await overrides_get_db.commit()

    otp = Otp(email="testuser@gmail.com", hashed_code=hashed_otp, expires_at=now + timedelta(minutes=2))
    overrides_get_db.add(otp)
    await overrides_get_db.commit()
    await overrides_get_db.refresh(otp)

    yield otp

    await overrides_get_db.delete(otp)
    await overrides_get_db.commit()


@pytest_asyncio.fixture(scope="function")
async def anon_client() -> AsyncGenerator[AsyncClient, None]:
    host, port = "localhost", 8080

    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app, client=(host, port)), base_url="http://test") as client:
            yield client


@pytest_asyncio.fixture(scope="function")
async def user_auth_client(overrides_get_db, anon_client) -> AsyncGenerator[AsyncClient, None]:
    user = await overrides_get_db.scalars(select(User).where(User.email == "testuser@gmail.com"))
    access_token = create_jwt_token(user.id, user.email, "access")
    anon_client.headers["Authorization"] = f"Bearer {access_token}"
    yield anon_client
