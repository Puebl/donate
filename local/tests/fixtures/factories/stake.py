import pytest
from collections.abc import Callable, Coroutine
from typing import Any
from uuid import UUID

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.models import Stake, StakeBalance, StakeOutcome, StakeDistribution, User
from src.core.database.enums.stake import StakeStatusEnum, StakeTypeEnum, VoteMechanicEnum


@pytest.fixture()
def user_factory(
    payment_session: AsyncSession,
    faker: Faker,
) -> Callable[..., Coroutine[None, None, User]]:
    async def _factory(**kwargs: Any) -> User:
        user = User(
            streamer_id=kwargs.get("streamer_id", faker.random_int(min=1, max=1000)),
            login=kwargs.get("login", faker.user_name()),
        )
        payment_session.add(user)
        await payment_session.commit()
        await payment_session.refresh(user)
        return user

    return _factory


@pytest.fixture()
def stake_factory(
    payment_session: AsyncSession,
    faker: Faker,
) -> Callable[..., Coroutine[None, None, Stake]]:
    async def _factory(**kwargs: Any) -> Stake:
        stake = Stake(
            streamer_id=kwargs.get("streamer_id", faker.random_int(min=1, max=1000)),
            title=kwargs.get("title", faker.sentence()),
            min_sum=kwargs.get("min_sum", faker.random_int(min=0, max=1000)),
            multiple_choice=kwargs.get("multiple_choice", faker.boolean()),
            description=kwargs.get("description", faker.text()),
            status=kwargs.get("status", faker.random_element(list(StakeStatusEnum))),
            stake_type=kwargs.get("stake_type", faker.random_element(list(StakeTypeEnum))),
            vote_mechanic=kwargs.get("vote_mechanic", faker.random_element(list(VoteMechanicEnum))),
            paused_time=kwargs.get("paused_time"),
            finished_time=kwargs.get("finished_time"),
            expires_at=kwargs.get("expires_at"),
            file_id=kwargs.get("file_id"),
            is_deleted=kwargs.get("is_deleted", False),
        )
        payment_session.add(stake)
        await payment_session.commit()
        await payment_session.refresh(stake)
        return stake

    return _factory


@pytest.fixture()
def stake_outcome_factory(
    payment_session: AsyncSession,
    faker: Faker,
) -> Callable[..., Coroutine[None, None, StakeOutcome]]:
    async def _factory(**kwargs: Any) -> StakeOutcome:
        outcome = StakeOutcome(
            stake_id=kwargs.get("stake_id"),
            title=kwargs.get("title", faker.sentence()),
            coefficient=kwargs.get("coefficient", faker.pyfloat(min_value=1.0, max_value=2.0)),
            is_winner=kwargs.get("is_winner", False),
            target_amount=kwargs.get("target_amount", faker.random_int(min=100, max=10000)),
            current_amount=kwargs.get("current_amount", faker.random_int(min=0, max=1000)),
            votes_count=kwargs.get("votes_count", faker.random_int(min=0, max=100)),
        )
        payment_session.add(outcome)
        await payment_session.commit()
        await payment_session.refresh(outcome)
        return outcome

    return _factory


@pytest.fixture()
def stake_balance_factory(
    payment_session: AsyncSession,
    faker: Faker,
) -> Callable[..., Coroutine[None, None, StakeBalance]]:
    async def _factory(**kwargs: Any) -> StakeBalance:
        balance = StakeBalance(
            stake_id=kwargs.get("stake_id"),
            outcome_id=kwargs.get("outcome_id"),
            amount=kwargs.get("amount", faker.random_int(min=1, max=1000)),
            total_amount=kwargs.get("total_amount", faker.random_int(min=1, max=1000)),
            created_by_id=kwargs.get("created_by_id", faker.random_int(min=1, max=1000)),
        )
        payment_session.add(balance)
        await payment_session.commit()
        await payment_session.refresh(balance)
        return balance

    return _factory


@pytest.fixture()
def stake_distribution_factory(
    payment_session: AsyncSession,
    faker: Faker,
) -> Callable[..., Coroutine[None, None, StakeDistribution]]:
    async def _factory(**kwargs: Any) -> StakeDistribution:
        distribution = StakeDistribution(
            stake_id=kwargs.get("stake_id"),
            user_id=kwargs.get("user_id", faker.random_int(min=1, max=1000) if faker.boolean() else None),
            amount=kwargs.get("amount", faker.random_int(min=1, max=1000)),
            distribution_type=kwargs.get("distribution_type", faker.random_element(['group', 'specific', 'streamer'])),
        )
        payment_session.add(distribution)
        await payment_session.commit()
        await payment_session.refresh(distribution)
        return distribution

    return _factory