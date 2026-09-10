from app.providers.oem_authorization.provider import (
    OEMAuthorizationAdapter,
    OEMAuthorizationRecord,
)


class MockOEMAuthorizationVerificationAdapter(OEMAuthorizationAdapter):
    """
    Deterministic development adapter for OEM Authorization.
    Clearly marked as synthetic mock data.
    """

    def __init__(self, records: dict[str, OEMAuthorizationRecord] | None = None) -> None:
        self._records = records or {
            "OEM-AUTH-1001": OEMAuthorizationRecord(
                authorization_reference_number="OEM-AUTH-1001",
                oem_name="GLOBAL TECH HARDWARE OEM INC",
                authorized_bidder_name="ABC INDUSTRIES PRIVATE LIMITED",
                product_category="SERVERS & NETWORKING",
                issue_date="2023-01-10",
                valid_until="2025-12-31",
                authorization_status="VALID",
            ),
            "OEM-AUTH-EXPIRED": OEMAuthorizationRecord(
                authorization_reference_number="OEM-AUTH-EXPIRED",
                oem_name="LEGACY HARDWARE OEM LLC",
                authorized_bidder_name="DEMO ENGINEERING PRIVATE LIMITED",
                product_category="STORAGE UNITS",
                issue_date="2020-01-01",
                valid_until="2022-12-31",
                authorization_status="EXPIRED",
            ),
        }

    def verify_oem_authorization(self, reference_number: str) -> OEMAuthorizationRecord | None:
        if reference_number in self._records:
            return self._records[reference_number]
        # Return valid mock record for any recognized reference pattern
        if "OEM" in reference_number or "AUTH" in reference_number:
            return OEMAuthorizationRecord(
                authorization_reference_number=reference_number,
                oem_name="AUTHORIZED OEM ENTERPRISE",
                authorized_bidder_name="QUALIFIED BIDDER",
                product_category="EQUIPMENT",
                issue_date="2023-06-01",
                valid_until="2026-12-31",
                authorization_status="VALID",
            )
        return None
