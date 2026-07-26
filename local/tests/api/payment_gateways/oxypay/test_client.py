import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from src.api.payment_gateways.oxypay.client.service import OxypayAPIClient


class TestOxypayAPIClient:
    @pytest.fixture
    def client(self):
        return OxypayAPIClient(
            merchant_key="test_merchant_key",
            base_url="https://api.test.oxypay.kz",
            callback_url="https://callback.test.com",
            debug_mode=False,
        )

    async def test_create_payment_request_format(self, client):
        """Should send correct request body to OxyPay API"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "token": "pay_tok_123",
            "processingUrl": "https://pay.oxypay.kz/test",
            "payment": {
                "amount": 5000,
                "currency": "KZT",
                "status": "init",
            },
            "errors": [],
        }

        client.client.post = AsyncMock(return_value=mock_response)

        await client.create_payment(
            amount=5000,
            currency="KZT",
            product="Донат для streamer",
            callback_url="https://callback.test.com/pay-in",
            redirect_success_url="https://success.test.com/donate/streamer",
            order_number="txn_001",
        )

        client.client.post.assert_called_once()
        call_kwargs = client.client.post.call_args
        body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")

        assert body["amount"] == 5000
        assert body["currency"] == "KZT"
        assert body["product"] == "Донат для streamer"
        assert body["callback_url"] == "https://callback.test.com/pay-in"
        assert (
            body["redirect_success_url"] == "https://success.test.com/donate/streamer"
        )
        assert body["order_number"] == "txn_001"

    async def test_bearer_auth_header(self, client):
        """Should include Bearer token in Authorization header"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "token": "pay_tok_456",
            "processingUrl": "https://pay.oxypay.kz/test2",
            "payment": {
                "amount": 1000,
                "currency": "KZT",
                "status": "init",
            },
            "errors": [],
        }

        client.client.post = AsyncMock(return_value=mock_response)

        await client.create_payment(
            amount=1000,
            currency="KZT",
            product="Test",
            callback_url="https://callback.test.com/pay-in",
            redirect_success_url="https://success.test.com",
            order_number="txn_002",
        )

        call_kwargs = client.client.post.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")

        assert headers["Authorization"] == "Bearer test_merchant_key"
        assert headers["Content-Type"] == "application/json"

    async def test_create_payout_request_format(self, client):
        """Should send correct payout request body"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "payout": {
                "id": 42,
                "amount": 3000,
                "currency": "KZT",
                "status": "accepted",
            },
            "errors": [],
        }

        client.client.post = AsyncMock(return_value=mock_response)

        await client.create_payout(
            amount=3000,
            currency="KZT",
            card_number="4111111111111111",
            order_id="payout_001",
        )

        call_kwargs = client.client.post.call_args
        body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")

        assert body["amount"] == 3000
        assert body["currency"] == "KZT"
        assert body["card_number"] == "4111111111111111"
        assert body["order_id"] == "payout_001"
