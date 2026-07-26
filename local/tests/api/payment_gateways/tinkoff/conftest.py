import pytest
from unittest.mock import AsyncMock, MagicMock

from src.api.payment_gateways.tinkoff.uow import TinkoffUnitOfWork
from src.api.payment_gateways.tinkoff.service import TinkoffService


@pytest.fixture(autouse=True)
async def process_test():
    yield


@pytest.fixture
def mock_uow():
    uow = MagicMock(spec=TinkoffUnitOfWork)
    uow.deals = AsyncMock()
    uow.payments = AsyncMock()
    uow.deposit_requests = AsyncMock()
    uow.withdraws = AsyncMock()
    return uow


@pytest.fixture
def tinkoff_service(mock_uow):
    return TinkoffService(mock_uow)
