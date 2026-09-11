import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.users.models import User
from app.vehicles.schemas import VehicleCreate, VehicleResponse, VehicleUpdate
from app.vehicles.services import (
    create_vehicle as svc_create,
    delete_vehicle as svc_delete,
    get_vehicle_by_id as svc_get_by_id,
    list_vehicles_for_owner as svc_list,
    update_vehicle as svc_update,
)

router = APIRouter(
    prefix="/vehicles",
    tags=["Vehicles"],
)


@router.post(
    "",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_vehicle(
    data: VehicleCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    vehicle = await svc_create(db, user.id, data)
    await db.commit()
    return vehicle


@router.get("", response_model=list[VehicleResponse])
async def list_my_vehicles(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    vehicles, _ = await svc_list(db, user.id, offset=offset, limit=limit)
    return vehicles


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    vehicle = await svc_get_by_id(db, vehicle_id)
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found.",
        )
    if vehicle.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this vehicle.",
        )
    return vehicle


@router.patch("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: uuid.UUID,
    data: VehicleUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    vehicle = await svc_get_by_id(db, vehicle_id)
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found.",
        )
    if vehicle.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own vehicles.",
        )
    updated = await svc_update(db, vehicle, data)
    await db.commit()
    return updated


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    vehicle = await svc_get_by_id(db, vehicle_id)
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found.",
        )
    if vehicle.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own vehicles.",
        )
    await svc_delete(db, vehicle)
    await db.commit()
