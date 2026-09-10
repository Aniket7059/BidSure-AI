from typing import Any
from pydantic import BaseModel, Field


class StandardizedDocumentExtraction(BaseModel):
    """
    Canonical, standardized payload structure for document extractions.

    Example structure:
    {
        "document_type": "GST_CERTIFICATE",
        "fields": {
            "gstin": "29ABCDE1234F1Z5",
            "legal_name": "Acme Private Limited",
            "registration_date": "2020-01-01",
            "status": "ACTIVE"
        }
    }
    """

    document_type: str
    fields: dict[str, Any] = Field(default_factory=dict)
    classification_confidence: float | None = None
    extraction_method: str | None = None
    total_pages: int | None = None
    total_characters: int | None = None


def get_extracted_fields(extracted_data: dict | None) -> dict[str, Any]:
    """
    Safely extract field key-values from an extracted_data payload.
    Supports standardized `{"document_type": "...", "fields": {...}}`
    and legacy flat `{"legal_name": "..."}` data payloads seamlessly.
    """
    if not extracted_data:
        return {}

    # If standardized structure with nested "fields" dict
    if "fields" in extracted_data and isinstance(extracted_data["fields"], dict):
        return extracted_data["fields"]

    # If flat dictionary (excluding metadata keys if any)
    metadata_keys = {
        "document_type",
        "classification_confidence",
        "extraction_method",
        "total_pages",
        "total_characters",
    }
    result = {}
    for k, v in extracted_data.items():
        if k not in metadata_keys:
            result[k] = v
    return result
