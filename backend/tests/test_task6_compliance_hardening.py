import io
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.main import app
from app.database.base import Base
from app.database.session import engine, SessionLocal
from app.models.bidder import Bidder
from app.models.tender import Tender
from app.models.tender_requirement import TenderRequirement
from app.models.bid_submission import BidSubmission
from app.models.bid_document import BidDocument
from app.models.compliance_check import ComplianceCheck
from app.models.compliance_assessment import ComplianceAssessment
from app.schemas.compliance_evaluation import ComplianceEvaluationRequest, ComplianceEvaluationResult
from app.services.compliance_service import compliance_service
from app.services.compliance_assessment_service import compliance_assessment_service
from app.services.end_to_end_verification_service import end_to_end_verification_service
from app.services.evaluators.oem_authorization_evaluator import OEMAuthorizationEvaluator
from app.services.evaluators.debarment_evaluator import DebarmentEvaluator
from app.services.evaluators.income_tax_evaluator import IncomeTaxEvaluator
from app.services.evaluators.startup_nsic_evaluator import StartupNSICEvaluator
from app.services.evaluators.epfo_esic_evaluator import EPFOESICEvaluator
from app.services.evaluators.gst_evaluator import GSTEvaluator
from app.services.evaluators.udyam_evaluator import UdyamEvaluator
from app.services.evaluators.mca21_evaluator import MCA21Evaluator
from app.services.evaluators.make_in_india_evaluator import MakeInIndiaEvaluator
from app.providers.register import register_providers
from app.services.evaluators.register import register_evaluators
from seed_users import seed_default_users


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    register_providers()
    register_evaluators()
    seed_default_users()
    yield


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# --------------------------------------------------
# Regression Bug 1: OEM Missing is_authorized MUST NOT PASS
# --------------------------------------------------
def test_reg_1_oem_missing_is_authorized_does_not_pass():
    evaluator = OEMAuthorizationEvaluator()
    req = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=1,
        requirement_type="OEM_AUTHORIZATION",
        requirement_name="OEM Authorization Certificate",
        extracted_data={"fields": {"oem_name": "Tech Corp"}},  # is_authorized missing
        verification_data={},
    )
    result = evaluator.evaluate(req)
    assert result.status != "PASS"
    assert result.status == "REVIEW"


# --------------------------------------------------
# Regression Bug 2: Debarment NOT_FOUND / ERROR MUST NOT be clean PASS
# --------------------------------------------------
def test_reg_2_debarment_not_found_or_error_does_not_pass():
    evaluator = DebarmentEvaluator()
    req = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=1,
        requirement_type="DEBARMENT",
        requirement_name="Debarment & Blacklisting Check",
        verification_data={"status": "NOT_FOUND", "is_debarred": None},
    )
    result = evaluator.evaluate(req)
    assert result.status != "PASS"
    assert result.status == "REVIEW"


# --------------------------------------------------
# Regression Bug 3: Income Tax Provider Field Normalization
# --------------------------------------------------
def test_reg_3_income_tax_field_normalization():
    evaluator = IncomeTaxEvaluator()
    req = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=1,
        requirement_type="INCOME_TAX",
        requirement_name="Income Tax Compliance",
        verification_data={
            "status": "VERIFIED",
            "pan": "ABCDE1234F",
            "pan_status": "ACTIVE",
            "tax_compliance_status": "NON_COMPLIANT",  # Normalized alias
        },
    )
    result = evaluator.evaluate(req)
    assert result.status == "FAIL"


# --------------------------------------------------
# Regression Bug 4: Startup/NSIC Missing EMD Exemption MUST NOT Default True
# --------------------------------------------------
def test_reg_4_startup_missing_emd_exemption_does_not_pass():
    evaluator = StartupNSICEvaluator()
    req = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=1,
        requirement_type="STARTUP_INDIA",
        requirement_name="Startup Recognition",
        extracted_data={"fields": {"registration_number": "DIPP12345"}},
        validation_config={"require_emd_exemption": True},
    )
    result = evaluator.evaluate(req)
    assert result.status != "PASS"
    assert result.status == "REVIEW"


