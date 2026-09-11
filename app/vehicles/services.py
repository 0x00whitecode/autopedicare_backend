import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.vehicles.models import Vehicle
from app.vehicles.schemas import VehicleCreate, VehicleUpdate


async def create_vehicle(
    db: AsyncSession,
    owner_id: uuid.UUID,
    data: VehicleCreate,
) -> Vehicle:
    vehicle = Vehicle(
        owner_id=owner_id,
        make=data.make,
        model=data.model,
        year=data.year,
        vin=data.vin,
        license_plate=data.license_plate,
        color=data.color,
    )
    db.add(vehicle)
    await db.flush()
    await db.refresh(vehicle)
    return vehicle


async def get_vehicle_by_id(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
) -> Vehicle | None:
    result = await db.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id)
    )
    return result.scalar_one_or_none()


async def list_vehicles_for_owner(
    db: AsyncSession,
    owner_id: uuid.UUID,
    *,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Vehicle], int]:
    query = select(Vehicle).where(Vehicle.owner_id == owner_id)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(Vehicle.created_at.desc()).offset(offset).limit(limit)
    vehicles = list((await db.execute(query)).scalars().all())
    return vehicles, total


async def update_vehicle(
    db: AsyncSession,
    vehicle: Vehicle,
    data: VehicleUpdate,
) -> Vehicle:
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(vehicle, key, value)
    await db.flush()
    await db.refresh(vehicle)
    return vehicle


async def delete_vehicle(
    db: AsyncSession,
    vehicle: Vehicle,
) -> None:
    await db.delete(vehicle)
    await db.flush()
