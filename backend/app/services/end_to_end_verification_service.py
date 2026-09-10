from sqlalchemy.orm import Session

from app.providers.register import register_providers
from app.providers.registry import provider_registry
from app.providers.schemas import VerificationRequest, map_to_requirement_type
from app.repositories.bid_document_repository import bid_document_repository
from app.repositories.bid_submission_repository import bid_submission_repository
from app.repositories.bidder_repository import bidder_repository
from app.repositories.document_extraction_repository import DocumentExtractionRepository
from app.repositories.tender_repository import tender_repository
from app.repositories.tender_requirement_repository import tender_requirement_repository
from app.repositories.compliance_check_repository import compliance_check_repository
from app.schemas.document_extraction import get_extracted_fields
from app.schemas.end_to_end_verification import (
    DocumentExtractionSummaryItem,
    EndToEndVerificationSummary,
    ProviderVerificationSummaryItem,
)
from app.services.compliance_assessment_service import (
    compliance_assessment_service,
)
from app.services.compliance_service import compliance_service
from app.services.cross_verification_service import cross_verification_service
from app.services.document_intelligence.document_service import (
    document_processing_service,
)
from app.services.evaluators.register import register_evaluators
from app.services.verification_service import verification_service


class EndToEndVerificationService:
    """
    Coordinates the full end-to-end verification workflow for a bid submission.

    Workflow Steps:
    1. Retrieve bid submission and associated tender.
    2. Find all submitted bid documents.
    3. Run Document Intelligence extraction pipeline on documents.
    4. Execute applicable statutory verification providers using extracted data and bidder profile.
    5. Perform multi-document cross-verification (inconsistency detection).
    6. Run Task 8 Compliance Engine for all tender requirements.
    7. Generate overall compliance assessment.
    8. Return structured summary report.
    """

    def __init__(self):
        self.extraction_repo = DocumentExtractionRepository()

    def verify_bid_submission(
        self,
        db: Session,
        bid_submission_id: int,
    ) -> EndToEndVerificationSummary:
        # Ensure providers & evaluators are registered
        register_providers()
        register_evaluators()

        # --------------------------------------------------
        # Step 1 & 2: Find bid submission & tender
        # --------------------------------------------------
        submission = bid_submission_repository.get_by_id(db, bid_submission_id)
        if submission is None:
            raise ValueError(f"Bid submission not found: {bid_submission_id}")

        tender = tender_repository.get_by_id(db, submission.tender_id)
        if tender is None:
            raise ValueError(f"Tender not found: {submission.tender_id}")

        bidder = getattr(submission, "bidder", None)
        if not bidder and submission.bidder_id:
            bidder = bidder_repository.get_by_id(db, submission.bidder_id)

        workflow_log: list[str] = []

        # --------------------------------------------------
        # Step 3 & 4: Find & Process Documents
        # --------------------------------------------------
        documents = bid_document_repository.get_by_submission_id(
            db, bid_submission_id
        )
        workflow_log.append(
            f"Found {len(documents)} document(s) for submission #{bid_submission_id}."
        )

        extracted_docs_summary: list[DocumentExtractionSummaryItem] = []
        for doc in documents:
            latest_ext = self.extraction_repo.get_latest_by_document_id(
                db, doc.id
            )
            if (
                latest_ext
                and latest_ext.extraction_status == "COMPLETED"
                and latest_ext.extracted_data
            ):
                extracted_docs_summary.append(
                    DocumentExtractionSummaryItem(
                        document_id=doc.id,
                        file_name=doc.file_name,
                        document_type=doc.document_type,
                        status="COMPLETED",
                        error=None,
                    )
                )
                continue

            try:
                extraction = document_processing_service.process_document(
                    db, doc.id, doc.file_path
                )
                ext_status = getattr(
                    extraction, "extraction_status", "COMPLETED"
                )
                error_msg = getattr(extraction, "error_message", None)
                extracted_docs_summary.append(
                    DocumentExtractionSummaryItem(
                        document_id=doc.id,
                        file_name=doc.file_name,
                        document_type=doc.document_type,
                        status=ext_status,
                        error=error_msg,
                    )
                )
            except Exception as exc:
                extracted_docs_summary.append(
                    DocumentExtractionSummaryItem(
                        document_id=doc.id,
                        file_name=doc.file_name,
                        document_type=doc.document_type,
                        status="FAILED",
                        error=str(exc),
                    )
                )

        workflow_log.append(
            f"Processed {len(extracted_docs_summary)} document extraction(s)."
        )

        # --------------------------------------------------
        # Step 5: Execute Verification Providers
        # --------------------------------------------------
        requirements = tender_requirement_repository.get_by_tender_id(
            db, tender.id
        )

        # Map extracted fields by requirement type (supporting multiple documents)
        extracted_data_by_req: dict[str, list[dict]] = {}
        doc_id_by_req: dict[str, int] = {}

        for doc in documents:
            ext = self.extraction_repo.get_latest_by_document_id(db, doc.id)
            if ext and ext.extracted_data:
                req_key = map_to_requirement_type(
                    doc.document_type
                    or ext.extracted_data.get("document_type")
                )
                fields = get_extracted_fields(ext.extracted_data)
                if req_key not in extracted_data_by_req:
                    extracted_data_by_req[req_key] = []
                extracted_data_by_req[req_key].append(fields)
                if req_key not in doc_id_by_req:
                    doc_id_by_req[req_key] = doc.id

        verifications_summary: list[ProviderVerificationSummaryItem] = []

        for req in requirements:
            req_type_canonical = map_to_requirement_type(req.requirement_type)
            doc_fields_list = extracted_data_by_req.get(req_type_canonical, [])
            has_submitted_doc = len(doc_fields_list) > 0
            # Merge fields across all submitted documents for this requirement
            fields: dict = {}
            for f_dict in doc_fields_list:
                for k, v in f_dict.items():
                    if v and k not in fields:
                        fields[k] = v
            doc_id = doc_id_by_req.get(req_type_canonical)

            # Resolve identifier from extracted fields or bidder profile
            identifier = None
            if req_type_canonical == "GST":
                identifier = fields.get("gstin")
                if not identifier and has_submitted_doc and bidder:
                    identifier = getattr(bidder, "gstin", None)
            elif req_type_canonical == "UDYAM":
                identifier = fields.get("udyam_number")
                if not identifier and has_submitted_doc and bidder:
                    identifier = getattr(bidder, "udyam_number", None)
            elif req_type_canonical in ("PAN", "INCOME_TAX"):
                identifier = fields.get("pan_number") or fields.get("pan")
                if not identifier and has_submitted_doc and bidder:
                    identifier = getattr(bidder, "pan", None)
            elif req_type_canonical == "EPFO":
                identifier = (
                    fields.get("establishment_id_pf_code")
                    or fields.get("est_code")
                    or fields.get("epfo_code")
                )
                if not identifier and has_submitted_doc and bidder:
                    identifier = getattr(bidder, "pan", None)
            elif req_type_canonical == "ESIC":
                identifier = (
                    fields.get("employer_code_esic_number")
                    or fields.get("esic_code")
                    or fields.get("esic_number")
                )
                if not identifier and has_submitted_doc and bidder:
                    identifier = getattr(bidder, "pan", None)
            elif req_type_canonical == "MCA21":
                identifier = fields.get("cin") or (
                    getattr(bidder, "company_name", None) if bidder else None
                )
            elif req_type_canonical == "DEBARMENT":
                identifier = (
                    (getattr(bidder, "pan", None) if bidder else None)
                    or fields.get("pan_number")
                    or fields.get("pan")
                    or (getattr(bidder, "company_name", None) if bidder else None)
                )
            elif req_type_canonical in ("STARTUP_INDIA", "NSIC"):
                identifier = (
                    fields.get("recognition_number")
                    or fields.get("nsic_certificate_number")
                    or fields.get("dipp_number")
                    or fields.get("certificate_number")
                )
                if not identifier and has_submitted_doc and bidder:
                    identifier = getattr(bidder, "company_name", None)
            elif req_type_canonical == "OEM_AUTHORIZATION":
                identifier = (
                    fields.get("authorization_reference_number")
                    or fields.get("oem_name")
                    or fields.get("oem_code")
                )
                if not identifier and has_submitted_doc:
                    identifier = "OEM-AUTH"
            elif req_type_canonical == "MAKE_IN_INDIA":
                identifier = (
                    fields.get("certificate_number")
                    or fields.get("declaration_ref")
                    or fields.get("bidder_name")
                )
                if not identifier and has_submitted_doc:
                    identifier = "MII-DECL"
            elif req_type_canonical == "DIGILOCKER":
                identifier = (
                    fields.get("digilocker_uri")
                    or fields.get("document_reference")
                    or fields.get("uri")
                )
                if not identifier and has_submitted_doc:
                    identifier = "in.gov.digilocker.doc.verified"

            provider = provider_registry.get(req_type_canonical)
            if provider is None:
                verifications_summary.append(
                    ProviderVerificationSummaryItem(
                        requirement_type=req_type_canonical,
                        identifier=str(identifier) if identifier else None,
                        status="NOT_AVAILABLE",
                        source=req_type_canonical,
                        error=f"No verification provider registered for type: {req_type_canonical}",
                    )
                )
                continue

            if identifier:
                try:
                    ver_req = VerificationRequest(
                        identifier=str(identifier).strip(),
                        verification_type=req_type_canonical,
                    )
                    res = verification_service.verify(
                        db=db,
                        bid_submission_id=bid_submission_id,
                        request=ver_req,
                        bid_document_id=doc_id,
                    )
                    res_status = (
                        res.status.value
                        if hasattr(res.status, "value")
                        else str(res.status)
                    )
                    verifications_summary.append(
                        ProviderVerificationSummaryItem(
                            requirement_type=req_type_canonical,
                            identifier=str(identifier),
                            status=res_status,
                            source=res.source or res.provider,
                            error=res.error_message,
                        )
                    )

                    # For GST, execute GST Return verification alongside registration verification
                    if req_type_canonical == "GST":
                        try:
                            ver_req_ret = VerificationRequest(
                                identifier=str(identifier).strip(),
                                verification_type="GST_RETURN",
                            )
                            res_ret = verification_service.verify(
                                db=db,
                                bid_submission_id=bid_submission_id,
                                request=ver_req_ret,
                                bid_document_id=doc_id,
                            )
                            res_ret_status = (
                                res_ret.status.value
                                if hasattr(res_ret.status, "value")
                                else str(res_ret.status)
                            )
                            verifications_summary.append(
                                ProviderVerificationSummaryItem(
                                    requirement_type="GST_RETURN",
                                    identifier=str(identifier),
                                    status=res_ret_status,
                                    source=res_ret.source or res_ret.provider,
                                    error=res_ret.error_message,
                                )
                            )
                        except Exception:
                            pass
                except Exception as exc:
                    verifications_summary.append(
                        ProviderVerificationSummaryItem(
                            requirement_type=req_type_canonical,
                            identifier=str(identifier),
                            status="ERROR",
                            source=req_type_canonical,
                            error=str(exc),
                        )
                    )
            else:
                verifications_summary.append(
                    ProviderVerificationSummaryItem(
                        requirement_type=req_type_canonical,
                        identifier=None,
                        status="SKIPPED_NO_IDENTIFIER",
                        source=req_type_canonical,
                        error="No identifier found in documents or bidder profile",
                    )
                )

        workflow_log.append(
            f"Executed {len(verifications_summary)} verification check(s)."
        )

        # --------------------------------------------------
        # Step 6: Cross-Verification
        # --------------------------------------------------
        cross_res = cross_verification_service.cross_verify_submission(
            db, bid_submission_id
        )
        workflow_log.append(
            f"Cross-verification completed. Discrepancies count: {cross_res.discrepancies_count}."
        )

        # --------------------------------------------------
        # Step 7 & 8: Compliance Engine & Assessment
        # --------------------------------------------------
        assessment = compliance_assessment_service.assess_submission(
            db, bid_submission_id
        )
        checks = compliance_check_repository.get_by_submission(
            db, bid_submission_id
        )
        workflow_log.append(
            f"Evaluated {len(checks)} compliance rule check(s)."
        )
        workflow_log.append(
            f"Generated compliance assessment: Status={assessment.status}, Score={assessment.score}, Risk={assessment.risk_level}."
        )

        # --------------------------------------------------
        # Step 9: Return Summary
        # --------------------------------------------------
        return EndToEndVerificationSummary(
            bid_submission_id=bid_submission_id,
            tender_id=submission.tender_id,
            status="COMPLETED",
            documents_processed_count=len(extracted_docs_summary),
            verifications_executed_count=len(verifications_summary),
            has_discrepancies=cross_res.has_discrepancies,
            discrepancies_count=cross_res.discrepancies_count,
            compliance_checks_count=len(checks),
            overall_status=assessment.status,
            compliance_score=assessment.score,
            risk_level=assessment.risk_level,
            summary=assessment.summary,
            documents_summary=extracted_docs_summary,
            verifications_summary=verifications_summary,
            workflow_log=workflow_log,
        )


end_to_end_verification_service = EndToEndVerificationService()
