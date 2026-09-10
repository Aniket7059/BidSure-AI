from app.providers.pan.provider import (
    PANVerificationAdapter,
    PANVerificationRecord,
)


class MockPANVerificationAdapter(PANVerificationAdapter):
    """
    Deterministic development adapter for PAN verification.
    Contains synthetic test records.
    """

    def __init__(self, records: dict[str, PANVerificationRecord] | None = None) -> None:
        self._records = records or {
            "ABCDE1234F": PANVerificationRecord(
                pan_number="ABCDE1234F",
                name="ABC INDUSTRIES PRIVATE LIMITED",
                category="COMPANY",
                status="ACTIVE",
                last_itr_filed_year="2024-25",
                tax_compliance_status="COMPLIANT",
            ),
            "DEMOP5678G": PANVerificationRecord(
                pan_number="DEMOP5678G",
                name="DEMO ENGINEERING PRIVATE LIMITED",
                category="COMPANY",
                status="ACTIVE",
                last_itr_filed_year="2023-24",
                tax_compliance_status="COMPLIANT",
            ),
            "INACT9999H": PANVerificationRecord(
                pan_number="INACT9999H",
                name="INACTIVE ENTERPRISES",
                category="FIRM",
                status="INOPERATIVE",
                last_itr_filed_year="2021-22",
                tax_compliance_status="NON_COMPLIANT",
            ),
        }

    def verify_pan(self, pan: str) -> PANVerificationRecord | None:
        return self._records.get(pan)
