from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.taxonomy import RequirementType


class SourceMode(str, Enum):
    """
    Provenance of a verification provider adapter.

    OFFICIAL_API: Direct official government API endpoint.
    AUTHORIZED_PROVIDER: Authorized provider/GSP/ASP API aggregator.
    MANUAL: Human-in-the-loop manual verification by Procurement Officer.
    SYNTHETIC: Development, testing, or demonstration mock adapter.
    """

    OFFICIAL_API = "OFFICIAL_API"
    AUTHORIZED_PROVIDER = "AUTHORIZED_PROVIDER"
    MANUAL = "MANUAL"
    SYNTHETIC = "SYNTHETIC"


class ProviderAvailability(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    CONFIGURATION_REQUIRED = "CONFIGURATION_REQUIRED"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    SYNTHETIC_ONLY = "SYNTHETIC_ONLY"


class ProviderCapability(BaseModel):
    """Exposes capability metadata for a registered verification connector."""

    model_config = ConfigDict(extra="ignore")

    provider_name: str
    supported_verification_types: list[str]
    source_mode: SourceMode
    availability: ProviderAvailability
    is_live: bool = False
    requires_manual: bool = False
    description: str | None = None
    configured_environment: str = "DEFAULT"


class VerificationStatus(str, Enum):
    """
    Normalized outcome of a verification attempt.

    These statuses describe the verification operation itself.
    They are separate from compliance decisions such as PASS/FAIL.
    """

    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    NOT_FOUND = "NOT_FOUND"
    MISMATCH = "MISMATCH"
    PENDING = "PENDING"
    ERROR = "ERROR"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class VerificationRequest(BaseModel):
    """Input required by a verification provider."""

    model_config = ConfigDict(extra="forbid")

    identifier: str = Field(min_length=1, max_length=255)
    verification_type: str = Field(min_length=1, max_length=100)


def map_to_requirement_type(raw_type: str | None) -> str:
    """Map raw verification_type or provider name to canonical RequirementType string."""
    if not raw_type:
        return RequirementType.OTHER.value
    cleaned = str(raw_type).upper().strip()

    # Direct match with canonical enum values
    for req_enum in RequirementType:
        if req_enum.value == cleaned:
            return req_enum.value

    mapping = {
        "GST_REGISTRATION": RequirementType.GST.value,
        "GST_RETURN_FILING": RequirementType.GST.value,
        "GST_CERTIFICATE": RequirementType.GST.value,
        "GST_RETURN": RequirementType.GST.value,
        "PAN_VERIFICATION": RequirementType.PAN.value,
        "PAN_CARD": RequirementType.PAN.value,
        "UDYAM_VERIFICATION": RequirementType.UDYAM.value,
        "UDYAM_CERTIFICATE": RequirementType.UDYAM.value,
        "MSME_CATEGORY_CHECK": RequirementType.UDYAM.value,
        "INCOME_TAX_COMPLIANCE": RequirementType.INCOME_TAX.value,
        "ITR": RequirementType.INCOME_TAX.value,
        "INCOME_TAX": RequirementType.INCOME_TAX.value,
        "MCA21_CORPORATE_CHECK": RequirementType.MCA21.value,
        "CIN_VERIFICATION": RequirementType.MCA21.value,
        "DEBARMENT_VERIFICATION": RequirementType.DEBARMENT.value,
        "BLACK_LISTING_CHECK": RequirementType.DEBARMENT.value,
        "BLACKLISTING_DEBARMENT": RequirementType.DEBARMENT.value,
        "EPFO_COMPLIANCE": RequirementType.EPFO.value,
        "ESIC_COMPLIANCE": RequirementType.ESIC.value,
        "EPFO_ESIC": RequirementType.EPFO.value,
        "STARTUP_INDIA_CHECK": RequirementType.STARTUP_INDIA.value,
        "NSIC_VERIFICATION": RequirementType.NSIC.value,
        "STARTUP_NSIC": RequirementType.STARTUP_INDIA.value,
        "OEM": RequirementType.OEM_AUTHORIZATION.value,
        "OEM_AUTHORIZATION_LETTER": RequirementType.OEM_AUTHORIZATION.value,
        "OEM_AUTHORIZATION": RequirementType.OEM_AUTHORIZATION.value,
        "LOCAL_CONTENT": RequirementType.MAKE_IN_INDIA.value,
        "MAKE_IN_INDIA_DECLARATION": RequirementType.MAKE_IN_INDIA.value,
        "MAKE_IN_INDIA": RequirementType.MAKE_IN_INDIA.value,
        "DIGILOCKER": RequirementType.DIGILOCKER.value,
        "DIGILOCKER_DOCUMENT": RequirementType.DIGILOCKER.value,
        "DIGILOCKER_VERIFICATION": RequirementType.DIGILOCKER.value,
    }
    if cleaned in mapping:
        return mapping[cleaned]

    if "GST" in cleaned:
        return RequirementType.GST.value
    if "UDYAM" in cleaned:
        return RequirementType.UDYAM.value
    if "PAN" in cleaned:
        return RequirementType.PAN.value
    if "EPFO" in cleaned:
        return RequirementType.EPFO.value
    if "ESIC" in cleaned:
        return RequirementType.ESIC.value
    if "STARTUP" in cleaned:
        return RequirementType.STARTUP_INDIA.value
    if "NSIC" in cleaned:
        return RequirementType.NSIC.value
    if "OEM" in cleaned:
        return RequirementType.OEM_AUTHORIZATION.value
    if "MAKE" in cleaned or "LOCAL" in cleaned:
        return RequirementType.MAKE_IN_INDIA.value
    if "DEBAR" in cleaned or "BLACK" in cleaned:
        return RequirementType.DEBARMENT.value

    return RequirementType.OTHER.value


class VerificationResult(BaseModel):
    """
    Standardized provider output consumed by the rest of the backend.

    Standardized structure:
    {
      "requirement_type": "GST",
      "identifier": "27ABCDE1234F1Z...",
      "status": "VERIFIED",
      "verified_data": {
        "gstin": "...",
        "legal_name": "...",
        "registration_status": "ACTIVE"
      },
      "source": "GST",
      "checked_at": "..."
    }
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    requirement_type: str = ""
    identifier: str = Field(min_length=1, max_length=255)
    status: VerificationStatus
    verified_data: dict[str, Any] | None = None
    source: str = ""
    source_mode: SourceMode = SourceMode.SYNTHETIC
    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Legacy/Tracking fields maintained for database and provider compatibility
    provider: str = Field(default="")
    verification_type: str = Field(default="")
    message: str | None = None
    error_message: str | None = None

    @model_validator(mode="after")
    def populate_standardized_fields(self):
        # Sync source and provider
        if not self.source and self.provider:
            self.source = self.provider
        elif not self.provider and self.source:
            self.provider = self.source

        # Sync requirement_type and verification_type
        if not self.requirement_type:
            raw = self.verification_type or self.provider or self.source
            self.requirement_type = map_to_requirement_type(raw)

        if not self.verification_type:
            self.verification_type = self.requirement_type

        return self