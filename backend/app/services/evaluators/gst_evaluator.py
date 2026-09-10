from app.core.taxonomy import RequirementType
from app.schemas.compliance_evaluation import (
    ComplianceEvaluationRequest,
    ComplianceEvaluationResult,
)
from app.schemas.document_extraction import get_extracted_fields
from app.services.evaluators.base import (
    RequirementEvaluator,
)


class GSTEvaluator(RequirementEvaluator):
    """
    Evaluates GST-related tender requirements using
    structured document and verification evidence.

    This evaluator does not communicate directly with
    external government portals. Government verification
    data is supplied through verification_data.
    """

    @property
    def requirement_type(self) -> str:
        return RequirementType.GST.value

    def evaluate(
        self,
        request: ComplianceEvaluationRequest,
    ) -> ComplianceEvaluationResult:

        extracted_data = request.extracted_data or {}
        verification_data = request.verification_data or {}
        fields = get_extracted_fields(extracted_data)

        # --------------------------------------------------
        # 1. Check whether any GST evidence exists
        # --------------------------------------------------

        if not extracted_data and not verification_data:
            return ComplianceEvaluationResult(
                status="REVIEW",
                reason="No GST evidence is available.",
                evidence={},
            )

        # --------------------------------------------------
        # 2. Extract GSTIN from available evidence
        # --------------------------------------------------

        v_cfg = self.get_validation_config(request)
        required_state_code = v_cfg.get("required_state_code") or v_cfg.get("state_code")

        document_gstin = fields.get("gstin")
        verified_gstin = verification_data.get("gstin")

        # --------------------------------------------------
        # 3. Check GSTIN consistency
        # --------------------------------------------------

        if (
            document_gstin
            and verified_gstin
            and document_gstin != verified_gstin
        ):
            return ComplianceEvaluationResult(
                status="REVIEW",
                reason=(
                    "GSTIN mismatch between document "
                    "evidence and verification data."
                ),
                evidence={
                    "document_gstin": document_gstin,
                    "verified_gstin": verified_gstin,
                },
            )

        gstin = verified_gstin or document_gstin

        # --------------------------------------------------
        # 3b. Check tender-specific state code requirement
        # --------------------------------------------------

        if required_state_code and gstin:
            gstin_state = str(gstin)[:2]
            if gstin_state != str(required_state_code):
                return ComplianceEvaluationResult(
                    status="FAIL",
                    reason=f"GSTIN state code ({gstin_state}) does not match tender requirement ({required_state_code}).",
                    evidence={
                        "gstin": gstin,
                        "gstin_state": gstin_state,
                        "required_state_code": required_state_code,
                    },
                )

        # --------------------------------------------------
        # 4. Check verification status
        # --------------------------------------------------

        verification_status = verification_data.get(
            "status"
        )

        if verification_status == "INVALID":
            return ComplianceEvaluationResult(
                status="FAIL",
                reason="GST registration could not be verified.",
                evidence={
                    "gstin": gstin,
                    "verification_status": verification_status,
                },
            )

        # --------------------------------------------------
        # 5. Check return filing status
        # --------------------------------------------------

        return_filing_status = verification_data.get(
            "return_filing_status"
        )

        require_return_filing = v_cfg.get("require_return_filing", v_cfg.get("require_return_filing_compliant", True))

        if return_filing_status == "NON_COMPLIANT" and require_return_filing:
            return ComplianceEvaluationResult(
                status="FAIL",
                reason="GST return filing is non-compliant.",
                evidence={
                    "gstin": gstin,
                    "return_filing_status": (
                        return_filing_status
                    ),
                },
            )

        # --------------------------------------------------
        # 6. Insufficient verification evidence
        # --------------------------------------------------

        if verification_status != "VERIFIED":
            return ComplianceEvaluationResult(
                status="REVIEW",
                reason=(
                    "GST registration verification "
                    "evidence is incomplete."
                ),
                evidence={
                    "gstin": gstin,
                    "verification_status": (
                        verification_status
                    ),
                    "return_filing_status": (
                        return_filing_status
                    ),
                },
            )

        # --------------------------------------------------
        # 7. GST requirement satisfied
        # --------------------------------------------------

        if (
            return_filing_status
            in (None, "COMPLIANT")
        ):
            return ComplianceEvaluationResult(
                status="PASS",
                reason=(
                    "GST registration is verified and "
                    "no non-compliant return filing "
                    "status was identified."
                ),
                evidence={
                    "gstin": gstin,
                    "verification_status": (
                        verification_status
                    ),
                    "return_filing_status": (
                        return_filing_status
                    ),
                },
            )

        # --------------------------------------------------
        # 8. Unknown filing status
        # --------------------------------------------------

        return ComplianceEvaluationResult(
            status="REVIEW",
            reason="GST return filing status requires review.",
            evidence={
                "gstin": gstin,
                "verification_status": verification_status,
                "return_filing_status": return_filing_status,
            },
        )