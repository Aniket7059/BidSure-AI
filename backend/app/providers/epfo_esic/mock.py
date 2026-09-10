from app.providers.epfo_esic.provider import (
    EPFOESICVerificationAdapter,
    EPFOESICVerificationRecord,
)


class MockEPFOESICVerificationAdapter(EPFOESICVerificationAdapter):
    """
    Deterministic development adapter for EPFO & ESIC verification.
    """

    def __init__(self, records: dict[str, EPFOESICVerificationRecord] | None = None) -> None:
        self._records = records or {
            "EPFO1234567": EPFOESICVerificationRecord(
                establishment_code="EPFO1234567",
                establishment_name="ABC INDUSTRIES PRIVATE LIMITED",
                coverage_status="ACTIVE",
                monthly_filing_status="COMPLIANT",
                last_ecr_month="2026-08",
                active_member_count=142,
            ),
            "ESIC9876543": EPFOESICVerificationRecord(
                establishment_code="ESIC9876543",
                establishment_name="DEMO ENGINEERING PRIVATE LIMITED",
                coverage_status="ACTIVE",
                monthly_filing_status="COMPLIANT",
                last_ecr_month="2026-08",
                active_member_count=88,
            ),
        }

    def verify_establishment(self, establishment_code: str) -> EPFOESICVerificationRecord | None:
        return self._records.get(establishment_code)
