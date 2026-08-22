"""
Hybrid retrieval: BM25 (keyword) + pgvector cosine (semantic), merged with a simple
weighted-rank fusion. Filters out DEPRECATED documents by default -- the single most
important retrieval-time safety rule in this whole system (see 02_Support_Policy_v2's own
"DO NOT USE FOR CURRENT REQUESTS" banner).
"""
from dataclasses import dataclass
from sqlalchemy.orm import Session
from rank_bm25 import BM25Okapi
from app.db.models import DocChunk, Document


@dataclass
class RetrievedChunk:
    doc_id: str
    filename: str
    doc_status: str
    effective_date: str | None
    page: int | None
    text: str
    score: float


def _get_embedder():
    from sentence_transformers import SentenceTransformer
    from app.config import settings
    return SentenceTransformer(settings.embedding_model)


def hybrid_search(
    db: Session,
    query: str,
    doc_types: list[str] | None = None,
    allow_deprecated: bool = False,
    account_id: str | None = None,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    q = (
        db.query(DocChunk, Document)
        .join(Document, DocChunk.doc_id == Document.doc_id)
    )
    if not allow_deprecated:
        q = q.filter(Document.status == "CURRENT")
    if doc_types:
        q = q.filter(Document.doc_type.in_(doc_types))
    if account_id:
        q = q.filter((Document.account_id == account_id) | (Document.account_id.is_(None)))

    rows = q.all()
    if not rows:
        return []

    corpus = [r[0].text for r in rows]
    tokenized_corpus = [c.lower().split() for c in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    bm25_scores = bm25.get_scores(query.lower().split())

    try:
        embedder = _get_embedder()
        query_vec = embedder.encode(query)
        chunk_vecs = embedder.encode(corpus)
        import numpy as np
        sem_scores = chunk_vecs @ query_vec / (
            (np.linalg.norm(chunk_vecs, axis=1) * np.linalg.norm(query_vec)) + 1e-8
        )
    except Exception:
        sem_scores = [0.0] * len(corpus)

    results = []
    for (chunk, doc), bm25_s, sem_s in zip(rows, bm25_scores, sem_scores):
        fused = 0.5 * float(bm25_s) + 0.5 * float(sem_s) * 10
        results.append(RetrievedChunk(
            doc_id=doc.doc_id, filename=doc.filename, doc_status=doc.status,
            effective_date=str(doc.effective_date) if doc.effective_date else None,
            page=chunk.page, text=chunk.text, score=round(fused, 4),
        ))

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_k]
