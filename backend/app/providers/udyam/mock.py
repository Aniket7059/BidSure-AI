from app.providers.udyam.provider import (
    UdyamVerificationAdapter,
    UdyamVerificationRecord,
)


class MockUdyamVerificationAdapter(UdyamVerificationAdapter):
    """
    Deterministic development adapter for Udyam verification.
    """

    def __init__(self, records: dict[str, UdyamVerificationRecord] | None = None) -> None:
        self._records = records or {
            "UDYAM-MH-01-0012345": UdyamVerificationRecord(
                udyam_number="UDYAM-MH-01-0012345",
                enterprise_name="ABC INDUSTRIES PRIVATE LIMITED",
                organisation_type="Private Limited Company",
                enterprise_type="MICRO",
                major_activity="SERVICES",
                registration_date="2021-05-10",
                status="ACTIVE",
            ),
            "UDYAM-DL-02-0098765": UdyamVerificationRecord(
                udyam_number="UDYAM-DL-02-0098765",
                enterprise_name="DEMO ENGINEERING PRIVATE LIMITED",
                organisation_type="Private Limited Company",
                enterprise_type="SMALL",
                major_activity="MANUFACTURING",
                registration_date="2020-09-15",
                status="ACTIVE",
            ),
        }

    def verify_udyam(self, udyam_number: str) -> UdyamVerificationRecord | None:
        return self._records.get(udyam_number)
