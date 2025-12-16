"""Authentication router."""
from fastapi import APIRouter, Depends, status, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.schemas import StandardResponse
from src.auth.schemas import LoginRequest, LoginResponse
from src.auth.dependencies import AuthApiDep, get_current_user, get_auth_api
from src.auth.documentations.auth_api_doc import AuthApiDocs
from src.auth.exceptions import (
    InvalidCredentials,
    UserNotActivated,
    UserSoftDeleted,
    FamilySoftDeleted,
)
from src.users.models import User


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=StandardResponse[LoginResponse],
    status_code=status.HTTP_200_OK,
    summary=AuthApiDocs.login["summary"],
    description=AuthApiDocs.login["description"],
)
async def login(
    data: LoginRequest,
    api: AuthApiDep = Depends(get_auth_api),
) -> StandardResponse[LoginResponse]:
    """Authenticate user and return JWT token."""
    result = await api.login(data.email, data.password)
    return StandardResponse(
        data=result,
        message="Login successful",
    )


@router.post(
    "/logout",
    response_model=StandardResponse[dict],
    status_code=status.HTTP_200_OK,
    summary=AuthApiDocs.logout["summary"],
    description=AuthApiDocs.logout["description"],
)
async def logout(
    current_user: User = Depends(get_current_user),
    api: AuthApiDep = Depends(get_auth_api),
) -> StandardResponse[dict]:
    """Logout user."""
    await api.logout()
    return StandardResponse(
        data={},
        message="Logout successful",
    )


@router.post(
    "/token",
    status_code=status.HTTP_200_OK,
    summary=AuthApiDocs.token["summary"],
    description=AuthApiDocs.token["description"],
)
async def token(
    username: str = Form(...),  # OAuth2 uses 'username' but we treat it as email
    password: str = Form(...),
    api: AuthApiDep = Depends(get_auth_api),
):
    """OAuth2-compatible token endpoint for Swagger UI authorization."""
    try:
        # Service handles all business logic (authentication, error handling)
        result = await api.login(username, password)  # username is actually email
        # Router only formats response (no business logic)
        return {
            "access_token": result.token,
            "token_type": "bearer",
        }
    except (InvalidCredentials, UserNotActivated, UserSoftDeleted, FamilySoftDeleted):
        # OAuth2-compatible error response
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
