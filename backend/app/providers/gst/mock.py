from app.providers.gst.provider import GSTVerificationAdapter, GSTVerificationRecord


class MockGSTVerificationAdapter(GSTVerificationAdapter):
    """
    Deterministic development adapter.

    These records are synthetic test data. They are not live GSTN data and
    must never be presented as government verification results in production.
    """

    def __init__(self, records: dict[str, GSTVerificationRecord] | None = None) -> None:
        self._records = records or {
            "27ABCDE1234F1Z5": GSTVerificationRecord(
                gstin="27ABCDE1234F1Z5",
                legal_name="ABC INDUSTRIES PRIVATE LIMITED",
                trade_name="ABC Industries",
                registration_status="ACTIVE",
                registration_date="2022-04-01",
                return_filing_status="COMPLIANT",
            ),
            "29ABCDE1234F1Z6": GSTVerificationRecord(
                gstin="29ABCDE1234F1Z6",
                legal_name="DEMO ENGINEERING PRIVATE LIMITED",
                trade_name="Demo Engineering",
                registration_status="ACTIVE",
                registration_date="2021-07-15",
                return_filing_status="NON_COMPLIANT",
            ),
            "07ABCDE1234F1Z7": GSTVerificationRecord(
                gstin="07ABCDE1234F1Z7",
                legal_name="INACTIVE DEMO PRIVATE LIMITED",
                trade_name="Inactive Demo",
                registration_status="INACTIVE",
                registration_date="2020-04-10",
                return_filing_status="COMPLIANT",
            ),
        }

    def verify_gstin(self, gstin: str) -> GSTVerificationRecord | None:
        return self._records.get(gstin)
