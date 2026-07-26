import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_sbp_banks_success(
    api_client: AsyncClient,
):
    """Test successful retrieval of SBP banks list."""
    response = await api_client.get("/api/sbp_banks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    bank = data[0]
    assert "member_id" in bank
    assert "member_name" in bank
    assert "member_name_rus" in bank
    assert isinstance(bank["member_id"], str)
    assert isinstance(bank["member_name"], str)
    assert isinstance(bank["member_name_rus"], str)


@pytest.mark.asyncio
async def test_get_sbp_banks_has_sber(
    api_client: AsyncClient,
):
    """Test that Sberbank is in SBP banks list."""
    response = await api_client.get("/api/sbp_banks")
    assert response.status_code == 200
    data = response.json()

    sber_found = any(
        "SBER" in bank["member_id"] or "Сбер" in bank["member_name_rus"]
        for bank in data
    )
    assert sber_found, "Sberbank should be in SBP banks list"


@pytest.mark.asyncio
async def test_get_sbp_banks_structure(
    api_client: AsyncClient,
):
    """Test that SBP banks list has correct structure."""
    response = await api_client.get("/api/sbp_banks")
    assert response.status_code == 200
    data = response.json()

    for bank in data:
        assert isinstance(bank, dict)
        assert "member_id" in bank
        assert "member_name" in bank
        assert "member_name_rus" in bank
        assert len(bank["member_id"]) > 0
        assert len(bank["member_name"]) > 0
        assert len(bank["member_name_rus"]) > 0
