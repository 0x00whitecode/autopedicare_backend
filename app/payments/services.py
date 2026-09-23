import hashlib
import hmac
import json
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.payments.models import (
    PaymentGatewaySettings,
    PaymentProvider,
    PaymentStatus,
    WalletTransaction,
)


def normalize_provider(provider: str) -> PaymentProvider:
    try:
        return PaymentProvider(provider)
    except ValueError as exc:
        raise ValueError(
            "Unsupported payment provider. Allowed values: paystack, flutterwave, wallet."
        ) from exc


async def get_active_payment_gateway(db: AsyncSession) -> PaymentGatewaySettings | None:
    result = await db.execute(
        select(PaymentGatewaySettings).where(PaymentGatewaySettings.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def get_gateway_by_provider(
    db: AsyncSession,
    provider: PaymentProvider,
) -> PaymentGatewaySettings | None:
    result = await db.execute(
        select(PaymentGatewaySettings).where(PaymentGatewaySettings.provider == provider)
    )
    return result.scalar_one_or_none()


def verify_paystack_signature(secret_key: str, raw_body: bytes, signature: str | None) -> bool:
    if not signature:
        return False
    expected = hmac.new(secret_key.encode("utf-8"), raw_body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_flutterwave_signature(secret_key: str, raw_body: bytes, signature: str | None) -> bool:
    if not signature:
        return False
    expected = hmac.new(secret_key.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


async def upsert_payment_gateway(
    db: AsyncSession,
    *,
    provider: str,
    public_key: str,
    secret_key: str,
    is_active: bool = False,
) -> PaymentGatewaySettings:
    provider_enum = normalize_provider(provider)

    existing = await db.scalar(
        select(PaymentGatewaySettings).where(PaymentGatewaySettings.provider == provider_enum)
    )

    if existing is None:
        config = PaymentGatewaySettings(
            provider=provider_enum,
            public_key=public_key,
            secret_key=secret_key,
            is_active=is_active,
        )
        db.add(config)
        await db.flush()
        await db.refresh(config)
        return config

    existing.public_key = public_key
    existing.secret_key = secret_key
    existing.is_active = is_active
    await db.flush()
    await db.refresh(existing)
    return existing


async def activate_payment_gateway(db: AsyncSession, gateway_id: uuid.UUID) -> PaymentGatewaySettings:
    all_gateways = (await db.execute(select(PaymentGatewaySettings))).scalars().all()
    for gateway in all_gateways:
        gateway.is_active = gateway.id == gateway_id

    active = next((g for g in all_gateways if g.id == gateway_id), None)
    if active is None:
        raise ValueError("Payment gateway not found.")

    await db.flush()
    await db.refresh(active)
    return active


async def create_wallet_transaction(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    amount: float,
    currency: str,
    provider: str,
    direction: str = "credit",
    metadata: str | None = None,
    status: PaymentStatus = PaymentStatus.PENDING,
) -> WalletTransaction:
    provider_enum = normalize_provider(provider)
    gateway = await get_active_payment_gateway(db)

    if gateway is None:
        raise ValueError("No active payment gateway is configured.")

    if gateway.provider != provider_enum:
        raise ValueError("The requested payment provider does not match the active gateway configuration.")

    reference = f"{provider}-{uuid.uuid4()}"

    transaction = WalletTransaction(
        user_id=user_id,
        provider=provider_enum,
        reference=reference,
        currency=currency,
        amount=amount,
        direction=direction,
        status=status,
        metadata=metadata,
    )
    db.add(transaction)
    await db.flush()
    await db.refresh(transaction)
    return transaction


async def get_wallet_transaction_by_reference(
    db: AsyncSession,
    provider: PaymentProvider,
    reference: str,
) -> WalletTransaction | None:
    result = await db.execute(
        select(WalletTransaction).where(
            WalletTransaction.provider == provider,
            WalletTransaction.reference == reference,
        )
    )
    return result.scalar_one_or_none()


async def update_transaction_status(
    db: AsyncSession,
    *,
    provider: PaymentProvider,
    reference: str,
    status: PaymentStatus,
    metadata: Any | None = None,
) -> WalletTransaction | None:
    transaction = await get_wallet_transaction_by_reference(db, provider, reference)
    if transaction is None:
        return None

    transaction.status = status
    if metadata is not None:
        transaction.metadata = json.dumps(metadata, default=str)

    await db.flush()
    await db.refresh(transaction)
    return transaction


async def handle_paystack_webhook(
    db: AsyncSession,
    raw_body: bytes,
    signature: str | None,
) -> dict[str, Any]:
    gateway = await get_gateway_by_provider(db, PaymentProvider.PAYSTACK)
    if gateway is None:
        raise ValueError("Paystack gateway is not configured.")

    if not verify_paystack_signature(gateway.secret_key, raw_body, signature):
        raise PermissionError("Invalid Paystack webhook signature.")

    payload = json.loads(raw_body.decode("utf-8"))
    event = payload.get("event")
    data = payload.get("data") or {}
    reference = data.get("reference")

    if not reference:
        raise ValueError("Paystack webhook payload missing reference.")

    status = data.get("status")
    if event == "charge.success" and status == "success":
        transaction = await update_transaction_status(
            db,
            provider=PaymentProvider.PAYSTACK,
            reference=reference,
            status=PaymentStatus.SUCCESS,
            metadata={"event": event, "provider": "paystack", "status": status},
        )
        return {"status": "ok", "reference": reference, "transaction_id": str(transaction.id) if transaction else None}

    if event == "charge.failed":
        transaction = await update_transaction_status(
            db,
            provider=PaymentProvider.PAYSTACK,
            reference=reference,
            status=PaymentStatus.FAILED,
            metadata={"event": event, "provider": "paystack", "status": status},
        )
        return {"status": "ok", "reference": reference, "transaction_id": str(transaction.id) if transaction else None}

    return {"status": "ignored", "reference": reference, "event": event}


async def handle_flutterwave_webhook(
    db: AsyncSession,
    raw_body: bytes,
    signature: str | None,
) -> dict[str, Any]:
    gateway = await get_gateway_by_provider(db, PaymentProvider.FLUTTERWAVE)
    if gateway is None:
        raise ValueError("Flutterwave gateway is not configured.")

    if not verify_flutterwave_signature(gateway.secret_key, raw_body, signature):
        raise PermissionError("Invalid Flutterwave webhook signature.")

    payload = json.loads(raw_body.decode("utf-8"))
    event = payload.get("event")
    data = payload.get("data") or {}
    reference = data.get("tx_ref") or data.get("reference")

    if not reference:
        raise ValueError("Flutterwave webhook payload missing reference.")

    status = data.get("status")
    if event in {"charge.completed", "transaction.successful"} or status in {"successful", "success"}:
        transaction = await update_transaction_status(
            db,
            provider=PaymentProvider.FLUTTERWAVE,
            reference=reference,
            status=PaymentStatus.SUCCESS,
            metadata={"event": event, "provider": "flutterwave", "status": status},
        )
        return {"status": "ok", "reference": reference, "transaction_id": str(transaction.id) if transaction else None}

    if status in {"failed", "cancelled", "error"}:
        transaction = await update_transaction_status(
            db,
            provider=PaymentProvider.FLUTTERWAVE,
            reference=reference,
            status=PaymentStatus.FAILED,
            metadata={"event": event, "provider": "flutterwave", "status": status},
        )
        return {"status": "ok", "reference": reference, "transaction_id": str(transaction.id) if transaction else None}

    return {"status": "ignored", "reference": reference, "event": event}


async def list_wallet_transactions(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[WalletTransaction], int]:
    query = select(WalletTransaction).where(WalletTransaction.user_id == user_id)
    total = (await db.execute(select(__import__('sqlalchemy').func.count()).select_from(query.subquery()))).scalar() or 0
    query = query.order_by(WalletTransaction.created_at.desc()).offset(offset).limit(limit)
    transactions = list((await db.execute(query)).scalars().all())
    return transactions, int(total)


async def list_gateway_settings(db: AsyncSession) -> list[PaymentGatewaySettings]:
    result = await db.execute(select(PaymentGatewaySettings).order_by(PaymentGatewaySettings.created_at.desc()))
    return list(result.scalars().all())
