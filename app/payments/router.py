import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_permission, require_role
from app.payments.models import PaymentGatewaySettings, PaymentProvider, PaymentStatus
from app.payments.schemas import (
    PaymentGatewaySettingsRequest,
    PaymentGatewaySettingsResponse,
    WalletTopUpRequest,
    WalletTransactionResponse,
)
from app.payments.services import (
    activate_payment_gateway,
    create_wallet_transaction,
    get_active_payment_gateway,
    handle_flutterwave_webhook,
    handle_paystack_webhook,
    list_gateway_settings,
    list_wallet_transactions,
    upsert_payment_gateway,
)
from app.users.models import User

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get(
    "/gateway/settings",
    response_model=list[PaymentGatewaySettingsResponse],
    dependencies=[Depends(require_role("superadmin")), Depends(require_permission("manage_finance"))],
)
async def get_gateway_settings(
    db: AsyncSession = Depends(get_db),
):
    return await list_gateway_settings(db)


@router.post(
    "/gateway/settings",
    response_model=PaymentGatewaySettingsResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("superadmin")), Depends(require_permission("manage_finance"))],
)
async def configure_gateway(
    payload: PaymentGatewaySettingsRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        gateway = await upsert_payment_gateway(
            db,
            provider=payload.provider,
            public_key=payload.public_key,
            secret_key=payload.secret_key,
            is_active=payload.is_active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if payload.is_active:
        gateway = await activate_payment_gateway(db, gateway.id)

    await db.commit()
    return gateway


@router.patch(
    "/gateway/settings/{gateway_id}/activate",
    response_model=PaymentGatewaySettingsResponse,
    dependencies=[Depends(require_role("superadmin")), Depends(require_permission("manage_finance"))],
)
async def activate_gateway(
    gateway_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    gateway = await activate_payment_gateway(db, gateway_id)
    await db.commit()
    return gateway


@router.post("/wallet/topup", response_model=WalletTransactionResponse, status_code=status.HTTP_201_CREATED)
async def top_up_wallet(
    payload: WalletTopUpRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    active_gateway = await get_active_payment_gateway(db)
    provider = payload.provider or (active_gateway.provider.value if active_gateway else None)

    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active payment gateway is configured.",
        )

    try:
        transaction = await create_wallet_transaction(
            db,
            user.id,
            amount=payload.amount,
            currency=payload.currency,
            provider=provider,
            direction="credit",
            metadata=f"{provider} wallet top-up",
            status=PaymentStatus.PENDING,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await db.commit()
    return transaction


@router.post("/paystack/webhook")
async def paystack_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    raw_body = await request.body()
    signature = request.headers.get("x-paystack-signature")

    try:
        result = await handle_paystack_webhook(db, raw_body, signature)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    await db.commit()
    return result


@router.post("/flutterwave/webhook")
async def flutterwave_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    raw_body = await request.body()
    signature = request.headers.get("verif-hash") or request.headers.get("x-flutterwave-signature")

    try:
        result = await handle_flutterwave_webhook(db, raw_body, signature)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    await db.commit()
    return result


@router.get("/wallet/transactions", response_model=list[WalletTransactionResponse])
async def list_transactions(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    transactions, _ = await list_wallet_transactions(db, user.id, offset=offset, limit=limit)
    return transactions
