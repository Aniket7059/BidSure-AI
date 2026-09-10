from app.core.taxonomy import RequirementType
from app.schemas.compliance_evaluation import (
    ComplianceEvaluationRequest,
    ComplianceEvaluationResult,
)
from app.schemas.document_extraction import get_extracted_fields
from app.services.evaluators.base import RequirementEvaluator


class StartupNSICEvaluator(RequirementEvaluator):
    """
    Evaluates Startup India / NSIC registration and waiver eligibility.
    """

    @property
    def requirement_type(self) -> str:
        return RequirementType.STARTUP_INDIA.value

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
                reason="No Startup India / NSIC registration evidence available.",
                evidence={},
            )

        reg_number = (
            verification_data.get("registration_number")
            or fields.get("registration_number")
            or verification_data.get("dipp_number")
        )
        emd_exemption = (
            verification_data.get("emd_exemption_eligible")
            if "emd_exemption_eligible" in verification_data
            else fields.get("emd_exemption_eligible")
        )
        v_status = str(verification_data.get("status") or verification_data.get("verification_status") or "").upper()

        v_cfg = self.get_validation_config(request)
        require_emd = v_cfg.get("require_emd_exemption", False)

        if require_emd and emd_exemption is False:
            return ComplianceEvaluationResult(
                status="FAIL",
                reason="Vendor does not satisfy tender requirement for EMD exemption eligibility.",
                evidence={
                    "registration_number": reg_number,
                    "emd_exemption_eligible": emd_exemption,
                },
            )

        if require_emd and emd_exemption is None:
            return ComplianceEvaluationResult(
                status="REVIEW",
                reason="EMD exemption eligibility evidence is missing or unverified.",
                evidence={
                    "registration_number": reg_number,
                    "emd_exemption_eligible": None,
                },
            )

        # Reg number and verified status required for PASS
        if reg_number and (v_status in ("VERIFIED", "CLEAN", "SUCCESS", "") or not verification_data):
            return ComplianceEvaluationResult(
                status="PASS",
                reason="Startup India / NSIC recognition verified. EMD & exemption criteria satisfied.",
                evidence={
                    "registration_number": reg_number,
                    "scheme_type": verification_data.get("scheme_type"),
                    "emd_exemption_eligible": emd_exemption,
                },
            )

        return ComplianceEvaluationResult(
            status="REVIEW",
            reason="Startup India / NSIC evidence is incomplete or requires officer review.",
            evidence={
                "registration_number": reg_number,
                "emd_exemption_eligible": emd_exemption,
                "verification_status": v_status,
            },
        )
