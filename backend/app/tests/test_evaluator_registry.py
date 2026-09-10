from app.services.evaluators.gst_evaluator import (
    GSTEvaluator,
)

from app.services.evaluators.registry import (
    EvaluatorRegistry,
)

from app.services.evaluators.register import (
    register_evaluators,
)
from app.services.evaluators.udyam_evaluator import (
    UdyamEvaluator,
)

def test_gst_evaluator_can_be_registered():

    registry = EvaluatorRegistry()

    evaluator = GSTEvaluator()

    registry.register(evaluator)

    registered = registry.get("GST")

    assert registered is evaluator


def test_gst_evaluator_registration_is_case_insensitive():

    registry = EvaluatorRegistry()

    evaluator = GSTEvaluator()

    registry.register(evaluator)

    assert registry.get("GST") is evaluator
    assert registry.get("gst") is evaluator
    assert registry.get("Gst") is evaluator


def test_duplicate_gst_registration_is_rejected():

    registry = EvaluatorRegistry()

    registry.register(
        GSTEvaluator()
    )

    try:
        registry.register(
            GSTEvaluator()
        )

        assert False, (
            "Duplicate GST evaluator "
            "registration should fail."
        )

    except ValueError as exc:

        assert (
            "Evaluator already registered"
            in str(exc)
        )


def test_register_evaluators_registers_gst():

    register_evaluators()

    from app.services.evaluators.registry import (
        evaluator_registry,
    )

    evaluator = evaluator_registry.get("GST")

    assert evaluator is not None

    assert isinstance(
        evaluator,
        GSTEvaluator,
    )

def test_register_evaluators_registers_udyam():

    register_evaluators()

    from app.services.evaluators.registry import (
        evaluator_registry,
    )

    evaluator = evaluator_registry.get("UDYAM")

    assert evaluator is not None

    assert isinstance(
        evaluator,
        UdyamEvaluator,
    )