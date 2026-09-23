import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ecommerce.models import (
    Cart,
    CartItem,
    CartStatus,
    InventoryItem,
    Order,
    OrderItem,
    OrderStatus,
    Product,
    ProductSearchIndex,
    ProductStatus,
)
from app.ecommerce.schemas import (
    CartItemRequest,
    CheckoutRequest,
    InventoryItemCreate,
    ProductCreate,
    ProductUpdate,
)


def _build_index_text(product: Product) -> str:
    parts = [
        product.name or "",
        product.category or "",
        product.brand or "",
        product.description or "",
        product.sku or "",
    ]
    return " ".join(part for part in parts if part).lower()


def _build_keyword_text(product: Product) -> str:
    parts = [
        product.name,
        product.category,
        product.brand,
        product.description or "",
        product.sku,
    ]
    unique_keywords = []
    seen = set()
    for part in parts:
        if not part:
            continue
        for token in part.lower().replace("-", " ").split():
            clean = token.strip(" ,.;:/()[]{}+")
            if clean and clean not in seen:
                unique_keywords.append(clean)
                seen.add(clean)
    return ",".join(unique_keywords[:25])


async def sync_search_index(db: AsyncSession, product: Product) -> ProductSearchIndex:
    existing = await db.execute(select(ProductSearchIndex).where(ProductSearchIndex.product_id == product.id))
    index = existing.scalar_one_or_none()
    if index is None:
        index = ProductSearchIndex(product_id=product.id)
        db.add(index)

    index.search_text = _build_index_text(product)
    index.keywords = _build_keyword_text(product)
    index.category = product.category
    index.popularity_score = float(max(0.0, product.price / 100.0))
    index.recommendation_score = float(max(0.0, 1.0 + (product.price / 1000.0)))
    await db.flush()
    await db.refresh(index)
    return index


async def create_product(db: AsyncSession, payload: ProductCreate) -> Product:
    existing = await db.execute(select(Product).where(Product.sku == payload.sku))
    if existing.scalar_one_or_none() is not None:
        raise ValueError("Product with this SKU already exists.")

    product = Product(
        sku=payload.sku,
        name=payload.name,
        description=payload.description,
        category=payload.category,
        brand=payload.brand,
        price=payload.price,
        image_url=payload.image_url,
        status=ProductStatus(payload.status),
    )
    db.add(product)
    await db.flush()
    await db.refresh(product)
    await sync_search_index(db, product)
    return product


async def get_product_by_id(db: AsyncSession, product_id: uuid.UUID) -> Product | None:
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def list_products(db: AsyncSession, *, offset: int = 0, limit: int = 20) -> tuple[list[Product], int]:
    query = select(Product)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    query = query.order_by(Product.created_at.desc()).offset(offset).limit(limit)
    products = list((await db.execute(query)).scalars().all())
    return products, int(total)


async def search_products(
    db: AsyncSession,
    query: str,
    *,
    category: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> list[dict]:
    if not query or len(query.strip()) < 2:
        return []

    search_term = f"%{query.strip().lower()}%"
    stmt = select(Product, ProductSearchIndex).join(ProductSearchIndex, ProductSearchIndex.product_id == Product.id)
    stmt = stmt.where(Product.status == ProductStatus.ACTIVE)
    stmt = stmt.where(ProductSearchIndex.search_text.like(search_term))
    if category:
        stmt = stmt.where(Product.category == category)

    stmt = stmt.order_by(ProductSearchIndex.recommendation_score.desc()).offset(offset).limit(limit)
    results = (await db.execute(stmt)).all()
    return [
        {
            "product_id": product.id,
            "name": product.name,
            "category": product.category,
            "price": product.price,
            "description": product.description,
            "score": float(index.recommendation_score),
        }
        for product, index in results
    ]


async def get_product_recommendations(
    db: AsyncSession,
    *,
    product_id: uuid.UUID | None = None,
    category: str | None = None,
    limit: int = 5,
) -> list[dict]:
    stmt = select(Product, ProductSearchIndex).join(ProductSearchIndex, ProductSearchIndex.product_id == Product.id)
    stmt = stmt.where(Product.status == ProductStatus.ACTIVE)

    if product_id is not None:
        stmt = stmt.where(Product.id != product_id)
    if category:
        stmt = stmt.where(Product.category == category)

    stmt = stmt.order_by(ProductSearchIndex.recommendation_score.desc(), Product.created_at.desc()).limit(limit)
    results = (await db.execute(stmt)).all()
    recs = []
    for product, index in results:
        rationale = f"Popular in {product.category}"
        if category and product.category == category:
            rationale = f"Recommended because it matches {category}"
        recs.append(
            {
                "product_id": product.id,
                "name": product.name,
                "category": product.category,
                "score": float(index.recommendation_score),
                "rationale": rationale,
            }
        )
    return recs


async def update_product(db: AsyncSession, product: Product, payload: ProductUpdate) -> Product:
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if value is not None:
            if key == "status":
                setattr(product, key, ProductStatus(value))
            else:
                setattr(product, key, value)
    await db.flush()
    await db.refresh(product)
    await sync_search_index(db, product)
    return product


async def ensure_inventory(db: AsyncSession, payload: InventoryItemCreate) -> InventoryItem:
    product = await get_product_by_id(db, payload.product_id)
    if product is None:
        raise ValueError("Product not found.")

    existing = await db.execute(select(InventoryItem).where(InventoryItem.product_id == payload.product_id))
    inventory = existing.scalar_one_or_none()
    if inventory is None:
        inventory = InventoryItem(
            product_id=payload.product_id,
            quantity=payload.quantity,
            low_stock_threshold=payload.low_stock_threshold,
            location=payload.location,
        )
        db.add(inventory)
    else:
        inventory.quantity = payload.quantity
        inventory.low_stock_threshold = payload.low_stock_threshold
        inventory.location = payload.location
    await db.flush()
    await db.refresh(inventory)
    return inventory


async def get_inventory_for_product(db: AsyncSession, product_id: uuid.UUID) -> InventoryItem | None:
    result = await db.execute(select(InventoryItem).where(InventoryItem.product_id == product_id))
    return result.scalar_one_or_none()


async def get_or_create_cart(db: AsyncSession, user_id: uuid.UUID) -> Cart:
    result = await db.execute(select(Cart).where(Cart.user_id == user_id, Cart.status == CartStatus.ACTIVE))
    cart = result.scalar_one_or_none()
    if cart is not None:
        return cart

    cart = Cart(user_id=user_id, status=CartStatus.ACTIVE)
    db.add(cart)
    await db.flush()
    await db.refresh(cart)
    return cart


async def add_item_to_cart(db: AsyncSession, user_id: uuid.UUID, payload: CartItemRequest) -> CartItem:
    cart = await get_or_create_cart(db, user_id)
    product = await get_product_by_id(db, payload.product_id)
    if product is None:
        raise ValueError("Product not found.")
    if product.status != ProductStatus.ACTIVE:
        raise ValueError("Product is not available for purchase.")

    inventory = await get_inventory_for_product(db, payload.product_id)
    if inventory is None:
        raise ValueError("Inventory is not configured for this product.")
    if inventory.quantity < payload.quantity:
        raise ValueError("Insufficient stock for this product.")

    existing_item = await db.execute(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == payload.product_id)
    )
    item = existing_item.scalar_one_or_none()
    if item is None:
        item = CartItem(
            cart_id=cart.id,
            product_id=payload.product_id,
            quantity=payload.quantity,
            unit_price=product.price,
        )
        db.add(item)
    else:
        item.quantity += payload.quantity
        item.unit_price = product.price

    await db.flush()
    await db.refresh(item)
    return item


