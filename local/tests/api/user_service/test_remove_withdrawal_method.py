import pytest
from unittest.mock import AsyncMock, patch
from starlette import status

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.user_service.schemas import WithdrawIDSchema
from src.core.database.enums.tinkoff_withdraw_method import TinkoffWithdrawTypeEnum


@pytest.mark.asyncio
async def test_remove_withdrawal_method_success(
    api_client: AsyncClient,
    withdraw_method_card,
    payment_session: AsyncSession,
):
    """Test successful removal of withdrawal method."""
    remove_data = WithdrawIDSchema(withdraw_id=withdraw_method_card.id)

    with patch('src.api.payment_gateways.tinkoff.service.TinkoffService.remove_card', new_callable=AsyncMock) as mock_remove:
        mock_remove.return_value = None

        response = await api_client.delete(
            "/api/user/remove-withdrawal",
            params=remove_data.model_dump(),
            headers={'Authorization': 'Bearer user_38'}
        )

        assert response.status_code == status.HTTP_200_OK, response.text

        # Check that method was removed from DB
        from src.api.user_service.repo import WithdrawMethodRepo
        repo = WithdrawMethodRepo(payment_session)
        methods = await repo.get_all_active(withdraw_method_card.streamer_id)
        assert len(methods) == 0

        mock_remove.assert_called_once()


@pytest.mark.asyncio
async def test_remove_withdrawal_method_not_found(
    api_client: AsyncClient,
):
    """Test removing non-existent withdrawal method."""
    from uuid import uuid4
    remove_data = WithdrawIDSchema(withdraw_id=uuid4())

    response = await api_client.delete(
        "/api/user/remove-withdrawal",
        params=remove_data.model_dump(),
        headers={'Authorization': 'Bearer user_38'}
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR, response.text  # ValueError raised


@pytest.mark.asyncio
async def test_remove_withdrawal_method_unauthorized(
    api_client: AsyncClient,
):
    """Test removing withdrawal method without authorization."""
    from uuid import uuid4
    remove_data = WithdrawIDSchema(withdraw_id=uuid4())

    response = await api_client.delete(
        "/api/user/remove-withdrawal",
        params=remove_data.model_dump(),
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text


@pytest.mark.asyncio
async def test_remove_withdrawal_method_invalid_id(
    api_client: AsyncClient,
):
    """Test removing withdrawal method with invalid ID."""
    remove_data = {"withdraw_id": "invalid-uuid"}

    response = await api_client.delete(
        "/api/user/remove-withdrawal",
        params=remove_data,
        headers={'Authorization': 'Bearer user_38'}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text


@pytest.mark.asyncio
async def test_remove_withdrawal_method_tinkoff_error(
    api_client: AsyncClient,
    withdraw_method_card,
):
    """Test removing withdrawal method when Tinkoff service fails."""
    remove_data = WithdrawIDSchema(withdraw_id=withdraw_method_card.id)

    with patch('src.api.payment_gateways.tinkoff.service.TinkoffService.remove_card', new_callable=AsyncMock) as mock_remove:
        mock_remove.side_effect = Exception("Tinkoff API error")

        response = await api_client.delete(
            "/api/user/remove-withdrawal",
            params=remove_data.model_dump(),
            headers={'Authorization': 'Bearer user_38'}
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR, response.text