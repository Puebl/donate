import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from faker import Faker

from src.core.constants import EnvironmentEnum
from src.core.database.connection import db_helper
from src.core.database.models import Base
from src.core.settings.base import settings

from src.main import main_app


pytest_plugins = [
    'tests.fixtures',
]


@pytest.fixture()
def prepare_test():
    async def prepare():
        assert settings.MODE == EnvironmentEnum.TEST

        async with db_helper.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            await conn.run_sync(Base.metadata.create_all)

    return prepare


@pytest.fixture()
def teardown_test():
    async def teardown():
        pass

    return teardown


@pytest.fixture(autouse=True)
async def process_test(prepare_test, teardown_test):
    await prepare_test()
    yield
    await teardown_test()
    await db_helper.engine.dispose()


@pytest.fixture()
async def api_client():
    async with AsyncClient(base_url='http://test', transport=ASGITransport(app=main_app)) as client:
        yield client


@pytest.fixture()
async def payment_session():
    async with db_helper.session_factory() as session:
        yield session


@pytest.fixture()
async def faker() -> Faker:
    faker = Faker(locale=['ru_RU'])
    return faker