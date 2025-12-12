"""Seed script to insert roles into the roles table."""
import asyncio
import sys
import traceback
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, func
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.config import settings
from src.roles.models import Role

# Ensure models are registered so relationships resolve
import src.users.models  # noqa: F401


async def check_tables_exist(session: AsyncSession) -> bool:
    """Check if database tables exist."""
    try:
        await session.execute(select(func.count()).select_from(Role))
        return True
    except ProgrammingError as e:
        error_str = str(e).lower()
        if "does not exist" in error_str or "relation" in error_str:
            return False
        raise


# Role definitions with permissions
ROLES_DATA = [
    {
        "name": "superadmin",
        "permissions": {
            "family:manage_all": True,
            "family:create": True,
            "family:update": True,
            "family:delete": True,
            "family:view_all": True,
            "user:manage_all": True,
            "user:create": True,
            "user:update": True,
            "user:delete": True,
            "user:view_all": True,
            "user:assign_roles": True,
            "user:reassign_roles": True,
            "user:assign_family": True,
            "user:reassign_family": True,
            "document:access": False,
        },
    },
    {
        "name": "familyadmin",
        "permissions": {
            "family:view": True,
            "family:update": True,
            "user:manage_family": True,
            "user:create": True,
            "user:update": True,
            "user:delete": True,
            "user:view_family": True,
            "user:assign_roles": True,
            "user:reassign_roles": True,
            "user:add_familyadmin": True,
            "user:add_member": True,
            "user:add_editor": True,
            "user:add_viewer": True,
            "document:create": True,
            "document:view_all": True,
            "document:edit_all": True,
            "document:delete_all": True,
            "document:assign_viewer": True,
            "document:assign_editor": True,
        },
    },
    {
        "name": "member",
        "permissions": {
            "document:create": True,
            "document:view_own": True,
            "document:edit_own": True,
            "document:delete_own": True,
            "document:assign_viewer": True,
            "document:assign_editor": True,
        },
    },
]


async def seed_roles() -> None:
    """Seed roles into the database."""
    print("=" * 60)
    print("Roles Seeding Script")
    print("=" * 60)
    print(f"\nDatabase URL: {settings.database_url.split('@')[0]}@***")  # Hide password
    print(f"Environment: {settings.environment}")

    # Create async engine using project settings
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600,
    )

    # Create async session maker
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        async with async_session() as session:
            # Check if tables exist
            print("\nChecking if database tables exist...")
            if not await check_tables_exist(session):
                print("⚠️  Database tables don't exist yet. Please run migrations first:")
                print("   alembic upgrade head")
                print("\n   Then run this script again:")
                print("   docker compose exec api python scripts/seed_role.py")
                print("\n   Or locally:")
                print("   python scripts/seed_role.py")
                return

            print("\nCreating/updating roles...")
            created_roles = []

            for role_data in ROLES_DATA:
                try:
                    # Check if role already exists
                    result = await session.execute(
                        select(Role).where(
                            Role.name == role_data["name"], Role.is_del == False
                        )
                    )
                    existing_role = result.scalar_one_or_none()

                    if existing_role:
                        # Update existing role if permissions changed
                        updated = False
                        if existing_role.permissions != role_data["permissions"]:
                            existing_role.permissions = role_data["permissions"]
                            updated = True

                        if updated:
                            await session.flush()
                            print(f"  ✅ Updated role: {role_data['name']}")
                        else:
                            print(f"  ✅ Role already exists: {role_data['name']}")
                        created_roles.append(existing_role)
                    else:
                        # Create new role
                        # Explicitly set audit fields to None for seeding (no users exist yet)
                        new_role = Role(
                            name=role_data["name"],
                            permissions=role_data["permissions"],
                            created_by=None,
                            updated_by=None,
                        )
                        session.add(new_role)
                        await session.flush()
                        print(f"  ✅ Created role: {role_data['name']}")
                        created_roles.append(new_role)

                except Exception as e:
                    await session.rollback()
                    print(f"  ❌ Error creating role {role_data['name']}: {e}")
                    raise

            # Commit all changes
            await session.commit()

            print("\n" + "=" * 60)
            print("✅ Roles created/updated successfully!")
            print("=" * 60)
            print(f"\nCreated/Updated Roles:")
            for role in created_roles:
                print(f"  - {role.name} (id: {role.id})")
            print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n❌ Error seeding roles: {e}")
        print(f"Error type: {type(e).__name__}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


async def main() -> None:
    """Main function to run the seeding script."""
    await seed_roles()


if __name__ == "__main__":
    asyncio.run(main())

