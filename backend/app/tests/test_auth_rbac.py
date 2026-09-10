import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models.user import User

# Setup in-memory SQLite DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def test_client():
    return TestClient(app)


# --------------------------------------------------
# Test 1 & 2: Password Hashing & Verification
# --------------------------------------------------

def test_password_hashing():
    raw_password = "SecretPassword123"
    hashed = hash_password(raw_password)
    assert hashed != raw_password
    assert len(hashed) > 10


def test_password_verification():
    raw_password = "SecretPassword123"
    hashed = hash_password(raw_password)
    assert verify_password("SecretPassword123", hashed) is True
    assert verify_password("WrongPassword123", hashed) is False


# --------------------------------------------------
# Test 3, 4, 5: Login Scenarios
# --------------------------------------------------

def test_successful_login(test_client):
    db = TestingSessionLocal()
    hashed = hash_password("OfficerPass123")
    user = User(
        full_name="Jane Officer",
        email="jane.officer@cpcl.gov.in",
        hashed_password=hashed,
        role="PROCUREMENT_OFFICER",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.close()

    response = test_client.post(
        "/auth/login",
        json={
            "email": "jane.officer@cpcl.gov.in",
            "password": "OfficerPass123",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(test_client):
    db = TestingSessionLocal()
    existing = db.query(User).filter(User.email == "jane.officer.wrong@cpcl.gov.in").first()
    if not existing:
        hashed = hash_password("OfficerPass123")
        user = User(
            full_name="Jane Officer Wrong",
            email="jane.officer.wrong@cpcl.gov.in",
            hashed_password=hashed,
            role="PROCUREMENT_OFFICER",
            is_active=True,
        )
        db.add(user)
        db.commit()
    db.close()

    response = test_client.post(
        "/auth/login",
        json={
            "email": "jane.officer.wrong@cpcl.gov.in",
            "password": "WrongPassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_unknown_email(test_client):
    response = test_client.post(
        "/auth/login",
        json={
            "email": "unknown@domain.com",
            "password": "AnyPassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


# --------------------------------------------------
# Test 6, 7, 8: JWT Token Validation
# --------------------------------------------------

def test_valid_jwt(test_client):
    db = TestingSessionLocal()
    user = User(
        full_name="Valid User",
        email="valid@cpcl.gov.in",
        hashed_password=hash_password("Pass123"),
        role="PROCUREMENT_OFFICER",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.role)
    db.close()

    response = test_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["email"] == "valid@cpcl.gov.in"
    assert data["role"] == "PROCUREMENT_OFFICER"
    # Verify password & hash are not present
    assert "password" not in data
    assert "hashed_password" not in data


def test_invalid_jwt(test_client):
    response = test_client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid_jwt_token_string"},
    )
    assert response.status_code == 401


def test_missing_jwt(test_client):
    response = test_client.get("/auth/me")
    assert response.status_code == 401


# --------------------------------------------------
# Test 9 & 10: GET /auth/me
# --------------------------------------------------

def test_get_me_valid_token(test_client):
    db = TestingSessionLocal()
    user = User(
        full_name="Admin User",
        email="admin@cpcl.gov.in",
        hashed_password=hash_password("AdminPass123"),
        role="ADMIN",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.role)
    db.close()

    response = test_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "admin@cpcl.gov.in"


def test_get_me_missing_token(test_client):
    response = test_client.get("/auth/me")
    assert response.status_code == 401


# --------------------------------------------------
# Test 11, 12, 13: RBAC & Inactive Users
# --------------------------------------------------

def test_role_allowed(test_client):
    db = TestingSessionLocal()
    user = User(
        full_name="Procurement Officer",
        email="officer@cpcl.gov.in",
        hashed_password=hash_password("Pass123"),
        role="PROCUREMENT_OFFICER",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.role)
    db.close()

    response = test_client.get(
        "/tenders",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_role_forbidden(test_client):
    db = TestingSessionLocal()
    user = User(
        full_name="Guest User",
        email="guest@cpcl.gov.in",
        hashed_password=hash_password("Pass123"),
        role="GUEST",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.role)
    db.close()

    response = test_client.get(
        "/tenders",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Operation not permitted for current user role"


def test_inactive_user_rejected(test_client):
    db = TestingSessionLocal()
    user = User(
        full_name="Inactive User",
        email="inactive@cpcl.gov.in",
        hashed_password=hash_password("Pass123"),
        role="PROCUREMENT_OFFICER",
        is_active=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.role)
    db.close()

    response = test_client.get(
        "/tenders",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "User account is inactive"


# --------------------------------------------------
# Test 14 & 15: Protected API Endpoints
# --------------------------------------------------

def test_protected_api_without_auth(test_client):
    response = test_client.get("/tenders")
    assert response.status_code == 401

    response = test_client.get("/bidders")
    assert response.status_code == 401

    response = test_client.get("/verification/submissions/1/results")
    assert response.status_code == 401


def test_protected_api_with_auth(test_client):
    db = TestingSessionLocal()
    user = User(
        full_name="Officer User",
        email="officer2@cpcl.gov.in",
        hashed_password=hash_password("Pass123"),
        role="PROCUREMENT_OFFICER",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.role)
    db.close()

    headers = {"Authorization": f"Bearer {token}"}

    res_tenders = test_client.get("/tenders", headers=headers)
    assert res_tenders.status_code == 200

    res_bidders = test_client.get("/bidders", headers=headers)
    assert res_bidders.status_code == 200
