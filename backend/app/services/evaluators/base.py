from abc import ABC, abstractmethod

from app.schemas.compliance_evaluation import (
    ComplianceEvaluationRequest,
    ComplianceEvaluationResult,
)


class RequirementEvaluator(ABC):
    """
    Base contract for all tender requirement evaluators.
    """

    @property
    @abstractmethod
    def requirement_type(self) -> str:
        """
        Return the requirement type handled by this evaluator.
        """
        raise NotImplementedError

    @abstractmethod
    def evaluate(
        self,
        request: ComplianceEvaluationRequest,
    ) -> ComplianceEvaluationResult:
        """
        Evaluate the supplied evidence against the requirement.
        """
        raise NotImplementedError

    def get_validation_config(
        self,
        request: ComplianceEvaluationRequest,
    ) -> dict:
        """
        Parse and return the tender-specific validation_config dictionary.
        """
        import json

        config = request.validation_config
        if not config:
            return {}
        if isinstance(config, dict):
            return config
        if isinstance(config, str):
            try:
                val = json.loads(config)
                if isinstance(val, dict):
                    return val
            except Exception:
                pass
        return {}