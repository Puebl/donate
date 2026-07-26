import pytest
from unittest.mock import AsyncMock, MagicMock

from src.api.payment_gateways.oxypay.service import OxypayService


@pytest.fixture(autouse=True)
async def process_test():
    yield


@pytest.fixture
def oxypay_service():
    return OxypayService()
