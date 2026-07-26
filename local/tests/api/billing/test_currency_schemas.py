import pytest
from datetime import datetime

from src.api.billing.schemas import TransactionReadSchema
from src.api.user_service.schemas import FullBalanceSchema
from src.core.database.enums.transactions import (
    TransactionStatusEnum,
    PaymentProviderEnum,
)


class TestCurrencySchemas:
    def test_full_balance_schema_four_fields(self):
        schema = FullBalanceSchema(
            main_balance=10000,
            stake_balance=5000,
            oxypay_balance=2000,
            oxypay_stake_balance=1000,
        )
        result = schema.model_dump(mode="json")

        assert len(result) == 4
        assert result["main_balance"] == 10000 // 100.0
        assert result["stake_balance"] == 5000 // 100.0
        assert result["oxypay_balance"] == 2000 // 100.0
        assert result["oxypay_stake_balance"] == 1000 // 100.0

    def test_serialize_amount_oxypay_divides_by_100(self):
        schema = TransactionReadSchema(
            amount=5000,
            status=TransactionStatusEnum.completed,
            payment_provider=PaymentProviderEnum.oxypay,
            created_at=datetime.now(),
            completed_at=None,
            balances=[],
        )
        result = schema.model_dump(mode="json")

        assert result["amount"] == 50
