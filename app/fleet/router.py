import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.fleet.schemas import FleetVehicleCreate, FleetVehicleResponse, FleetVehicleUpdate
from app.fleet.services import (
    create_fleet_vehicle as svc_create,
    delete_fleet_vehicle as svc_delete,
    get_fleet_vehicle_by_id as svc_get_by_id,
    list_fleet_vehicles_for_owner as svc_list,
    update_fleet_vehicle as svc_update,
)
from app.users.models import User

router = APIRouter(prefix="/fleet", tags=["Fleet"])


@router.post("/vehicles", response_model=FleetVehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    data: FleetVehicleCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    vehicle = await svc_create(db, user.id, data)
    await db.commit()
    return vehicle


@router.get("/vehicles", response_model=list[FleetVehicleResponse])
async def list_vehicles(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    vehicles, _ = await svc_list(db, user.id, offset=offset, limit=limit)
    return vehicles


@router.get("/vehicles/{vehicle_id}", response_model=FleetVehicleResponse)
async def get_vehicle(
    vehicle_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    vehicle = await svc_get_by_id(db, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fleet vehicle not found.")
    if vehicle.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this fleet vehicle.")
    return vehicle


@router.patch("/vehicles/{vehicle_id}", response_model=FleetVehicleResponse)
async def update_vehicle(
    vehicle_id: uuid.UUID,
    data: FleetVehicleUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    vehicle = await svc_get_by_id(db, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fleet vehicle not found.")
    if vehicle.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own fleet vehicles.")
    updated = await svc_update(db, vehicle, data)
    await db.commit()
    return updated


@router.delete("/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    vehicle = await svc_get_by_id(db, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fleet vehicle not found.")
    if vehicle.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own fleet vehicles.")
    await svc_delete(db, vehicle)
    await db.commit()
