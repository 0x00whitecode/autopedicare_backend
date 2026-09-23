import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_permission, require_role
from app.ecommerce.models import Cart, CartItem, InventoryItem, Order, OrderItem, Product
from app.ecommerce.schemas import (
    CartItemRequest,
    CartItemResponse,
    CartResponse,
    CheckoutRequest,
    CommerceLedgerEntry,
    InventoryItemCreate,
    InventoryItemResponse,
    OrderItemResponse,
    OrderResponse,
    ProductCreate,
    ProductResponse,
    ProductSearchResult,
    ProductUpdate,
    RecommendationResponse,
)
from app.ecommerce.services import (
    add_item_to_cart,
    calculate_cart_total,
    checkout_cart,
    create_product,
    ensure_inventory,
    get_admin_ledger,
    get_or_create_cart,
    get_order_by_id,
    get_product_by_id,
    get_product_recommendations,
    list_cart_items,
    list_orders_for_user,
    list_products,
    search_products,
    update_product,
)
from app.users.models import User

router = APIRouter(prefix="/commerce", tags=["Commerce"])


@router.get("/products", response_model=list[ProductResponse])
async def list_product_catalog(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    products, _ = await list_products(db, offset=offset, limit=limit)
    return products


@router.get("/products/search", response_model=list[ProductSearchResult])
async def product_search(
    q: str = Query(..., min_length=2, description="Search terms for product discovery"),
    category: str | None = Query(default=None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    results = await search_products(db, q, category=category, offset=offset, limit=limit)
    return [ProductSearchResult(**item) for item in results]


@router.get("/products/recommendations", response_model=list[RecommendationResponse])
async def product_recommendations(
    product_id: uuid.UUID | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    results = await get_product_recommendations(db, product_id=product_id, category=category, limit=limit)
    return [RecommendationResponse(**item) for item in results]


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    product = await get_product_by_id(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product


@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("manage_products"))],
)
async def create_new_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        product = await create_product(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await db.commit()
    return product


@router.patch(
    "/products/{product_id}",
    response_model=ProductResponse,
    dependencies=[Depends(require_permission("manage_products"))],
)
async def update_existing_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
):
    product = await get_product_by_id(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    product = await update_product(db, product, payload)
    await db.commit()
    return product


@router.post(
    "/products/{product_id}/inventory",
    response_model=InventoryItemResponse,
    dependencies=[Depends(require_permission("manage_inventory"))],
)
async def set_inventory(
    product_id: uuid.UUID,
    payload: InventoryItemCreate,
    db: AsyncSession = Depends(get_db),
):
    if payload.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product ID mismatch.")

    try:
        inventory = await ensure_inventory(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await db.commit()
    return inventory


@router.get("/cart", response_model=CartResponse)
async def get_user_cart(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart = await get_or_create_cart(db, user.id)
    items = await list_cart_items(db, cart)
    item_responses = []
    for item in items:
        product = await get_product_by_id(db, item.product_id)
        item_responses.append(
            CartItemResponse(
                id=item.id,
                cart_id=item.cart_id,
                product_id=item.product_id,
                product_name=product.name if product else None,
                quantity=item.quantity,
                unit_price=item.unit_price,
                created_at=item.created_at,
            )
        )
    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        status=cart.status.value,
        items=item_responses,
        total_amount=await calculate_cart_total(items),
        created_at=cart.created_at,
        updated_at=cart.updated_at,
    )


@router.post("/cart/items", response_model=CartItemResponse)
async def add_cart_item(
    payload: CartItemRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await add_item_to_cart(db, user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await db.commit()
    product = await get_product_by_id(db, item.product_id)
    return CartItemResponse(
        id=item.id,
        cart_id=item.cart_id,
        product_id=item.product_id,
        product_name=product.name if product else None,
        quantity=item.quantity,
        unit_price=item.unit_price,
        created_at=item.created_at,
    )


@router.post("/checkout", response_model=OrderResponse)
async def checkout(
    payload: CheckoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        order = await checkout_cart(db, user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await db.commit()

    order = await get_order_by_id(db, order.id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    items = list((await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))).scalars().all())
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        cart_id=order.cart_id,
        status=order.status.value,
        subtotal=order.subtotal,
        shipping_fee=order.shipping_fee,
        discount=order.discount,
        total_amount=order.total_amount,
        currency=order.currency,
        payment_reference=order.payment_reference,
        payment_status=order.payment_status,
        shipping_address=order.shipping_address,
        notes=order.notes,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=[
            OrderItemResponse(
                id=item.id,
                order_id=item.order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                created_at=item.created_at,
            )
            for item in items
        ],
    )


@router.get("/orders", response_model=list[OrderResponse])
async def list_my_orders(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    orders, _ = await list_orders_for_user(db, user.id, offset=offset, limit=limit)
    response = []
    for order in orders:
        items = list((await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))).scalars().all())
        response.append(
            OrderResponse(
                id=order.id,
                user_id=order.user_id,
                cart_id=order.cart_id,
                status=order.status.value,
                subtotal=order.subtotal,
                shipping_fee=order.shipping_fee,
                discount=order.discount,
                total_amount=order.total_amount,
                currency=order.currency,
                payment_reference=order.payment_reference,
                payment_status=order.payment_status,
                shipping_address=order.shipping_address,
                notes=order.notes,
                created_at=order.created_at,
                updated_at=order.updated_at,
                items=[
                    OrderItemResponse(
                        id=item.id,
                        order_id=item.order_id,
                        product_id=item.product_id,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        total_price=item.total_price,
                        created_at=item.created_at,
                    )
                    for item in items
                ],
            )
        )
    return response


@router.get(
    "/admin/ledger",
    response_model=list[CommerceLedgerEntry],
    dependencies=[Depends(require_role("superadmin")), Depends(require_permission("view_commerce_ledger"))],
)
async def commerce_ledger(db: AsyncSession = Depends(get_db)):
    entries = await get_admin_ledger(db)
    return [CommerceLedgerEntry(**entry) for entry in entries]
