import pytest
from unittest.mock import AsyncMock, MagicMock

from src.api.webhooks.service import WebhookService
from src.api.webhooks.schemas import UnifiedWebhookEvent
from src.core.database.enums.transactions import (
    PaymentProviderEnum,
    TransactionStatusEnum,
)


def _make_uow(**overrides):
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)
    uow.rollback = AsyncMock()
    for k, v in overrides.items():
        setattr(uow, k, v)
    return uow


class TestCurrencyWebhook:
    @pytest.mark.asyncio
    async def test_usd_deposit_no_auto_withdraw(self):
        event = UnifiedWebhookEvent(
            external_id="test-ext-id",
            provider=PaymentProviderEnum.oxypay,
            status=TransactionStatusEnum.completed,
            amount=5000,
            deal_id=None,
        )

        confirm_resp = MagicMock()
        confirm_resp.streamer_id = 1
        confirm_resp.amount = 5000

        transaction_service = MagicMock()
        transaction_service.process_webhook = AsyncMock(return_value=confirm_resp)

        user_service = MagicMock()
        user_service.check_auto_withdraw = AsyncMock(return_value=True)

        widget_service = MagicMock()
        widget_service.park_donat_paid = AsyncMock()

        uow = _make_uow()

        service = WebhookService(uow, transaction_service, user_service, widget_service)
        await service.payment_process_event(event)

        user_service.check_auto_withdraw.assert_not_called()
