import pytest

from app.providers.gst import (
    GSTVerificationProvider,
    MockGSTVerificationAdapter,
)
from app.providers.schemas import VerificationRequest, VerificationStatus


@pytest.fixture
def provider() -> GSTVerificationProvider:
    return GSTVerificationProvider(MockGSTVerificationAdapter())


def test_gst_registration_verified(provider: GSTVerificationProvider) -> None:
    result = provider.verify(
        VerificationRequest(
            identifier="27abcde1234f1z5",
            verification_type="gst_registration",
        )
    )

    assert result.provider == "GST"
    assert result.verification_type == "GST_REGISTRATION"
    assert result.identifier == "27ABCDE1234F1Z5"
    assert result.status == VerificationStatus.VERIFIED
    assert result.verified_data is not None
    assert result.verified_data["legal_name"] == "ABC INDUSTRIES PRIVATE LIMITED"
    assert result.verified_data["registration_status"] == "ACTIVE"


from app.providers.gst_return import (
    GSTReturnVerificationProvider,
    MockGSTReturnVerificationAdapter,
)


def test_gst_return_filing_returns_filing_status() -> None:
    return_provider = GSTReturnVerificationProvider(
        MockGSTReturnVerificationAdapter()
    )
    result = return_provider.verify(
        VerificationRequest(
            identifier="29ABCDE1234F1Z6",
            verification_type="GST_RETURN_FILING",
        )
    )

    assert result.status == VerificationStatus.MISMATCH
    assert result.verified_data["filing_status"] == "NOT_FILED"


def test_unknown_gstin_returns_not_found(
    provider: GSTVerificationProvider,
) -> None:
    result = provider.verify(
        VerificationRequest(
            identifier="27ZZZZZ9999Q1Z1",
            verification_type="GST_REGISTRATION",
        )
    )

    assert result.status == VerificationStatus.NOT_FOUND
    assert result.verified_data is None


def test_invalid_gstin_format_is_not_verified(
    provider: GSTVerificationProvider,
) -> None:
    result = provider.verify(
        VerificationRequest(
            identifier="INVALID-GSTIN",
            verification_type="GST_REGISTRATION",
        )
    )

    assert result.status == VerificationStatus.NOT_VERIFIED
    assert result.message == "GSTIN format is invalid."


def test_unsupported_verification_type_returns_not_applicable(
    provider: GSTVerificationProvider,
) -> None:
    result = provider.verify(
        VerificationRequest(
            identifier="27ABCDE1234F1Z5",
            verification_type="GST_REFUND",
        )
    )

    assert result.status == VerificationStatus.NOT_APPLICABLE


def test_adapter_error_returns_error_status() -> None:
    class FailingAdapter(MockGSTVerificationAdapter):
        def verify_gstin(self, gstin: str):
            raise RuntimeError("synthetic adapter failure")

    provider = GSTVerificationProvider(FailingAdapter())

    result = provider.verify(
        VerificationRequest(
            identifier="27ABCDE1234F1Z5",
            verification_type="GST_REGISTRATION",
        )
    )

    assert result.status == VerificationStatus.ERROR
    assert result.message == "GST verification source could not be reached."
    assert result.error_message == "synthetic adapter failure"
