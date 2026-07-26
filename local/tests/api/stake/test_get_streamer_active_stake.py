import pytest
from httpx import AsyncClient

from src.core.database.models import Stake


@pytest.mark.asyncio
async def test_get_streamer_active_stake_success(
    api_client: AsyncClient,
    active_stake: Stake,
):
    """Test successful retrieval of active stakes for a streamer."""
    response = await api_client.get(f"/api/stake/testuser")  # Use a string login
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    stake_ids = [s["id"] for s in data]
    assert str(active_stake.id) in stake_ids
    assert all(s["status"] == "active" for s in data)


@pytest.mark.asyncio
async def test_get_streamer_active_stake_no_active(
    api_client: AsyncClient,
    finished_stake: Stake,
):
    """Test when streamer has no active stake — returns empty list."""
    response = await api_client.get("/api/stake/testuser")
    assert response.status_code == 200
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_streamer_active_stake_invalid_login(
    api_client: AsyncClient,
):
    """Test with invalid streamer login."""
    response = await api_client.get("/api/stake/invalid_login")
    assert response.status_code == 404
