from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import verification
from app.database.session import get_db
from app.services.verification_service import verification_service


from app.api.dependencies import get_current_user
from app.models.user import User


def mock_get_current_user():
    return User(
        id=1,
        full_name="Test Officer",
        email="officer@test.com",
        role="PROCUREMENT_OFFICER",
        is_active=True,
    )


def create_test_app():
    app = FastAPI()
    app.include_router(verification.router)

    db = Mock()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = mock_get_current_user
    return app, db


def test_verify_identifier_returns_persisted_result():
    app, db = create_test_app()

    result = SimpleNamespace(
        provider="GST",
        verification_type="GST_REGISTRATION",
        identifier="27ABCDE1234F1Z5",
        checked_at=datetime.now(timezone.utc),
    )

    persisted = SimpleNamespace(
        id=1,
        bid_submission_id=10,
        bid_document_id=20,
        provider="GST",
        verification_type="GST_REGISTRATION",
        identifier="27ABCDE1234F1Z5",
        verification_status="VERIFIED",
        verified_data={"gstin": "27ABCDE1234F1Z5"},
        message="verified",
        error_message=None,
        checked_at=result.checked_at,
        created_at=result.checked_at,
    )

    original_verify = verification_service.verify
    original_get = verification.verification_result_repository.get_by_submission

    verification_service.verify = Mock(return_value=result)
    verification.verification_result_repository.get_by_submission = Mock(
        return_value=[persisted]
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/verification/verify",
            json={
                "bid_submission_id": 10,
                "bid_document_id": 20,
                "verification_type": "GST_REGISTRATION",
                "identifier": "27ABCDE1234F1Z5",
            },
        )

        assert response.status_code == 201
        assert response.json()["verification_status"] == "VERIFIED"
        assert response.json()["provider"] == "GST"

        verification_service.verify.assert_called_once()
    finally:
        verification_service.verify = original_verify
        verification.verification_result_repository.get_by_submission = original_get


def test_verify_identifier_maps_service_value_error_to_400():
    app, db = create_test_app()

    original_verify = verification_service.verify
    verification_service.verify = Mock(
        side_effect=ValueError("Bid submission not found: 999")
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/verification/verify",
            json={
                "bid_submission_id": 999,
                "verification_type": "GST_REGISTRATION",
                "identifier": "27ABCDE1234F1Z5",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Bid submission not found: 999"
    finally:
        verification_service.verify = original_verify
