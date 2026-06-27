from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


class AuthError(Exception):
    """Base class for authentication failures."""


class AuthConfigError(AuthError):
    """Raised when authentication is not configured."""


class DuplicateUserError(AuthError):
    """Raised when registering an email that already exists."""


class InvalidCredentialsError(AuthError):
    """Raised when credentials or tokens are invalid."""


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    email: str


@dataclass(frozen=True)
class PersonalizationSettings:
    nickname: str
    speaking_style: str
    setup_completed: bool


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_at: datetime
    user: AuthenticatedUser

    @property
    def expires_in(self) -> int:
        now = datetime.now(self.expires_at.tzinfo)
        return max(0, int((self.expires_at - now).total_seconds()))
