"""
Integration tests for TinkoffService with real DB + mocked Tinkoff HTTP client.

Tests the service-layer logic: _ensure_deal, confirm_deposit, _process_deal_pay_pay_out.
"""

import uuid
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.payment_gateways.tinkoff.client.schemas import TinkoffDealResponse
from src.api.payment_gateways.tinkoff.exceptions import (
    DealCreationError,
    DealLockedError,
    PayoutError,
)
from src.api.payment_gateways.tinkoff.repo import DealRepo
from src.api.payment_gateways.tinkoff.service import TinkoffService
from src.api.payment_gateways.tinkoff.uow import TinkoffUnitOfWork
from src.core.database.models import Deal
from src.core.database.utils import get_utc_now


# ──────────────────────────────────────────────────────────────────────
# _ensure_deal
# ──────────────────────────────────────────────────────────────────────


class TestEnsureDeal:
    """TinkoffService._ensure_deal — создание/получение сделки в БД."""

    @patch("src.api.payment_gateways.tinkoff.service.tinkoff_client")
    async def test_ensure_deal_creates_nn_when_no_active(
        self, mock_client, payment_session: AsyncSession
    ):
        """Когда нет активной сделки — создаёт новую NN через API и сохраняет в БД."""
        mock_client.create_deal = AsyncMock(
            return_value=MagicMock(success=True, deal_id="deal_new_123")
        )

        uow = TinkoffUnitOfWork(payment_session)
        service = TinkoffService(uow)

        deal = await service._ensure_deal(streamer_id=100)

        assert deal.deal_id == "deal_new_123"
        assert deal.deal_type == "NN"
        assert deal.open_status is True
        assert deal.streamer_id == 100
        assert deal.expires_at is not None
        mock_client.create_deal.assert_called_once_with(deal_type="NN")

    async def test_ensure_deal_returns_existing(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Когда есть активная сделка — возвращает её, не создаёт новую."""
        existing = await deal_factory(
            streamer_id=101, open_status=True, deal_type="NN", amount=5000
        )

        uow = TinkoffUnitOfWork(payment_session)
        service = TinkoffService(uow)

        deal = await service._ensure_deal(streamer_id=101)

        assert deal.deal_id == existing.deal_id
        assert deal.amount == 5000

    @patch("src.api.payment_gateways.tinkoff.service.tinkoff_client")
    async def test_ensure_deal_api_failure_raises(
        self, mock_client, payment_session: AsyncSession
    ):
        """Когда API возвращает success=False — DealCreationError."""
        mock_client.create_deal = AsyncMock(
            return_value=MagicMock(success=False, message="API error")
        )

        uow = TinkoffUnitOfWork(payment_session)
        service = TinkoffService(uow)

        with pytest.raises(DealCreationError):
            await service._ensure_deal(streamer_id=102)


# ──────────────────────────────────────────────────────────────────────
# confirm_deposit
# ──────────────────────────────────────────────────────────────────────


class TestConfirmDeposit:
    """TinkoffService.confirm_deposit — фиксация доната в БД."""

    async def test_confirm_deposit_adds_amount(
        self, payment_session: AsyncSession, deal_factory, transaction_factory
    ):
        """confirm_deposit увеличивает deal.amount и создаёт Payment."""
        deal = await deal_factory(
            streamer_id=200, amount=1000, deal_type="NN", open_status=True
        )
        tx = await transaction_factory(streamer_id=200)

        uow = TinkoffUnitOfWork(payment_session)
        service = TinkoffService(uow)

        await service.confirm_deposit(
            transaction_id=tx.id,
            order_id=str(uuid.uuid4()),
            streamer_id=200,
            amount=3000,
            deal_id=deal.deal_id,
        )
        await payment_session.commit()

        await payment_session.refresh(deal)
        assert deal.amount == 4000

    async def test_confirm_deposit_uses_webhook_deal_id(
        self, payment_session: AsyncSession, deal_factory, transaction_factory
    ):
        """Когда deal_id передан (из webhook) — используется именно он, без вызова _ensure_deal."""
        deal = await deal_factory(
            streamer_id=201, amount=0, deal_type="NN", open_status=True
        )
        tx = await transaction_factory(streamer_id=201)

        uow = TinkoffUnitOfWork(payment_session)
        service = TinkoffService(uow)

        await service.confirm_deposit(
            transaction_id=tx.id,
            order_id=str(uuid.uuid4()),
            streamer_id=201,
            amount=5000,
            deal_id=deal.deal_id,
        )
        await payment_session.commit()

        await payment_session.refresh(deal)
        assert deal.amount == 5000

    @patch("src.api.payment_gateways.tinkoff.service.tinkoff_client")
    async def test_confirm_deposit_without_deal_id_calls_ensure(
        self,
        mock_client,
        payment_session: AsyncSession,
        deal_factory,
        transaction_factory,
    ):
        """Когда deal_id=None — вызывается _ensure_deal для определения сделки."""
        deal = await deal_factory(
            streamer_id=202, amount=0, deal_type="NN", open_status=True
        )
        tx = await transaction_factory(streamer_id=202)

        uow = TinkoffUnitOfWork(payment_session)
        service = TinkoffService(uow)

        await service.confirm_deposit(
            transaction_id=tx.id,
            order_id=str(uuid.uuid4()),
            streamer_id=202,
            amount=2000,
        )
        await payment_session.commit()

        await payment_session.refresh(deal)
        assert deal.amount == 2000
        mock_client.create_deal.assert_not_called()


# ──────────────────────────────────────────────────────────────────────
# _process_deal_pay_pay_out
# ──────────────────────────────────────────────────────────────────────


class TestProcessDealPayOut:
    """TinkoffService._process_deal_pay_pay_out — обработка сделки для выплаты."""

    async def test_nn_deal_partial_payout(
        self, payment_session: AsyncSession, deal_factory
    ):
        """NN-сделка: частичная выплата, FinalPayout=False, amount уменьшается."""
        deal = await deal_factory(
            streamer_id=300, amount=10000, deal_type="NN", open_status=True
        )

        uow = TinkoffUnitOfWork(payment_session)
        service = TinkoffService(uow)

        result_deal, final_payout = await service._process_deal_pay_pay_out(300, 3000)
        await payment_session.commit()

        assert final_payout is False
        assert result_deal.deal_id == deal.deal_id

        await payment_session.refresh(deal)
        assert deal.amount == 7000  # 10000 - 3000
        assert deal.open_status is True  # Сделка остается открытой

    async def test_n1_deal_full_payout(
        self, payment_session: AsyncSession, deal_factory
    ):
        """N1-сделка: полный вывод, FinalPayout=True, сделка закрывается."""
        deal = await deal_factory(
            streamer_id=301, amount=5000, deal_type="N1", open_status=True
        )

        uow = TinkoffUnitOfWork(payment_session)
        service = TinkoffService(uow)

        result_deal, final_payout = await service._process_deal_pay_pay_out(301, 5000)
        await payment_session.commit()

        assert final_payout is True
        await payment_session.refresh(deal)
        assert deal.open_status is False  # N1 закрывается

    async def test_no_active_deal_raises(self, payment_session: AsyncSession):
        """Нет активной сделки — PayoutError."""
        uow = TinkoffUnitOfWork(payment_session)
        service = TinkoffService(uow)

        with pytest.raises(PayoutError, match="No active deal found"):
            await service._process_deal_pay_pay_out(999, 1000)

    async def test_locked_deal_raises(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Залоченная сделка — DealLockedError."""
        deal = await deal_factory(
            streamer_id=302, amount=5000, deal_type="NN", open_status=True
        )
        repo = DealRepo(payment_session)
        await repo.lock_deal(deal.deal_id)
        await payment_session.commit()

        uow = TinkoffUnitOfWork(payment_session)
        service = TinkoffService(uow)

        with pytest.raises(DealLockedError):
            await service._process_deal_pay_pay_out(302, 1000)

    async def test_insufficient_balance_raises(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Недостаточно средств — PayoutError."""
        await deal_factory(
            streamer_id=303, amount=500, deal_type="NN", open_status=True
        )

        uow = TinkoffUnitOfWork(payment_session)
        service = TinkoffService(uow)

        with pytest.raises(PayoutError, match="Insufficient deal balance"):
            await service._process_deal_pay_pay_out(303, 1000)

    async def test_minimum_amount_100_kopecks(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Минимальная сумма выплаты — 100 копеек (1 рубль)."""
        await deal_factory(
            streamer_id=304, amount=10000, deal_type="NN", open_status=True
        )

        uow = TinkoffUnitOfWork(payment_session)
        service = TinkoffService(uow)

        with pytest.raises(PayoutError, match="Minimum payout amount"):
            await service._process_deal_pay_pay_out(304, 50)

    async def test_nn_multiple_partial_payouts(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Несколько частичных выплат из NN-сделки — баланс уменьшается корректно."""
        deal = await deal_factory(
            streamer_id=305, amount=10000, deal_type="NN", open_status=True
        )

        uow = TinkoffUnitOfWork(payment_session)
        service = TinkoffService(uow)

        _, fp1 = await service._process_deal_pay_pay_out(305, 3000)
        await payment_session.commit()
        assert fp1 is False

        _, fp2 = await service._process_deal_pay_pay_out(305, 4000)
        await payment_session.commit()
        assert fp2 is False

        await payment_session.refresh(deal)
        assert deal.amount == 3000  # 10000 - 3000 - 4000
        assert deal.open_status is True

    async def test_nn_payout_drains_to_zero(
        self, payment_session: AsyncSession, deal_factory
    ):
        """NN-сделка: вывод всего баланса — amount=0, сделка всё равно открыта."""
        deal = await deal_factory(
            streamer_id=306, amount=5000, deal_type="NN", open_status=True
        )

        uow = TinkoffUnitOfWork(payment_session)
        service = TinkoffService(uow)

        _, final_payout = await service._process_deal_pay_pay_out(306, 5000)
        await payment_session.commit()

        assert final_payout is False
        await payment_session.refresh(deal)
        assert deal.amount == 0
        assert deal.open_status is True  # NN не закрывается!
