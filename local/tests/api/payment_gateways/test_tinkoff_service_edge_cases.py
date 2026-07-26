import pytest
from sqlalchemy import select
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from src.api.payment_gateways.tinkoff.service import TinkoffService
from src.api.payment_gateways.tinkoff.client.schemas import TinkoffAddSellerResponse, BaseTinkoffResponse
from src.api.payment_gateways.tinkoff.exceptions import (
    DealCreationError,
    QRGenerationError,
    PaymentInitializationError,
    PayoutError
)
from src.api.payment_gateways.schemas import PayInResult, PayoutResult
from src.api.payment_gateways.constants import TinkoffPaymentMethod
from src.core.database.enums.transactions import TransactionStatusEnum, PaymentProviderEnum
from src.api.user_service.schemas import WithdrawMethodSchema, InitializeUserSchema


@pytest.fixture
def mock_tinkoff_service(mock_tinkoff_client, payment_session):
    """Create TinkoffService with mocked dependencies."""
    from src.api.payment_gateways.tinkoff.uow import TinkoffUnitOfWork

    mock_uow = MagicMock(spec=TinkoffUnitOfWork)
    mock_uow.deals = AsyncMock()
    mock_uow.payments = AsyncMock()

    async def mock_context():
        yield mock_uow

    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    service = TinkoffService(uow=mock_uow)
    return service


@pytest.mark.asyncio
async def test_make_pay_out_insufficient_funds(mock_tinkoff_service):
    """Test payout when deal has insufficient funds."""
    mock_deal = MagicMock()
    mock_deal.deal_id = "deal_123"
    mock_deal.amount = 50

    mock_tinkoff_service.uow.deals.get_active = AsyncMock(return_value=mock_deal)

    with pytest.raises(PayoutError, match="Insufficient balance"):
        await mock_tinkoff_service.make_pay_out(
            streamer_id=38,
            amount=200,
            external_transaction_id=str(uuid4()),
            method_data=WithdrawMethodSchema(
                streamer_id=38,
                payment_provider=PaymentProviderEnum.tinkoff,
                card_id="card_123"
            )
        )


@pytest.mark.asyncio
async def test_make_pay_out_no_active_deal(mock_tinkoff_service):
    """Test payout when there is no active deal."""
    mock_tinkoff_service.uow.deals.get_active = AsyncMock(return_value=None)

    with pytest.raises(PayoutError, match="Insufficient balance"):
        await mock_tinkoff_service.make_pay_out(
            streamer_id=38,
            amount=100,
            external_transaction_id=str(uuid4()),
            method_data=WithdrawMethodSchema(
                streamer_id=38,
                payment_provider=PaymentProviderEnum.tinkoff,
                card_id="card_123"
            )
        )


@pytest.mark.asyncio
async def test_add_withdraw_method_non_card_returns_success(mock_tinkoff_service):
    """Test adding non-card withdraw method returns immediate success."""
    result = await mock_tinkoff_service.add_withdraw_method(
        streamer_id=38,
        type_="sbp"
    )

    assert result is not None
    assert result.status == "success"
    assert result.payment_url is None


@pytest.mark.asyncio
async def test_initialize_user_success():
    """Test successful user initialization."""

    with patch('src.api.payment_gateways.tinkoff.service.tinkoff_client') as mock_client:
        mock_client.add_seller = AsyncMock(
            return_value=TinkoffAddSellerResponse.model_validate({
                "Success": True,
                "ErrorCode": "0",
                "TerminalKey": "test_terminal_e2c",
                "CustomerKey": "seller_123"
            })
        )

        await TinkoffService.initialize_user(
            InitializeUserSchema(
                account_id=123,
            email="test@example.com"
        )
    )

    mock_client.add_seller.assert_called_once_with("123", "test@example.com")


