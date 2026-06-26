from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, field_validator

from app.services.auth import (
    AuthConfigError,
    AuthenticatedUser,
    DuplicateUserError,
    InvalidCredentialsError,
    TokenPair,
    auth_service,
)


bearer_scheme = HTTPBearer(auto_error=False)


class AuthUserResponse(BaseModel):
    id: str
    email: str


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    expires_at: str
    user: AuthUserResponse


class EmailPasswordRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not any(character.isupper() for character in value):
            raise ValueError("Password must contain an uppercase letter.")
        if not any(character.isdigit() for character in value):
            raise ValueError("Password must contain a digit.")
        if not any(not character.isalnum() for character in value):
            raise ValueError("Password must contain a special character.")
        return value


class RefreshTokenRequest(BaseModel):
    refresh_token: str


def token_response(token_pair: TokenPair) -> AuthTokenResponse:
    return AuthTokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type="bearer",
        expires_in=token_pair.expires_in,
        expires_at=token_pair.expires_at.isoformat(),
        user=AuthUserResponse(
            id=token_pair.user.id,
            email=token_pair.user.email,
        ),
    )


def auth_http_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise auth_http_error()
    try:
        return auth_service.user_from_access_token(credentials.credentials)
    except (AuthConfigError, InvalidCredentialsError) as error:
        raise auth_http_error() from error


CurrentUser = Annotated[AuthenticatedUser, Depends(current_user)]


def register_user(request: EmailPasswordRequest) -> AuthTokenResponse:
    try:
        return token_response(auth_service.register(str(request.email), request.password))
    except DuplicateUserError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        ) from error
    except AuthConfigError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication is not configured.",
        ) from error


def login_user(request: EmailPasswordRequest) -> AuthTokenResponse:
    try:
        return token_response(auth_service.login(str(request.email), request.password))
    except InvalidCredentialsError as error:
        raise auth_http_error() from error
    except AuthConfigError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication is not configured.",
        ) from error


def refresh_user_token(request: RefreshTokenRequest) -> AuthTokenResponse:
    try:
        return token_response(auth_service.refresh(request.refresh_token))
    except InvalidCredentialsError as error:
        raise auth_http_error() from error
    except AuthConfigError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication is not configured.",
        ) from error


def logout_user(request: RefreshTokenRequest, user: CurrentUser) -> dict[str, str]:
    auth_service.logout(request.refresh_token)
    return {"status": "ok"}
