"""Main API router."""
from fastapi import APIRouter
from src.auth.router import router as auth_router
from src.families.router import router as families_router
from src.users.router import router as users_router
from src.users.invitations_router import invite_router, invitations_router
from src.users.profile_router import router as profile_router
from src.roles.router import router as roles_router

api_router = APIRouter()

# Include domain module routers
api_router.include_router(auth_router)
api_router.include_router(families_router)
api_router.include_router(users_router)
api_router.include_router(invite_router)
api_router.include_router(invitations_router)
api_router.include_router(profile_router)
api_router.include_router(roles_router)

