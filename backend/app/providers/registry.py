from app.core.taxonomy import RequirementType
from app.providers.base import VerificationProvider

# Mapping from canonical RequirementType / legacy names to target provider search keys
VERIFICATION_TYPE_ALIASES: dict[str, str] = {
    "GST": "GST_REGISTRATION",
    "GST_RETURN": "GST_RETURN_FILING",
    "GST_RETURN_FILING": "GST_RETURN_FILING",
    "PAN": "PAN_VERIFICATION",
    "INCOME_TAX": "INCOME_TAX_COMPLIANCE",
    "INCOME_TAX_COMPLIANCE": "INCOME_TAX_COMPLIANCE",
    "ITR": "INCOME_TAX_COMPLIANCE",
    "UDYAM": "UDYAM_VERIFICATION",
    "MCA21": "MCA21_CORPORATE_CHECK",
    "DEBARMENT": "DEBARMENT_VERIFICATION",
    "BLACKLISTING": "DEBARMENT_VERIFICATION",
    "EPFO": "EPFO_COMPLIANCE",
    "ESIC": "ESIC_COMPLIANCE",
    "EPFO_ESIC": "EPFO_COMPLIANCE",
    "STARTUP_INDIA": "STARTUP_INDIA_CHECK",
    "NSIC": "NSIC_VERIFICATION",
    "STARTUP_NSIC": "STARTUP_INDIA_CHECK",
    "OEM_AUTHORIZATION": "OEM_AUTHORIZATION",
    "OEM": "OEM_AUTHORIZATION",
    "MAKE_IN_INDIA": "MAKE_IN_INDIA",
    "LOCAL_CONTENT": "MAKE_IN_INDIA",
    "DIGILOCKER": "DIGILOCKER_VERIFICATION",
    "DIGILOCKER_DOCUMENT": "DIGILOCKER_VERIFICATION",
}


class ProviderRegistry:
    """Registry that maps verification types and canonical RequirementTypes to provider adapters."""

    def __init__(self) -> None:
        self._providers: dict[str, VerificationProvider] = {}

    def register(
        self,
        provider: VerificationProvider,
    ) -> None:
        """Register all verification types supported by a provider."""

        for verification_type in provider.supported_verification_types:
            key = str(verification_type).upper()

            if key in self._providers:
                raise ValueError(
                    "Verification provider already registered for "
                    f"type: {key}"
                )

            self._providers[key] = provider

    def get(
        self,
        verification_type: str | RequirementType,
    ) -> VerificationProvider | None:
        """Return the provider registered for a verification type or canonical RequirementType."""

        if hasattr(verification_type, "value"):
            raw_key = str(verification_type.value).upper().strip()
        else:
            raw_key = str(verification_type).upper().strip()

        if raw_key.startswith("REQUIREMENTTYPE."):
            raw_key = raw_key.split(".")[-1]

        # Direct match
        if raw_key in self._providers:
            return self._providers[raw_key]

        # Alias lookup
        mapped = VERIFICATION_TYPE_ALIASES.get(raw_key)
        if mapped and mapped in self._providers:
            return self._providers[mapped]

        return None

    def clear(self) -> None:
        """Clear registrations; useful for isolated tests."""
        self._providers.clear()


provider_registry = ProviderRegistry()