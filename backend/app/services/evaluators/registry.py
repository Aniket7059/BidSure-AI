from app.core.taxonomy import RequirementType
from app.services.evaluators.base import RequirementEvaluator

# Alias mapping from alternative/legacy requirement type names to canonical RequirementType
REQUIREMENT_TYPE_ALIASES: dict[str, RequirementType] = {
    "OEM": RequirementType.OEM_AUTHORIZATION,
    "OEM_AUTHORIZATION": RequirementType.OEM_AUTHORIZATION,
    "LOCAL_CONTENT": RequirementType.MAKE_IN_INDIA,
    "MAKE_IN_INDIA": RequirementType.MAKE_IN_INDIA,
    "BLACKLISTING": RequirementType.DEBARMENT,
    "DEBARMENT": RequirementType.DEBARMENT,
    "STARTUP": RequirementType.STARTUP_INDIA,
    "STARTUP_INDIA": RequirementType.STARTUP_INDIA,
    "STARTUP_NSIC": RequirementType.STARTUP_INDIA,
    "NSIC": RequirementType.NSIC,
    "EPFO_ESIC": RequirementType.EPFO,
    "EPFO": RequirementType.EPFO,
    "ESIC": RequirementType.ESIC,
}


class EvaluatorRegistry:
    """
    Registry of requirement evaluators.
    Maps canonical RequirementType (and aliases) to their evaluator.
    """

    def __init__(self):
        self._evaluators: dict[str, RequirementEvaluator] = {}

    def register(
        self,
        evaluator: RequirementEvaluator,
        requirement_type_override: str | None = None,
    ) -> None:
        target_type = (requirement_type_override or evaluator.requirement_type).upper()

        if target_type in self._evaluators:
            raise ValueError(f"Evaluator already registered for type: {target_type}")

        self._evaluators[target_type] = evaluator

    def get(
        self,
        requirement_type: str | RequirementType,
    ) -> RequirementEvaluator | None:
        if hasattr(requirement_type, "value"):
            raw_key = str(requirement_type.value).upper().strip()
        else:
            raw_key = str(requirement_type).upper().strip()

        if raw_key.startswith("REQUIREMENTTYPE."):
            raw_key = raw_key.split(".")[-1]

        # Direct match
        if raw_key in self._evaluators:
            return self._evaluators[raw_key]

        # Alias lookup
        canonical = REQUIREMENT_TYPE_ALIASES.get(raw_key)
        if canonical and canonical.value in self._evaluators:
            return self._evaluators[canonical.value]

        return None


evaluator_registry = EvaluatorRegistry()