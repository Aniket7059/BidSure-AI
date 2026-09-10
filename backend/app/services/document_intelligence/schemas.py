from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DocumentType(str, Enum):
    """
    Supported bidder document types for Document Intelligence.
    Includes all statutory and eligibility document categories required by PS 26100.
    """

    GST_CERTIFICATE = "GST_CERTIFICATE"
    GST_RETURN = "GST_RETURN"
    PAN = "PAN"
    INCOME_TAX = "INCOME_TAX"
    UDYAM_CERTIFICATE = "UDYAM_CERTIFICATE"
    EPFO = "EPFO"
    ESIC = "ESIC"
    STARTUP_INDIA = "STARTUP_INDIA"
    NSIC = "NSIC"
    OEM_AUTHORIZATION = "OEM_AUTHORIZATION"
    MAKE_IN_INDIA = "MAKE_IN_INDIA"
    DIGILOCKER_DOCUMENT = "DIGILOCKER_DOCUMENT"
    BLACKLISTING_DEBARMENT = "BLACKLISTING_DEBARMENT"
    BIDDER_DECLARATION = "BIDDER_DECLARATION"
    GENERAL_CERTIFICATE = "GENERAL_CERTIFICATE"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class DocumentClassificationResponse(BaseModel):
    """
    Structured response produced by the document classification layer.
    """

    document_type: DocumentType

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


class GSTDocumentFields(BaseModel):
    """Fields extracted from a GST registration certificate."""

    model_config = ConfigDict(extra="forbid")

    gstin: str | None = None
    legal_name: str | None = None
    trade_name: str | None = None
    registration_date: str | None = None
    status: str | None = None
    constitution_of_business: str | None = None
    principal_place_of_business: str | None = None
    additional_places_of_business: list[str] | str | None = None
    taxpayer_type: str | None = None
    state_or_jurisdiction: str | None = None
    effective_date: str | None = None
    certificate_number: str | None = None


class GSTReturnDocumentFields(BaseModel):
    """Fields extracted from a GST Return / Filing document (e.g. GSTR-1, GSTR-3B)."""

    model_config = ConfigDict(extra="forbid")

    gstin: str | None = None
    return_type: str | None = None
    financial_year: str | None = None
    tax_period: str | None = None
    filing_date: str | None = None
    filing_status: str | None = None
    arn_acknowledgement_number: str | None = None
    return_period: str | None = None
    filing_frequency: str | None = None
    turnover_or_tax_liability: str | None = None
    return_reference: str | None = None


class PANDocumentFields(BaseModel):
    """Fields extracted from a PAN document / card."""

    model_config = ConfigDict(extra="forbid")

    pan_number: str | None = None
    name: str | None = None
    father_or_mother_name: str | None = None
    date_of_birth_or_incorporation: str | None = None
    pan_holder_type: str | None = None
    document_reference_number: str | None = None


class IncomeTaxDocumentFields(BaseModel):
    """Fields extracted from an Income Tax return / ITR acknowledgement."""

    model_config = ConfigDict(extra="forbid")

    pan_number: str | None = None
    assessment_year: str | None = None
    financial_year: str | None = None
    itr_form: str | None = None
    filing_date: str | None = None
    acknowledgement_number: str | None = None
    gross_total_income: str | None = None
    total_income: str | None = None
    tax_payable: str | None = None
    tax_paid: str | None = None
    return_status: str | None = None
    taxpayer_name: str | None = None


class UdyamDocumentFields(BaseModel):
    """Fields extracted from an Udyam / MSME certificate."""

    model_config = ConfigDict(extra="forbid")

    udyam_number: str | None = None
    enterprise_name: str | None = None
    organisation_type: str | None = None
    major_activity: str | None = None
    date_of_incorporation: str | None = None
    registration_date: str | None = None
    enterprise_category: str | None = None
    nic_code_activity: str | None = None
    address: str | None = None
    state: str | None = None
    district: str | None = None
    authorized_signatory: str | None = None
    status: str | None = None


class EPFODocumentFields(BaseModel):
    """Fields extracted from EPFO registration / compliance proof."""

    model_config = ConfigDict(extra="forbid")

    establishment_id_pf_code: str | None = None
    employer_name: str | None = None
    establishment_name: str | None = None
    registration_date: str | None = None
    establishment_status: str | None = None
    address: str | None = None
    contribution_or_return_period: str | None = None
    filing_reference_number: str | None = None
    employee_summary: str | None = None


