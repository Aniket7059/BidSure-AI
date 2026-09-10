import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.session import engine, SessionLocal
from app.models.bidder import Bidder
from app.models.tender import Tender
from app.models.tender_requirement import TenderRequirement
from app.models.bid_submission import BidSubmission
from app.models.bid_document import BidDocument
from app.services.end_to_end_verification_service import end_to_end_verification_service
from app.services.document_intelligence.document_service import document_processing_service
from app.repositories.document_extraction_repository import DocumentExtractionRepository
from app.models.document_extraction import DocumentExtraction


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure test tables exist."""
    Base.metadata.create_all(bind=engine)
    yield


def test_full_pipeline_compliant_bidder():
    """Test full integration pipeline for a fully compliant bidder."""
    db: Session = SessionLocal()
    ts = int(datetime.now().timestamp())
    try:
        # 1. Create or reuse Bidder with mock valid GSTIN & PAN
        existing_bidder = db.query(Bidder).filter(Bidder.gstin == "27ABCDE1234F1Z5").first()
        if existing_bidder:
            bidder = existing_bidder
        else:
            bidder = Bidder(
                company_name=f"Acme Solutions Private Limited {ts}",
                contact_email=f"contact_{ts}@acmesolutions.com",
                contact_phone="9876543210",
                pan="ABCDE1234F",
                gstin="27ABCDE1234F1Z5",
                udyam_number=f"UDYAM-UP-01-{ts}",
            )
            db.add(bidder)
            db.commit()
            db.refresh(bidder)

        # 2. Create Tender
        tender = Tender(
            title="Procurement of IT Infrastructure Hardware",
            reference_number=f"CPCL/IT/2026/{ts}",
            description="Supply and installation of server hardware",
            status="ACTIVE",
        )
        db.add(tender)
        db.commit()
        db.refresh(tender)

        # 3. Create Tender Requirements
        req1 = TenderRequirement(
            tender_id=tender.id,
            requirement_type="GST",
            requirement_name="Valid Active GSTIN Registration",
            is_required=True,
        )
        req2 = TenderRequirement(
            tender_id=tender.id,
            requirement_type="PAN",
            requirement_name="Valid Permanent Account Number",
            is_required=True,
        )
        req3 = TenderRequirement(
            tender_id=tender.id,
            requirement_type="UDYAM",
            requirement_name="Valid Udyam MSME Registration Certificate",
            is_required=False,
        )
        db.add_all([req1, req2, req3])
        db.commit()

        # 4. Create Bid Submission
        submission = BidSubmission(
            tender_id=tender.id,
            bidder_id=bidder.id,
            status="SUBMITTED",
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)

        # 5. Create & Seed Document Extractions
        doc1 = BidDocument(
            bid_submission_id=submission.id,
            document_type="GST_CERTIFICATE",
            file_name="gst_certificate.pdf",
            file_path="mock_data/gst_certificate.pdf",
            file_size=1024,
            content_type="application/pdf",
        )
        doc2 = BidDocument(
            bid_submission_id=submission.id,
            document_type="PAN",
            file_name="pan_card.pdf",
            file_path="mock_data/pan_card.pdf",
            file_size=1024,
            content_type="application/pdf",
        )
        db.add_all([doc1, doc2])
        db.commit()

        ext_repo = DocumentExtractionRepository()
        ext1 = DocumentExtraction(
            bid_document_id=doc1.id,
            extraction_status="COMPLETED",
            extracted_data={
                "document_type": "GST_CERTIFICATE",
                "fields": {
                    "gstin": "27ABCDE1234F1Z5",
                    "legal_name": "Acme Solutions Private Limited",
                    "status": "Active",
                },
            },
            confidence_score=0.96,
            completed_at=datetime.now(timezone.utc),
        )
        ext2 = DocumentExtraction(
            bid_document_id=doc2.id,
            extraction_status="COMPLETED",
            extracted_data={
                "document_type": "PAN",
                "fields": {
                    "pan_number": "ABCDE1234F",
                    "name": "Acme Solutions Private Limited",
                },
            },
            confidence_score=0.97,
            completed_at=datetime.now(timezone.utc),
        )
        db.add_all([ext1, ext2])
        db.commit()

        # 6. Execute End-to-End Verification Pipeline
        result = end_to_end_verification_service.verify_bid_submission(
            db, submission.id
        )

        # 7. Assertions
        assert result.bid_submission_id == submission.id
        assert result.status == "COMPLETED"
        assert result.documents_processed_count >= 2
        assert result.verifications_executed_count >= 2
        assert result.overall_status in ("COMPLIANT", "REVIEW")
        assert result.compliance_score is not None
        assert result.compliance_score >= 80.0
        assert result.risk_level in ("LOW", "MEDIUM")

    finally:
        db.close()


def test_full_pipeline_mismatched_identifier_and_debarment():
    """Test full integration pipeline for a non-compliant/debarred bidder."""
    db: Session = SessionLocal()
    ts = int(datetime.now().timestamp()) + 1
    try:
        rnd = uuid.uuid4().hex[:6].upper()
        bidder = Bidder(
            company_name=f"Fraudulent Corp Pvt Ltd {ts}",
            contact_email=f"fraud_{ts}_{rnd}@corp.com",
            contact_phone="9999999999",
            pan=f"MIS{rnd[:7]}",
            gstin=f"09INVALID{rnd}",
        )
        db.add(bidder)
        db.commit()
        db.refresh(bidder)

        tender = Tender(
            title="Supply of Oil Refining Catalysts",
            reference_number=f"CPCL/CAT/2026/{ts}",
            description="Procurement of specialized chemical catalysts",
            status="ACTIVE",
        )
        db.add(tender)
        db.commit()
        db.refresh(tender)

        req1 = TenderRequirement(
            tender_id=tender.id,
            requirement_type="DEBARMENT",
            requirement_name="Debarment & Blacklisting Check",
            is_required=True,
        )
        db.add(req1)
        db.commit()

        submission = BidSubmission(
            tender_id=tender.id,
            bidder_id=bidder.id,
            status="SUBMITTED",
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)

        result = end_to_end_verification_service.verify_bid_submission(
            db, submission.id
        )

        assert result.bid_submission_id == submission.id
        assert result.status == "COMPLETED"
        assert result.verifications_executed_count >= 1

    finally:
        db.close()
