import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.stake.repo import StakeRepo, StakeOutcomeRepo
from src.core.database.enums.stake import StakeStatusEnum, StakeTypeEnum, VoteMechanicEnum


@pytest.mark.asyncio
async def test_create_stake_success(
    api_client: AsyncClient,
    payment_session: AsyncSession,
):
    """Test successful stake creation."""
    create_data = {
        "status": StakeStatusEnum.active,
        "title": "New Test Stake",
        "min_sum": 10,
        "vote_mechanic": VoteMechanicEnum.weighted,
        "stake_type": StakeTypeEnum.vote,
        "description": "Test stake creation",
        "outcomes": [
            {"title": "Yes", "current_amount": 0, "votes_count": 0, "target_amount": 1000},
            {"title": "No", "current_amount": 0, "votes_count": 0, "target_amount": 1000},
        ]
    }
    response = await api_client.post("/api/stake", json=create_data, headers={'Authorization': 'Bearer user_38'})
    assert response.status_code == 200
    data = response.json()
    assert "outcomes" not in data
    data = response.json()
    assert data["title"] == "New Test Stake"
    assert data["bg_img_url"] is None
    assert "outcomes" not in data

    stake_id = data["id"]
    get_response = await api_client.get(f"/api/stake/details/{stake_id}", headers={'Authorization': 'Bearer user_38'})
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["title"] == "New Test Stake"
    assert get_data["description"] == "Test stake creation"
    assert len(get_data["outcomes"]) == 2

    stake_repo = StakeRepo(payment_session)
    stake = await stake_repo.get(id_=stake_id)
    assert stake is not None
    await payment_session.refresh(stake)
    assert stake.title == "New Test Stake"
    assert stake.description == "Test stake creation"

    outcome_repo = StakeOutcomeRepo(payment_session)
    outcomes = await outcome_repo.get_many_by(stake_id=stake_id)
    assert len(outcomes) == 2
    await payment_session.refresh(outcomes[0])
    await payment_session.refresh(outcomes[1])
    assert outcomes[0].title in ["Yes", "No"]
    assert outcomes[1].title in ["Yes", "No"]


@pytest.mark.asyncio
async def test_create_stake_min_outcomes(
    api_client: AsyncClient,
):
    """Test stake creation with minimum required outcomes."""
    create_data = {
        "status": StakeStatusEnum.active,
        "title": "Minimal Stake",
        "min_sum": 0,
        "vote_mechanic": VoteMechanicEnum.fixed,
        "stake_type": StakeTypeEnum.quiz,
        "description": "Minimal test",
        "outcomes": [
            {"title": "Option 1", "current_amount": 0, "votes_count": 0}
        ]
    }
    response = await api_client.post("/api/stake", json=create_data, headers={'Authorization': 'Bearer user_38'})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_stake_invalid_data(
    api_client: AsyncClient,
):
    """Test stake creation with invalid data."""
    invalid_data = {
        "status": StakeStatusEnum.active,
        "title": "",  # Invalid title
        "min_sum": 10,
        "vote_mechanic": VoteMechanicEnum.weighted,
        "stake_type": StakeTypeEnum.vote,
        "description": "Test",
        "outcomes": []  # No outcomes
    }
    response = await api_client.post("/api/stake", json=invalid_data, headers={'Authorization': 'Bearer user_38'})
    assert response.status_code == 422  # Validation error

