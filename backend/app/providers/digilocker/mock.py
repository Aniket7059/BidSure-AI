from app.providers.digilocker.provider import (
    DigiLockerVerificationAdapter,
    DigiLockerVerificationRecord,
)


class MockDigiLockerVerificationAdapter(DigiLockerVerificationAdapter):
    """
    Deterministic development adapter for DigiLocker document verification.
    Clearly marked as synthetic mock data.
    """

    def __init__(self, records: dict[str, DigiLockerVerificationRecord] | None = None) -> None:
        self._records = records or {
            "in.gov.digilocker.doc.12345": DigiLockerVerificationRecord(
                digilocker_uri="in.gov.digilocker.doc.12345",
                document_type="INCORPORATION_CERTIFICATE",
                document_name="Certificate of Incorporation",
                issuer_name="Ministry of Corporate Affairs (MCA)",
                issuer_id="in.gov.mca",
                digital_signature_valid=True,
                verification_status="VERIFIED",
            ),
            "in.gov.digilocker.doc.INVALID": DigiLockerVerificationRecord(
                digilocker_uri="in.gov.digilocker.doc.INVALID",
                document_type="UNKNOWN",
                document_name="Corrupted Document",
                issuer_name="UNKNOWN ISSUER",
                issuer_id="unknown",
                digital_signature_valid=False,
                verification_status="UNVERIFIED",
            ),
        }

    def verify_digilocker_document(self, digilocker_uri_or_id: str) -> DigiLockerVerificationRecord | None:
        if digilocker_uri_or_id in self._records:
            return self._records[digilocker_uri_or_id]

        if "digilocker" in digilocker_uri_or_id.lower() or "doc" in digilocker_uri_or_id.lower():
            return DigiLockerVerificationRecord(
                digilocker_uri=digilocker_uri_or_id,
                document_type="STATUTORY_CERTIFICATE",
                document_name="DigiLocker Verified Statutory Document",
                issuer_name="Government of India DigiLocker Portal",
                issuer_id="in.gov.digilocker",
                digital_signature_valid=True,
                verification_status="VERIFIED",
            )
        return None
