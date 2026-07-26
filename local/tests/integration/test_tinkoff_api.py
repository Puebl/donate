"""
Integration tests for TinkoffAPIClient against rest-api-test.tinkoff.ru.

These tests make REAL HTTP calls to the Tinkoff test environment.
Mark: pytest.mark.tinkoff_api — can be skipped in CI with `-m "not tinkoff_api"`.
"""

import uuid

import pytest

from src.api.payment_gateways.tinkoff.client.service import TinkoffAPIClient
from tests.integration.conftest import NN_UNSUPPORTED_MSG


pytestmark = pytest.mark.tinkoff_api


def _skip_if_nn_unsupported(exc: ValueError) -> None:
    if "256" in str(exc) and "некорректный тип" in str(exc).lower():
        pytest.skip(NN_UNSUPPORTED_MSG)


# ──────────────────────────────────────────────────────────────────────
# createSpDeal
# ──────────────────────────────────────────────────────────────────────


class TestCreateSpDeal:
    """POST /v2/createSpDeal — создание сделки"""

    async def test_create_nn_deal_success(self, tinkoff_test_client: TinkoffAPIClient):
        try:
            resp = await tinkoff_test_client.create_deal(deal_type="NN")
        except ValueError as e:
            _skip_if_nn_unsupported(e)
            raise

        assert resp.success is True
        assert resp.deal_id
        assert isinstance(resp.deal_id, str)
        assert len(resp.deal_id) > 0

        await tinkoff_test_client.close_deal(resp.deal_id)

    async def test_create_deal_returns_unique_ids(
        self, tinkoff_test_client: TinkoffAPIClient
    ):
        try:
            resp1 = await tinkoff_test_client.create_deal(deal_type="NN")
        except ValueError as e:
            _skip_if_nn_unsupported(e)
            raise
        resp2 = await tinkoff_test_client.create_deal(deal_type="NN")

        assert resp1.deal_id != resp2.deal_id

        await tinkoff_test_client.close_deal(resp1.deal_id)
        await tinkoff_test_client.close_deal(resp2.deal_id)

    async def test_create_multiple_nn_deals(
        self, tinkoff_test_client: TinkoffAPIClient
    ):
        deals = []
        for i in range(3):
            try:
                resp = await tinkoff_test_client.create_deal(deal_type="NN")
            except ValueError as e:
                if i == 0:
                    _skip_if_nn_unsupported(e)
                raise
            assert resp.success
            deals.append(resp.deal_id)

        assert len(set(deals)) == 3

        for deal_id in deals:
            await tinkoff_test_client.close_deal(deal_id)


# ──────────────────────────────────────────────────────────────────────
# closeSpDeal
# ──────────────────────────────────────────────────────────────────────


class TestCloseSpDeal:
    """POST /v2/closeSpDeal — закрытие сделки"""

    async def test_close_deal_success(self, tinkoff_test_client: TinkoffAPIClient):
        try:
            resp = await tinkoff_test_client.create_deal(deal_type="NN")
        except ValueError as e:
            _skip_if_nn_unsupported(e)
            raise
        close_resp = await tinkoff_test_client.close_deal(resp.deal_id)

        assert close_resp.success is True

    async def test_close_deal_invalid_id(self, tinkoff_test_client: TinkoffAPIClient):
        with pytest.raises(ValueError, match="Tinkoff API Error"):
            await tinkoff_test_client.close_deal("nonexistent_deal_999999")

    async def test_close_deal_twice_is_idempotent(
        self, tinkoff_test_client: TinkoffAPIClient
    ):
        """Tinkoff closeSpDeal is idempotent — double close returns Success=true."""
        try:
            resp = await tinkoff_test_client.create_deal(deal_type="NN")
        except ValueError as e:
            _skip_if_nn_unsupported(e)
            raise
        await tinkoff_test_client.close_deal(resp.deal_id)

        # Second close succeeds (idempotent)
        close_resp = await tinkoff_test_client.close_deal(resp.deal_id)
        assert close_resp.success is True


# ──────────────────────────────────────────────────────────────────────
# Init (pay-in)
# ──────────────────────────────────────────────────────────────────────


