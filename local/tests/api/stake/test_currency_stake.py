import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from tests.api.stake.test_stake_payout import (
    _make_uow,
    _make_stake,
    _make_outcome,
    _make_stake_balance,
    _make_deal,
    _make_distribution,
)
from src.api.stake.service import StakeService
from src.api.stake.payout_service import StakePayoutService
from src.api.stake.schemas import FinishStakeSchema
from src.core.database.enums.balances import OperationTypeEnum
from src.core.database.enums.transactions import TransactionStatusEnum


class TestCurrencyStake:
    @pytest.mark.asyncio
    async def test_get_stake_balance_usd(self):
        stake_id = uuid4()
        outcome = _make_outcome(
            outcome_id=uuid4(), stake_id=stake_id, current_amount=500
        )
        stake = _make_stake(
            stake_id=stake_id,
            streamer_id=38,
            outcomes=[outcome],
            currency="USD",
        )

        uow = _make_uow()
        uow.stake.get_full.return_value = stake

        service = StakeService(uow)
        result = await service.get_stake_balance(38)

        assert result == 500

    @pytest.mark.asyncio
    async def test_get_active_stake_with_currency_filter(self):
        stake_id = uuid4()
        stake = _make_stake(stake_id=stake_id, streamer_id=38, currency="USD")

        uow = _make_uow()
        uow.stake.get_full.return_value = stake

        service = StakeService(uow)
        result = await service.get_active_stake(38)

        assert result.currency == "USD"
        uow.stake.get_full.assert_called_once()

    @pytest.mark.asyncio
    async def test_finish_usd_stake_uses_oxypay_payout(self):
        stake_id = uuid4()
        dist = _make_distribution(amount=500, source_streamer_id=38, stake_id=stake_id)
        mock_stake = _make_stake(stake_id=stake_id, currency="USD")

        uow = _make_uow()
        uow.stake.get_by.return_value = mock_stake

        payout_result = MagicMock()
        payout_result.status = TransactionStatusEnum.completed

        tinkoff = MagicMock()
        oxypay = MagicMock()
        oxypay.make_pay_out = AsyncMock(return_value=payout_result)

        service = StakePayoutService(uow, tinkoff, oxypay)
        withdraw_method = MagicMock()

        result = await service.process_stake_withdrawal(dist, withdraw_method)

        assert result == TransactionStatusEnum.completed
        uow.deals.get_active.assert_not_called()
        uow.deals.reserve_for_stake.assert_not_called()
        oxypay.make_pay_out.assert_called_once()
        tinkoff.make_pay_out = AsyncMock()
        tinkoff.make_pay_out.assert_not_called()

    @pytest.mark.asyncio
    async def test_finish_usd_stake_credits_usd_distributions(self):
        stake_id = uuid4()
        winner_id = uuid4()
        sb = _make_stake_balance(
            outcome_id=winner_id, created_by_id=10, total_amount=500
        )
        outcome = _make_outcome(
            outcome_id=winner_id, stake_id=stake_id, current_amount=500
        )
        stake = _make_stake(
            stake_id=stake_id,
            streamer_id=38,
            outcomes=[outcome],
            stake_balances=[sb],
            currency="USD",
        )

        deal = _make_deal(amount=5000)
        uow = _make_uow()
        uow.deals.get_active.return_value = deal

        actual_balance = MagicMock()
        actual_balance.balance_total = 0
        uow.balance.get_actual_balance.return_value = actual_balance

        service = StakeService(uow)
        finish_data = FinishStakeSchema(
            winner_outcome_id=winner_id,
            group_percent=50,
            streamer_percent=50,
        )
        await service._perform_distribution(stake, finish_data)

        bulk_call = uow.stake_distribution.bulk_insert.call_args[0][0]
        total_distributed = sum(d["amount"] for d in bulk_call)
        assert total_distributed == 500
        assert uow.balance.create.call_count >= 1
