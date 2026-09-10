from abc import ABC, abstractmethod
import re

from pydantic import BaseModel, ConfigDict

from app.providers.base import VerificationProvider
from app.providers.schemas import (
    VerificationRequest,
    VerificationResult,
    VerificationStatus,
)


PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


from app.core.taxonomy import RequirementType


class PANVerificationRecord(BaseModel):
    """Normalized facts returned by a PAN verification source."""

    model_config = ConfigDict(extra="forbid")

    pan_number: str
    name: str | None = None
    category: str | None = None
    status: str | None = None
    last_itr_filed_year: str | None = None
    tax_compliance_status: str | None = None


class PANVerificationAdapter(ABC):
    """
    Source adapter used by the PAN provider.

    Can wrap live Income Tax Department / NSDL / UTIITSL API integrations.
    """

    @abstractmethod
    def verify_pan(self, pan: str) -> PANVerificationRecord | None:
        raise NotImplementedError


class PANVerificationProvider(VerificationProvider):
    """PAN registration and Income Tax compliance verification provider."""

    def __init__(self, adapter: PANVerificationAdapter) -> None:
        self._adapter = adapter

    @property
    def provider_name(self) -> str:
        return "PAN"

    @property
    def supported_verification_types(self) -> set[str]:
        return {
            RequirementType.PAN.value,
            "PAN_VERIFICATION",
        }

    def verify(self, request: VerificationRequest) -> VerificationResult:
        verification_type = request.verification_type.upper().strip()
        pan = request.identifier.strip().upper()

        if not self.supports(verification_type):
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=pan,
                status=VerificationStatus.NOT_APPLICABLE,
                message=(
                    f"PAN provider does not support verification type: "
                    f"{verification_type}"
                ),
            )

        if not PAN_PATTERN.fullmatch(pan):
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=pan,
                status=VerificationStatus.NOT_VERIFIED,
                message="PAN format is invalid. Must be 10 alphanumeric characters (e.g. ABCDE1234F).",
            )

        try:
            record = self._adapter.verify_pan(pan)
        except Exception as exc:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=pan,
                status=VerificationStatus.ERROR,
                message="PAN verification source could not be reached.",
                error_message=str(exc),
            )

        if record is None:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=pan,
                status=VerificationStatus.NOT_FOUND,
                message="PAN was not found in the configured verification source.",
            )

        verified_data = record.model_dump(exclude_none=True)

        if verification_type == "PAN_VERIFICATION":
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=pan,
                status=VerificationStatus.VERIFIED,
                verified_data=verified_data,
                message="PAN details were successfully verified in the configured source.",
            )

        return VerificationResult(
            provider=self.provider_name,
            verification_type=verification_type,
            identifier=pan,
            status=VerificationStatus.VERIFIED,
            verified_data={
                "pan_number": record.pan_number,
                "last_itr_filed_year": record.last_itr_filed_year,
                "tax_compliance_status": record.tax_compliance_status,
            },
            message="Income Tax compliance information was found in the configured source.",
        )
