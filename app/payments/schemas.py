from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WalletTopUpRequest(BaseModel):
    amount: float = Field(gt=0)
    currency: str = Field(default="NGN", max_length=10)
    provider: str | None = Field(default=None, max_length=30)


class PaymentGatewaySettingsRequest(BaseModel):
    provider: str = Field(..., max_length=30)
    public_key: str = Field(..., min_length=1, max_length=255)
    secret_key: str = Field(..., min_length=1, max_length=255)
    is_active: bool = False


class PaymentGatewaySettingsResponse(BaseModel):
    id: UUID
    provider: str
    public_key: str
    secret_key: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WalletTransactionResponse(BaseModel):
    id: UUID
    user_id: UUID
    provider: str
    reference: str
    currency: str
    amount: float
    direction: str
    status: str
    metadata: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
