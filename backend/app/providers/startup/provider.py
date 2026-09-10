from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict

from app.core.taxonomy import RequirementType
from app.providers.base import VerificationProvider
from app.providers.schemas import (
    VerificationRequest,
    VerificationResult,
    VerificationStatus,
)


class StartupNSICVerificationRecord(BaseModel):
    """Normalized facts returned by a Startup India / NSIC registration source."""

    model_config = ConfigDict(extra="forbid")

    registration_number: str
    entity_name: str | None = None
    scheme_type: str | None = None  # DPIIT_STARTUP, NSIC_SINGLE_POINT
    valid_until: str | None = None
    emd_exemption_eligible: bool = True
    turnover_exemption_eligible: bool = True


class StartupNSICVerificationAdapter(ABC):
    """Source adapter for Startup India & NSIC registry verification."""

    @abstractmethod
    def verify_registration(self, number: str) -> StartupNSICVerificationRecord | None:
        raise NotImplementedError


class StartupNSICVerificationProvider(VerificationProvider):
    """Startup India & NSIC registration verification provider."""

    def __init__(self, adapter: StartupNSICVerificationAdapter) -> None:
        self._adapter = adapter

    @property
    def provider_name(self) -> str:
        return "STARTUP_NSIC"

    @property
    def supported_verification_types(self) -> set[str]:
        return {
            RequirementType.STARTUP_INDIA.value,
            RequirementType.NSIC.value,
            "STARTUP_INDIA_CHECK",
            "NSIC_VERIFICATION",
        }

    def verify(self, request: VerificationRequest) -> VerificationResult:
        verification_type = request.verification_type.upper().strip()
        number = request.identifier.strip().upper()

        if not self.supports(verification_type):
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=number,
                status=VerificationStatus.NOT_APPLICABLE,
                message=(
                    f"Startup/NSIC provider does not support verification type: "
                    f"{verification_type}"
                ),
            )

        if not number:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=number,
                status=VerificationStatus.NOT_VERIFIED,
                message="Registration number cannot be empty.",
            )

        try:
            record = self._adapter.verify_registration(number)
        except Exception as exc:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=number,
                status=VerificationStatus.ERROR,
                message="Startup India / NSIC verification database could not be reached.",
                error_message=str(exc),
            )

        if record is None:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=number,
                status=VerificationStatus.NOT_FOUND,
                message="Registration number was not found in Startup India / NSIC records.",
            )

        verified_data = record.model_dump(exclude_none=True)

        return VerificationResult(
            provider=self.provider_name,
            verification_type=verification_type,
            identifier=number,
            status=VerificationStatus.VERIFIED,
            verified_data=verified_data,
            message="Startup India / NSIC registration and waiver eligibility verified.",
        )
