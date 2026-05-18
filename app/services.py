import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import InsufficientFundsError, WalletNotFoundError
from app.models import Wallet
from app.schemas import OperationType


async def get_wallet(session: AsyncSession, wallet_id: uuid.UUID) -> Wallet:
    wallet = await session.get(Wallet, wallet_id)
    if wallet is None:
        raise WalletNotFoundError(str(wallet_id))
    return wallet


async def apply_operation(
    session: AsyncSession,
    wallet_id: uuid.UUID,
    operation_type: OperationType,
    amount: int,
) -> Wallet:
    """Apply a deposit/withdraw atomically with row-level locking.

    Concurrency model:
        * DEPOSIT pre-inserts an empty wallet row via INSERT ... ON CONFLICT
          DO NOTHING, then takes a row-level lock with SELECT ... FOR UPDATE.
          This serialises concurrent updates and avoids unique-violation
          races on first-time creation.
        * WITHDRAW takes the same lock but never creates the wallet.

    Raises:
        WalletNotFoundError: WITHDRAW against an unknown wallet.
        InsufficientFundsError: WITHDRAW that would push balance below zero.
    """
    async with session.begin():
        if operation_type is OperationType.DEPOSIT:
            await session.execute(
                pg_insert(Wallet)
                .values(id=wallet_id, balance=0)
                .on_conflict_do_nothing(index_elements=["id"])
            )

        stmt = (
            select(Wallet)
            .where(Wallet.id == wallet_id)
            .with_for_update()
        )
        wallet = (await session.execute(stmt)).scalar_one_or_none()

        if wallet is None:
            raise WalletNotFoundError(str(wallet_id))

        if operation_type is OperationType.DEPOSIT:
            wallet.balance += amount
        else:  # WITHDRAW
            if wallet.balance < amount:
                raise InsufficientFundsError(str(wallet_id))
            wallet.balance -= amount

    return wallet