async def get_cart_details(db: AsyncSession, cart_id: uuid.UUID, *, user_id: uuid.UUID | None = None) -> Cart | None:
    query = select(Cart).where(Cart.id == cart_id)
    if user_id is not None:
        query = query.where(Cart.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def list_cart_items(db: AsyncSession, cart: Cart) -> list[CartItem]:
    result = await db.execute(select(CartItem).where(CartItem.cart_id == cart.id).order_by(CartItem.created_at.desc()))
    return list(result.scalars().all())


async def calculate_cart_total(cart_items: list[CartItem]) -> float:
    total = 0.0
    for item in cart_items:
        total += item.quantity * item.unit_price
    return total


async def checkout_cart(db: AsyncSession, user_id: uuid.UUID, payload: CheckoutRequest) -> Order:
    cart = await get_cart_details(db, payload.cart_id, user_id=user_id)
    if cart is None:
        raise ValueError("Cart not found.")
    if cart.status != CartStatus.ACTIVE:
        raise ValueError("Cart is not active.")

    items = await list_cart_items(db, cart)
    if not items:
        raise ValueError("Cart is empty.")

    subtotal = 0.0
    for item in items:
        product = await get_product_by_id(db, item.product_id)
        if product is None:
            raise ValueError(f"Product {item.product_id} no longer exists.")
        if product.status != ProductStatus.ACTIVE:
            raise ValueError(f"Product {product.name} is no longer available.")

        inventory = await get_inventory_for_product(db, item.product_id)
        if inventory is None or inventory.quantity < item.quantity:
            raise ValueError(f"Insufficient stock for product {product.name}.")

        subtotal += item.quantity * item.unit_price

    shipping_fee = 0.0 if subtotal >= 1000 else 50.0
    total_amount = subtotal + shipping_fee
    order = Order(
        user_id=user_id,
        cart_id=cart.id,
        status=OrderStatus.PENDING,
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        discount=0.0,
        total_amount=total_amount,
        currency="NGN",
        payment_reference=f"ORD-{uuid.uuid4().hex[:12].upper()}",
        payment_status="pending",
        shipping_address=payload.shipping_address,
        notes=payload.notes,
    )
    db.add(order)
    await db.flush()
    await db.refresh(order)

    for item in items:
        product = await get_product_by_id(db, item.product_id)
        inventory = await get_inventory_for_product(db, item.product_id)
        if inventory is not None:
            inventory.quantity -= item.quantity
            inventory.reserved_quantity += item.quantity

        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.quantity * item.unit_price,
        )
        db.add(order_item)

    cart.status = CartStatus.CHECKED_OUT
    await db.flush()
    await db.refresh(order)
    return order


async def list_orders_for_user(db: AsyncSession, user_id: uuid.UUID, *, offset: int = 0, limit: int = 20) -> tuple[list[Order], int]:
    query = select(Order).where(Order.user_id == user_id)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    query = query.order_by(Order.created_at.desc()).offset(offset).limit(limit)
    orders = list((await db.execute(query)).scalars().all())
    return orders, int(total)


async def get_order_by_id(db: AsyncSession, order_id: uuid.UUID) -> Order | None:
    result = await db.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()


async def get_admin_ledger(db: AsyncSession) -> list[dict]:
    orders = (await db.execute(select(Order).order_by(Order.created_at.desc()))).scalars().all()

    ledger = []
    for order in orders:
        ledger.append(
            {
                "id": order.id,
                "user_id": order.user_id,
                "type": "order",
                "payment_reference": order.payment_reference,
                "status": order.payment_status,
                "amount": order.total_amount,
                "currency": order.currency,
                "created_at": order.created_at,
            }
        )
    return ledger
