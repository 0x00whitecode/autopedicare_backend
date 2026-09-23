"""add fleet and wallet tables

Revision ID: f1b2a3c4d5e6
Revises: 5c974eefac94
Create Date: 2026-09-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f1b2a3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "5c974eefac94"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "fleet_vehicles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("vehicle_type", sa.String(length=80), nullable=False),
        sa.Column("plate_number", sa.String(length=50), nullable=True),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "IN_MAINTENANCE", "OFFLINE", name="fleet_vehicle_status"),
            nullable=False,
        ),
        sa.Column("last_location", sa.String(length=255), nullable=True),
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
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_fleet_vehicles_owner_id"),
        "fleet_vehicles",
        ["owner_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_fleet_vehicles_plate_number"),
        "fleet_vehicles",
        ["plate_number"],
        unique=True,
    )

    op.create_table(
        "wallet_transactions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "provider",
            sa.Enum("PAYSTACK", "FLUTTERWAVE", "WALLET", name="payment_provider"),
            nullable=False,
        ),
        sa.Column("reference", sa.String(length=120), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "SUCCESS", "FAILED", "REVERSED", name="payment_status"),
            nullable=False,
        ),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_wallet_transactions_reference"),
        "wallet_transactions",
        ["reference"],
        unique=True,
    )
    op.create_index(
        op.f("ix_wallet_transactions_user_id"),
        "wallet_transactions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_wallet_transactions_user_id"), table_name="wallet_transactions")
    op.drop_index(op.f("ix_wallet_transactions_reference"), table_name="wallet_transactions")
    op.drop_table("wallet_transactions")

    op.drop_index(op.f("ix_fleet_vehicles_plate_number"), table_name="fleet_vehicles")
    op.drop_index(op.f("ix_fleet_vehicles_owner_id"), table_name="fleet_vehicles")
    op.drop_table("fleet_vehicles")
