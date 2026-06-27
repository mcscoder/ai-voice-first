import sqlite3

from app.core.config import AuthConfig
from app.services.auth import (
    AuthConfigError,
    AuthService,
    DuplicateUserError,
    InvalidCredentialsError,
)


def create_service(tmp_path) -> AuthService:
    return AuthService(
        AuthConfig(
            secret_key="test-secret-key-with-at-least-32-bytes",
            db_path=tmp_path / "auth.sqlite3",
        )
    )


def test_register_creates_user_and_token_pair(tmp_path) -> None:
    service = create_service(tmp_path)

    token_pair = service.register("Test@Example.com", "Password1!")

    assert token_pair.access_token
    assert token_pair.refresh_token
    assert token_pair.user.email == "test@example.com"
    assert service.user_from_access_token(token_pair.access_token) == token_pair.user


def test_register_rejects_duplicate_email(tmp_path) -> None:
    service = create_service(tmp_path)
    service.register("test@example.com", "Password1!")

    try:
        service.register("TEST@example.com", "Password1!")
    except DuplicateUserError:
        return

    raise AssertionError("Expected duplicate email to be rejected.")


def test_register_without_secret_does_not_create_user(tmp_path) -> None:
    broken_service = AuthService(
        AuthConfig(secret_key=None, db_path=tmp_path / "auth.sqlite3")
    )

    try:
        broken_service.register("test@example.com", "Password1!")
    except AuthConfigError:
        pass
    else:
        raise AssertionError("Expected missing auth secret to fail.")

    working_service = create_service(tmp_path)
    token_pair = working_service.register("test@example.com", "Password1!")

    assert token_pair.user.email == "test@example.com"


def test_login_rejects_wrong_password(tmp_path) -> None:
    service = create_service(tmp_path)
    service.register("test@example.com", "Password1!")

    try:
        service.login("test@example.com", "Wrongpass1!")
    except InvalidCredentialsError:
        return

    raise AssertionError("Expected invalid credentials.")


def test_refresh_rotates_refresh_token(tmp_path) -> None:
    service = create_service(tmp_path)
    first = service.register("test@example.com", "Password1!")

    second = service.refresh(first.refresh_token)

    assert second.refresh_token != first.refresh_token
    assert second.user == first.user
    try:
        service.refresh(first.refresh_token)
    except InvalidCredentialsError:
        return

    raise AssertionError("Expected rotated refresh token to be invalid.")


def test_logout_revokes_refresh_token(tmp_path) -> None:
    service = create_service(tmp_path)
    token_pair = service.register("test@example.com", "Password1!")

    service.logout(token_pair.refresh_token)

    try:
        service.refresh(token_pair.refresh_token)
    except InvalidCredentialsError:
        return

    raise AssertionError("Expected logged-out refresh token to be invalid.")


def test_memory_preference_defaults_to_enabled_without_row(tmp_path) -> None:
    service = create_service(tmp_path)
    token_pair = service.register("test@example.com", "Password1!")

    assert service.is_memory_enabled(token_pair.user.id) is True


def test_memory_preference_persists_updates(tmp_path) -> None:
    service = create_service(tmp_path)
    token_pair = service.register("test@example.com", "Password1!")

    assert service.set_memory_enabled(token_pair.user.id, False) is False
    assert service.is_memory_enabled(token_pair.user.id) is False
    assert service.set_memory_enabled(token_pair.user.id, True) is True
    assert service.is_memory_enabled(token_pair.user.id) is True


def test_voice_preference_defaults_persists_and_migrates(tmp_path) -> None:
    db_path = tmp_path / "auth.sqlite3"
    with sqlite3.connect(db_path) as db:
        db.execute(
            """
            CREATE TABLE user_preferences (
                user_id TEXT PRIMARY KEY,
                memory_enabled INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        db.commit()

    service = AuthService(
        AuthConfig(
            secret_key="test-secret-key-with-at-least-32-bytes",
            db_path=db_path,
        )
    )
    token_pair = service.register("test@example.com", "Password1!")

    assert service.get_voice(token_pair.user.id) == "Mỹ Duyên"
    assert service.set_voice(token_pair.user.id, "Ngọc Linh") == "Ngọc Linh"
    assert service.get_voice(token_pair.user.id) == "Ngọc Linh"

    with sqlite3.connect(db_path) as db:
        columns = {
            row[1] for row in db.execute("PRAGMA table_info(user_preferences)")
        }
        row = db.execute(
            "SELECT voice FROM user_preferences WHERE user_id = ?",
            (token_pair.user.id,),
        ).fetchone()

    assert "voice" in columns
    assert row == ("Ngọc Linh",)
