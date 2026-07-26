import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from src.api.stake.service import StakeService
from src.api.stake.payout_service import StakePayoutService
from src.api.stake.schemas import FinishStakeSchema, SpecificUserDistribution
from src.api.billing.schemas import OperationCalculationSchema
from src.core.database.enums.stake import StakeStatusEnum
from src.core.database.enums.balances import OperationTypeEnum
from src.core.database.enums.transactions import TransactionStatusEnum
from src.api.payment_gateways.tinkoff.exceptions import PayoutError


def _make_uow(**overrides):
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)
    uow.rollback = AsyncMock()

    uow.stake = MagicMock()
    uow.stake.get_by = AsyncMock()
    uow.stake.get_full = AsyncMock()
    uow.stake.get_full_for_update = AsyncMock()
    uow.stake.update = AsyncMock()

    uow.stake_outcome = MagicMock()
    uow.stake_outcome.get_by = AsyncMock()
    uow.stake_outcome.update = AsyncMock()
    uow.stake_outcome.increment_amount = AsyncMock()

    uow.stake_balance = MagicMock()
    uow.stake_balance.create = AsyncMock()

    uow.stake_distribution = MagicMock()
    uow.stake_distribution.bulk_insert = AsyncMock()
    uow.stake_distribution.update = AsyncMock()
    uow.stake_distribution.get_pending_for_user = AsyncMock(return_value=[])
    uow.stake_distribution.get_many_by = AsyncMock(return_value=[])

    uow.deals = MagicMock()
    uow.deals.get_active = AsyncMock()
    uow.deals.reserve_for_stake = AsyncMock(return_value=1)
    uow.deals.fulfill_reservation = AsyncMock(return_value=1)
    uow.deals.subtract_amount = AsyncMock(return_value=1)

    uow.balance = MagicMock()
    uow.balance.get_actual_balance = AsyncMock()
    uow.balance.init_new_balance = AsyncMock()
    uow.balance.create = AsyncMock()

    for k, v in overrides.items():
        setattr(uow, k, v)
    return uow


def _make_stake(
    *,
    stake_id=None,
    streamer_id=38,
    status=StakeStatusEnum.active,
    expires_at=None,
    outcomes=None,
    stake_balances=None,
    currency="RUB",
):
    stake = MagicMock()
    stake.id = stake_id or uuid4()
    stake.streamer_id = streamer_id
    stake.status = status
    stake.expires_at = expires_at
    stake.outcomes = outcomes or []
    stake.stake_balances = stake_balances or []
    stake.currency = currency
    return stake


def _make_outcome(*, outcome_id=None, stake_id=None, current_amount=0, is_winner=False):
    outcome = MagicMock()
    outcome.id = outcome_id or uuid4()
    outcome.stake_id = stake_id or uuid4()
    outcome.current_amount = current_amount
    outcome.is_winner = is_winner
    return outcome


def _make_stake_balance(*, outcome_id, created_by_id, total_amount):
    sb = MagicMock()
    sb.outcome_id = outcome_id
    sb.created_by_id = created_by_id
    sb.total_amount = total_amount
    return sb


def _make_deal(*, deal_id="deal_1", amount=5000, stake_reserved=0, is_locked=False):
    deal = MagicMock()
    deal.id = 1
    deal.deal_id = deal_id
    deal.amount = amount
    deal.stake_reserved = stake_reserved
    deal.is_locked = is_locked
    deal.open_status = True
    return deal


def _make_distribution(
    *, dist_id=None, user_id=100, amount=500, source_streamer_id=38, stake_id=None
):
    dist = MagicMock()
    dist.id = dist_id or uuid4()
    dist.user_id = user_id
    dist.amount = amount
    dist.source_streamer_id = source_streamer_id
    dist.stake_id = stake_id or uuid4()
    return dist


def _calc_data(amount=1000):
    return OperationCalculationSchema(
        amount_to_send=amount,
        commission=0,
        operation_type=OperationTypeEnum.stake_payout_credit,
        commission_type=OperationTypeEnum.stake_payout_credit,
    )


# ---------------------------------------------------------------------------
# Bug fixes
# ---------------------------------------------------------------------------


