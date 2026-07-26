import pytest
from collections.abc import Callable, Coroutine

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.models import TinkoffWithdrawMethod, User
from src.core.database.enums.tinkoff_withdraw_method import TinkoffWithdrawTypeEnum
from src.core.database.enums.transactions import PaymentProviderEnum


@pytest.fixture
async def withdraw_method_card(
    payment_session: AsyncSession,
    tinkoff_withdraw_method_factory: Callable[..., Coroutine[None, None, TinkoffWithdrawMethod]],
    testuser: User,
) -> TinkoffWithdrawMethod:
    """A card withdraw method for testing."""
    return await tinkoff_withdraw_method_factory(
        streamer_id=testuser.streamer_id,
        type=TinkoffWithdrawTypeEnum.card,
        provider=PaymentProviderEnum.tinkoff,
        bank_name="Tinkoff Bank",
        card_id="card_123",
        card_pan="1234",
        is_main=True,
    )


@pytest.fixture
async def withdraw_method_sbp(
    payment_session: AsyncSession,
    tinkoff_withdraw_method_factory: Callable[..., Coroutine[None, None, TinkoffWithdrawMethod]],
    testuser: User,
) -> TinkoffWithdrawMethod:
    """An SBP withdraw method for testing."""
    return await tinkoff_withdraw_method_factory(
        streamer_id=testuser.streamer_id,
        type=TinkoffWithdrawTypeEnum.sbp,
        provider=PaymentProviderEnum.tinkoff,
        bank_name="SBP Bank",
        sbp_member_id="sbp_123",
        phone="+79991234567",
        is_main=False,
    )


@pytest.fixture
async def multiple_withdraw_methods(
    payment_session: AsyncSession,
    tinkoff_withdraw_method_factory: Callable[..., Coroutine[None, None, TinkoffWithdrawMethod]],
    testuser: User,
) -> list[TinkoffWithdrawMethod]:
    """Multiple withdraw methods for a user."""
    methods = []
    # Main card method
    method1 = await tinkoff_withdraw_method_factory(
        streamer_id=testuser.streamer_id,
        type=TinkoffWithdrawTypeEnum.card,
        provider=PaymentProviderEnum.tinkoff,
        bank_name="Tinkoff Bank",
        card_id="card_123",
        card_pan="1234",
        is_main=True,
    )
    methods.append(method1)

    # Secondary SBP method
    method2 = await tinkoff_withdraw_method_factory(
        streamer_id=testuser.streamer_id,
        type=TinkoffWithdrawTypeEnum.sbp,
        provider=PaymentProviderEnum.tinkoff,
        bank_name="SBP Bank",
        sbp_member_id="sbp_456",
        phone="+79997654321",
        is_main=False,
    )
    methods.append(method2)

    return methods