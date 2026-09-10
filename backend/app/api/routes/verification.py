from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.verification_result_repository import (
    verification_result_repository,
)
from app.providers.schemas import VerificationRequest
from app.schemas.verification import (
    VerificationAPIRequest,
    VerificationAPIResponse,
)
from app.services.verification_service import verification_service


from app.api.dependencies import require_role

router = APIRouter(
    prefix="/verification",
    tags=["Verification"],
    dependencies=[Depends(require_role("PROCUREMENT_OFFICER", "ADMIN"))],
)


@router.post(
    "/verify",
    response_model=VerificationAPIResponse,
    status_code=status.HTTP_201_CREATED,
)
def verify_identifier(
    request: VerificationAPIRequest,
    db: Session = Depends(get_db),
):
    """Run a registered provider verification and persist its result."""

    provider_request = VerificationRequest(
        identifier=request.identifier,
        verification_type=request.verification_type,
    )

    try:
        result = verification_service.verify(
            db=db,
            bid_submission_id=request.bid_submission_id,
            request=provider_request,
            bid_document_id=request.bid_document_id,
        )

        persisted_results = verification_result_repository.get_by_submission(
            db,
            request.bid_submission_id,
        )

        # The service has just persisted this result. Return the matching
        # newest record without exposing SQLAlchemy internals to providers.
        persisted = next(
            (
                item
                for item in reversed(persisted_results)
                if item.provider == result.provider
                and item.verification_type == result.verification_type
                and item.identifier == result.identifier
                and item.checked_at == result.checked_at
            ),
            None,
        )

        if persisted is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Verification result was not persisted.",
            )

        return persisted

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/submissions/{bid_submission_id}/results",
    response_model=list[VerificationAPIResponse],
)
def get_submission_verification_results(
    bid_submission_id: int,
    db: Session = Depends(get_db),
):
    """Return persisted provider verification results for a submission."""

    return verification_result_repository.get_by_submission(
        db,
        bid_submission_id,
    )


from app.api.dependencies import get_current_user
from app.models.user import User
from app.providers.registry import provider_registry
from app.providers.schemas import ProviderCapability
from app.schemas.manual_verification import ManualVerificationCreate


@router.get(
    "/providers",
    response_model=list[ProviderCapability],
    status_code=status.HTTP_200_OK,
)
def list_verification_providers():
    """
    Returns capability and provenance metadata for all registered verification connectors.
    Hides internal API keys, passwords, and sensitive credentials.
    """
    capabilities: list[ProviderCapability] = []
    seen_names: set[str] = set()

    for key, provider in provider_registry._providers.items():
        p_name = provider.provider_name
        if p_name not in seen_names:
            seen_names.add(p_name)
            capabilities.append(provider.capability)

    return capabilities


@router.post(
    "/manual",
    response_model=VerificationAPIResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_manual_verification(
    manual_in: ManualVerificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Records a human-in-the-loop manual verification result by a Procurement Officer.
    Tagged with source_mode = MANUAL and logs an audit log entry.
    """
    try:
        created_obj = verification_service.record_manual_verification(
            db=db,
            user_id=current_user.id,
            manual_in=manual_in,
        )
        return created_obj
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

