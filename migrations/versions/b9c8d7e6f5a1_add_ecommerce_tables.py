"""add ecommerce tables

Revision ID: b9c8d7e6f5a1
Revises: a1b2c3d4e5f6
Create Date: 2026-09-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b9c8d7e6f5a1"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "products",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("sku", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("brand", sa.String(length=120), nullable=True),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "HIDDEN", "OUT_OF_STOCK", name="product_status"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_products_sku"), "products", ["sku"], unique=True)

    op.create_table(
        "product_search_indexes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("keywords", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("popularity_score", sa.Float(), nullable=False),
        sa.Column("recommendation_score", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_product_search_indexes_product_id"),
        "product_search_indexes",
        ["product_id"],
        unique=True,
    )

    op.create_table(
        "inventory_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reserved_quantity", sa.Integer(), nullable=False),
        sa.Column("low_stock_threshold", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(length=150), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_inventory_items_product_id"),
        "inventory_items",
        ["product_id"],
        unique=True,
    )

    op.create_table(
        "carts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "CHECKED_OUT", "ABANDONED", name="cart_status"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_carts_user_id"), "carts", ["user_id"], unique=False)

    op.create_table(
        "cart_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("cart_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["cart_id"], ["carts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cart_items_cart_id"), "cart_items", ["cart_id"], unique=False)
    op.create_index(op.f("ix_cart_items_product_id"), "cart_items", ["product_id"], unique=False)

    op.create_table(
        "orders",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("cart_id", sa.UUID(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("PENDING", "PAID", "PROCESSING", "SHIPPED", "COMPLETED", "CANCELLED", name="order_status"),
            nullable=False,
        ),
        sa.Column("subtotal", sa.Float(), nullable=False),
        sa.Column("shipping_fee", sa.Float(), nullable=False),
        sa.Column("discount", sa.Float(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("payment_reference", sa.String(length=120), nullable=True),
        sa.Column("payment_status", sa.String(length=25), nullable=False),
        sa.Column("shipping_address", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["cart_id"], ["carts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_orders_cart_id"), "orders", ["cart_id"], unique=False)
    op.create_index(op.f("ix_orders_payment_reference"), "orders", ["payment_reference"], unique=False)
    op.create_index(op.f("ix_orders_user_id"), "orders", ["user_id"], unique=False)

    op.create_table(
        "order_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("total_price", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_items_order_id"), "order_items", ["order_id"], unique=False)
    op.create_index(op.f("ix_order_items_product_id"), "order_items", ["product_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_order_items_product_id"), table_name="order_items")
    op.drop_index(op.f("ix_order_items_order_id"), table_name="order_items")
    op.drop_table("order_items")

    op.drop_index(op.f("ix_orders_user_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_payment_reference"), table_name="orders")
    op.drop_index(op.f("ix_orders_cart_id"), table_name="orders")
    op.drop_table("orders")

    op.drop_index(op.f("ix_cart_items_product_id"), table_name="cart_items")
    op.drop_index(op.f("ix_cart_items_cart_id"), table_name="cart_items")
    op.drop_table("cart_items")

    op.drop_index(op.f("ix_carts_user_id"), table_name="carts")
    op.drop_table("carts")

    op.drop_index(op.f("ix_inventory_items_product_id"), table_name="inventory_items")
    op.drop_table("inventory_items")

    op.drop_index(op.f("ix_product_search_indexes_product_id"), table_name="product_search_indexes")
    op.drop_table("product_search_indexes")

    op.drop_index(op.f("ix_products_sku"), table_name="products")
    op.drop_table("products")
