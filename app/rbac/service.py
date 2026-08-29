from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.rbac.models import Role, UserRole


async def get_role_by_name(session: AsyncSession, role_name: str) -> Role | None:
    result = await session.execute(select(Role).where(Role.name == role_name))
    return result.scalar_one_or_none()


async def assign_role_to_user(
    db: AsyncSession,
    user_id,
    role_id,
    assigned_by=None,
) -> UserRole:

    user_role = UserRole(
        user_id=user_id,
        role_id=role_id,
        assigned_by=assigned_by,
    )

    db.add(user_role)

    await db.flush()

    return user_role
