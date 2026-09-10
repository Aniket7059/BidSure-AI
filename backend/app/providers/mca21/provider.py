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


# Standard 21-character Corporate Identification Number format (e.g. U12345MH2020PTC123456)
CIN_PATTERN = re.compile(r"^[LU][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$")


class MCA21VerificationRecord(BaseModel):
    """Normalized facts returned by an MCA21 corporate verification source."""

    model_config = ConfigDict(extra="forbid")

    cin: str
    company_name: str | None = None
    company_status: str | None = None  # ACTIVE, STRUCK_OFF, AMALGAMATED
    date_of_incorporation: str | None = None
    authorized_capital_inr: float | None = None
    paid_up_capital_inr: float | None = None
    active_directors: list[str] | None = None


class MCA21VerificationAdapter(ABC):
    """Source adapter used by the MCA21 corporate provider."""

    @abstractmethod
    def verify_cin(self, cin: str) -> MCA21VerificationRecord | None:
        raise NotImplementedError


class MCA21VerificationProvider(VerificationProvider):
    """MCA21 Corporate & Company registration verification provider."""

    def __init__(self, adapter: MCA21VerificationAdapter) -> None:
        self._adapter = adapter

    @property
    def provider_name(self) -> str:
        return "MCA21"

    @property
    def supported_verification_types(self) -> set[str]:
        return {
            RequirementType.MCA21.value,
            "MCA21_CORPORATE_CHECK",
            "CIN_VERIFICATION",
        }

    def verify(self, request: VerificationRequest) -> VerificationResult:
        verification_type = request.verification_type.upper().strip()
        cin = request.identifier.strip().upper()

        if not self.supports(verification_type):
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=cin,
                status=VerificationStatus.NOT_APPLICABLE,
                message=(
                    f"MCA21 provider does not support verification type: "
                    f"{verification_type}"
                ),
            )

        if not CIN_PATTERN.fullmatch(cin):
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=cin,
                status=VerificationStatus.NOT_VERIFIED,
                message="CIN format is invalid. Must be 21 characters (e.g. U12345MH2020PTC123456).",
            )

        try:
            record = self._adapter.verify_cin(cin)
        except Exception as exc:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=cin,
                status=VerificationStatus.ERROR,
                message="MCA21 registry could not be reached.",
                error_message=str(exc),
            )

        if record is None:
            return VerificationResult(
                provider=self.provider_name,
                verification_type=verification_type,
                identifier=cin,
                status=VerificationStatus.NOT_FOUND,
                message="Corporate Identification Number (CIN) was not found in MCA21 registry.",
            )

        verified_data = record.model_dump(exclude_none=True)

        return VerificationResult(
            provider=self.provider_name,
            verification_type=verification_type,
            identifier=cin,
            status=VerificationStatus.VERIFIED,
            verified_data=verified_data,
            message="MCA21 corporate filing and active director details were successfully verified.",
        )