class TestCreditStakeBalance:
    @pytest.mark.asyncio
    async def test_credit_stake_balance_rejects_paused_stake(self):
        from fastapi import HTTPException

        outcome_id = uuid4()
        stake_id = uuid4()

        outcome = MagicMock()
        outcome.id = outcome_id
        outcome.stake_id = stake_id

        stake = _make_stake(stake_id=stake_id, status=StakeStatusEnum.paused)

        uow = _make_uow()
        uow.stake_outcome.get_by.return_value = outcome
        uow.stake.get_by.return_value = stake

        service = StakeService(uow)
        with pytest.raises(HTTPException) as exc_info:
            await service.credit_stake_balance(outcome_id, _calc_data(), user_id=1)
        assert exc_info.value.status_code == 400
        assert "paused" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_credit_stake_balance_rejects_expired_stake(self):
        from fastapi import HTTPException

        outcome_id = uuid4()
        stake_id = uuid4()

        outcome = MagicMock()
        outcome.id = outcome_id
        outcome.stake_id = stake_id

        expired_at = datetime.utcnow() - timedelta(hours=1)
        stake = _make_stake(
            stake_id=stake_id,
            status=StakeStatusEnum.active,
            expires_at=expired_at,
        )

        uow = _make_uow()
        uow.stake_outcome.get_by.return_value = outcome
        uow.stake.get_by.return_value = stake

        service = StakeService(uow)
        with pytest.raises(HTTPException) as exc_info:
            await service.credit_stake_balance(outcome_id, _calc_data(), user_id=1)
        assert exc_info.value.status_code == 400
        assert "expired" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_credit_stake_balance_uses_external_uow(self):
        outcome_id = uuid4()
        stake_id = uuid4()

        outcome = MagicMock()
        outcome.id = outcome_id
        outcome.stake_id = stake_id

        future_expires = datetime.utcnow() + timedelta(hours=24)
        stake = _make_stake(
            stake_id=stake_id,
            status=StakeStatusEnum.active,
            expires_at=future_expires,
        )

        external_uow = _make_uow()
        external_uow.stake_outcome.get_by.return_value = outcome
        external_uow.stake.get_by.return_value = stake

        own_uow = _make_uow()
        service = StakeService(own_uow)

        await service.credit_stake_balance(
            outcome_id, _calc_data(500), user_id=7, external_uow=external_uow
        )

        own_uow.__aenter__.assert_not_called()
        external_uow.stake_balance.create.assert_called_once()
        external_uow.stake_outcome.increment_amount.assert_called_once_with(
            outcome_id, 500
        )


