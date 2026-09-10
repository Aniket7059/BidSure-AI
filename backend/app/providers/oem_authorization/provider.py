from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict

from app.core.taxonomy import RequirementType
from app.providers.base import VerificationProvider
from app.providers.schemas import (
    VerificationRequest,
    VerificationResult,
    VerificationStatus,
)


class OEMAuthorizationRecord(BaseModel):
    """Facts returned by an OEM Authorization verification source."""

    model_config = ConfigDict(extra="forbid")

    authorization_reference_number: str
    oem_name: str | None = None
    authorized_bidder_name: str | None = None
    product_category: str | None = None
    issue_date: str | None = None
    valid_until: str | None = None
    authorization_status: str = "VALID"  # VALID, EXPIRED, REVOKED, INVALID


class OEMAuthorizationAdapter(ABC):
    """Adapter interface for OEM Authorization letter verification."""

    @abstractmethod
    def verify_oem_authorization(self, reference_number: str) -> OEMAuthorizationRecord | None:
        raise NotImplementedError


class OEMAuthorizationVerificationProvider(VerificationProvider):
    """Provider specifically handling OEM Authorization letter verification."""

    def __init__(self, adapter: OEMAuthorizationAdapter) -> None:
        self._adapter = adapter

    @property
    def provider_name(self) -> str:
        return "OEM_AUTHORIZATION"

    @property
    def supported_verification_types(self) -> set[str]:
        return {
            RequirementType.OEM_AUTHORIZATION.value,
            "OEM",
            "OEM_AUTHORIZATION_LETTER",
        }

    def verify(self, request: VerificationRequest) -> VerificationResult:
        verification_type = request.verification_type.upper().strip()
        ref_num = request.identifier.strip()

        if not self.supports(verification_type):
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=ref_num,
                status=VerificationStatus.NOT_APPLICABLE,
                message=f"OEM Authorization provider does not support verification type: {verification_type}",
            )

        if not ref_num or ref_num in ("NONE", "MISSING", "UNKNOWN", "NOT_FOUND"):
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=ref_num,
                status=VerificationStatus.NOT_FOUND,
                message="No valid OEM authorization reference provided.",
            )

        try:
            record = self._adapter.verify_oem_authorization(ref_num)
        except Exception as exc:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=ref_num,
                status=VerificationStatus.ERROR,
                message="OEM authorization verification source could not be reached.",
                error_message=str(exc),
            )

        if record is None:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=ref_num,
                status=VerificationStatus.NOT_FOUND,
                message="OEM authorization reference was not found in verification source.",
            )

        verified_data = record.model_dump(exclude_none=True)

        if record.authorization_status == "VALID":
            status_val = VerificationStatus.VERIFIED
            msg = "OEM authorization certificate verified successfully."
        elif record.authorization_status == "EXPIRED":
            status_val = VerificationStatus.MISMATCH
            msg = "OEM authorization certificate is expired."
        else:
            status_val = VerificationStatus.NOT_VERIFIED
            msg = "OEM authorization status is invalid or revoked."

        return VerificationResult(
            provider=self.provider_name,
            verification_type=verification_type,
            identifier=ref_num,
            status=status_val,
            verified_data=verified_data,
            source="MOCK_OEM_AUTHORIZATION",
            message=msg,
        )
