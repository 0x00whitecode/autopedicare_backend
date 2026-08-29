from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.onboarding.models import (
    OnboardingRequest,
    OnboardingStatus,
    RequestedAccountType,
)


async def get_onboarding_request(
    session: AsyncSession,
    user_id,
) -> OnboardingRequest | None:

    result = await session.execute(
        select(OnboardingRequest).where(
            OnboardingRequest.user_id == user_id
        )
    )

    return result.scalar_one_or_none()


async def create_onboarding_request(
    session: AsyncSession,
    user_id,
    requested_type: RequestedAccountType,
) -> OnboardingRequest:

    onboarding_request = OnboardingRequest(
        user_id=user_id,
        requested_type=requested_type,
        status=OnboardingStatus.PENDING,
    )

    session.add(onboarding_request)

    await session.flush()

    return onboarding_request


async def get_or_create_onboarding_request(
    session: AsyncSession,
    user_id,
    requested_type: RequestedAccountType,
) -> OnboardingRequest:

    onboarding_request = await get_onboarding_request(
        session=session,
        user_id=user_id,
    )

    if onboarding_request is not None:
        return onboarding_request

    return await create_onboarding_request(
        session=session,
        user_id=user_id,
        requested_type=requested_type,
    )