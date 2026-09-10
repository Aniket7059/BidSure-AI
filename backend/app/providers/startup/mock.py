from app.providers.startup.provider import (
    StartupNSICVerificationAdapter,
    StartupNSICVerificationRecord,
)


class MockStartupNSICVerificationAdapter(StartupNSICVerificationAdapter):
    """
    Deterministic development adapter for Startup India & NSIC verification.
    """

    def __init__(self, records: dict[str, StartupNSICVerificationRecord] | None = None) -> None:
        self._records = records or {
            "DPIIT12345": StartupNSICVerificationRecord(
                registration_number="DPIIT12345",
                entity_name="ABC TECH INNOVATIONS PRIVATE LIMITED",
                scheme_type="DPIIT_STARTUP",
                valid_until="2028-12-31",
                emd_exemption_eligible=True,
                turnover_exemption_eligible=True,
            ),
            "NSIC98765": StartupNSICVerificationRecord(
                registration_number="NSIC98765",
                entity_name="DEMO ENGINEERING PRIVATE LIMITED",
                scheme_type="NSIC_SINGLE_POINT",
                valid_until="2027-06-30",
                emd_exemption_eligible=True,
                turnover_exemption_eligible=False,
            ),
        }

    def verify_registration(self, number: str) -> StartupNSICVerificationRecord | None:
        return self._records.get(number)
