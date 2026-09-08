"""
Local vector store using sentence-transformers embeddings + FAISS.

Design note (mention this in your pitch): embeddings run locally, so raw
document text never has to leave the machine just to get embedded - only the
final retrieved snippets + question go to the LLM API for generation. That's
a meaningful data-governance win for a financial institution.

This module is written behind a small interface (`VectorStore`) so swapping
FAISS for a managed/production vector DB (Pinecone, Weaviate, Milvus,
pgvector) later is a one-file change, not a rewrite - see the "Scaling" note
in README.md.
"""
from __future__ import annotations
import os
import pickle
from dataclasses import dataclass

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from .ingest import Chunk


@dataclass
class RetrievedChunk:
    text: str
    source: str
    page: int
    chunk_type: str
    score: float


class VectorStore:
    def __init__(self, embedding_model_name: str):
        self.model = SentenceTransformer(embedding_model_name)
        self.index: faiss.Index | None = None
        self.chunks: list[Chunk] = []

    def build(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        texts = [c.text for c in chunks]
        embeddings = self.model.encode(texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True)
        embeddings = np.asarray(embeddings, dtype="float32")

        dim = embeddings.shape[1]
        # Inner product on normalized vectors == cosine similarity
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)

    def save(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)
        faiss.write_index(self.index, os.path.join(path, "index.faiss"))
        with open(os.path.join(path, "chunks.pkl"), "wb") as f:
            pickle.dump(self.chunks, f)

    def load(self, path: str) -> None:
        self.index = faiss.read_index(os.path.join(path, "index.faiss"))
        with open(os.path.join(path, "chunks.pkl"), "rb") as f:
            self.chunks = pickle.load(f)

    def search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        if self.index is None:
            raise RuntimeError("Index not built or loaded yet")

        q_emb = self.model.encode([query], normalize_embeddings=True)
        q_emb = np.asarray(q_emb, dtype="float32")

        scores, indices = self.index.search(q_emb, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            c = self.chunks[idx]
            results.append(RetrievedChunk(text=c.text, source=c.source, page=c.page, chunk_type=c.chunk_type, score=float(score)))
        return results
