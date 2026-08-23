"""Local, free embedding via sentence-transformers -- no external API call, no per-request
cost, and no dependency on any paid embedding provider.

NOTE: sentence-transformers is only required for ingestion (pdf_loader, load_workbook).
It is NOT required at web-service runtime. On Render free tier it is not installed.
"""
_model = None


def _get_model():
    global _model
    if _model is None:
        try:
            import torch
            torch.set_num_threads(1)
            torch.set_grad_enabled(False)
            from sentence_transformers import SentenceTransformer
            from app.config import settings
            _model = SentenceTransformer(settings.embedding_model, device="cpu")
            _model.eval()
        except ImportError:
            raise RuntimeError(
                "sentence-transformers is not installed. "
                "Run: pip install sentence-transformers==3.1.1"
            )
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    vectors = model.encode(texts)
    return [v.tolist() for v in vectors]
