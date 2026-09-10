from app.schemas.compliance_evaluation import (
    ComplianceEvaluationRequest,
)

from app.services.evaluators.income_tax_evaluator import (
    IncomeTaxEvaluator,
)


def make_request(
    extracted_data=None,
    verification_data=None,
):
    return ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=1,
        requirement_type="INCOME_TAX",
        requirement_name="PAN and Income Tax Compliance",
        extracted_data=extracted_data,
        verification_data=verification_data,
    )


def test_income_tax_evaluator_has_correct_requirement_type():

    evaluator = IncomeTaxEvaluator()

    assert evaluator.requirement_type == "INCOME_TAX"


def test_no_evidence_returns_review():

    evaluator = IncomeTaxEvaluator()

    request = make_request()

    result = evaluator.evaluate(request)

    assert result.status == "REVIEW"

    assert (
        "No PAN or Income Tax compliance evidence"
        in result.reason
    )


def test_valid_pan_and_compliant_income_tax_returns_pass():

    evaluator = IncomeTaxEvaluator()

    request = make_request(
        extracted_data={
            "pan": "ABCDE1234F",
        },
        verification_data={
            "status": "VERIFIED",
            "pan": "ABCDE1234F",
            "pan_status": "ACTIVE",
            "income_tax_compliance": "COMPLIANT",
        },
    )

    result = evaluator.evaluate(request)

    assert result.status == "PASS"

    assert result.evidence["pan"] == "ABCDE1234F"

    assert (
        result.evidence["verification_status"]
        == "VERIFIED"
    )

    assert (
        result.evidence["pan_status"]
        == "ACTIVE"
    )

    assert (
        result.evidence["income_tax_compliance"]
        == "COMPLIANT"
    )


def test_invalid_pan_returns_fail():

    evaluator = IncomeTaxEvaluator()

    request = make_request(
        extracted_data={
            "pan": "ABCDE1234F",
        },
        verification_data={
            "status": "INVALID",
            "pan": "ABCDE1234F",
            "pan_status": "INVALID",
        },
    )

    result = evaluator.evaluate(request)

    assert result.status == "FAIL"

    assert (
        "PAN could not be verified"
        in result.reason
    )


def test_inactive_pan_returns_fail():

    evaluator = IncomeTaxEvaluator()

    request = make_request(
        verification_data={
            "status": "VERIFIED",
            "pan": "ABCDE1234F",
            "pan_status": "INACTIVE",
        },
    )

    result = evaluator.evaluate(request)

    assert result.status == "FAIL"

    assert "PAN is not active" in result.reason


def test_non_compliant_income_tax_returns_fail():

    evaluator = IncomeTaxEvaluator()

    request = make_request(
        verification_data={
            "status": "VERIFIED",
            "pan": "ABCDE1234F",
            "pan_status": "ACTIVE",
            "income_tax_compliance": "NON_COMPLIANT",
        },
    )

    result = evaluator.evaluate(request)

    assert result.status == "FAIL"

    assert (
        "Income Tax compliance requirements"
        in result.reason
    )


def test_pan_mismatch_returns_review():

    evaluator = IncomeTaxEvaluator()

    request = make_request(
        extracted_data={
            "pan": "ABCDE1234F",
        },
        verification_data={
            "status": "VERIFIED",
            "pan": "XYZAB5678G",
            "pan_status": "ACTIVE",
            "income_tax_compliance": "COMPLIANT",
        },
    )

    result = evaluator.evaluate(request)

    assert result.status == "REVIEW"

    assert (
        "PAN mismatch"
        in result.reason
    )

    assert (
        result.evidence["document_pan"]
        == "ABCDE1234F"
    )

    assert (
        result.evidence["verified_pan"]
        == "XYZAB5678G"
    )


def test_incomplete_verification_returns_review():

    evaluator = IncomeTaxEvaluator()

    request = make_request(
        extracted_data={
            "pan": "ABCDE1234F",
        },
        verification_data={
            "status": "PENDING",
            "pan": "ABCDE1234F",
        },
    )

    result = evaluator.evaluate(request)

    assert result.status == "REVIEW"

    assert (
        "verification evidence is incomplete"
        in result.reason
    )


def test_verified_pan_without_filing_status_returns_pass():

    evaluator = IncomeTaxEvaluator()

    request = make_request(
        verification_data={
            "status": "VERIFIED",
            "pan": "ABCDE1234F",
            "pan_status": "ACTIVE",
        },
    )

    result = evaluator.evaluate(request)

    assert result.status == "PASS"

    assert (
        result.evidence["pan"]
        == "ABCDE1234F"
    )

    assert (
        result.evidence["verification_status"]
        == "VERIFIED"
    )