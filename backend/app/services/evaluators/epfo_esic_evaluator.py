from app.core.taxonomy import RequirementType
from app.schemas.compliance_evaluation import (
    ComplianceEvaluationRequest,
    ComplianceEvaluationResult,
)
from app.schemas.document_extraction import get_extracted_fields
from app.services.evaluators.base import RequirementEvaluator


class EPFOESICEvaluator(RequirementEvaluator):
    """
    Evaluates EPFO and ESIC statutory labor compliance.
    """

    @property
    def requirement_type(self) -> str:
        return RequirementType.EPFO.value

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
                reason="No EPFO/ESIC compliance evidence available.",
                evidence={},
            )

        filing_status = (
            verification_data.get("monthly_filing_status")
            or fields.get("monthly_filing_status")
        )
        coverage_status = (
            verification_data.get("coverage_status")
            or fields.get("coverage_status")
        )

        v_status = str(verification_data.get("status") or verification_data.get("verification_status") or "").upper()
        if v_status in ("FAILED", "INVALID"):
            return ComplianceEvaluationResult(
                status="FAIL",
                reason="EPFO/ESIC verification failed or establishment code is invalid.",
                evidence={
                    "verification_status": v_status,
                    "monthly_filing_status": filing_status,
                },
            )

        v_cfg = self.get_validation_config(request)
        min_members = v_cfg.get("minimum_active_members") if "minimum_active_members" in v_cfg else v_cfg.get("min_member_count")

        active_members = verification_data.get("active_member_count") or fields.get("active_member_count")
        if min_members is not None and active_members is not None:
            try:
                a_num = int(active_members)
                m_num = int(min_members)
                if a_num < m_num:
                    return ComplianceEvaluationResult(
                        status="FAIL",
                        reason=f"Active EPFO member count ({a_num}) is below tender minimum requirement ({m_num}).",
                        evidence={
                            "active_member_count": a_num,
                            "minimum_active_members": m_num,
                            "monthly_filing_status": filing_status,
                        },
                    )
            except (ValueError, TypeError):
                pass

        if filing_status == "DEFAULTED":
            return ComplianceEvaluationResult(
                status="FAIL",
                reason="Statutory EPFO/ESIC monthly ECR filings are in default status.",
                evidence={
                    "monthly_filing_status": filing_status,
                    "coverage_status": coverage_status,
                },
            )

        if filing_status == "COMPLIANT" and coverage_status in ("ACTIVE", None) and (v_status in ("VERIFIED", "") or not verification_data):
            return ComplianceEvaluationResult(
                status="PASS",
                reason="EPFO/ESIC establishment coverage and monthly filing are compliant.",
                evidence={
                    "monthly_filing_status": filing_status,
                    "coverage_status": coverage_status or "ACTIVE",
                    "active_member_count": verification_data.get("active_member_count"),
                },
            )

        return ComplianceEvaluationResult(
            status="REVIEW",
            reason="EPFO/ESIC compliance evidence requires officer review.",
            evidence={
                "monthly_filing_status": filing_status,
                "coverage_status": coverage_status,
            },
        )
