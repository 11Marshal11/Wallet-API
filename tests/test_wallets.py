import uuid

import pytest


@pytest.mark.asyncio
async def test_get_unknown_wallet_returns_404(client):
    wallet_id = uuid.uuid4()
    response = await client.get(f"/api/v1/wallets/{wallet_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_deposit_creates_wallet(client):
    wallet_id = uuid.uuid4()
    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 1000},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(wallet_id)
    assert body["balance"] == 1000


@pytest.mark.asyncio
async def test_deposit_then_get_returns_balance(client):
    wallet_id = uuid.uuid4()
    await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 500},
    )
    response = await client.get(f"/api/v1/wallets/{wallet_id}")
    assert response.status_code == 200
    assert response.json()["balance"] == 500


@pytest.mark.asyncio
async def test_multiple_deposits_accumulate(client):
    wallet_id = uuid.uuid4()
    for amount in (100, 200, 300):
        await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": amount},
        )
    response = await client.get(f"/api/v1/wallets/{wallet_id}")
    assert response.json()["balance"] == 600


@pytest.mark.asyncio
async def test_withdraw_from_missing_wallet_returns_404(client):
    wallet_id = uuid.uuid4()
    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 100},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_withdraw_insufficient_funds_returns_400(client):
    wallet_id = uuid.uuid4()
    await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 100},
    )
    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 500},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_withdraw_reduces_balance(client):
    wallet_id = uuid.uuid4()
    await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 1000},
    )
    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 250},
    )
    assert response.status_code == 200
    assert response.json()["balance"] == 750


@pytest.mark.asyncio
async def test_invalid_amount_rejected(client):
    wallet_id = uuid.uuid4()
    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": -10},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_operation_type_rejected(client):
    wallet_id = uuid.uuid4()
    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "PURCHASE", "amount": 10},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_uuid_returns_422(client):
    response = await client.get("/api/v1/wallets/not-a-uuid")
    assert response.status_code == 422
