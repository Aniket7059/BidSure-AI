from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db

from app.schemas.compliance_check import (
    ComplianceCheckResponse,
)

from app.schemas.compliance_assessment import (
    ComplianceAssessmentResponse,
)

from app.schemas.compliance_evaluation import (
    ComplianceEvaluationRequest,
)

from app.repositories.compliance_check_repository import (
    compliance_check_repository,
)

from app.services.compliance_service import (
    compliance_service,
)

from app.services.compliance_assessment_service import (
    compliance_assessment_service,
)

from app.services.cross_verification_service import (
    CrossVerificationResult,
    cross_verification_service,
)
from app.services.recommendation_service import (
    recommendation_service,
)


from app.api.dependencies import require_role

router = APIRouter(
    prefix="/compliance",
    tags=["Compliance"],
    dependencies=[Depends(require_role("PROCUREMENT_OFFICER", "ADMIN"))],
)


@router.post(
    "/evaluate",
    response_model=ComplianceCheckResponse,
    status_code=status.HTTP_201_CREATED,
)
def evaluate_compliance_requirement(
    request: ComplianceEvaluationRequest,
    db: Session = Depends(get_db),
):
    try:
        return compliance_service.evaluate_requirement(
            db,
            request,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/assess/{bid_submission_id}",
    response_model=ComplianceAssessmentResponse,
)
def assess_bid_submission(
    bid_submission_id: int,
    db: Session = Depends(get_db),
):
    try:
        return (
            compliance_assessment_service.assess_submission(
                db,
                bid_submission_id,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/cross-verify/{bid_submission_id}",
    response_model=CrossVerificationResult,
)
def cross_verify_bid_submission(
    bid_submission_id: int,
    db: Session = Depends(get_db),
):
    try:
        return cross_verification_service.cross_verify_submission(
            db,
            bid_submission_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/checks/{bid_submission_id}",
    response_model=list[ComplianceCheckResponse],
)
def get_bid_submission_checks(
    bid_submission_id: int,
    db: Session = Depends(get_db),
):
    return compliance_check_repository.get_by_submission(
        db,
        bid_submission_id,
    )


from app.schemas.recommendation import (
    RecommendationResponse,
)
from app.repositories.compliance_assessment_repository import (
    compliance_assessment_repository,
)

@router.post(
    "/recommend/{bid_submission_id}",
    response_model=RecommendationResponse,
)
def recommend_bid_submission(
    bid_submission_id: int,
    db: Session = Depends(get_db),
):
    try:
        return (
            recommendation_service.generate_recommendation(
                db,
                bid_submission_id,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/recommendation/{bid_submission_id}",
    response_model=RecommendationResponse,
)
def get_bid_submission_recommendation(
    bid_submission_id: int,
    db: Session = Depends(get_db),
):
    assessment = compliance_assessment_repository.get_latest_by_submission(
        db, bid_submission_id
    )
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance assessment not found for submission #{bid_submission_id}",
        )

    meta = assessment.assessment_metadata or {}
    detail = meta.get("recommendation_detail")
    if detail:
        return RecommendationResponse.model_validate(detail)

    # If detail is not yet generated, generate it on demand
    return recommendation_service.generate_recommendation(db, bid_submission_id)