@pytest.mark.asyncio
async def test_remove_card_success():
    """Test successful card removal."""

    with patch('src.api.payment_gateways.tinkoff.service.tinkoff_client') as mock_client:
        mock_client.remove_seller_card = AsyncMock(
            return_value=BaseTinkoffResponse.model_validate({
                "Success": True,
                "ErrorCode": "0"
            })
        )

        await TinkoffService.remove_card(streamer_id=38, card_id="card_123")

        mock_client.remove_seller_card.assert_called_once_with("38", "card_123")


@pytest.mark.asyncio
async def test_ensure_deal_returns_existing(mock_tinkoff_service):
    """Test that existing active deal is returned instead of creating new one."""
    mock_deal = MagicMock()
    mock_deal.deal_id = "existing_deal_123"
    mock_tinkoff_service.uow.deals.get_active = AsyncMock(return_value=mock_deal)

    result = await mock_tinkoff_service._ensure_deal(streamer_id=38)

    assert result == mock_deal
    mock_tinkoff_service.uow.deals.get_active.assert_called_once_with(38)


@pytest.mark.asyncio
async def test_ensure_deal_creates_new_when_none_exists(mock_tinkoff_service):
    """Test that new deal is created when none exists."""
    from src.api.payment_gateways.tinkoff.client.schemas import TinkoffDealResponse

    mock_tinkoff_service.uow.deals.get_active = AsyncMock(return_value=None)

    with patch('src.api.payment_gateways.tinkoff.service.tinkoff_client') as mock_client:
        mock_client.create_deal = AsyncMock(
            return_value=TinkoffDealResponse.model_validate({
                "Success": True,
                "ErrorCode": "0",
                "SpAccumulationId": "new_deal_123"
            })
        )

        mock_deal = MagicMock()
        mock_deal.deal_id = "new_deal_123"
        mock_tinkoff_service.uow.deals.create = AsyncMock(return_value=mock_deal)

        result = await mock_tinkoff_service._ensure_deal(streamer_id=38)

        assert result.deal_id == "new_deal_123"
        mock_client.create_deal.assert_called_once()


@pytest.mark.asyncio
async def test_make_success_url_with_streamer_login(mock_tinkoff_service):
    """Test success URL generation with streamer login."""
    url = TinkoffService._make_success_url("testuser")
    assert url is not None
    assert "testuser" in url
    assert "/donate/" in url


@pytest.mark.asyncio
async def test_make_success_url_without_streamer_login(mock_tinkoff_service):
    """Test success URL generation without streamer login."""
    url = TinkoffService._make_success_url(None)
    assert "/donate/" not in url if url else True


@pytest.mark.asyncio
async def test_confirm_deposit_creates_payment_and_updates_deal(
    mock_tinkoff_service, payment_session
):
    """Test deposit confirmation creates payment record and updates deal amount."""
    transaction_id = uuid4()
    deal_id = "deal_123"
    streamer_id = 38
    amount = 1000

    from src.core.database.models import Payment, Deal

    deal = Deal(
        streamer_id=streamer_id,
        deal_id=deal_id,
        amount=500,
        open_status=True
    )
    payment_session.add(deal)
    await payment_session.commit()

    # Mock add_amount to actually update the database
    async def mock_add_amount(deal_id_arg: str, amount_arg: int):
        stmt = select(Deal).where(Deal.deal_id == deal_id_arg)
        deal_obj = await payment_session.scalar(stmt)
        if deal_obj:
            deal_obj.amount += amount_arg
            await payment_session.commit()

    mock_tinkoff_service.uow.deals.add_amount = mock_add_amount

    # Mock get_active to return the real deal from database
    async def mock_get_active(streamer_id_arg: int):
        stmt = select(Deal).where(Deal.streamer_id == streamer_id_arg, Deal.open_status == True)
        return await payment_session.scalar(stmt)

    mock_tinkoff_service.uow.deals.get_active = mock_get_active

    await mock_tinkoff_service.confirm_deposit(
        transaction_id=transaction_id,
        order_id="order_123",
        streamer_id=streamer_id,
        amount=amount
    )

    await payment_session.refresh(deal)
    assert deal.amount == 1500
