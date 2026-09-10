from enum import Enum


class RequirementType(str, Enum):
    """
    Canonical requirement taxonomy across BidSure AI.

    Used by:
    - RAG requirement generation & extraction
    - Database models (TenderRequirement, ComplianceCheck)
    - Verification Providers (GST, PAN, Udyam, etc.)
    - Requirement Evaluators & Compliance Engine
    """

    GST = "GST"
    UDYAM = "UDYAM"
    PAN = "PAN"
    INCOME_TAX = "INCOME_TAX"
    EPFO = "EPFO"
    ESIC = "ESIC"
    STARTUP_INDIA = "STARTUP_INDIA"
    NSIC = "NSIC"
    OEM_AUTHORIZATION = "OEM_AUTHORIZATION"
    MAKE_IN_INDIA = "MAKE_IN_INDIA"
    MCA21 = "MCA21"
    DIGILOCKER = "DIGILOCKER"
    DEBARMENT = "DEBARMENT"
    OTHER = "OTHER"
