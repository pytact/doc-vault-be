"""Authentication router."""
from fastapi import APIRouter, Depends, status, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.schemas import StandardResponse
from src.auth.schemas import (
    LoginRequest,
    LoginResponse,
    TokenRequest,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    PasswordResetConfirm,
    PasswordResetConfirmResponse,
)
from src.auth.dependencies import AuthApiDep, get_current_user, get_auth_api
from src.auth.documentations.auth_api_doc import AuthApiDocs
from src.auth.exceptions import (
    InvalidCredentials,
    UserNotActivated,
    UserSoftDeleted,
    FamilySoftDeleted,
    ResetTokenInvalid,
    ResetTokenExpired,
)
from src.users.models import User


async def get_token_request(
    username: str = Form(..., description="Username (email address) for OAuth2 compatibility"),
    password: str = Form(..., description="User password"),
) -> TokenRequest:
    """Dependency to convert Form fields to TokenRequest schema."""
    return TokenRequest(username=username, password=password)


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
    data: TokenRequest = Depends(get_token_request),
    api: AuthApiDep = Depends(get_auth_api),
):
    """OAuth2-compatible token endpoint for Swagger UI authorization."""
    try:
        # Service handles all business logic (authentication, error handling)
        result = await api.login(data.username, data.password)  # username is actually email
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


@router.post(
    "/password-reset/request",
    response_model=StandardResponse[PasswordResetRequestResponse],
    status_code=status.HTTP_200_OK,
    summary=AuthApiDocs.password_reset_request["summary"],
    description=AuthApiDocs.password_reset_request["description"],
)
async def request_password_reset(
    data: PasswordResetRequest,
    api: AuthApiDep = Depends(get_auth_api),
) -> StandardResponse[PasswordResetRequestResponse]:
    """Request password reset for a user."""
    result = await api.request_password_reset(data.email)
    return StandardResponse(
        data=result,
        message=result.message,
    )


@router.post(
    "/password-reset/confirm",
    response_model=StandardResponse[PasswordResetConfirmResponse],
    status_code=status.HTTP_200_OK,
    summary=AuthApiDocs.password_reset_confirm["summary"],
    description=AuthApiDocs.password_reset_confirm["description"],
)
async def confirm_password_reset(
    data: PasswordResetConfirm,
    api: AuthApiDep = Depends(get_auth_api),
) -> StandardResponse[PasswordResetConfirmResponse]:
    """Confirm password reset with token and new password."""
    try:
        result = await api.confirm_password_reset(data.reset_token, data.password)
        return StandardResponse(
            data=result,
            message=result.message,
        )
    except (ResetTokenInvalid, ResetTokenExpired) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )
