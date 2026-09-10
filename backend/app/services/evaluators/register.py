from app.core.taxonomy import RequirementType
from app.services.evaluators.gst_evaluator import GSTEvaluator
from app.services.evaluators.udyam_evaluator import UdyamEvaluator
from app.services.evaluators.income_tax_evaluator import IncomeTaxEvaluator
from app.services.evaluators.debarment_evaluator import DebarmentEvaluator
from app.services.evaluators.epfo_esic_evaluator import EPFOESICEvaluator
from app.services.evaluators.mca21_evaluator import MCA21Evaluator
from app.services.evaluators.make_in_india_evaluator import MakeInIndiaEvaluator
from app.services.evaluators.oem_authorization_evaluator import OEMAuthorizationEvaluator
from app.services.evaluators.startup_nsic_evaluator import StartupNSICEvaluator
from app.services.evaluators.registry import evaluator_registry


def register_evaluators() -> None:
    """
    Register all requirement evaluators under canonical RequirementType keys.
    """

    if evaluator_registry.get(RequirementType.GST) is None:
        evaluator_registry.register(GSTEvaluator())

    if evaluator_registry.get(RequirementType.UDYAM) is None:
        evaluator_registry.register(UdyamEvaluator())

    if evaluator_registry.get(RequirementType.INCOME_TAX) is None:
        evaluator_registry.register(IncomeTaxEvaluator())

    if evaluator_registry.get(RequirementType.PAN) is None:
        evaluator_registry.register(IncomeTaxEvaluator(), requirement_type_override=RequirementType.PAN.value)

    if evaluator_registry.get(RequirementType.DEBARMENT) is None:
        evaluator_registry.register(DebarmentEvaluator())

    epfo_esic_eval = EPFOESICEvaluator()
    if evaluator_registry.get(RequirementType.EPFO) is None:
        evaluator_registry.register(epfo_esic_eval, requirement_type_override=RequirementType.EPFO.value)
    if evaluator_registry.get(RequirementType.ESIC) is None:
        evaluator_registry.register(epfo_esic_eval, requirement_type_override=RequirementType.ESIC.value)

    if evaluator_registry.get(RequirementType.MCA21) is None:
        evaluator_registry.register(MCA21Evaluator())

    if evaluator_registry.get(RequirementType.MAKE_IN_INDIA) is None:
        evaluator_registry.register(MakeInIndiaEvaluator())

    if evaluator_registry.get(RequirementType.OEM_AUTHORIZATION) is None:
        evaluator_registry.register(OEMAuthorizationEvaluator())

    startup_nsic_eval = StartupNSICEvaluator()
    if evaluator_registry.get(RequirementType.STARTUP_INDIA) is None:
        evaluator_registry.register(startup_nsic_eval, requirement_type_override=RequirementType.STARTUP_INDIA.value)
    if evaluator_registry.get(RequirementType.NSIC) is None:
        evaluator_registry.register(startup_nsic_eval, requirement_type_override=RequirementType.NSIC.value)