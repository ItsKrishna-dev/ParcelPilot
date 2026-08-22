"""Simple whitespace-token chunker with overlap. Deliberately simple (not sentence-aware
NLP) -- the source documents are short (1-2 pages each), so a naive sliding window is more
than sufficient and avoids an extra NLP dependency."""


def chunk_text(text: str, max_tokens: int = 180, overlap_tokens: int = 30) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + max_tokens, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - overlap_tokens
    return chunks
