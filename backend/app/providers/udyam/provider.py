from abc import ABC, abstractmethod
import re

from pydantic import BaseModel, ConfigDict

from app.providers.base import VerificationProvider
from app.providers.schemas import (
    VerificationRequest,
    VerificationResult,
    VerificationStatus,
)


# Standard format: UDYAM-XX-00-0000000
UDYAM_PATTERN = re.compile(r"^UDYAM-[A-Z]{2}-[0-9]{2}-[0-9]{7}$")


from app.core.taxonomy import RequirementType


class UdyamVerificationRecord(BaseModel):
    """Normalized facts returned by an Udyam/MSME verification source."""

    model_config = ConfigDict(extra="forbid")

    udyam_number: str
    enterprise_name: str | None = None
    organisation_type: str | None = None
    enterprise_type: str | None = None  # MICRO, SMALL, MEDIUM
    major_activity: str | None = None   # MANUFACTURING, SERVICES
    registration_date: str | None = None
    status: str | None = None


class UdyamVerificationAdapter(ABC):
    """Source adapter used by the Udyam provider."""

    @abstractmethod
    def verify_udyam(self, udyam_number: str) -> UdyamVerificationRecord | None:
        raise NotImplementedError


class UdyamVerificationProvider(VerificationProvider):
    """Udyam MSME registration verification provider."""

    def __init__(self, adapter: UdyamVerificationAdapter) -> None:
        self._adapter = adapter

    @property
    def provider_name(self) -> str:
        return "UDYAM"

    @property
    def supported_verification_types(self) -> set[str]:
        return {
            RequirementType.UDYAM.value,
            "UDYAM_VERIFICATION",
            "MSME_CATEGORY_CHECK",
        }

    def verify(self, request: VerificationRequest) -> VerificationResult:
        verification_type = request.verification_type.upper().strip()
        udyam_number = request.identifier.strip().upper()

        if not self.supports(verification_type):
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=udyam_number,
                status=VerificationStatus.NOT_APPLICABLE,
                message=(
                    f"Udyam provider does not support verification type: "
                    f"{verification_type}"
                ),
            )

        if not UDYAM_PATTERN.fullmatch(udyam_number):
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=udyam_number,
                status=VerificationStatus.NOT_VERIFIED,
                message="Udyam registration number format is invalid. Example: UDYAM-KR-03-0012345.",
            )

        try:
            record = self._adapter.verify_udyam(udyam_number)
        except Exception as exc:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=udyam_number,
                status=VerificationStatus.ERROR,
                message="Udyam verification portal could not be reached.",
                error_message=str(exc),
            )

        if record is None:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=udyam_number,
                status=VerificationStatus.NOT_FOUND,
                message="Udyam registration number was not found in the official database.",
            )

        verified_data = record.model_dump(exclude_none=True)

        if verification_type == "UDYAM_VERIFICATION":
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=udyam_number,
                status=VerificationStatus.VERIFIED,
                verified_data=verified_data,
                message="Udyam registration was successfully verified.",
            )

        return VerificationResult(
            provider=self.provider_name,
            verification_type=verification_type,
            identifier=udyam_number,
            status=VerificationStatus.VERIFIED,
            verified_data={
                "udyam_number": record.udyam_number,
                "enterprise_type": record.enterprise_type,
                "major_activity": record.major_activity,
            },
            message="MSME enterprise category details were successfully verified.",
        )
