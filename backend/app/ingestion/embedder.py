"""Local, free embedding via sentence-transformers -- no external API call, no per-request
cost, and no dependency on any paid embedding provider."""
_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        from app.config import settings
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    vectors = model.encode(texts)
    return [v.tolist() for v in vectors]
