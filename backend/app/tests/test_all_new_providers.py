import pytest

from app.providers.pan.mock import MockPANVerificationAdapter
from app.providers.pan.provider import PANVerificationProvider
from app.providers.udyam.mock import MockUdyamVerificationAdapter
from app.providers.udyam.provider import UdyamVerificationProvider
from app.providers.mca21.mock import MockMCA21VerificationAdapter
from app.providers.mca21.provider import MCA21VerificationProvider
from app.providers.debarment.mock import MockDebarmentVerificationAdapter
from app.providers.debarment.provider import DebarmentVerificationProvider
from app.providers.epfo_esic.mock import MockEPFOESICVerificationAdapter
from app.providers.epfo_esic.provider import EPFOESICVerificationProvider
from app.providers.startup.mock import MockStartupNSICVerificationAdapter
from app.providers.startup.provider import StartupNSICVerificationProvider
from app.providers.register import register_providers
from app.providers.registry import provider_registry, ProviderRegistry
from app.providers.schemas import VerificationRequest, VerificationStatus


def test_pan_provider_verification():
    provider = PANVerificationProvider(adapter=MockPANVerificationAdapter())

    assert provider.provider_name == "PAN"
    assert provider.supports("PAN_VERIFICATION")
    assert provider.supports("PAN")

    # Test valid PAN
    req = VerificationRequest(identifier="ABCDE1234F", verification_type="PAN_VERIFICATION")
    res = provider.verify(req)
    assert res.status == VerificationStatus.VERIFIED
    assert res.verified_data["name"] == "ABC INDUSTRIES PRIVATE LIMITED"

    # Test invalid PAN format
    invalid_req = VerificationRequest(identifier="INVALID123", verification_type="PAN_VERIFICATION")
    invalid_res = provider.verify(invalid_req)
    assert invalid_res.status == VerificationStatus.NOT_VERIFIED

    # Test missing PAN
    missing_req = VerificationRequest(identifier="NOTFN1234X", verification_type="PAN_VERIFICATION")
    missing_res = provider.verify(missing_req)
    assert missing_res.status == VerificationStatus.NOT_FOUND


def test_udyam_provider_verification():
    provider = UdyamVerificationProvider(adapter=MockUdyamVerificationAdapter())

    assert provider.provider_name == "UDYAM"
    assert provider.supports("UDYAM_VERIFICATION")
    assert provider.supports("MSME_CATEGORY_CHECK")

    req = VerificationRequest(identifier="UDYAM-MH-01-0012345", verification_type="UDYAM_VERIFICATION")
    res = provider.verify(req)
    assert res.status == VerificationStatus.VERIFIED
    assert res.verified_data["enterprise_type"] == "MICRO"


def test_mca21_provider_verification():
    provider = MCA21VerificationProvider(adapter=MockMCA21VerificationAdapter())

    assert provider.provider_name == "MCA21"
    assert provider.supports("MCA21_CORPORATE_CHECK")

    req = VerificationRequest(identifier="U74999MH2018PTC301234", verification_type="MCA21_CORPORATE_CHECK")
    res = provider.verify(req)
    assert res.status == VerificationStatus.VERIFIED
    assert res.verified_data["company_name"] == "ABC INDUSTRIES PRIVATE LIMITED"


def test_debarment_provider_verification():
    provider = DebarmentVerificationProvider(adapter=MockDebarmentVerificationAdapter())

    assert provider.provider_name == "DEBARMENT"
    assert provider.supports("DEBARMENT_VERIFICATION")

    # Clean vendor test
    clean_req = VerificationRequest(identifier="CLEAN1234F", verification_type="DEBARMENT_VERIFICATION")
    clean_res = provider.verify(clean_req)
    assert clean_res.status == VerificationStatus.VERIFIED
    assert clean_res.verified_data["is_debarred"] is False

    # Debarred vendor test
    debarred_req = VerificationRequest(identifier="DEBAR1234F", verification_type="DEBARMENT_VERIFICATION")
    debarred_res = provider.verify(debarred_req)
    assert debarred_res.status == VerificationStatus.NOT_VERIFIED
    assert debarred_res.verified_data["is_debarred"] is True


def test_epfo_esic_provider_verification():
    provider = EPFOESICVerificationProvider(adapter=MockEPFOESICVerificationAdapter())

    assert provider.provider_name == "EPFO_ESIC"
    assert provider.supports("EPFO_COMPLIANCE")

    req = VerificationRequest(identifier="EPFO1234567", verification_type="EPFO_COMPLIANCE")
    res = provider.verify(req)
    assert res.status == VerificationStatus.VERIFIED
    assert res.verified_data["monthly_filing_status"] == "COMPLIANT"


def test_startup_provider_verification():
    provider = StartupNSICVerificationProvider(adapter=MockStartupNSICVerificationAdapter())

    assert provider.provider_name == "STARTUP_NSIC"
    assert provider.supports("STARTUP_INDIA_CHECK")

    req = VerificationRequest(identifier="DPIIT12345", verification_type="STARTUP_INDIA_CHECK")
    res = provider.verify(req)
    assert res.status == VerificationStatus.VERIFIED
    assert res.verified_data["emd_exemption_eligible"] is True


def test_all_providers_registered_properly():
    register_providers()

    assert provider_registry.get("GST_REGISTRATION") is not None
    assert provider_registry.get("PAN_VERIFICATION") is not None
    assert provider_registry.get("UDYAM_VERIFICATION") is not None
    assert provider_registry.get("MCA21_CORPORATE_CHECK") is not None
    assert provider_registry.get("DEBARMENT_VERIFICATION") is not None
    assert provider_registry.get("EPFO_COMPLIANCE") is not None
    assert provider_registry.get("STARTUP_INDIA_CHECK") is not None
