import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.stake.repo import StakeRepo, StakeOutcomeRepo
from src.core.database.models import Stake, StakeOutcome
from src.core.database.enums.stake import StakeStatusEnum


@pytest.mark.asyncio
async def test_finish_stake_success(
    api_client: AsyncClient,
    stake_with_outcomes: Stake,
    payment_session: AsyncSession,
):
    """Test successful stake finishing."""
    # Assume first outcome is winner
    winner_outcome = stake_with_outcomes.outcomes[0]
    finish_data = {
        "winner_outcome_id": str(winner_outcome.id),
        "group_percent": 50.0,
        "streamer_percent": 30.0,
        "specific_users": []
    }
    response = await api_client.post(f"/api/stake/{stake_with_outcomes.id}/finish", json=finish_data, headers={'Authorization': 'Bearer user_38'})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == StakeStatusEnum.finished

    # Additional GET request to check the finished stake
    get_response = await api_client.get(f"/api/stake/details/{stake_with_outcomes.id}", headers={'Authorization': 'Bearer user_38'})
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["status"] == StakeStatusEnum.finished.value

    # Check database
    stake_repo = StakeRepo(payment_session)
    stake = await stake_repo.get(id_=stake_with_outcomes.id)
    assert stake is not None
    await payment_session.refresh(stake)
    assert stake.status == StakeStatusEnum.finished

    outcome_repo = StakeOutcomeRepo(payment_session)
    outcomes = await outcome_repo.get_many_by(stake_id=stake_with_outcomes.id)
    for outcome in outcomes:
        await payment_session.refresh(outcome)
    winner = next((o for o in outcomes if o.id == winner_outcome.id), None)
    assert winner is not None
    assert winner.is_winner is True


@pytest.mark.asyncio
async def test_finish_stake_already_finished(
    api_client: AsyncClient,
    finished_stake: Stake,
):
    """Test finishing already finished stake."""
    finish_data = {
        "winner_outcome_id": str(finished_stake.outcomes[0].id) if finished_stake.outcomes else None,
        "group_percent": 50.0,
        "streamer_percent": 50.0,
        "specific_users": []
    }
    response = await api_client.post(f"/api/stake/{finished_stake.id}/finish", json=finish_data, headers={'Authorization': 'Bearer user_38'})
    assert response.status_code == 400
    data = response.json()
    assert "Stake is already finished" in data["detail"]


@pytest.mark.asyncio
async def test_finish_stake_invalid_winner(
    api_client: AsyncClient,
    stake_with_outcomes: Stake,
):
    """Test finishing with invalid winner outcome."""
    from uuid import uuid4
    finish_data = {
        "winner_outcome_id": str(uuid4()),  # Invalid ID
        "group_percent": 50.0,
        "streamer_percent": 50.0,
        "specific_users": []
    }
    response = await api_client.post(f"/api/stake/{stake_with_outcomes.id}/finish", json=finish_data, headers={'Authorization': 'Bearer user_38'})
    # This might fail at winner_outcome_id validation or in service
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_finish_stake_wrong_streamer(
    api_client: AsyncClient,
    stake_with_outcomes: Stake,
):
    """Test finishing by wrong streamer."""
    winner_outcome = stake_with_outcomes.outcomes[0]
    finish_data = {
        "winner_outcome_id": str(winner_outcome.id),
        "group_percent": 100.0,
        "streamer_percent": 0.0,
        "specific_users": []
    }
    response = await api_client.post(f"/api/stake/{stake_with_outcomes.id}/finish", json=finish_data, headers={'Authorization': 'Bearer user_999'})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_finish_stake_with_distribution(
    api_client: AsyncClient,
    stake_with_balances: Stake,
    payment_session: AsyncSession,
):
    """Test finishing stake with balances and distribution."""
    # Assuming balances exist
    winner_outcome = stake_with_balances.outcomes[0]
    finish_data = {
        "winner_outcome_id": str(winner_outcome.id),
        "group_percent": 70.0,
        "streamer_percent": 20.0,
        "specific_users": [{"user_id": 3, "percent": 10.0}]
    }
    response = await api_client.post(f"/api/stake/{stake_with_balances.id}/finish", json=finish_data, headers={'Authorization': 'Bearer user_38'})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == StakeStatusEnum.finished.value

    # Additional GET request to check the finished stake
    get_response = await api_client.get(f"/api/stake/details/{stake_with_balances.id}", headers={'Authorization': 'Bearer user_38'})
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["status"] == StakeStatusEnum.finished.value

    # Check database
    stake_repo = StakeRepo(payment_session)
    stake = await stake_repo.get(id_=stake_with_balances.id)
    assert stake is not None
    await payment_session.refresh(stake)
    assert stake.status == StakeStatusEnum.finished

    outcome_repo = StakeOutcomeRepo(payment_session)
    outcomes = await outcome_repo.get_many_by(stake_id=stake_with_balances.id)
    for outcome in outcomes:
        await payment_session.refresh(outcome)
    winner = next((o for o in outcomes if o.id == winner_outcome.id), None)
    assert winner is not None
    assert winner.is_winner is True