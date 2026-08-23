"""Comprehensive Stage 2 Knowledge Administration & Document Governance Test Suite."""

import io
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.db.models import Document, DocChunk, AuditLog, ContractRule
from app.retrieval.hybrid_search import hybrid_search

client = TestClient(app)


import uuid

def _make_sample_pdf_bytes(text: str = "ParcelPilot Policy Document. Clause 1. Cancellation fee is waived for all booked orders.") -> bytes:
    unique_id = uuid.uuid4().hex
    full_text = f"{text} (Ref: {unique_id})"
    escaped = full_text.replace("(", "\\(").replace(")", "\\)")
    stream_content = f"BT /F1 12 Tf 50 750 Td ({escaped}) Tj ET\n"
    stream_len = len(stream_content)
    pdf = (
        "%PDF-1.4\n"
        "1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        "2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        "3 0 obj <</Type /Page /Parent 2 0 R /Resources <</Font <</F1 4 0 R>>>> /MediaBox [0 0 612 792] /Contents 5 0 R>> endobj\n"
        "4 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
        f"5 0 obj <</Length {stream_len}>> stream\n{stream_content}endstream\nendobj\n"
        "xref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000230 00000 n\n0000000302 00000 n\n"
        "trailer <</Size 6 /Root 1 0 R>>\nstartxref\n400\n%%EOF\n"
    )
    return pdf.encode("latin-1")


def test_01_customer_upload_denied():
    pdf_bytes = _make_sample_pdf_bytes()
    resp = client.post(
        "/admin/documents/upload",
        headers={"Authorization": "Bearer cust-northstar"},
        files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"doc_type": "support_policy", "visibility": "customer_visible"},
    )
    assert resp.status_code == 403


def test_02_support_agent_upload_denied():
    pdf_bytes = _make_sample_pdf_bytes()
    resp = client.post(
        "/admin/documents/upload",
        headers={"Authorization": "Bearer agent-rohit"},
        files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"doc_type": "support_policy", "visibility": "internal_only"},
    )
    assert resp.status_code == 403


