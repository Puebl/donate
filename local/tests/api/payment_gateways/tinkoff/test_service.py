import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from src.api.payment_gateways.tinkoff.service import TinkoffService
from src.api.payment_gateways.tinkoff.exceptions import PayoutError, DealLockedError


class TestEnsureDeal:
    async def test_ensure_deal_creates_nn(self, tinkoff_service, mock_uow):
        """New deals should be created as NN type with expires_at"""
        mock_uow.deals.get_active = AsyncMock(return_value=None)

        mock_deal = MagicMock()
        mock_deal.deal_type = "NN"
        mock_deal.expires_at = datetime(2026, 4, 1)
        mock_uow.deals.create = AsyncMock(return_value=mock_deal)

        with patch(
            "src.api.payment_gateways.tinkoff.service.tinkoff_client"
        ) as mock_client:
            mock_client.create_deal = AsyncMock(
                return_value=MagicMock(success=True, deal_id="new_deal_123")
            )

            result = await tinkoff_service._ensure_deal(1)

        mock_uow.deals.get_active.assert_called_once_with(1, for_update=True)
        create_call = mock_uow.deals.create.call_args
        assert create_call[1]["deal_type"] == "NN"
        assert "expires_at" in create_call[1]

    async def test_ensure_deal_returns_existing(self, tinkoff_service, mock_uow):
        """Should return existing active deal without creating new one"""
        existing_deal = MagicMock()
        existing_deal.deal_id = "existing_deal_123"
        mock_uow.deals.get_active = AsyncMock(return_value=existing_deal)

        result = await tinkoff_service._ensure_deal(1)

        assert result == existing_deal
        mock_uow.deals.create.assert_not_called()


class TestProcessDealPayPayOut:
    async def test_partial_payout_keeps_deal_open(self, tinkoff_service, mock_uow):
        mock_deal = MagicMock()
        mock_deal.deal_type = "NN"
        mock_deal.amount = 1000
        mock_deal.stake_reserved = 0
        mock_deal.is_locked = False
        mock_deal.deal_id = "deal_123"
        mock_deal.id = 1
        mock_uow.deals.get_active = AsyncMock(return_value=mock_deal)
        mock_uow.deals.subtract_amount = AsyncMock(return_value=1)

        deal, final_payout = await tinkoff_service._process_deal_pay_pay_out(1, 500)

        assert final_payout is False
        mock_uow.deals.subtract_amount.assert_called_once_with("deal_123", 500)
        mock_uow.deals.update.assert_not_called()  # Should NOT close deal

    async def test_n1_deal_uses_final_payout_true(self, tinkoff_service, mock_uow):
        mock_deal = MagicMock()
        mock_deal.deal_type = "N1"
        mock_deal.amount = 1000
        mock_deal.stake_reserved = 0
        mock_deal.is_locked = False
        mock_deal.id = 1
        mock_uow.deals.get_active = AsyncMock(return_value=mock_deal)
        mock_uow.deals.update = AsyncMock()

        deal, final_payout = await tinkoff_service._process_deal_pay_pay_out(1, 1000)

        assert final_payout is True
        mock_uow.deals.update.assert_called_once_with(1, open_status=False)

    async def test_payout_insufficient_balance(self, tinkoff_service, mock_uow):
        mock_deal = MagicMock()
        mock_deal.deal_type = "NN"
        mock_deal.amount = 100
        mock_deal.stake_reserved = 0
        mock_deal.is_locked = False
        mock_uow.deals.get_active = AsyncMock(return_value=mock_deal)

        with pytest.raises(PayoutError, match="Insufficient"):
            await tinkoff_service._process_deal_pay_pay_out(1, 500)

    async def test_locked_deal_raises_error(self, tinkoff_service, mock_uow):
        """Should raise DealLockedError when deal is locked"""
        mock_deal = MagicMock()
        mock_deal.is_locked = True
        mock_uow.deals.get_active = AsyncMock(return_value=mock_deal)

        with pytest.raises(DealLockedError):
            await tinkoff_service._process_deal_pay_pay_out(1, 500)

    async def test_no_active_deal_raises_error(self, tinkoff_service, mock_uow):
        """Should raise PayoutError when no active deal exists"""
        mock_uow.deals.get_active = AsyncMock(return_value=None)

        with pytest.raises(PayoutError, match="No active deal"):
            await tinkoff_service._process_deal_pay_pay_out(1, 500)

    async def test_minimum_amount_check(self, tinkoff_service, mock_uow):
        """Should raise PayoutError when amount is below 100 kopecks"""
        mock_deal = MagicMock()
        mock_deal.is_locked = False
        mock_deal.amount = 1000
        mock_uow.deals.get_active = AsyncMock(return_value=mock_deal)

        with pytest.raises(PayoutError, match="Minimum payout"):
            await tinkoff_service._process_deal_pay_pay_out(1, 50)


class TestConfirmDeposit:
    async def test_confirm_deposit_uses_webhook_deal_id(
        self, tinkoff_service, mock_uow
    ):
        """Should use deal_id from webhook, not _ensure_deal"""
        mock_uow.payments.create = AsyncMock()
        mock_uow.deposit_requests.update_by = AsyncMock()
        mock_uow.deals.add_amount = AsyncMock()

        await tinkoff_service.confirm_deposit(
            transaction_id=uuid.uuid4(),
            order_id="ord_1",
            streamer_id=1,
            amount=1000,
            deal_id="webhook_deal_123",
        )

        mock_uow.deals.add_amount.assert_called_once_with("webhook_deal_123", 1000)
