import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.fleet.models import FleetVehicle
from app.fleet.schemas import FleetVehicleCreate, FleetVehicleUpdate


async def create_fleet_vehicle(
    db: AsyncSession,
    owner_id: uuid.UUID,
    data: FleetVehicleCreate,
) -> FleetVehicle:
    vehicle = FleetVehicle(
        owner_id=owner_id,
        name=data.name,
        vehicle_type=data.vehicle_type,
        plate_number=data.plate_number,
        last_location=data.last_location,
    )
    db.add(vehicle)
    await db.flush()
    await db.refresh(vehicle)
    return vehicle


async def get_fleet_vehicle_by_id(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
) -> FleetVehicle | None:
    result = await db.execute(select(FleetVehicle).where(FleetVehicle.id == vehicle_id))
    return result.scalar_one_or_none()


async def list_fleet_vehicles_for_owner(
    db: AsyncSession,
    owner_id: uuid.UUID,
    *,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[FleetVehicle], int]:
    query = select(FleetVehicle).where(FleetVehicle.owner_id == owner_id)
    total = (await db.execute(select(__import__('sqlalchemy').func.count()).select_from(query.subquery()))).scalar() or 0
    query = query.order_by(FleetVehicle.created_at.desc()).offset(offset).limit(limit)
    vehicles = list((await db.execute(query)).scalars().all())
    return vehicles, int(total)


async def update_fleet_vehicle(
    db: AsyncSession,
    vehicle: FleetVehicle,
    data: FleetVehicleUpdate,
) -> FleetVehicle:
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(vehicle, key, value)
    await db.flush()
    await db.refresh(vehicle)
    return vehicle


async def delete_fleet_vehicle(
    db: AsyncSession,
    vehicle: FleetVehicle,
) -> None:
    await db.delete(vehicle)
    await db.flush()