# --------------------------------------------------
# Regression Bug 5 & 6: Mandatory vs Optional Compliance Rules
# --------------------------------------------------
def test_reg_5_6_optional_fail_does_not_fail_bid(db: Session):
    ts = int(datetime.now().timestamp())
    bidder = Bidder(company_name=f"Opt Bidder {ts}", gstin=f"27OPT{ts % 10000:04d}1Z5")
    tender = Tender(reference_number=f"TENDER-OPT-{ts}", title="Opt Test Tender")
    db.add_all([bidder, tender])
    db.commit()

    req_mand = TenderRequirement(tender_id=tender.id, requirement_type="GST", requirement_name="GST Mand", is_required=True)
    req_opt = TenderRequirement(tender_id=tender.id, requirement_type="UDYAM", requirement_name="Udyam Opt", is_required=False)
    db.add_all([req_mand, req_opt])
    db.commit()

    sub = BidSubmission(tender_id=tender.id, bidder_id=bidder.id, status="SUBMITTED")
    db.add(sub)
    db.commit()

    # Pass mandatory check, fail optional check
    c1 = ComplianceCheck(bid_submission_id=sub.id, tender_requirement_id=req_mand.id, status="PASS", reason="GST Pass", checked_by="TEST")
    c2 = ComplianceCheck(bid_submission_id=sub.id, tender_requirement_id=req_opt.id, status="FAIL", reason="Udyam Fail", checked_by="TEST")
    db.add_all([c1, c2])
    db.commit()

    ass = compliance_assessment_service.assess_submission(db, sub.id)
    assert ass.status == "COMPLIANT"
    assert ass.assessment_metadata["mandatory_pass_count"] == 1
    assert ass.assessment_metadata["mandatory_fail_count"] == 0
    assert ass.assessment_metadata["optional_fail_count"] == 1


# --------------------------------------------------
# Regression Bug 7: High Score + Mandatory Fail MUST BE HIGH Risk
# --------------------------------------------------
def test_reg_7_high_score_with_mandatory_fail_is_high_risk(db: Session):
    ts = int(datetime.now().timestamp())
    bidder = Bidder(company_name=f"High Fail Bidder {ts}")
    tender = Tender(reference_number=f"TENDER-HF-{ts}", title="High Fail Tender")
    db.add_all([bidder, tender])
    db.commit()

    req_fail = TenderRequirement(tender_id=tender.id, requirement_type="GST", requirement_name="GST Req", is_required=True)
    req_pass1 = TenderRequirement(tender_id=tender.id, requirement_type="PAN", requirement_name="PAN Req", is_required=False)
    req_pass2 = TenderRequirement(tender_id=tender.id, requirement_type="UDYAM", requirement_name="Udyam Req", is_required=False)
    req_pass3 = TenderRequirement(tender_id=tender.id, requirement_type="MCA21", requirement_name="MCA Req", is_required=False)
    req_pass4 = TenderRequirement(tender_id=tender.id, requirement_type="EPFO", requirement_name="EPFO Req", is_required=False)
    db.add_all([req_fail, req_pass1, req_pass2, req_pass3, req_pass4])
    db.commit()

    sub = BidSubmission(tender_id=tender.id, bidder_id=bidder.id, status="SUBMITTED")
    db.add(sub)
    db.commit()

    db.add(ComplianceCheck(bid_submission_id=sub.id, tender_requirement_id=req_fail.id, status="FAIL", checked_by="TEST"))
    db.add(ComplianceCheck(bid_submission_id=sub.id, tender_requirement_id=req_pass1.id, status="PASS", checked_by="TEST"))
    db.add(ComplianceCheck(bid_submission_id=sub.id, tender_requirement_id=req_pass2.id, status="PASS", checked_by="TEST"))
    db.add(ComplianceCheck(bid_submission_id=sub.id, tender_requirement_id=req_pass3.id, status="PASS", checked_by="TEST"))
    db.add(ComplianceCheck(bid_submission_id=sub.id, tender_requirement_id=req_pass4.id, status="PASS", checked_by="TEST"))
    db.commit()

    ass = compliance_assessment_service.assess_submission(db, sub.id)
    assert ass.score == 80.0
    assert ass.status == "NON_COMPLIANT"
    assert ass.risk_level == "HIGH"  # Must NOT be LOW risk despite score=80.0


# --------------------------------------------------
# Regression Bug 8: Duplicate Evaluation Run Prevention
# --------------------------------------------------
def test_reg_8_duplicate_evaluation_run_prevention(db: Session):
    ts = int(datetime.now().timestamp())
    bidder = Bidder(company_name=f"Dup Bidder {ts}")
    tender = Tender(reference_number=f"TENDER-DUP-{ts}", title="Dup Tender")
    db.add_all([bidder, tender])
    db.commit()

    req = TenderRequirement(tender_id=tender.id, requirement_type="GST", requirement_name="GST Req", is_required=True)
    db.add(req)
    db.commit()

    sub = BidSubmission(tender_id=tender.id, bidder_id=bidder.id, status="SUBMITTED")
    db.add(sub)
    db.commit()

    # Run evaluation twice
    checks1 = compliance_service.evaluate_submission(db, sub.id)
    checks2 = compliance_service.evaluate_submission(db, sub.id)

    assert len(checks1) == 1
    assert len(checks2) == 1
    total_db_checks = db.query(ComplianceCheck).filter(ComplianceCheck.bid_submission_id == sub.id).count()
    assert total_db_checks == 1


