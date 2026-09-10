from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict

from app.core.taxonomy import RequirementType
from app.providers.base import VerificationProvider
from app.providers.schemas import (
    VerificationRequest,
    VerificationResult,
    VerificationStatus,
)


class MakeInIndiaVerificationRecord(BaseModel):
    """Facts returned by a Make In India / Local Content verification source."""

    model_config = ConfigDict(extra="forbid")

    identifier: str
    bidder_name: str | None = None
    local_content_percentage: float = 60.0
    supplier_class: str = "CLASS_1_LOCAL_SUPPLIER"
    location_of_value_addition: str | None = "INDIA"
    declaration_status: str = "VERIFIED"


class MakeInIndiaVerificationAdapter(ABC):
    """Adapter interface for Make In India / Local Content verification."""

    @abstractmethod
    def verify_local_content(self, identifier: str) -> MakeInIndiaVerificationRecord | None:
        raise NotImplementedError


class MakeInIndiaVerificationProvider(VerificationProvider):
    """Provider specifically handling Make In India / Local Content verification."""

    def __init__(self, adapter: MakeInIndiaVerificationAdapter) -> None:
        self._adapter = adapter

    @property
    def provider_name(self) -> str:
        return "MAKE_IN_INDIA"

    @property
    def supported_verification_types(self) -> set[str]:
        return {
            RequirementType.MAKE_IN_INDIA.value,
            "LOCAL_CONTENT",
            "MAKE_IN_INDIA_DECLARATION",
        }

    def verify(self, request: VerificationRequest) -> VerificationResult:
        verification_type = request.verification_type.upper().strip()
        identifier = request.identifier.strip()

        if not self.supports(verification_type):
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=identifier,
                status=VerificationStatus.NOT_APPLICABLE,
                message=f"Make In India provider does not support verification type: {verification_type}",
            )

        try:
            record = self._adapter.verify_local_content(identifier)
        except Exception as exc:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=identifier,
                status=VerificationStatus.ERROR,
                message="Make In India verification source could not be reached.",
                error_message=str(exc),
            )

        if record is None:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=identifier,
                status=VerificationStatus.NOT_FOUND,
                message="Make In India declaration or certificate reference was not found in verification source.",
            )

        verified_data = record.model_dump(exclude_none=True)
        return VerificationResult(
            provider=self.provider_name,
            verification_type=verification_type,
            identifier=identifier,
            status=VerificationStatus.VERIFIED if record.declaration_status == "VERIFIED" else VerificationStatus.MISMATCH,
            verified_data=verified_data,
            source="MOCK_MAKE_IN_INDIA",
            message="Make In India local content declaration verified successfully.",
        )