def test_03_manager_upload_accepted_for_valid_pdf():
    pdf_bytes = _make_sample_pdf_bytes("Support policy update v5. Priority responses target 10 minutes.")
    resp = client.post(
        "/admin/documents/upload",
        headers={"Authorization": "Bearer manager-priya"},
        files={"file": ("policy_v5.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={
            "title": "Support Policy v5 Draft",
            "doc_type": "support_policy",
            "visibility": "internal_only",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "OK"
    assert data["document"]["status"] == "PENDING_REVIEW"
    assert data["document"]["doc_type"] == "support_policy"


def test_04_non_pdf_upload_rejected():
    resp = client.post(
        "/admin/documents/upload",
        headers={"Authorization": "Bearer manager-priya"},
        files={"file": ("script.txt", io.BytesIO(b"Hello world"), "text/plain")},
        data={"doc_type": "support_policy", "visibility": "internal_only"},
    )
    assert resp.status_code == 400
    assert "Only PDF documents" in resp.json()["detail"]


def test_05_oversize_pdf_rejected():
    large_bytes = b"%PDF-1.4\n" + (b"A" * (11 * 1024 * 1024))
    resp = client.post(
        "/admin/documents/upload",
        headers={"Authorization": "Bearer manager-priya"},
        files={"file": ("large.pdf", io.BytesIO(large_bytes), "application/pdf")},
        data={"doc_type": "support_policy", "visibility": "internal_only"},
    )
    assert resp.status_code == 400
    assert "10MB limit" in resp.json()["detail"]


def test_06_path_traversal_filename_sanitized():
    pdf_bytes = _make_sample_pdf_bytes("Sanitization check text.")
    resp = client.post(
        "/admin/documents/upload",
        headers={"Authorization": "Bearer manager-priya"},
        files={"file": ("../../etc/passwd.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"doc_type": "sop", "visibility": "internal_only"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "passwd" in data["document"]["filename"]
    assert ".." not in data["document"]["filename"]


def test_07_uploaded_doc_starts_processing_then_pending_review():
    pdf_bytes = _make_sample_pdf_bytes("Ingestion workflow test content.")
    resp = client.post(
        "/admin/documents/upload",
        headers={"Authorization": "Bearer manager-priya"},
        files={"file": ("workflow_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"title": "Workflow Test", "doc_type": "sop", "visibility": "internal_only"},
    )
    assert resp.status_code == 200
    doc_id = resp.json()["document"]["doc_id"]

    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.doc_id == doc_id).first()
        assert doc is not None
        assert doc.status == "PENDING_REVIEW"
        assert doc.is_user_uploaded is True
    finally:
        db.close()


def test_08_pending_review_document_excluded_from_normal_retrieval():
    pdf_bytes = _make_sample_pdf_bytes("UniqueSecretKeyword12345: Priority SLA target is 2 minutes.")
    resp = client.post(
        "/admin/documents/upload",
        headers={"Authorization": "Bearer manager-priya"},
        files={"file": ("pending_secret.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"doc_type": "support_policy", "visibility": "customer_visible"},
    )
    assert resp.status_code == 200
    doc_id = resp.json()["document"]["doc_id"]

    db = SessionLocal()
    try:
        results = hybrid_search(db, query="UniqueSecretKeyword12345", allow_deprecated=False)
        assert not any(r.doc_id == doc_id for r in results)
    finally:
        db.close()


def test_09_manager_activation_required_for_retrieval_eligibility():
    pdf_bytes = _make_sample_pdf_bytes("ActiveSecretKeyword99999: Verified active support rule.")
    resp = client.post(
        "/admin/documents/upload",
        headers={"Authorization": "Bearer manager-priya"},
        files={"file": ("activate_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"doc_type": "support_policy", "visibility": "customer_visible"},
    )
    assert resp.status_code == 200
    doc_id = resp.json()["document"]["doc_id"]

    # Before activation -> not retrieved
    db = SessionLocal()
    try:
        results_before = hybrid_search(db, query="ActiveSecretKeyword99999")
        assert not any(r.doc_id == doc_id for r in results_before)
    finally:
        db.close()

    # Manager activates document
    review_resp = client.post(
        f"/admin/documents/{doc_id}/review",
        headers={"Authorization": "Bearer manager-priya"},
        json={"action": "activate", "reason": "Manager approval granted", "confirmed": True},
    )
    assert review_resp.status_code == 200
    assert review_resp.json()["document"]["status"] == "ACTIVE"

    # After activation -> retrieved
    db = SessionLocal()
    try:
        results_after = hybrid_search(db, query="ActiveSecretKeyword99999", top_k=20)
        assert any(r.doc_id == doc_id for r in results_after)
    finally:
        db.close()


def test_10_support_agent_activation_denied():
    pdf_bytes = _make_sample_pdf_bytes("Agent activation test.")
    upload_resp = client.post(
        "/admin/documents/upload",
        headers={"Authorization": "Bearer manager-priya"},
        files={"file": ("agent_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"doc_type": "sop", "visibility": "internal_only"},
    )
    doc_id = upload_resp.json()["document"]["doc_id"]

    act_resp = client.post(
        f"/admin/documents/{doc_id}/review",
        headers={"Authorization": "Bearer agent-rohit"},
        json={"action": "activate", "reason": "Attempted agent activation", "confirmed": True},
    )
    assert act_resp.status_code == 403


def test_11_activation_creates_audit_log():
    pdf_bytes = _make_sample_pdf_bytes("Audit log verification text.")
    upload_resp = client.post(
        "/admin/documents/upload",
        headers={"Authorization": "Bearer manager-priya"},
        files={"file": ("audit_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"doc_type": "sop", "visibility": "internal_only"},
    )
    doc_id = upload_resp.json()["document"]["doc_id"]

    client.post(
        f"/admin/documents/{doc_id}/review",
        headers={"Authorization": "Bearer manager-priya"},
        json={"action": "activate", "reason": "Audit verification test", "confirmed": True},
    )

    audit_resp = client.get(
        f"/admin/audit-log?doc_id={doc_id}",
        headers={"Authorization": "Bearer manager-priya"},
    )
    assert audit_resp.status_code == 200
    logs = audit_resp.json()["audit_logs"]
    assert len(logs) >= 2
    actions = [l["action_type"] for l in logs]
    assert "document_uploaded" in actions
    assert "document_activated" in actions


def test_12_deprecation_removes_document_from_current_retrieval():
    pdf_bytes = _make_sample_pdf_bytes("DeprecationSecret777: Old policy statement.")
    upload_resp = client.post(
        "/admin/documents/upload",
        headers={"Authorization": "Bearer manager-priya"},
        files={"file": ("dep_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"doc_type": "sop", "visibility": "customer_visible"},
    )
    doc_id = upload_resp.json()["document"]["doc_id"]

    # Activate
    client.post(
        f"/admin/documents/{doc_id}/review",
        headers={"Authorization": "Bearer manager-priya"},
        json={"action": "activate", "reason": "Initial activation", "confirmed": True},
    )

    # Deprecate
    client.post(
        f"/admin/documents/{doc_id}/review",
        headers={"Authorization": "Bearer manager-priya"},
        json={"action": "deprecate", "reason": "Replaced by v6", "confirmed": True},
    )

    db = SessionLocal()
    try:
        # Excluded from normal search
        results_normal = hybrid_search(db, query="DeprecationSecret777", allow_deprecated=False)
        assert not any(r.doc_id == doc_id for r in results_normal)

        # Included when allow_deprecated is True
        results_deprecated = hybrid_search(db, query="DeprecationSecret777", allow_deprecated=True, top_k=20)
        assert any(r.doc_id == doc_id for r in results_deprecated)
    finally:
        db.close()


def test_13_agreement_requires_account_scope():
    pdf_bytes = _make_sample_pdf_bytes("Agreement text without account.")
    resp = client.post(
        "/admin/documents/upload",
        headers={"Authorization": "Bearer manager-priya"},
        files={"file": ("bad_agreement.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"doc_type": "agreement", "visibility": "internal_only"},
    )
    assert resp.status_code == 400
    assert "Agreement documents require a valid account_id" in resp.json()["detail"]


def test_14_internal_note_cannot_be_customer_visible():
    pdf_bytes = _make_sample_pdf_bytes("Internal ops note text.")
    resp = client.post(
        "/admin/documents/upload",
        headers={"Authorization": "Bearer manager-priya"},
        files={"file": ("bad_note.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"doc_type": "internal_note", "visibility": "customer_visible"},
    )
    assert resp.status_code == 400
    assert "Internal notes cannot be made customer_visible" in resp.json()["detail"]


def test_15_customer_cannot_see_other_account_agreement():
    db = SessionLocal()
    try:
        # Northstar customer searching for LumenWorks agreements
        results = hybrid_search(
            db,
            query="LumenWorks Service Agreement",
            account_id="ACCT-001",
            role="customer",
        )
        assert not any(r.doc_id == "DOC-06" for r in results)
    finally:
        db.close()


def test_16_customer_can_retrieve_own_active_agreement():
    db = SessionLocal()
    try:
        results = hybrid_search(
            db,
            query="Northstar Logistics Enterprise Agreement",
            account_id="ACCT-001",
            role="customer",
        )
        assert any(r.doc_id == "DOC-05" for r in results)
    finally:
        db.close()
