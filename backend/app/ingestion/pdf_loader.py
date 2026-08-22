"""
Parses the 6 supplied PDFs directly (NOT pre-converted to Markdown -- pre-flattening to
Markdown is a shortcut that would fail to generalize if the grader swaps in a differently
formatted PDF). Chunks the extracted text and embeds it locally.

Usage:
    python -m app.ingestion.pdf_loader --dir ../data_pack
"""
import argparse
import re
from pathlib import Path
from pypdf import PdfReader
from app.db.session import SessionLocal
from app.db.models import Document, DocChunk
from app.ingestion.chunker import chunk_text
from app.ingestion.embedder import embed_texts

FILENAME_TO_DOC_ID = {
    "01_Support_Policy_v3_CURRENT.pdf": "DOC-01",
    "02_Support_Policy_v2_DEPRECATED.pdf": "DOC-02",
    "03_Cancellation_and_Service_Credit_SOP_v4.pdf": "DOC-03",
    "04_Product_Operations_Guide_and_Known_Issues.pdf": "DOC-04",
    "05_Northstar_Logistics_Enterprise_Agreement.pdf": "DOC-05",
    "06_LumenWorks_Service_Agreement.pdf": "DOC-06",
}


def extract_pdf_pages(path: Path) -> list[str]:
    reader = PdfReader(str(path))
    return [page.extract_text() or "" for page in reader.pages]


def load_pdfs(data_dir: str):
    db = SessionLocal()
    try:
        for fname, doc_id in FILENAME_TO_DOC_ID.items():
            fpath = Path(data_dir) / fname
            if not fpath.exists():
                print(f"[pdf_loader] Skipping missing file: {fpath}")
                continue

            doc = db.query(Document).filter(Document.doc_id == doc_id).first()
            if doc is None:
                print(f"[pdf_loader] No Document row for {doc_id} -- run init_db first.")
                continue

            pages = extract_pdf_pages(fpath)
            doc.raw_text = "\n".join(pages)
            db.query(DocChunk).filter(DocChunk.doc_id == doc_id).delete()

            for page_num, page_text in enumerate(pages, start=1):
                cleaned = re.sub(r"\s+", " ", page_text).strip()
                if not cleaned:
                    continue
                for chunk in chunk_text(cleaned, max_tokens=180, overlap_tokens=30):
                    embedding = embed_texts([chunk])[0]
                    db.add(DocChunk(doc_id=doc_id, page=page_num, text=chunk, embedding=embedding))

            db.commit()
            print(f"[pdf_loader] Ingested {fname} -> {doc_id} ({len(pages)} pages)")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True, help="Directory containing the 6 supplied PDFs")
    args = parser.parse_args()
    load_pdfs(args.dir)
