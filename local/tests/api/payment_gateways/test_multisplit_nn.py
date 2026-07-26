import uuid

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.payment_gateways.tinkoff.client.service import TinkoffAPIClient
from src.api.payment_gateways.tinkoff.client.schemas import (
    TinkoffDealResponse,
    TinkoffCloseSpDealResponse,
    TinkoffInitResponse,
    TinkoffPaymentResponse,
)
from src.api.payment_gateways.tinkoff.exceptions import PayoutError
from src.api.payment_gateways.tinkoff.service import TinkoffService
from src.api.payment_gateways.tinkoff.strategy import (
    SBPPayoutStrategy,
    CardPayoutStrategy,
)
from src.api.payment_gateways.tinkoff.uow import TinkoffUnitOfWork
from src.api.user_service.schemas import WithdrawMethodSchema
from src.core.database.enums.transactions import (
    PaymentProviderEnum,
    TransactionStatusEnum,
)


@pytest.fixture
def tinkoff_client():
    return TinkoffAPIClient(
        password="test_password",
        terminal_key="test_terminal",
        terminal_key_e2c="test_terminal_e2c",
        notification_url="https://test.com/notify",
        use_test=True,
    )


@pytest.fixture
def mock_uow():
    uow = MagicMock(spec=TinkoffUnitOfWork)
    uow.deals = MagicMock()
    uow.deals.get_active = AsyncMock()
    uow.deals.create = AsyncMock()
    uow.deals.subtract_amount = AsyncMock()
    uow.deals.close = AsyncMock()
    uow.deals.update = AsyncMock()
    uow.deals.add_amount = AsyncMock()
    uow.payments = MagicMock()
    uow.payments.create = AsyncMock()
    uow.deposit_requests = MagicMock()
    uow.deposit_requests.create = AsyncMock()
    uow.deposit_requests.update_by = AsyncMock()
    uow.deposit_requests.get_last_deposit_request = AsyncMock(return_value=None)
    return uow


def _mock_post_response(data: dict) -> MagicMock:
    return MagicMock(status_code=200, json=lambda: data)


def _make_deal(
    *,
    deal_id="deal_1",
    deal_type="NN",
    amount=5000,
    is_locked=False,
    open_status=True,
    streamer_id=38,
):
    deal = MagicMock()
    deal.id = 1
    deal.deal_id = deal_id
    deal.deal_type = deal_type
    deal.amount = amount
    deal.stake_reserved = 0
    deal.is_locked = is_locked
    deal.open_status = open_status
    deal.streamer_id = streamer_id
    return deal


