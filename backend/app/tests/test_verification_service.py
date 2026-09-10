from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.models import (  # noqa: F401
    BidDocument,
    BidSubmission,
    Bidder,
    Tender,
    TenderRequirement,
    VerificationResult as VerificationResultModel,
)
from app.providers.base import VerificationProvider
from app.providers.registry import ProviderRegistry
from app.providers.schemas import (
    VerificationRequest,
    VerificationResult,
    VerificationStatus,
)
from app.services.verification_service import VerificationService


class FakeProvider(VerificationProvider):
    @property
    def provider_name(self) -> str:
        return "FAKE"

    @property
    def supported_verification_types(self) -> set[str]:
        return {"GST_REGISTRATION"}

    def verify(self, request: VerificationRequest) -> VerificationResult:
        return VerificationResult(
            provider=self.provider_name,
            verification_type=request.verification_type.upper(),
            identifier=request.identifier.strip().upper(),
            status=VerificationStatus.VERIFIED,
            verified_data={"gstin": request.identifier.strip().upper()},
            message="Synthetic verification result.",
            checked_at=datetime.now(timezone.utc),
        )


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_submission(db):
    bidder = Bidder(company_name="Demo Bidder")
    db.add(bidder)
    db.flush()

    tender = Tender(title="Demo Tender", reference_number=f"DEMO-REF-{uuid4().hex[:12]}")
    db.add(tender)
    db.flush()

    submission = BidSubmission(
        tender_id=tender.id,
        bidder_id=bidder.id,
        status="SUBMITTED",
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def test_verification_is_persisted(db):
    submission = create_submission(db)
    registry = ProviderRegistry()
    registry.register(FakeProvider())
    service = VerificationService(registry)

    result = service.verify(
        db=db,
        bid_submission_id=submission.id,
        request=VerificationRequest(
            identifier="27abcde1234f1z5",
            verification_type="gst_registration",
        ),
    )

    assert result.status == VerificationStatus.VERIFIED

    stored = db.query(VerificationResultModel).one()
    assert stored.bid_submission_id == submission.id
    assert stored.provider == "FAKE"
    assert stored.verification_type == "GST_REGISTRATION"
    assert stored.identifier == "27ABCDE1234F1Z5"
    assert stored.verification_status == "VERIFIED"
    assert stored.verified_data == {"gstin": "27ABCDE1234F1Z5"}


def test_missing_submission_is_rejected(db):
    registry = ProviderRegistry()
    registry.register(FakeProvider())
    service = VerificationService(registry)

    with pytest.raises(ValueError, match="Bid submission not found"):
        service.verify(
            db=db,
            bid_submission_id=999,
            request=VerificationRequest(
                identifier="27ABCDE1234F1Z5",
                verification_type="GST_REGISTRATION",
            ),
        )


def test_unregistered_provider_is_rejected(db):
    submission = create_submission(db)
    service = VerificationService(ProviderRegistry())

    with pytest.raises(ValueError, match="No verification provider"):
        service.verify(
            db=db,
            bid_submission_id=submission.id,
            request=VerificationRequest(
                identifier="27ABCDE1234F1Z5",
                verification_type="GST_REGISTRATION",
            ),
        )


def test_document_must_belong_to_submission(db):
    first_submission = create_submission(db)
    second_submission = create_submission(db)

    document = BidDocument(
        bid_submission_id=second_submission.id,
        document_type="GST_CERTIFICATE",
        file_name="gst.pdf",
        file_path="/tmp/gst.pdf",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    registry = ProviderRegistry()
    registry.register(FakeProvider())
    service = VerificationService(registry)

    with pytest.raises(ValueError, match="does not belong"):
        service.verify(
            db=db,
            bid_submission_id=first_submission.id,
            bid_document_id=document.id,
            request=VerificationRequest(
                identifier="27ABCDE1234F1Z5",
                verification_type="GST_REGISTRATION",
            ),
        )
