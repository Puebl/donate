import pytest
from fastapi import status
from httpx import AsyncClient
from uuid import uuid4

from src.core.database.models import Stake


@pytest.mark.asyncio
async def test_get_stake_donators_success_200(
    stake_with_donators: Stake, api_client: AsyncClient
):
    response = await api_client.get(
        f'/api/stake/donators/{stake_with_donators.id}', headers={'Authorization': f'Bearer test_token'}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2, data  # Two outcomes

    # Find the group for "Yes" outcome
    yes_group = next((g for g in data if g['outcome_title'] == 'Yes'), None)
    assert yes_group is not None
    assert len(yes_group['donators']) == 2

    # Check donators in Yes group
    donator1_yes = next((d for d in yes_group['donators'] if d['user_id'] == 2), None)
    assert donator1_yes is not None
    assert donator1_yes['login'] == 'donator1'
    assert donator1_yes['total_donated'] == 200

    donator2_yes = next((d for d in yes_group['donators'] if d['user_id'] == 3), None)
    assert donator2_yes is not None
    assert donator2_yes['login'] == 'donator2'
    assert donator2_yes['total_donated'] == 75

    # Find the group for "No" outcome
    no_group = next((g for g in data if g['outcome_title'] == 'No'), None)
    assert no_group is not None
    assert len(no_group['donators']) == 1

    # Check donator in No group
    donator1_no = next((d for d in no_group['donators'] if d['user_id'] == 2), None)
    assert donator1_no is not None
    assert donator1_no['login'] == 'donator1'
    assert donator1_no['total_donated'] == 150


@pytest.mark.asyncio
async def test_get_stake_donators_no_donators_200(
    stake_with_outcomes: Stake, api_client: AsyncClient
):
    response = await api_client.get(
        f'/api/stake/donators/{stake_with_outcomes.id}', headers={'Authorization': f'Bearer test_token'}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_stake_donators_stake_not_exists_fail_404(
    stake_with_outcomes: Stake, api_client: AsyncClient
):
    fake_id = uuid4()
    response = await api_client.get(
        f'/api/stake/donators/{fake_id}', headers={'Authorization': f'Bearer test_token'}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Stake not found'}