class ESICDocumentFields(BaseModel):
    """Fields extracted from ESIC registration / compliance proof."""

    model_config = ConfigDict(extra="forbid")

    employer_code_esic_number: str | None = None
    employer_name: str | None = None
    establishment_name: str | None = None
    registration_date: str | None = None
    address: str | None = None
    registration_status: str | None = None
    contribution_or_filing_period: str | None = None
    acknowledgement_reference: str | None = None


class StartupIndiaDocumentFields(BaseModel):
    """Fields extracted from Startup India Recognition Certificate."""

    model_config = ConfigDict(extra="forbid")

    recognition_number: str | None = None
    entity_name: str | None = None
    cin_or_registration_id: str | None = None
    recognition_date: str | None = None
    status: str | None = None
    dpiit_recognition_details: str | None = None
    business_activity: str | None = None
    address: str | None = None
    validity_period: str | None = None
    certificate_number: str | None = None


class NSICDocumentFields(BaseModel):
    """Fields extracted from NSIC registration certificate."""

    model_config = ConfigDict(extra="forbid")

    nsic_certificate_number: str | None = None
    enterprise_name: str | None = None
    registration_number: str | None = None
    issue_date: str | None = None
    validity_date: str | None = None
    product_or_service_details: str | None = None
    category: str | None = None
    address: str | None = None
    status: str | None = None
    exemption_or_preference_details: str | None = None


class OEMAuthorizationFields(BaseModel):
    """Fields extracted from OEM Authorization Letter."""

    model_config = ConfigDict(extra="forbid")

    oem_name: str | None = None
    authorized_bidder_name: str | None = None
    product_name: str | None = None
    product_model: str | None = None
    product_category: str | None = None
    authorization_reference_number: str | None = None
    authorization_date: str | None = None
    validity_period: str | None = None
    tender_reference: str | None = None
    authorized_scope: str | None = None
    manufacturer_details: str | None = None
    signatory_name: str | None = None
    signatory_designation: str | None = None
    contact_details: str | None = None
    conditions_or_limitations: str | None = None


class MakeInIndiaFields(BaseModel):
    """Fields extracted from Make In India / Local Content Declaration."""

    model_config = ConfigDict(extra="forbid")

    bidder_name: str | None = None
    manufacturer_or_oem_name: str | None = None
    product_name: str | None = None
    country_of_origin: str | None = None
    local_content_percentage: str | None = None
    local_content_class: str | None = None
    local_value_addition_details: str | None = None
    manufacturing_location: str | None = None
    declaration_date: str | None = None
    authorized_signatory: str | None = None
    tender_reference: str | None = None
    certificate_number: str | None = None


class DigiLockerDocumentFields(BaseModel):
    """Fields extracted from DigiLocker issued document metadata."""

    model_config = ConfigDict(extra="forbid")

    issuing_authority: str | None = None
    document_type: str | None = None
    document_title: str | None = None
    document_reference_id: str | None = None
    issued_date: str | None = None
    holder_name: str | None = None
    identifier: str | None = None
    verification_metadata: str | None = None
    qr_reference_info: str | None = None


class BlacklistingDebarmentFields(BaseModel):
    """Fields extracted from Blacklisting / Debarment order or declaration."""

    model_config = ConfigDict(extra="forbid")

    entity_name: str | None = None
    issuing_authority: str | None = None
    debarment_status: str | None = None
    order_reference_number: str | None = None
    order_date: str | None = None
    effective_date: str | None = None
    expiry_date: str | None = None
    reason_or_grounds: str | None = None
    scope_of_debarment: str | None = None
    tender_reference: str | None = None


class BidderDeclarationFields(BaseModel):
    """Fields extracted from tender-specific bidder declarations/undertakings/affidavits."""

    model_config = ConfigDict(extra="forbid")

    bidder_name: str | None = None
    tender_reference: str | None = None
    declaration_type: str | None = None
    declaration_statement: str | None = None
    declared_values: str | None = None
    declaration_date: str | None = None
    signatory_name: str | None = None
    signatory_designation: str | None = None
    organization_name: str | None = None
    reference_number: str | None = None


class GeneralCertificateFields(BaseModel):
    """Fields extracted from general certificates or supporting registration documents."""

    model_config = ConfigDict(extra="forbid")

    certificate_title: str | None = None
    issued_to: str | None = None
    issuing_authority: str | None = None
    certificate_number: str | None = None
    issue_date: str | None = None
    validity_date: str | None = None
    summary_or_scope: str | None = None


class UnknownDocumentFields(BaseModel):
    """Fields for unknown or unclassified documents."""

    model_config = ConfigDict(extra="forbid")

    raw_summary: str | None = None
    detected_keywords: list[str] | None = None