class TestClientMultisplitNN:
    @pytest.mark.asyncio
    async def test_create_deal_sends_nn_type(self, tinkoff_client):
        mock_response = {
            "Success": True,
            "ErrorCode": "0",
            "SpAccumulationId": "deal_123",
        }
        with patch.object(
            tinkoff_client.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = _mock_post_response(mock_response)
            await tinkoff_client.create_deal()
            called_body = mock_post.call_args[1]["json"]
            assert called_body["SpDealType"] == "NN"

    @pytest.mark.asyncio
    async def test_close_deal_sends_correct_body(self, tinkoff_client):
        mock_response = {"Success": True, "ErrorCode": "0"}
        with patch.object(
            tinkoff_client.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = _mock_post_response(mock_response)
            result = await tinkoff_client.close_deal("deal_xyz")
            assert isinstance(result, TinkoffCloseSpDealResponse)

            url = mock_post.call_args[0][0]
            assert "/closeSpDeal" in url

            called_body = mock_post.call_args[1]["json"]
            assert called_body["SpAccumulationId"] == "deal_xyz"
            assert called_body["TerminalKey"] == "test_terminal"

    @pytest.mark.asyncio
    async def test_init_pay_out_partial_payout(self, tinkoff_client):
        mock_response = {
            "Success": True,
            "ErrorCode": "0",
            "PaymentId": "pay_1",
            "OrderId": "ord_1",
            "Amount": 1000,
            "Status": "NEW",
        }
        with patch.object(
            tinkoff_client.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = _mock_post_response(mock_response)
            await tinkoff_client.init_pay_out(
                order_id="ord_1",
                deal_id="deal_1",
                amount=1000,
                card_id="card_123",
                final_payout=False,
            )
            called_body = mock_post.call_args[1]["json"]
            assert called_body["FinalPayout"] is False

    @pytest.mark.asyncio
    async def test_init_pay_out_final_payout(self, tinkoff_client):
        mock_response = {
            "Success": True,
            "ErrorCode": "0",
            "PaymentId": "pay_2",
            "OrderId": "ord_2",
            "Amount": 5000,
            "Status": "NEW",
        }
        with patch.object(
            tinkoff_client.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = _mock_post_response(mock_response)
            await tinkoff_client.init_pay_out(
                order_id="ord_2",
                deal_id="deal_1",
                amount=5000,
                card_id="card_123",
                final_payout=True,
            )
            called_body = mock_post.call_args[1]["json"]
            assert called_body["FinalPayout"] is True

    @pytest.mark.asyncio
    async def test_init_pay_in_with_payment_recipient_id(self, tinkoff_client):
        mock_response = {
            "Success": True,
            "ErrorCode": "0",
            "PaymentId": "pay_3",
            "OrderId": "ord_3",
            "Amount": 2000,
            "Status": "NEW",
            "PaymentURL": "https://pay.test",
        }
        with patch.object(
            tinkoff_client.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = _mock_post_response(mock_response)
            await tinkoff_client.init_pay_in(
                order_id="ord_3",
                amount=2000,
                deal_id="deal_1",
                success_url="https://ok.test",
                payment_recipient_id="123",
            )
            called_body = mock_post.call_args[1]["json"]
            assert called_body["PaymentRecipientId"] == "123"


class TestServiceMultisplitNN:
    @pytest.mark.asyncio
    async def test_ensure_deal_creates_nn_deal(self, mock_uow):
        mock_uow.deals.get_active.return_value = None

        service = TinkoffService(mock_uow)

        with patch(
            "src.api.payment_gateways.tinkoff.service.tinkoff_client"
        ) as mock_client:
            mock_client.create_deal = AsyncMock(
                return_value=TinkoffDealResponse.model_validate(
                    {
                        "Success": True,
                        "ErrorCode": "0",
                        "SpAccumulationId": "new_deal",
                    }
                )
            )

            new_deal = MagicMock()
            new_deal.deal_id = "new_deal"
            mock_uow.deals.create.return_value = new_deal

            result = await service._ensure_deal(123)

            mock_client.create_deal.assert_called_once_with(deal_type="NN")
            create_kwargs = mock_uow.deals.create.call_args[1]
            assert create_kwargs["deal_type"] == "NN"
            assert "expires_at" in create_kwargs
            assert result.deal_id == "new_deal"

    @pytest.mark.asyncio
    async def test_process_deal_nn_partial_payout(self, mock_uow):
        deal = _make_deal(deal_type="NN", amount=5000)
        mock_uow.deals.get_active.return_value = deal
        mock_uow.deals.subtract_amount.return_value = 1

        service = TinkoffService(mock_uow)
        result_deal, final_payout = await service._process_deal_pay_pay_out(38, 1000)

        mock_uow.deals.subtract_amount.assert_called_once_with(deal.deal_id, 1000)
        assert final_payout is False
        assert result_deal is deal
        mock_uow.deals.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_deal_n1_full_payout(self, mock_uow):
        deal = _make_deal(deal_type="N1", amount=5000)
        mock_uow.deals.get_active.return_value = deal

        service = TinkoffService(mock_uow)
        result_deal, final_payout = await service._process_deal_pay_pay_out(38, 5000)

        mock_uow.deals.update.assert_called_once_with(deal.id, open_status=False)
        assert final_payout is True
        assert result_deal is deal

    @pytest.mark.asyncio
    async def test_confirm_deposit_uses_webhook_deal_id(self, mock_uow):
        service = TinkoffService(mock_uow)
        tx_id = uuid.uuid4()

        with patch("src.api.payment_gateways.tinkoff.service.tinkoff_client"):
            await service.confirm_deposit(
                transaction_id=tx_id,
                order_id="order_1",
                streamer_id=38,
                amount=1000,
                deal_id="webhook_deal",
            )

        mock_uow.deals.add_amount.assert_called_once_with("webhook_deal", 1000)
        mock_uow.deals.get_active.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_deal_insufficient_balance(self, mock_uow):
        deal = _make_deal(deal_type="NN", amount=100)
        mock_uow.deals.get_active.return_value = deal

        service = TinkoffService(mock_uow)

        with pytest.raises(PayoutError, match="Insufficient deal balance"):
            await service._process_deal_pay_pay_out(38, 500)


class TestStrategyMultisplitNN:
    @pytest.mark.asyncio
    async def test_sbp_strategy_passes_final_payout(self):
        mock_client = MagicMock(spec=TinkoffAPIClient)
        mock_client.init_pay_out = AsyncMock(
            return_value=TinkoffInitResponse.model_validate(
                {
                    "Success": True,
                    "ErrorCode": "0",
                    "PaymentId": "pay_sbp",
                    "OrderId": "ord_sbp",
                    "Amount": 500,
                    "Status": "NEW",
                }
            )
        )

        method_data = WithdrawMethodSchema(
            streamer_id=38,
            payment_provider=PaymentProviderEnum.tinkoff,
            phone="+79001234567",
            sbp_member_id="member_123",
        )

        strategy = SBPPayoutStrategy()
        result = await strategy.process(
            client=mock_client,
            streamer_id=38,
            amount=500,
            external_transaction_id="tx_1",
            method_data=method_data,
            deal_id="deal_1",
            final_payout=False,
            payment_recipient_id="123",
        )

        mock_client.init_pay_out.assert_called_once()
        call_kwargs = mock_client.init_pay_out.call_args[1]
        assert call_kwargs["final_payout"] is False
        assert call_kwargs["payment_recipient_id"] == "123"
        assert result.status == TransactionStatusEnum.pending

    @pytest.mark.asyncio
    async def test_card_strategy_passes_final_payout(self):
        mock_client = MagicMock(spec=TinkoffAPIClient)
        mock_client.init_pay_out = AsyncMock(
            return_value=TinkoffInitResponse.model_validate(
                {
                    "Success": True,
                    "ErrorCode": "0",
                    "PaymentId": "pay_card",
                    "OrderId": "ord_card",
                    "Amount": 1000,
                    "Status": "NEW",
                }
            )
        )
        mock_client.confirm_payout = AsyncMock(
            return_value=TinkoffPaymentResponse.model_validate(
                {
                    "Success": True,
                    "ErrorCode": "0",
                    "PaymentId": "pay_card",
                    "Status": "COMPLETED",
                }
            )
        )

        method_data = WithdrawMethodSchema(
            streamer_id=38,
            payment_provider=PaymentProviderEnum.tinkoff,
            card_id="card_456",
        )

        strategy = CardPayoutStrategy()
        result = await strategy.process(
            client=mock_client,
            streamer_id=38,
            amount=1000,
            external_transaction_id="tx_2",
            method_data=method_data,
            deal_id="deal_1",
            final_payout=False,
            payment_recipient_id="456",
        )

        call_kwargs = mock_client.init_pay_out.call_args[1]
        assert call_kwargs["final_payout"] is False
        assert call_kwargs["payment_recipient_id"] == "456"
        assert result.status == TransactionStatusEnum.completed
