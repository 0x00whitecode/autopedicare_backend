import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.users.models import User

from enum import Enum as PyEnum


class FleetVehicleStatus(str, PyEnum):
    ACTIVE = "active"
    IN_MAINTENANCE = "in_maintenance"
    OFFLINE = "offline"


class FleetVehicle(Base):
    __tablename__ = "fleet_vehicles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(80), nullable=False)
    plate_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        unique=True,
        index=True,
    )
    status: Mapped[FleetVehicleStatus] = mapped_column(
        Enum(FleetVehicleStatus, name="fleet_vehicle_status"),
        nullable=False,
        default=FleetVehicleStatus.ACTIVE,
    )
    last_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
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

    owner: Mapped["User"] = relationship(
        "User",
        back_populates="fleet_vehicles",
    )
