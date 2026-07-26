import pytest
from unittest.mock import AsyncMock, MagicMock

from src.api.payment_gateways.tinkoff.client.service import TinkoffAPIClient
from src.api.payment_gateways.tinkoff.client.schemas import (
    TinkoffDealResponse,
    TinkoffInitResponse,
    TinkoffGetQrResponse,
    TinkoffPaymentResponse,
    TinkoffAddSellerResponse,
    TinkoffCardSchema,
    TinkoffAddCardResponse,
    BaseTinkoffResponse,
    TinkoffSbpMembersResponse
)


@pytest.fixture
def mock_tinkoff_client():
    """Create a mocked TinkoffAPIClient instance for testing."""
    client = TinkoffAPIClient(
        password="test_password",
        terminal_key="test_terminal",
        terminal_key_e2c="test_terminal_e2c",
        notification_url="https://test.com/notify",
        use_test=True
    )

    client.client = MagicMock()
    client.client.post = AsyncMock()
    client.close = AsyncMock()

    return client


@pytest.fixture
def tinkoff_deal_response_mock():
    """Mock successful Tinkoff deal creation response."""
    return {
        "Success": True,
        "ErrorCode": "0",
        "SpAccumulationId": "deal_123456"
    }


@pytest.fixture
def tinkoff_init_response_mock():
    """Mock successful Tinkoff payment initialization response."""
    return {
        "Success": True,
        "ErrorCode": "0",
        "PaymentId": "payment_789",
        "OrderId": "order_123",
        "Amount": 1000,
        "Status": "NEW",
        "PaymentURL": "https://securepay.tinkoff.ru/payment"
    }


@pytest.fixture
def tinkoff_qr_response_mock():
    """Mock successful Tinkoff QR code generation response."""
    return {
        "Success": True,
        "ErrorCode": "0",
        "Data": "qr-payload-base64-encoded",
        "PaymentId": 123456
    }


@pytest.fixture
def tinkoff_payment_response_mock():
    """Mock successful Tinkoff payment response."""
    return {
        "Success": True,
        "ErrorCode": "0",
        "PaymentId": "payment_456",
        "OrderId": "order_789",
        "Amount": 500,
        "Status": "COMPLETED"
    }


@pytest.fixture
def tinkoff_add_seller_response_mock():
    """Mock successful Tinkoff seller addition response."""
    return {
        "Success": True,
        "ErrorCode": "0",
        "TerminalKey": "test_terminal_e2c",
        "CustomerKey": "seller_123"
    }


@pytest.fixture
def tinkoff_card_list_response_mock():
    """Mock successful Tinkoff card list response."""
    return {
        "Success": True,
        "ErrorCode": "0",
        "CardList": [
            {
                "CardId": "card_1",
                "Pan": "424200******1234",
                "Status": "A",
                "RebillId": "rebill_abc123",
                "CardType": 0
            },
            {
                "CardId": "card_2",
                "Pan": "555900******5678",
                "Status": "A",
                "RebillId": "rebill_xyz789",
                "CardType": 0
            }
        ]
    }


@pytest.fixture
def tinkoff_add_card_response_mock():
    """Mock successful Tinkoff card addition response."""
    return {
        "Success": True,
        "ErrorCode": "0",
        "PaymentId": 999999,
        "TerminalKey": "test_terminal_e2c",
        "CustomerKey": "seller_123",
        "PaymentURL": "https://securepay.tinkoff.ru/add-card",
        "RequestKey": "req_key_12345"
    }


@pytest.fixture
def tinkoff_base_response_mock():
    """Mock successful base Tinkoff response."""
    return {
        "Success": True,
        "ErrorCode": "0"
    }


@pytest.fixture
def tinkoff_sbp_members_response_mock():
    """Mock successful Tinkoff SBP members response."""
    return {
        "Success": True,
        "ErrorCode": "0",
        "Members": [
            {
                "MemberID": "100000000001",
                "MemberName": "Sberbank"
            },
            {
                "MemberID": "100000000007",
                "MemberName": "VTB"
            },
            {
                "MemberID": "100000000010",
                "MemberName": "Alfa-Bank"
            }
        ]
    }


@pytest.fixture
def tinkoff_error_response_mock():
    """Mock Tinkoff error response."""
    return {
        "Success": False,
        "ErrorCode": "101",
        "Message": "Invalid terminal key",
        "Details": "Terminal key not found"
    }


@pytest.fixture
def tinkoff_http_error_mock():
    """Mock HTTP error response from Tinkoff API."""
    def create_error_response(status_code=500):
        response = MagicMock()
        response.status_code = status_code
        response.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
        response.json.return_value = {"error": "Internal Server Error"}
        return response
    return create_error_response
