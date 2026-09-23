from datetime import datetime
from uuid import UUID

from enum import Enum as PyEnum

from pydantic import BaseModel, Field

from app.onboarding.models import OnboardingStatus, RequestedAccountType


class OnboardingDecision(str, PyEnum):
    APPROVE = "approve"
    REJECT = "reject"


class ReviewOnboardingRequest(BaseModel):
    decision: OnboardingDecision
    reason: str | None = Field(default=None, max_length=500)


class OnboardingSummaryResponse(BaseModel):
    id: UUID
    user_id: UUID
    requested_type: RequestedAccountType
    status: OnboardingStatus
    assigned_role_id: UUID | None
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class OnboardingReviewResponse(BaseModel):
    id: UUID
    user_id: UUID
    requested_type: RequestedAccountType
    status: OnboardingStatus
    assigned_role_id: UUID | None
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    rejection_reason: str | None

    model_config = {"from_attributes": True}
