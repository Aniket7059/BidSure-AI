from app.schemas.compliance_evaluation import (
    ComplianceEvaluationRequest,
)
from app.services.evaluators.gst_evaluator import (
    GSTEvaluator,
)


def make_request(
    extracted_data=None,
    verification_data=None,
):
    return ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=1,
        requirement_type="GST",
        requirement_name="GST Registration and Return Filing",
        extracted_data=extracted_data,
        verification_data=verification_data,
    )


def test_gst_evaluator_has_correct_requirement_type():

    evaluator = GSTEvaluator()

    assert evaluator.requirement_type == "GST"


def test_no_evidence_returns_review():

    evaluator = GSTEvaluator()

    request = make_request()

    result = evaluator.evaluate(request)

    assert result.status == "REVIEW"

    assert (
        result.reason
        == "No GST evidence is available."
    )

    assert result.evidence == {}


def test_valid_gst_returns_pass():

    evaluator = GSTEvaluator()

    request = make_request(
        extracted_data={
            "gstin": "29ABCDE1234F1Z5",
        },
        verification_data={
            "status": "VERIFIED",
            "gstin": "29ABCDE1234F1Z5",
            "return_filing_status": "COMPLIANT",
        },
    )

    result = evaluator.evaluate(request)

    assert result.status == "PASS"

    assert (
        "GST registration is verified"
        in result.reason
    )

    assert (
        result.evidence["gstin"]
        == "29ABCDE1234F1Z5"
    )

    assert (
        result.evidence["verification_status"]
        == "VERIFIED"
    )

    assert (
        result.evidence["return_filing_status"]
        == "COMPLIANT"
    )


def test_invalid_gst_returns_fail():

    evaluator = GSTEvaluator()

    request = make_request(
        extracted_data={
            "gstin": "29ABCDE1234F1Z5",
        },
        verification_data={
            "status": "INVALID",
            "gstin": "29ABCDE1234F1Z5",
        },
    )

    result = evaluator.evaluate(request)

    assert result.status == "FAIL"

    assert (
        result.reason
        == "GST registration could not be verified."
    )

    assert (
        result.evidence["gstin"]
        == "29ABCDE1234F1Z5"
    )

    assert (
        result.evidence["verification_status"]
        == "INVALID"
    )


def test_non_compliant_returns_fail():

    evaluator = GSTEvaluator()

    request = make_request(
        extracted_data={
            "gstin": "29ABCDE1234F1Z5",
        },
        verification_data={
            "status": "VERIFIED",
            "gstin": "29ABCDE1234F1Z5",
            "return_filing_status": "NON_COMPLIANT",
        },
    )

    result = evaluator.evaluate(request)

    assert result.status == "FAIL"

    assert (
        result.reason
        == "GST return filing is non-compliant."
    )

    assert (
        result.evidence["return_filing_status"]
        == "NON_COMPLIANT"
    )


def test_gstin_mismatch_returns_review():

    evaluator = GSTEvaluator()

    request = make_request(
        extracted_data={
            "gstin": "29ABCDE1234F1Z5",
        },
        verification_data={
            "status": "VERIFIED",
            "gstin": "29XYZ9876K1Z5",
            "return_filing_status": "COMPLIANT",
        },
    )

    result = evaluator.evaluate(request)

    assert result.status == "REVIEW"

    assert (
        result.reason
        == (
            "GSTIN mismatch between document "
            "evidence and verification data."
        )
    )

    assert (
        result.evidence["document_gstin"]
        == "29ABCDE1234F1Z5"
    )

    assert (
        result.evidence["verified_gstin"]
        == "29XYZ9876K1Z5"
    )


def test_incomplete_verification_returns_review():

    evaluator = GSTEvaluator()

    request = make_request(
        extracted_data={
            "gstin": "29ABCDE1234F1Z5",
        },
        verification_data={
            "gstin": "29ABCDE1234F1Z5",
        },
    )

    result = evaluator.evaluate(request)

    assert result.status == "REVIEW"

    assert (
        result.reason
        == (
            "GST registration verification "
            "evidence is incomplete."
        )
    )

    assert (
        result.evidence["gstin"]
        == "29ABCDE1234F1Z5"
    )

    assert (
        result.evidence["verification_status"]
        is None
    )


def test_verified_gst_without_filing_status_returns_pass():

    evaluator = GSTEvaluator()

    request = make_request(
        extracted_data={
            "gstin": "29ABCDE1234F1Z5",
        },
        verification_data={
            "status": "VERIFIED",
            "gstin": "29ABCDE1234F1Z5",
        },
    )

    result = evaluator.evaluate(request)

    assert result.status == "PASS"

    assert (
        result.evidence["gstin"]
        == "29ABCDE1234F1Z5"
    )

    assert (
        result.evidence["verification_status"]
        == "VERIFIED"
    )

    assert (
        result.evidence["return_filing_status"]
        is None
    )