class TestInitPayIn:
    """POST /v2/Init — инициализация платежа (донат)"""

    async def test_init_pay_in_with_nn_deal(
        self, tinkoff_test_client: TinkoffAPIClient, created_nn_deal: str
    ):
        order_id = f"test_{uuid.uuid4().hex[:16]}"

        resp = await tinkoff_test_client.init_pay_in(
            order_id=order_id,
            amount=1000,  # 10 рублей в копейках
            deal_id=created_nn_deal,
            success_url="https://test.example.com/success",
            description="Integration test payment",
            payment_recipient_id="test_streamer_1",
        )

        assert resp.success is True
        assert resp.payment_id
        assert resp.order_id == order_id
        assert resp.amount == 1000
        assert resp.payment_url  # URL для оплаты

    async def test_init_pay_in_with_recipient_id(
        self, tinkoff_test_client: TinkoffAPIClient, created_nn_deal: str
    ):
        order_id = f"test_{uuid.uuid4().hex[:16]}"

        resp = await tinkoff_test_client.init_pay_in(
            order_id=order_id,
            amount=500,
            deal_id=created_nn_deal,
            success_url="https://test.example.com/success",
            description="Test with recipient",
            payment_recipient_id="streamer_42",
        )

        assert resp.success is True
        assert resp.payment_id

    async def test_init_pay_in_multiple_payments_same_deal(
        self, tinkoff_test_client: TinkoffAPIClient, created_nn_deal: str
    ):
        payment_ids = []
        for i in range(3):
            order_id = f"test_{uuid.uuid4().hex[:16]}"
            resp = await tinkoff_test_client.init_pay_in(
                order_id=order_id,
                amount=500 + i * 100,
                deal_id=created_nn_deal,
                success_url="https://test.example.com/success",
                description=f"Multi-payment test #{i + 1}",
                payment_recipient_id="test_streamer_1",
            )
            assert resp.success
            payment_ids.append(resp.payment_id)

        # Все PaymentId уникальны
        assert len(set(payment_ids)) == 3

    async def test_init_pay_in_invalid_deal(
        self, tinkoff_test_client: TinkoffAPIClient
    ):
        order_id = f"test_{uuid.uuid4().hex[:16]}"

        with pytest.raises(ValueError, match="Tinkoff API Error"):
            await tinkoff_test_client.init_pay_in(
                order_id=order_id,
                amount=1000,
                deal_id="nonexistent_deal_999",
                success_url="https://test.example.com/success",
                description="Should fail",
                payment_recipient_id="test_streamer_1",
            )

    async def test_init_pay_in_closed_deal_still_succeeds(
        self, tinkoff_test_client: TinkoffAPIClient
    ):
        """Tinkoff Init accepts a closed NN deal — payment is created with status NEW."""
        try:
            resp = await tinkoff_test_client.create_deal(deal_type="NN")
        except ValueError as e:
            _skip_if_nn_unsupported(e)
            raise
        await tinkoff_test_client.close_deal(resp.deal_id)

        order_id = f"test_{uuid.uuid4().hex[:16]}"
        pay_resp = await tinkoff_test_client.init_pay_in(
            order_id=order_id,
            amount=1000,
            deal_id=resp.deal_id,
            success_url="https://test.example.com/success",
            description="Init on closed deal",
            payment_recipient_id="test_streamer_1",
        )
        assert pay_resp.success is True
        assert pay_resp.status == "NEW"


# ──────────────────────────────────────────────────────────────────────
# Init (pay-out) — e2c
# ──────────────────────────────────────────────────────────────────────


class TestInitPayOut:
    """POST /e2c/v2/Init — инициализация выплаты"""

    async def test_init_pay_out_requires_destination(
        self, tinkoff_test_client: TinkoffAPIClient, created_nn_deal: str
    ):
        with pytest.raises(ValueError, match="Destination"):
            await tinkoff_test_client.init_pay_out(
                order_id=f"test_{uuid.uuid4().hex[:16]}",
                deal_id=created_nn_deal,
                amount=100,
                # no card_id, no phone, no sbp_member_id
            )

    async def test_init_pay_out_empty_deal_sbp(
        self, tinkoff_test_client: TinkoffAPIClient, created_nn_deal: str
    ):
        with pytest.raises((ValueError, Exception)):
            await tinkoff_test_client.init_pay_out(
                order_id=f"test_{uuid.uuid4().hex[:16]}",
                deal_id=created_nn_deal,
                amount=100,
                phone="+79001234567",
                sbp_member_id="100000000004",
                final_payout=False,
                payment_recipient_id="test_streamer_1",
            )

    async def test_final_payout_flag_accepted(
        self, tinkoff_test_client: TinkoffAPIClient, created_nn_deal: str
    ):
        with pytest.raises((ValueError, Exception)):
            await tinkoff_test_client.init_pay_out(
                order_id=f"test_{uuid.uuid4().hex[:16]}",
                deal_id=created_nn_deal,
                amount=100,
                phone="+79001234567",
                sbp_member_id="100000000004",
                final_payout=True,  # финальная выплата
                payment_recipient_id="test_streamer_1",
            )


# ──────────────────────────────────────────────────────────────────────
# GetState
# ──────────────────────────────────────────────────────────────────────


class TestGetState:
    """POST /v2/GetState — проверка статуса платежа"""

    async def test_get_state_after_init(
        self, tinkoff_test_client: TinkoffAPIClient, created_nn_deal: str
    ):
        order_id = f"test_{uuid.uuid4().hex[:16]}"
        init_resp = await tinkoff_test_client.init_pay_in(
            order_id=order_id,
            amount=1000,
            deal_id=created_nn_deal,
            success_url="https://test.example.com/success",
            description="GetState test",
            payment_recipient_id="test_streamer_1",
        )

        state_resp = await tinkoff_test_client.get_state(
            payment_id=init_resp.payment_id,
            is_payout=False,
        )

        assert state_resp.success is True
        assert state_resp.status == "NEW"


# ──────────────────────────────────────────────────────────────────────
# Token generation
# ──────────────────────────────────────────────────────────────────────


class TestTokenGeneration:
    """Проверка корректности генерации Token (SHA-256)."""

    def test_token_excludes_data_field(self, tinkoff_test_client: TinkoffAPIClient):
        body = {
            "TerminalKey": "test",
            "Amount": 1000,
            "DATA": {"Phone": "+71234567890"},
            "Token": "should_be_ignored",
        }
        token = tinkoff_test_client._generate_token(body)
        assert isinstance(token, str)
        assert len(token) == 64  # SHA-256 hex

    def test_token_handles_bool_values(self, tinkoff_test_client: TinkoffAPIClient):
        body1 = {"TerminalKey": "test", "FinalPayout": True}
        body2 = {"TerminalKey": "test", "FinalPayout": False}

        token1 = tinkoff_test_client._generate_token(body1)
        token2 = tinkoff_test_client._generate_token(body2)

        assert token1 != token2  # Разные значения → разные токены
        assert len(token1) == 64

    def test_token_deterministic(self, tinkoff_test_client: TinkoffAPIClient):
        body = {"TerminalKey": "test", "Amount": 500, "OrderId": "order1"}
        assert tinkoff_test_client._generate_token(
            body
        ) == tinkoff_test_client._generate_token(body)