class TestFinishStake:
    @pytest.mark.asyncio
    async def test_finish_stake_sets_finished_time(self):
        stake_id = uuid4()
        winner_id = uuid4()
        outcome = _make_outcome(
            outcome_id=winner_id, stake_id=stake_id, current_amount=0
        )
        stake = _make_stake(
            stake_id=stake_id,
            streamer_id=38,
            status=StakeStatusEnum.active,
            outcomes=[outcome],
            stake_balances=[],
        )

        uow = _make_uow()
        uow.stake.get_full_for_update.return_value = stake
        uow.stake.get_full.return_value = stake

        service = StakeService(uow)
        finish_data = FinishStakeSchema(
            winner_outcome_id=winner_id,
            group_percent=0,
            streamer_percent=100,
        )
        await service.finish_stake(stake_id, 38, finish_data)

        update_call = uow.stake.update.call_args
        assert update_call is not None
        kwargs = (
            update_call[1]
            if update_call[1]
            else dict(
                zip(
                    ["id", "status", "winner_outcome_id", "finished_time"],
                    update_call[0],
                )
            )
        )
        assert "finished_time" in kwargs or any(
            isinstance(a, datetime) for a in (update_call[0] if update_call[0] else [])
        )

    @pytest.mark.asyncio
    async def test_finish_stake_rejects_non_donator_specific_users(self):
        from fastapi import HTTPException

        stake_id = uuid4()
        winner_id = uuid4()
        outcome = _make_outcome(
            outcome_id=winner_id, stake_id=stake_id, current_amount=1000
        )
        sb = _make_stake_balance(
            outcome_id=winner_id, created_by_id=10, total_amount=1000
        )
        stake = _make_stake(
            stake_id=stake_id,
            streamer_id=38,
            status=StakeStatusEnum.active,
            outcomes=[outcome],
            stake_balances=[sb],
        )

        uow = _make_uow()
        uow.stake.get_full_for_update.return_value = stake

        service = StakeService(uow)
        finish_data = FinishStakeSchema(
            winner_outcome_id=winner_id,
            group_percent=50,
            streamer_percent=40,
            specific_users=[SpecificUserDistribution(user_id=9999, percent=10)],
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.finish_stake(stake_id, 38, finish_data)
        assert exc_info.value.status_code == 400
        assert "9999" in exc_info.value.detail


# ---------------------------------------------------------------------------
# Distribution + deal reservation
# ---------------------------------------------------------------------------


class TestPerformDistribution:
    @pytest.mark.asyncio
    async def test_perform_distribution_largest_remainder(self):
        stake_id = uuid4()
        winner_id = uuid4()
        loser_id = uuid4()

        sb1 = _make_stake_balance(
            outcome_id=winner_id, created_by_id=10, total_amount=300
        )
        sb2 = _make_stake_balance(
            outcome_id=winner_id, created_by_id=11, total_amount=200
        )
        sb3 = _make_stake_balance(
            outcome_id=loser_id, created_by_id=12, total_amount=500
        )

        outcome_w = _make_outcome(
            outcome_id=winner_id, stake_id=stake_id, current_amount=500
        )
        outcome_l = _make_outcome(
            outcome_id=loser_id, stake_id=stake_id, current_amount=500
        )

        stake = _make_stake(
            stake_id=stake_id,
            streamer_id=38,
            outcomes=[outcome_w, outcome_l],
            stake_balances=[sb1, sb2, sb3],
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
            group_percent=70,
            streamer_percent=30,
        )
        await service._perform_distribution(stake, finish_data)

        bulk_call = uow.stake_distribution.bulk_insert.call_args[0][0]
        total_distributed = sum(d["amount"] for d in bulk_call)
        assert total_distributed == 1000

    @pytest.mark.asyncio
    async def test_perform_distribution_adds_source_streamer_id(self):
        stake_id = uuid4()
        winner_id = uuid4()
        sb = _make_stake_balance(
            outcome_id=winner_id, created_by_id=10, total_amount=100
        )
        outcome = _make_outcome(
            outcome_id=winner_id, stake_id=stake_id, current_amount=100
        )
        stake = _make_stake(
            stake_id=stake_id,
            streamer_id=42,
            outcomes=[outcome],
            stake_balances=[sb],
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
        for d in bulk_call:
            assert d["source_streamer_id"] == 42

    @pytest.mark.asyncio
    async def test_perform_distribution_sets_payout_status_credited(self):
        stake_id = uuid4()
        winner_id = uuid4()
        sb = _make_stake_balance(
            outcome_id=winner_id, created_by_id=10, total_amount=200
        )
        outcome = _make_outcome(
            outcome_id=winner_id, stake_id=stake_id, current_amount=200
        )
        stake = _make_stake(
            stake_id=stake_id,
            streamer_id=38,
            outcomes=[outcome],
            stake_balances=[sb],
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
        for d in bulk_call:
            assert d["payout_status"] == "credited"

    @pytest.mark.asyncio
    async def test_perform_distribution_reserves_non_streamer_amount(self):
        stake_id = uuid4()
        winner_id = uuid4()
        sb = _make_stake_balance(
            outcome_id=winner_id, created_by_id=10, total_amount=1000
        )
        outcome = _make_outcome(
            outcome_id=winner_id, stake_id=stake_id, current_amount=1000
        )
        stake = _make_stake(
            stake_id=stake_id,
            streamer_id=38,
            outcomes=[outcome],
            stake_balances=[sb],
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
            group_percent=60,
            streamer_percent=40,
        )
        await service._perform_distribution(stake, finish_data)

        uow.deals.reserve_for_stake.assert_called_once_with(deal.deal_id, 600)

    @pytest.mark.asyncio
    async def test_perform_distribution_credits_balances(self):
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
        )

        deal = _make_deal(amount=5000)
        uow = _make_uow()
        uow.deals.get_active.return_value = deal

        actual_balance = MagicMock()
        actual_balance.balance_total = 100
        uow.balance.get_actual_balance.return_value = actual_balance

        service = StakeService(uow)
        finish_data = FinishStakeSchema(
            winner_outcome_id=winner_id,
            group_percent=50,
            streamer_percent=50,
        )
        await service._perform_distribution(stake, finish_data)

        assert uow.balance.create.call_count == 2
        for call in uow.balance.create.call_args_list:
            kwargs = call[1]
            assert kwargs["operation_type"] == OperationTypeEnum.stake_payout_credit
            assert kwargs["balance_diff"] > 0

    @pytest.mark.asyncio
    async def test_perform_distribution_empty_pot_returns_early(self):
        stake_id = uuid4()
        winner_id = uuid4()
        outcome = _make_outcome(
            outcome_id=winner_id, stake_id=stake_id, current_amount=0
        )
        loser = _make_outcome(stake_id=stake_id, current_amount=0)
        stake = _make_stake(
            stake_id=stake_id,
            streamer_id=38,
            outcomes=[outcome, loser],
            stake_balances=[],
        )

        uow = _make_uow()
        service = StakeService(uow)
        finish_data = FinishStakeSchema(
            winner_outcome_id=winner_id,
            group_percent=50,
            streamer_percent=50,
        )
        await service._perform_distribution(stake, finish_data)

        uow.stake_distribution.bulk_insert.assert_not_called()
        uow.deals.get_active.assert_not_called()


# ---------------------------------------------------------------------------
# Deal reservation (via TinkoffService._process_deal_pay_pay_out)
# ---------------------------------------------------------------------------


class TestDealReservation:
    @pytest.mark.asyncio
    async def test_process_deal_pay_pay_out_respects_stake_reserved(self):
        from src.api.payment_gateways.tinkoff.service import TinkoffService
        from src.api.payment_gateways.tinkoff.exceptions import (
            PayoutError as TPayoutError,
        )

        deal = _make_deal(amount=5000, stake_reserved=4000)
        uow = _make_uow()
        uow.deals.get_active.return_value = deal
        uow.deposit_requests = MagicMock()
        uow.deposit_requests.get_last_deposit_request = AsyncMock(return_value=None)

        service = TinkoffService(uow)
        with pytest.raises(TPayoutError, match="Insufficient deal balance"):
            await service._process_deal_pay_pay_out(38, 1500)

    @pytest.mark.asyncio
    async def test_reserve_for_stake_insufficient_balance_raises(self):
        from fastapi import HTTPException

        stake_id = uuid4()
        winner_id = uuid4()
        sb = _make_stake_balance(
            outcome_id=winner_id, created_by_id=10, total_amount=1000
        )
        outcome = _make_outcome(
            outcome_id=winner_id, stake_id=stake_id, current_amount=1000
        )
        stake = _make_stake(
            stake_id=stake_id,
            streamer_id=38,
            outcomes=[outcome],
            stake_balances=[sb],
        )

        deal = _make_deal(amount=100)
        uow = _make_uow()
        uow.deals.get_active.return_value = deal
        uow.deals.reserve_for_stake.return_value = 0

        service = StakeService(uow)
        finish_data = FinishStakeSchema(
            winner_outcome_id=winner_id,
            group_percent=60,
            streamer_percent=40,
        )
        with pytest.raises(HTTPException) as exc_info:
            await service._perform_distribution(stake, finish_data)
        assert exc_info.value.status_code == 400
        assert "insufficient" in exc_info.value.detail.lower()


# ---------------------------------------------------------------------------
# Payout service
# ---------------------------------------------------------------------------


class TestStakePayoutService:
    @pytest.mark.asyncio
    async def test_stake_payout_service_fulfill_reservation(self):
        stake_id = uuid4()
        dist = _make_distribution(amount=500, source_streamer_id=38, stake_id=stake_id)
        deal = _make_deal(amount=5000, stake_reserved=500)
        mock_stake = _make_stake(stake_id=stake_id, currency="RUB")

        uow = _make_uow()
        uow.stake.get_by.return_value = mock_stake
        uow.deals.get_active.return_value = deal
        uow.deals.fulfill_reservation.return_value = 1

        payout_result = MagicMock()
        payout_result.status = TransactionStatusEnum.completed

        tinkoff = MagicMock()
        tinkoff.make_pay_out = AsyncMock(return_value=payout_result)

        oxypay = MagicMock()

        service = StakePayoutService(uow, tinkoff, oxypay)
        withdraw_method = MagicMock()

        result = await service.process_stake_withdrawal(dist, withdraw_method)

        assert result == TransactionStatusEnum.completed
        uow.deals.fulfill_reservation.assert_called_once_with(deal.deal_id, 500)
        uow.stake_distribution.update.assert_called_once_with(
            dist.id, payout_status="paid_out"
        )

    @pytest.mark.asyncio
    async def test_stake_payout_service_failed_payout_marks_failed(self):
        stake_id = uuid4()
        dist = _make_distribution(amount=500, source_streamer_id=38, stake_id=stake_id)
        deal = _make_deal(amount=5000, stake_reserved=500)
        mock_stake = _make_stake(stake_id=stake_id, currency="RUB")

        uow = _make_uow()
        uow.stake.get_by.return_value = mock_stake
        uow.deals.get_active.return_value = deal
        uow.deals.fulfill_reservation.return_value = 1

        payout_result = MagicMock()
        payout_result.status = TransactionStatusEnum.failed

        tinkoff = MagicMock()
        tinkoff.make_pay_out = AsyncMock(return_value=payout_result)

        oxypay = MagicMock()

        service = StakePayoutService(uow, tinkoff, oxypay)
        withdraw_method = MagicMock()

        result = await service.process_stake_withdrawal(dist, withdraw_method)

        assert result == TransactionStatusEnum.failed
        uow.stake_distribution.update.assert_called_once_with(
            dist.id, payout_status="failed"
        )


# ---------------------------------------------------------------------------
# Deal rotation
# ---------------------------------------------------------------------------


class TestDealRotation:
    @pytest.mark.asyncio
    async def test_rotation_skips_deal_with_stake_reserved(self):
        from src.scheduler.tasks.tasks.rotate_expired_deals import (
            RotateExpiredDealsTask,
        )

        deal_reserved = _make_deal(
            deal_id="deal_reserved", amount=3000, stake_reserved=1000
        )
        deal_free = _make_deal(deal_id="deal_free", amount=2000, stake_reserved=0)

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        mock_uow = MagicMock()
        mock_uow.deals = MagicMock()
        mock_uow.deals.get_expiring_deals = AsyncMock(
            return_value=[deal_reserved, deal_free]
        )
        mock_uow.deals.lock_deal = AsyncMock(return_value=1)
        mock_uow.deals.close = AsyncMock()
        mock_uow.deals.create = AsyncMock()
        mock_uow.deals.unlock_deal = AsyncMock()

        mock_deal_resp = MagicMock()
        mock_deal_resp.success = True
        mock_deal_resp.deal_id = "new_deal"

        with (
            patch(
                "src.scheduler.tasks.tasks.rotate_expired_deals.db_helper"
            ) as mock_db,
            patch(
                "src.scheduler.tasks.tasks.rotate_expired_deals.tinkoff_client"
            ) as mock_client,
            patch(
                "src.scheduler.tasks.tasks.rotate_expired_deals.TinkoffUnitOfWork",
                return_value=mock_uow,
            ),
        ):
            cm = AsyncMock()
            cm.__aenter__ = AsyncMock(return_value=mock_session)
            cm.__aexit__ = AsyncMock(return_value=False)
            mock_db.get_async_session_not_closed.return_value = cm

            mock_client.close_deal = AsyncMock()
            mock_client.create_deal = AsyncMock(return_value=mock_deal_resp)

            task = RotateExpiredDealsTask()
            await task.execute()

            mock_uow.deals.lock_deal.assert_called_once_with("deal_free")
            lock_calls = [c[0][0] for c in mock_uow.deals.lock_deal.call_args_list]
            assert "deal_reserved" not in lock_calls
