from app.core.taxonomy import RequirementType
from app.schemas.compliance_evaluation import (
    ComplianceEvaluationRequest,
    ComplianceEvaluationResult,
)
from app.schemas.document_extraction import get_extracted_fields
from app.services.evaluators.base import RequirementEvaluator


class OEMAuthorizationEvaluator(RequirementEvaluator):
    """
    Evaluates Original Equipment Manufacturer (OEM) authorization letters.
    """

    @property
    def requirement_type(self) -> str:
        return RequirementType.OEM_AUTHORIZATION.value

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
                reason="No OEM authorization evidence available.",
                evidence={},
            )

        oem_name = fields.get("oem_name") or verification_data.get("oem_name")

        # Explicitly check for is_authorized without unsafe default True
        is_authorized = None
        if "is_authorized" in fields:
            is_authorized = fields.get("is_authorized")
        elif "is_authorized" in verification_data:
            is_authorized = verification_data.get("is_authorized")

        is_expired = fields.get("is_expired") or verification_data.get("is_expired") or False

        v_cfg = self.get_validation_config(request)
        required_oem = v_cfg.get("required_oem_name") or v_cfg.get("required_oem")

        if is_expired or is_authorized is False:
            reason = "OEM authorization letter has expired." if is_expired else "OEM authorization is explicitly not granted."
            return ComplianceEvaluationResult(
                status="FAIL",
                reason=reason,
                evidence={
                    "oem_name": oem_name,
                    "is_authorized": is_authorized,
                    "is_expired": is_expired,
                },
            )

        if required_oem and oem_name:
            if str(oem_name).strip().upper() != str(required_oem).strip().upper():
                return ComplianceEvaluationResult(
                    status="FAIL",
                    reason=f"OEM authorization is for '{oem_name}', but tender requires '{required_oem}'.",
                    evidence={
                        "oem_name": oem_name,
                        "required_oem_name": required_oem,
                    },
                )

        # Missing authorization decision or missing OEM name cannot PASS automatically
        if is_authorized is True and oem_name and not is_expired:
            return ComplianceEvaluationResult(
                status="PASS",
                reason="Valid OEM Manufacturer Authorization Certificate is verified.",
                evidence={
                    "oem_name": oem_name,
                    "is_authorized": True,
                },
            )

        return ComplianceEvaluationResult(
            status="REVIEW",
            reason="OEM authorization document is missing explicit verification decision or OEM identity.",
            evidence={
                "oem_name": oem_name,
                "is_authorized": is_authorized,
                "is_expired": is_expired,
                "extracted_fields": fields,
            },
        )
