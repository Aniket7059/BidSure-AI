from app.providers.gst.provider import GSTVerificationProvider
from app.providers.register import register_providers
from app.providers.registry import provider_registry


def test_register_providers_registers_gst_provider():
    provider_registry.clear()

    try:
        register_providers()

        provider = provider_registry.get("GST_REGISTRATION")

        assert isinstance(provider, GSTVerificationProvider)
        assert provider_registry.get("GST_RETURN_FILING") is not None
    finally:
        provider_registry.clear()
        register_providers()
