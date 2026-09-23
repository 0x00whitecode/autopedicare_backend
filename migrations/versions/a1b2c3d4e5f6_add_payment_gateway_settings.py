"""add payment gateway settings

Revision ID: a1b2c3d4e5f6
Revises: f1b2a3c4d5e6
Create Date: 2026-09-23 00:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f1b2a3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "payment_gateway_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "provider",
            sa.Enum("PAYSTACK", "FLUTTERWAVE", "WALLET", name="payment_provider"),
            nullable=False,
        ),
        sa.Column("public_key", sa.String(length=255), nullable=False),
        sa.Column("secret_key", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
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
    op.create_index(
        op.f("ix_payment_gateway_settings_provider"),
        "payment_gateway_settings",
        ["provider"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_payment_gateway_settings_provider"), table_name="payment_gateway_settings")
    op.drop_table("payment_gateway_settings")
