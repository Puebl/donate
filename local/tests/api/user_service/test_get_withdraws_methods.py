import pytest
from starlette import status

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.user_service.schemas import WithdrawReadSchema
from src.core.database.enums.tinkoff_withdraw_method import TinkoffWithdrawTypeEnum


@pytest.mark.asyncio
async def test_get_withdraws_methods_success(
    api_client: AsyncClient,
    multiple_withdraw_methods,
):
    """Test successful retrieval of withdrawal methods."""
    response = await api_client.get(
        "/api/user/cards",
        headers={'Authorization': 'Bearer user_38'}
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2

    # Check that data is properly serialized
    for method in data:
        assert "id" in method
        assert "bank_name" in method
        assert "is_main" in method
        assert "type" in method


@pytest.mark.asyncio
async def test_get_withdraws_methods_empty(
    api_client: AsyncClient,
):
    """Test retrieval of withdrawal methods when user has none."""
    response = await api_client.get(
        "/api/user/cards",
        headers={'Authorization': 'Bearer user_38'}
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_withdraws_methods_unauthorized(
    api_client: AsyncClient,
):
    """Test retrieval of withdrawal methods without authorization."""
    response = await api_client.get("/api/user/cards")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text


@pytest.mark.asyncio
async def test_get_withdraws_methods_db_validation(
    api_client: AsyncClient,
    multiple_withdraw_methods,
    payment_session: AsyncSession,
):
    """Test that retrieved methods match database state."""
    response = await api_client.get(
        "/api/user/cards",
        headers={'Authorization': 'Bearer user_38'}
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()

    # Check against DB
    from src.api.user_service.repo import WithdrawMethodRepo
    repo = WithdrawMethodRepo(payment_session)
    db_methods = await repo.get_all_active(multiple_withdraw_methods[0].streamer_id)

    assert len(data) == len(db_methods)

    # Check that IDs match
    response_ids = {method["id"] for method in data}
    db_ids = {str(method.id) for method in db_methods}
    assert response_ids == db_ids