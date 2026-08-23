"""Secure PDF document upload handler and ingestion pipeline for Stage 2 Knowledge Administration."""

import hashlib
import re
import uuid
from datetime import datetime
from pathlib import Path
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.db.models import Account, AuditLog, DocChunk, Document
from app.ingestion.chunker import chunk_text
from app.ingestion.contract_rules import extract_contract_rules_for_document
from app.ingestion.embedder import embed_texts

STORAGE_DIR = Path(__file__).resolve().parents[2] / "storage" / "documents"
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit


def _sanitize_filename(name: str) -> str:
    cleaned = Path(name).name
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]", "_", cleaned)
    return cleaned or "document.pdf"


def log_audit_event(
    db: Session,
    actor_user_id: str,
    actor_role: str,
    action_type: str,
    target_account_id: str | None,
    doc_id: str,
    result: str,
    payload: dict | None = None,
):
    meta = payload or {}
    meta["doc_id"] = doc_id
    audit = AuditLog(
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        action_type=action_type,
        target_account_id=target_account_id,
        payload=meta,
        result=result,
        created_at=datetime.utcnow(),
    )
    db.add(audit)
    db.flush()


def process_uploaded_document(
    db: Session,
    file_bytes: bytes,
    original_filename: str,
    metadata: dict,
    actor_user_id: str,
    actor_role: str,
) -> Document:
    """Validate, store, extract, chunk, embed, and transition uploaded PDF document."""
    # 1. Validation checks
    if len(file_bytes) == 0:
        raise ValueError("Uploaded file is empty (0 bytes).")

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise ValueError("File size exceeds 10MB limit.")

    if not original_filename.lower().endswith(".pdf"):
        raise ValueError("Only PDF documents (.pdf) are permitted.")

    if not file_bytes.startswith(b"%PDF-"):
        raise ValueError("File content is not a valid PDF document header.")

    sanitized_name = _sanitize_filename(original_filename)

    # 2. Checksum validation
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
    existing_active = (
        db.query(Document)
        .filter(
            Document.checksum_sha256 == sha256_hash,
            Document.status.in_(["ACTIVE", "CURRENT"]),
        )
        .first()
    )
    if existing_active:
        raise ValueError(
            f"An active document with identical content (SHA-256: {sha256_hash[:8]}...) already exists ({existing_active.doc_id})."
        )

    # 3. Validate metadata constraints
    doc_type = metadata.get("doc_type", "support_policy")
    allowed_types = {"support_policy", "sop", "product_ops", "agreement", "internal_note"}
    if doc_type not in allowed_types:
        raise ValueError(f"Invalid document_type: {doc_type}. Must be one of {allowed_types}")

    visibility = metadata.get("visibility", "internal_only")
    if visibility not in {"customer_visible", "internal_only"}:
        raise ValueError("Visibility must be either 'customer_visible' or 'internal_only'")

    if visibility == "customer_visible" and doc_type == "internal_note":
        raise ValueError("Internal notes cannot be made customer_visible.")

    account_id = metadata.get("account_id")
    if doc_type == "agreement":
        if not account_id:
            raise ValueError("Agreement documents require a valid account_id.")
        acc = db.query(Account).filter(Account.account_id == account_id).first()
        if not acc:
            raise ValueError(f"Account '{account_id}' does not exist.")
    else:
        if account_id:
            raise ValueError(f"Global document type '{doc_type}' must not specify an account_id.")

    effective_date = metadata.get("effective_date")
    expires_at = metadata.get("expires_at")
    if effective_date and expires_at and expires_at < effective_date:
        raise ValueError("expires_at cannot be prior to effective_date.")

    # 4. Generate storage path and doc_id
    doc_uuid = uuid.uuid4().hex
    doc_id = f"DOC-USER-{doc_uuid[:8].upper()}"
    storage_filename = f"doc_{doc_uuid}.pdf"

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    full_storage_path = STORAGE_DIR / storage_filename

    # 5. Create Document record in PROCESSING state
    doc = Document(
        doc_id=doc_id,
        filename=sanitized_name,
        original_filename=original_filename,
        storage_path=str(full_storage_path),
        title=metadata.get("title") or sanitized_name,
        doc_type=doc_type,
        status="PROCESSING",
        visibility=visibility,
        effective_date=effective_date or datetime.utcnow(),
        expires_at=expires_at,
        account_id=account_id,
        authority_rank=metadata.get("authority_rank"),
        checksum_sha256=sha256_hash,
        uploaded_by=actor_user_id,
        uploaded_at=datetime.utcnow(),
        is_user_uploaded=True,
        source_origin="user_upload",
        raw_text="",
    )
    db.add(doc)
    db.flush()

    log_audit_event(
        db,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        action_type="document_uploaded",
        target_account_id=account_id,
        doc_id=doc_id,
        result="PROCESSING",
        payload={"filename": sanitized_name, "doc_type": doc_type},
    )

    try:
        # Save file to local storage
        with open(full_storage_path, "wb") as f:
            f.write(file_bytes)

        log_audit_event(
            db,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            action_type="document_ingestion_started",
            target_account_id=account_id,
            doc_id=doc_id,
            result="IN_PROGRESS",
        )

        # Extract text using PyPDF
        reader = PdfReader(str(full_storage_path))
        pages = [page.extract_text() or "" for page in reader.pages]

        if not pages or sum(len(p.strip()) for p in pages) == 0:
            raise ValueError("PDF document contains no readable text pages or is empty.")

        doc.raw_text = "\n".join(pages)

        # Chunk text & generate embeddings
        chunk_count = 0
        for page_num, page_text in enumerate(pages, start=1):
            cleaned = re.sub(r"\s+", " ", page_text).strip()
            if not cleaned:
                continue

            chunks = chunk_text(cleaned, max_tokens=180, overlap_tokens=30)
            embeddings = embed_texts(chunks)

            for chunk, embedding in zip(chunks, embeddings):
                db.add(
                    DocChunk(
                        doc_id=doc_id,
                        page=page_num,
                        text=chunk,
                        embedding=embedding,
                    )
                )
                chunk_count += 1

        # Extract contract rules if agreement
        if doc_type == "agreement":
            extract_contract_rules_for_document(db, doc)

        # Success -> transition to PENDING_REVIEW
        doc.status = "PENDING_REVIEW"
        doc.ingestion_error = None

        log_audit_event(
            db,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            action_type="document_ingestion_succeeded",
            target_account_id=account_id,
            doc_id=doc_id,
            result="PENDING_REVIEW",
            payload={"page_count": len(pages), "chunk_count": chunk_count},
        )

        db.commit()
        db.refresh(doc)
        return doc

    except Exception as e:
        db.rollback()
        # Mark document as FAILED
        failed_doc = db.query(Document).filter(Document.doc_id == doc_id).first()
        if failed_doc:
            failed_doc.status = "FAILED"
            failed_doc.ingestion_error = str(e)
            log_audit_event(
                db,
                actor_user_id=actor_user_id,
                actor_role=actor_role,
                action_type="document_ingestion_failed",
                target_account_id=account_id,
                doc_id=doc_id,
                result="FAILED",
                payload={"error": str(e)},
            )
            db.commit()
            db.refresh(failed_doc)
            return failed_doc
        raise
