import json
import os
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Disable Hugging Face hub network roundtrips for maximum speed
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

VECTORSTORE_DIR = Path("vectorstore")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_model: SentenceTransformer = None
_index: faiss.Index = None
_chunks: list[dict] = None


def _load():
    global _model, _index, _chunks

    index_path = VECTORSTORE_DIR / "index.faiss"
    chunks_path = VECTORSTORE_DIR / "chunks.json"

    if not index_path.exists() or not chunks_path.exists():
        raise FileNotFoundError(
            "Vectorstore not found. Run: python -m app.services.document_ingestion"
        )

    if _index is None:
        _index = faiss.read_index(str(index_path))

    if _chunks is None:
        with open(chunks_path, encoding="utf-8") as f:
            _chunks = json.load(f)

    if _model is None:
        try:
            _model = SentenceTransformer(EMBEDDING_MODEL, local_files_only=True)
        except Exception:
            _model = SentenceTransformer(EMBEDDING_MODEL)


def search_documents(query: str, top_k: int = 5) -> list[dict]:
    _load()

    embedding = _model.encode([query], convert_to_numpy=True).astype(np.float32)
    faiss.normalize_L2(embedding)

    scores, indices = _index.search(embedding, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        chunk = _chunks[idx]
        results.append({
            "text": chunk["text"],
            "source": chunk["source"],
            "page": chunk["page"],
            "score": round(float(score), 4),
        })
    return results
