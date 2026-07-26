import pytest
from fastapi import status
from httpx import AsyncClient
from uuid import uuid4

from src.core.database.models import Stake


@pytest.mark.asyncio
async def test_get_stake_by_id_success_200(
    active_stake: Stake, api_client: AsyncClient
):
    response = await api_client.get(
        f'/api/stake/details/{active_stake.id}', headers={'Authorization': f'Bearer test_token'}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['id'] == str(active_stake.id)
    assert data['status'] == active_stake.status.value
    assert data['title'] == active_stake.title
    assert data['description'] == active_stake.description
    assert data['min_sum'] == active_stake.min_sum
    assert data['vote_mechanic'] == active_stake.vote_mechanic.value
    assert data['stake_type'] == active_stake.stake_type.value
    assert data['expires_at'] == active_stake.expires_at.isoformat() if active_stake.expires_at else None
    assert data['bg_img_url'] is None
    assert len(data['outcomes']) > 0


@pytest.mark.asyncio
async def test_get_stake_by_id_not_exists_fail_404(
    active_stake: Stake, api_client: AsyncClient
):
    fake_id = uuid4()
    response = await api_client.get(
        f'/api/stake/details/{fake_id}', headers={'Authorization': f'Bearer test_token'}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Stake not found'}