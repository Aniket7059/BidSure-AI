from app.core.taxonomy import RequirementType
from app.schemas.compliance_evaluation import (
    ComplianceEvaluationRequest,
    ComplianceEvaluationResult,
)
from app.schemas.document_extraction import get_extracted_fields
from app.services.evaluators.base import RequirementEvaluator


class DebarmentEvaluator(RequirementEvaluator):
    """
    Evaluates vendor debarment and blacklisting status against tender rules.
    """

    @property
    def requirement_type(self) -> str:
        return RequirementType.DEBARMENT.value

    def evaluate(
        self,
        request: ComplianceEvaluationRequest,
    ) -> ComplianceEvaluationResult:
        extracted_data = request.extracted_data or {}
        verification_data = request.verification_data or {}
        fields = get_extracted_fields(extracted_data)

        if not extracted_data and not verification_data:
            return ComplianceEvaluationResult(
                status="REVIEW",
                reason="No debarment or blacklisting check evidence is available.",
                evidence={},
            )

        is_debarred = (
            verification_data.get("is_debarred")
            if "is_debarred" in verification_data
            else fields.get("is_debarred")
        )
        debarment_status = (
            verification_data.get("debarment_status")
            or fields.get("debarment_status")
        )
        v_status = str(verification_data.get("status") or verification_data.get("verification_status") or "").upper()

        v_cfg = self.get_validation_config(request)
        prohibit_debarment = v_cfg.get("prohibit_debarment", True)

        if (is_debarred is True or debarment_status in ("DEBARRED", "BLACK_LISTED")) and prohibit_debarment:
            return ComplianceEvaluationResult(
                status="FAIL",
                reason=(
                    "Bidder or affiliated entity is flagged as DEBARRED/BLACKLISTED "
                    f"by {verification_data.get('debarring_agency') or 'Government Authority'}."
                ),
                evidence={
                    "is_debarred": True,
                    "debarment_status": debarment_status or "DEBARRED",
                    "debarring_agency": verification_data.get("debarring_agency"),
                    "reason": verification_data.get("reason"),
                },
            )

        # Provider NOT_FOUND, ERROR, or PENDING cannot be assumed clean
        if v_status in ("NOT_FOUND", "ERROR", "PENDING", "UNAVAILABLE", "SKIPPED_NO_IDENTIFIER"):
            return ComplianceEvaluationResult(
                status="REVIEW",
                reason=f"Debarment verification provider returned status '{v_status}'. Requires manual review.",
                evidence={
                    "verification_status": v_status,
                    "debarment_status": debarment_status,
                },
            )

        if (debarment_status == "CLEAN" or is_debarred is False) and v_status in ("VERIFIED", "CLEAN", "SUCCESS", ""):
            return ComplianceEvaluationResult(
                status="PASS",
                reason="Vendor has clean status with no blacklisting records verified by authoritative source.",
                evidence={
                    "is_debarred": False,
                    "debarment_status": "CLEAN",
                    "verification_status": v_status or "VERIFIED",
                },
            )

        return ComplianceEvaluationResult(
            status="REVIEW",
            reason="Debarment check status requires officer review.",
            evidence=verification_data,
        )
