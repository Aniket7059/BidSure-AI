import json
import pytest

from app.schemas.compliance_evaluation import ComplianceEvaluationRequest
from app.services.evaluators.make_in_india_evaluator import MakeInIndiaEvaluator
from app.services.evaluators.gst_evaluator import GSTEvaluator
from app.services.evaluators.income_tax_evaluator import IncomeTaxEvaluator
from app.services.evaluators.udyam_evaluator import UdyamEvaluator
from app.services.evaluators.epfo_esic_evaluator import EPFOESICEvaluator
from app.services.evaluators.mca21_evaluator import MCA21Evaluator
from app.services.evaluators.oem_authorization_evaluator import OEMAuthorizationEvaluator


def test_make_in_india_tender_specific_validation_config():
    evaluator = MakeInIndiaEvaluator()

    # Tender requiring 65% minimum local content
    v_config = {"minimum_local_content": 65}

    # 1. Local content 70% -> PASS
    req_70 = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=1,
        requirement_type="MAKE_IN_INDIA",
        requirement_name="Local Content 65%",
        validation_config=v_config,
        extracted_data={"local_content_percentage": 70.0},
    )
    res_70 = evaluator.evaluate(req_70)
    assert res_70.status == "PASS"

    # 2. Local content 65% -> PASS
    req_65 = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=1,
        requirement_type="MAKE_IN_INDIA",
        requirement_name="Local Content 65%",
        validation_config=v_config,
        extracted_data={"local_content_percentage": 65.0},
    )
    res_65 = evaluator.evaluate(req_65)
    assert res_65.status == "PASS"

    # 3. Local content 50% -> FAIL (since tender requires 65%)
    req_50 = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=1,
        requirement_type="MAKE_IN_INDIA",
        requirement_name="Local Content 65%",
        validation_config=v_config,
        extracted_data={"local_content_percentage": 50.0},
    )
    res_50 = evaluator.evaluate(req_50)
    assert res_50.status == "FAIL"
    assert "65.0" in res_50.reason

    # 4. JSON string validation_config requiring 80%
    v_config_json = json.dumps({"minimum_local_content": 80})
    req_json = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=1,
        requirement_type="MAKE_IN_INDIA",
        requirement_name="High Local Content",
        validation_config=v_config_json,
        extracted_data={"local_content_percentage": 75.0},
    )
    res_json = evaluator.evaluate(req_json)
    assert res_json.status == "FAIL"


def test_gst_tender_specific_state_code_validation():
    evaluator = GSTEvaluator()

    # Tender requiring state code 27 (Maharashtra)
    v_config = {"required_state_code": "27"}

    req_pass = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=2,
        requirement_type="GST",
        requirement_name="MH GST Registration",
        validation_config=v_config,
        verification_data={"gstin": "27ABCDE1234F1Z5", "status": "VERIFIED", "return_filing_status": "COMPLIANT"},
    )
    res_pass = evaluator.evaluate(req_pass)
    assert res_pass.status == "PASS"

    req_fail = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=2,
        requirement_type="GST",
        requirement_name="MH GST Registration",
        validation_config=v_config,
        verification_data={"gstin": "07ABCDE1234F1Z5", "status": "VERIFIED", "return_filing_status": "COMPLIANT"},
    )
    res_fail = evaluator.evaluate(req_fail)
    assert res_fail.status == "FAIL"
    assert "state code (07) does not match" in res_fail.reason


def test_income_tax_tender_specific_turnover_validation():
    evaluator = IncomeTaxEvaluator()

    v_config = {"minimum_annual_turnover": 10000000}  # 1 Crore

    req_pass = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=3,
        requirement_type="INCOME_TAX",
        requirement_name="Turnover > 1Cr",
        validation_config=v_config,
        extracted_data={"annual_turnover": 15000000},
        verification_data={"pan": "ABCDE1234F", "status": "VERIFIED", "pan_status": "ACTIVE", "income_tax_compliance": "COMPLIANT"},
    )
    res_pass = evaluator.evaluate(req_pass)
    assert res_pass.status == "PASS"

    req_fail = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=3,
        requirement_type="INCOME_TAX",
        requirement_name="Turnover > 1Cr",
        validation_config=v_config,
        extracted_data={"annual_turnover": 8000000},
        verification_data={"pan": "ABCDE1234F", "status": "VERIFIED", "pan_status": "ACTIVE", "income_tax_compliance": "COMPLIANT"},
    )
    res_fail = evaluator.evaluate(req_fail)
    assert res_fail.status == "FAIL"
    assert "below tender minimum requirement" in res_fail.reason


