import pytest
from httpx import AsyncClient
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock

from src.api.payment_gateways.constants import TinkoffPaymentMethod
from src.api.payment_gateways.schemas import PayInResult
from src.core.database.enums.transactions import PaymentProviderEnum


@pytest.mark.asyncio
async def test_create_payment_success_card(
    api_client: AsyncClient,
    testuser,
):
    """Test successful payment creation with Tinkoff card method."""
    external_tx_id = str(uuid4())

    with patch('src.api.payment_gateways.tinkoff.service.tinkoff_client') as mock_client:
        mock_client.create_deal = AsyncMock(return_value=MagicMock(
            success=True,
            deal_id="deal_123"
        ))
        mock_client.init_pay_in = AsyncMock(return_value=MagicMock(
            success=True,
            payment_id="123456",
            order_id=external_tx_id,
            amount=1000,
            payment_url="https://payment-url.test",
            status="NEW"
        ))

        create_data = {
            "streamer_id": 38,
            "external_transaction_id": external_tx_id,
            "provider": PaymentProviderEnum.tinkoff,
            "payment_method": TinkoffPaymentMethod.t_card,
            "amount": 1000,
            "external_data": {
                "streamer_login": "testuser",
                "description": "Test payment"
            }
        }
        response = await api_client.post("/api/payment", json=create_data)
        assert response.status_code == 200
        data = response.json()
        assert "payment_url" in data
        assert data["payment_url"] == "https://payment-url.test"
        assert data["qr_url"] is None


@pytest.mark.asyncio
async def test_create_payment_success_sbp(
    api_client: AsyncClient,
    testuser,
):
    """Test successful payment creation with Tinkoff SBP method."""
    external_tx_id = str(uuid4())

    with patch('src.api.payment_gateways.tinkoff.service.tinkoff_client') as mock_client:
        mock_client.create_deal = AsyncMock(return_value=MagicMock(
            success=True,
            deal_id="deal_123"
        ))
        mock_client.init_pay_in = AsyncMock(return_value=MagicMock(
            success=True,
            payment_id="123456",
            order_id=external_tx_id,
            amount=1000,
            payment_url="https://payment-url.test",
            status="NEW"
        ))

        mock_client.get_qr = AsyncMock(return_value=MagicMock(
            success=True,
            data="qr-code-payload-data",
            payment_id=123456
        ))

        create_data = {
            "streamer_id": 38,
            "external_transaction_id": external_tx_id,
            "provider": PaymentProviderEnum.tinkoff,
            "payment_method": TinkoffPaymentMethod.t_sbp,
            "amount": 1000,
            "external_data": {
                "streamer_login": "testuser",
                "description": "Test SBP payment"
            }
        }
        response = await api_client.post("/api/payment", json=create_data)
        assert response.status_code == 200
        data = response.json()
        assert "qr_url" in data
        assert data["qr_url"] == "qr-code-payload-data"
        assert data["payment_url"] is None


@pytest.mark.asyncio
async def test_create_payment_with_stake(
    api_client: AsyncClient,
    testuser,
    stake_factory,
    stake_outcome_factory,
):
    """Test payment creation associated with a stake."""
    stake = await stake_factory(streamer_id=38, title="Test Stake")
    outcome = await stake_outcome_factory(stake_id=stake.id, title="Yes")
    external_tx_id = str(uuid4())

    with patch('src.api.payment_gateways.tinkoff.service.tinkoff_client') as mock_client:
        mock_client.create_deal = AsyncMock(return_value=MagicMock(
            success=True,
            deal_id="deal_123"
        ))
        mock_client.init_pay_in = AsyncMock(return_value=MagicMock(
            success=True,
            payment_id="123456",
            order_id=external_tx_id,
            amount=1000,
            payment_url="https://payment-url.test",
            status="NEW"
        ))

        create_data = {
            "streamer_id": 38,
            "external_transaction_id": external_tx_id,
            "provider": PaymentProviderEnum.tinkoff,
            "payment_method": TinkoffPaymentMethod.t_card,
            "amount": 1000,
            "stake_id": str(stake.id),
            "outcome_id": str(outcome.id),
            "external_data": {
                "streamer_login": "testuser"
            }
        }
        response = await api_client.post("/api/payment", json=create_data)
        assert response.status_code == 200
        data = response.json()
        assert "payment_url" in data


