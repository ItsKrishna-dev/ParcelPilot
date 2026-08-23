"""Tool 1/3: Document search/retrieval."""
from sqlalchemy.orm import Session
from app.agent.schemas import DocSearchInput, DocSearchOutput, ToolResultStatus
from app.retrieval.hybrid_search import hybrid_search

from app.config import settings

def run_doc_search(db: Session, tool_input: DocSearchInput, account_id: str | None, role: str | None = None) -> DocSearchOutput:
    top_k = tool_input.top_k if tool_input.top_k is not None else settings.retrieval_top_k
    max_chars = settings.retrieval_max_chunk_chars

    chunks = hybrid_search(
        db, query=tool_input.query, doc_types=tool_input.doc_types,
        allow_deprecated=tool_input.allow_deprecated, account_id=account_id, role=role,
        top_k=top_k, max_chunk_chars=max_chars,
    )
    if not chunks:
        return DocSearchOutput(status=ToolResultStatus.NEEDS_VERIFICATION, results=[])

    results = [
        {
            "doc_id": c.doc_id,
            "filename": c.filename,
            "status": c.doc_status,
            "effective_date": c.effective_date,
            "page": c.page,
            "text": c.text[:max_chars],
            "score": c.score,
        }
        for c in chunks
    ]
    return DocSearchOutput(status=ToolResultStatus.OK, results=results)
