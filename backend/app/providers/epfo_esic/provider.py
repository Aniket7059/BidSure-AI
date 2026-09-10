from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict

from app.core.taxonomy import RequirementType
from app.providers.base import VerificationProvider
from app.providers.schemas import (
    VerificationRequest,
    VerificationResult,
    VerificationStatus,
)


class EPFOESICVerificationRecord(BaseModel):
    """Normalized facts returned by an EPFO/ESIC verification source."""

    model_config = ConfigDict(extra="forbid")

    establishment_code: str
    establishment_name: str | None = None
    coverage_status: str | None = None  # ACTIVE, INACTIVE
    monthly_filing_status: str | None = None  # COMPLIANT, DEFTERRED, DEFAULTED
    last_ecr_month: str | None = None
    active_member_count: int | None = None


class EPFOESICVerificationAdapter(ABC):
    """Source adapter for EPFO & ESIC establishment verification."""

    @abstractmethod
    def verify_establishment(self, establishment_code: str) -> EPFOESICVerificationRecord | None:
        raise NotImplementedError


class EPFOESICVerificationProvider(VerificationProvider):
    """EPFO & ESIC statutory employee compliance verification provider."""

    def __init__(self, adapter: EPFOESICVerificationAdapter) -> None:
        self._adapter = adapter

    @property
    def provider_name(self) -> str:
        return "EPFO_ESIC"

    @property
    def supported_verification_types(self) -> set[str]:
        return {
            RequirementType.EPFO.value,
            RequirementType.ESIC.value,
            "EPFO_COMPLIANCE",
            "ESIC_COMPLIANCE",
        }

    def verify(self, request: VerificationRequest) -> VerificationResult:
        verification_type = request.verification_type.upper().strip()
        code = request.identifier.strip().upper()

        if not self.supports(verification_type):
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=code,
                status=VerificationStatus.NOT_APPLICABLE,
                message=(
                    f"EPFO/ESIC provider does not support verification type: "
                    f"{verification_type}"
                ),
            )

        if not code:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=code,
                status=VerificationStatus.NOT_VERIFIED,
                message="Establishment code cannot be empty.",
            )

        try:
            record = self._adapter.verify_establishment(code)
        except Exception as exc:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=code,
                status=VerificationStatus.ERROR,
                message="EPFO/ESIC portal could not be reached.",
                error_message=str(exc),
            )

        if record is None:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=code,
                status=VerificationStatus.NOT_FOUND,
                message="Establishment code was not found in the EPFO/ESIC database.",
            )

        verified_data = record.model_dump(exclude_none=True)

        return VerificationResult(
            provider=self.provider_name,
            verification_type=verification_type,
            identifier=code,
            status=VerificationStatus.VERIFIED,
            verified_data=verified_data,
            message=f"{verification_type} establishment compliance and monthly ECR filings verified.",
        )
