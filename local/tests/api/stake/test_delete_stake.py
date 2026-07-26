import pytest
from httpx import AsyncClient
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.api.stake.repo import StakeRepo
from src.core.database.models import Stake


async def test_delete_stake_success(
    api_client: AsyncClient,
    active_stake: Stake,
    payment_session: AsyncSession,
):
    """Test successful stake deletion (soft delete)."""
    response = await api_client.delete(f"/api/stake/{active_stake.id}", headers={'Authorization': 'Bearer user_38'})
    assert response.status_code == 200
    data = response.json()
    assert data["is_deleted"] is True

    # Additional GET request to check the deleted stake
    get_response = await api_client.get(f"/api/stake/details/{active_stake.id}", headers={'Authorization': 'Bearer user_38'})
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

    stake_repo = StakeRepo(payment_session)
    stake = await stake_repo.get(id_=active_stake.id)
    assert stake is not None
    await payment_session.refresh(stake)
    assert stake.is_deleted is True


async def test_delete_stake_not_found(
    api_client: AsyncClient,
):
    """Test deletion of non-existent stake."""
    response = await api_client.delete(f"/api/stake/{uuid4()}", headers={'Authorization': 'Bearer user_38'})
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_stake_already_deleted(
    api_client: AsyncClient,
    deleted_stake: Stake,
):
    """Test deletion of already deleted stake."""
    response = await api_client.delete(f"/api/stake/{deleted_stake.id}", headers={'Authorization': 'Bearer user_38'})
    assert response.status_code == status.HTTP_404_NOT_FOUND  # Since it's already deleted


async def test_delete_stake_wrong_streamer(
    api_client: AsyncClient,
    active_stake: Stake,
):
    """Test deletion by wrong streamer."""
    response = await api_client.delete(f"/api/stake/{active_stake.id}", headers={'Authorization': 'Bearer user_999'})
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_stake_finished(
    api_client: AsyncClient,
    finished_stake: Stake,
    payment_session: AsyncSession,
):
    response = await api_client.delete(f"/api/stake/{finished_stake.id}", headers={'Authorization': 'Bearer user_38'})
    assert response.status_code == 200
    data = response.json()
    assert data["is_deleted"] is True

    get_response = await api_client.get(f"/api/stake/details/{finished_stake.id}", headers={'Authorization': 'Bearer user_38'})
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

    stake_repo = StakeRepo(payment_session)
    stake = await stake_repo.get(id_=finished_stake.id)
    assert stake is not None
    await payment_session.refresh(stake)
    assert stake.is_deleted is True, stake.is_deleted