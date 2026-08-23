"""
Hybrid retrieval: BM25 (keyword) + pgvector cosine (semantic), merged with weighted rank fusion.

Performance and reliability principles:
1. Embed ONLY the query at search time (1 vector encode vs re-encoding entire corpus).
2. Cache query vector encodings to ensure sub-10ms performance on repeated queries.
3. Fall back gracefully to BM25-only if sentence-transformers is unavailable (e.g. Render free tier).
4. Hard-filter out DEPRECATED documents by default (e.g. 02_Support_Policy_v2).
5. Deduplicate results strictly (one top chunk per document).
6. Truncate chunk text to prevent context blowup under free-tier token limits.
"""

import functools
import re
import threading
import time
from dataclasses import dataclass
from typing import List, Optional

from rank_bm25 import BM25Okapi
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import DocChunk, Document

_embedder_lock = threading.Lock()
_embedder_instance = None
_embedder_available: Optional[bool] = None  # None = unchecked, True/False = checked


def _try_load_embedder():
    """
    Attempt to load sentence-transformers. Returns the model or None.
    If sentence-transformers is not installed (e.g. Render free tier),
    returns None cleanly so BM25-only mode activates.
    """
    global _embedder_instance, _embedder_available
    if _embedder_available is False:
        return None
    if _embedder_instance is not None:
        return _embedder_instance
    with _embedder_lock:
        if _embedder_instance is not None:
            return _embedder_instance
        if _embedder_available is False:
            return None
        try:
            import torch
            torch.set_num_threads(1)
            torch.set_grad_enabled(False)
            from sentence_transformers import SentenceTransformer
            _embedder_instance = SentenceTransformer(
                settings.embedding_model,
                device="cpu"
            )
            _embedder_instance.eval()
            _embedder_available = True
            print("[hybrid_search] sentence-transformers loaded — hybrid mode active")
        except Exception as e:
            _embedder_available = False
            _embedder_instance = None
            print(f"[hybrid_search] sentence-transformers unavailable ({e}) — BM25-only mode")
    return _embedder_instance


@functools.lru_cache(maxsize=256)
def _embed_query_cached(query: str) -> Optional[tuple]:
    embedder = _try_load_embedder()
    if embedder is None:
        return None
    try:
        vec = embedder.encode([query])[0]
        vec_list = vec.tolist() if hasattr(vec, "tolist") else list(vec)
        return tuple(vec_list)
    except Exception:
        return None


def _embed_query(query: str) -> Optional[List[float]]:
    res = _embed_query_cached(query)
    return list(res) if res is not None else None


@dataclass
class RetrievedChunk:
    doc_id: str
    filename: str
    doc_status: str
    effective_date: Optional[str]
    page: Optional[int]
    text: str
    score: float


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _deduplicate_by_document(results: List[RetrievedChunk], max_results: int) -> List[RetrievedChunk]:
    seen_documents = set()
    unique = []

    for result in results:
        if result.doc_id in seen_documents:
            continue

        seen_documents.add(result.doc_id)
        unique.append(result)

        if len(unique) >= max_results:
            break

    return unique


def hybrid_search(
    db: Session,
    query: str,
    doc_types: Optional[List[str]] = None,
    allow_deprecated: bool = False,
    account_id: Optional[str] = None,
    role: Optional[str] = None,
    top_k: Optional[int] = None,
    max_chunk_chars: Optional[int] = None,
) -> List[RetrievedChunk]:
    """
    Fast hybrid search combining pgvector cosine similarity and BM25 scoring.
    Falls back cleanly to BM25-only when sentence-transformers is not available.
    """
    request_started = time.perf_counter()
    effective_top_k = top_k if top_k is not None else settings.retrieval_top_k
    max_chars = max_chunk_chars if max_chunk_chars is not None else settings.retrieval_max_chunk_chars

    clean_query = query.strip()
    if not clean_query:
        return []

    # 1. Base query with strict status & scope filtering
    q = (
        db.query(DocChunk, Document)
        .join(Document, DocChunk.doc_id == Document.doc_id)
    )

    if not allow_deprecated:
        q = q.filter(Document.status.in_(["CURRENT", "ACTIVE"]))
    else:
        q = q.filter(Document.status.in_(["CURRENT", "ACTIVE", "DEPRECATED"]))

    if role == "customer":
        q = q.filter(Document.doc_type != "internal_note")
        if account_id:
            q = q.filter(
                (Document.visibility == "customer_visible")
                | ((Document.account_id == account_id) & (Document.doc_type == "agreement"))
            )
        else:
            q = q.filter(Document.visibility == "customer_visible")

    if doc_types:
        q = q.filter(Document.doc_type.in_(doc_types))

    if account_id:
        q = q.filter(
            (Document.account_id == account_id) | (Document.account_id.is_(None))
        )

    rows = q.all()
    if not rows:
        return []

    # 2. BM25 keyword scoring (always available — no ML dependency)
    corpus = [r[0].text for r in rows]
    tokenized_corpus = [c.lower().split() for c in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    bm25_raw_scores = bm25.get_scores(clean_query.lower().split())

    max_bm25 = max(bm25_raw_scores) if len(bm25_raw_scores) > 0 and max(bm25_raw_scores) > 0 else 1.0
    bm25_norm_scores = [float(s) / max_bm25 for s in bm25_raw_scores]

    # 3. Semantic scoring — use pre-stored chunk embeddings from Neon
    #    If sentence-transformers is available, encode the query locally.
    #    If not (Render free tier), fall back to BM25-only (sem_scores all 0.0).
    sem_scores = [0.0] * len(rows)
    query_vec = _embed_query(clean_query)

    if query_vec is not None:
        try:
            import numpy as np
            q_arr = np.array(query_vec, dtype=np.float32)
            q_norm = np.linalg.norm(q_arr)

            for i, (chunk, _) in enumerate(rows):
                if chunk.embedding is not None:
                    c_arr = np.array(chunk.embedding, dtype=np.float32)
                    c_norm = np.linalg.norm(c_arr)
                    if c_norm > 1e-8 and q_norm > 1e-8:
                        cosine_sim = float(np.dot(c_arr, q_arr) / (c_norm * q_norm))
                        sem_scores[i] = max(0.0, cosine_sim)
        except Exception:
            sem_scores = [0.0] * len(rows)

    # 4. Score Fusion & Candidate Generation
    # In BM25-only mode (sem_scores all 0), fused == bm25_norm, which is still effective.
    candidates: List[RetrievedChunk] = []
    for (chunk, doc), bm25_s, sem_s in zip(rows, bm25_norm_scores, sem_scores):
        fused = 0.5 * bm25_s + 0.5 * sem_s if any(s > 0 for s in sem_scores) else bm25_s
        truncated_text = chunk.text[:max_chars] if chunk.text else ""
        candidates.append(
            RetrievedChunk(
                doc_id=doc.doc_id,
                filename=doc.filename,
                doc_status=doc.status,
                effective_date=str(doc.effective_date) if doc.effective_date else None,
                page=chunk.page,
                text=truncated_text,
                score=round(fused, 4),
            )
        )

    # Sort descending by fused score
    candidates.sort(key=lambda r: r.score, reverse=True)

    # 5. Strict Document Deduplication
    final_results = _deduplicate_by_document(candidates, max_results=effective_top_k)

    mode = "hybrid" if query_vec is not None else "bm25-only"
    print(
        "[hybrid_search]",
        {
            "query": query,
            "mode": mode,
            "total_ms": round((time.perf_counter() - request_started) * 1000, 2),
            "rows_loaded": len(rows),
            "top_k": effective_top_k,
        },
    )

    return final_results
