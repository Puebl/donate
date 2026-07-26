import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi import HTTPException

from src.api.transaction.service import TransactionService
from src.api.payment_gateways.constants import TinkoffPaymentMethod, OxypayPaymentMethod
from src.core.database.enums.transactions import (
    PaymentProviderEnum,
    TransactionStatusEnum,
)
from src.core.database.models.stake_outcome import StakeOutcome


def _make_uow(**overrides):
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)
    uow.rollback = AsyncMock()

    uow.transaction = MagicMock()
    uow.transaction.get_by = AsyncMock(return_value=None)
    uow.transaction.create = AsyncMock()
    uow.transaction.update = AsyncMock()

    uow.stake_outcome = MagicMock()
    uow.stake_outcome.get_full = AsyncMock()

    for k, v in overrides.items():
        setattr(uow, k, v)
    return uow


class TestCurrencyValidation:
    @pytest.mark.asyncio
    async def test_rub_deposit_to_usd_stake_rejected(self):
        outcome_id = uuid4()

        mock_stake = MagicMock()
        mock_stake.currency = "USD"

        mock_outcome = MagicMock()
        mock_outcome.stake = mock_stake

        uow = _make_uow()
        uow.stake_outcome.get_full.return_value = mock_outcome

        billing_service = MagicMock()
        billing_service.exchange_currency = MagicMock(return_value=10000)
        billing_service.calculate_operation = AsyncMock()

        tinkoff_service = MagicMock()
        tinkoff_service.make_pay_in = AsyncMock()

        oxypay_service = MagicMock()
        stake_service = MagicMock()

        service = TransactionService(
            uow, billing_service, tinkoff_service, oxypay_service, stake_service
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.request_deposit(
                streamer_id=1,
                external_transaction_id="test-rub-to-usd",
                provider=PaymentProviderEnum.tinkoff,
                payment_method=TinkoffPaymentMethod.t_sbp,
                amount=100,
                outcome_id=outcome_id,
            )
        assert exc_info.value.status_code == 400
        assert "currency mismatch" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_usd_deposit_to_rub_stake_rejected(self):
        outcome_id = uuid4()

        mock_stake = MagicMock()
        mock_stake.currency = "RUB"

        mock_outcome = MagicMock()
        mock_outcome.stake = mock_stake

        uow = _make_uow()
        uow.stake_outcome.get_full.return_value = mock_outcome

        billing_service = MagicMock()
        billing_service.exchange_currency = MagicMock(return_value=10000)
        billing_service.calculate_operation = AsyncMock()

        tinkoff_service = MagicMock()
        oxypay_service = MagicMock()
        oxypay_service.make_pay_in = AsyncMock()
        stake_service = MagicMock()

        service = TransactionService(
            uow, billing_service, tinkoff_service, oxypay_service, stake_service
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.request_deposit(
                streamer_id=1,
                external_transaction_id="test-usd-to-rub",
                provider=PaymentProviderEnum.oxypay,
                payment_method=OxypayPaymentMethod.ox_card,
                amount=100,
                outcome_id=outcome_id,
            )
        assert exc_info.value.status_code == 400
        assert "currency mismatch" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_request_withdraw_uses_correct_currency_balance(self):
        uow = _make_uow()
        uow.transaction.get_by.return_value = None

        mock_transaction = MagicMock()
        mock_transaction.id = uuid4()
        mock_transaction.commission = None
        uow.transaction.create.return_value = mock_transaction

        billing_service = MagicMock()
        billing_service.get_main_balance = AsyncMock(return_value=5000)
        billing_service.process_operation = AsyncMock(
            return_value=MagicMock(amount_to_send=-5000, commission=0)
        )

        payout_resp = MagicMock()
        payout_resp.status = TransactionStatusEnum.completed

        tinkoff_service = MagicMock()
        oxypay_service = MagicMock()
        oxypay_service.make_pay_out = AsyncMock(return_value=payout_resp)
        stake_service = MagicMock()

        service = TransactionService(
            uow, billing_service, tinkoff_service, oxypay_service, stake_service
        )

        user_service = MagicMock()
        user_service.get_main_withdraw_method = AsyncMock(
            return_value=MagicMock(
                phone=None,
                card_id="card_123",
                payment_provider=PaymentProviderEnum.oxypay,
            )
        )

        withdraw_method = MagicMock()
        withdraw_method.phone = None
        withdraw_method.card_id = "card_123"

        await service.request_withdraw(
            user_service=user_service,
            streamer_id=1,
            payment_provider=PaymentProviderEnum.oxypay,
            request_amount=None,
            withdraw_method=withdraw_method,
        )

        billing_service.get_main_balance.assert_called_once_with(1, currency="USD")
