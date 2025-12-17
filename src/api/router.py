"""Main API router."""
from fastapi import APIRouter
from src.auth.router import router as auth_router
from src.families.router import router as families_router
from src.users.router import router as users_router
from src.users.invitations_router import invite_router, invitations_router
from src.users.profile_router import router as profile_router
from src.roles.router import router as roles_router
from src.taxonomy.router import router as taxonomy_router
from src.documents.router import router as documents_router
from src.notification.router import router as notification_router

api_router = APIRouter()

# Include domain module routers
api_router.include_router(auth_router)
api_router.include_router(families_router)
api_router.include_router(users_router)
api_router.include_router(invite_router)
api_router.include_router(invitations_router)
api_router.include_router(profile_router)
api_router.include_router(roles_router)
api_router.include_router(taxonomy_router)
api_router.include_router(documents_router)
api_router.include_router(notification_router)

