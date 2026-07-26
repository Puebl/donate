from collections.abc import Callable, Coroutine
from datetime import datetime
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.models import Transaction, Payment, Balance, Deal, User
from src.core.database.enums.transactions import TransactionStatusEnum, PaymentProviderEnum
from src.core.database.enums.balances import OperationTypeEnum


@pytest.fixture
async def completed_deposit_transaction(
    payment_session: AsyncSession,
    transaction_factory: Callable[..., Coroutine[None, None, Transaction]],
    testuser: User,
) -> Transaction:
    """A completed deposit transaction for testing."""
    return await transaction_factory(
        streamer_id=testuser.streamer_id,
        amount=10000,
        status=TransactionStatusEnum.completed,
        operation_type=OperationTypeEnum.t_deposit_sbp,
        payment_provider=PaymentProviderEnum.tinkoff,
        completed_at=datetime.now(),
    )


@pytest.fixture
async def pending_deposit_transaction(
    payment_session: AsyncSession,
    transaction_factory: Callable[..., Coroutine[None, None, Transaction]],
    testuser: User,
) -> Transaction:
    """A pending deposit transaction for testing."""
    return await transaction_factory(
        streamer_id=testuser.streamer_id,
        amount=5000,
        status=TransactionStatusEnum.pending,
        operation_type=OperationTypeEnum.t_deposit_sbp,
        payment_provider=PaymentProviderEnum.tinkoff,
    )


@pytest.fixture
async def completed_withdraw_transaction(
    payment_session: AsyncSession,
    withdraw_transaction_factory: Callable[..., Coroutine[None, None, Transaction]],
    testuser: User,
) -> Transaction:
    """A completed withdraw transaction for testing."""
    return await withdraw_transaction_factory(
        streamer_id=testuser.streamer_id,
        amount=3000,
        status=TransactionStatusEnum.completed,
        payment_provider=PaymentProviderEnum.tinkoff,
        completed_at=datetime.now(),
    )


@pytest.fixture
async def pending_withdraw_transaction(
    payment_session: AsyncSession,
    withdraw_transaction_factory: Callable[..., Coroutine[None, None, Transaction]],
    testuser: User,
) -> Transaction:
    """A pending withdraw transaction for testing."""
    return await withdraw_transaction_factory(
        streamer_id=testuser.streamer_id,
        amount=2000,
        status=TransactionStatusEnum.pending,
        payment_provider=PaymentProviderEnum.tinkoff,
    )


@pytest.fixture
async def transaction_with_balance(
    payment_session: AsyncSession,
    completed_deposit_transaction: Transaction,
    balance_factory: Callable[..., Coroutine[None, None, Balance]],
    testuser: User,
) -> Transaction:
    """A transaction with associated balance entries."""
    await balance_factory(
        streamer_id=testuser.streamer_id,
        operation_type=OperationTypeEnum.credit,
        balance_diff=10000,
        balance_total=10000,
        transaction_id=completed_deposit_transaction.id,
    )
    await payment_session.refresh(completed_deposit_transaction)
    return completed_deposit_transaction


@pytest.fixture
async def transaction_with_multiple_balances(
    payment_session: AsyncSession,
    completed_deposit_transaction: Transaction,
    balance_factory: Callable[..., Coroutine[None, None, Balance]],
    testuser: User,
) -> Transaction:
    """A transaction with multiple balance entries."""
    await balance_factory(
        streamer_id=testuser.streamer_id,
        operation_type=OperationTypeEnum.credit,
        balance_diff=10000,
        balance_total=10000,
        transaction_id=completed_deposit_transaction.id,
    )
    await balance_factory(
        streamer_id=testuser.streamer_id,
        operation_type=OperationTypeEnum.t_deposit_card_fee,
        balance_diff=-25,
        balance_total=9975,
        transaction_id=completed_deposit_transaction.id,
    )
    await payment_session.refresh(completed_deposit_transaction)
    return completed_deposit_transaction


