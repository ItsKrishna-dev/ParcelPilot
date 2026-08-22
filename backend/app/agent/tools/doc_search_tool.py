"""Tool 1/3: Document search/retrieval."""
from sqlalchemy.orm import Session
from app.agent.schemas import DocSearchInput, DocSearchOutput, ToolResultStatus
from app.retrieval.hybrid_search import hybrid_search


def run_doc_search(db: Session, tool_input: DocSearchInput, account_id: str | None) -> DocSearchOutput:
    chunks = hybrid_search(
        db, query=tool_input.query, doc_types=tool_input.doc_types,
        allow_deprecated=tool_input.allow_deprecated, account_id=account_id,
        top_k=tool_input.top_k,
    )
    if not chunks:
        return DocSearchOutput(status=ToolResultStatus.NEEDS_VERIFICATION, results=[])

    results = [
        {
            "doc_id": c.doc_id, "filename": c.filename, "status": c.doc_status,
            "effective_date": c.effective_date, "page": c.page, "text": c.text, "score": c.score,
        }
        for c in chunks
    ]
    return DocSearchOutput(status=ToolResultStatus.OK, results=results)
