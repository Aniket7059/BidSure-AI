from app.providers.make_in_india.provider import (
    MakeInIndiaVerificationAdapter,
    MakeInIndiaVerificationRecord,
)


class MockMakeInIndiaVerificationAdapter(MakeInIndiaVerificationAdapter):
    """
    Deterministic development adapter for Make In India / Local Content verification.
    Clearly marked as synthetic mock data.
    """

    def __init__(self, records: dict[str, MakeInIndiaVerificationRecord] | None = None) -> None:
        self._records = records or {
            "MII-DECL-123": MakeInIndiaVerificationRecord(
                identifier="MII-DECL-123",
                bidder_name="ABC INDUSTRIES PRIVATE LIMITED",
                local_content_percentage=65.0,
                supplier_class="CLASS_1_LOCAL_SUPPLIER",
                location_of_value_addition="MUMBAI, MAHARASHTRA",
                declaration_status="VERIFIED",
            ),
            "MII-DECL-456": MakeInIndiaVerificationRecord(
                identifier="MII-DECL-456",
                bidder_name="DEMO ENGINEERING PRIVATE LIMITED",
                local_content_percentage=15.0,
                supplier_class="NON_LOCAL_SUPPLIER",
                location_of_value_addition="OVERSEAS",
                declaration_status="VERIFIED",
            ),
        }

    def verify_local_content(self, identifier: str) -> MakeInIndiaVerificationRecord | None:
        if identifier in self._records:
            return self._records[identifier]
        # Fallback default for any non-empty MII reference
        return MakeInIndiaVerificationRecord(
            identifier=identifier,
            bidder_name="VERIFIED BIDDER",
            local_content_percentage=60.0,
            supplier_class="CLASS_1_LOCAL_SUPPLIER",
            location_of_value_addition="INDIA",
            declaration_status="VERIFIED",
        )
