from google import genai

from app.core.config import settings
from app.services.document_intelligence.schemas import (
    DocumentClassificationResponse,
    DocumentType,
)


class DocumentClassifier:
    """
    Uses Gemini (with deterministic rule-based fallback) to classify
    bidder documents into supported PS 26100 document types.

    This component performs classification only.
    It does not extract document fields or verify
    information against external government sources.
    """

    SYSTEM_INSTRUCTION = """
You are the document classification component of BidSure AI.

Your task is to classify a bidder document into exactly one of the supported document types.

Supported document types:
1. GST_CERTIFICATE: Goods and Services Tax registration certificate (Form GST REG-06).
2. GST_RETURN: GST Return filing proof or summary (GSTR-1, GSTR-3B, ARN receipt).
3. PAN: Permanent Account Number card or document issued by Income Tax Department.
4. INCOME_TAX: Income Tax Return (ITR-V), acknowledgement, or tax computation document.
5. UDYAM_CERTIFICATE: Udyam Registration / MSME certificate.
6. EPFO: Employees' Provident Fund Organisation registration, code allocation, or ECR payment proof.
7. ESIC: Employees' State Insurance Corporation registration or C-18 contribution proof.
8. STARTUP_INDIA: Startup India Recognition Certificate issued by DPIIT.
9. NSIC: National Small Industries Corporation registration certificate.
10. OEM_AUTHORIZATION: Manufacturer Authorization Form (MAF) / OEM Letter authorizing bidder.
11. MAKE_IN_INDIA: Local Content Self-Declaration or Class-I/II Local Supplier certificate under Public Procurement Order.
12. DIGILOCKER_DOCUMENT: DigiLocker issued document or metadata verification record.
13. BLACKLISTING_DEBARMENT: Declaration, affidavit, or order regarding debarment or blacklisting status.
14. BIDDER_DECLARATION: Tender-specific bidder undertaking, affidavit, integrity pact, or declaration form.
15. GENERAL_CERTIFICATE: General statutory, ISO, incorporation, or business registration certificate.
16. OTHER: Known document type not fitting above categories.
17. UNKNOWN: Document type cannot be determined from text.

Rules:
1. Classify the document only from the supplied document content.
2. Do not extract or invent document field values.
3. If confidence is low or text is ambiguous, classify as UNKNOWN.
4. Confidence must be a value between 0.0 and 1.0.
5. Do not classify a document based only on its filename.
6. This component performs classification only; it does not make compliance or qualification decisions.
""".strip()

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = (
            api_key
            if api_key is not None
            else settings.GEMINI_API_KEY
        )

        self.model = (
            model
            if model is not None
            else settings.GEMINI_MODEL
        )

        # Gemini client is created lazily.
        # This allows tests to inject/mock the client
        # without making real API calls.
        self.client = None

    def classify(
        self,
        document_text: str,
    ) -> DocumentClassificationResponse:
        """
        Classify the supplied document text using Gemini or fallback keyword rules.

        Args:
            document_text: Text extracted from the bidder document.

        Returns:
            DocumentClassificationResponse containing document_type and confidence.
        """

        # Validate document content first.
        if not document_text or not document_text.strip():
            raise ValueError("Document text cannot be empty.")

        # Validate API configuration before creating the client.
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        # Create the Gemini client only when needed.
        if self.client is None:
            self.client = genai.Client(
                api_key=self.api_key,
            )

        response = self.client.interactions.create(
            model=self.model,
            system_instruction=self.SYSTEM_INSTRUCTION,
            input=(
                "Classify the following document.\n\n"
                "Document text:\n"
                f"{document_text}"
            ),
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": (
                    DocumentClassificationResponse
                    .model_json_schema()
                ),
            },
        )

        output_text = response.output_text

        if not output_text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return DocumentClassificationResponse.model_validate_json(
            output_text
        )

    @staticmethod
    def classify_by_keywords(document_text: str) -> DocumentClassificationResponse:
        """
        Deterministic rule/keyword-based classification fallback.
        Useful for offline environments, synthetic text, and tests.
        """
        if not document_text or not document_text.strip():
            raise ValueError("Document text cannot be empty.")

        text_upper = document_text.upper()

        if "FORM GST REG-06" in text_upper or ("GOODS AND SERVICES TAX" in text_upper and "REGISTRATION CERTIFICATE" in text_upper):
            return DocumentClassificationResponse(document_type=DocumentType.GST_CERTIFICATE, confidence=0.95)
        elif "GSTR-" in text_upper or "GST RETURN" in text_upper or ("GSTIN" in text_upper and "FILING" in text_upper):
            return DocumentClassificationResponse(document_type=DocumentType.GST_RETURN, confidence=0.92)
        elif "PERMANENT ACCOUNT NUMBER" in text_upper or ("PAN" in text_upper and "INCOME TAX DEPARTMENT" in text_upper):
            return DocumentClassificationResponse(document_type=DocumentType.PAN, confidence=0.95)
        elif "INCOME TAX RETURN" in text_upper or "ITR-" in text_upper or "ACKNOWLEDGEMENT NUMBER" in text_upper:
            return DocumentClassificationResponse(document_type=DocumentType.INCOME_TAX, confidence=0.95)
        elif "UDYAM REGISTRATION" in text_upper or "UDYAM-" in text_upper or "MSME" in text_upper:
            return DocumentClassificationResponse(document_type=DocumentType.UDYAM_CERTIFICATE, confidence=0.95)
        elif "EMPLOYEES' PROVIDENT FUND" in text_upper or "EPFO" in text_upper or "PF CODE" in text_upper:
            return DocumentClassificationResponse(document_type=DocumentType.EPFO, confidence=0.95)
        elif "EMPLOYEES' STATE INSURANCE" in text_upper or "ESIC" in text_upper or "ESI CODE" in text_upper:
            return DocumentClassificationResponse(document_type=DocumentType.ESIC, confidence=0.95)
        elif "STARTUP INDIA" in text_upper or "DPIIT" in text_upper:
            return DocumentClassificationResponse(document_type=DocumentType.STARTUP_INDIA, confidence=0.95)
        elif "NSIC" in text_upper or "NATIONAL SMALL INDUSTRIES" in text_upper:
            return DocumentClassificationResponse(document_type=DocumentType.NSIC, confidence=0.95)
        elif "OEM AUTHORIZATION" in text_upper or "MANUFACTURER AUTHORIZATION" in text_upper:
            return DocumentClassificationResponse(document_type=DocumentType.OEM_AUTHORIZATION, confidence=0.95)
        elif "LOCAL CONTENT" in text_upper or "MAKE IN INDIA" in text_upper or "CLASS-I LOCAL" in text_upper:
            return DocumentClassificationResponse(document_type=DocumentType.MAKE_IN_INDIA, confidence=0.95)
        elif "DIGILOCKER" in text_upper:
            return DocumentClassificationResponse(document_type=DocumentType.DIGILOCKER_DOCUMENT, confidence=0.95)
        elif "BLACKLIST" in text_upper or "DEBAR" in text_upper:
            return DocumentClassificationResponse(document_type=DocumentType.BLACKLISTING_DEBARMENT, confidence=0.95)
        elif "UNDERTAKING" in text_upper or "BIDDER DECLARATION" in text_upper or "AFFIDAVIT" in text_upper:
            return DocumentClassificationResponse(document_type=DocumentType.BIDDER_DECLARATION, confidence=0.95)
        elif "CERTIFICATE OF INCORPORATION" in text_upper or "REGISTRATION CERTIFICATE" in text_upper:
            return DocumentClassificationResponse(document_type=DocumentType.GENERAL_CERTIFICATE, confidence=0.85)
        else:
            return DocumentClassificationResponse(document_type=DocumentType.UNKNOWN, confidence=0.50)


# Shared classifier instance used by the application.
document_classifier = DocumentClassifier()