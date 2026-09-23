import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.users.models import User

from enum import Enum as PyEnum


class PaymentProvider(str, PyEnum):
    PAYSTACK = "paystack"
    FLUTTERWAVE = "flutterwave"
    WALLET = "wallet"


class PaymentStatus(str, PyEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REVERSED = "reversed"


class PaymentGatewaySettings(Base):
    __tablename__ = "payment_gateway_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(PaymentProvider, name="payment_provider"),
        nullable=False,
        unique=True,
        index=True,
    )
    public_key: Mapped[str] = mapped_column(String(255), nullable=False)
    secret_key: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(PaymentProvider, name="payment_provider"),
        nullable=False,
    )
    reference: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="NGN")
    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        nullable=False,
        default=PaymentStatus.PENDING,
    )
    metadata: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="wallet_transactions",
    )