@pytest.fixture
async def payment_with_transaction(
    payment_session: AsyncSession,
    completed_deposit_transaction: Transaction,
    payment_factory: Callable[..., Coroutine[None, None, Payment]],
    testuser: User,
) -> Payment:
    """A payment associated with a transaction."""
    payment = await payment_factory(
        deal_id="test_deal_123",
        transaction_id=completed_deposit_transaction.id,
        streamer_id=testuser.streamer_id,
        amount=10000,
    )
    return payment


@pytest.fixture
async def deal_with_payments(
    payment_session: AsyncSession,
    deal_factory: Callable[..., Coroutine[None, None, Deal]],
    payment_factory: Callable[..., Coroutine[None, None, Payment]],
    completed_deposit_transaction: Transaction,
    testuser: User,
) -> Deal:
    """A deal with multiple payments."""
    deal = await deal_factory(
        streamer_id=testuser.streamer_id,
        deal_id="test_deal_multiple",
        amount=0,
        open_status=True,
    )
    
    for i in range(3):
        await payment_factory(
            deal_id=deal.deal_id,
            transaction_id=completed_deposit_transaction.id,
            streamer_id=testuser.streamer_id,
            amount=1000 * (i + 1),
        )
    
    await payment_session.refresh(deal)
    return deal


@pytest.fixture
async def closed_deal(
    payment_session: AsyncSession,
    deal_factory: Callable[..., Coroutine[None, None, Deal]],
    testuser: User,
) -> Deal:
    """A closed deal (open_status=False)."""
    deal = await deal_factory(
        streamer_id=testuser.streamer_id,
        deal_id="test_deal_closed",
        amount=5000,
        open_status=False,
    )
    return deal


@pytest.fixture
async def multiple_transactions_for_user(
    payment_session: AsyncSession,
    transaction_factory: Callable[..., Coroutine[None, None, Transaction]],
    testuser: User,
) -> list[Transaction]:
    """Multiple transactions for a single user."""
    transactions = []
    
    # Create deposit transactions
    for i in range(3):
        tx = await transaction_factory(
            streamer_id=testuser.streamer_id,
            amount=1000 * (i + 1),
            status=TransactionStatusEnum.completed,
            operation_type=OperationTypeEnum.t_deposit_sbp,
            payment_provider=PaymentProviderEnum.tinkoff,
            completed_at=datetime.now(),
        )
        transactions.append(tx)
    
    # Create withdraw transaction
    tx = await transaction_factory(
        streamer_id=testuser.streamer_id,
        amount=500,
        status=TransactionStatusEnum.pending,
        operation_type=OperationTypeEnum.withdraw,
        payment_provider=PaymentProviderEnum.tinkoff,
    )
    transactions.append(tx)
    
    return transactions


@pytest.fixture
async def failed_transaction(
    payment_session: AsyncSession,
    transaction_factory: Callable[..., Coroutine[None, None, Transaction]],
    testuser: User,
) -> Transaction:
    """A failed transaction for testing error handling."""
    return await transaction_factory(
        streamer_id=testuser.streamer_id,
        amount=1000,
        status=TransactionStatusEnum.failed,
        operation_type=OperationTypeEnum.t_deposit_sbp,
        payment_provider=PaymentProviderEnum.tinkoff,
    )


@pytest.fixture
async def transaction_with_stake(
    payment_session: AsyncSession,
    transaction_factory: Callable[..., Coroutine[None, None, Transaction]],
    stake_factory: Callable[..., Coroutine[None, None, Any]],  # Using Any to avoid circular import
    stake_outcome_factory: Callable[..., Coroutine[None, None, Any]],
    testuser: User,
) -> Transaction:
    """A transaction associated with a stake and outcome."""
    stake = await stake_factory(
        streamer_id=testuser.streamer_id,
        title="Test Stake for Transaction",
    )
    outcome = await stake_outcome_factory(
        stake_id=stake.id,
        title="Yes",
    )
    
    return await transaction_factory(
        streamer_id=testuser.streamer_id,
        amount=500,
        status=TransactionStatusEnum.completed,
        operation_type=OperationTypeEnum.t_deposit_sbp,
        payment_provider=PaymentProviderEnum.tinkoff,
        outcome_id=outcome.id,
        completed_at=datetime.now(),
    )
