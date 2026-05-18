"""Concurrency tests — verify row-level locking prevents lost updates.

These tests require PostgreSQL (rely on SELECT ... FOR UPDATE semantics).
"""
import asyncio
import uuid

import pytest


@pytest.mark.asyncio
async def test_parallel_deposits_no_lost_updates(client):
    wallet_id = uuid.uuid4()
    n = 50
    amount = 10

    async def deposit() -> int:
        resp = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": amount},
        )
        return resp.status_code

    statuses = await asyncio.gather(*(deposit() for _ in range(n)))
    assert all(s == 200 for s in statuses)

    final = await client.get(f"/api/v1/wallets/{wallet_id}")
    assert final.json()["balance"] == n * amount


@pytest.mark.asyncio
async def test_parallel_withdraws_never_go_negative(client):
    wallet_id = uuid.uuid4()
    initial = 1000
    withdraw_amount = 30
    attempts = 50  # 50 * 30 = 1500 > 1000

    await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": initial},
    )

    async def withdraw() -> int:
        resp = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "WITHDRAW", "amount": withdraw_amount},
        )
        return resp.status_code

    statuses = await asyncio.gather(*(withdraw() for _ in range(attempts)))
    successes = sum(1 for s in statuses if s == 200)
    rejections = sum(1 for s in statuses if s == 400)

    assert successes + rejections == attempts
    assert successes == initial // withdraw_amount  # 33 successes

    final = await client.get(f"/api/v1/wallets/{wallet_id}")
    assert final.json()["balance"] == initial - successes * withdraw_amount
    assert final.json()["balance"] >= 0


@pytest.mark.asyncio
async def test_mixed_deposit_withdraw_consistent(client):
    wallet_id = uuid.uuid4()
    await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 10_000},
    )

    deposits = [
        client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": 100},
        )
        for _ in range(20)
    ]
    withdraws = [
        client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "WITHDRAW", "amount": 50},
        )
        for _ in range(20)
    ]
    await asyncio.gather(*deposits, *withdraws)

    final = await client.get(f"/api/v1/wallets/{wallet_id}")
    assert final.json()["balance"] == 10_000 + 20 * 100 - 20 * 50
