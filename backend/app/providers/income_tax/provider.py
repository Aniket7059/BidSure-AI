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

PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


class IncomeTaxVerificationRecord(BaseModel):
    """Facts returned by an Income Tax / ITR compliance verification source."""

    model_config = ConfigDict(extra="forbid")

    pan_number: str
    assessment_year: str | None = "2023-24"
    itr_filed: bool = True
    acknowledgement_number: str | None = None
    filing_date: str | None = None
    gross_total_income: float | None = None
    tax_compliance_status: str | None = "COMPLIANT"


class IncomeTaxVerificationAdapter(ABC):
    """Adapter interface for Income Tax compliance verification."""

    @abstractmethod
    def verify_income_tax(self, pan_number: str) -> IncomeTaxVerificationRecord | None:
        raise NotImplementedError


class IncomeTaxVerificationProvider(VerificationProvider):
    """Provider specifically handling Income Tax / ITR compliance verification."""

    def __init__(self, adapter: IncomeTaxVerificationAdapter) -> None:
        self._adapter = adapter

    @property
    def provider_name(self) -> str:
        return "INCOME_TAX"

    @property
    def supported_verification_types(self) -> set[str]:
        return {
            RequirementType.INCOME_TAX.value,
            "INCOME_TAX_COMPLIANCE",
            "ITR",
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
                message=f"Income Tax provider does not support verification type: {verification_type}",
            )

        if not PAN_PATTERN.fullmatch(pan):
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=pan,
                status=VerificationStatus.NOT_VERIFIED,
                message="PAN format is invalid for Income Tax check.",
            )

        try:
            record = self._adapter.verify_income_tax(pan)
        except Exception as exc:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=pan,
                status=VerificationStatus.ERROR,
                message="Income Tax verification source could not be reached.",
                error_message=str(exc),
            )

        if record is None:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=pan,
                status=VerificationStatus.NOT_FOUND,
                message="Income Tax record was not found in the configured source.",
            )

        verified_data = record.model_dump(exclude_none=True)
        return VerificationResult(
            provider=self.provider_name,
            verification_type=verification_type,
            identifier=pan,
            status=VerificationStatus.VERIFIED if record.itr_filed else VerificationStatus.MISMATCH,
            verified_data=verified_data,
            source="MOCK_INCOME_TAX",
            message="Income Tax filing compliance details retrieved successfully.",
        )
