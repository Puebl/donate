import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from src.api.payment_gateways.tinkoff.client.service import TinkoffAPIClient
from src.api.payment_gateways.tinkoff.client.schemas import (
    TinkoffDealResponse,
    TinkoffInitResponse,
    TinkoffGetQrResponse,
    TinkoffPaymentResponse,
    TinkoffAddSellerResponse,
    TinkoffCardSchema,
    TinkoffGetCardListResponse,
    TinkoffAddCardResponse,
    BaseTinkoffResponse,
    TinkoffSbpMembersResponse,
    SbpMemberSchema
)


@pytest.fixture
def tinkoff_client():
    """Create a TinkoffAPIClient instance for testing."""
    client = TinkoffAPIClient(
        password="test_password",
        terminal_key="test_terminal",
        terminal_key_e2c="test_terminal_e2c",
        notification_url="https://test.com/notify",
        use_test=True
    )
    return client


@pytest.mark.asyncio
async def test_create_deal_success(tinkoff_client):
    """Test successful deal creation."""
    mock_response = {
        "Success": True,
        "ErrorCode": "0",
        "SpAccumulationId": "deal_123"
    }

    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response
        )

        result = await tinkoff_client.create_deal()

        assert isinstance(result, TinkoffDealResponse)
        assert result.deal_id == "deal_123"
        assert result.success is True
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_create_deal_failure(tinkoff_client):
    """Test deal creation with error response."""
    mock_response = {
        "Success": False,
        "ErrorCode": "101",
        "Message": "Deal creation failed",
        "Details": "Invalid terminal key"
    }

    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response
        )

        with pytest.raises(ValueError, match="101"):
            await tinkoff_client.create_deal()


@pytest.mark.asyncio
async def test_init_pay_in_success(tinkoff_client):
    """Test successful payment initialization for pay-in."""
    mock_response = {
        "Success": True,
        "ErrorCode": "0",
        "PaymentId": "payment_123",
        "OrderId": "order_123",
        "Amount": 1000,
        "Status": "NEW",
        "PaymentURL": "https://payment-url.test"
    }

    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response
        )

        result = await tinkoff_client.init_pay_in(
            order_id="order_123",
            amount=1000,
            deal_id="deal_123",
            success_url="https://success.test",
            description="Test payment",
            customer_key="customer_123",
            data={"key": "value"}
        )

        assert isinstance(result, TinkoffInitResponse)
        assert result.payment_id == "payment_123"
        assert result.payment_url == "https://payment-url.test"
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_get_qr_success(tinkoff_client):
    """Test successful QR code retrieval."""
    mock_response = {
        "Success": True,
        "ErrorCode": "0",
        "Data": "qr-payload-data",
        "PaymentId": 123456
    }

    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response
        )

        result = await tinkoff_client.get_qr(payment_id="123456")

        assert isinstance(result, TinkoffGetQrResponse)
        assert result.data == "qr-payload-data"
        assert result.payment_id == 123456


@pytest.mark.asyncio
async def test_get_qr_failure(tinkoff_client):
    """Test QR code retrieval with error."""
    mock_response = {
        "Success": False,
        "ErrorCode": "102",
        "Message": "QR generation failed"
    }

    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response
        )

        with pytest.raises(ValueError, match="102"):
            await tinkoff_client.get_qr(payment_id="123456")


@pytest.mark.asyncio
async def test_init_pay_out_with_card_success(tinkoff_client):
    """Test successful payout initialization with card ID."""
    mock_response = {
        "Success": True,
        "ErrorCode": "0",
        "PaymentId": "payout_123",
        "OrderId": "order_456",
        "Amount": 500,
        "Status": "NEW"
    }

    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response
        )

        result = await tinkoff_client.init_pay_out(
            order_id="order_456",
            deal_id="deal_123",
            amount=500,
            card_id="card_789"
        )

        assert isinstance(result, TinkoffInitResponse)
        assert result.payment_id == "payout_123"


@pytest.mark.asyncio
async def test_init_pay_out_with_sbp_success(tinkoff_client):
    """Test successful payout initialization with SBP."""
    mock_response = {
        "Success": True,
        "ErrorCode": "0",
        "PaymentId": "payout_123",
        "OrderId": "order_456",
        "Amount": 500,
        "Status": "NEW"
    }

    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response
        )

        result = await tinkoff_client.init_pay_out(
            order_id="order_456",
            deal_id="deal_123",
            amount=500,
            phone="+79001234567",
            sbp_member_id="member_123"
        )

        assert isinstance(result, TinkoffInitResponse)
        assert result.payment_id == "payout_123"


@pytest.mark.asyncio
async def test_init_pay_out_without_destination(tinkoff_client):
    """Test payout initialization fails without card ID or phone+SBP."""
    with pytest.raises(ValueError, match="Destination.*is required"):
        await tinkoff_client.init_pay_out(
            order_id="order_456",
            deal_id="deal_123",
            amount=500
        )


