from abc import ABC, abstractmethod
import re
from pydantic import BaseModel, ConfigDict

from app.core.taxonomy import RequirementType
from app.providers.base import VerificationProvider
from app.providers.schemas import (
    VerificationRequest,
    VerificationResult,
    VerificationStatus,
)

GSTIN_PATTERN = re.compile(
    r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9]Z[A-Z0-9]$"
)


class GSTReturnVerificationRecord(BaseModel):
    """Facts returned by a GST Return / filing verification source."""

    model_config = ConfigDict(extra="forbid")

    gstin: str
    return_type: str | None = "GSTR-3B"
    financial_year: str | None = "2023-24"
    tax_period: str | None = "MARCH"
    filing_date: str | None = None
    filing_status: str | None = "FILED"
    arn_acknowledgement_number: str | None = None


class GSTReturnVerificationAdapter(ABC):
    """Adapter interface for GST Return filing verification."""

    @abstractmethod
    def verify_gst_return(self, gstin: str) -> GSTReturnVerificationRecord | None:
        raise NotImplementedError


class GSTReturnVerificationProvider(VerificationProvider):
    """Provider specifically handling GST Return filing verification."""

    def __init__(self, adapter: GSTReturnVerificationAdapter) -> None:
        self._adapter = adapter

    @property
    def provider_name(self) -> str:
        return "GST_RETURN"

    @property
    def supported_verification_types(self) -> set[str]:
        return {
            "GST_RETURN_FILING",
            "GST_RETURN",
        }

    def verify(self, request: VerificationRequest) -> VerificationResult:
        verification_type = request.verification_type.upper().strip()
        gstin = request.identifier.strip().upper()

        if not self.supports(verification_type):
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=gstin,
                status=VerificationStatus.NOT_APPLICABLE,
                message=f"GST Return provider does not support verification type: {verification_type}",
            )

        if not GSTIN_PATTERN.fullmatch(gstin):
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=gstin,
                status=VerificationStatus.NOT_VERIFIED,
                message="GSTIN format is invalid for GST Return check.",
            )

        try:
            record = self._adapter.verify_gst_return(gstin)
        except Exception as exc:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=gstin,
                status=VerificationStatus.ERROR,
                message="GST Return verification source could not be reached.",
                error_message=str(exc),
            )

        if record is None:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=gstin,
                status=VerificationStatus.NOT_FOUND,
                message="GST Return filing record was not found in the configured source.",
            )

        verified_data = record.model_dump(exclude_none=True)
        return VerificationResult(
            provider=self.provider_name,
            verification_type=verification_type,
            identifier=gstin,
            status=VerificationStatus.VERIFIED if record.filing_status == "FILED" else VerificationStatus.MISMATCH,
            verified_data=verified_data,
            source="MOCK_GST_RETURN",
            message="GST Return filing status retrieved successfully.",
        )
