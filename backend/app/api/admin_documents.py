"""FastAPI Admin Router for Stage 2 Knowledge Administration & Document Governance."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_session, require_role
from app.auth.mock_auth import Session as UserSession
from app.db.models import Account, AuditLog, ContractRule, DocChunk, Document
from app.db.session import get_db
from app.ingestion.contract_rules import extract_contract_rules_for_document
from app.ingestion.doc_processor import log_audit_event, process_uploaded_document

router = APIRouter(prefix="/admin", tags=["knowledge_admin"])


class DocumentReviewRequest(BaseModel):
    action: str = Field(..., description="Action: activate | reject | deprecate | supersede | reprocess")
    reason: Optional[str] = None
    supersedes_doc_id: Optional[str] = None
    confirmed: bool = True


def _parse_iso_date(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format '{dt_str}'. Use ISO format (YYYY-MM-DDTHH:MM:SS)",
        )


def _serialize_document(doc: Document, db: Session) -> dict:
    chunk_count = db.query(DocChunk).filter(DocChunk.doc_id == doc.doc_id).count()
    rule_count = db.query(ContractRule).filter(ContractRule.doc_id == doc.doc_id).count()

    return {
        "doc_id": doc.doc_id,
        "filename": doc.filename,
        "original_filename": doc.original_filename or doc.filename,
        "title": doc.title or doc.filename,
        "doc_type": doc.doc_type,
        "status": doc.status,
        "visibility": doc.visibility,
        "effective_date": str(doc.effective_date) if doc.effective_date else None,
        "expires_at": str(doc.expires_at) if doc.expires_at else None,
        "account_id": doc.account_id,
        "authority_rank": doc.authority_rank,
        "supersedes_doc_id": doc.supersedes_doc_id,
        "superseded_by_doc_id": doc.superseded_by_doc_id,
        "checksum_sha256": doc.checksum_sha256,
        "uploaded_by": doc.uploaded_by,
        "uploaded_at": str(doc.uploaded_at) if doc.uploaded_at else None,
        "reviewed_by": doc.reviewed_by,
        "reviewed_at": str(doc.reviewed_at) if doc.reviewed_at else None,
        "activated_by": doc.activated_by,
        "activated_at": str(doc.activated_at) if doc.activated_at else None,
        "ingestion_error": doc.ingestion_error,
        "is_user_uploaded": doc.is_user_uploaded,
        "source_origin": doc.source_origin,
        "chunk_count": chunk_count,
        "rule_count": rule_count,
    }


@router.get("/documents")
def list_documents(
    doc_status: Optional[str] = None,
    doc_type: Optional[str] = None,
    account_id: Optional[str] = None,
    visibility: Optional[str] = None,
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_session),
):
    require_role(session, ["manager"])

    query = db.query(Document)
    if doc_status:
        query = query.filter(Document.status == doc_status)
    if doc_type:
        query = query.filter(Document.doc_type == doc_type)
    if account_id:
        query = query.filter(Document.account_id == account_id)
    if visibility:
        query = query.filter(Document.visibility == visibility)

    docs = query.order_by(Document.doc_id.desc()).all()
    return {"documents": [_serialize_document(d, db) for d in docs]}


@router.post("/documents/upload")
def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    doc_type: str = Form(...),
    visibility: str = Form("internal_only"),
    account_id: Optional[str] = Form(None),
    effective_date: Optional[str] = Form(None),
    expires_at: Optional[str] = Form(None),
    authority_rank: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_session),
):
    require_role(session, ["manager"])

    parsed_effective = _parse_iso_date(effective_date)
    parsed_expires = _parse_iso_date(expires_at)

    metadata = {
        "title": title,
        "doc_type": doc_type,
        "visibility": visibility,
        "account_id": account_id if account_id and account_id.strip() else None,
        "effective_date": parsed_effective,
        "expires_at": parsed_expires,
        "authority_rank": authority_rank,
    }

    try:
        file_bytes = file.file.read()
        doc = process_uploaded_document(
            db=db,
            file_bytes=file_bytes,
            original_filename=file.filename or "document.pdf",
            metadata=metadata,
            actor_user_id=session.user_id,
            actor_role=session.role,
        )
        return {
            "status": "OK",
            "message": "Document uploaded successfully and queued in PENDING_REVIEW.",
            "document": _serialize_document(doc, db),
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion process error: {str(e)}",
        )


@router.get("/documents/{doc_id}")
def get_document_details(
    doc_id: str,
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_session),
):
    require_role(session, ["manager"])

    doc = db.query(Document).filter(Document.doc_id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{doc_id}' not found."
        )

    return {"document": _serialize_document(doc, db)}


@router.get("/documents/{doc_id}/preview")
def get_document_preview(
    doc_id: str,
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_session),
):
    require_role(session, ["manager"])

    doc = db.query(Document).filter(Document.doc_id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{doc_id}' not found."
        )

    chunks = db.query(DocChunk).filter(DocChunk.doc_id == doc_id).order_by(DocChunk.chunk_id.asc()).all()
    rules = db.query(ContractRule).filter(ContractRule.doc_id == doc_id).all()

    page_numbers = sorted({c.page for c in chunks if c.page})

    preview_text = (doc.raw_text or "")[:2000]
    if len(doc.raw_text or "") > 2000:
        preview_text += "\n\n[... preview truncated ...]"

    return {
        "doc_id": doc.doc_id,
        "title": doc.title or doc.filename,
        "filename": doc.filename,
        "doc_type": doc.doc_type,
        "status": doc.status,
        "page_count": len(page_numbers) if page_numbers else 1,
        "chunk_count": len(chunks),
        "preview_text": preview_text,
        "chunks_snippet": [
            {"page": c.page, "text": c.text[:200]} for c in chunks[:5]
        ],
        "extracted_contract_rules": [
            {
                "rule_key": r.rule_key,
                "clause_type": r.clause_type,
                "value_number": r.value_number,
                "value_boolean": r.value_boolean,
                "value_text": r.value_text,
                "source_text": r.source_text,
            }
            for r in rules
        ],
    }


@router.post("/documents/{doc_id}/review")
def review_document(
    doc_id: str,
    req: DocumentReviewRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_session),
):
    require_role(session, ["manager"])

    if not req.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State transition requires explicit confirmation payload (confirmed=True).",
        )

    doc = db.query(Document).filter(Document.doc_id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{doc_id}' not found."
        )

    allowed_actions = {"activate", "reject", "deprecate", "supersede", "reprocess"}
    if req.action not in allowed_actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action '{req.action}'. Allowed: {allowed_actions}",
        )

    now = datetime.utcnow()

    if req.action == "activate":
        if doc.status in {"REJECTED", "FAILED"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot directly activate document in '{doc.status}' state. Reprocess or upload a new version.",
            )

        doc.status = "ACTIVE"
        doc.activated_by = session.user_id
        doc.activated_at = now
        doc.reviewed_by = session.user_id
        doc.reviewed_at = now

        # Handle supersedes relationship if specified
        target_supersede_id = req.supersedes_doc_id or doc.supersedes_doc_id
        if target_supersede_id:
            target_doc = db.query(Document).filter(Document.doc_id == target_supersede_id).first()
            if target_doc:
                doc.supersedes_doc_id = target_doc.doc_id
                target_doc.status = "SUPERSEDED"
                target_doc.superseded_by_doc_id = doc.doc_id
                log_audit_event(
                    db,
                    actor_user_id=session.user_id,
                    actor_role=session.role,
                    action_type="document_superseded",
                    target_account_id=target_doc.account_id,
                    doc_id=target_doc.doc_id,
                    result="SUPERSEDED",
                    payload={"superseded_by": doc.doc_id, "reason": req.reason},
                )

        # Refresh contract rules if agreement
        if doc.doc_type == "agreement":
            extract_contract_rules_for_document(db, doc)

        log_audit_event(
            db,
            actor_user_id=session.user_id,
            actor_role=session.role,
            action_type="document_activated",
            target_account_id=doc.account_id,
            doc_id=doc.doc_id,
            result="ACTIVE",
            payload={"reason": req.reason},
        )

    elif req.action == "reject":
        if doc.status == "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reject an ACTIVE document. Use deprecate instead.",
            )
        doc.status = "REJECTED"
        doc.reviewed_by = session.user_id
        doc.reviewed_at = now
        log_audit_event(
            db,
            actor_user_id=session.user_id,
            actor_role=session.role,
            action_type="document_rejected",
            target_account_id=doc.account_id,
            doc_id=doc.doc_id,
            result="REJECTED",
            payload={"reason": req.reason},
        )

    elif req.action == "deprecate":
        if doc.status not in {"ACTIVE", "CURRENT"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only active/current documents can be deprecated (current status: '{doc.status}').",
            )
        doc.status = "DEPRECATED"
        doc.reviewed_by = session.user_id
        doc.reviewed_at = now
        log_audit_event(
            db,
            actor_user_id=session.user_id,
            actor_role=session.role,
            action_type="document_deprecated",
            target_account_id=doc.account_id,
            doc_id=doc.doc_id,
            result="DEPRECATED",
            payload={"reason": req.reason},
        )

    elif req.action == "supersede":
        target_id = req.supersedes_doc_id
        if not target_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action 'supersede' requires 'supersedes_doc_id' target.",
            )
        target_doc = db.query(Document).filter(Document.doc_id == target_id).first()
        if not target_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target document '{target_id}' to supersede not found.",
            )
        target_doc.status = "SUPERSEDED"
        target_doc.superseded_by_doc_id = doc.doc_id
        doc.supersedes_doc_id = target_doc.doc_id
        log_audit_event(
            db,
            actor_user_id=session.user_id,
            actor_role=session.role,
            action_type="document_superseded",
            target_account_id=target_doc.account_id,
            doc_id=target_doc.doc_id,
            result="SUPERSEDED",
            payload={"superseded_by": doc.doc_id, "reason": req.reason},
        )

    elif req.action == "reprocess":
        log_audit_event(
            db,
            actor_user_id=session.user_id,
            actor_role=session.role,
            action_type="document_reprocessed",
            target_account_id=doc.account_id,
            doc_id=doc.doc_id,
            result="REPROCESSED",
            payload={"reason": req.reason},
        )
        if doc.storage_path and Path(doc.storage_path).exists():
            with open(doc.storage_path, "rb") as f:
                file_bytes = f.read()
            metadata = {
                "title": doc.title,
                "doc_type": doc.doc_type,
                "visibility": doc.visibility,
                "account_id": doc.account_id,
                "effective_date": doc.effective_date,
                "expires_at": doc.expires_at,
            }
            doc = process_uploaded_document(
                db=db,
                file_bytes=file_bytes,
                original_filename=doc.original_filename or doc.filename,
                metadata=metadata,
                actor_user_id=session.user_id,
                actor_role=session.role,
            )

    db.commit()
    db.refresh(doc)

    return {
        "status": "OK",
        "message": f"Document '{doc_id}' state updated to '{doc.status}' via action '{req.action}'.",
        "document": _serialize_document(doc, db),
    }


@router.get("/audit-log")
def get_audit_logs(
    doc_id: Optional[str] = None,
    action_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_session),
):
    require_role(session, ["manager"])

    query = db.query(AuditLog)
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)

    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()

    results = []
    for l in logs:
        # Filter by doc_id inside payload if requested
        if doc_id and l.payload and l.payload.get("doc_id") != doc_id:
            continue
        results.append(
            {
                "log_id": l.log_id,
                "actor_user_id": l.actor_user_id,
                "actor_role": l.actor_role,
                "action_type": l.action_type,
                "target_account_id": l.target_account_id,
                "payload": l.payload,
                "result": l.result,
                "created_at": str(l.created_at),
            }
        )

    return {"audit_logs": results}
