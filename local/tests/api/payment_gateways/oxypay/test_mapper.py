from src.api.payment_gateways.oxypay.mapper import OxypayWebhookMapper
from src.api.payment_gateways.oxypay.schemas import OxypayWebhookPayload
from src.core.database.enums.transactions import (
    TransactionStatusEnum,
    PaymentProviderEnum,
)


class TestOxypayWebhookMapper:
    def test_accepted_maps_to_completed(self):
        payload = OxypayWebhookPayload(
            token="tok_123",
            status="accepted",
            amount=1000,
            currency="RUB",
            order_number="ord_1",
        )

        event = OxypayWebhookMapper.map_to_unified_event(payload)

        assert event.status == TransactionStatusEnum.completed
        assert event.external_id == "ord_1"
        assert event.provider == PaymentProviderEnum.oxypay
        assert event.amount == 1000

    def test_declined_maps_to_failed(self):
        payload = OxypayWebhookPayload(
            token="tok_456",
            status="declined",
            amount=2000,
            currency="RUB",
            order_number="ord_2",
        )

        event = OxypayWebhookMapper.map_to_unified_event(payload)

        assert event.status == TransactionStatusEnum.failed
        assert event.external_id == "ord_2"

    def test_pending_maps_to_pending(self):
        payload = OxypayWebhookPayload(
            token="tok_789",
            status="pending",
            amount=3000,
            currency="RUB",
            order_number="ord_3",
        )

        event = OxypayWebhookMapper.map_to_unified_event(payload)

        assert event.status == TransactionStatusEnum.pending
        assert event.external_id == "ord_3"

    def test_unknown_status_maps_to_pending(self):
        """Unknown statuses should default to pending"""
        payload = OxypayWebhookPayload(
            token="tok_unknown",
            status="init",
            amount=500,
            currency="RUB",
            order_number="ord_4",
        )

        event = OxypayWebhookMapper.map_to_unified_event(payload)

        assert event.status == TransactionStatusEnum.pending

    def test_missing_order_number_uses_token(self):
        """When order_number is None, external_id should fall back to token"""
        payload = OxypayWebhookPayload(
            token="tok_fallback",
            status="accepted",
            amount=100,
            currency="RUB",
            order_number=None,
        )

        event = OxypayWebhookMapper.map_to_unified_event(payload)

        assert event.external_id == "tok_fallback"
