import pytest
from collections.abc import Callable, Coroutine
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.models import Transaction, Payment, Balance, Deal
from src.core.database.enums.transactions import (
    TransactionStatusEnum,
    PaymentProviderEnum,
)
from src.core.database.enums.balances import OperationTypeEnum


@pytest.fixture()
def transaction_factory(
    payment_session: AsyncSession,
    faker: Faker,
) -> Callable[..., Coroutine[None, None, Transaction]]:
    async def _factory(**kwargs: Any) -> Transaction:
        transaction = Transaction(
            streamer_id=kwargs.get("streamer_id", faker.random_int(min=1, max=1000)),
            amount=kwargs.get("amount", faker.random_int(min=100, max=100000)),
            status=kwargs.get("status", TransactionStatusEnum.pending),
            commission=kwargs.get("commission"),
            payment_provider=kwargs.get(
                "payment_provider", PaymentProviderEnum.tinkoff
            ),
            external_transaction_id=kwargs.get("external_transaction_id", str(uuid4())),
            operation_type=kwargs.get(
                "operation_type", OperationTypeEnum.t_deposit_sbp
            ),
            completed_at=kwargs.get("completed_at"),
            expires_at=kwargs.get("expires_at", datetime(2025, 12, 31)),
            outcome_id=kwargs.get("outcome_id"),
            user_id=kwargs.get("user_id"),
        )
        payment_session.add(transaction)
        await payment_session.commit()
        await payment_session.refresh(transaction)
        return transaction

    return _factory


@pytest.fixture()
def payment_transaction_factory(
    payment_session: AsyncSession,
    faker: Faker,
) -> Callable[..., Coroutine[None, None, Transaction]]:
    """Factory for transactions that represent payments."""

    async def _factory(**kwargs: Any) -> Transaction:
        transaction = Transaction(
            streamer_id=kwargs.get("streamer_id", faker.random_int(min=1, max=1000)),
            amount=kwargs.get("amount", faker.random_int(min=100, max=100000)),
            status=kwargs.get("status", TransactionStatusEnum.pending),
            commission=kwargs.get("commission", 0),
            payment_provider=kwargs.get(
                "payment_provider", PaymentProviderEnum.tinkoff
            ),
            external_transaction_id=kwargs.get("external_transaction_id", str(uuid4())),
            operation_type=kwargs.get(
                "operation_type", OperationTypeEnum.t_deposit_sbp
            ),
            completed_at=None,
            expires_at=kwargs.get("expires_at", datetime(2025, 12, 31)),
        )
        payment_session.add(transaction)
        await payment_session.commit()
        await payment_session.refresh(transaction)
        return transaction

    return _factory


@pytest.fixture()
def withdraw_transaction_factory(
    payment_session: AsyncSession,
    faker: Faker,
) -> Callable[..., Coroutine[None, None, Transaction]]:
    """Factory for withdraw transactions."""

    async def _factory(**kwargs: Any) -> Transaction:
        transaction = Transaction(
            streamer_id=kwargs.get("streamer_id", faker.random_int(min=1, max=1000)),
            amount=kwargs.get("amount", faker.random_int(min=100, max=100000)),
            status=kwargs.get("status", TransactionStatusEnum.pending),
            commission=kwargs.get("commission", faker.random_int(min=10, max=100)),
            payment_provider=kwargs.get(
                "payment_provider", PaymentProviderEnum.tinkoff
            ),
            external_transaction_id=kwargs.get("external_transaction_id", str(uuid4())),
            operation_type=kwargs.get("operation_type", OperationTypeEnum.withdraw),
            completed_at=None,
            expires_at=kwargs.get("expires_at", datetime(2025, 12, 31)),
        )
        payment_session.add(transaction)
        await payment_session.commit()
        await payment_session.refresh(transaction)
        return transaction

    return _factory


@pytest.fixture()
def payment_factory(
    payment_session: AsyncSession,
    faker: Faker,
) -> Callable[..., Coroutine[None, None, Payment]]:
    async def _factory(**kwargs: Any) -> Payment:
        payment = Payment(
            deal_id=kwargs.get("deal_id", faker.uuid4()),
            transaction_id=kwargs.get("transaction_id"),
            streamer_id=kwargs.get("streamer_id", faker.random_int(min=1, max=1000)),
            amount=kwargs.get("amount", faker.random_int(min=100, max=100000)),
        )
        payment_session.add(payment)
        await payment_session.commit()
        await payment_session.refresh(payment)
        return payment

    return _factory


@pytest.fixture()
def balance_factory(
    payment_session: AsyncSession,
    faker: Faker,
) -> Callable[..., Coroutine[None, None, Balance]]:
    async def _factory(**kwargs: Any) -> Balance:
        balance = Balance(
            operation_type=kwargs.get("operation_type", OperationTypeEnum.credit),
            balance_diff=kwargs.get(
                "balance_diff", faker.random_int(min=-10000, max=10000)
            ),
            balance_total=kwargs.get(
                "balance_total", faker.random_int(min=0, max=100000)
            ),
            streamer_id=kwargs.get("streamer_id", faker.random_int(min=1, max=1000)),
            transaction_id=kwargs.get("transaction_id"),
        )
        payment_session.add(balance)
        await payment_session.commit()
        await payment_session.refresh(balance)
        return balance

    return _factory


@pytest.fixture()
def deal_factory(
    payment_session: AsyncSession,
    faker: Faker,
) -> Callable[..., Coroutine[None, None, Deal]]:
    async def _factory(**kwargs: Any) -> Deal:
        deal = Deal(
            streamer_id=kwargs.get("streamer_id", faker.random_int(min=1, max=1000)),
            deal_id=kwargs.get("deal_id", str(uuid4())),
            amount=kwargs.get("amount", faker.random_int(min=0, max=100000)),
            open_status=kwargs.get("open_status", True),
            deal_type=kwargs.get("deal_type", "N1"),
            expires_at=kwargs.get("expires_at"),
        )
        payment_session.add(deal)
        await payment_session.commit()
        await payment_session.refresh(deal)
        return deal

    return _factory


@pytest.fixture()
def user_withdraw_method_factory(
    payment_session: AsyncSession,
    faker: Faker,
) -> Callable[..., Coroutine[None, None, dict]]:
    """Factory for user withdraw method data (not a model, just test data)."""

    async def _factory(**kwargs: Any) -> dict:
        return {
            "withdraw_id": kwargs.get("withdraw_id", "withdraw_123"),
            "payment_provider": kwargs.get(
                "payment_provider", PaymentProviderEnum.tinkoff
            ),
            "streamer_id": kwargs.get("streamer_id", faker.random_int(min=1, max=1000)),
        }

    return _factory


@pytest.fixture()
def completed_transaction_factory(
    transaction_factory: Callable[..., Coroutine[None, None, Transaction]],
) -> Callable[..., Coroutine[None, None, Transaction]]:
    """Factory for completed transactions."""

    async def _factory(**kwargs: Any) -> Transaction:
        return await transaction_factory(
            **kwargs,
            status=TransactionStatusEnum.completed,
            completed_at=datetime.now(),
        )

    return _factory


@pytest.fixture()
def pending_transaction_factory(
    transaction_factory: Callable[..., Coroutine[None, None, Transaction]],
) -> Callable[..., Coroutine[None, None, Transaction]]:
    """Factory for pending transactions."""

    async def _factory(**kwargs: Any) -> Transaction:
        return await transaction_factory(
            **kwargs,
            status=TransactionStatusEnum.pending,
        )

    return _factory
