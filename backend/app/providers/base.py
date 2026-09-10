from abc import ABC, abstractmethod

from app.providers.schemas import (
    ProviderAvailability,
    ProviderCapability,
    SourceMode,
    VerificationRequest,
    VerificationResult,
)


class VerificationProvider(ABC):
    """
    Contract implemented by every verification adapter.

    Providers retrieve/verify facts from a configured source.
    They do not perform tender compliance evaluation, scoring,
    risk classification, or final qualification decisions.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Stable provider identifier used for persistence and auditing."""
        raise NotImplementedError

    @property
    @abstractmethod
    def supported_verification_types(self) -> set[str]:
        """Verification types handled by this provider."""
        raise NotImplementedError

    @property
    def source_mode(self) -> SourceMode:
        """Provenance of the underlying adapter. Default is SYNTHETIC unless overridden."""
        return SourceMode.SYNTHETIC

    @property
    def capability(self) -> ProviderCapability:
        """Exposes connector capability metadata."""
        is_live = self.source_mode in (SourceMode.OFFICIAL_API, SourceMode.AUTHORIZED_PROVIDER)
        avail = (
            ProviderAvailability.AVAILABLE
            if self.source_mode == SourceMode.SYNTHETIC
            else (ProviderAvailability.AVAILABLE if is_live else ProviderAvailability.CONFIGURATION_REQUIRED)
        )
        return ProviderCapability(
            provider_name=self.provider_name,
            supported_verification_types=sorted(list(self.supported_verification_types)),
            source_mode=self.source_mode,
            availability=avail,
            is_live=is_live,
            requires_manual=self.source_mode == SourceMode.MANUAL,
            description=f"{self.provider_name} connector operating in {self.source_mode.value} mode",
        )

    def supports(self, verification_type: str) -> bool:
        """Return whether this provider supports the requested verification."""
        return verification_type.upper() in {
            item.upper()
            for item in self.supported_verification_types
        }

    @abstractmethod
    def verify(
        self,
        request: VerificationRequest,
    ) -> VerificationResult:
        """Perform verification and return a normalized result."""
        raise NotImplementedError