import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import services
from app.database import get_session
from app.exceptions import InsufficientFundsError, WalletNotFoundError
from app.schemas import OperationRequest, WalletResponse

router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])


@router.get(
    "/{wallet_id}",
    response_model=WalletResponse,
    responses={404: {"description": "Wallet not found"}},
)
async def get_wallet(
    wallet_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> WalletResponse:
    try:
        wallet = await services.get_wallet(session, wallet_id)
    except WalletNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wallet {exc} not found",
        ) from exc
    return WalletResponse.model_validate(wallet)


@router.post(
    "/{wallet_id}/operation",
    response_model=WalletResponse,
    responses={
        400: {"description": "Insufficient funds"},
        404: {"description": "Wallet not found"},
    },
)
async def operate(
    wallet_id: uuid.UUID,
    payload: OperationRequest,
    session: AsyncSession = Depends(get_session),
) -> WalletResponse:
    try:
        wallet = await services.apply_operation(
            session,
            wallet_id=wallet_id,
            operation_type=payload.operation_type,
            amount=payload.amount,
        )
    except WalletNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wallet {exc} not found",
        ) from exc
    except InsufficientFundsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient funds on wallet {exc}",
        ) from exc
    return WalletResponse.model_validate(wallet)