@pytest.mark.asyncio
async def test_confirm_payout_success(tinkoff_client):
    """Test successful payout confirmation."""
    mock_response = {
        "Success": True,
        "ErrorCode": "0",
        "PaymentId": "payout_123",
        "OrderId": "order_456",
        "Amount": 500,
        "Status": "CONFIRMED"
    }

    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response
        )

        result = await tinkoff_client.confirm_payout(payment_id="payout_123")

        assert isinstance(result, TinkoffPaymentResponse)
        assert result.payment_id == "payout_123"
        assert result.status == "CONFIRMED"


@pytest.mark.asyncio
async def test_add_seller_success(tinkoff_client):
    """Test successful seller addition."""
    mock_response = {
        "Success": True,
        "ErrorCode": "0",
        "TerminalKey": "test_terminal_e2c",
        "CustomerKey": "seller_123"
    }

    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response
        )

        result = await tinkoff_client.add_seller(
            seller_id="seller_123",
            email="test@example.com"
        )

        assert result.CustomerKey == "seller_123"


@pytest.mark.asyncio
async def test_get_seller_cards_success(tinkoff_client):
    """Test successful retrieval of seller cards."""
    mock_response = {
        "Success": True,
        "ErrorCode": "0",
        "CardList": [
            {
                "CardId": "card_1",
                "Pan": "****1234",
                "Status": "ACTIVE",
                "RebillId": "rebill_1",
                "CardType": 1
            },
            {
                "CardId": "card_2",
                "Pan": "****5678",
                "Status": "ACTIVE",
                "RebillId": "rebill_2",
                "CardType": 2
            }
        ]
    }

    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response
        )

        result = await tinkoff_client.get_seller_cards(seller_id="seller_123")

        assert len(result) == 2
        assert all(isinstance(card, TinkoffCardSchema) for card in result)
        assert result[0].card_id == "card_1"
        assert result[1].card_id == "card_2"


@pytest.mark.asyncio
async def test_get_seller_cards_as_list(tinkoff_client):
    """Test seller cards when response is a list (edge case)."""
    mock_response = [
        {
            "CardId": "card_1",
            "Pan": "****1234",
            "Status": "ACTIVE",
            "RebillId": "rebill_1",
            "CardType": 1
        }
    ]

    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response
        )

        result = await tinkoff_client.get_seller_cards(seller_id="seller_123")

        assert len(result) == 1
        assert isinstance(result[0], TinkoffCardSchema)


@pytest.mark.asyncio
async def test_add_seller_card_success(tinkoff_client):
    """Test successful seller card addition."""
    mock_response = {
        "Success": True,
        "ErrorCode": "0",
        "PaymentId": 123456,
        "TerminalKey": "test_terminal_e2c",
        "CustomerKey": "seller_123",
        "PaymentURL": "https://add-card.test",
        "RequestKey": "request_key_123"
    }

    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response
        )

        result = await tinkoff_client.add_seller_card(
            seller_id="seller_123",
            check_type="NO"
        )

        assert isinstance(result, TinkoffAddCardResponse)
        assert result.payment_url == "https://add-card.test"
        assert result.request_key == "request_key_123"


@pytest.mark.asyncio
async def test_remove_seller_card_success(tinkoff_client):
    """Test successful seller card removal."""
    mock_response = {
        "Success": True,
        "ErrorCode": "0"
    }

    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response
        )

        result = await tinkoff_client.remove_seller_card(
            seller_id="seller_123",
            card_id="card_123"
        )

        assert isinstance(result, BaseTinkoffResponse)
        assert result.success is True


@pytest.mark.asyncio
async def test_get_sbp_members_success(tinkoff_client):
    """Test successful SBP members retrieval."""
    mock_response = {
        "Success": True,
        "ErrorCode": "0",
        "Members": [
            {
                "MemberID": "100000000001",
                "MemberName": "Sberbank",
                "MemberNameRus": "Сбер"
            },
            {
                "MemberID": "100000000002",
                "MemberName": "VTB",
                "MemberNameRus": "ВТБ"
            }
        ]
    }

    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response
        )

        result = await tinkoff_client.get_sbp_members()

        assert isinstance(result, TinkoffSbpMembersResponse)
        assert len(result.members) == 2
        assert all(isinstance(member, SbpMemberSchema) for member in result.members)


@pytest.mark.asyncio
async def test_get_state_success(tinkoff_client):
    """Test successful payment state retrieval."""
    mock_response = {
        "Success": True,
        "ErrorCode": "0",
        "PaymentId": "payment_123",
        "OrderId": "order_123",
        "Amount": 1000,
        "Status": "COMPLETED"
    }

    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response
        )

        result = await tinkoff_client.get_state(
            payment_id="payment_123",
            ip="192.168.1.1",
            is_payout=False
        )

        assert isinstance(result, TinkoffPaymentResponse)
        assert result.status == "COMPLETED"


