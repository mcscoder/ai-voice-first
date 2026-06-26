from __future__ import annotations

import hashlib
import secrets
import sqlite3
import threading
from datetime import datetime, timezone
from uuid import uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jwt import InvalidTokenError

from app.core.config import AuthConfig, config
from app.services.auth.types import (
    AuthConfigError,
    AuthenticatedUser,
    DuplicateUserError,
    InvalidCredentialsError,
    TokenPair,
)


class AuthService:
    def __init__(self, auth_config: AuthConfig = config.auth) -> None:
        self.auth_config = auth_config
        self._password_hasher = PasswordHasher()
        self._lock = threading.RLock()
        self._initialized = False

    def register(self, email: str, password: str) -> TokenPair:
        self._secret_key()
        normalized_email = self._normalize_email(email)
        self._validate_password(password)
        user_id = uuid4().hex
        password_hash = self._password_hasher.hash(password)

        with self._connect() as db:
            try:
                db.execute(
                    """
                    INSERT INTO users (id, email, password_hash, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, normalized_email, password_hash, self._now_iso()),
                )
            except sqlite3.IntegrityError as error:
                raise DuplicateUserError("Email is already registered.") from error

        return self._issue_token_pair(AuthenticatedUser(user_id, normalized_email))

    def login(self, email: str, password: str) -> TokenPair:
        normalized_email = self._normalize_email(email)
        with self._connect() as db:
            row = db.execute(
                "SELECT id, email, password_hash FROM users WHERE email = ?",
                (normalized_email,),
            ).fetchone()

        if row is None:
            raise InvalidCredentialsError("Invalid email or password.")

        try:
            verified = self._password_hasher.verify(row["password_hash"], password)
        except VerifyMismatchError as error:
            raise InvalidCredentialsError("Invalid email or password.") from error

        if not verified:
            raise InvalidCredentialsError("Invalid email or password.")

        return self._issue_token_pair(AuthenticatedUser(row["id"], row["email"]))

    def refresh(self, refresh_token: str) -> TokenPair:
        token_hash = self._hash_refresh_token(refresh_token)
        now = self._now_iso()
        with self._connect() as db:
            row = db.execute(
                """
                SELECT users.id, users.email
                FROM refresh_tokens
                JOIN users ON users.id = refresh_tokens.user_id
                WHERE refresh_tokens.token_hash = ?
                  AND refresh_tokens.revoked_at IS NULL
                  AND refresh_tokens.expires_at > ?
                """,
                (token_hash, now),
            ).fetchone()
            if row is None:
                raise InvalidCredentialsError("Invalid refresh token.")
            db.execute(
                "UPDATE refresh_tokens SET revoked_at = ? WHERE token_hash = ?",
                (now, token_hash),
            )

        return self._issue_token_pair(AuthenticatedUser(row["id"], row["email"]))

    def logout(self, refresh_token: str) -> None:
        token_hash = self._hash_refresh_token(refresh_token)
        with self._connect() as db:
            db.execute(
                """
                UPDATE refresh_tokens
                SET revoked_at = ?
                WHERE token_hash = ? AND revoked_at IS NULL
                """,
                (self._now_iso(), token_hash),
            )

    def user_from_access_token(self, access_token: str) -> AuthenticatedUser:
        secret_key = self._secret_key()
        try:
            payload = jwt.decode(
                access_token,
                secret_key,
                algorithms=[self.auth_config.algorithm],
            )
        except InvalidTokenError as error:
            raise InvalidCredentialsError("Invalid access token.") from error

        user_id = payload.get("sub")
        email = payload.get("email")
        token_type = payload.get("type")
        if not isinstance(user_id, str) or not isinstance(email, str):
            raise InvalidCredentialsError("Invalid access token.")
        if token_type != "access":
            raise InvalidCredentialsError("Invalid access token.")

        with self._connect() as db:
            row = db.execute(
                "SELECT id, email FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        if row is None:
            raise InvalidCredentialsError("Invalid access token.")
        return AuthenticatedUser(row["id"], row["email"])

    def _issue_token_pair(self, user: AuthenticatedUser) -> TokenPair:
        expires_at = datetime.now(timezone.utc) + self.auth_config.access_token_ttl
        access_token = jwt.encode(
            {
                "sub": user.id,
                "email": user.email,
                "type": "access",
                "exp": expires_at,
            },
            self._secret_key(),
            algorithm=self.auth_config.algorithm,
        )
        refresh_token = secrets.token_urlsafe(48)
        refresh_expires_at = (
            datetime.now(timezone.utc) + self.auth_config.refresh_token_ttl
        )
        with self._connect() as db:
            db.execute(
                """
                INSERT INTO refresh_tokens (
                    token_hash, user_id, expires_at, created_at, revoked_at
                )
                VALUES (?, ?, ?, ?, NULL)
                """,
                (
                    self._hash_refresh_token(refresh_token),
                    user.id,
                    refresh_expires_at.isoformat(),
                    self._now_iso(),
                ),
            )
        return TokenPair(access_token, refresh_token, expires_at, user)

    def _connect(self) -> sqlite3.Connection:
        self._ensure_initialized()
        db = sqlite3.connect(self.auth_config.db_path)
        db.row_factory = sqlite3.Row
        return db

    def _ensure_initialized(self) -> None:
        with self._lock:
            if self._initialized:
                return
            self.auth_config.db_path.parent.mkdir(parents=True, exist_ok=True)
            db = sqlite3.connect(self.auth_config.db_path)
            try:
                db.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        email TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                db.execute(
                    """
                    CREATE TABLE IF NOT EXISTS refresh_tokens (
                        token_hash TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        revoked_at TEXT,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                    """
                )
                db.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id
                    ON refresh_tokens (user_id)
                    """
                )
                db.commit()
            finally:
                db.close()
            self._initialized = True

    def _secret_key(self) -> str:
        if not self.auth_config.secret_key:
            raise AuthConfigError("AUTH_SECRET_KEY is required.")
        return self.auth_config.secret_key

    def _normalize_email(self, email: str) -> str:
        normalized = email.strip().lower()
        if not normalized:
            raise InvalidCredentialsError("Email is required.")
        return normalized

    def _validate_password(self, password: str) -> None:
        if len(password) < 8:
            raise InvalidCredentialsError("Password is too short.")
        if not any(character.isupper() for character in password):
            raise InvalidCredentialsError("Password must contain an uppercase letter.")
        if not any(character.isdigit() for character in password):
            raise InvalidCredentialsError("Password must contain a digit.")
        if not any(not character.isalnum() for character in password):
            raise InvalidCredentialsError("Password must contain a special character.")

    def _hash_refresh_token(self, refresh_token: str) -> str:
        return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()


auth_service = AuthService()
