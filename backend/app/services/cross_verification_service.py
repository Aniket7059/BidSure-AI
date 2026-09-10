from datetime import datetime, timezone
import re
from typing import Any
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.repositories.bid_document_repository import bid_document_repository
from app.repositories.document_extraction_repository import DocumentExtractionRepository
from app.repositories.verification_result_repository import verification_result_repository
from app.repositories.bid_submission_repository import bid_submission_repository
from app.schemas.document_extraction import get_extracted_fields


def normalize_name(name: str | None) -> str:
    if not name or not isinstance(name, str):
        return ""
    # Remove corporate suffixes and non-alphanumeric chars for clean matching
    cleaned = name.upper()
    cleaned = re.sub(r"\b(PVT|LTD|PRIVATE|LIMITED|INC|CORP|LLP|COMPANY|ENTERPRISE)\b", "", cleaned)
    cleaned = re.sub(r"[^A-Z0-9]", "", cleaned)
    return cleaned


GSTIN_PATTERN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9]Z[A-Z0-9]$")
PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


def get_v_provider(v: Any) -> str:
    from app.providers.schemas import map_to_requirement_type

    v_type = None
    for attr in ("verification_type", "source", "provider"):
        val = getattr(v, attr, None)
        if isinstance(val, str) and val:
            v_type = val
            break

    if v_type:
        return map_to_requirement_type(v_type)
    return ""





class DiscrepancyItem(BaseModel):
    discrepancy_type: str
    severity: str  # HIGH, MEDIUM, LOW
    field: str
    source_a: str
    source_b: str
    message: str


class CrossVerificationResult(BaseModel):
    bid_submission_id: int
    has_discrepancies: bool
    discrepancies_count: int
    discrepancies: list[DiscrepancyItem]


