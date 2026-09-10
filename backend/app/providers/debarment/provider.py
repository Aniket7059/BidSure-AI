from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict

from app.core.taxonomy import RequirementType
from app.providers.base import VerificationProvider
from app.providers.schemas import (
    VerificationRequest,
    VerificationResult,
    VerificationStatus,
)


class DebarmentVerificationRecord(BaseModel):
    """Normalized facts returned by a debarment/blacklisting verification check."""

    model_config = ConfigDict(extra="forbid")

    identifier: str
    is_debarred: bool
    debarment_status: str | None = None  # CLEAN, DEBARRED, SUSPENDED
    debarring_agency: str | None = None
    debarment_period: str | None = None
    reason: str | None = None


class DebarmentVerificationAdapter(ABC):
    """Source adapter for checking blacklisting/debarment databases."""

    @abstractmethod
    def check_debarment(self, identifier: str) -> DebarmentVerificationRecord | None:
        raise NotImplementedError


class DebarmentVerificationProvider(VerificationProvider):
    """GeM and Central Public Sector Debarment/Blacklisting verification provider."""

    def __init__(self, adapter: DebarmentVerificationAdapter) -> None:
        self._adapter = adapter

    @property
    def provider_name(self) -> str:
        return "DEBARMENT"

    @property
    def supported_verification_types(self) -> set[str]:
        return {
            RequirementType.DEBARMENT.value,
            "DEBARMENT_VERIFICATION",
            "BLACK_LISTING_CHECK",
        }

    def verify(self, request: VerificationRequest) -> VerificationResult:
        verification_type = request.verification_type.upper().strip()
        identifier = request.identifier.strip().upper()

        if not self.supports(verification_type):
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=identifier,
                status=VerificationStatus.NOT_APPLICABLE,
                message=(
                    f"Debarment provider does not support verification type: "
                    f"{verification_type}"
                ),
            )

        if not identifier:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=identifier,
                status=VerificationStatus.NOT_VERIFIED,
                message="Identifier cannot be empty for debarment check.",
            )

        try:
            record = self._adapter.check_debarment(identifier)
        except Exception as exc:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=identifier,
                status=VerificationStatus.ERROR,
                message="Debarment/Blacklisting database could not be reached.",
                error_message=str(exc),
            )

        if record is None:
            # If no record is found, vendor has a clean status with no blacklisting records.
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=identifier,
                status=VerificationStatus.VERIFIED,
                verified_data={
                    "identifier": identifier,
                    "is_debarred": False,
                    "debarment_status": "CLEAN",
                },
                message="No debarment or blacklisting record found for this identifier. Vendor status is clean.",
            )

        verified_data = record.model_dump(exclude_none=True)

        if record.is_debarred:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=identifier,
                status=VerificationStatus.NOT_VERIFIED,
                verified_data=verified_data,
                message=f"CRITICAL WARNING: Identifier is flagged as DEBARRED/BLACKLISTED by {record.debarring_agency or 'Central Authority'}.",
            )

        return VerificationResult(
            provider=self.provider_name,
            verification_type=verification_type,
            identifier=identifier,
            status=VerificationStatus.VERIFIED,
            verified_data=verified_data,
            message="Debarment records checked. Vendor is in good standing.",
        )
