import pytest
from unittest.mock import AsyncMock, MagicMock

from src.api.payment_gateways.tinkoff.strategy import (
    SBPPayoutStrategy,
    CardPayoutStrategy,
)


class TestSBPStrategy:
    async def test_sbp_passes_final_payout_false(self):
        """SBP strategy should pass FinalPayout=False to init_pay_out"""
        strategy = SBPPayoutStrategy()
        mock_client = MagicMock()
        mock_client.init_pay_out = AsyncMock(
            return_value=MagicMock(
                success=True,
                order_id="ord_1",
                payment_id="pay_1",
            )
        )
        method_data = MagicMock(phone="79001234567", sbp_member_id="100000000004")

        await strategy.process(
            client=mock_client,
            streamer_id=1,
            amount=500,
            external_transaction_id="ext_1",
            method_data=method_data,
            deal_id="deal_1",
            final_payout=False,
            payment_recipient_id="1",
        )

        call_kwargs = mock_client.init_pay_out.call_args[1]
        assert call_kwargs["final_payout"] is False
        assert call_kwargs["payment_recipient_id"] == "1"

    async def test_sbp_passes_final_payout_true(self):
        """SBP strategy should pass FinalPayout=True for N1 deals"""
        strategy = SBPPayoutStrategy()
        mock_client = MagicMock()
        mock_client.init_pay_out = AsyncMock(
            return_value=MagicMock(
                success=True,
                order_id="ord_1",
                payment_id="pay_1",
            )
        )
        method_data = MagicMock(phone="79001234567", sbp_member_id="100000000004")

        await strategy.process(
            client=mock_client,
            streamer_id=1,
            amount=500,
            external_transaction_id="ext_1",
            method_data=method_data,
            deal_id="deal_1",
            final_payout=True,
            payment_recipient_id="1",
        )

        call_kwargs = mock_client.init_pay_out.call_args[1]
        assert call_kwargs["final_payout"] is True


class TestCardStrategy:
    async def test_card_passes_final_payout_false(self):
        """Card strategy should pass FinalPayout=False to init_pay_out"""
        strategy = CardPayoutStrategy()
        mock_client = MagicMock()
        mock_client.init_pay_out = AsyncMock(
            return_value=MagicMock(
                success=True,
                order_id="ord_1",
                payment_id="pay_1",
            )
        )
        mock_client.confirm_payout = AsyncMock(
            return_value=MagicMock(
                success=True,
                status="COMPLETED",
                payment_id="pay_1",
            )
        )
        method_data = MagicMock(card_id="card_1")

        await strategy.process(
            client=mock_client,
            streamer_id=1,
            amount=500,
            external_transaction_id="ext_1",
            method_data=method_data,
            deal_id="deal_1",
            final_payout=False,
            payment_recipient_id="1",
        )

        call_kwargs = mock_client.init_pay_out.call_args[1]
        assert call_kwargs["final_payout"] is False
        assert call_kwargs["payment_recipient_id"] == "1"

    async def test_card_passes_final_payout_true(self):
        """Card strategy should pass FinalPayout=True for N1 deals"""
        strategy = CardPayoutStrategy()
        mock_client = MagicMock()
        mock_client.init_pay_out = AsyncMock(
            return_value=MagicMock(
                success=True,
                order_id="ord_1",
                payment_id="pay_1",
            )
        )
        mock_client.confirm_payout = AsyncMock(
            return_value=MagicMock(
                success=True,
                status="COMPLETED",
                payment_id="pay_1",
            )
        )
        method_data = MagicMock(card_id="card_1")

        await strategy.process(
            client=mock_client,
            streamer_id=1,
            amount=500,
            external_transaction_id="ext_1",
            method_data=method_data,
            deal_id="deal_1",
            final_payout=True,
            payment_recipient_id="1",
        )

        call_kwargs = mock_client.init_pay_out.call_args[1]
        assert call_kwargs["final_payout"] is True
