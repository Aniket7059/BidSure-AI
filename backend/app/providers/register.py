from app.core.config import settings
from app.providers.debarment.mock import MockDebarmentVerificationAdapter
from app.providers.debarment.provider import DebarmentVerificationProvider
from app.providers.digilocker.mock import MockDigiLockerVerificationAdapter
from app.providers.digilocker.provider import DigiLockerVerificationProvider
from app.providers.epfo_esic.mock import MockEPFOESICVerificationAdapter
from app.providers.epfo_esic.provider import EPFOESICVerificationProvider
from app.providers.gst.mock import MockGSTVerificationAdapter
from app.providers.gst.provider import GSTVerificationProvider
from app.providers.gst_return.mock import MockGSTReturnVerificationAdapter
from app.providers.gst_return.provider import GSTReturnVerificationProvider
from app.providers.income_tax.mock import MockIncomeTaxVerificationAdapter
from app.providers.income_tax.provider import IncomeTaxVerificationProvider
from app.providers.live_adapters import (
    LiveDigiLockerAdapter,
    LiveEPFOAdapter,
    LiveGSTAdapter,
    LiveMCAAdapter,
    LivePANAdapter,
    LiveUdyamAdapter,
)
from app.providers.make_in_india.mock import MockMakeInIndiaVerificationAdapter
from app.providers.make_in_india.provider import MakeInIndiaVerificationProvider
from app.providers.mca21.mock import MockMCA21VerificationAdapter
from app.providers.mca21.provider import MCA21VerificationProvider
from app.providers.oem_authorization.mock import MockOEMAuthorizationVerificationAdapter
from app.providers.oem_authorization.provider import OEMAuthorizationVerificationProvider
from app.providers.pan.mock import MockPANVerificationAdapter
from app.providers.pan.provider import PANVerificationProvider
from app.providers.registry import provider_registry
from app.providers.startup.mock import MockStartupNSICVerificationAdapter
from app.providers.startup.provider import StartupNSICVerificationProvider
from app.providers.udyam.mock import MockUdyamVerificationAdapter
from app.providers.udyam.provider import UdyamVerificationProvider


def register_providers() -> None:
    """Register verification providers available to the application.

    Instantiates live adapters if configured in settings; otherwise
    registers deterministic synthetic mock adapters for development/demo.
    """

    if provider_registry.get("GST_REGISTRATION") is None:
        gst_adapter = (
            LiveGSTAdapter(
                enabled=settings.GST_API_ENABLED,
                base_url=settings.GST_API_URL,
                api_key=settings.GST_API_KEY,
                timeout=settings.GST_API_TIMEOUT,
            )
            if settings.GST_API_ENABLED
            else MockGSTVerificationAdapter()
        )
        provider_registry.register(GSTVerificationProvider(adapter=gst_adapter))

    if provider_registry.get("GST_RETURN_FILING") is None:
        provider_registry.register(
            GSTReturnVerificationProvider(
                adapter=MockGSTReturnVerificationAdapter(),
            )
        )

    if provider_registry.get("PAN_VERIFICATION") is None:
        pan_adapter = (
            LivePANAdapter(
                enabled=settings.PAN_API_ENABLED,
                base_url=settings.PAN_API_URL,
                api_key=settings.PAN_API_KEY,
                timeout=settings.PAN_API_TIMEOUT,
            )
            if settings.PAN_API_ENABLED
            else MockPANVerificationAdapter()
        )
        provider_registry.register(PANVerificationProvider(adapter=pan_adapter))

    if provider_registry.get("INCOME_TAX_COMPLIANCE") is None:
        provider_registry.register(
            IncomeTaxVerificationProvider(
                adapter=MockIncomeTaxVerificationAdapter(),
            )
        )

    if provider_registry.get("UDYAM_VERIFICATION") is None:
        udyam_adapter = (
            LiveUdyamAdapter(
                enabled=settings.UDYAM_API_ENABLED,
                base_url=settings.UDYAM_API_URL,
                api_key=settings.UDYAM_API_KEY,
                timeout=settings.UDYAM_API_TIMEOUT,
            )
            if settings.UDYAM_API_ENABLED
            else MockUdyamVerificationAdapter()
        )
        provider_registry.register(UdyamVerificationProvider(adapter=udyam_adapter))

    if provider_registry.get("MCA21_CORPORATE_CHECK") is None:
        mca_adapter = (
            LiveMCAAdapter(
                enabled=settings.MCA_API_ENABLED,
                base_url=settings.MCA_API_URL,
                api_key=settings.MCA_API_KEY,
                timeout=settings.MCA_API_TIMEOUT,
            )
            if settings.MCA_API_ENABLED
            else MockMCA21VerificationAdapter()
        )
        provider_registry.register(MCA21VerificationProvider(adapter=mca_adapter))

    if provider_registry.get("DEBARMENT_VERIFICATION") is None:
        provider_registry.register(
            DebarmentVerificationProvider(
                adapter=MockDebarmentVerificationAdapter(),
            )
        )

    if provider_registry.get("EPFO_COMPLIANCE") is None:
        epfo_adapter = (
            LiveEPFOAdapter(
                enabled=settings.EPFO_API_ENABLED,
                base_url=settings.EPFO_API_URL,
                api_key=settings.EPFO_API_KEY,
                timeout=settings.EPFO_API_TIMEOUT,
            )
            if settings.EPFO_API_ENABLED
            else MockEPFOESICVerificationAdapter()
        )
        provider_registry.register(EPFOESICVerificationProvider(adapter=epfo_adapter))

    if provider_registry.get("STARTUP_INDIA_CHECK") is None:
        provider_registry.register(
            StartupNSICVerificationProvider(
                adapter=MockStartupNSICVerificationAdapter(),
            )
        )

    if provider_registry.get("MAKE_IN_INDIA") is None:
        provider_registry.register(
            MakeInIndiaVerificationProvider(
                adapter=MockMakeInIndiaVerificationAdapter(),
            )
        )

    if provider_registry.get("OEM_AUTHORIZATION") is None:
        provider_registry.register(
            OEMAuthorizationVerificationProvider(
                adapter=MockOEMAuthorizationVerificationAdapter(),
            )
        )

    if provider_registry.get("DIGILOCKER_VERIFICATION") is None:
        digi_adapter = (
            LiveDigiLockerAdapter(
                enabled=settings.DIGILOCKER_API_ENABLED,
                base_url=settings.DIGILOCKER_API_URL,
                api_key=settings.DIGILOCKER_API_KEY,
                timeout=settings.DIGILOCKER_API_TIMEOUT,
            )
            if settings.DIGILOCKER_API_ENABLED
            else MockDigiLockerVerificationAdapter()
        )
        provider_registry.register(DigiLockerVerificationProvider(adapter=digi_adapter))
