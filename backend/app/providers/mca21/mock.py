from app.providers.mca21.provider import (
    MCA21VerificationAdapter,
    MCA21VerificationRecord,
)


class MockMCA21VerificationAdapter(MCA21VerificationAdapter):
    """
    Deterministic development adapter for MCA21 verification.
    """

    def __init__(self, records: dict[str, MCA21VerificationRecord] | None = None) -> None:
        self._records = records or {
            "U74999MH2018PTC301234": MCA21VerificationRecord(
                cin="U74999MH2018PTC301234",
                company_name="ABC INDUSTRIES PRIVATE LIMITED",
                company_status="ACTIVE",
                date_of_incorporation="2018-04-12",
                authorized_capital_inr=5000000.0,
                paid_up_capital_inr=1000000.0,
                active_directors=["01234567", "08901234"],
            ),
            "U27100DL2015PTC209876": MCA21VerificationRecord(
                cin="U27100DL2015PTC209876",
                company_name="DEMO ENGINEERING PRIVATE LIMITED",
                company_status="ACTIVE",
                date_of_incorporation="2015-08-20",
                authorized_capital_inr=10000000.0,
                paid_up_capital_inr=5000000.0,
                active_directors=["05678901"],
            ),
        }

    def verify_cin(self, cin: str) -> MCA21VerificationRecord | None:
        return self._records.get(cin)