class CrossVerificationService:
    """
    Cross-checks information across submitted bidder documents, bidder profile, and government portal evidence.
    Identifies missing and inconsistent information as mandated by Problem Statement 26100.
    """

    def __init__(
        self,
        doc_repo=bid_document_repository,
        extraction_repo=None,
        verification_repo=verification_result_repository,
        submission_repo=bid_submission_repository,
    ):
        self.doc_repo = doc_repo
        self.extraction_repo = extraction_repo or DocumentExtractionRepository()
        self.verification_repo = verification_repo
        self.submission_repo = submission_repo

    def cross_verify_submission(
        self,
        db: Session,
        bid_submission_id: int,
    ) -> CrossVerificationResult:
        documents = self.doc_repo.get_by_submission_id(db, bid_submission_id)
        verifications = self.verification_repo.get_by_submission(db, bid_submission_id)
        submission = self.submission_repo.get_by_id(db, bid_submission_id)
        bidder = getattr(submission, "bidder", None) if submission else None

        extractions = []
        for doc in documents:
            ext = self.extraction_repo.get_latest_by_document_id(db, doc.id)
            if ext and ext.extracted_data:
                extractions.append({
                    "document_id": doc.id,
                    "file_name": doc.file_name,
                    "document_type": doc.document_type,
                    "data": ext.extracted_data,
                })

        discrepancies: list[DiscrepancyItem] = []

        # ----------------------------------------------------
        # 1. 5-Way Name Cross-Checking (Bidder ↕ GST ↕ Udyam ↕ PAN ↕ MCA)
        # ----------------------------------------------------
        names: list[tuple[str, str]] = []  # (Name, SourceDescription)

        if bidder and isinstance(getattr(bidder, "company_name", None), str):
            names.append((bidder.company_name, "Bidder Profile"))

        for ext in extractions:
            d = get_extracted_fields(ext["data"])
            fname = ext["file_name"]
            lname = (
                d.get("legal_name")
                or d.get("enterprise_name")
                or d.get("name")
                or d.get("company_name")
                or d.get("taxpayer_name")
                or d.get("employer_name")
                or d.get("entity_name")
                or d.get("authorized_bidder_name")
                or d.get("bidder_name")
            )
            if lname and isinstance(lname, str):
                names.append((lname, f"Document '{fname}'"))

        for v in verifications:
            data = v.verified_data or {}
            lname = (
                data.get("legal_name")
                or data.get("enterprise_name")
                or data.get("name")
                or data.get("company_name")
                or data.get("employer_name")
            )
            if lname and isinstance(lname, str):
                provider_label = get_v_provider(v) or "Portal"
                names.append((lname, f"Portal Verification ({provider_label})"))

        if len(names) >= 2:
            seen_pairs = set()
            for i in range(len(names)):
                name_a, src_a = names[i]
                norm_a = normalize_name(name_a)
                for j in range(i + 1, len(names)):
                    name_b, src_b = names[j]
                    norm_b = normalize_name(name_b)
                    if norm_a and norm_b and norm_a != norm_b:
                        pair_key = tuple(sorted([src_a, src_b]))
                        if pair_key not in seen_pairs:
                            seen_pairs.add(pair_key)
                            discrepancies.append(
                                DiscrepancyItem(
                                    discrepancy_type="LEGAL_NAME_MISMATCH",
                                    severity="HIGH",
                                    field="company_name",
                                    source_a=f"{src_a}: '{name_a}'",
                                    source_b=f"{src_b}: '{name_b}'",
                                    message=f"Company name mismatch identified between {src_a} and {src_b}.",
                                )
                            )

        # ----------------------------------------------------
        # 2. Document Identifiers Cross-Checking (GSTIN, PAN, Udyam)
        # ----------------------------------------------------
        # GSTIN sources
        gstin_entries: list[tuple[str, str]] = []
        if bidder and isinstance(getattr(bidder, "gstin", None), str):
            gstin_entries.append((bidder.gstin.strip().upper(), "Bidder Profile"))

        for ext in extractions:
            d = get_extracted_fields(ext["data"])
            g = d.get("gstin")
            if g and isinstance(g, str):
                gstin_entries.append((g.strip().upper(), f"Document '{ext['file_name']}'"))

        for v in verifications:
            p_name = get_v_provider(v)
            if p_name in ("GST", "GST_REGISTRATION") and getattr(v, "identifier", None) and isinstance(v.identifier, str):
                gstin_entries.append((v.identifier.strip().upper(), "GST Portal Verification"))

        if len(gstin_entries) >= 2:
            base_g, base_src = gstin_entries[0]
            for other_g, other_src in gstin_entries[1:]:
                if base_g != other_g:
                    discrepancies.append(
                        DiscrepancyItem(
                            discrepancy_type="GSTIN_MISMATCH",
                            severity="HIGH",
                            field="gstin",
                            source_a=f"{base_src}: '{base_g}'",
                            source_b=f"{other_src}: '{other_g}'",
                            message=f"GSTIN mismatch identified between {base_src} and {other_src}.",
                        )
                    )

        # PAN sources
        pan_entries: list[tuple[str, str]] = []
        if bidder and isinstance(getattr(bidder, "pan", None), str):
            pan_entries.append((bidder.pan.strip().upper(), "Bidder Profile"))

        for ext in extractions:
            d = get_extracted_fields(ext["data"])
            p = d.get("pan_number") or d.get("pan")
            if p and isinstance(p, str):
                pan_entries.append((p.strip().upper(), f"Document '{ext['file_name']}'"))

        for v in verifications:
            p_name = get_v_provider(v)
            if p_name in ("PAN", "PAN_VERIFICATION") and getattr(v, "identifier", None) and isinstance(v.identifier, str):
                pan_entries.append((v.identifier.strip().upper(), "PAN Portal Verification"))

        if len(pan_entries) >= 2:
            base_p, base_src = pan_entries[0]
            for other_p, other_src in pan_entries[1:]:
                if base_p != other_p:
                    discrepancies.append(
                        DiscrepancyItem(
                            discrepancy_type="PAN_MISMATCH",
                            severity="HIGH",
                            field="pan",
                            source_a=f"{base_src}: '{base_p}'",
                            source_b=f"{other_src}: '{other_p}'",
                            message=f"PAN mismatch identified between {base_src} and {other_src}.",
                        )
                    )

        # Embedded PAN in GSTIN check (digits 3..12 of GSTIN)
        for g_val, g_src in gstin_entries:
            if GSTIN_PATTERN.fullmatch(g_val):
                embedded_pan = g_val[2:12]
                for p_val, p_src in pan_entries:
                    if PAN_PATTERN.fullmatch(p_val) and embedded_pan != p_val:
                        discrepancies.append(
                            DiscrepancyItem(
                                discrepancy_type="PAN_GSTIN_EMBEDDED_MISMATCH",
                                severity="HIGH",
                                field="pan",
                                source_a=f"GSTIN ({g_src}): '{g_val}' (embedded PAN: {embedded_pan})",
                                source_b=f"PAN ({p_src}): '{p_val}'",
                                message=f"Embedded PAN from GSTIN ({embedded_pan}) does not match declared PAN ({p_val}).",
                            )
                        )

        # Udyam sources
        udyam_entries: list[tuple[str, str]] = []
        if bidder and isinstance(getattr(bidder, "udyam_number", None), str):
            udyam_entries.append((bidder.udyam_number.strip().upper(), "Bidder Profile"))

        for ext in extractions:
            d = get_extracted_fields(ext["data"])
            u = d.get("udyam_number")
            if u and isinstance(u, str):
                udyam_entries.append((u.strip().upper(), f"Document '{ext['file_name']}'"))

        for v in verifications:
            p_name = get_v_provider(v)
            if p_name in ("UDYAM", "UDYAM_VERIFICATION") and getattr(v, "identifier", None) and isinstance(v.identifier, str):
                udyam_entries.append((v.identifier.strip().upper(), "Udyam Portal Verification"))

        if len(udyam_entries) >= 2:
            base_u, base_src = udyam_entries[0]
            for other_u, other_src in udyam_entries[1:]:
                if base_u != other_u:
                    discrepancies.append(
                        DiscrepancyItem(
                            discrepancy_type="UDYAM_MISMATCH",
                            severity="HIGH",
                            field="udyam_number",
                            source_a=f"{base_src}: '{base_u}'",
                            source_b=f"{other_src}: '{other_u}'",
                            message=f"Udyam registration number mismatch identified between {base_src} and {other_src}.",
                        )
                    )

        # ----------------------------------------------------
        # 3. Registration Status Cross-Checking
        # ----------------------------------------------------
        for v in verifications:
            provider = get_v_provider(v)
            data = v.verified_data or {}
            v_status = getattr(v, "status", None) or getattr(v, "verification_status", None) or ""
            if hasattr(v_status, "value"):
                v_status = v_status.value

            # GST status
            if provider in ("GST", "GST_REGISTRATION"):
                reg_status = (data.get("registration_status") or data.get("status") or "").upper()
                if reg_status in ("INACTIVE", "CANCELLED", "SUSPENDED", "INVALID"):
                    discrepancies.append(
                        DiscrepancyItem(
                            discrepancy_type="INACTIVE_REGISTRATION",
                            severity="HIGH",
                            field="gst_status",
                            source_a=f"GST Verification ({v.identifier})",
                            source_b="Portal Record",
                            message=f"GST registration is non-active ({reg_status}).",
                        )
                    )

            # Udyam status
            elif provider in ("UDYAM", "UDYAM_VERIFICATION"):
                ent_status = (data.get("enterprise_status") or data.get("status") or "").upper()
                if ent_status in ("INACTIVE", "DEREGISTERED", "INVALID"):
                    discrepancies.append(
                        DiscrepancyItem(
                            discrepancy_type="INACTIVE_REGISTRATION",
                            severity="HIGH",
                            field="udyam_status",
                            source_a=f"Udyam Verification ({v.identifier})",
                            source_b="Portal Record",
                            message=f"Udyam MSME registration is non-active ({ent_status}).",
                        )
                    )

            # MCA21 status
            elif provider in ("MCA21", "MCA21_CORPORATE_CHECK"):
                comp_status = (data.get("company_status") or "").upper()
                if comp_status in ("STRUCK_OFF", "DISSOLVED", "DORMANT", "INACTIVE"):
                    discrepancies.append(
                        DiscrepancyItem(
                            discrepancy_type="INACTIVE_REGISTRATION",
                            severity="HIGH",
                            field="mca_status",
                            source_a=f"MCA21 Verification ({v.identifier})",
                            source_b="Portal Record",
                            message=f"Company status is non-active ({comp_status}) in MCA21 registry.",
                        )
                    )

            # Debarment status
            elif provider in ("DEBARMENT", "BLACKLISTING", "DEBARMENT_VERIFICATION"):
                is_debarred = data.get("is_debarred", False)
                d_status = (data.get("debarment_status") or "").upper()
                if is_debarred or d_status in ("DEBARRED", "BLACK_LISTED"):
                    agency = data.get("debarring_agency") or "Central Authority"
                    discrepancies.append(
                        DiscrepancyItem(
                            discrepancy_type="DEBARRED_VENDOR",
                            severity="HIGH",
                            field="debarment",
                            source_a=f"Debarment Database Check ({v.identifier})",
                            source_b=f"Flagged by {agency}",
                            message=f"Vendor is flagged as DEBARRED/BLACKLISTED by {agency}.",
                        )
                    )

        # ----------------------------------------------------
        # 4. Dates & Validity Cross-Checking
        # ----------------------------------------------------
        now_dt = datetime.now(timezone.utc)
        for ext in extractions:
            d = get_extracted_fields(ext["data"])
            fname = ext["file_name"]

            # Expiration / Validity check
            is_expired = d.get("is_expired")
            if is_expired is True:
                discrepancies.append(
                    DiscrepancyItem(
                        discrepancy_type="EXPIRED_DOCUMENT",
                        severity="HIGH",
                        field="validity",
                        source_a=f"Document '{fname}'",
                        source_b="Document Intelligence",
                        message=f"Document '{fname}' is explicitly flagged as expired.",
                    )
                )

            valid_until_str = d.get("valid_until") or d.get("expiry_date") or d.get("validity_date") or d.get("validity_period")
            if valid_until_str and isinstance(valid_until_str, str):
                try:
                    # ISO or YYYY-MM-DD parsing
                    valid_dt = datetime.fromisoformat(valid_until_str.replace("Z", "+00:00"))
                    if valid_dt.tzinfo is None:
                        valid_dt = valid_dt.replace(tzinfo=timezone.utc)
                    if valid_dt < now_dt:
                        discrepancies.append(
                            DiscrepancyItem(
                                discrepancy_type="EXPIRED_DOCUMENT",
                                severity="HIGH",
                                field="valid_until",
                                source_a=f"Document '{fname}': {valid_until_str}",
                                source_b=f"Current Date: {now_dt.strftime('%Y-%m-%d')}",
                                message=f"Validity period for document '{fname}' expired on {valid_until_str}.",
                            )
                        )
                except (ValueError, TypeError):
                    pass

        # ----------------------------------------------------
        # 5. Missing Information Identification
        # ----------------------------------------------------
        # Check if documents were uploaded but portal verification was missing
        uploaded_doc_types = {ext["document_type"] for ext in extractions if ext.get("document_type")}
        verified_providers = {get_v_provider(v) for v in verifications}


        doc_provider_map = {
            "GST_CERTIFICATE": "GST",
            "GST_RETURN": "GST",
            "PAN": "PAN",
            "UDYAM_CERTIFICATE": "UDYAM",
            "MCA21": "MCA21",
            "EPFO": "EPFO",
            "ESIC": "ESIC",
            "STARTUP_INDIA": "STARTUP_INDIA",
            "NSIC": "NSIC",
        }

        for doc_type, provider_name in doc_provider_map.items():
            if doc_type in uploaded_doc_types and provider_name not in verified_providers:
                discrepancies.append(
                    DiscrepancyItem(
                        discrepancy_type="MISSING_PORTAL_VERIFICATION",
                        severity="MEDIUM",
                        field="verification",
                        source_a=f"Uploaded Document ({doc_type})",
                        source_b=f"{provider_name} Verification Portal",
                        message=f"Document of type {doc_type} was uploaded, but corresponding portal verification ({provider_name}) was not performed.",
                    )
                )

        # ----------------------------------------------------
        # 6. Persist Discrepancy findings to Database
        # ----------------------------------------------------
        from app.services.discrepancy_service import discrepancy_service

        for d in discrepancies:
            try:
                finding_key = f"cross_ver:{bid_submission_id}:{d.discrepancy_type}:{d.field}"
                discrepancy_service.record_discrepancy(
                    db=db,
                    bid_submission_id=bid_submission_id,
                    type=d.discrepancy_type,
                    title=f"{d.discrepancy_type.replace('_', ' ').title()}: {d.field}",
                    description=d.message,
                    severity=d.severity,
                    source="CROSS_VERIFICATION",
                    expected_value=d.source_a,
                    observed_value=d.source_b,
                    evidence={
                        "field": d.field,
                        "source_a": d.source_a,
                        "source_b": d.source_b,
                        "message": d.message,
                    },
                    finding_key=finding_key,
                )
            except Exception as exc:
                pass

        from app.core.audit_actions import AuditAction, AuditEntityType
        from app.services.audit_log_service import audit_log_service

        audit_log_service.record_event(
            db=db,
            action=AuditAction.CROSS_VERIFICATION_COMPLETED,
            entity_type=AuditEntityType.BID_SUBMISSION,
            entity_id=bid_submission_id,
            bid_submission_id=bid_submission_id,
            new_value={
                "has_discrepancies": len(discrepancies) > 0,
                "discrepancies_count": len(discrepancies),
            },
            details=f"Cross-verification completed for submission #{bid_submission_id} with {len(discrepancies)} findings",
        )

        return CrossVerificationResult(
            bid_submission_id=bid_submission_id,
            has_discrepancies=len(discrepancies) > 0,
            discrepancies_count=len(discrepancies),
            discrepancies=discrepancies,
        )



cross_verification_service = CrossVerificationService()

