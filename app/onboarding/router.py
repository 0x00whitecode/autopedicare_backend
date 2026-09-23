from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_permission
from app.onboarding.models import OnboardingRequest, OnboardingStatus, RequestedAccountType
from app.onboarding.schemas import (
    OnboardingDecision,
    OnboardingReviewResponse,
    OnboardingSummaryResponse,
    ReviewOnboardingRequest,
)
from app.rbac.models import Role
from app.rbac.service import assign_role_to_user
from app.users.models import User

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.get(
    "/requests",
    response_model=list[OnboardingSummaryResponse],
    dependencies=[Depends(require_permission("review_onboarding"))],
)
async def list_onboarding_requests(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    del user
    result = await db.execute(
        select(OnboardingRequest)
        .order_by(OnboardingRequest.created_at.desc())
    )
    requests = result.scalars().all()
    return [
        OnboardingSummaryResponse(
            id=item.id,
            user_id=item.user_id,
            requested_type=item.requested_type,
            status=item.status,
            assigned_role_id=item.assigned_role_id,
            reviewed_by=item.reviewed_by,
            reviewed_at=item.reviewed_at,
            created_at=item.created_at,
        )
        for item in requests
    ]


@router.patch(
    "/requests/{request_id}",
    response_model=OnboardingReviewResponse,
    dependencies=[Depends(require_permission("review_onboarding"))],
)
async def review_onboarding_request(
    request_id: str,
    payload: ReviewOnboardingRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(OnboardingRequest).where(OnboardingRequest.id == request_id))
    onboarding = result.scalar_one_or_none()

    if onboarding is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onboarding request not found.",
        )

    if payload.decision == OnboardingDecision.APPROVE:
        onboarding.status = OnboardingStatus.APPROVED
        onboarding.reviewed_by = user.id
        onboarding.reviewed_at = datetime.now(timezone.utc)
        onboarding.rejection_reason = None

        target_role_name = (
            "car_owner"
            if onboarding.requested_type == RequestedAccountType.CAR_OWNER
            else "company"
        )

        role_result = await db.execute(select(Role).where(Role.name == target_role_name))
        role = role_result.scalar_one_or_none()

        if role is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{target_role_name}' is not configured.",
            )

        await assign_role_to_user(
            db=db,
            user_id=onboarding.user_id,
            role_id=role.id,
            assigned_by=user.id,
        )
        onboarding.assigned_role_id = role.id
    else:
        onboarding.status = OnboardingStatus.REJECTED
        onboarding.reviewed_by = user.id
        onboarding.reviewed_at = datetime.now(timezone.utc)
        onboarding.rejection_reason = payload.reason or "No reason provided."

    await db.commit()
    await db.refresh(onboarding)

    return OnboardingReviewResponse(
        id=onboarding.id,
        user_id=onboarding.user_id,
        requested_type=onboarding.requested_type,
        status=onboarding.status,
        assigned_role_id=onboarding.assigned_role_id,
        reviewed_by=onboarding.reviewed_by,
        reviewed_at=onboarding.reviewed_at,
        rejection_reason=onboarding.rejection_reason,
    )
