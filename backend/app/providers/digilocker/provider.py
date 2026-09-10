from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict

from app.core.taxonomy import RequirementType
from app.providers.base import VerificationProvider
from app.providers.schemas import (
    VerificationRequest,
    VerificationResult,
    VerificationStatus,
)


class DigiLockerVerificationRecord(BaseModel):
    """Facts returned by a DigiLocker verification adapter."""

    model_config = ConfigDict(extra="forbid")

    digilocker_uri: str
    document_type: str | None = None
    document_name: str | None = None
    issuer_name: str | None = None
    issuer_id: str | None = None
    digital_signature_valid: bool = True
    verification_status: str = "VERIFIED"  # VERIFIED, UNVERIFIED, EXPIRED, MISMATCH


class DigiLockerVerificationAdapter(ABC):
    """Adapter interface for DigiLocker document verification."""

    @abstractmethod
    def verify_digilocker_document(self, digilocker_uri_or_id: str) -> DigiLockerVerificationRecord | None:
        raise NotImplementedError


class DigiLockerVerificationProvider(VerificationProvider):
    """Provider specifically handling DigiLocker document verification."""

    def __init__(self, adapter: DigiLockerVerificationAdapter) -> None:
        self._adapter = adapter

    @property
    def provider_name(self) -> str:
        return "DIGILOCKER"

    @property
    def supported_verification_types(self) -> set[str]:
        return {
            RequirementType.DIGILOCKER.value,
            "DIGILOCKER_DOCUMENT",
            "DIGILOCKER_VERIFICATION",
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
                message=f"DigiLocker provider does not support verification type: {verification_type}",
            )

        if not identifier or identifier in ("NONE", "MISSING", "UNKNOWN"):
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=identifier,
                status=VerificationStatus.NOT_FOUND,
                message="No DigiLocker URI or document reference provided.",
            )

        try:
            record = self._adapter.verify_digilocker_document(identifier)
        except Exception as exc:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=identifier,
                status=VerificationStatus.ERROR,
                message="DigiLocker verification source could not be reached.",
                error_message=str(exc),
            )

        if record is None:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=identifier,
                status=VerificationStatus.NOT_FOUND,
                message="DigiLocker document reference was not found in verification source.",
            )

        verified_data = record.model_dump(exclude_none=True)
        is_valid = record.digital_signature_valid and record.verification_status == "VERIFIED"

        return VerificationResult(
            provider=self.provider_name,
            verification_type=verification_type,
            identifier=identifier,
            status=VerificationStatus.VERIFIED if is_valid else VerificationStatus.MISMATCH,
            verified_data=verified_data,
            source="MOCK_DIGILOCKER",
            message="DigiLocker document signature and issuer verification completed.",
        )
