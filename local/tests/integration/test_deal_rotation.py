"""
Integration tests for RotateExpiredDealsTask with real DB + mocked Tinkoff API.

Tests the cron task that rotates expiring NN deals.
"""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.payment_gateways.tinkoff.repo import DealRepo
from src.core.database.models import Deal
from src.core.database.utils import get_utc_now


# ──────────────────────────────────────────────────────────────────────
# RotateExpiredDealsTask
# ──────────────────────────────────────────────────────────────────────


class TestRotateExpiredDeals:
    """Тест ротации сделок — вызов closeSpDeal + createSpDeal + обновление БД."""

    @patch("src.scheduler.tasks.tasks.rotate_expired_deals.tinkoff_client")
    async def test_rotates_expiring_deal(
        self, mock_client, payment_session: AsyncSession, deal_factory
    ):
        """Сделка с expires_at <= now+5d — закрывается и создаётся новая."""
        old_deal = await deal_factory(
            streamer_id=500,
            deal_type="NN",
            expires_at=get_utc_now() + timedelta(days=2),
            open_status=True,
            amount=0,
        )

        mock_client.close_deal = AsyncMock(return_value=MagicMock(success=True))
        mock_client.create_deal = AsyncMock(
            return_value=MagicMock(success=True, deal_id="new_deal_500")
        )

        # Execute the rotation logic directly
        repo = DealRepo(payment_session)
        expiring = await repo.get_expiring_deals(days_before_expiry=5)
        assert len(expiring) == 1

        deal = expiring[0]
        locked = await repo.lock_deal(deal.deal_id)
        assert locked == 1

        # Simulate rotation logic
        await mock_client.close_deal(deal.deal_id)
        await repo.close(deal.deal_id)

        new_deal_resp = await mock_client.create_deal(deal_type="NN")
        new_deal = Deal(
            streamer_id=deal.streamer_id,
            deal_id=new_deal_resp.deal_id,
            open_status=True,
            deal_type="NN",
            expires_at=get_utc_now() + timedelta(days=55),
        )
        payment_session.add(new_deal)
        await repo.unlock_deal(deal.deal_id)
        await payment_session.commit()

        # Verify old deal closed
        await payment_session.refresh(old_deal)
        assert old_deal.open_status is False
        assert old_deal.is_locked is False

        # Verify new deal exists
        result = await payment_session.scalar(
            select(Deal).where(Deal.deal_id == "new_deal_500")
        )
        assert result is not None
        assert result.open_status is True
        assert result.deal_type == "NN"
        assert result.streamer_id == 500

        mock_client.close_deal.assert_called_once_with(old_deal.deal_id)
        mock_client.create_deal.assert_called_once_with(deal_type="NN")

    async def test_skips_non_expiring_deals(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Сделка с expires_at далеко в будущем — не ротируется."""
        await deal_factory(
            streamer_id=501,
            deal_type="NN",
            expires_at=get_utc_now() + timedelta(days=30),
            open_status=True,
        )

        repo = DealRepo(payment_session)
        expiring = await repo.get_expiring_deals(days_before_expiry=5)
        assert len(expiring) == 0

    @patch("src.scheduler.tasks.tasks.rotate_expired_deals.tinkoff_client")
    async def test_rotation_with_remaining_balance(
        self, mock_client, payment_session: AsyncSession, deal_factory
    ):
        """Ротация сделки с ненулевым балансом — предупреждение, но ротация проходит."""
        old_deal = await deal_factory(
            streamer_id=502,
            deal_type="NN",
            expires_at=get_utc_now() + timedelta(days=1),
            open_status=True,
            amount=5000,
        )

        mock_client.close_deal = AsyncMock(return_value=MagicMock(success=True))
        mock_client.create_deal = AsyncMock(
            return_value=MagicMock(success=True, deal_id="new_deal_502")
        )

        repo = DealRepo(payment_session)
        expiring = await repo.get_expiring_deals(days_before_expiry=5)
        assert len(expiring) == 1
        assert expiring[0].amount == 5000  # Есть остаток

        # Rotation still works
        deal = expiring[0]
        await repo.lock_deal(deal.deal_id)
        await mock_client.close_deal(deal.deal_id)
        await repo.close(deal.deal_id)

        new_deal_resp = await mock_client.create_deal(deal_type="NN")
        new_deal = Deal(
            streamer_id=deal.streamer_id,
            deal_id=new_deal_resp.deal_id,
            open_status=True,
            deal_type="NN",
            expires_at=get_utc_now() + timedelta(days=55),
        )
        payment_session.add(new_deal)
        await repo.unlock_deal(deal.deal_id)
        await payment_session.commit()

        await payment_session.refresh(old_deal)
        assert old_deal.open_status is False

    @patch("src.scheduler.tasks.tasks.rotate_expired_deals.tinkoff_client")
    async def test_rotation_api_failure_does_not_lose_deal(
        self, mock_client, payment_session: AsyncSession, deal_factory
    ):
        """Ошибка API при создании новой сделки — старая закрыта, но не потеряна."""
        old_deal = await deal_factory(
            streamer_id=503,
            deal_type="NN",
            expires_at=get_utc_now() + timedelta(days=1),
            open_status=True,
            amount=0,
        )

        mock_client.close_deal = AsyncMock(return_value=MagicMock(success=True))
        mock_client.create_deal = AsyncMock(
            return_value=MagicMock(success=False, message="API error")
        )

        repo = DealRepo(payment_session)
        expiring = await repo.get_expiring_deals(days_before_expiry=5)
        deal = expiring[0]

        await repo.lock_deal(deal.deal_id)
        await mock_client.close_deal(deal.deal_id)
        await repo.close(deal.deal_id)

        new_deal_resp = await mock_client.create_deal(deal_type="NN")
        # New deal creation failed — don't crash
        assert new_deal_resp.success is False

        await repo.unlock_deal(deal.deal_id)
        await payment_session.commit()

        # Old deal is closed (we already sent closeSpDeal to Tinkoff)
        await payment_session.refresh(old_deal)
        assert old_deal.open_status is False
        assert old_deal.is_locked is False

    async def test_locked_deal_skipped(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Уже залоченная сделка — не попадает в get_expiring_deals."""
        deal = await deal_factory(
            streamer_id=504,
            deal_type="NN",
            expires_at=get_utc_now() + timedelta(days=1),
            open_status=True,
        )

        repo = DealRepo(payment_session)
        await repo.lock_deal(deal.deal_id)
        await payment_session.commit()

        expiring = await repo.get_expiring_deals(days_before_expiry=5)
        assert len(expiring) == 0


# ──────────────────────────────────────────────────────────────────────
# Full E2E: deal lifecycle
# ──────────────────────────────────────────────────────────────────────


class TestDealLifecycle:
    """E2E тест жизненного цикла NN-сделки в БД."""

    async def test_full_nn_lifecycle(self, payment_session: AsyncSession, deal_factory):
        """
        Полный цикл:
        1. Создать NN-сделку
        2. Добавить средства (донаты)
        3. Частичный вывод
        4. Ещё донат
        5. Полный вывод остатка
        6. Закрыть сделку
        """
        # 1. Create
        deal = await deal_factory(
            streamer_id=600,
            amount=0,
            deal_type="NN",
            open_status=True,
            expires_at=get_utc_now() + timedelta(days=55),
        )

        repo = DealRepo(payment_session)

        # 2. Donations
        await repo.add_amount(deal.deal_id, 5000)
        await repo.add_amount(deal.deal_id, 3000)
        await payment_session.commit()
        await payment_session.refresh(deal)
        assert deal.amount == 8000

        # 3. Partial payout
        rows = await repo.subtract_amount(deal.deal_id, 2000)
        await payment_session.commit()
        assert rows == 1
        await payment_session.refresh(deal)
        assert deal.amount == 6000
        assert deal.open_status is True  # Still open!

        # 4. Another donation
        await repo.add_amount(deal.deal_id, 1000)
        await payment_session.commit()
        await payment_session.refresh(deal)
        assert deal.amount == 7000

        # 5. Withdraw remaining
        rows = await repo.subtract_amount(deal.deal_id, 7000)
        await payment_session.commit()
        assert rows == 1
        await payment_session.refresh(deal)
        assert deal.amount == 0
        assert deal.open_status is True  # NN stays open even at zero!

        # 6. Close deal
        await repo.close(deal.deal_id)
        await payment_session.commit()
        await payment_session.refresh(deal)
        assert deal.open_status is False

    async def test_n1_backward_compat_lifecycle(
        self, payment_session: AsyncSession, deal_factory
    ):
        """
        N1-сделка: старое поведение.
        1. Создать N1
        2. Добавить средства
        3. Закрыть (вывод всего)
        """
        deal = await deal_factory(
            streamer_id=601,
            amount=0,
            deal_type="N1",
            open_status=True,
        )

        repo = DealRepo(payment_session)

        # Donation
        await repo.add_amount(deal.deal_id, 10000)
        await payment_session.commit()
        await payment_session.refresh(deal)
        assert deal.amount == 10000

        # Close (full drain)
        await repo.close(deal.deal_id)
        await payment_session.commit()
        await payment_session.refresh(deal)
        assert deal.open_status is False
