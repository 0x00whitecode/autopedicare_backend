from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FleetVehicleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    vehicle_type: str = Field(min_length=1, max_length=80)
    plate_number: str | None = Field(default=None, max_length=50)
    last_location: str | None = Field(default=None, max_length=255)


class FleetVehicleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    vehicle_type: str | None = Field(default=None, min_length=1, max_length=80)
    plate_number: str | None = Field(default=None, max_length=50)
    last_location: str | None = Field(default=None, max_length=255)


class FleetVehicleResponse(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    vehicle_type: str
    plate_number: str | None
    status: str
    last_location: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
