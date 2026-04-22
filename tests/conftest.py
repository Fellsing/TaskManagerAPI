import asyncio
import os
import sys
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from database import get_db
from models.models import Base
from main import app
from core.redis_config import redis_client

os.environ["TESTING"] = "True"
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=NullPool
)
async_session = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        # run_sync позволяет выполнить синхронные методы метадаты в асинхронной среде
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def override_get_db():
    async with async_session() as db:
        yield db


app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def event_loop():
    """Создает единый цикл событий для всей сессии (исправляет 'different loop' error)."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def ac():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    await redis_client.aclose()
    await redis_client.connection_pool.disconnect()