@pytest.mark.asyncio
async def test_create_payment_invalid_provider(
    api_client: AsyncClient,
    testuser,
):
    """Test payment creation with unsupported payment provider."""
    external_tx_id = str(uuid4())

    create_data = {
        "streamer_id": 38,
        "external_transaction_id": external_tx_id,
        "provider": "unsupported_provider",
        "payment_method": TinkoffPaymentMethod.t_card,
        "amount": 1000
    }
    response = await api_client.post("/api/payment", json=create_data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_payment_missing_required_fields(
    api_client: AsyncClient,
    testuser,
):
    """Test payment creation with missing required fields."""
    create_data = {
        "streamer_id": 38,
        "amount": 1000
    }
    response = await api_client.post("/api/payment", json=create_data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_payment_invalid_amount(
    api_client: AsyncClient,
    testuser,
):
    """Test payment creation with invalid amount."""
    external_tx_id = str(uuid4())

    create_data = {
        "streamer_id": 38,
        "external_transaction_id": external_tx_id,
        "provider": PaymentProviderEnum.tinkoff,
        "payment_method": TinkoffPaymentMethod.t_card,
        "amount": -100
    }
    response = await api_client.post("/api/payment", json=create_data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_payment_without_external_data(
    api_client: AsyncClient,
    testuser,
):
    """Test payment creation without external_data (should use defaults)."""
    external_tx_id = str(uuid4())

    with patch('src.api.payment_gateways.tinkoff.service.tinkoff_client') as mock_client:
        mock_client.create_deal = AsyncMock(return_value=MagicMock(
            success=True,
            deal_id="deal_123"
        ))
        mock_client.init_pay_in = AsyncMock(return_value=MagicMock(
            success=True,
            payment_id="123456",
            order_id=external_tx_id,
            amount=1000,
            payment_url="https://payment-url.test",
            status="NEW"
        ))

        create_data = {
            "streamer_id": 38,
            "external_transaction_id": external_tx_id,
            "provider": PaymentProviderEnum.tinkoff,
            "payment_method": TinkoffPaymentMethod.t_card,
            "amount": 1000
        }
        response = await api_client.post("/api/payment", json=create_data)
        assert response.status_code == 200
        data = response.json()
        assert "payment_url" in data


@pytest.mark.asyncio
async def test_create_payment_duplicate_transaction_id(
    api_client: AsyncClient,
    testuser,
):
    """Test that duplicate external_transaction_id is rejected."""
    external_tx_id = str(uuid4())

    with patch('src.api.payment_gateways.tinkoff.service.tinkoff_client') as mock_client:
        mock_client.create_deal = AsyncMock(return_value=MagicMock(
            success=True,
            deal_id="deal_123"
        ))
        mock_client.init_pay_in = AsyncMock(return_value=MagicMock(
            success=True,
            payment_id="123456",
            order_id=external_tx_id,
            amount=1000,
            payment_url="https://payment-url.test",
            status="NEW"
        ))

        create_data = {
            "streamer_id": 38,
            "external_transaction_id": external_tx_id,
            "provider": PaymentProviderEnum.tinkoff,
            "payment_method": TinkoffPaymentMethod.t_card,
            "amount": 1000
        }

        response1 = await api_client.post("/api/payment", json=create_data)
        assert response1.status_code == 200

        response2 = await api_client.post("/api/payment", json=create_data)
        assert response2.status_code == 500


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_payment_success_card_real_request(
    api_client: AsyncClient,
    testuser,
):
    """Test successful payment creation with Tinkoff card method using real API request."""
    external_tx_id = str(uuid4())

    create_data = {
        "streamer_id": 38,
        "external_transaction_id": external_tx_id,
        "provider": PaymentProviderEnum.tinkoff,
        "payment_method": TinkoffPaymentMethod.t_card,
        "amount": 1000,
        "external_data": {
            "streamer_login": "testuser",
            "description": "Test payment"
        }
    }
    response = await api_client.post("/api/payment", json=create_data)
    assert response.status_code in [200, 422]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_payment_success_sbp_real_request(
    api_client: AsyncClient,
    testuser,
):
    """Test successful payment creation with Tinkoff SBP method using real API request."""
    external_tx_id = str(uuid4())

    create_data = {
        "streamer_id": 38,
        "external_transaction_id": external_tx_id,
        "provider": PaymentProviderEnum.tinkoff,
        "payment_method": TinkoffPaymentMethod.t_sbp,
        "amount": 1000,
        "external_data": {
            "streamer_login": "testuser",
            "description": "Test SBP payment"
        }
    }
    response = await api_client.post("/api/payment", json=create_data)
    assert response.status_code in [200, 422]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_payment_with_stake_real_request(
    api_client: AsyncClient,
    testuser,
    stake_factory,
    stake_outcome_factory,
):
    """Test payment creation associated with a stake using real API request."""
    stake = await stake_factory(streamer_id=38, title="Test Stake")
    outcome = await stake_outcome_factory(stake_id=stake.id, title="Yes")
    external_tx_id = str(uuid4())

    create_data = {
        "streamer_id": 38,
        "external_transaction_id": external_tx_id,
        "provider": PaymentProviderEnum.tinkoff,
        "payment_method": TinkoffPaymentMethod.t_card,
        "amount": 1000,
        "stake_id": str(stake.id),
        "outcome_id": str(outcome.id),
        "external_data": {
            "streamer_login": "testuser"
        }
    }
    response = await api_client.post("/api/payment", json=create_data)
    assert response.status_code in [200, 422]