def test_udyam_tender_specific_classification_validation():
    evaluator = UdyamEvaluator()

    v_config = {"allowed_enterprise_types": ["MICRO", "SMALL"]}

    req_micro = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=4,
        requirement_type="UDYAM",
        requirement_name="Micro/Small MSME Only",
        validation_config=v_config,
        verification_data={"udyam_number": "UDYAM-MH-01-0012345", "status": "VERIFIED", "enterprise_status": "ACTIVE", "enterprise_type": "MICRO"},
    )
    res_micro = evaluator.evaluate(req_micro)
    assert res_micro.status == "PASS"

    req_medium = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=4,
        requirement_type="UDYAM",
        requirement_name="Micro/Small MSME Only",
        validation_config=v_config,
        verification_data={"udyam_number": "UDYAM-MH-01-0012345", "status": "VERIFIED", "enterprise_status": "ACTIVE", "enterprise_type": "MEDIUM"},
    )
    res_medium = evaluator.evaluate(req_medium)
    assert res_medium.status == "FAIL"
    assert "classification (MEDIUM) is not eligible" in res_medium.reason


def test_epfo_tender_specific_member_count_validation():
    evaluator = EPFOESICEvaluator()

    v_config = {"minimum_active_members": 20}

    req_pass = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=5,
        requirement_type="EPFO",
        requirement_name="Min 20 Employees",
        validation_config=v_config,
        verification_data={"monthly_filing_status": "COMPLIANT", "coverage_status": "ACTIVE", "active_member_count": 25},
    )
    res_pass = evaluator.evaluate(req_pass)
    assert res_pass.status == "PASS"

    req_fail = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=5,
        requirement_type="EPFO",
        requirement_name="Min 20 Employees",
        validation_config=v_config,
        verification_data={"monthly_filing_status": "COMPLIANT", "coverage_status": "ACTIVE", "active_member_count": 10},
    )
    res_fail = evaluator.evaluate(req_fail)
    assert res_fail.status == "FAIL"
    assert "Active EPFO member count (10) is below" in res_fail.reason


def test_mca21_tender_specific_paid_up_capital_validation():
    evaluator = MCA21Evaluator()

    v_config = {"minimum_paid_up_capital": 5000000}

    req_pass = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=6,
        requirement_type="MCA21",
        requirement_name="Min 50L Paid Up Capital",
        validation_config=v_config,
        verification_data={"company_status": "ACTIVE", "cin": "U74999MH2018PTC301234", "paid_up_capital": 10000000},
    )
    res_pass = evaluator.evaluate(req_pass)
    assert res_pass.status == "PASS"

    req_fail = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=6,
        requirement_type="MCA21",
        requirement_name="Min 50L Paid Up Capital",
        validation_config=v_config,
        verification_data={"company_status": "ACTIVE", "cin": "U74999MH2018PTC301234", "paid_up_capital": 2000000},
    )
    res_fail = evaluator.evaluate(req_fail)
    assert res_fail.status == "FAIL"
    assert "paid-up capital (2000000.0) is below" in res_fail.reason.lower()


def test_oem_authorization_tender_specific_oem_name_validation():
    evaluator = OEMAuthorizationEvaluator()

    v_config = {"required_oem_name": "Cisco"}

    req_pass = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=7,
        requirement_type="OEM_AUTHORIZATION",
        requirement_name="Cisco OEM Authorization",
        validation_config=v_config,
        extracted_data={"oem_name": "Cisco", "is_authorized": True, "is_expired": False},
    )
    res_pass = evaluator.evaluate(req_pass)
    assert res_pass.status == "PASS"

    req_fail = ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=7,
        requirement_type="OEM_AUTHORIZATION",
        requirement_name="Cisco OEM Authorization",
        validation_config=v_config,
        extracted_data={"oem_name": "Dell Technologies", "is_authorized": True, "is_expired": False},
    )
    res_fail = evaluator.evaluate(req_fail)
    assert res_fail.status == "FAIL"
    assert "OEM authorization is for 'Dell Technologies', but tender requires 'Cisco'" in res_fail.reason
