from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=180)
    description: str | None = Field(default=None)
    category: str = Field(default="general", min_length=1, max_length=120)
    brand: str | None = Field(default=None, max_length=120)
    price: float = Field(default=0.0, ge=0)
    image_url: str | None = Field(default=None, max_length=500)
    status: str = Field(default="active")


class ProductUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=100)
    name: str | None = Field(default=None, min_length=1, max_length=180)
    description: str | None = Field(default=None)
    category: str | None = Field(default=None, min_length=1, max_length=120)
    brand: str | None = Field(default=None, max_length=120)
    price: float | None = Field(default=None, ge=0)
    image_url: str | None = Field(default=None, max_length=500)
    status: str | None = Field(default=None)


class ProductResponse(BaseModel):
    id: UUID
    sku: str
    name: str
    description: str | None
    category: str
    brand: str | None
    price: float
    image_url: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InventoryItemCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=5, ge=0)
    location: str | None = Field(default=None, max_length=150)


class InventoryItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    quantity: int
    reserved_quantity: int
    low_stock_threshold: int
    location: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class CartItemRequest(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0)


class CartItemResponse(BaseModel):
    id: UUID
    cart_id: UUID
    product_id: UUID
    product_name: str | None = None
    quantity: int
    unit_price: float
    created_at: datetime

    model_config = {"from_attributes": True}


class CartResponse(BaseModel):
    id: UUID
    user_id: UUID
    status: str
    items: list[CartItemResponse]
    total_amount: float = 0.0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CheckoutRequest(BaseModel):
    cart_id: UUID
    shipping_address: str = Field(..., min_length=3, max_length=2000)
    notes: str | None = Field(default=None, max_length=500)


class OrderItemResponse(BaseModel):
    id: UUID
    order_id: UUID
    product_id: UUID
    quantity: int
    unit_price: float
    total_price: float
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: UUID
    user_id: UUID
    cart_id: UUID | None
    status: str
    subtotal: float
    shipping_fee: float
    discount: float
    total_amount: float
    currency: str
    payment_reference: str | None
    payment_status: str
    shipping_address: str
    notes: str | None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse]

    model_config = {"from_attributes": True}


class ProductSearchResult(BaseModel):
    product_id: UUID
    name: str
    category: str
    price: float
    description: str | None = None
    score: float = 0.0

    model_config = {"from_attributes": True}


class RecommendationResponse(BaseModel):
    product_id: UUID
    name: str
    category: str
    score: float = 0.0
    rationale: str

    model_config = {"from_attributes": True}


class CommerceLedgerEntry(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    payment_reference: str | None
    status: str
    amount: float
    currency: str
    created_at: datetime

    model_config = {"from_attributes": True}
