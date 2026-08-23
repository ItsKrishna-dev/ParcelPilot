"""
Unit and integration tests for fast hybrid retrieval.
"""

import time
from app.db.models import DocChunk, Document
from app.retrieval.hybrid_search import hybrid_search, _embed_query


def test_query_embedder_speed():
    # Warm up / ensure model loaded
    _embed_query("warmup query")

    start = time.time()
    vec = _embed_query("cancellation policy and fee rules")
    elapsed_ms = (time.time() - start) * 1000
    assert vec is not None
    assert len(vec) == 384
    # Query embedding is fast (well under 300ms after model is loaded)
    assert elapsed_ms < 300


def test_hybrid_search_filters_deprecated_by_default(db_session):
    # Add chunks for current and deprecated policy
    db_session.add(
        DocChunk(doc_id="DOC-01", page=1, text="Current support policy SLA rules P1 P2 P3.")
    )
    db_session.add(
        DocChunk(doc_id="DOC-02", page=1, text="DEPRECATED v2 policy - DO NOT USE FOR CURRENT REQUESTS.")
    )
    db_session.commit()

    results = hybrid_search(db_session, query="SLA rules", allow_deprecated=False)
    doc_ids = [r.doc_id for r in results]
    assert "DOC-02" not in doc_ids


def test_hybrid_search_allows_deprecated_when_requested(db_session):
    db_session.add(
        DocChunk(doc_id="DOC-02", page=1, text="DEPRECATED v2 policy - DO NOT USE FOR CURRENT REQUESTS.")
    )
    db_session.commit()

    results = hybrid_search(db_session, query="DEPRECATED v2 policy", allow_deprecated=True)
    assert any(r.doc_id == "DOC-02" for r in results)


def test_hybrid_search_deduplication(db_session):
    # Add two identical chunks
    text_content = "Special cancellation terms: may cancel any BOOKED shipment before pickup."
    db_session.add(DocChunk(doc_id="DOC-05", page=1, text=text_content))
    db_session.add(DocChunk(doc_id="DOC-05", page=1, text=text_content))
    db_session.commit()

    results = hybrid_search(db_session, query="cancellation before pickup", top_k=5)
    matching = [r for r in results if r.doc_id == "DOC-05"]
    assert len(matching) == 1


def test_hybrid_search_truncation(db_session):
    long_text = "Policy details: " + ("x" * 3000)
    db_session.add(DocChunk(doc_id="DOC-03", page=1, text=long_text))
    db_session.commit()

    results = hybrid_search(db_session, query="Policy details", max_chunk_chars=500)
    for r in results:
        assert len(r.text) <= 500
