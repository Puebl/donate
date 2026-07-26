import pytest
from httpx import AsyncClient

from src.core.database.models import Stake


@pytest.mark.asyncio
async def test_get_all_stakes_success(
    api_client: AsyncClient,
    multiple_stakes_for_streamer: list[Stake],
):
    """Test successful retrieval of all stakes for a streamer."""
    response = await api_client.get("/api/stake", headers={'Authorization': 'Bearer user_38'})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3  # From multiple_stakes_for_streamer


@pytest.mark.asyncio
async def test_get_all_stakes_empty(
    api_client: AsyncClient,
):
    """Test when streamer has no stakes."""
    response = await api_client.get("/api/stake", headers={'Authorization': 'Bearer user_999'})
    assert response.status_code == 200
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_all_stakes_excludes_deleted(
    api_client: AsyncClient,
    active_stake: Stake,
    deleted_stake: Stake,
):
    """Test that deleted stakes are excluded."""
    response = await api_client.get("/api/stake", headers={'Authorization': 'Bearer user_38'})
    assert response.status_code == 200
    data = response.json()
    stake_ids = [stake["id"] for stake in data]
    assert str(active_stake.id) in stake_ids
    assert str(deleted_stake.id) not in stake_ids