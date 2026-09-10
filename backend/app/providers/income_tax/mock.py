from app.providers.income_tax.provider import (
    IncomeTaxVerificationAdapter,
    IncomeTaxVerificationRecord,
)


class MockIncomeTaxVerificationAdapter(IncomeTaxVerificationAdapter):
    """
    Deterministic development adapter for Income Tax compliance.
    Clearly marked as synthetic mock data.
    """

    def __init__(self, records: dict[str, IncomeTaxVerificationRecord] | None = None) -> None:
        self._records = records or {
            "ABCDE1234F": IncomeTaxVerificationRecord(
                pan_number="ABCDE1234F",
                assessment_year="2023-24",
                itr_filed=True,
                acknowledgement_number="ITR202312345678",
                filing_date="2023-10-15",
                gross_total_income=5000000.0,
                tax_compliance_status="COMPLIANT",
            ),
            "FGHIJ5678K": IncomeTaxVerificationRecord(
                pan_number="FGHIJ5678K",
                assessment_year="2023-24",
                itr_filed=False,
                acknowledgement_number=None,
                filing_date=None,
                gross_total_income=0.0,
                tax_compliance_status="NON_COMPLIANT",
            ),
        }

    def verify_income_tax(self, pan_number: str) -> IncomeTaxVerificationRecord | None:
        return self._records.get(pan_number)
