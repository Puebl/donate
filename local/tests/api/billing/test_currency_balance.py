import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.api.billing.service import BillingService
from src.core.database.enums.balances import OperationTypeEnum


def _make_uow(**overrides):
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)
    uow.rollback = AsyncMock()

    uow.balance = MagicMock()
    uow.balance.get_actual_balance = AsyncMock(return_value=None)
    uow.balance.init_new_balance = AsyncMock()
    uow.balance.create = AsyncMock()

    uow.commissions = MagicMock()
    uow.commissions.get_rates = AsyncMock(return_value=None)

    for k, v in overrides.items():
        setattr(uow, k, v)
    return uow


class TestCurrencyBalance:
    @pytest.mark.asyncio
    async def test_rub_deposit_only_updates_rub_balance(self):
        uow = _make_uow()
        actual_balance = MagicMock()
        actual_balance.balance_total = 0
        uow.balance.get_actual_balance.return_value = actual_balance

        stake_service = MagicMock()
        service = BillingService(uow, stake_service)

        await service.process_operation(
            streamer_id=1,
            request_amount=1000,
            operation_type=OperationTypeEnum.t_deposit_sbp,
            transaction_id=uuid4(),
            commission=0,
            currency="RUB",
        )

        assert uow.balance.create.call_count >= 1
        first_call_kwargs = uow.balance.create.call_args_list[0][1]
        assert first_call_kwargs["currency"] == "RUB"

    @pytest.mark.asyncio
    async def test_usd_deposit_only_updates_usd_balance(self):
        uow = _make_uow()
        actual_balance = MagicMock()
        actual_balance.balance_total = 0
        uow.balance.get_actual_balance.return_value = actual_balance

        stake_service = MagicMock()
        service = BillingService(uow, stake_service)

        await service.process_operation(
            streamer_id=1,
            request_amount=1000,
            operation_type=OperationTypeEnum.ox_deposit_card,
            transaction_id=uuid4(),
            commission=0,
            currency="USD",
        )

        assert uow.balance.create.call_count >= 1
        first_call_kwargs = uow.balance.create.call_args_list[0][1]
        assert first_call_kwargs["currency"] == "USD"

    @pytest.mark.asyncio
    async def test_get_main_balance_returns_zero_for_empty_currency(self):
        uow = _make_uow()
        uow.balance.get_actual_balance.return_value = None

        stake_service = MagicMock()
        service = BillingService(uow, stake_service)

        result = await service.get_main_balance(1, "USD")

        assert result == 0
        uow.balance.get_actual_balance.assert_called_once_with(1, currency="USD")

    @pytest.mark.asyncio
    async def test_initialize_balance_creates_both_currencies(self):
        uow = _make_uow()

        stake_service = MagicMock()
        service = BillingService(uow, stake_service)

        await service.initialize_balance(1)

        assert uow.balance.init_new_balance.call_count == 2
        calls = [c[0] for c in uow.balance.init_new_balance.call_args_list]
        assert (1, "RUB") in calls
        assert (1, "USD") in calls
