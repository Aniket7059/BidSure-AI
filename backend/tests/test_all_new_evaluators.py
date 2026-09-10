import pytest

from app.schemas.compliance_evaluation import ComplianceEvaluationRequest
from app.services.evaluators.debarment_evaluator import DebarmentEvaluator
from app.services.evaluators.epfo_esic_evaluator import EPFOESICEvaluator
from app.services.evaluators.mca21_evaluator import MCA21Evaluator
from app.services.evaluators.make_in_india_evaluator import MakeInIndiaEvaluator
from app.services.evaluators.oem_authorization_evaluator import OEMAuthorizationEvaluator
from app.services.evaluators.startup_nsic_evaluator import StartupNSICEvaluator
from app.services.evaluators.register import register_evaluators
from app.services.evaluators.registry import evaluator_registry


def test_debarment_evaluator():
    evaluator = DebarmentEvaluator()
    assert evaluator.requirement_type == "DEBARMENT"

    # Clean vendor
    req_clean = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=1,
        requirement_type="DEBARMENT",
        requirement_name="Debarment Check",
        verification_data={"is_debarred": False, "debarment_status": "CLEAN"},
    )
    res_clean = evaluator.evaluate(req_clean)
    assert res_clean.status == "PASS"

    # Debarred vendor
    req_debarred = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=1,
        requirement_type="DEBARMENT",
        requirement_name="Debarment Check",
        verification_data={"is_debarred": True, "debarment_status": "DEBARRED", "debarring_agency": "GeM Authority"},
    )
    res_debarred = evaluator.evaluate(req_debarred)
    assert res_debarred.status == "FAIL"


def test_epfo_esic_evaluator():
    evaluator = EPFOESICEvaluator()
    assert evaluator.requirement_type == "EPFO"

    req_pass = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=2,
        requirement_type="EPFO",
        requirement_name="Labor Compliance",
        verification_data={"monthly_filing_status": "COMPLIANT", "coverage_status": "ACTIVE"},
    )
    res_pass = evaluator.evaluate(req_pass)
    assert res_pass.status == "PASS"


def test_mca21_evaluator():
    evaluator = MCA21Evaluator()
    assert evaluator.requirement_type == "MCA21"

    req_pass = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=3,
        requirement_type="MCA21",
        requirement_name="Corporate Status",
        verification_data={"company_status": "ACTIVE", "cin": "U74999MH2018PTC301234"},
    )
    res_pass = evaluator.evaluate(req_pass)
    assert res_pass.status == "PASS"


def test_make_in_india_evaluator():
    evaluator = MakeInIndiaEvaluator()
    assert evaluator.requirement_type == "MAKE_IN_INDIA"

    # 60% local content >= 50% required => PASS
    req_pass = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=4,
        requirement_type="MAKE_IN_INDIA",
        requirement_name="Local Content",
        extracted_data={"local_content_percentage": 60.0},
    )
    res_pass = evaluator.evaluate(req_pass)
    assert res_pass.status == "PASS"

    # 30% local content < 50% required => FAIL
    req_fail = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=4,
        requirement_type="MAKE_IN_INDIA",
        requirement_name="Local Content",
        extracted_data={"local_content_percentage": 30.0},
    )
    res_fail = evaluator.evaluate(req_fail)
    assert res_fail.status == "FAIL"


def test_oem_authorization_evaluator():
    evaluator = OEMAuthorizationEvaluator()
    assert evaluator.requirement_type == "OEM_AUTHORIZATION"

    req_pass = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=5,
        requirement_type="OEM_AUTHORIZATION",
        requirement_name="OEM Authorization",
        extracted_data={"oem_name": "HP Inc", "is_authorized": True, "is_expired": False},
    )
    res_pass = evaluator.evaluate(req_pass)
    assert res_pass.status == "PASS"


def test_startup_nsic_evaluator():
    evaluator = StartupNSICEvaluator()
    assert evaluator.requirement_type == "STARTUP_INDIA"

    req_pass = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=6,
        requirement_type="STARTUP_INDIA",
        requirement_name="Startup Exemption",
        verification_data={"registration_number": "DPIIT12345", "scheme_type": "DPIIT_STARTUP"},
    )
    res_pass = evaluator.evaluate(req_pass)
    assert res_pass.status == "PASS"


def test_evaluator_registration():
    register_evaluators()
    assert evaluator_registry.get("DEBARMENT") is not None
    assert evaluator_registry.get("EPFO") is not None
    assert evaluator_registry.get("ESIC") is not None
    assert evaluator_registry.get("MCA21") is not None
    assert evaluator_registry.get("MAKE_IN_INDIA") is not None
    assert evaluator_registry.get("OEM_AUTHORIZATION") is not None
    assert evaluator_registry.get("STARTUP_INDIA") is not None
    assert evaluator_registry.get("NSIC") is not None
