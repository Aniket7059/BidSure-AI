from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing():
    password = "TestPassword123"

    hashed = hash_password(password)

    # Password must not be stored as plain text
    assert hashed != password

    # Correct password should work
    assert verify_password(password, hashed)

    # Wrong password should fail
    assert not verify_password("WrongPassword", hashed)


def test_jwt_token():
    token = create_access_token(
        user_id=1,
        role="PROCUREMENT_OFFICER",
    )

    payload = decode_access_token(token)

    assert payload["sub"] == "1"
    assert payload["role"] == "PROCUREMENT_OFFICER"