DOCUMENT_FIELDS_UNION = (
    GSTDocumentFields
    | GSTReturnDocumentFields
    | PANDocumentFields
    | IncomeTaxDocumentFields
    | UdyamDocumentFields
    | EPFODocumentFields
    | ESICDocumentFields
    | StartupIndiaDocumentFields
    | NSICDocumentFields
    | OEMAuthorizationFields
    | MakeInIndiaFields
    | DigiLockerDocumentFields
    | BlacklistingDebarmentFields
    | BidderDeclarationFields
    | GeneralCertificateFields
    | UnknownDocumentFields
)


DOCUMENT_TYPE_FIELDS_MAP: dict[DocumentType, type[BaseModel]] = {
    DocumentType.GST_CERTIFICATE: GSTDocumentFields,
    DocumentType.GST_RETURN: GSTReturnDocumentFields,
    DocumentType.PAN: PANDocumentFields,
    DocumentType.INCOME_TAX: IncomeTaxDocumentFields,
    DocumentType.UDYAM_CERTIFICATE: UdyamDocumentFields,
    DocumentType.EPFO: EPFODocumentFields,
    DocumentType.ESIC: ESICDocumentFields,
    DocumentType.STARTUP_INDIA: StartupIndiaDocumentFields,
    DocumentType.NSIC: NSICDocumentFields,
    DocumentType.OEM_AUTHORIZATION: OEMAuthorizationFields,
    DocumentType.MAKE_IN_INDIA: MakeInIndiaFields,
    DocumentType.DIGILOCKER_DOCUMENT: DigiLockerDocumentFields,
    DocumentType.BLACKLISTING_DEBARMENT: BlacklistingDebarmentFields,
    DocumentType.BIDDER_DECLARATION: BidderDeclarationFields,
    DocumentType.GENERAL_CERTIFICATE: GeneralCertificateFields,
}


class DocumentFieldExtractionResponse(BaseModel):
    """
    Common response returned by the structured field extraction layer.
    """

    document_type: DocumentType

    fields: DOCUMENT_FIELDS_UNION

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    @model_validator(mode="after")
    def validate_document_type_matches_fields(self):
        if self.document_type in (DocumentType.UNKNOWN, DocumentType.OTHER):
            raise ValueError(
                "Structured field extraction is not supported for "
                f"document type: {self.document_type.value}"
            )

        expected_type = DOCUMENT_TYPE_FIELDS_MAP.get(self.document_type)

        if expected_type is None:
            raise ValueError(
                "Structured field extraction is not supported for "
                f"document type: {self.document_type.value}"
            )

        if not isinstance(self.fields, expected_type):
            raise ValueError(
                f"Fields type {type(self.fields).__name__} does not match "
                f"document type {self.document_type.value}"
            )

        return self


class ExtractedPage(BaseModel):
    """
    Text extracted from a single document page.
    """

    page_number: int = Field(ge=1)
    text: str


class PDFTextExtractionResult(BaseModel):
    """
    Common result returned by PDF text extraction and OCR extraction.
    """

    pages: list[ExtractedPage]
    total_pages: int = Field(ge=0)
    total_characters: int = Field(ge=0)


class TextExtractionMethod(str, Enum):
    """
    Method used to obtain document text.
    """

    NATIVE_PDF = "NATIVE_PDF"
    OCR = "OCR"


class DocumentIntelligenceResult(BaseModel):
    """
    Complete result produced by the Document Intelligence pipeline.
    """

    document_type: DocumentType

    classification_confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    extraction_method: TextExtractionMethod

    extracted_text: str

    total_pages: int = Field(
        ge=0,
    )

    total_characters: int = Field(
        ge=0,
    )

    fields: DOCUMENT_FIELDS_UNION

    extraction_confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    @model_validator(mode="after")
    def validate_document_type_matches_fields(self):
        if self.document_type in (DocumentType.UNKNOWN, DocumentType.OTHER):
            if not isinstance(self.fields, UnknownDocumentFields):
                raise ValueError(
                    f"Fields type {type(self.fields).__name__} does not match "
                    f"document type {self.document_type.value}"
                )
            return self

        expected_type = DOCUMENT_TYPE_FIELDS_MAP.get(self.document_type)

        if expected_type is None:
            raise ValueError(
                "Document intelligence does not support structured "
                f"extraction for document type: {self.document_type.value}"
            )

        if not isinstance(self.fields, expected_type):
            raise ValueError(
                f"Fields type {type(self.fields).__name__} does not match "
                f"document type {self.document_type.value}"
            )

        return self