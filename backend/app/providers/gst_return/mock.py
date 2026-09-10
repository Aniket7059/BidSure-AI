from app.providers.gst_return.provider import (
    GSTReturnVerificationAdapter,
    GSTReturnVerificationRecord,
)


class MockGSTReturnVerificationAdapter(GSTReturnVerificationAdapter):
    """
    Deterministic development adapter for GST Return filings.
    Clearly marked as synthetic mock data.
    """

    def __init__(self, records: dict[str, GSTReturnVerificationRecord] | None = None) -> None:
        self._records = records or {
            "27ABCDE1234F1Z5": GSTReturnVerificationRecord(
                gstin="27ABCDE1234F1Z5",
                return_type="GSTR-3B",
                financial_year="2023-24",
                tax_period="MARCH",
                filing_date="2024-04-15",
                filing_status="FILED",
                arn_acknowledgement_number="AA2703241234567",
            ),
            "29ABCDE1234F1Z6": GSTReturnVerificationRecord(
                gstin="29ABCDE1234F1Z6",
                return_type="GSTR-3B",
                financial_year="2023-24",
                tax_period="MARCH",
                filing_date=None,
                filing_status="NOT_FILED",
                arn_acknowledgement_number=None,
            ),
        }

    def verify_gst_return(self, gstin: str) -> GSTReturnVerificationRecord | None:
        return self._records.get(gstin)
