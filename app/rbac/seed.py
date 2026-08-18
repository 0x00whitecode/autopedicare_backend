import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.rbac.models import Role, Permission, RolePermission, UserRole
from app.users.models import User
from app.auth.models import UserLoginHistory
from app.onboarding.models import OnboardingRequest


ROLES = {
    "car_owner": "A customer who owns or manages a vehicle.",
    "mechanic": "An approved automotive mechanic.",
    "company": "An approved automotive service or towing company.",
    "admin": "An administrator with assigned administrative permissions.",
    "superadmin": "A system administrator with unrestricted access.",
}


PERMISSIONS = {
    # General user permissions
    "view_own_profile": "View own profile.",
    "update_own_profile": "Update own profile.",

    # Vehicle permissions
    "view_own_vehicles": "View own vehicles.",
    "create_vehicle": "Create a vehicle.",
    "update_own_vehicle": "Update own vehicle.",
    "delete_own_vehicle": "Delete own vehicle.",

    # Mechanic permissions
    "view_service_requests": "View service requests available to the mechanic.",
    "accept_service_request": "Accept a service request.",
    "update_service_request": "Update the status of an assigned service request.",
    "manage_mechanic_profile": "Manage mechanic profile information.",

    # Company permissions
    "manage_company_profile": "Manage company profile information.",
    "view_company_requests": "View company service requests.",
    "manage_company_requests": "Manage company service requests.",

    # Administration
    "view_users": "View users.",
    "manage_users": "Manage users.",
    "review_onboarding": "Review onboarding requests.",
    "assign_roles": "Assign roles to users.",
    "manage_roles": "Create, update, and manage roles.",
    "manage_permissions": "Create, update, and manage permissions.",

    # Administrative areas
    "manage_finance": "Manage financial administration.",
    "manage_marketing": "Manage marketing administration.",
    "manage_regulated_roles": "Manage regulated roles and approvals.",
}


ROLE_PERMISSIONS = {
    "car_owner": [
        "view_own_profile",
        "update_own_profile",
        "view_own_vehicles",
        "create_vehicle",
        "update_own_vehicle",
        "delete_own_vehicle",
    ],

    "mechanic": [
        "view_own_profile",
        "update_own_profile",
        "view_service_requests",
        "accept_service_request",
        "update_service_request",
        "manage_mechanic_profile",
    ],

    "company": [
        "view_own_profile",
        "update_own_profile",
        "manage_company_profile",
        "view_company_requests",
        "manage_company_requests",
    ],

    "admin": [
        "view_own_profile",
        "update_own_profile",
        "view_users",
        "manage_users",
        "review_onboarding",
        "assign_roles",
        "manage_roles",
        "manage_permissions",
        "manage_finance",
        "manage_marketing",
        "manage_regulated_roles",
    ],

    "superadmin": [],
}


async def seed_rbac() -> None:
    async with AsyncSessionLocal() as session:

        roles = {}

        for role_name, description in ROLES.items():

            result = await session.execute(
                select(Role).where(Role.name == role_name)
            )

            role = result.scalar_one_or_none()

            if role is None:
                role = Role(
                    name=role_name,
                    description=description,
                    is_system_role=True,
                )

                session.add(role)

                print(f"Created role: {role_name}")

            else:
                print(f"Role already exists: {role_name}")

            roles[role_name] = role

        await session.flush()

        permissions = {}

        for permission_name, description in PERMISSIONS.items():

            result = await session.execute(
                select(Permission).where(
                    Permission.name == permission_name
                )
            )

            permission = result.scalar_one_or_none()

            if permission is None:
                permission = Permission(
                    name=permission_name,
                    description=description,
                )

                session.add(permission)

                print(f"Created permission: {permission_name}")

            else:
                print(f"Permission already exists: {permission_name}")

            permissions[permission_name] = permission

        await session.flush()

        for role_name, permission_names in ROLE_PERMISSIONS.items():

            role = roles[role_name]

            for permission_name in permission_names:

                permission = permissions[permission_name]

                result = await session.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == permission.id,
                    )
                )

                existing = result.scalar_one_or_none()

                if existing is None:
                    session.add(
                        RolePermission(
                            role_id=role.id,
                            permission_id=permission.id,
                        )
                    )

                    print(
                        f"Assigned permission "
                        f"'{permission_name}' "
                        f"to role '{role_name}'"
                    )

                else:
                    print(
                        f"Permission '{permission_name}' "
                        f"already assigned to '{role_name}'"
                    )

        await session.commit()

        print()
        print("========================================")
        print("RBAC seed completed successfully.")
        print("========================================")

if __name__ == "__main__":
    asyncio.run(seed_rbac())