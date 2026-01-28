import uuid

from sqlalchemy import text

from app.auth import hash_password


def _normalize_user_ids(test_db) -> None:
    new_user_id = str(uuid.uuid4())
    new_role_id = str(uuid.uuid4())
    test_db.execute(
        text("UPDATE users SET id = :new_id WHERE id = :old_id"),
        {"new_id": new_user_id, "old_id": "12345678-1234-5678-1234-567812345678"},
    )
    test_db.execute(
        text("UPDATE roles SET id = :new_id WHERE id = :old_id"),
        {"new_id": new_role_id, "old_id": "87654321-4321-8765-4321-876543210987"},
    )
    test_db.execute(
        text(
            """
            UPDATE user_roles
            SET user_id = :new_user_id, role_id = :new_role_id
            WHERE user_id = :old_user_id AND role_id = :old_role_id
            """
        ),
        {
            "new_user_id": new_user_id,
            "new_role_id": new_role_id,
            "old_user_id": "12345678-1234-5678-1234-567812345678",
            "old_role_id": "87654321-4321-8765-4321-876543210987",
        },
    )
    test_db.commit()
    test_db.expire_all()


def _set_password(test_db, email: str, password: str) -> None:
    password_hash = hash_password(password)
    test_db.execute(
        text("UPDATE users SET password_hash = :hash WHERE email = :email"),
        {"hash": password_hash, "email": email},
    )
    test_db.commit()


def test_login_valid_returns_token_and_user_info(client, test_db, test_user):
    _set_password(test_db, test_user.email, "testpass123")

    response = client.post(
        "/auth/login",
        json={"email": test_user.email, "password": "testpass123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == test_user.email
    assert "admin" in data["user"]["roles"]


def test_login_invalid_email_returns_401(client):
    response = client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "anypassword"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_invalid_password_returns_401(client, test_db, test_user):
    _set_password(test_db, test_user.email, "correct-password")

    response = client.post(
        "/auth/login",
        json={"email": test_user.email, "password": "wrongpassword"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_missing_fields_returns_422(client):
    response = client.post("/auth/login", json={"email": "test@example.com"})
    assert response.status_code == 422

    response = client.post("/auth/login", json={"password": "test123"})
    assert response.status_code == 422

    response = client.post("/auth/login", json={})
    assert response.status_code == 422
