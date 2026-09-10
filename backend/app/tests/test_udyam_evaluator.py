from app.schemas.compliance_evaluation import (
    ComplianceEvaluationRequest,
)
from app.services.evaluators.udyam_evaluator import (
    UdyamEvaluator,
)


def make_request(
    extracted_data=None,
    verification_data=None,
):
    return ComplianceEvaluationRequest(
        bid_submission_id=1,
        tender_requirement_id=1,
        requirement_type="UDYAM",
        requirement_name="Udyam/MSME Registration",
        extracted_data=extracted_data,
        verification_data=verification_data,
    )


def test_udyam_evaluator_has_correct_requirement_type():

    evaluator = UdyamEvaluator()

    assert evaluator.requirement_type == "UDYAM"


def test_no_evidence_returns_review():

    evaluator = UdyamEvaluator()

    request = make_request()

    result = evaluator.evaluate(request)

    assert result.status == "REVIEW"

    assert (
        result.reason
        == "No Udyam/MSME evidence is available."
    )

    assert result.evidence == {}


def test_valid_udyam_returns_pass():

    evaluator = UdyamEvaluator()

    request = make_request(
        extracted_data={
            "udyam_number": "UDYAM-UP-00-1234567",
        },
        verification_data={
            "status": "VERIFIED",
            "udyam_number": "UDYAM-UP-00-1234567",
            "enterprise_status": "ACTIVE",
        },
    )

    result = evaluator.evaluate(request)

    assert result.status == "PASS"

    assert (
        "Udyam/MSME registration is verified"
        in result.reason
    )

    assert (
        result.evidence["udyam_number"]
        == "UDYAM-UP-00-1234567"
    )

    assert (
        result.evidence["verification_status"]
        == "VERIFIED"
    )

    assert (
        result.evidence["enterprise_status"]
        == "ACTIVE"
    )


def test_invalid_udyam_returns_fail():

    evaluator = UdyamEvaluator()

    request = make_request(
        extracted_data={
            "udyam_number": "UDYAM-UP-00-1234567",
        },
        verification_data={
            "status": "INVALID",
            "udyam_number": "UDYAM-UP-00-1234567",
        },
    )

    result = evaluator.evaluate(request)

    assert result.status == "FAIL"

    assert (
        result.reason
        == "Udyam/MSME registration could not be verified."
    )

    assert (
        result.evidence["udyam_number"]
        == "UDYAM-UP-00-1234567"
    )

    assert (
        result.evidence["verification_status"]
        == "INVALID"
    )


def test_inactive_enterprise_returns_fail():

    evaluator = UdyamEvaluator()

    request = make_request(
        extracted_data={
            "udyam_number": "UDYAM-UP-00-1234567",
        },
        verification_data={
            "status": "VERIFIED",
            "udyam_number": "UDYAM-UP-00-1234567",
            "enterprise_status": "INACTIVE",
        },
    )

    result = evaluator.evaluate(request)

    assert result.status == "FAIL"

    assert (
        result.reason
        == "Udyam/MSME enterprise is not active."
    )

    assert (
        result.evidence["enterprise_status"]
        == "INACTIVE"
    )


def test_udyam_number_mismatch_returns_review():

    evaluator = UdyamEvaluator()

    request = make_request(
        extracted_data={
            "udyam_number": "UDYAM-UP-00-1234567",
        },
        verification_data={
            "status": "VERIFIED",
            "udyam_number": "UDYAM-UP-00-7654321",
            "enterprise_status": "ACTIVE",
        },
    )

    result = evaluator.evaluate(request)

    assert result.status == "REVIEW"

    assert (
        result.reason
        == (
            "Udyam number mismatch between "
            "document evidence and verification data."
        )
    )

    assert (
        result.evidence["document_udyam_number"]
        == "UDYAM-UP-00-1234567"
    )

    assert (
        result.evidence["verified_udyam_number"]
        == "UDYAM-UP-00-7654321"
    )


def test_incomplete_verification_returns_review():

    evaluator = UdyamEvaluator()

    request = make_request(
        extracted_data={
            "udyam_number": "UDYAM-UP-00-1234567",
        },
        verification_data={
            "udyam_number": "UDYAM-UP-00-1234567",
        },
    )

    result = evaluator.evaluate(request)

    assert result.status == "REVIEW"

    assert (
        result.reason
        == (
            "Udyam/MSME verification evidence "
            "is incomplete."
        )
    )

    assert (
        result.evidence["udyam_number"]
        == "UDYAM-UP-00-1234567"
    )

    assert (
        result.evidence["verification_status"]
        is None
    )


def test_verified_udyam_without_enterprise_status_returns_pass():

    evaluator = UdyamEvaluator()

    request = make_request(
        extracted_data={
            "udyam_number": "UDYAM-UP-00-1234567",
        },
        verification_data={
            "status": "VERIFIED",
            "udyam_number": "UDYAM-UP-00-1234567",
        },
    )

    result = evaluator.evaluate(request)

    assert result.status == "PASS"

    assert (
        result.evidence["udyam_number"]
        == "UDYAM-UP-00-1234567"
    )

    assert (
        result.evidence["verification_status"]
        == "VERIFIED"
    )

    assert (
        result.evidence["enterprise_status"]
        is None
    )


def test_udyam_document_only_returns_review():

    evaluator = UdyamEvaluator()

    request = make_request(
        extracted_data={
            "udyam_number": "UDYAM-UP-00-1234567",
        },
    )

    result = evaluator.evaluate(request)

    assert result.status == "REVIEW"

    assert (
        result.evidence["udyam_number"]
        == "UDYAM-UP-00-1234567"
    )

    assert (
        result.evidence["verification_status"]
        is None
    )