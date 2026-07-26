import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.api.payment_gateways.oxypay.service import OxypayService
from src.api.payment_gateways.oxypay.exceptions import OxypayPaymentInitializationError
from src.api.payment_gateways.oxypay.client.schemas import (
    OxypayCreatePaymentResponse,
    OxypayPaymentInfo,
    OxypayPayoutResponse,
    OxypayPayoutInfo,
)
from src.api.payment_gateways.schemas import PayInResult, PayoutResult
from src.core.database.enums.transactions import TransactionStatusEnum


class TestMakePayIn:
    async def test_make_pay_in_success(self, oxypay_service):
        """Successful pay-in should return PayInResult with payment_url"""
        mock_response = OxypayCreatePaymentResponse(
            success=True,
            token="tok_abc",
            processingUrl="https://pay.oxypay.kz/test",
            payment=OxypayPaymentInfo(amount=5000, currency="KZT", status="init"),
            errors=[],
        )

        mock_settings = MagicMock()
        mock_settings.OXYPAY.CURRENCY = "KZT"
        mock_settings.OXYPAY.CALLBACK_URL = "https://callback.test.com"
        mock_settings.OXYPAY.SUCCESS_URL_BASE = "https://success.test.com"

        with (
            patch(
                "src.api.payment_gateways.oxypay.service.oxypay_client"
            ) as mock_client,
            patch("src.api.payment_gateways.oxypay.service.settings", mock_settings),
        ):
            mock_client.create_payment = AsyncMock(return_value=mock_response)

            result = await oxypay_service.make_pay_in(
                streamer_id=1,
                amount=5000,
                external_data={"external_data": {"streamer_login": "test_streamer"}},
                external_transaction_id="txn_001",
                payment_method="card",
            )

        assert isinstance(result, PayInResult)
        assert result.payment_url == "https://pay.oxypay.kz/test"
        assert result.qr_url is None

    async def test_make_pay_in_failure(self, oxypay_service):
        """Failed pay-in should raise OxypayPaymentInitializationError"""
        mock_response = OxypayCreatePaymentResponse(
            success=False,
            token="tok_fail",
            processingUrl="",
            payment=OxypayPaymentInfo(amount=5000, currency="KZT", status="init"),
            errors=["error"],
        )

        mock_settings = MagicMock()
        mock_settings.OXYPAY.CURRENCY = "KZT"
        mock_settings.OXYPAY.CALLBACK_URL = "https://callback.test.com"
        mock_settings.OXYPAY.SUCCESS_URL_BASE = "https://success.test.com"

        with (
            patch(
                "src.api.payment_gateways.oxypay.service.oxypay_client"
            ) as mock_client,
            patch("src.api.payment_gateways.oxypay.service.settings", mock_settings),
        ):
            mock_client.create_payment = AsyncMock(return_value=mock_response)

            with pytest.raises(OxypayPaymentInitializationError):
                await oxypay_service.make_pay_in(
                    streamer_id=1,
                    amount=5000,
                    external_data={
                        "external_data": {"streamer_login": "test_streamer"}
                    },
                    external_transaction_id="txn_002",
                    payment_method="card",
                )

    async def test_make_pay_in_processing_url_list(self, oxypay_service):
        """When processingUrl is a list, should use first element"""
        mock_response = OxypayCreatePaymentResponse(
            success=True,
            token="tok_list",
            processingUrl=[
                "https://pay.oxypay.kz/first",
                "https://pay.oxypay.kz/second",
            ],
            payment=OxypayPaymentInfo(amount=3000, currency="KZT", status="init"),
            errors=[],
        )

        mock_settings = MagicMock()
        mock_settings.OXYPAY.CURRENCY = "KZT"
        mock_settings.OXYPAY.CALLBACK_URL = "https://callback.test.com"
        mock_settings.OXYPAY.SUCCESS_URL_BASE = "https://success.test.com"

        with (
            patch(
                "src.api.payment_gateways.oxypay.service.oxypay_client"
            ) as mock_client,
            patch("src.api.payment_gateways.oxypay.service.settings", mock_settings),
        ):
            mock_client.create_payment = AsyncMock(return_value=mock_response)

            result = await oxypay_service.make_pay_in(
                streamer_id=1,
                amount=3000,
                external_data={"external_data": {"streamer_login": "streamer2"}},
                external_transaction_id="txn_003",
                payment_method="card",
            )

        assert result.payment_url == "https://pay.oxypay.kz/first"


class TestMakePayOut:
    async def test_make_pay_out_success(self, oxypay_service):
        """Successful payout should return PayoutResult with completed status"""
        mock_response = OxypayPayoutResponse(
            success=True,
            payout=OxypayPayoutInfo(
                id=1, amount=5000, currency="KZT", status="accepted"
            ),
            errors=[],
        )

        mock_settings = MagicMock()
        mock_settings.OXYPAY.CURRENCY = "KZT"

        method_data = MagicMock()
        method_data.card_number = "4111111111111111"

        with (
            patch(
                "src.api.payment_gateways.oxypay.service.oxypay_client"
            ) as mock_client,
            patch("src.api.payment_gateways.oxypay.service.settings", mock_settings),
        ):
            mock_client.create_payout = AsyncMock(return_value=mock_response)

            result = await oxypay_service.make_pay_out(
                streamer_id=1,
                amount=5000,
                external_transaction_id="txn_004",
                method_data=method_data,
            )

        assert isinstance(result, PayoutResult)
        assert result.status == TransactionStatusEnum.completed
        assert result.payout_id == "1"
        assert result.error_message is None

    async def test_make_pay_out_failure(self, oxypay_service):
        """Failed payout should return PayoutResult with failed status"""
        mock_response = OxypayPayoutResponse(
            success=False,
            payout=None,
            errors=["insufficient funds"],
        )

        mock_settings = MagicMock()
        mock_settings.OXYPAY.CURRENCY = "KZT"

        method_data = MagicMock()
        method_data.card_number = "4111111111111111"

        with (
            patch(
                "src.api.payment_gateways.oxypay.service.oxypay_client"
            ) as mock_client,
            patch("src.api.payment_gateways.oxypay.service.settings", mock_settings),
        ):
            mock_client.create_payout = AsyncMock(return_value=mock_response)

            result = await oxypay_service.make_pay_out(
                streamer_id=1,
                amount=5000,
                external_transaction_id="txn_005",
                method_data=method_data,
            )

        assert isinstance(result, PayoutResult)
        assert result.status == TransactionStatusEnum.failed
        assert result.payout_id == "txn_005"
        assert result.error_message is not None
