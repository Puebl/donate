from uuid import UUID

import pytest
from collections.abc import Callable, Coroutine
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.database.enums.stake import StakeStatusEnum, StakeTypeEnum, VoteMechanicEnum
from src.core.database.models import Stake, StakeBalance, StakeOutcome, User


@pytest.fixture
async def testuser(user_factory):
    return await user_factory(streamer_id=38, login='testuser')


async def _get_stake_with_relations(session: AsyncSession, stake_id: UUID) -> Stake:
    stmt = (
        select(Stake)
        .options(
            selectinload(Stake.outcomes),
            selectinload(Stake.stake_balances),
            selectinload(Stake.distributions),
        )
        .where(Stake.id == stake_id)
    )
    return await session.scalar(stmt)


@pytest.fixture
async def active_stake(
    payment_session: AsyncSession,
    stake_factory: Callable[..., Coroutine[None, None, Stake]],
    stake_outcome_factory: Callable[..., Coroutine[None, None, StakeOutcome]],
    testuser: User,
) -> Stake:
    stake = await stake_factory(
        streamer_id=38,
        title="Active Test Stake",
        status=StakeStatusEnum.active,
        stake_type=StakeTypeEnum.vote,
        vote_mechanic=VoteMechanicEnum.weighted,
        min_sum=10,
        description="A test stake for voting",
        expires_at=datetime(2025, 12, 31),
    )
    await stake_outcome_factory(
        stake_id=stake.id, title="Yes", target_amount=1000, current_amount=500
    )
    await stake_outcome_factory(
        stake_id=stake.id, title="No", target_amount=1000, current_amount=300
    )
    return await _get_stake_with_relations(payment_session, stake.id)


@pytest.fixture
async def finished_stake(
    payment_session: AsyncSession,
    stake_factory: Callable[..., Coroutine[None, None, Stake]],
    stake_outcome_factory: Callable[..., Coroutine[None, None, StakeOutcome]],
    testuser: User,
) -> Stake:
    stake = await stake_factory(
        streamer_id=38,
        title="Finished Test Stake",
        status=StakeStatusEnum.finished,
        stake_type=StakeTypeEnum.vote,
        vote_mechanic=VoteMechanicEnum.weighted,
        min_sum=10,
        description="A finished test stake",
        finished_time=datetime(2025, 12, 5),
    )
    await stake_outcome_factory(
        stake_id=stake.id, title="Yes", target_amount=1000, current_amount=500
    )
    await stake_outcome_factory(
        stake_id=stake.id, title="No", target_amount=1000, current_amount=300
    )
    return await _get_stake_with_relations(payment_session, stake.id)


@pytest.fixture
async def paused_stake(
    payment_session: AsyncSession,
    stake_factory: Callable[..., Coroutine[None, None, Stake]],
    stake_outcome_factory: Callable[..., Coroutine[None, None, StakeOutcome]],
    testuser: User,
) -> Stake:
    stake = await stake_factory(
        streamer_id=38,
        title="Paused Test Stake",
        status=StakeStatusEnum.paused,
        stake_type=StakeTypeEnum.vote,
        vote_mechanic=VoteMechanicEnum.weighted,
        min_sum=10,
        description="A paused test stake",
        paused_time=datetime(2025, 12, 4),
    )
    await stake_outcome_factory(
        stake_id=stake.id, title="Yes", target_amount=1000, current_amount=500
    )
    await stake_outcome_factory(
        stake_id=stake.id, title="No", target_amount=1000, current_amount=300
    )
    return await _get_stake_with_relations(payment_session, stake.id)


@pytest.fixture
async def deleted_stake(
    payment_session: AsyncSession,
    stake_factory: Callable[..., Coroutine[None, None, Stake]],
    stake_outcome_factory: Callable[..., Coroutine[None, None, StakeOutcome]],
    testuser: User,
) -> Stake:
    stake = await stake_factory(
        streamer_id=38,
        title="Deleted Test Stake",
        status=StakeStatusEnum.active,
        stake_type=StakeTypeEnum.vote,
        vote_mechanic=VoteMechanicEnum.weighted,
        min_sum=10,
        description="A deleted test stake",
        is_deleted=True,
    )
    await stake_outcome_factory(
        stake_id=stake.id, title="Yes", target_amount=1000, current_amount=500
    )
    await stake_outcome_factory(
        stake_id=stake.id, title="No", target_amount=1000, current_amount=300
    )
    return await _get_stake_with_relations(payment_session, stake.id)


