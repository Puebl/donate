import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.stake.repo import StakeRepo
from src.core.database.models import Stake
from src.core.database.enums.stake import StakeStatusEnum


@pytest.mark.asyncio
async def test_update_stake_success(
    api_client: AsyncClient,
    active_stake: Stake,
    payment_session: AsyncSession,
):
    """Test successful stake update."""
    update_data = {
        "title": "Updated Title",
        "description": "Updated description"
    }
    response = await api_client.patch(f"/api/stake/{active_stake.id}", json=update_data, headers={'Authorization': 'Bearer user_38'})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated description"
    assert "bg_img_url" in data
    assert data["bg_img_url"] is None
    assert "outcomes" not in data

    # Additional GET request to check the updated stake
    get_response = await api_client.get(f"/api/stake/details/{active_stake.id}", headers={'Authorization': 'Bearer user_38'})
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["title"] == "Updated Title"
    assert get_data["description"] == "Updated description"

    # Check database
    stake_repo = StakeRepo(payment_session)
    stake = await stake_repo.get(id_=active_stake.id)
    assert stake is not None
    await payment_session.refresh(stake)
    assert stake.title == "Updated Title"
    assert stake.description == "Updated description"


@pytest.mark.asyncio
async def test_update_stake_not_found(
    api_client: AsyncClient,
):
    """Test update of non-existent stake."""
    from uuid import uuid4
    update_data = {"title": "New Title"}
    response = await api_client.patch(f"/api/stake/{uuid4()}", json=update_data, headers={'Authorization': 'Bearer user_38'})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_stake_finished_forbidden(
    api_client: AsyncClient,
    finished_stake: Stake,
):
    """Test update of finished stake is forbidden."""
    update_data = {"title": "Should Fail"}
    response = await api_client.patch(f"/api/stake/{finished_stake.id}", json=update_data, headers={'Authorization': 'Bearer user_38'})
    assert response.status_code == 400
    data = response.json()
    assert "Forbidden to update finished stake" in data["detail"]


@pytest.mark.asyncio
async def test_update_stake_to_finished_forbidden(
    api_client: AsyncClient,
    active_stake: Stake,
):
    """Test setting status to finished via update is forbidden."""
    update_data = {"status": StakeStatusEnum.finished}
    response = await api_client.patch(f"/api/stake/{active_stake.id}", json=update_data, headers={'Authorization': 'Bearer user_38'})
    assert response.status_code == 400
    data = response.json()
    assert "Use finish endpoint to finish the stake" in data["detail"]


@pytest.mark.asyncio
async def test_update_stake_wrong_streamer(
    api_client: AsyncClient,
    active_stake: Stake,
):
    """Test update by wrong streamer."""
    update_data = {"title": "Wrong Update"}
    response = await api_client.patch(f"/api/stake/{active_stake.id}", json=update_data, headers={'Authorization': 'Bearer user_999'})
    assert response.status_code == 404  # Not found for this streamer