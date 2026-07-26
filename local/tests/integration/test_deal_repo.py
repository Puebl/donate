"""
Integration tests for DealRepo against real PostgreSQL.

These tests verify DB operations: create, get_active, add/subtract_amount,
lock/unlock, get_expiring_deals.
"""

from datetime import timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.payment_gateways.tinkoff.repo import DealRepo
from src.core.database.models import Deal
from src.core.database.utils import get_utc_now


# ──────────────────────────────────────────────────────────────────────
# get_active
# ──────────────────────────────────────────────────────────────────────


class TestGetActive:
    """DealRepo.get_active — получение активной сделки стримера."""

    async def test_get_active_returns_open_deal(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Возвращает сделку с open_status=True."""
        deal = await deal_factory(streamer_id=1, open_status=True, deal_type="NN")

        repo = DealRepo(payment_session)
        result = await repo.get_active(streamer_id=1)

        assert result is not None
        assert result.deal_id == deal.deal_id
        assert result.open_status is True

    async def test_get_active_ignores_closed(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Не возвращает сделку с open_status=False."""
        await deal_factory(streamer_id=2, open_status=False, deal_type="NN")

        repo = DealRepo(payment_session)
        result = await repo.get_active(streamer_id=2)

        assert result is None

    async def test_get_active_returns_none_for_unknown_streamer(
        self, payment_session: AsyncSession
    ):
        """Возвращает None если у стримера нет сделок."""
        repo = DealRepo(payment_session)
        result = await repo.get_active(streamer_id=99999)

        assert result is None

    async def test_get_active_with_for_update(
        self, payment_session: AsyncSession, deal_factory
    ):
        """for_update=True не ломает запрос (SELECT FOR UPDATE)."""
        await deal_factory(streamer_id=3, open_status=True, deal_type="NN")

        repo = DealRepo(payment_session)
        result = await repo.get_active(streamer_id=3, for_update=True)

        assert result is not None

    async def test_get_active_prefers_nn_over_nothing(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Если есть и N1 (закрытая) и NN (открытая), возвращает NN."""
        await deal_factory(streamer_id=4, open_status=False, deal_type="N1")
        nn_deal = await deal_factory(streamer_id=4, open_status=True, deal_type="NN")

        repo = DealRepo(payment_session)
        result = await repo.get_active(streamer_id=4)

        assert result is not None
        assert result.deal_id == nn_deal.deal_id
        assert result.deal_type == "NN"


# ──────────────────────────────────────────────────────────────────────
# add_amount
# ──────────────────────────────────────────────────────────────────────


class TestAddAmount:
    """DealRepo.add_amount — увеличение баланса сделки."""

    async def test_add_amount_increments(
        self, payment_session: AsyncSession, deal_factory
    ):
        """add_amount прибавляет сумму к текущему amount."""
        deal = await deal_factory(streamer_id=10, amount=0, deal_type="NN")

        repo = DealRepo(payment_session)
        await repo.add_amount(deal.deal_id, 5000)
        await payment_session.commit()

        await payment_session.refresh(deal)
        assert deal.amount == 5000

    async def test_add_amount_cumulative(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Несколько вызовов add_amount складываются."""
        deal = await deal_factory(streamer_id=11, amount=1000, deal_type="NN")

        repo = DealRepo(payment_session)
        await repo.add_amount(deal.deal_id, 500)
        await repo.add_amount(deal.deal_id, 300)
        await payment_session.commit()

        await payment_session.refresh(deal)
        assert deal.amount == 1800


# ──────────────────────────────────────────────────────────────────────
# subtract_amount
# ──────────────────────────────────────────────────────────────────────


class TestSubtractAmount:
    """DealRepo.subtract_amount — уменьшение баланса сделки с защитой от отрицательных значений."""

    async def test_subtract_amount_success(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Вычитание суммы когда баланс достаточен."""
        deal = await deal_factory(streamer_id=20, amount=10000, deal_type="NN")

        repo = DealRepo(payment_session)
        rows = await repo.subtract_amount(deal.deal_id, 3000)
        await payment_session.commit()

        assert rows == 1
        await payment_session.refresh(deal)
        assert deal.amount == 7000

    async def test_subtract_amount_exact_balance(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Вычитание ровно всего баланса — amount = 0."""
        deal = await deal_factory(streamer_id=21, amount=5000, deal_type="NN")

        repo = DealRepo(payment_session)
        rows = await repo.subtract_amount(deal.deal_id, 5000)
        await payment_session.commit()

        assert rows == 1
        await payment_session.refresh(deal)
        assert deal.amount == 0

    async def test_subtract_amount_insufficient_balance(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Вычитание больше баланса — 0 rows affected, баланс не изменен."""
        deal = await deal_factory(streamer_id=22, amount=1000, deal_type="NN")

        repo = DealRepo(payment_session)
        rows = await repo.subtract_amount(deal.deal_id, 2000)
        await payment_session.commit()

        assert rows == 0
        await payment_session.refresh(deal)
        assert deal.amount == 1000  # Не изменился

    async def test_subtract_amount_zero_balance(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Вычитание из нулевого баланса — 0 rows affected."""
        deal = await deal_factory(streamer_id=23, amount=0, deal_type="NN")

        repo = DealRepo(payment_session)
        rows = await repo.subtract_amount(deal.deal_id, 100)

        assert rows == 0


# ──────────────────────────────────────────────────────────────────────
# lock_deal / unlock_deal
# ──────────────────────────────────────────────────────────────────────


class TestLockUnlock:
    """DealRepo.lock_deal / unlock_deal — блокировка сделки для ротации."""

    async def test_lock_deal_success(self, payment_session: AsyncSession, deal_factory):
        """lock_deal блокирует незалоченную сделку."""
        deal = await deal_factory(streamer_id=30, deal_type="NN")

        repo = DealRepo(payment_session)
        rows = await repo.lock_deal(deal.deal_id)
        await payment_session.commit()

        assert rows == 1
        await payment_session.refresh(deal)
        assert deal.is_locked is True

    async def test_lock_deal_already_locked(
        self, payment_session: AsyncSession, deal_factory
    ):
        """lock_deal на уже залоченной сделке — 0 rows affected (CAS)."""
        deal = await deal_factory(streamer_id=31, deal_type="NN")

        repo = DealRepo(payment_session)
        await repo.lock_deal(deal.deal_id)
        await payment_session.commit()

        # Второй lock
        rows = await repo.lock_deal(deal.deal_id)
        assert rows == 0

    async def test_unlock_deal(self, payment_session: AsyncSession, deal_factory):
        """unlock_deal снимает блокировку."""
        deal = await deal_factory(streamer_id=32, deal_type="NN")

        repo = DealRepo(payment_session)
        await repo.lock_deal(deal.deal_id)
        await payment_session.commit()

        await repo.unlock_deal(deal.deal_id)
        await payment_session.commit()

        await payment_session.refresh(deal)
        assert deal.is_locked is False

    async def test_lock_unlock_cycle(self, payment_session: AsyncSession, deal_factory):
        """Полный цикл: lock → unlock → lock снова."""
        deal = await deal_factory(streamer_id=33, deal_type="NN")

        repo = DealRepo(payment_session)

        # Lock
        rows = await repo.lock_deal(deal.deal_id)
        assert rows == 1

        # Unlock
        await repo.unlock_deal(deal.deal_id)
        await payment_session.commit()

        # Lock again
        rows = await repo.lock_deal(deal.deal_id)
        assert rows == 1


# ──────────────────────────────────────────────────────────────────────
# get_expiring_deals
# ──────────────────────────────────────────────────────────────────────


class TestGetExpiringDeals:
    """DealRepo.get_expiring_deals — поиск сделок с истекающим сроком."""

    async def test_finds_expiring_nn_deal(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Находит NN-сделку, expires_at <= now + 5 дней."""
        await deal_factory(
            streamer_id=40,
            deal_type="NN",
            expires_at=get_utc_now() + timedelta(days=3),  # Истекает через 3 дня
            open_status=True,
        )

        repo = DealRepo(payment_session)
        deals = await repo.get_expiring_deals(days_before_expiry=5)

        assert len(deals) == 1
        assert deals[0].streamer_id == 40

    async def test_ignores_far_future_deal(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Не находит сделку с expires_at далеко в будущем."""
        await deal_factory(
            streamer_id=41,
            deal_type="NN",
            expires_at=get_utc_now() + timedelta(days=30),  # Ещё 30 дней
            open_status=True,
        )

        repo = DealRepo(payment_session)
        deals = await repo.get_expiring_deals(days_before_expiry=5)

        assert len(deals) == 0

    async def test_ignores_closed_deal(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Не находит закрытую сделку (open_status=False)."""
        await deal_factory(
            streamer_id=42,
            deal_type="NN",
            expires_at=get_utc_now() + timedelta(days=2),
            open_status=False,
        )

        repo = DealRepo(payment_session)
        deals = await repo.get_expiring_deals(days_before_expiry=5)

        assert len(deals) == 0

    async def test_ignores_n1_deal(self, payment_session: AsyncSession, deal_factory):
        """Не находит N1-сделку (только NN)."""
        await deal_factory(
            streamer_id=43,
            deal_type="N1",
            expires_at=get_utc_now() + timedelta(days=2),
            open_status=True,
        )

        repo = DealRepo(payment_session)
        deals = await repo.get_expiring_deals(days_before_expiry=5)

        assert len(deals) == 0

    async def test_ignores_locked_deal(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Не находит залоченную сделку (is_locked=True)."""
        deal = await deal_factory(
            streamer_id=44,
            deal_type="NN",
            expires_at=get_utc_now() + timedelta(days=2),
            open_status=True,
        )

        repo = DealRepo(payment_session)
        await repo.lock_deal(deal.deal_id)
        await payment_session.commit()

        deals = await repo.get_expiring_deals(days_before_expiry=5)
        assert len(deals) == 0

    async def test_ignores_deal_without_expires_at(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Не находит сделку без expires_at (NULL)."""
        await deal_factory(
            streamer_id=45,
            deal_type="NN",
            expires_at=None,
            open_status=True,
        )

        repo = DealRepo(payment_session)
        deals = await repo.get_expiring_deals(days_before_expiry=5)

        assert len(deals) == 0

    async def test_multiple_expiring_deals(
        self, payment_session: AsyncSession, deal_factory
    ):
        """Возвращает все подходящие сделки."""
        for i in range(3):
            await deal_factory(
                streamer_id=50 + i,
                deal_type="NN",
                expires_at=get_utc_now() + timedelta(days=i + 1),
                open_status=True,
            )

        repo = DealRepo(payment_session)
        deals = await repo.get_expiring_deals(days_before_expiry=5)

        assert len(deals) == 3


# ──────────────────────────────────────────────────────────────────────
# close
# ──────────────────────────────────────────────────────────────────────


class TestClose:
    """DealRepo.close — закрытие сделки в БД."""

    async def test_close_sets_open_status_false(
        self, payment_session: AsyncSession, deal_factory
    ):
        """close() устанавливает open_status=False."""
        deal = await deal_factory(streamer_id=60, open_status=True, deal_type="NN")

        repo = DealRepo(payment_session)
        await repo.close(deal.deal_id)
        await payment_session.commit()

        await payment_session.refresh(deal)
        assert deal.open_status is False

    async def test_close_does_not_affect_other_deals(
        self, payment_session: AsyncSession, deal_factory
    ):
        """close() закрывает только указанную сделку."""
        deal1 = await deal_factory(streamer_id=61, open_status=True, deal_type="NN")
        deal2 = await deal_factory(streamer_id=62, open_status=True, deal_type="NN")

        repo = DealRepo(payment_session)
        await repo.close(deal1.deal_id)
        await payment_session.commit()

        await payment_session.refresh(deal1)
        await payment_session.refresh(deal2)
        assert deal1.open_status is False
        assert deal2.open_status is True