@pytest.fixture
async def stake_with_outcomes(
    payment_session: AsyncSession,
    stake_factory: Callable[..., Coroutine[None, None, Stake]],
    stake_outcome_factory: Callable[..., Coroutine[None, None, StakeOutcome]],
    testuser: User,
) -> Stake:
    stake = await stake_factory(
        streamer_id=38,
        title="Stake with Outcomes",
        status=StakeStatusEnum.active,
        stake_type=StakeTypeEnum.vote,
        vote_mechanic=VoteMechanicEnum.weighted,
        min_sum=10,
        description="Stake with multiple outcomes",
    )
    await stake_outcome_factory(
        stake_id=stake.id, title="Yes", target_amount=1000, current_amount=500
    )
    await stake_outcome_factory(
        stake_id=stake.id, title="No", target_amount=1000, current_amount=300
    )
    return await _get_stake_with_relations(payment_session, stake.id)


@pytest.fixture
async def stake_with_balances(
    payment_session: AsyncSession,
    stake_with_outcomes: Stake,
    stake_balance_factory: Callable[..., Coroutine[None, None, StakeBalance]],
) -> Stake:
    if stake_with_outcomes.outcomes:
        await stake_balance_factory(
            stake_id=stake_with_outcomes.id,
            outcome_id=stake_with_outcomes.outcomes[0].id,
            amount=100,
            total_amount=200,
            created_by_id=2,
        )
    return await _get_stake_with_relations(payment_session, stake_with_outcomes.id)


@pytest.fixture
async def multiple_stakes_for_streamer(
    payment_session: AsyncSession,
    stake_factory: Callable[..., Coroutine[None, None, Stake]],
    stake_outcome_factory: Callable[..., Coroutine[None, None, StakeOutcome]],
    testuser: User,
) -> list[Stake]:
    stakes = []
    for i in range(3):
        stake = await stake_factory(
            streamer_id=38,
            title=f"Stake {i+1}",
            status=StakeStatusEnum.active if i < 2 else StakeStatusEnum.finished,
            stake_type=StakeTypeEnum.vote,
            vote_mechanic=VoteMechanicEnum.weighted,
            min_sum=10,
            description=f"Test stake {i+1}",
        )
        await stake_outcome_factory(
            stake_id=stake.id, title="Yes", target_amount=1000, current_amount=500
        )
        await stake_outcome_factory(
            stake_id=stake.id, title="No", target_amount=1000, current_amount=300
        )
        loaded_stake = await _get_stake_with_relations(payment_session, stake.id)
        stakes.append(loaded_stake)
    return stakes


@pytest.fixture
async def stake_with_donators(
    payment_session: AsyncSession,
    stake_with_outcomes: Stake,
    stake_balance_factory: Callable[..., Coroutine[None, None, StakeBalance]],
    user_factory: Callable[..., Coroutine[None, None, User]],
) -> Stake:
    await user_factory(streamer_id=2, login="donator1")
    await user_factory(streamer_id=3, login="donator2")

    outcomes = stake_with_outcomes.outcomes
    if len(outcomes) >= 2:
        await stake_balance_factory(
            stake_id=stake_with_outcomes.id,
            outcome_id=outcomes[0].id,
            amount=100,
            total_amount=200,
            created_by_id=2,
        )
        await stake_balance_factory(
            stake_id=stake_with_outcomes.id,
            outcome_id=outcomes[1].id,
            amount=50,
            total_amount=150,
            created_by_id=2,
        )
        await stake_balance_factory(
            stake_id=stake_with_outcomes.id,
            outcome_id=outcomes[0].id,
            amount=75,
            total_amount=75,
            created_by_id=3,
        )

    await payment_session.commit()

    return await _get_stake_with_relations(payment_session, stake_with_outcomes.id)