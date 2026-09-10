from app.core.taxonomy import RequirementType
from app.schemas.compliance_evaluation import (
    ComplianceEvaluationRequest,
    ComplianceEvaluationResult,
)
from app.schemas.document_extraction import get_extracted_fields
from app.services.evaluators.base import (
    RequirementEvaluator,
)


class IncomeTaxEvaluator(RequirementEvaluator):
    """
    Evaluates PAN and Income Tax compliance requirements
    using document extraction and verification evidence.

    This evaluator does not communicate directly with
    the Income Tax Department. Verification data is
    supplied by the Government Verification module.
    """

    @property
    def requirement_type(self) -> str:
        return RequirementType.INCOME_TAX.value

    def evaluate(
        self,
        request: ComplianceEvaluationRequest,
    ) -> ComplianceEvaluationResult:

        extracted_data = request.extracted_data or {}
        verification_data = request.verification_data or {}
        fields = get_extracted_fields(extracted_data)

        # --------------------------------------------------
        # 1. Check whether any evidence exists
        # --------------------------------------------------

        if not extracted_data and not verification_data:
            return ComplianceEvaluationResult(
                status="REVIEW",
                reason=(
                    "No PAN or Income Tax compliance "
                    "evidence is available."
                ),
                evidence={},
            )

        # --------------------------------------------------
        # 2. Extract PAN from available evidence
        # --------------------------------------------------

        document_pan = fields.get("pan") or fields.get("pan_number")

        verified_pan = verification_data.get("pan")

        # --------------------------------------------------
        # 3. Check PAN consistency
        # --------------------------------------------------

        if (
            document_pan
            and verified_pan
            and document_pan != verified_pan
        ):
            return ComplianceEvaluationResult(
                status="REVIEW",
                reason=(
                    "PAN mismatch between document evidence "
                    "and verification data."
                ),
                evidence={
                    "document_pan": document_pan,
                    "verified_pan": verified_pan,
                },
            )

        pan = verified_pan or document_pan

        # --------------------------------------------------
        # 4. Check verification status
        # --------------------------------------------------

        verification_status = verification_data.get(
            "status"
        )

        if verification_status == "INVALID":
            return ComplianceEvaluationResult(
                status="FAIL",
                reason=(
                    "PAN could not be verified."
                ),
                evidence={
                    "pan": pan,
                    "verification_status": (
                        verification_status
                    ),
                },
            )

        # --------------------------------------------------
        # 5. Check PAN status
        # --------------------------------------------------

        pan_status = verification_data.get(
            "pan_status"
        )

        if pan_status == "INACTIVE":
            return ComplianceEvaluationResult(
                status="FAIL",
                reason=(
                    "PAN is not active."
                ),
                evidence={
                    "pan": pan,
                    "pan_status": pan_status,
                },
            )

        # --------------------------------------------------
        # 6. Check Income Tax compliance & tender-specific turnover rules
        # --------------------------------------------------

        v_cfg = self.get_validation_config(request)
        min_turnover = v_cfg.get("minimum_annual_turnover") if "minimum_annual_turnover" in v_cfg else v_cfg.get("min_turnover")

        if min_turnover is not None:
            turnover_val = fields.get("annual_turnover") or verification_data.get("annual_turnover")
            if turnover_val is not None:
                try:
                    t_num = float(turnover_val)
                    m_num = float(min_turnover)
                    if t_num < m_num:
                        return ComplianceEvaluationResult(
                            status="FAIL",
                            reason=f"Declared annual turnover ({t_num}) is below tender minimum requirement ({m_num}).",
                            evidence={
                                "pan": pan,
                                "annual_turnover": t_num,
                                "minimum_annual_turnover": m_num,
                            },
                        )
                except (ValueError, TypeError):
                    pass

        income_tax_compliance = (
            verification_data.get("income_tax_compliance")
            or verification_data.get("tax_compliance_status")
            or fields.get("income_tax_compliance")
        )

        if income_tax_compliance in ("NON_COMPLIANT", "FAIL", "FAILED"):
            return ComplianceEvaluationResult(
                status="FAIL",
                reason=(
                    "Income Tax compliance requirements "
                    "are not satisfied."
                ),
                evidence={
                    "pan": pan,
                    "pan_status": pan_status,
                    "income_tax_compliance": (
                        income_tax_compliance
                    ),
                },
            )

        # --------------------------------------------------
        # 7. Incomplete verification
        # --------------------------------------------------

        if verification_status != "VERIFIED":
            return ComplianceEvaluationResult(
                status="REVIEW",
                reason=(
                    "PAN and Income Tax verification "
                    "evidence is incomplete."
                ),
                evidence={
                    "pan": pan,
                    "verification_status": (
                        verification_status
                    ),
                    "pan_status": pan_status,
                    "income_tax_compliance": (
                        income_tax_compliance
                    ),
                },
            )

        # --------------------------------------------------
        # 8. Verified PAN and compliant Income Tax status
        # --------------------------------------------------

        if income_tax_compliance in (
            None,
            "COMPLIANT",
        ):
            return ComplianceEvaluationResult(
                status="PASS",
                reason=(
                    "PAN is verified and Income Tax "
                    "compliance requirements are satisfied."
                ),
                evidence={
                    "pan": pan,
                    "verification_status": (
                        verification_status
                    ),
                    "pan_status": pan_status,
                    "income_tax_compliance": (
                        income_tax_compliance
                    ),
                },
            )

        # --------------------------------------------------
        # 9. Unknown compliance state
        # --------------------------------------------------

        return ComplianceEvaluationResult(
            status="REVIEW",
            reason=(
                "Income Tax compliance status "
                "requires review."
            ),
            evidence={
                "pan": pan,
                "verification_status": verification_status,
                "pan_status": pan_status,
                "income_tax_compliance": (
                    income_tax_compliance
                ),
            },
        )