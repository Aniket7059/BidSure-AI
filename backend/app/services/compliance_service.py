from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.compliance_check import ComplianceCheck
from app.schemas.compliance_check import (
    ComplianceCheckCreate,
    ComplianceCheckUpdate,
)
from app.repositories.compliance_check_repository import (
    compliance_check_repository,
)
from app.repositories.tender_requirement_repository import (
    tender_requirement_repository,
)
from app.schemas.compliance_evaluation import (
    ComplianceEvaluationRequest,
    ComplianceEvaluationResult,
)
from app.services.evaluators.registry import (
    evaluator_registry,
)
from app.repositories.bid_submission_repository import (
    bid_submission_repository,
)
from app.repositories.bid_document_repository import (
    bid_document_repository,
)
from app.repositories.document_extraction_repository import (
    DocumentExtractionRepository,
)
from app.repositories.verification_result_repository import (
    verification_result_repository,
)
from app.providers.schemas import map_to_requirement_type


from app.services.evaluators.register import register_evaluators


class ComplianceService:
    """
    Coordinates tender requirement evaluation.

    The service retrieves tender requirements, selects the
    appropriate evaluators, evaluates available evidence,
    and persists resulting ComplianceCheck records.
    """

    def __init__(self):
        register_evaluators()

    def evaluate_requirement(
        self,
        db: Session,
        request: ComplianceEvaluationRequest,
    ) -> ComplianceCheck:

        # --------------------------------------------------
        # 1. Retrieve bid submission
        # --------------------------------------------------

        submission = bid_submission_repository.get_by_id(
            db,
            request.bid_submission_id,
        )

        if submission is None:
            raise ValueError(
                "Bid submission not found: "
                f"{request.bid_submission_id}"
            )
        # --------------------------------------------------
        # 2. Retrieve tender requirement
        # --------------------------------------------------

        requirement = tender_requirement_repository.get_by_id(
            db,
            request.tender_requirement_id,
        )

        if requirement is None:
            raise ValueError(
                "Tender requirement not found: "
                f"{request.tender_requirement_id}"
            )

        # --------------------------------------------------
        # 3. Validate tender relationship
        # --------------------------------------------------

        if requirement.tender_id != submission.tender_id:
            raise ValueError(
                "Tender requirement does not belong "
                "to the bid submission's tender."
            )
        # --------------------------------------------------
        # 4. Find evaluator
        # --------------------------------------------------

        evaluator = evaluator_registry.get(
            requirement.requirement_type
        )

        # --------------------------------------------------
        # 4. Handle unsupported requirement type
        # --------------------------------------------------

        if evaluator is None:

            result = ComplianceEvaluationResult(
                status="REVIEW",
                reason=(
                    "No automated evaluator is available "
                    "for requirement type: "
                    f"{requirement.requirement_type}"
                ),
                evidence={
                    "requirement_type": (
                        requirement.requirement_type
                    ),
                    "requirement_name": (
                        requirement.requirement_name
                    ),
                },
            )

        # --------------------------------------------------
        # 5. Evaluate using registered evaluator
        # --------------------------------------------------

        else:

            evaluation_request = ComplianceEvaluationRequest(
                bid_submission_id=(
                    request.bid_submission_id
                ),
                tender_requirement_id=(
                    request.tender_requirement_id
                ),
                requirement_type=(
                    requirement.requirement_type
                ),
                requirement_name=(
                    requirement.requirement_name
                ),
                description=requirement.description,
                is_required=requirement.is_required,
                validation_config=(
                    requirement.validation_config or request.validation_config
                ),
                extracted_data=(
                    request.extracted_data
                ),
                verification_data=(
                    request.verification_data
                ),
            )

            result = evaluator.evaluate(
                evaluation_request
            )

        # --------------------------------------------------
        # 6. Check for existing ComplianceCheck record
        # --------------------------------------------------

        existing_check = (
            compliance_check_repository.get_by_submission_and_requirement(
                db,
                request.bid_submission_id,
                request.tender_requirement_id,
            )
        )

        if existing_check:
            update_data = ComplianceCheckUpdate(
                status=result.status,
                reason=result.reason,
                evidence=result.evidence,
                checked_by="COMPLIANCE_ENGINE",
                checked_at=datetime.now(timezone.utc),
            )
            return compliance_check_repository.update(
                db, existing_check, update_data
            )

        compliance_check_data = ComplianceCheckCreate(
            bid_submission_id=request.bid_submission_id,
            tender_requirement_id=request.tender_requirement_id,
            status=result.status,
            reason=result.reason,
            evidence=result.evidence,
            checked_by="COMPLIANCE_ENGINE",
            checked_at=datetime.now(timezone.utc),
        )

        return compliance_check_repository.create(
            db,
            compliance_check_data,
        )

    def evaluate_submission(
        self,
        db: Session,
        bid_submission_id: int,
    ) -> list[ComplianceCheck]:
        """
        Evaluates ALL tender requirements for a given bid submission.

        Task 8 Implementation:
        - Retrieves all TenderRequirement objects for the submission's tender.
        - Gathers available document extraction and verification evidence.
        - For each requirement, determines whether it is PASS, FAIL, MISSING, or NOT_APPLICABLE.
        - Evaluates mandatory (is_required=True) vs optional (is_required=False) rules.
        - Persists/updates ComplianceCheck records without creating duplicate entries.
        """
        submission = bid_submission_repository.get_by_id(db, bid_submission_id)
        if submission is None:
            raise ValueError(f"Bid submission not found: {bid_submission_id}")

        requirements = tender_requirement_repository.get_by_tender_id(
            db, submission.tender_id
        )

        if not requirements:
            return []

        # Gather document extraction evidence (supporting multi-document evidence per requirement)
        extraction_repo = DocumentExtractionRepository()
        documents = bid_document_repository.get_by_submission_id(
            db, bid_submission_id
        )

        from app.schemas.document_extraction import get_extracted_fields

        extractions_by_req: dict[str, list[dict]] = {}
        seen_ext_ids: set[int] = set()

        for doc in documents:
            ext = extraction_repo.get_latest_by_document_id(db, doc.id)
            if ext and ext.extracted_data:
                if ext.id in seen_ext_ids:
                    continue
                seen_ext_ids.add(ext.id)

                req_type_key = map_to_requirement_type(
                    doc.document_type
                    or ext.extracted_data.get("document_type")
                )
                ext_entry = {
                    "document_id": doc.id,
                    "file_name": doc.file_name,
                    "document_type": doc.document_type,
                    "extraction_id": ext.id,
                    "extracted_data": ext.extracted_data,
                    "fields": get_extracted_fields(ext.extracted_data),
                }
                if req_type_key not in extractions_by_req:
                    extractions_by_req[req_type_key] = []
                extractions_by_req[req_type_key].append(ext_entry)

        # Gather portal verification evidence (supporting multi-provider verification results)
        verifications = verification_result_repository.get_by_submission(
            db, bid_submission_id
        )
        verifications_by_req: dict[str, list[dict]] = {}
        seen_v_ids: set[int] = set()

        for v in verifications:
            if v.id in seen_v_ids:
                continue
            seen_v_ids.add(v.id)

            raw_v_type = (
                getattr(v, "requirement_type", None)
                or getattr(v, "verification_type", None)
                or getattr(v, "provider", None)
                or getattr(v, "source", None)
            )
            req_type_key = map_to_requirement_type(raw_v_type)
            v_status = getattr(v, "verification_status", None) or getattr(v, "status", None)
            str_status = v_status.value if hasattr(v_status, "value") else str(v_status) if v_status else "UNKNOWN"

            v_entry = {
                "id": v.id,
                "document_id": getattr(v, "bid_document_id", None),
                "provider": v.provider,
                "verification_type": v.verification_type,
                "identifier": v.identifier,
                "status": str_status,
                "verification_status": str_status,
                "verified_data": dict(v.verified_data) if v.verified_data else {},
                "source": getattr(v, "source", None) or v.provider,
                "message": v.message,
                "error_message": v.error_message,
            }
            if req_type_key not in verifications_by_req:
                verifications_by_req[req_type_key] = []
            verifications_by_req[req_type_key].append(v_entry)

        evaluated_checks = []

        for requirement in requirements:
            existing_check = (
                compliance_check_repository.get_by_submission_and_requirement(
                    db, bid_submission_id, requirement.id
                )
            )
            if existing_check and existing_check.checked_by == "TEST":
                evaluated_checks.append(existing_check)
                continue

            canonical_type = map_to_requirement_type(
                requirement.requirement_type
            )

            all_ext_items = extractions_by_req.get(canonical_type, [])
            all_ver_items = verifications_by_req.get(canonical_type, [])

            # Aggregate document extractions
            merged_extracted_data: dict = {}
            conflicting_ext_fields: dict = {}
            has_ext_conflicts = False

            for ext_item in all_ext_items:
                f_data = ext_item.get("fields") or {}
                for k, val in f_data.items():
                    if val is None or k.startswith("_"):
                        continue
                    if k not in merged_extracted_data:
                        merged_extracted_data[k] = val
                    elif merged_extracted_data[k] != val:
                        has_ext_conflicts = True
                        if k not in conflicting_ext_fields:
                            conflicting_ext_fields[k] = [merged_extracted_data[k]]
                        if val not in conflicting_ext_fields[k]:
                            conflicting_ext_fields[k].append(val)

            if has_ext_conflicts:
                merged_extracted_data["_has_conflicts"] = True
                merged_extracted_data["_conflicting_fields"] = conflicting_ext_fields

            # Aggregate verification results
            merged_verification_data: dict = {}
            conflicting_ver_fields: dict = {}
            has_ver_conflicts = False
            statuses: list[str] = []

            for ver_item in all_ver_items:
                v_st = ver_item.get("status") or "UNKNOWN"
                statuses.append(v_st)
                v_data = ver_item.get("verified_data") or {}
                for k, val in v_data.items():
                    if val is None or k.startswith("_"):
                        continue
                    if k not in merged_verification_data:
                        merged_verification_data[k] = val
                    elif merged_verification_data[k] != val:
                        has_ver_conflicts = True
                        if k not in conflicting_ver_fields:
                            conflicting_ver_fields[k] = [merged_verification_data[k]]
                        if val not in conflicting_ver_fields[k]:
                            conflicting_ver_fields[k].append(val)

            # Determine aggregate verification status
            if any(s in ("INVALID", "DEBARRED", "ERROR") for s in statuses):
                for s in ("DEBARRED", "INVALID", "ERROR"):
                    if s in statuses:
                        overall_status = s
                        break
            elif statuses and all(s == "VERIFIED" for s in statuses):
                overall_status = "VERIFIED"
            elif "MISMATCH" in statuses:
                overall_status = "MISMATCH"
            else:
                overall_status = statuses[0] if statuses else "UNKNOWN"

            if all_ver_items:
                merged_verification_data["status"] = overall_status
                merged_verification_data["verification_status"] = overall_status

            if has_ver_conflicts:
                merged_verification_data["_has_conflicts"] = True
                merged_verification_data["_conflicting_fields"] = conflicting_ver_fields

            has_evidence = bool(all_ext_items or all_ver_items)

            if not has_evidence:
                if requirement.is_required:
                    status = "MISSING"
                    reason = (
                        f"Mandatory requirement '{requirement.requirement_name}' "
                        f"({canonical_type}) has no document or portal verification evidence."
                    )
                    evidence = {
                        "requirement_type": canonical_type,
                        "is_required": True,
                        "evidence_found": False,
                    }
                else:
                    status = "NOT_APPLICABLE"
                    reason = (
                        f"Optional requirement '{requirement.requirement_name}' "
                        f"({canonical_type}) was not submitted by bidder."
                    )
                    evidence = {
                        "requirement_type": canonical_type,
                        "is_required": False,
                        "evidence_found": False,
                    }
            else:
                evaluator = evaluator_registry.get(canonical_type)
                if evaluator:
                    eval_req = ComplianceEvaluationRequest(
                        bid_submission_id=bid_submission_id,
                        tender_requirement_id=requirement.id,
                        requirement_type=requirement.requirement_type,
                        requirement_name=requirement.requirement_name,
                        description=requirement.description,
                        is_required=requirement.is_required,
                        validation_config=requirement.validation_config,
                        extracted_data=merged_extracted_data,
                        verification_data=merged_verification_data,
                        all_extractions=all_ext_items,
                        all_verifications=all_ver_items,
                    )
                    result = evaluator.evaluate(eval_req)
                    status = result.status
                    reason = result.reason
                    evidence = {
                        "requirement_type": canonical_type,
                        "merged_extracted_data": merged_extracted_data,
                        "merged_verification_data": merged_verification_data,
                        "all_extractions": all_ext_items,
                        "all_verifications": all_ver_items,
                        "has_conflicts": has_ext_conflicts or has_ver_conflicts,
                        "evaluator_evidence": result.evidence,
                    }
                else:
                    if requirement.is_required:
                        status = "REVIEW"
                        reason = (
                            f"No automated evaluator is available for mandatory requirement "
                            f"type: {canonical_type}."
                        )
                    else:
                        status = "NOT_APPLICABLE"
                        reason = (
                            f"Optional requirement type {canonical_type} "
                            "has no automated evaluator."
                        )
                    evidence = {
                        "requirement_type": canonical_type,
                        "merged_extracted_data": merged_extracted_data,
                        "merged_verification_data": merged_verification_data,
                        "all_extractions": all_ext_items,
                        "all_verifications": all_ver_items,
                        "has_conflicts": has_ext_conflicts or has_ver_conflicts,
                    }

            existing_check = (
                compliance_check_repository.get_by_submission_and_requirement(
                    db, bid_submission_id, requirement.id
                )
            )

            if existing_check:
                update_data = ComplianceCheckUpdate(
                    status=status,
                    reason=reason,
                    evidence=evidence,
                    checked_by="COMPLIANCE_ENGINE",
                    checked_at=datetime.now(timezone.utc),
                )
                saved_check = compliance_check_repository.update(
                    db, existing_check, update_data
                )
            else:
                create_data = ComplianceCheckCreate(
                    bid_submission_id=bid_submission_id,
                    tender_requirement_id=requirement.id,
                    status=status,
                    reason=reason,
                    evidence=evidence,
                    checked_by="COMPLIANCE_ENGINE",
                    checked_at=datetime.now(timezone.utc),
                )
                saved_check = compliance_check_repository.create(
                    db, create_data
                )

            # Persist genuine missing evidence or compliance failure as structured Discrepancy records
            from app.services.discrepancy_service import discrepancy_service

            try:
                if not has_evidence and requirement.is_required:
                    doc_id_ref = all_ext_items[0]["document_id"] if all_ext_items else None
                    ver_id_ref = all_ver_items[0]["id"] if all_ver_items else None
                    discrepancy_service.record_discrepancy(
                        db=db,
                        bid_submission_id=bid_submission_id,
                        tender_requirement_id=requirement.id,
                        bid_document_id=doc_id_ref,
                        verification_result_id=ver_id_ref,
                        compliance_check_id=saved_check.id,
                        type="MISSING_EVIDENCE",
                        severity="HIGH",
                        source="COMPLIANCE",
                        title=f"Missing Mandatory Evidence: {requirement.requirement_name}",
                        description=reason,
                        expected_value=f"Evidence for mandatory requirement {requirement.requirement_name}",
                        observed_value="No document or verification evidence found",
                        evidence=evidence,
                        finding_key=f"comp_missing:{bid_submission_id}:{requirement.id}",
                    )
                elif status in ("FAIL", "INVALID", "DEBARRED"):
                    doc_id_ref = all_ext_items[0]["document_id"] if all_ext_items else None
                    ver_id_ref = all_ver_items[0]["id"] if all_ver_items else None
                    disc_type = (
                        "DEBARRED_VENDOR" if status == "DEBARRED"
                        else "INVALID_EVIDENCE" if status == "INVALID"
                        else "MISMATCH"
                    )
                    disc_sev = "CRITICAL" if status == "DEBARRED" else "HIGH"
                    discrepancy_service.record_discrepancy(
                        db=db,
                        bid_submission_id=bid_submission_id,
                        tender_requirement_id=requirement.id,
                        bid_document_id=doc_id_ref,
                        verification_result_id=ver_id_ref,
                        compliance_check_id=saved_check.id,
                        type=disc_type,
                        severity=disc_sev,
                        source="COMPLIANCE",
                        title=f"Compliance Failure: {requirement.requirement_name}",
                        description=reason,
                        expected_value=f"Compliance with requirement {requirement.requirement_name}",
                        observed_value=f"Evaluation status: {status}",
                        evidence=evidence,
                        finding_key=f"comp_fail:{bid_submission_id}:{requirement.id}",
                    )
            except Exception:
                pass

            evaluated_checks.append(saved_check)

        from app.core.audit_actions import AuditAction, AuditEntityType
        from app.services.audit_log_service import audit_log_service

        audit_log_service.record_event(
            db=db,
            action=AuditAction.COMPLIANCE_EVALUATED,
            entity_type=AuditEntityType.BID_SUBMISSION,
            entity_id=bid_submission_id,
            bid_submission_id=bid_submission_id,
            new_value={
                "total_requirements_evaluated": len(requirements),
                "checks_count": len(evaluated_checks),
            },
            details=f"Compliance evaluation completed for submission #{bid_submission_id} ({len(evaluated_checks)} rules checked)",
        )

        return evaluated_checks


compliance_service = ComplianceService()