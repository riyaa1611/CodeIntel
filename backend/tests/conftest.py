import asyncio
import os

import pytest
from dotenv import load_dotenv

# Load test env BEFORE any app module is imported so that the lru_cached
# settings singleton picks up test values on first construction.
load_dotenv(
    os.path.join(os.path.dirname(__file__), "..", ".env.test"),
    override=True,
)

# Clear the settings cache so any already-constructed singleton is discarded
# and rebuilt with the test env values.
from app.config import get_settings
get_settings.cache_clear()

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import Base

TEST_DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://codeintel:codeintel@localhost:5432/codeintel_test",
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    eng = create_async_engine(TEST_DB_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest.fixture
async def db(engine):
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
