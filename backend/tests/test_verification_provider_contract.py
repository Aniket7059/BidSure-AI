from app.providers.base import VerificationProvider
from app.providers.registry import ProviderRegistry
from app.providers.schemas import (
    VerificationRequest,
    VerificationResult,
    VerificationStatus,
)


class FakeGSTProvider(VerificationProvider):

    @property
    def provider_name(self) -> str:
        return "GST"

    @property
    def supported_verification_types(self) -> set[str]:
        return {
            "GST_REGISTRATION",
            "GST_RETURN_FILING",
        }

    def verify(
        self,
        request: VerificationRequest,
    ) -> VerificationResult:

        return VerificationResult(
            provider=self.provider_name,
            verification_type=request.verification_type,
            identifier=request.identifier,
            status=VerificationStatus.VERIFIED,
            verified_data={
                "gstin": request.identifier
            },
            message="Verification completed successfully.",
        )


def test_verification_result_has_normalized_shape():

    result = VerificationResult(
        provider="GST",
        verification_type="GST_REGISTRATION",
        identifier="27ABCDE1234F1Z5",
        status=VerificationStatus.VERIFIED,
        verified_data={
            "registration_status": "ACTIVE"
        },
    )

    assert result.provider == "GST"

    assert result.status == (
        VerificationStatus.VERIFIED
    )

    assert (
        result.verified_data["registration_status"]
        == "ACTIVE"
    )

    assert result.checked_at.tzinfo is not None


def test_provider_supports_verification_type_case_insensitively():

    provider = FakeGSTProvider()

    assert provider.supports(
        "GST_REGISTRATION"
    ) is True

    assert provider.supports(
        "gst_return_filing"
    ) is True

    assert provider.supports(
        "PAN"
    ) is False


def test_registry_returns_provider_for_supported_type():

    registry = ProviderRegistry()

    provider = FakeGSTProvider()

    registry.register(provider)

    assert registry.get(
        "GST_REGISTRATION"
    ) is provider

    assert registry.get(
        "gst_return_filing"
    ) is provider

    assert registry.get(
        "PAN"
    ) is None


def test_registry_rejects_duplicate_verification_type():

    registry = ProviderRegistry()

    registry.register(
        FakeGSTProvider()
    )

    try:
        registry.register(
            FakeGSTProvider()
        )

        assert False, (
            "Expected duplicate registration "
            "to raise ValueError"
        )

    except ValueError as exc:

        assert (
            "Verification provider already registered "
            "for type"
        ) in str(exc)


def test_provider_returns_standardized_result():

    provider = FakeGSTProvider()

    request = VerificationRequest(
        identifier="27ABCDE1234F1Z5",
        verification_type="GST_REGISTRATION",
    )

    result = provider.verify(request)

    assert result.provider == "GST"

    assert result.identifier == (
        request.identifier
    )

    assert result.status == (
        VerificationStatus.VERIFIED
    )

    assert result.verified_data == {
        "gstin": request.identifier
    }