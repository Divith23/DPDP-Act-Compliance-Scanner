import json
import re
from pathlib import Path

import pymupdf as fitz
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

DOCUMENTS_DIR = Path("knowledge_base/documents")
VECTORSTORE_DIR = Path("vectorstore")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 250   # target words per chunk
CHUNK_OVERLAP = 40  # words overlap between chunks

_model: SentenceTransformer = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _extract_pages(pdf_path: Path) -> list[dict]:
    pages = []
    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text()
            text = re.sub(r"\n{3,}", "\n\n", text)
            text = re.sub(r"[ \t]+", " ", text).strip()
            if text:
                pages.append({
                    "text": text,
                    "source": pdf_path.name,
                    "page": page_num,
                })
    return pages


def _chunk_pages(pages: list[dict]) -> list[dict]:
    chunks = []
    for page in pages:
        words = page["text"].split()
        start = 0
        while start < len(words):
            end = start + CHUNK_SIZE
            chunk_text = " ".join(words[start:end])
            chunks.append({
                "text": chunk_text,
                "source": page["source"],
                "page": page["page"],
            })
            if end >= len(words):
                break
            start = end - CHUNK_OVERLAP
    return chunks


def build_vectorstore():
    VECTORSTORE_DIR.mkdir(exist_ok=True)

    pdf_files = list(DOCUMENTS_DIR.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {DOCUMENTS_DIR}")

    all_chunks = []
    for pdf_path in pdf_files:
        print(f"  Extracting: {pdf_path.name}")
        pages = _extract_pages(pdf_path)
        chunks = _chunk_pages(pages)
        all_chunks.extend(chunks)
        print(f"  -> {len(pages)} pages, {len(chunks)} chunks")

    print(f"\nGenerating embeddings for {len(all_chunks)} chunks...")
    model = _get_model()
    texts = [c["text"] for c in all_chunks]
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    embeddings = embeddings.astype(np.float32)
    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, str(VECTORSTORE_DIR / "index.faiss"))
    with open(VECTORSTORE_DIR / "chunks.json", "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"\nVectorstore saved to {VECTORSTORE_DIR}/")
    print(f"  index.faiss — {index.ntotal} vectors")
    print(f"  chunks.json — {len(all_chunks)} chunks")


if __name__ == "__main__":
    print("Building vectorstore...\n")
    build_vectorstore()