# --------------------------------------------------
# Regression Bug 9: Workflow COMPLETED != Compliance COMPLIANT
# --------------------------------------------------
def test_reg_9_workflow_completed_does_not_mean_compliant(db: Session):
    ts = int(datetime.now().timestamp())
    bidder = Bidder(company_name=f"Wf Bidder {ts}")
    tender = Tender(reference_number=f"TENDER-WF-{ts}", title="Wf Tender")
    db.add_all([bidder, tender])
    db.commit()

    req = TenderRequirement(tender_id=tender.id, requirement_type="GST", requirement_name="GST Req", is_required=True)
    db.add(req)
    db.commit()

    sub = BidSubmission(tender_id=tender.id, bidder_id=bidder.id, status="SUBMITTED")
    db.add(sub)
    db.commit()

    summary = end_to_end_verification_service.verify_bid_submission(db, sub.id)
    assert summary.status == "COMPLETED"  # Workflow completed
    assert summary.overall_status in ("REVIEW", "NON_COMPLIANT")  # Compliance status distinct


# --------------------------------------------------
# Regression Bug 10: Unsupported Mandatory Requirement MUST NOT PASS
# --------------------------------------------------
def test_reg_10_unsupported_mandatory_requirement_does_not_pass(db: Session):
    ts = int(datetime.now().timestamp())
    bidder = Bidder(company_name=f"Unsup Bidder {ts}")
    tender = Tender(reference_number=f"TENDER-UNSUP-{ts}", title="Unsup Tender")
    db.add_all([bidder, tender])
    db.commit()

    req = TenderRequirement(tender_id=tender.id, requirement_type="CUSTOM_TENDER_RULE", requirement_name="Custom Rule", is_required=True)
    db.add(req)
    db.commit()

    sub = BidSubmission(tender_id=tender.id, bidder_id=bidder.id, status="SUBMITTED")
    db.add(sub)
    db.commit()

    checks = compliance_service.evaluate_submission(db, sub.id)
    assert len(checks) == 1
    assert checks[0].status in ("REVIEW", "MISSING")  # Must NOT pass


# --------------------------------------------------
# Evaluator Unit Tests
# --------------------------------------------------
def test_evaluators_unit_tests():
    # GST Evaluator
    gst_eval = GSTEvaluator()
    r1 = gst_eval.evaluate(ComplianceEvaluationRequest(bid_submission_id=1, tender_requirement_id=1, requirement_type="GST", requirement_name="GST Reg", verification_data={"status": "VERIFIED", "gstin": "27ABCDE1234F1Z5"}))
    assert r1.status == "PASS"

    # Udyam Evaluator
    udyam_eval = UdyamEvaluator()
    r2 = udyam_eval.evaluate(ComplianceEvaluationRequest(bid_submission_id=1, tender_requirement_id=1, requirement_type="UDYAM", requirement_name="Udyam Reg", verification_data={"status": "VERIFIED", "udyam_number": "UDYAM-UP-01-0001"}))
    assert r2.status == "PASS"

    # MCA21 Evaluator
    mca_eval = MCA21Evaluator()
    r3 = mca_eval.evaluate(ComplianceEvaluationRequest(bid_submission_id=1, tender_requirement_id=1, requirement_type="MCA21", requirement_name="MCA Check", verification_data={"company_status": "STRUCK_OFF"}))
    assert r3.status == "FAIL"

    # Make in India Evaluator
    mii_eval = MakeInIndiaEvaluator()
    r4 = mii_eval.evaluate(ComplianceEvaluationRequest(bid_submission_id=1, tender_requirement_id=1, requirement_type="MAKE_IN_INDIA", requirement_name="MII Declaration", extracted_data={"fields": {"local_content_percentage": 60.0}}))
    assert r4.status == "PASS"
    r5 = mii_eval.evaluate(ComplianceEvaluationRequest(bid_submission_id=1, tender_requirement_id=1, requirement_type="MAKE_IN_INDIA", requirement_name="MII Declaration", extracted_data={"fields": {"local_content_percentage": 30.0}}))
    assert r5.status == "FAIL"


# --------------------------------------------------
# Assessment Determinism Test
# --------------------------------------------------
def test_assessment_repeatability(db: Session):
    ts = int(datetime.now().timestamp())
    bidder = Bidder(company_name=f"Det Bidder {ts}")
    tender = Tender(reference_number=f"TENDER-DET-{ts}", title="Det Tender")
    db.add_all([bidder, tender])
    db.commit()

    req = TenderRequirement(tender_id=tender.id, requirement_type="GST", requirement_name="GST Req", is_required=True)
    db.add(req)
    db.commit()

    sub = BidSubmission(tender_id=tender.id, bidder_id=bidder.id, status="SUBMITTED")
    db.add(sub)
    db.commit()

    ass1 = compliance_assessment_service.assess_submission(db, sub.id)
    ass2 = compliance_assessment_service.assess_submission(db, sub.id)

    assert ass1.status == ass2.status
    assert ass1.score == ass2.score
    assert ass1.risk_level == ass2.risk_level
