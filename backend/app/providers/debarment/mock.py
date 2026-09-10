from app.providers.debarment.provider import (
    DebarmentVerificationAdapter,
    DebarmentVerificationRecord,
)


class MockDebarmentVerificationAdapter(DebarmentVerificationAdapter):
    """
    Deterministic development adapter for debarment/blacklisting check.
    """

    def __init__(self, records: dict[str, DebarmentVerificationRecord] | None = None) -> None:
        self._records = records or {
            "DEBAR1234F": DebarmentVerificationRecord(
                identifier="DEBAR1234F",
                is_debarred=True,
                debarment_status="DEBARRED",
                debarring_agency="GeM Central Incident Management",
                debarment_period="2023-01-01 to 2026-12-31",
                reason="Submission of forged compliance document in Tender GEM/2023/B/1002.",
            ),
            "BLACK9999Z": DebarmentVerificationRecord(
                identifier="BLACK9999Z",
                is_debarred=True,
                debarment_status="SUSPENDED",
                debarring_agency="Ministry of Petroleum Audit Wing",
                debarment_period="2024-06-01 to 2025-06-01",
                reason="Non-performance & contractual breach.",
            ),
        }

    def check_debarment(self, identifier: str) -> DebarmentVerificationRecord | None:
        return self._records.get(identifier)
