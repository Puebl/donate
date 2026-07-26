"""
Integration test fixtures.

- tinkoff_test_client: real TinkoffAPIClient hitting rest-api-test.tinkoff.ru
- DB fixtures inherited from root conftest (process_test drops/creates tables per test)
"""

import pytest

from src.api.payment_gateways.tinkoff.client.service import TinkoffAPIClient
from src.api.payment_gateways.tinkoff.uow import TinkoffUnitOfWork
from src.api.payment_gateways.tinkoff.service import TinkoffService
from src.core.settings.base import settings


NN_UNSUPPORTED_MSG = (
    "Terminal does not support NN deals (Multisplit not enabled). "
    "Contact Tinkoff manager to enable Multisplit NN on the test terminal."
)


@pytest.fixture()
async def tinkoff_test_client() -> TinkoffAPIClient:
    """Real Tinkoff API client pointing to test environment.

    Function-scoped to avoid 'Event loop is closed' errors across tests.
    """
    return TinkoffAPIClient(
        password=settings.TINKOFF.PASSWORD,
        terminal_key=settings.TINKOFF.TERMINAL_KEY,
        terminal_key_e2c=settings.TINKOFF.TERMINAL_KEY_E2C,
        notification_url=settings.TINKOFF.NOTIFICATION_URL,
        use_test=True,
        debug_mode=True,
    )


@pytest.fixture()
async def tinkoff_uow(payment_session):
    """TinkoffUnitOfWork backed by a real DB session."""
    return TinkoffUnitOfWork(payment_session)


@pytest.fixture()
async def tinkoff_service_real(tinkoff_uow):
    """TinkoffService backed by real DB (Tinkoff API calls still go through the module-level client)."""
    return TinkoffService(tinkoff_uow)


@pytest.fixture()
async def created_nn_deal(tinkoff_test_client):
    """Create a real NN deal on Tinkoff test API, yield deal_id, close it after test.

    Skips the test automatically if the terminal does not support NN deals
    (error 256 — Multisplit NN must be enabled by Tinkoff on the terminal).
    """
    try:
        resp = await tinkoff_test_client.create_deal(deal_type="NN")
    except ValueError as e:
        if "256" in str(e) and "некорректный тип" in str(e).lower():
            pytest.skip(NN_UNSUPPORTED_MSG)
        raise
    assert resp.success
    deal_id = resp.deal_id

    yield deal_id

    # Cleanup: close the deal
    try:
        await tinkoff_test_client.close_deal(deal_id)
    except Exception:
        pass  # Best-effort cleanup
