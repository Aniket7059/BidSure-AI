from abc import ABC, abstractmethod
import re

from pydantic import BaseModel, ConfigDict

from app.providers.base import VerificationProvider
from app.providers.schemas import (
    SourceMode,
    VerificationRequest,
    VerificationResult,
    VerificationStatus,
)


GSTIN_PATTERN = re.compile(
    r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9]Z[A-Z0-9]$"
)


from app.core.taxonomy import RequirementType


class GSTVerificationRecord(BaseModel):
    """Normalized facts returned by a GST verification source."""

    model_config = ConfigDict(extra="forbid")

    gstin: str
    legal_name: str | None = None
    trade_name: str | None = None
    registration_status: str | None = None
    registration_date: str | None = None
    return_filing_status: str | None = None


class GSTVerificationAdapter(ABC):
    """
    Source adapter used by the GST provider.

    A production implementation can wrap an authorized GST/GSP integration.
    The provider itself remains independent of the transport or source.
    """

    @abstractmethod
    def verify_gstin(self, gstin: str) -> GSTVerificationRecord | None:
        raise NotImplementedError


class GSTVerificationProvider(VerificationProvider):
    """GST registration and return-filing verification provider."""

    def __init__(self, adapter: GSTVerificationAdapter) -> None:
        self._adapter = adapter

    @property
    def provider_name(self) -> str:
        return "GST"

    @property
    def supported_verification_types(self) -> set[str]:
        return {
            RequirementType.GST.value,
            "GST_REGISTRATION",
        }

    @property
    def source_mode(self) -> SourceMode:
        if hasattr(self._adapter, "source_mode"):
            return self._adapter.source_mode
        return SourceMode.SYNTHETIC

    def verify(self, request: VerificationRequest) -> VerificationResult:
        verification_type = request.verification_type.upper().strip()
        gstin = request.identifier.strip().upper()

        if not self.supports(verification_type):
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=gstin,
                status=VerificationStatus.NOT_APPLICABLE,
                source_mode=self.source_mode,
                message=(
                    f"GST provider does not support verification type: "
                    f"{verification_type}"
                ),
            )

        if not GSTIN_PATTERN.fullmatch(gstin):
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=gstin,
                status=VerificationStatus.NOT_VERIFIED,
                source_mode=self.source_mode,
                message="GSTIN format is invalid.",
            )

        try:
            record = self._adapter.verify_gstin(gstin)
        except Exception as exc:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=gstin,
                status=VerificationStatus.ERROR,
                source_mode=self.source_mode,
                message="GST verification source could not be reached.",
                error_message=str(exc),
            )

        if record is None:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=gstin,
                status=VerificationStatus.NOT_FOUND,
                source_mode=self.source_mode,
                message="GSTIN was not found in the configured verification source.",
            )

        verified_data = record.model_dump(exclude_none=True)

        if verification_type == "GST_REGISTRATION":
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=gstin,
                status=VerificationStatus.VERIFIED,
                source_mode=self.source_mode,
                verified_data=verified_data,
                message="GST registration details were found in the configured source.",
            )

        return VerificationResult(
            provider=self.provider_name,
            verification_type=verification_type,
            identifier=gstin,
            status=VerificationStatus.VERIFIED,
            source_mode=self.source_mode,
            verified_data={
                "gstin": record.gstin,
                "return_filing_status": record.return_filing_status,
            },
            message="GST return-filing information was found in the configured source.",
        )
