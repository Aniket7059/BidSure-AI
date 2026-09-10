import logging
from typing import Any
from urllib.parse import urlparse

import httpx

from app.providers.schemas import SourceMode

logger = logging.getLogger(__name__)


class BaseLiveHttpAdapter:
    """
    Base class for legitimate live government / authorized API adapters.

    Security & Failure Semantics:
    - Enforces server-side configured base URLs only (prevents SSRF attacks).
    - Configured timeout enforcement.
    - Upstream 4xx/5xx errors, timeouts, or malformed JSON NEVER silently produce VERIFIED results.
    - Missing credentials return explicit OFFICIAL_INTEGRATION_NOT_CONFIGURED status.
    """

    def __init__(
        self,
        enabled: bool = False,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 10,
        source_mode: SourceMode = SourceMode.OFFICIAL_API,
    ) -> None:
        self.enabled = enabled
        self.base_url = base_url.rstrip("/") if base_url else None
        self.api_key = api_key
        self.timeout = timeout
        self.source_mode = source_mode

    def is_configured(self) -> bool:
        return bool(self.enabled and self.base_url and self.api_key)

    def validate_url(self, target_url: str) -> bool:
        """Validate destination URL against server-configured base_url to prevent SSRF."""
        if not self.base_url or not target_url:
            return False
        parsed_target = urlparse(target_url)
        parsed_base = urlparse(self.base_url)

        return (
            parsed_target.scheme in ("http", "https")
            and parsed_target.netloc == parsed_base.netloc
        )

    def execute_get(
        self,
        endpoint_path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[dict[str, Any] | None, str | None, str | None]:
        """
        Execute an HTTP GET request to a trusted server-configured endpoint.

        Returns: (data_dict, error_message, detailed_reason)
        """
        if not self.is_configured():
            return None, "Integration is not configured or disabled.", "OFFICIAL_INTEGRATION_NOT_CONFIGURED"

        full_url = f"{self.base_url}/{endpoint_path.lstrip('/')}"
        if not self.validate_url(full_url):
            return None, "Target URL validation failed (SSRF Protection).", "UNTRUSTED_DESTINATION_URL"

        req_headers = {"User-Agent": "BidSure-AI-GovernmentConnector/1.0", "Accept": "application/json"}
        if self.api_key:
            req_headers["Authorization"] = f"Bearer {self.api_key}"
            req_headers["x-api-key"] = self.api_key
        if headers:
            req_headers.update(headers)

        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=False) as client:
                resp = client.get(full_url, params=params, headers=req_headers)

            if resp.status_code == 401 or resp.status_code == 403:
                return None, f"Upstream authorization failed (HTTP {resp.status_code}).", "AUTHENTICATION_FAILED"
            elif resp.status_code == 404:
                return None, "Identifier not found in upstream portal.", "NOT_FOUND"
            elif resp.status_code >= 400:
                return None, f"Upstream error (HTTP {resp.status_code}).", f"UPSTREAM_HTTP_{resp.status_code}"

            payload = resp.json()
            if not isinstance(payload, dict):
                return None, "Malformed upstream response payload.", "MALFORMED_RESPONSE"

            return payload, None, None

        except httpx.TimeoutException:
            logger.warning(f"Timeout calling {full_url}")
            return None, f"Upstream request timed out after {self.timeout}s.", "UPSTREAM_TIMEOUT"
        except httpx.RequestError as exc:
            logger.warning(f"Connection error calling {full_url}: {exc}")
            return None, f"Connection failed: {str(exc)}", "UPSTREAM_UNAVAILABLE"
        except Exception as exc:
            logger.warning(f"Unexpected error parsing response from {full_url}: {exc}")
            return None, f"Error processing response: {str(exc)}", "PROCESSING_ERROR"
