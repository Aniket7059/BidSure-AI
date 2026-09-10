from app.core.taxonomy import RequirementType
from app.schemas.compliance_evaluation import (
    ComplianceEvaluationRequest,
    ComplianceEvaluationResult,
)
from app.schemas.document_extraction import get_extracted_fields
from app.services.evaluators.base import RequirementEvaluator


class MCA21Evaluator(RequirementEvaluator):
    """
    Evaluates MCA21 corporate incorporation and active company status.
    """

    @property
    def requirement_type(self) -> str:
        return RequirementType.MCA21.value

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
                reason="No MCA21 corporate check evidence available.",
                evidence={},
            )

        company_status = (
            verification_data.get("company_status")
            or fields.get("company_status")
        )

        v_cfg = self.get_validation_config(request)
        min_paid_up = v_cfg.get("minimum_paid_up_capital") if "minimum_paid_up_capital" in v_cfg else v_cfg.get("min_paid_up_capital")

        paid_up = verification_data.get("paid_up_capital") or fields.get("paid_up_capital")
        if min_paid_up is not None and paid_up is not None:
            try:
                p_num = float(paid_up)
                m_num = float(min_paid_up)
                if p_num < m_num:
                    return ComplianceEvaluationResult(
                        status="FAIL",
                        reason=f"Company paid-up capital ({p_num}) is below tender minimum requirement ({m_num}).",
                        evidence={
                            "cin": verification_data.get("cin") or fields.get("cin"),
                            "company_status": company_status,
                            "paid_up_capital": p_num,
                            "minimum_paid_up_capital": m_num,
                        },
                    )
            except (ValueError, TypeError):
                pass

        if company_status in ("STRUCK_OFF", "DORMANT", "DISSOLVED"):
            return ComplianceEvaluationResult(
                status="FAIL",
                reason=f"Company status is non-active ({company_status}) in MCA21 registry.",
                evidence={
                    "cin": verification_data.get("cin") or fields.get("cin"),
                    "company_status": company_status,
                },
            )

        if company_status == "ACTIVE":
            return ComplianceEvaluationResult(
                status="PASS",
                reason="Company is active and in good standing with MCA21 registry.",
                evidence={
                    "cin": verification_data.get("cin") or extracted_data.get("cin"),
                    "company_name": verification_data.get("company_name"),
                    "company_status": company_status,
                },
            )

        return ComplianceEvaluationResult(
            status="REVIEW",
            reason="MCA21 corporate filing evidence requires officer review.",
            evidence=verification_data,
        )
