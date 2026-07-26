import pytest
from collections.abc import Callable, Coroutine
from typing import Any

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.models import TinkoffWithdrawMethod
from src.core.database.enums.tinkoff_withdraw_method import TinkoffWithdrawTypeEnum
from src.core.database.enums.transactions import PaymentProviderEnum


@pytest.fixture()
def tinkoff_withdraw_method_factory(
    payment_session: AsyncSession,
    faker: Faker,
) -> Callable[..., Coroutine[None, None, TinkoffWithdrawMethod]]:
    async def _factory(**kwargs: Any) -> TinkoffWithdrawMethod:
        method = TinkoffWithdrawMethod(
            streamer_id=kwargs.get("streamer_id", faker.random_int(min=1, max=1000)),
            bank_name=kwargs.get("bank_name", faker.company()),
            card_id=kwargs.get("card_id", str(faker.uuid4())),
            sbp_member_id=kwargs.get("sbp_member_id", str(faker.uuid4())),
            type=kwargs.get("type", faker.random_element(list(TinkoffWithdrawTypeEnum))),
            provider=kwargs.get("provider", PaymentProviderEnum.tinkoff),
            phone=kwargs.get("phone", faker.phone_number()),
            card_pan=kwargs.get("card_pan", faker.credit_card_number()[-4:]),
            request_id=kwargs.get("request_id"),
            is_main=kwargs.get("is_main", True),
            removed_at=kwargs.get("removed_at"),
        )
        payment_session.add(method)
        await payment_session.commit()
        await payment_session.refresh(method)
        return method

    return _factory