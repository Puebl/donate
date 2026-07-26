import pytest
from unittest.mock import AsyncMock, patch
from starlette import status

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.payment_gateways.schemas import AddPaymentMethodSchema, AddPaymentMethodStatus
from src.api.user_service.schemas import CreateWithdrawMethodSchema
from src.core.database.enums.tinkoff_withdraw_method import TinkoffWithdrawTypeEnum
from src.core.database.models import TinkoffWithdrawMethod


@pytest.mark.asyncio
async def test_add_withdrawal_method_card_success(
    api_client: AsyncClient,
    testuser,
    payment_session: AsyncSession,
):
    """Test successful addition of card withdrawal method."""
    create_data = CreateWithdrawMethodSchema(
        bank_name="Test Bank",
        withdraw_type=TinkoffWithdrawTypeEnum.card,
    )

    mock_response = AddPaymentMethodSchema(
        status=AddPaymentMethodStatus.success,
        payment_url=None,
    )

    with patch('src.api.payment_gateways.tinkoff.service.TinkoffService.add_withdraw_method', new_callable=AsyncMock) as mock_add:
        mock_add.return_value = mock_response

        response = await api_client.post(
            "/api/user/add-withdrawal",
            json=create_data.model_dump(),
            headers={'Authorization': 'Bearer user_38'}
        )

        assert response.status_code == status.HTTP_200_OK, response.text
        data = response.json()
        assert data["status"] == AddPaymentMethodStatus.success.value

        # Check that method was added to DB
        from src.api.user_service.repo import WithdrawMethodRepo
        repo = WithdrawMethodRepo(payment_session)
        methods = await repo.get_all_active(testuser.streamer_id)
        assert len(methods) == 1
        assert methods[0].type == TinkoffWithdrawTypeEnum.card
        assert methods[0].bank_name == "Test Bank"


@pytest.mark.asyncio
async def test_add_withdrawal_method_sbp_success(
    api_client: AsyncClient,
    testuser,
    payment_session: AsyncSession,
):
    """Test successful addition of SBP withdrawal method."""
    create_data = CreateWithdrawMethodSchema(
        bank_name="SBP Bank",
        phone="+79991234567",
        sbp_member_id="sbp_123",
        withdraw_type=TinkoffWithdrawTypeEnum.sbp,
    )

    mock_response = AddPaymentMethodSchema(
        status=AddPaymentMethodStatus.success,
        payment_url=None,
    )

    with patch('src.api.payment_gateways.tinkoff.service.TinkoffService.add_withdraw_method', new_callable=AsyncMock) as mock_add:
        mock_add.return_value = mock_response

        response = await api_client.post(
            "/api/user/add-withdrawal",
            json=create_data.model_dump(),
            headers={'Authorization': 'Bearer user_38'}
        )

        assert response.status_code == status.HTTP_200_OK, response.text

        # Check DB
        from src.api.user_service.repo import WithdrawMethodRepo
        repo = WithdrawMethodRepo(payment_session)
        methods = await repo.get_all_active(testuser.streamer_id)
        assert len(methods) == 1
        assert methods[0].type == TinkoffWithdrawTypeEnum.sbp
        assert methods[0].phone == "+79991234567"


@pytest.mark.asyncio
async def test_add_withdrawal_method_unauthorized(
    api_client: AsyncClient,
):
    """Test adding withdrawal method without authorization."""
    create_data = CreateWithdrawMethodSchema(
        bank_name="Test Bank",
        withdraw_type=TinkoffWithdrawTypeEnum.card,
    )

    response = await api_client.post(
        "/api/user/add-withdrawal",
        json=create_data.model_dump(),
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text


@pytest.mark.asyncio
async def test_add_withdrawal_method_invalid_type(
    api_client: AsyncClient,
):
    """Test adding withdrawal method with invalid type."""
    create_data = {
        "bank_name": "Test Bank",
        "withdraw_type": "invalid_type",
    }

    response = await api_client.post(
        "/api/user/add-withdrawal",
        json=create_data,
        headers={'Authorization': 'Bearer user_38'}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text


@pytest.mark.asyncio
async def test_add_withdrawal_method_tinkoff_error(
    api_client: AsyncClient,
):
    """Test adding withdrawal method when Tinkoff service fails."""
    create_data = CreateWithdrawMethodSchema(
        bank_name="Test Bank",
        withdraw_type=TinkoffWithdrawTypeEnum.card,
    )

    with patch('src.api.payment_gateways.tinkoff.service.TinkoffService.add_withdraw_method', new_callable=AsyncMock) as mock_add:
        mock_add.side_effect = Exception("Tinkoff API error")

        response = await api_client.post(
            "/api/user/add-withdrawal",
            json=create_data.model_dump(),
            headers={'Authorization': 'Bearer user_38'}
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR, response.text