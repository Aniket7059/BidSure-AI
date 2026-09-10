from app.core.taxonomy import RequirementType
from app.schemas.compliance_evaluation import (
    ComplianceEvaluationRequest,
    ComplianceEvaluationResult,
)
from app.schemas.document_extraction import get_extracted_fields
from app.services.evaluators.base import RequirementEvaluator


class MakeInIndiaEvaluator(RequirementEvaluator):
    """
    Evaluates Make in India / Local Content percentage requirements.
    """

    @property
    def requirement_type(self) -> str:
        return RequirementType.MAKE_IN_INDIA.value

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
                reason="No Make in India / Local Content evidence available.",
                evidence={},
            )

        local_content_pct = (
            fields.get("local_content_percentage")
            or verification_data.get("local_content_percentage")
        )

        v_cfg = self.get_validation_config(request)
        raw_min = (
            v_cfg.get("minimum_local_content")
            if "minimum_local_content" in v_cfg
            else v_cfg.get("minimum_local_content_pct")
            if "minimum_local_content_pct" in v_cfg
            else v_cfg.get("min_local_content")
            if "min_local_content" in v_cfg
            else v_cfg.get("min_local_content_pct")
            if "min_local_content_pct" in v_cfg
            else v_cfg.get("required_min_pct")
            if "required_min_pct" in v_cfg
            else v_cfg.get("minimum_percentage")
        )
        required_min_pct = float(raw_min) if raw_min is not None else 50.0

        if local_content_pct is None:
            return ComplianceEvaluationResult(
                status="REVIEW",
                reason="Local content percentage declaration is missing.",
                evidence=extracted_data,
            )

        try:
            pct_val = float(local_content_pct)
        except (ValueError, TypeError):
            return ComplianceEvaluationResult(
                status="REVIEW",
                reason="Local content percentage value is invalid.",
                evidence={"local_content_percentage": local_content_pct},
            )

        if pct_val >= required_min_pct:
            return ComplianceEvaluationResult(
                status="PASS",
                reason=f"Declared local content ({pct_val}%) meets the minimum requirement ({required_min_pct}%).",
                evidence={
                    "local_content_percentage": pct_val,
                    "required_minimum_percentage": required_min_pct,
                    "supplier_tier": "Class-I Local Supplier" if pct_val >= 50 else "Class-II Local Supplier",
                },
            )

        return ComplianceEvaluationResult(
            status="FAIL",
            reason=f"Declared local content ({pct_val}%) is below the minimum required ({required_min_pct}%).",
            evidence={
                "local_content_percentage": pct_val,
                "required_minimum_percentage": required_min_pct,
            },
        )