@pytest.mark.asyncio
async def test_get_state_payout_mode(tinkoff_client):
    """Test payment state retrieval in payout mode."""
    mock_response = {
        "Success": True,
        "ErrorCode": "0",
        "PaymentId": "payout_123",
        "OrderId": "order_456",
        "Amount": 500,
        "Status": "CONFIRMED"
    }

    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response
        )

        result = await tinkoff_client.get_state(
            payment_id="payout_123",
            is_payout=True
        )

        assert isinstance(result, TinkoffPaymentResponse)
        assert result.status == "CONFIRMED"


@pytest.mark.asyncio
async def test_http_status_error(tinkoff_client):
    """Test handling of HTTP status errors."""
    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.HTTPStatusError(
            "Server error",
            request=MagicMock(),
            response=MagicMock(status_code=500)
        )

        with pytest.raises(httpx.HTTPStatusError):
            await tinkoff_client.create_deal()


@pytest.mark.asyncio
async def test_network_error(tinkoff_client):
    """Test handling of network errors."""
    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Network error")

        with pytest.raises(httpx.ConnectError):
            await tinkoff_client.create_deal()


@pytest.mark.asyncio
async def test_close_client(tinkoff_client):
    """Test proper client closure."""
    with patch.object(tinkoff_client.client, 'aclose', new_callable=AsyncMock) as mock_close:
        await tinkoff_client.close()
        mock_close.assert_called_once()


def test_generate_token(tinkoff_client):
    """Test token generation with proper parameters."""
    request_body = {
        "TerminalKey": "test_terminal",
        "Amount": 1000,
        "OrderId": "order_123"
    }

    token = tinkoff_client._generate_token(request_body)

    assert isinstance(token, str)
    assert len(token) == 64  # SHA256 hex string length


def test_generate_token_with_ignored_fields(tinkoff_client):
    """Test token generation ignores certain fields."""
    request_body = {
        "TerminalKey": "test_terminal",
        "Amount": 1000,
        "Shops": [{"id": 1}],  # Should be ignored
        "Receipt": {"test": 1},  # Should be ignored
        "DATA": {"custom": 1},  # Should be ignored
        "Token": "old_token"  # Should be ignored
    }

    token = tinkoff_client._generate_token(request_body)

    assert isinstance(token, str)
    assert len(token) == 64


def test_generate_token_with_boolean(tinkoff_client):
    """Test token generation handles boolean values correctly."""
    request_body = {
        "TerminalKey": "test_terminal",
        "FinalPayout": True,
        "AnotherField": False
    }

    token = tinkoff_client._generate_token(request_body)

    assert isinstance(token, str)
    assert len(token) == 64


@pytest.mark.asyncio
async def test_init_pay_in_without_customer_key(tinkoff_client):
    """Test payment initialization without customer key."""
    mock_response = {
        "Success": True,
        "ErrorCode": "0",
        "PaymentId": "payment_123",
        "OrderId": "order_123",
        "Amount": 1000,
        "Status": "NEW",
        "PaymentURL": "https://payment-url.test"
    }

    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response
        )

        result = await tinkoff_client.init_pay_in(
            order_id="order_123",
            amount=1000,
            deal_id="deal_123",
            success_url="https://success.test",
            description="Test payment"
        )

        assert isinstance(result, TinkoffInitResponse)
        assert result.payment_id == "payment_123"


@pytest.mark.asyncio
async def test_init_pay_in_without_optional_data(tinkoff_client):
    """Test payment initialization without optional data field."""
    mock_response = {
        "Success": True,
        "ErrorCode": "0",
        "PaymentId": "payment_123",
        "OrderId": "order_123",
        "Amount": 1000,
        "Status": "NEW",
        "PaymentURL": "https://payment-url.test"
    }

    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response
        )

        result = await tinkoff_client.init_pay_in(
            order_id="order_123",
            amount=1000,
            deal_id="deal_123",
            success_url="https://success.test",
            description="Test payment",
            customer_key="customer_123"
        )

        assert isinstance(result, TinkoffInitResponse)


@pytest.mark.asyncio
async def test_init_pay_out_with_both_card_and_sbp(tinkoff_client):
    """Test payout initialization prioritizes card_id over phone+SBP."""
    mock_response = {
        "Success": True,
        "ErrorCode": "0",
        "PaymentId": "payout_123",
        "OrderId": "order_456",
        "Amount": 500,
        "Status": "NEW"
    }

    with patch.object(tinkoff_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_response
        )

        result = await tinkoff_client.init_pay_out(
            order_id="order_456",
            deal_id="deal_123",
            amount=500,
            card_id="card_789",
            phone="+79001234567",
            sbp_member_id="member_123"
        )

        assert isinstance(result, TinkoffInitResponse)

        called_body = mock_post.call_args[1]['json']
        assert 'CardId' in called_body
        assert 'Phone' not in called_body
        assert 'SbpMemberId' not in called_body
