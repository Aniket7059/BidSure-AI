import logging
from typing import Any

from app.providers.debarment.provider import DebarmentVerificationAdapter, DebarmentVerificationRecord
from app.providers.digilocker.provider import DigiLockerVerificationAdapter, DigiLockerVerificationRecord
from app.providers.epfo_esic.provider import EPFOESICVerificationAdapter, EPFOESICVerificationRecord
from app.providers.gst.provider import GSTVerificationAdapter, GSTVerificationRecord
from app.providers.income_tax.provider import IncomeTaxVerificationAdapter
from app.providers.live_base import BaseLiveHttpAdapter
from app.providers.mca21.provider import MCA21VerificationAdapter, MCA21VerificationRecord
from app.providers.pan.provider import PANVerificationAdapter, PANVerificationRecord
from app.providers.schemas import SourceMode
from app.providers.udyam.provider import UdyamVerificationAdapter, UdyamVerificationRecord

logger = logging.getLogger(__name__)


class LiveGSTAdapter(GSTVerificationAdapter, BaseLiveHttpAdapter):
    """Authorized GSTN GSP API Adapter."""

    def __init__(
        self,
        enabled: bool = False,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 10,
    ) -> None:
        BaseLiveHttpAdapter.__init__(
            self,
            enabled=enabled,
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            source_mode=SourceMode.AUTHORIZED_PROVIDER,
        )

    def verify_gstin(self, gstin: str) -> GSTVerificationRecord | None:
        data, err, reason = self.execute_get(f"/gstin/{gstin}")
        if err:
            raise RuntimeError(f"{err}: {reason}")
        if not data:
            return None

        return GSTVerificationRecord(
            gstin=data.get("gstin", gstin),
            legal_name=data.get("legal_name"),
            trade_name=data.get("trade_name"),
            registration_status=data.get("registration_status", "ACTIVE"),
            registration_date=data.get("registration_date"),
            return_filing_status=data.get("return_filing_status", "FILLED"),
        )


class LivePANAdapter(PANVerificationAdapter, BaseLiveHttpAdapter):
    """Authorized Income Tax / NSDL PAN Verification Adapter."""

    def __init__(
        self,
        enabled: bool = False,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 10,
    ) -> None:
        BaseLiveHttpAdapter.__init__(
            self,
            enabled=enabled,
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            source_mode=SourceMode.AUTHORIZED_PROVIDER,
        )

    def verify_pan(self, pan: str) -> PANVerificationRecord | None:
        data, err, reason = self.execute_get(f"/pan/{pan}")
        if err:
            raise RuntimeError(f"{err}: {reason}")
        if not data:
            return None

        return PANVerificationRecord(
            pan=data.get("pan", pan),
            name_on_card=data.get("name_on_card"),
            status=data.get("status", "VALID"),
            aadhaar_seeding_status=data.get("aadhaar_seeding_status", "LINKED"),
            category=data.get("category", "COMPANY"),
        )


class LiveUdyamAdapter(UdyamVerificationAdapter, BaseLiveHttpAdapter):
    """Authorized MSME Udyam Portal Verification Adapter."""

    def __init__(
        self,
        enabled: bool = False,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 10,
    ) -> None:
        BaseLiveHttpAdapter.__init__(
            self,
            enabled=enabled,
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            source_mode=SourceMode.AUTHORIZED_PROVIDER,
        )

    def verify_udyam(self, udyam_number: str) -> UdyamVerificationRecord | None:
        data, err, reason = self.execute_get(f"/udyam/{udyam_number}")
        if err:
            raise RuntimeError(f"{err}: {reason}")
        if not data:
            return None

        return UdyamVerificationRecord(
            udyam_registration_number=data.get("udyam_registration_number", udyam_number),
            enterprise_name=data.get("enterprise_name"),
            enterprise_type=data.get("enterprise_type", "MICRO"),
            organization_type=data.get("organization_type", "PRIVATE_LIMITED"),
            major_activity=data.get("major_activity", "MANUFACTURING"),
            social_category=data.get("social_category", "GENERAL"),
            date_of_registration=data.get("date_of_registration"),
        )


class LiveMCAAdapter(MCA21VerificationAdapter, BaseLiveHttpAdapter):
    """Official MCA21 Corporate Data Portal Adapter."""

    def __init__(
        self,
        enabled: bool = False,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 10,
    ) -> None:
        BaseLiveHttpAdapter.__init__(
            self,
            enabled=enabled,
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            source_mode=SourceMode.OFFICIAL_API,
        )

    def verify_cin(self, cin: str) -> MCA21VerificationRecord | None:
        data, err, reason = self.execute_get(f"/cin/{cin}")
        if err:
            raise RuntimeError(f"{err}: {reason}")
        if not data:
            return None

        return MCA21VerificationRecord(
            cin=data.get("cin", cin),
            company_name=data.get("company_name"),
            company_status=data.get("company_status", "ACTIVE"),
            date_of_incorporation=data.get("date_of_incorporation"),
            authorized_capital_inr=data.get("authorized_capital_inr"),
            paid_up_capital_inr=data.get("paid_up_capital_inr"),
            active_directors=data.get("active_directors"),
        )


class LiveEPFOAdapter(EPFOESICVerificationAdapter, BaseLiveHttpAdapter):
    """Authorized EPFO Shram Suvidha Verification Adapter."""

    def __init__(
        self,
        enabled: bool = False,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 10,
    ) -> None:
        BaseLiveHttpAdapter.__init__(
            self,
            enabled=enabled,
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            source_mode=SourceMode.OFFICIAL_API,
        )

    def verify_establishment(self, establishment_code: str) -> EPFOESICVerificationRecord | None:
        data, err, reason = self.execute_get(f"/epfo/{establishment_code}")
        if err:
            raise RuntimeError(f"{err}: {reason}")
        if not data:
            return None

        return EPFOESICVerificationRecord(
            establishment_code=data.get("establishment_code", establishment_code),
            establishment_name=data.get("establishment_name"),
            coverage_status=data.get("coverage_status", "ACTIVE"),
            monthly_filing_status=data.get("monthly_filing_status", "COMPLIANT"),
            last_ecr_month=data.get("last_ecr_month"),
            active_member_count=data.get("active_member_count"),
        )


class LiveDigiLockerAdapter(DigiLockerVerificationAdapter, BaseLiveHttpAdapter):
    """Official DigiLocker Government Gateway Adapter."""

    def __init__(
        self,
        enabled: bool = False,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 10,
    ) -> None:
        BaseLiveHttpAdapter.__init__(
            self,
            enabled=enabled,
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            source_mode=SourceMode.OFFICIAL_API,
        )

    def verify_digilocker_document(self, digilocker_uri_or_id: str) -> DigiLockerVerificationRecord | None:
        data, err, reason = self.execute_get(f"/doc/{digilocker_uri_or_id}")
        if err:
            raise RuntimeError(f"{err}: {reason}")
        if not data:
            return None

        return DigiLockerVerificationRecord(
            digilocker_uri=data.get("digilocker_uri", digilocker_uri_or_id),
            document_type=data.get("document_type", "CERTIFICATE"),
            document_name=data.get("document_name"),
            issuer_name=data.get("issuer_name", "GOVT_ISSUER"),
            issuer_id=data.get("issuer_id"),
            digital_signature_valid=data.get("digital_signature_valid", True),
            verification_status=data.get("verification_status", "VERIFIED"),
        )

