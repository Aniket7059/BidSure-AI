import pytest
from app.core.taxonomy import RequirementType
from app.providers.register import register_providers
from app.providers.registry import provider_registry
from app.providers.schemas import (
    VerificationRequest,
    VerificationStatus,
    map_to_requirement_type,
)


def setup_module():
    register_providers()


def test_all_14_verification_providers_registered():
    """Verify that all 14 statutory verification categories are registered and resolvable."""
    expected_categories = [
        ("GST", "GST_REGISTRATION"),
        ("GST_RETURN", "GST_RETURN_FILING"),
        ("PAN", "PAN_VERIFICATION"),
        ("INCOME_TAX", "INCOME_TAX_COMPLIANCE"),
        ("UDYAM", "UDYAM_VERIFICATION"),
        ("MCA21", "MCA21_CORPORATE_CHECK"),
        ("DEBARMENT", "DEBARMENT_VERIFICATION"),
        ("EPFO", "EPFO_COMPLIANCE"),
        ("ESIC", "ESIC_COMPLIANCE"),
        ("STARTUP_INDIA", "STARTUP_INDIA_CHECK"),
        ("NSIC", "NSIC_VERIFICATION"),
        ("MAKE_IN_INDIA", "MAKE_IN_INDIA"),
        ("OEM_AUTHORIZATION", "OEM_AUTHORIZATION"),
        ("DIGILOCKER", "DIGILOCKER_VERIFICATION"),
    ]

    for req_type, alias_key in expected_categories:
        provider = provider_registry.get(req_type)
        assert provider is not None, f"Provider for {req_type} failed to resolve."
        
        provider_by_alias = provider_registry.get(alias_key)
        assert provider_by_alias is not None, f"Provider for alias {alias_key} failed to resolve."


def test_gst_registration_provider():
    provider = provider_registry.get("GST")
    res = provider.verify(VerificationRequest(identifier="27ABCDE1234F1Z5", verification_type="GST_REGISTRATION"))
    assert res.status == VerificationStatus.VERIFIED
    assert res.verified_data.get("gstin") == "27ABCDE1234F1Z5"
    assert res.verified_data.get("registration_status") == "ACTIVE"


def test_gst_return_provider():
    provider = provider_registry.get("GST_RETURN")
    res = provider.verify(VerificationRequest(identifier="27ABCDE1234F1Z5", verification_type="GST_RETURN"))
    assert res.status == VerificationStatus.VERIFIED
    assert res.verified_data.get("filing_status") == "FILED"
    assert res.verified_data.get("return_type") == "GSTR-3B"
    assert res.source == "MOCK_GST_RETURN"


def test_pan_provider():
    provider = provider_registry.get("PAN")
    res = provider.verify(VerificationRequest(identifier="ABCDE1234F", verification_type="PAN_VERIFICATION"))
    assert res.status == VerificationStatus.VERIFIED
    assert res.verified_data.get("pan_number") == "ABCDE1234F"
    assert res.verified_data.get("name") == "ABC INDUSTRIES PRIVATE LIMITED"


def test_income_tax_provider():
    provider = provider_registry.get("INCOME_TAX")
    res = provider.verify(VerificationRequest(identifier="ABCDE1234F", verification_type="INCOME_TAX_COMPLIANCE"))
    assert res.status == VerificationStatus.VERIFIED
    assert res.verified_data.get("itr_filed") is True
    assert res.verified_data.get("tax_compliance_status") == "COMPLIANT"
    assert res.source == "MOCK_INCOME_TAX"


def test_udyam_provider():
    provider = provider_registry.get("UDYAM")
    res = provider.verify(VerificationRequest(identifier="UDYAM-MH-01-0012345", verification_type="UDYAM_VERIFICATION"))
    assert res.status == VerificationStatus.VERIFIED
    assert res.verified_data.get("enterprise_type") == "MICRO"


def test_mca21_provider():
    provider = provider_registry.get("MCA21")
    res = provider.verify(VerificationRequest(identifier="U74999MH2018PTC301234", verification_type="MCA21_CORPORATE_CHECK"))
    assert res.status == VerificationStatus.VERIFIED
    assert res.verified_data.get("company_status") == "ACTIVE"


def test_debarment_provider():
    provider = provider_registry.get("DEBARMENT")
    res = provider.verify(VerificationRequest(identifier="ABCDE1234F", verification_type="DEBARMENT_VERIFICATION"))
    assert res.status == VerificationStatus.VERIFIED
    assert res.verified_data.get("is_debarred") is False


def test_make_in_india_provider():
    provider = provider_registry.get("MAKE_IN_INDIA")
    res = provider.verify(VerificationRequest(identifier="MII-DECL-123", verification_type="MAKE_IN_INDIA"))
    assert res.status == VerificationStatus.VERIFIED
    assert res.verified_data.get("local_content_percentage") == 65.0
    assert res.verified_data.get("supplier_class") == "CLASS_1_LOCAL_SUPPLIER"
    assert res.source == "MOCK_MAKE_IN_INDIA"


def test_oem_authorization_provider():
    provider = provider_registry.get("OEM_AUTHORIZATION")
    res = provider.verify(VerificationRequest(identifier="OEM-AUTH-1001", verification_type="OEM_AUTHORIZATION"))
    assert res.status == VerificationStatus.VERIFIED
    assert res.verified_data.get("authorization_status") == "VALID"
    assert res.source == "MOCK_OEM_AUTHORIZATION"


def test_oem_authorization_missing_or_invalid_returns_not_found():
    provider = provider_registry.get("OEM_AUTHORIZATION")
    res = provider.verify(VerificationRequest(identifier="INVALID-REF-9999", verification_type="OEM_AUTHORIZATION"))
    assert res.status == VerificationStatus.NOT_FOUND
    assert res.status != VerificationStatus.VERIFIED


def test_digilocker_provider():
    provider = provider_registry.get("DIGILOCKER")
    res = provider.verify(VerificationRequest(identifier="in.gov.digilocker.doc.12345", verification_type="DIGILOCKER_VERIFICATION"))
    assert res.status == VerificationStatus.VERIFIED
    assert res.verified_data.get("digital_signature_valid") is True
    assert res.source == "MOCK_DIGILOCKER"


def test_digilocker_requirement_type_mapping():
    assert map_to_requirement_type("DIGILOCKER") == RequirementType.DIGILOCKER.value
    assert map_to_requirement_type("DIGILOCKER_DOCUMENT") == RequirementType.DIGILOCKER.value
    assert map_to_requirement_type("DIGILOCKER") != RequirementType.OTHER.value
