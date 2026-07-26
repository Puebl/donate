import pytest
from unittest.mock import AsyncMock, MagicMock

from src.api.payment_gateways.tinkoff.client.service import TinkoffAPIClient


@pytest.fixture
def client():
    return TinkoffAPIClient(
        password="test_password",
        terminal_key="test_terminal",
        terminal_key_e2c="test_terminal_e2c",
        notification_url="https://test.com/notification",
        debug_mode=False,
        use_test=True,
    )


@pytest.fixture
def mock_post():
    """Mock httpx post to return a successful response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    return mock_response


class TestCreateDeal:
    async def test_create_deal_nn(self, client, mock_post):
        """Verifies create_deal sends SpDealType: NN by default"""
        mock_post.json.return_value = {
            "SpAccumulationId": "123",
            "Success": True,
            "ErrorCode": "0",
        }
        client.client.post = AsyncMock(return_value=mock_post)

        result = await client.create_deal()
        call_body = client.client.post.call_args[1]["json"]
        assert call_body["SpDealType"] == "NN"
        assert result.deal_id == "123"

    async def test_create_deal_n1(self, client, mock_post):
        """Verifies create_deal with explicit N1 type"""
        mock_post.json.return_value = {
            "SpAccumulationId": "456",
            "Success": True,
            "ErrorCode": "0",
        }
        client.client.post = AsyncMock(return_value=mock_post)

        result = await client.create_deal(deal_type="N1")
        call_body = client.client.post.call_args[1]["json"]
        assert call_body["SpDealType"] == "N1"


class TestCloseDeal:
    async def test_close_deal(self, client, mock_post):
        """Verifies close_deal sends SpAccumulationId"""
        mock_post.json.return_value = {"Success": True, "ErrorCode": "0"}
        client.client.post = AsyncMock(return_value=mock_post)

        await client.close_deal("deal_123")
        call_body = client.client.post.call_args[1]["json"]
        assert call_body["SpAccumulationId"] == "deal_123"
        assert call_body["TerminalKey"] == "test_terminal"  # main terminal, not e2c


class TestInitPayOut:
    async def test_init_pay_out_partial(self, client, mock_post):
        """Verifies FinalPayout=False for partial payouts"""
        mock_post.json.return_value = {
            "PaymentId": "pay_1",
            "OrderId": "ord_1",
            "Amount": 500,
            "Status": "NEW",
            "Success": True,
            "ErrorCode": "0",
        }
        client.client.post = AsyncMock(return_value=mock_post)

        await client.init_pay_out(
            order_id="ord_1",
            deal_id="deal_1",
            amount=500,
            card_id="card_1",
            final_payout=False,
        )
        call_body = client.client.post.call_args[1]["json"]
        assert call_body["FinalPayout"] is False

    async def test_init_pay_out_final(self, client, mock_post):
        """Verifies FinalPayout=True when explicitly set"""
        mock_post.json.return_value = {
            "PaymentId": "pay_1",
            "OrderId": "ord_1",
            "Amount": 500,
            "Status": "NEW",
            "Success": True,
            "ErrorCode": "0",
        }
        client.client.post = AsyncMock(return_value=mock_post)

        await client.init_pay_out(
            order_id="ord_1",
            deal_id="deal_1",
            amount=500,
            card_id="card_1",
            final_payout=True,
        )
        call_body = client.client.post.call_args[1]["json"]
        assert call_body["FinalPayout"] is True

    async def test_init_pay_out_with_recipient_id(self, client, mock_post):
        """Verifies PaymentRecipientId is sent when provided"""
        mock_post.json.return_value = {
            "PaymentId": "pay_1",
            "OrderId": "ord_1",
            "Amount": 500,
            "Status": "NEW",
            "Success": True,
            "ErrorCode": "0",
        }
        client.client.post = AsyncMock(return_value=mock_post)

        await client.init_pay_out(
            order_id="ord_1",
            deal_id="deal_1",
            amount=500,
            card_id="card_1",
            payment_recipient_id="42",
        )
        call_body = client.client.post.call_args[1]["json"]
        assert call_body["PaymentRecipientId"] == "42"


class TestInitPayIn:
    async def test_init_pay_in_with_recipient_id(self, client, mock_post):
        """Verifies PaymentRecipientId is sent in pay-in Init"""
        mock_post.json.return_value = {
            "PaymentId": "pay_1",
            "OrderId": "ord_1",
            "Amount": 1000,
            "PaymentURL": "https://pay.url",
            "Status": "NEW",
            "Success": True,
            "ErrorCode": "0",
        }
        client.client.post = AsyncMock(return_value=mock_post)

        await client.init_pay_in(
            order_id="ord_1",
            amount=1000,
            deal_id="deal_1",
            success_url="https://ok.url",
            payment_recipient_id="42",
        )
        call_body = client.client.post.call_args[1]["json"]
        assert call_body["PaymentRecipientId"] == "42"
