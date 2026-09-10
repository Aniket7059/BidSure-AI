from datetime import datetime, timezone

from app.providers.schemas import VerificationResult, VerificationStatus


def test_standardized_verification_result_structure():
    result = VerificationResult(
        provider="GST",
        verification_type="GST_REGISTRATION",
        identifier="27ABCDE1234F1Z5",
        status=VerificationStatus.VERIFIED,
        verified_data={
            "gstin": "27ABCDE1234F1Z5",
            "legal_name": "Acme Private Limited",
            "registration_status": "ACTIVE",
        },
    )

    dumped = result.model_dump(mode="json")
    assert dumped["requirement_type"] == "GST"
    assert dumped["identifier"] == "27ABCDE1234F1Z5"
    assert dumped["status"] == "VERIFIED"
    assert dumped["verified_data"] == {
        "gstin": "27ABCDE1234F1Z5",
        "legal_name": "Acme Private Limited",
        "registration_status": "ACTIVE",
    }
    assert dumped["source"] == "GST"
    assert "checked_at" in dumped


def test_standardized_verification_result_explicit_fields():
    now = datetime.now(timezone.utc)
    result = VerificationResult(
        requirement_type="UDYAM",
        identifier="UDYAM-KR-03-0012345",
        status=VerificationStatus.VERIFIED,
        verified_data={
            "udyam_number": "UDYAM-KR-03-0012345",
            "enterprise_name": "Tech Corp",
        },
        source="UDYAM",
        checked_at=now,
    )

    assert result.requirement_type == "UDYAM"
    assert result.source == "UDYAM"
    assert result.provider == "UDYAM"
    assert result.status == VerificationStatus.VERIFIED
